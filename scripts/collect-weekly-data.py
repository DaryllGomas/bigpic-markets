#!/usr/bin/env python3
"""
collect-weekly-data.py — Deterministic market ground-truth for the weekly Eagle Eye.

The weekly Eagle Eye report currently sources every hard number (index levels, weekly %,
YTD, sector returns, yields, commodity moves) from WebSearch agents — no deterministic
anchor, which is the report's #1 correctness risk (e.g. W21 shipped a stale WTI "Friday
close" and a hand-written S&P weekly of ~+0.6% when the real figure was +1.43%).

This collector pulls those numbers deterministically from the Schwab options API
(/api/history) + FRED, computes weekly% / YTD% / sector-5d / yields aligned to the
report's target Friday, and writes them to the `weekly_scorecard` table in market.db
(the SSOT the stamp-scorecard.py / verify gate read). It also emits a human/LLM-readable
markdown artifact (mirroring how collect-weekly-calendar.py feeds stamp-calendar.py).

NO new JSON files (market.db is the SSOT, per project policy). stdlib-only.

Usage:
    python3 collect-weekly-data.py --friday 2026-05-29 \
        --db /path/to/market.db --output /path/to/weekly_groundtruth.md [--verbose]

Exit codes:
    0 - Full success (all index data collected)
    1 - Partial (some symbols/series failed, but indices present)
    3 - Total failure (no index data — Schwab API down or unreachable)

Key API gotchas (all confirmed live, 2026-05-31):
  - Weekend /api/quotes returns netPercentChange=0.0 (stale) — NEVER use it for weekly%.
    Weekly% comes from /api/history?frequency_type=weekly (candles[-1] vs candles[-2]).
  - YTD needs period_type=year&period=2&frequency_type=daily (502 candles incl. the prior
    Dec-31 close). period_type=ytd returns 0 candles; period=1 only reaches ~May (no Jan).
  - '/'-prefixed futures roots (/CL,/BZ,/GC) return 0 candles on /api/history — commodity
    weekly deltas MUST use ETF proxies (USO=WTI, BNO=Brent, GLD=Gold, UUP=Dollar).
  - Use '$'-prefixed Schwab index symbols ($SPX,$DJI,$COMPX,$RUT,$NDX,$VIX); '^GSPC' is empty.
"""

import argparse
import csv
import datetime as dt
import io
import logging
import sqlite3
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# ── Configuration ─────────────────────────────────────────────────────────────
SCHWAB_BASE = "http://192.168.10.60:8000"
FRED_BASE = "https://fred.stlouisfed.org/graph/fredgraph.csv"
SCHWAB_TIMEOUT = 20
FRED_TIMEOUT = 15
MAX_RETRIES = 2
CHUNK_DELAY = 0.5          # seconds between sequential Schwab calls (API pacing — never burst)
USER_AGENT = "BigPic-Markets-Weekly/1.0"
EMAIL_TO = "daryll@bigpicsolutions.com"

# Symbol universe (Schwab '$' index symbols; ETFs plain).
INDICES = [
    ("$SPX", "S&P 500"),
    ("$COMPX", "Nasdaq Composite"),
    ("$NDX", "Nasdaq-100"),
    ("$DJI", "Dow Jones"),
    ("$RUT", "Russell 2000"),
    ("$VIX", "VIX"),
]
SECTORS = [
    ("XLK", "Technology"), ("XLF", "Financials"), ("XLE", "Energy"),
    ("XLV", "Health Care"), ("XLI", "Industrials"), ("XLY", "Consumer Disc."),
    ("XLP", "Consumer Staples"), ("XLU", "Utilities"), ("XLB", "Materials"),
    ("XLRE", "Real Estate"), ("XLC", "Communication Svcs."),
]
# proxy_symbol, display name, the underlying it proxies
COMMODITY_PROXIES = [
    ("USO", "WTI Crude (USO proxy)", "WTI"),
    ("BNO", "Brent Crude (BNO proxy)", "Brent"),
    ("GLD", "Gold (GLD proxy)", "Gold"),
    ("UUP", "US Dollar (UUP proxy)", "DXY"),
]
# 10Y/30Y come from Schwab index symbols (yield = close/10) — same reliable API as the
# indices. 2Y has no Schwab equivalent, so it falls back to FRED DGS2 (best-effort).
SCHWAB_YIELDS = [("$TNX", "10-Year Treasury"), ("$TYX", "30-Year Treasury")]
FRED_YIELDS = [("DGS2", "2-Year Treasury")]

log = logging.getLogger("weekly-data")


# ── HTTP (stdlib urllib, retry + backoff) ─────────────────────────────────────
def _get(url, timeout):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def fetch_json(url, timeout=SCHWAB_TIMEOUT, retries=MAX_RETRIES):
    """GET JSON with retry/backoff. Returns dict or None."""
    import json
    for attempt in range(1, retries + 2):
        try:
            raw = _get(url, timeout)
            return json.loads(raw.decode("utf-8"))
        except (urllib.error.URLError, urllib.error.HTTPError, ValueError, TimeoutError) as e:
            if attempt > retries:
                log.warning("fetch_json failed (%s): %s", url, e)
                return None
            time.sleep(2 ** (attempt - 1))
    return None


def fetch_text(url, timeout=FRED_TIMEOUT, retries=MAX_RETRIES):
    """GET text (FRED CSV) with retry/backoff. Returns str or None."""
    for attempt in range(1, retries + 2):
        try:
            return _get(url, timeout).decode("utf-8")
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            if attempt > retries:
                log.warning("fetch_text failed (%s): %s", url, e)
                return None
            time.sleep(2 ** (attempt - 1))
    return None


def history_url(symbol, *, freq_type, period_type, period):
    """Build an /api/history URL ('$' and '/' are URL-encoded)."""
    sym = urllib.parse.quote(symbol, safe="")
    return (f"{SCHWAB_BASE}/api/history/{sym}"
            f"?frequency_type={freq_type}&period_type={period_type}"
            f"&period={period}&frequency=1")


# ── Candle helpers ────────────────────────────────────────────────────────────
def candle_date(c):
    """UTC date of a candle (datetime is epoch-ms; weekly = Monday week-open)."""
    return dt.datetime.fromtimestamp(c["datetime"] / 1000, tz=dt.timezone.utc).date()


def fetch_candles(symbol, *, freq_type, period_type, period):
    data = fetch_json(history_url(symbol, freq_type=freq_type, period_type=period_type, period=period))
    if not data:
        return []
    return data.get("candles", []) or []


# Freshness guards: the selected candle must actually COVER the target Friday.
# Without this, a `--friday` past the last candle (future/out-of-range) silently
# returns the most-recent candle, and we'd write stale numbers under the target
# date with a false "verified" label. A weekly candle's Monday is <=6d before its
# Friday; a daily candle sits on/just-before the Friday (holiday-tolerant).
WEEKLY_MAX_GAP_DAYS = 7
DAILY_MAX_GAP_DAYS = 5


def _covers(candle, friday, max_gap_days):
    """True if `candle` actually covers `friday` (not a stale most-recent candle)."""
    return (friday - candle_date(candle)).days <= max_gap_days


def week_close_and_prev(candles, friday):
    """The weekly candle whose week contains `friday`, plus the prior week's candle.

    Weekly candle datetime = the week-open Monday, so the candle for the week
    containing `friday` is the last one whose Monday <= friday. This aligns to the
    report's target Friday even when the collector runs mid-week (Monday backup cron).
    Returns (None, None) if the target week has no candle yet (future / out-of-range).
    """
    elig = [c for c in candles if candle_date(c) <= friday]
    if len(elig) < 2 or not _covers(elig[-1], friday, WEEKLY_MAX_GAP_DAYS):
        return None, None
    return elig[-1], elig[-2]


def daily_current_and_prev(candles, friday):
    """The daily candle on/at `friday` and the prior trading day's candle."""
    elig = [c for c in candles if candle_date(c) <= friday]
    if len(elig) < 2 or not _covers(elig[-1], friday, DAILY_MAX_GAP_DAYS):
        return None, None
    return elig[-1], elig[-2]


def ytd_base(candles, friday):
    """Last candle of the prior calendar year (the Dec-31 YTD baseline)."""
    base = None
    for c in candles:
        if candle_date(c).year == friday.year - 1:
            base = c
    return base


def ret_5d(candles, friday):
    """Trailing 5-trading-day return aligned to `friday` (holiday-safe via candle gaps)."""
    elig = [c for c in candles if candle_date(c) <= friday]
    if len(elig) < 6 or not _covers(elig[-1], friday, DAILY_MAX_GAP_DAYS):
        return None, None
    return elig[-1], elig[-6]


def pct(curr, prev):
    if prev in (None, 0) or curr is None:
        return None
    return (curr - prev) / prev * 100.0


# ── Database ──────────────────────────────────────────────────────────────────
SCHEMA = """
CREATE TABLE IF NOT EXISTS weekly_scorecard (
    market_date TEXT NOT NULL,        -- target Friday (week ending), ISO date
    symbol      TEXT NOT NULL,        -- canonical symbol ($SPX, XLK, USO, DGS10, ...)
    name        TEXT,                 -- display name
    asset_class TEXT,                 -- index | sector | commodity | treasury
    level       REAL,                 -- last close (index level / ETF price / yield %)
    daily_pct   REAL,                 -- Friday daily % (price assets)
    weekly_pct  REAL,                 -- week-over-week % (price assets; 5d for sectors)
    ytd_pct     REAL,                 -- year-to-date %
    weekly_bp   REAL,                 -- weekly change in basis points (treasuries)
    source      TEXT,                 -- schwab_history | etf_proxy | fred
    proxy_for   TEXT,                 -- underlying when this is an ETF proxy (e.g. WTI)
    fetched_at  TEXT NOT NULL,
    PRIMARY KEY (market_date, symbol)
);
"""


def init_db(conn):
    conn.executescript(SCHEMA)
    conn.commit()


def upsert(conn, market_date, row, fetched_at):
    conn.execute(
        """INSERT OR REPLACE INTO weekly_scorecard
           (market_date, symbol, name, asset_class, level, daily_pct, weekly_pct,
            ytd_pct, weekly_bp, source, proxy_for, fetched_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        (market_date, row["symbol"], row.get("name"), row.get("asset_class"),
         row.get("level"), row.get("daily_pct"), row.get("weekly_pct"),
         row.get("ytd_pct"), row.get("weekly_bp"), row.get("source"),
         row.get("proxy_for"), fetched_at),
    )


# ── Collectors ────────────────────────────────────────────────────────────────
def collect_index(symbol, name, friday):
    """Index/VIX: level + weekly% (weekly candles), daily% + YTD% (daily period=2)."""
    weekly = fetch_candles(symbol, freq_type="weekly", period_type="year", period=1)
    cur_w, prev_w = week_close_and_prev(weekly, friday)
    if not cur_w:
        return None
    row = {"symbol": symbol, "name": name, "asset_class": "index",
           "level": cur_w["close"], "weekly_pct": pct(cur_w["close"], prev_w["close"]),
           "source": "schwab_history"}
    time.sleep(CHUNK_DELAY)
    daily = fetch_candles(symbol, freq_type="daily", period_type="year", period=2)
    if daily:
        cur_d, prev_d = daily_current_and_prev(daily, friday)
        if cur_d:
            row["daily_pct"] = pct(cur_d["close"], prev_d["close"])
            base = ytd_base(daily, friday)
            if base:
                row["ytd_pct"] = pct(cur_d["close"], base["close"])
            # Prefer the exact daily close for the level (weekly candle close should match).
            row["level"] = cur_d["close"]
    return row


def collect_sector(symbol, name, friday):
    """Sector SPDR: trailing 5-trading-day return (the heatmap metric)."""
    daily = fetch_candles(symbol, freq_type="daily", period_type="month", period=1)
    cur, prior = ret_5d(daily, friday)
    if not cur:
        return None
    return {"symbol": symbol, "name": name, "asset_class": "sector",
            "level": cur["close"], "weekly_pct": pct(cur["close"], prior["close"]),
            "source": "schwab_history"}


def collect_commodity(symbol, name, proxy_for, friday):
    """Commodity via ETF proxy: weekly% only (futures roots fail on /api/history).

    Only the WEEKLY % is kept — over a short horizon the proxy tracks the underlying
    directionally. ETF YTD/level are NOT emitted: roll/contango makes a proxy's yearly
    move and its raw price meaningless as a stand-in for the commodity spot.
    """
    weekly = fetch_candles(symbol, freq_type="weekly", period_type="year", period=1)
    cur_w, prev_w = week_close_and_prev(weekly, friday)
    if not cur_w:
        return None
    return {"symbol": symbol, "name": name, "asset_class": "commodity",
            "level": cur_w["close"], "weekly_pct": pct(cur_w["close"], prev_w["close"]),
            "source": "etf_proxy", "proxy_for": proxy_for}


def _fred_series(sid, friday):
    """Fetch one FRED series as [(date, value), ...] within ~3 weeks of `friday`.

    Single-id queries honor cosd/coed (small, fast). A multi-id query
    (id=DGS2,DGS10,DGS30) silently IGNORES the date bounds and dumps the full
    history back to 1962 — so always fetch one series at a time.
    """
    start = (friday - dt.timedelta(days=21)).isoformat()
    url = f"{FRED_BASE}?id={sid}&cosd={start}&coed={friday.isoformat()}"
    text = fetch_text(url, retries=1)  # 2Y is best-effort; don't hang on a throttled FRED
    if not text:
        return []
    out = []
    for rec in csv.DictReader(io.StringIO(text)):
        rdate = rec.get("observation_date") or rec.get("DATE")
        val = (rec.get(sid) or "").strip()
        if rdate and val and val != ".":
            try:
                out.append((rdate, float(val)))
            except ValueError:
                pass
    return out


def collect_treasuries(friday):
    """Treasury yields + weekly bp move. 10Y/30Y from Schwab history; 2Y from FRED."""
    out = []
    anchor = (friday - dt.timedelta(days=5)).isoformat()

    # 10Y/30Y via Schwab $TNX/$TYX weekly history (value is yield x10).
    for sym, name in SCHWAB_YIELDS:
        weekly = fetch_candles(sym, freq_type="weekly", period_type="year", period=1)
        time.sleep(CHUNK_DELAY)
        cur_w, prev_w = week_close_and_prev(weekly, friday)
        if not cur_w:
            continue
        weekly_bp = round((cur_w["close"] - prev_w["close"]) * 10, 1) if prev_w else None
        out.append({"symbol": sym, "name": name, "asset_class": "treasury",
                    "level": cur_w["close"] / 10.0, "weekly_bp": weekly_bp,
                    "source": "schwab_history"})

    # 2Y via FRED DGS2 (best-effort; no Schwab equivalent).
    for sid, name in FRED_YIELDS:
        series = _fred_series(sid, friday)
        time.sleep(CHUNK_DELAY)
        if not series:
            continue
        cur = series[-1][1]
        wk_ago_val = None
        for d, v in series:
            if d <= anchor:
                wk_ago_val = v
        weekly_bp = round((cur - wk_ago_val) * 100, 1) if wk_ago_val is not None else None
        out.append({"symbol": sid, "name": name, "asset_class": "treasury",
                    "level": cur, "weekly_bp": weekly_bp, "source": "fred"})
    return out


# ── Markdown ground-truth artifact ────────────────────────────────────────────
def _fp(x, dp=2):
    return "—" if x is None else f"{x:,.{dp}f}"


def _pp(x):
    return "—" if x is None else f"{x:+.2f}%"


def emit_markdown(rows, friday, path):
    idx = [r for r in rows if r["asset_class"] == "index"]
    sec = [r for r in rows if r["asset_class"] == "sector"]
    com = [r for r in rows if r["asset_class"] == "commodity"]
    tre = [r for r in rows if r["asset_class"] == "treasury"]
    out = []
    out.append(f"# Weekly Market Ground Truth — week ending {friday.isoformat()}")
    out.append("")
    out.append("_Deterministic data from Schwab /api/history + FRED. These are EXACT, "
               "verified numbers — use them as-is in the Scorecard; do NOT override with web estimates._")
    out.append("")
    if idx:
        out.append("## Indices")
        out.append("| Index | Fri Close | Fri Day % | Weekly % | YTD % |")
        out.append("|-------|----------:|----------:|---------:|------:|")
        for r in idx:
            out.append(f"| {r['name']} ({r['symbol']}) | {_fp(r.get('level'))} | "
                       f"{_pp(r.get('daily_pct'))} | {_pp(r.get('weekly_pct'))} | {_pp(r.get('ytd_pct'))} |")
        out.append("")
    if sec:
        out.append("## Sectors — trailing 5-day return")
        out.append("| Sector ETF | 5-Day % |")
        out.append("|-----------|--------:|")
        for r in sorted(sec, key=lambda x: (x.get("weekly_pct") if x.get("weekly_pct") is not None else -999), reverse=True):
            out.append(f"| {r['name']} ({r['symbol']}) | {_pp(r.get('weekly_pct'))} |")
        out.append("")
    if com:
        out.append("## Commodities & Dollar — ETF-proxy weekly % (directional only; NOT spot futures %, no level)")
        out.append("| Underlying | Weekly % | (via proxy) |")
        out.append("|-----------|---------:|:------------|")
        for r in com:
            out.append(f"| {r.get('proxy_for')} | {_pp(r.get('weekly_pct'))} | {r['symbol']} |")
        out.append("")
    if tre:
        out.append("## Treasuries — Schwab $TNX/$TYX (10Y/30Y); 2Y via FRED")
        out.append("| Maturity | Yield % | Weekly Δ (bp) |")
        out.append("|----------|--------:|--------------:|")
        for r in tre:
            bp = "—" if r.get("weekly_bp") is None else f"{r['weekly_bp']:+.1f}"
            out.append(f"| {r['name']} | {_fp(r.get('level'), 3)} | {bp} |")
        out.append("")
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(out) + "\n", encoding="utf-8")


# ── Failure email (best-effort, matches sibling scripts) ──────────────────────
def send_failure_email(friday, detail):
    body = (f"Subject: [FAILED] Eagle Eye weekly data collection — week ending {friday}\n"
            f"From: weekly-data@bigpic\nTo: {EMAIL_TO}\n\n"
            f"collect-weekly-data.py could not collect index ground truth.\n\nDetail: {detail}\n")
    try:
        subprocess.run(["msmtp", EMAIL_TO], input=body.encode(), timeout=30, check=False)
    except (FileNotFoundError, subprocess.SubprocessError) as e:
        log.warning("msmtp unavailable, no failure email sent: %s", e)


# ── Date helper ───────────────────────────────────────────────────────────────
def most_recent_friday(today=None):
    today = today or dt.date.today()
    # Friday weekday() == 4; step back to it (today if it's Friday).
    return today - dt.timedelta(days=(today.weekday() - 4) % 7)


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description="Collect deterministic weekly market ground truth for Eagle Eye.")
    ap.add_argument("--friday", help="Week-ending Friday (YYYY-MM-DD). Default: most recent Friday.")
    ap.add_argument("--db", required=True, help="Path to market.db")
    ap.add_argument("--output", help="Path to write the ground-truth markdown artifact.")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    friday = dt.date.fromisoformat(args.friday) if args.friday else most_recent_friday()
    market_date = friday.isoformat()
    fetched_at = dt.datetime.now(tz=dt.timezone.utc).isoformat()
    log.info("Collecting weekly ground truth for week ending %s", market_date)

    conn = sqlite3.connect(str(args.db))
    init_db(conn)

    rows, failures = [], []

    # Indices (critical — failure here is fatal)
    for sym, name in INDICES:
        r = collect_index(sym, name, friday)
        if r:
            rows.append(r)
            log.info("index %-7s level=%s weekly=%s ytd=%s", sym,
                     _fp(r.get("level")), _pp(r.get("weekly_pct")), _pp(r.get("ytd_pct")))
        else:
            failures.append(sym)
            log.warning("index %s — no data", sym)
        time.sleep(CHUNK_DELAY)

    index_count = sum(1 for r in rows if r["asset_class"] == "index")
    if index_count == 0:
        log.error("No index data for week ending %s — Schwab API unreachable, OR --friday is "
                  "outside the available candle range (too early / future).", market_date)
        send_failure_email(friday, f"No index ground truth for week ending {market_date} "
                                   f"(Schwab API down, or --friday out of range).")
        conn.close()
        return 3

    # Sectors
    for sym, name in SECTORS:
        r = collect_sector(sym, name, friday)
        if r:
            rows.append(r)
            log.info("sector %-5s 5d=%s", sym, _pp(r.get("weekly_pct")))
        else:
            failures.append(sym)
        time.sleep(CHUNK_DELAY)

    # Commodity proxies
    for sym, name, proxy_for in COMMODITY_PROXIES:
        r = collect_commodity(sym, name, proxy_for, friday)
        if r:
            rows.append(r)
            log.info("commod %-4s (%s) weekly=%s", sym, proxy_for, _pp(r.get("weekly_pct")))
        else:
            failures.append(sym)
        time.sleep(CHUNK_DELAY)

    # Treasuries (FRED)
    tre = collect_treasuries(friday)
    if tre:
        rows.extend(tre)
        for r in tre:
            log.info("treasury %-6s yield=%s bp=%s", r["symbol"], _fp(r.get("level"), 3), r.get("weekly_bp"))
    else:
        failures.append("treasuries")
        log.warning("treasuries — no data (Schwab $TNX/$TYX + FRED all failed)")
    if not any(r.get("symbol") == "DGS2" for r in tre):
        failures.append("DGS2-2Y")
        log.warning("2Y yield (FRED DGS2) missing — partial (best-effort series)")

    # Persist (idempotent via PRIMARY KEY upsert)
    for r in rows:
        upsert(conn, market_date, r, fetched_at)
    conn.commit()
    conn.close()
    log.info("Wrote %d rows to weekly_scorecard (market_date=%s)", len(rows), market_date)

    if args.output:
        emit_markdown(rows, friday, args.output)
        log.info("Wrote ground-truth markdown to %s", args.output)

    if failures:
        log.warning("Partial: %d series missing (%s)", len(failures), ", ".join(failures))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

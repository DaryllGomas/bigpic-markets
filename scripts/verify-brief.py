#!/usr/bin/env python3
"""
verify-brief.py — Schwab-powered fact-checker for Morning Brief markdown.

Reads the compiled brief, extracts ticker symbols and price/move claims,
pulls real-time quotes from the local Schwab API, and corrects discrepancies.

Usage: python3 verify-brief.py <path-to-brief.md>
"""

import re
import sys
import json
import time
import sqlite3
import urllib.request
from pathlib import Path

SCHWAB_API = "http://192.168.10.60:8000/api/quotes"
CHUNK_SIZE = 8
CHUNK_DELAY = 1.0  # seconds between API calls

# Thresholds for flagging discrepancies
PRICE_THRESHOLD = 0.02   # 2% for stock prices
MOVE_THRESHOLD = 2.0     # 2 percentage points for % moves
MACRO_THRESHOLD = 0.005  # 0.5% for index/futures levels

# Map Pre-Market Snapshot labels → Schwab symbols
SNAPSHOT_MAP = {
    "S&P 500 Futures": "/ES",
    "Nasdaq 100 Futures": "/NQ",
    "Dow Futures": "/YM",
    "Russell 2000 Futures": "/RTY",
    "10Y Yield": "$TNX",
    "WTI Crude": "/CL",
    "Gold": "/GC",
    # Not available on Schwab:
    "Brent Crude": None,
    "Bitcoin": None,      # IBIT is a proxy, not direct BTC price
    "Ethereum": None,
    "DXY": None,
    "2Y Yield": None,
    "30Y Yield": None,
    "2s/10s Spread": None,
}

# Always look up these macro symbols
MACRO_SYMBOLS = [
    "$SPX", "$NDX", "$DJI", "$RUT", "$VIX", "$TNX", "$SOX",
    "/ES", "/NQ", "/YM", "/RTY", "/GC", "/CL", "/ZN", "/ZB",
    "IBIT",
]


def fetch_quotes(symbols):
    """Fetch quotes from Schwab API in small chunks with delays."""
    all_quotes = {}
    symbols = list(symbols)
    chunks = [symbols[i:i + CHUNK_SIZE] for i in range(0, len(symbols), CHUNK_SIZE)]

    for i, chunk in enumerate(chunks):
        if i > 0:
            time.sleep(CHUNK_DELAY)

        sym_str = ",".join(chunk)
        url = f"{SCHWAB_API}?symbols={sym_str}"
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())

            # Single-symbol endpoint returns differently than multi-symbol
            if "quotes" in data:
                for sym, quote in data["quotes"].items():
                    if sym != "errors" and isinstance(quote, dict):
                        all_quotes[sym] = quote
            elif "quote" in data:
                all_quotes[chunk[0]] = data["quote"]
        except Exception as e:
            print(f"  WARNING: chunk {i + 1} failed ({chunk}): {e}")

    return all_quotes


def resolve_quote(quotes, symbol):
    """Find a quote, handling futures contract month suffixes (e.g. /ES → /ESH26)."""
    if symbol in quotes:
        return quotes[symbol]
    # Try matching prefix for futures (e.g. /ES matches /ESH26)
    for sym, q in quotes.items():
        if sym.startswith(symbol) and len(sym) > len(symbol):
            return q
    return None


def get_price(quote):
    """Extract the best available price from a quote."""
    return quote.get("lastPrice") or quote.get("mark") or quote.get("price")


def get_change_pct(quote):
    """Extract percentage change from a quote."""
    pct = quote.get("futurePercentChange") or quote.get("netPercentChange")
    if pct is not None:
        return pct
    last = get_price(quote)
    prev = quote.get("closePrice") or quote.get("previousClose")
    if last and prev and prev != 0:
        return ((last - prev) / prev) * 100
    return None


def parse_number(s):
    """Parse a number from markdown, stripping ~, $, commas, %, bold markers."""
    if not s:
        return None
    s = s.strip().replace(",", "").replace("~", "").replace("$", "")
    s = s.replace("*", "").replace("%", "").strip()
    # Skip ranges like "+15-23"
    if re.match(r"^[+-]?\d+\.?\d*\s*-\s*\d+\.?\d*$", s):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def fmt_price(price, reference=None):
    """Format a price to match the style of the reference string."""
    if price >= 10000:
        return f"{price:,.0f}"
    elif price >= 100:
        return f"{price:,.0f}"
    elif price >= 1:
        return f"{price:.2f}"
    else:
        return f"{price:.4f}"


# ── Table parsing ────────────────────────────────────────────────────────────


def find_snapshot_section(md_text):
    """Find the Pre-Market Snapshot table section."""
    m = re.search(r"## Pre-Market Snapshot\s*\n(.*?)(?=\n---|\n##)", md_text, re.DOTALL)
    return m.group(1) if m else ""


def find_table_rows(section_text):
    """Yield non-header, non-separator table rows."""
    for line in section_text.split("\n"):
        line = line.strip()
        if not line.startswith("|"):
            continue
        if re.match(r"\|\s*[-:]+", line):
            continue
        cols = [c.strip() for c in line.split("|")[1:-1]]
        if len(cols) >= 2:
            yield line, cols


def extract_tickers_from_tables(md_text):
    """Extract all stock ticker symbols mentioned in any markdown table."""
    tickers = set()
    header_words = {
        "Ticker", "Date", "Time", "Speaker", "Sector", "Instrument",
        "Event", "Release", "Priority", "Result", "Key", "Impact",
        "Signal", "Catalyst", "Tier", "Consensus", "Prior",
    }
    for line in md_text.split("\n"):
        line = line.strip()
        if not line.startswith("|"):
            continue
        # Find uppercase 1-5 letter words that look like tickers
        for m in re.finditer(r"\*{0,2}([A-Z]{1,5})\*{0,2}", line):
            sym = m.group(1)
            if sym not in header_words and len(sym) >= 2:
                tickers.add(sym)
    return tickers


# ── Correction logic ─────────────────────────────────────────────────────────


def check_snapshot(md_text, quotes):
    """Check Pre-Market Snapshot table claims against Schwab data."""
    corrections = []
    section = find_snapshot_section(md_text)
    if not section:
        return corrections

    for line, cols in find_table_rows(section):
        if len(cols) < 3:
            continue
        label = cols[0].replace("*", "").strip()
        level_str = cols[1].strip()
        change_str = cols[2].strip()

        schwab_sym = SNAPSHOT_MAP.get(label)
        if not schwab_sym:
            continue

        quote = resolve_quote(quotes, schwab_sym)
        if not quote:
            continue

        actual_price = get_price(quote)
        actual_change = get_change_pct(quote)
        if actual_price is None:
            continue

        # Special: $TNX → yield (reported as price * 0.1)
        if schwab_sym == "$TNX":
            actual_yield = actual_price / 10
            claimed_yield = parse_number(level_str)
            if claimed_yield and abs(claimed_yield - actual_yield) / actual_yield > MACRO_THRESHOLD:
                new_val = f"{actual_yield:.3f}%"
                corrections.append({
                    "line": line,
                    "old": level_str,
                    "new": new_val,
                    "desc": f"{label}: {level_str} → {new_val}",
                })
            continue

        # Normal futures/index level
        claimed = parse_number(level_str)
        if claimed and actual_price:
            pct_off = abs(claimed - actual_price) / actual_price
            if pct_off > MACRO_THRESHOLD:
                new_val = fmt_price(actual_price)
                corrections.append({
                    "line": line,
                    "old": level_str,
                    "new": new_val,
                    "desc": f"{label}: {level_str} → {new_val} ({pct_off:.1%} off)",
                })

        # Change percentage
        claimed_change = parse_number(change_str)
        if claimed_change is not None and actual_change is not None:
            if abs(claimed_change - actual_change) > MOVE_THRESHOLD:
                new_val = f"{actual_change:+.2f}%"
                corrections.append({
                    "line": line,
                    "old": change_str,
                    "new": new_val,
                    "desc": f"{label} change: {change_str} → {new_val}",
                })

    return corrections


def find_section(md_text, heading_pattern):
    """Extract table rows from a markdown section identified by heading."""
    m = re.search(heading_pattern + r"\s*\n(.*?)(?=\n###|\n---|\n##|\Z)", md_text, re.DOTALL)
    if not m:
        return []
    rows = []
    for line in m.group(1).split("\n"):
        line = line.strip()
        if not line.startswith("|") or re.match(r"\|\s*[-:]", line):
            continue
        cols = [c.strip() for c in line.split("|")[1:-1]]
        if len(cols) >= 3:
            rows.append((line, cols))
    return rows


def extract_ticker(col_text):
    """Extract a ticker symbol from a table cell, stripping bold markers."""
    m = re.match(r"\*{0,2}([A-Z]{2,5})\*{0,2}$", col_text.strip())
    return m.group(1) if m else None


def is_clean_daily_move(cell_text):
    """Check if a cell contains a clean daily move like +7% or -1.5%, not a range or narrative."""
    clean = cell_text.replace("*", "").strip()
    # Skip blanks, text, and dashes
    if clean in ("", "—", "Flat", "Steady", "Beat"):
        return False
    # Must be a simple +X% or -X% pattern (not a range, not followed by YoY/ATH)
    if re.match(r"^[+-]\d+\.?\d*%$", clean):
        return True
    return False


def check_movers_table(md_text, quotes):
    """Check the ### Movers table: col 2 (Price) and col 3 (Move) only."""
    corrections = []
    rows = find_section(md_text, r"### Movers")

    for line, cols in rows:
        if len(cols) < 4:
            continue

        # Col 0: Ticker, Col 1: Sector, Col 2: Price, Col 3: Move, Col 4: Catalyst
        ticker = extract_ticker(cols[0])
        if not ticker:
            continue
        quote = quotes.get(ticker)
        if not quote:
            continue

        actual_price = get_price(quote)
        actual_change = get_change_pct(quote)

        # Check Price column (col 2)
        price_col = cols[2].replace("*", "").strip()
        price_match = re.search(r"~?\$([0-9,]+\.?\d*)", price_col)
        if price_match and actual_price:
            claimed = parse_number(price_match.group(1))
            if claimed and claimed > 1:
                pct_off = abs(claimed - actual_price) / actual_price
                if pct_off > PRICE_THRESHOLD:
                    old_str = price_match.group(0)
                    prefix = "~$" if old_str.startswith("~") else "$"
                    new_str = f"{prefix}{fmt_price(actual_price)}"
                    corrections.append({
                        "line": line,
                        "old": old_str,
                        "new": new_str,
                        "desc": f"{ticker}: {old_str} → {new_str} ({pct_off:.1%} off)",
                    })

        # Check Move column (col 3) — only clean daily moves
        move_col = cols[3]
        if is_clean_daily_move(move_col) and actual_change is not None:
            clean = move_col.replace("*", "").strip()
            move_match = re.match(r"([+-]\d+\.?\d*)%", clean)
            if move_match:
                claimed_move = float(move_match.group(1))
                diff = abs(claimed_move - actual_change)
                if diff > MOVE_THRESHOLD:
                    old_str = move_match.group(0)
                    new_str = f"{actual_change:+.1f}%"
                    corrections.append({
                        "line": line,
                        "old": old_str,
                        "new": new_str,
                        "desc": f"{ticker} move: {old_str} → {new_str}",
                    })

    return corrections


def check_technicals_table(md_text, quotes, already_corrected):
    """Check ### Key Technical Levels table: col 1 (Current) only."""
    corrections = []
    rows = find_section(md_text, r"### Key Technical Levels")

    for line, cols in rows:
        if len(cols) < 4:
            continue

        # Col 0: Ticker, Col 1: Current, Col 2: Support, Col 3: Resistance, Col 4: Signal
        ticker = extract_ticker(cols[0])
        if not ticker or ticker in already_corrected:
            continue
        quote = quotes.get(ticker)
        if not quote:
            continue

        actual_price = get_price(quote)
        if not actual_price:
            continue

        # Check Current column (col 1) only
        current_col = cols[1].replace("*", "").strip()
        price_match = re.search(r"~?\$([0-9,]+\.?\d*)", current_col)
        if price_match:
            claimed = parse_number(price_match.group(1))
            if claimed and claimed > 1:
                pct_off = abs(claimed - actual_price) / actual_price
                if pct_off > PRICE_THRESHOLD:
                    old_str = price_match.group(0)
                    prefix = "~$" if old_str.startswith("~") else "$"
                    new_str = f"{prefix}{fmt_price(actual_price)}"
                    corrections.append({
                        "line": line,
                        "old": old_str,
                        "new": new_str,
                        "desc": f"{ticker}: {old_str} → {new_str} ({pct_off:.1%} off)",
                    })

    return corrections


def apply_corrections(md_text, corrections):
    """Apply corrections to the markdown, scoped to the specific line."""
    lines = md_text.split("\n")
    applied = []

    for corr in corrections:
        target_line = corr["line"]
        for i, line in enumerate(lines):
            if line.strip() == target_line:
                new_line = line.replace(corr["old"], corr["new"], 1)
                if new_line != line:
                    lines[i] = new_line
                    applied.append(corr)
                    # Update target for any subsequent corrections on the same line
                    corr["line"] = new_line.strip()
                break

    return "\n".join(lines), applied


# ── Database cross-checks ─────────────────────────────────────────────────────

DB_PATH = Path.home() / "projects" / "bigpic-markets" / "data" / "market.db"


def get_db_connection(market_date):
    """Connect to the market database if it exists."""
    if not DB_PATH.exists():
        return None
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    # Verify we have data for this date
    count = conn.execute(
        "SELECT COUNT(*) FROM quotes WHERE market_date = ?", (market_date,)
    ).fetchone()[0]
    if count == 0:
        conn.close()
        return None
    return conn


def extract_market_date(md_path):
    """Extract market date from filename like 2026-02-12_Thu.md."""
    m = re.match(r"(\d{4}-\d{2}-\d{2})", md_path.stem)
    return m.group(1) if m else None


def check_calendar_fabrication(md_text, conn, market_date):
    """Flag any 'Actual' values in the brief for events where DB shows actual is NULL."""
    corrections = []
    # Get unreleased events from DB
    unreleased = conn.execute(
        "SELECT event_name FROM economic_events "
        "WHERE market_date = ? AND actual IS NULL",
        (market_date,),
    ).fetchall()
    unreleased_names = [r["event_name"].upper() for r in unreleased]

    if not unreleased_names:
        return corrections

    # Find calendar table in the brief
    calendar_section = re.search(
        r"## (?:Today's Calendar|Economic Calendar)\s*\n(.*?)(?=\n---|\n##)",
        md_text, re.DOTALL,
    )
    if not calendar_section:
        return corrections

    for line in calendar_section.group(1).split("\n"):
        line = line.strip()
        if not line.startswith("|") or re.match(r"\|\s*[-:]", line):
            continue
        cols = [c.strip() for c in line.split("|")[1:-1]]
        if len(cols) < 5:
            continue

        # Check if this event is in our unreleased list
        event_name = cols[1].replace("*", "").strip().upper() if len(cols) > 1 else ""
        actual_col = cols[-1].replace("*", "").strip() if cols else ""

        for unreleased_name in unreleased_names:
            if unreleased_name in event_name or event_name in unreleased_name:
                # This event hasn't been released — check if brief has an actual value
                if actual_col and actual_col not in ("—", "-", "Pending", "N/A", "TBD", ""):
                    # Fabricated actual value — strip it
                    corrections.append({
                        "line": line,
                        "old": actual_col,
                        "new": "Pending",
                        "desc": f"FABRICATION: {event_name} actual '{actual_col}' → 'Pending' (not released)",
                    })
                break

    return corrections


def check_earnings_fabrication(md_text, conn, market_date):
    """Flag any fabricated EPS actual values for earnings not yet reported."""
    corrections = []
    # Get earnings with NULL actual from DB
    unreported = conn.execute(
        "SELECT symbol FROM earnings "
        "WHERE market_date = ? AND eps_actual IS NULL",
        (market_date,),
    ).fetchall()
    unreported_syms = {r["symbol"].upper() for r in unreported}

    if not unreported_syms:
        return corrections

    # Find earnings tables in the brief
    for section_pattern in [r"### (?:Reporting Today|Earnings)", r"## (?:Earnings)"]:
        m = re.search(section_pattern + r"\s*\n(.*?)(?=\n---|\n##|\n###|\Z)", md_text, re.DOTALL)
        if not m:
            continue
        for line in m.group(1).split("\n"):
            line = line.strip()
            if not line.startswith("|") or re.match(r"\|\s*[-:]", line):
                continue
            cols = [c.strip() for c in line.split("|")[1:-1]]
            if len(cols) < 3:
                continue
            ticker = cols[0].replace("*", "").strip().upper()
            if ticker in unreported_syms:
                # Check last column for actual EPS
                actual_col = cols[-1].replace("*", "").strip()
                if actual_col and actual_col not in ("—", "-", "Pending", "N/A", "TBD", ""):
                    corrections.append({
                        "line": line,
                        "old": actual_col,
                        "new": "—",
                        "desc": f"FABRICATION: {ticker} EPS actual '{actual_col}' → '—' (not reported)",
                    })

    return corrections


def check_quotes_vs_database(md_text, conn, market_date):
    """Cross-check price claims against collected database values."""
    corrections = []

    # Build a map of best quotes from DB (prefer schwab)
    db_quotes = {}
    rows = conn.execute(
        "SELECT symbol, price, change_pct, source, "
        "CASE source WHEN 'schwab' THEN 1 WHEN 'stooq' THEN 2 "
        "WHEN 'fred' THEN 3 WHEN 'coingecko' THEN 4 ELSE 9 END as prio "
        "FROM quotes WHERE market_date = ? AND price IS NOT NULL "
        "ORDER BY symbol, prio",
        (market_date,),
    ).fetchall()

    for row in rows:
        sym = row["symbol"]
        if sym not in db_quotes:
            db_quotes[sym] = {"price": row["price"], "change_pct": row["change_pct"], "source": row["source"]}

    # Check snapshot table prices against DB
    snapshot = find_snapshot_section(md_text)
    if snapshot:
        # Map briefing labels to DB symbols
        label_to_db = {
            "S&P 500 Futures": "/ES", "Nasdaq 100 Futures": "/NQ",
            "Dow Futures": "/YM", "Russell 2000 Futures": "/RTY",
            "WTI Crude": "/CL", "Gold": "/GC", "Brent Crude": "/BZ",
            "Bitcoin": "BTC", "Ethereum": "ETH",
            "DXY": "DXY", "FTSE 100": "FTSE", "Kospi": "KOSPI",
        }
        for line, cols in find_table_rows(snapshot):
            if len(cols) < 3:
                continue
            label = cols[0].replace("*", "").strip()
            level_str = cols[1].strip()

            # Try exact label match, then prefix match
            db_sym = label_to_db.get(label)
            if not db_sym:
                continue

            # Find in DB (including prefix match for futures)
            db_entry = db_quotes.get(db_sym)
            if not db_entry:
                for sym, entry in db_quotes.items():
                    if sym.startswith(db_sym) and len(sym) > len(db_sym):
                        db_entry = entry
                        break
            if not db_entry:
                continue

            claimed = parse_number(level_str)
            actual = db_entry["price"]
            if claimed and actual and actual != 0:
                pct_off = abs(claimed - actual) / actual
                if pct_off > MACRO_THRESHOLD:
                    new_val = fmt_price(actual)
                    corrections.append({
                        "line": line,
                        "old": level_str,
                        "new": new_val,
                        "desc": f"DB CHECK: {label}: {level_str} → {new_val} (db={actual:.2f}, {pct_off:.1%} off)",
                    })

    return corrections


def check_completeness(md_text, conn, market_date):
    """Warn if brief has data that the database doesn't — possible fabrication."""
    warnings = []

    # Check: if DB shows 0 economic events but brief has calendar entries
    db_events = conn.execute(
        "SELECT COUNT(*) FROM economic_events WHERE market_date = ?", (market_date,)
    ).fetchone()[0]

    calendar_section = re.search(
        r"## (?:Today's Calendar|Economic Calendar)\s*\n(.*?)(?=\n---|\n##)",
        md_text, re.DOTALL,
    )
    if calendar_section:
        brief_event_rows = 0
        for line in calendar_section.group(1).split("\n"):
            if line.strip().startswith("|") and not re.match(r"\|\s*[-:]", line.strip()):
                # Skip header row
                cols = [c.strip() for c in line.split("|")[1:-1]]
                if len(cols) >= 3 and cols[0] not in ("Time", "Time (ET)"):
                    brief_event_rows += 1

        if db_events == 0 and brief_event_rows > 0:
            warnings.append(
                f"SUSPECT: Brief has {brief_event_rows} calendar events but database has 0. "
                f"Events may be fabricated."
            )

    return warnings


# ── Main ─────────────────────────────────────────────────────────────────────


def main():
    if len(sys.argv) < 2:
        print("Usage: verify-brief.py <path-to-brief.md>")
        sys.exit(1)

    md_path = Path(sys.argv[1])
    if not md_path.exists():
        print(f"ERROR: File not found: {md_path}")
        sys.exit(1)

    md_text = md_path.read_text()
    print(f"=== Fact-Check: {md_path.name} ===")

    # ── Part 1: Live Schwab checks (existing) ──
    print("\n--- Live Schwab API checks ---")
    tickers = extract_tickers_from_tables(md_text)
    all_symbols = set(MACRO_SYMBOLS) | tickers
    all_symbols = sorted(all_symbols)
    print(f"  Looking up {len(all_symbols)} symbols...")

    quotes = fetch_quotes(all_symbols)
    print(f"  Got quotes for {len(quotes)} symbols")

    snapshot_corrections = check_snapshot(md_text, quotes)
    movers_corrections = check_movers_table(md_text, quotes)
    corrected_tickers = {c["desc"].split(":")[0] for c in movers_corrections}
    technicals_corrections = check_technicals_table(md_text, quotes, corrected_tickers)
    all_corrections = snapshot_corrections + movers_corrections + technicals_corrections

    # ── Part 2: Database cross-checks (new) ──
    market_date = extract_market_date(md_path)
    db_corrections = []
    db_warnings = []

    if market_date:
        conn = get_db_connection(market_date)
        if conn:
            print(f"\n--- Database cross-checks (market_date={market_date}) ---")
            cal_fabrications = check_calendar_fabrication(md_text, conn, market_date)
            earn_fabrications = check_earnings_fabrication(md_text, conn, market_date)
            db_quote_corrections = check_quotes_vs_database(md_text, conn, market_date)
            db_warnings = check_completeness(md_text, conn, market_date)

            db_corrections = cal_fabrications + earn_fabrications + db_quote_corrections

            if db_corrections:
                print(f"  {len(db_corrections)} database corrections:")
                for c in db_corrections:
                    print(f"    {c['desc']}")
            else:
                print("  No database discrepancies found")

            if db_warnings:
                for w in db_warnings:
                    print(f"  WARNING: {w}")

            conn.close()
        else:
            print(f"\n--- Database cross-checks: skipped (no data for {market_date}) ---")
    else:
        print("\n--- Database cross-checks: skipped (could not parse date from filename) ---")

    # ── Apply all corrections ──
    all_corrections = all_corrections + db_corrections

    if all_corrections:
        print(f"\n  {len(all_corrections)} total corrections needed:")
        for c in all_corrections:
            print(f"    {c['desc']}")

        corrected, applied = apply_corrections(md_text, all_corrections)
        if applied:
            md_path.write_text(corrected)
            print(f"\n  {len(applied)} corrections written to {md_path.name}")
        else:
            print("\n  WARNING: corrections identified but could not be applied")
    else:
        print("\n  All claims within tolerance — no corrections needed")

    print("=== Fact-check complete ===")


if __name__ == "__main__":
    main()

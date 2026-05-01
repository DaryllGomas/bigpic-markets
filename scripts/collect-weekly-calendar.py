#!/usr/bin/env python3
"""
collect-weekly-calendar.py — Pre-collect economic calendar for Eagle Eye Week Ahead.

Fetches upcoming week's economic events from multiple sources and writes a
structured markdown file that Eagle Eye agents use as ground truth.

Data sources (priority order):
  1. Calendar API with date parameter (per-day queries)
  2. Forex Factory next-week calendar (HTML scrape)
  3. SQLite DB historical data (fallback)

Usage:
    python3 collect-weekly-calendar.py --start 2026-03-23 --end 2026-03-27 \
        --output /path/to/next_week_calendar.md --db /path/to/market.db

Exit codes:
    0 - Full calendar collected (API or Forex Factory)
    1 - Partial (some sources failed, but usable data)
    2 - Fallback only (DB historical patterns used)
    3 - Total failure (no data collected)

Dependencies: Python stdlib only
"""

import argparse
import datetime
import json
import logging
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

# ── Configuration ─────────────────────────────────────────────────────────────

ECON_CALENDAR_BASE = "http://192.168.10.60:3000/api/calendar"
FOREX_FACTORY_URL = "https://www.forexfactory.com/calendar?week=next"
USER_AGENT = "BigPic-Markets/1.0"
TIMEOUT = 10
MAX_RETRIES = 2

# Major releases — if absent from the week, explicitly note it
HEAVY_EVENTS = [
    ("FOMC", ["FOMC", "Fed Funds Rate", "Federal Funds"]),
    ("Nonfarm Payrolls", ["Nonfarm Payrolls", "NFP", "Employment Situation"]),
    ("CPI Report", ["CPI", "Consumer Price Index"]),
    ("GDP Report", ["GDP", "Gross Domestic Product"]),
    ("PCE Price Index", ["PCE", "Personal Consumption"]),
    ("PPI Report", ["PPI", "Producer Price Index"]),
    ("Michigan Consumer Sentiment", ["Michigan", "UoM Consumer Sentiment",
                                     "Revised UoM Consumer Sentiment"]),
]

log = logging.getLogger("weekly-calendar")


# -- Timezone conversion -------------------------------------------------------

def utc_to_et(time_str):
    """Convert a UTC HH:MM time string to Eastern Time.

    The calendar API stores event times in UTC. This converts to ET
    (EST = UTC-5, EDT = UTC-4) using the current offset.
    Returns the converted time string, or the original if parsing fails.
    """
    if not time_str or time_str in ("", "—", "—"):
        return time_str
    try:
        from zoneinfo import ZoneInfo
        from datetime import datetime, date

        match = re.match(r"^(\d{1,2}):(\d{2})$", time_str.strip())
        if not match:
            return time_str

        hour, minute = int(match.group(1)), int(match.group(2))
        utc_dt = datetime(date.today().year, date.today().month,
                         date.today().day, hour, minute,
                         tzinfo=ZoneInfo("UTC"))
        et_dt = utc_dt.astimezone(ZoneInfo("America/New_York"))
        return et_dt.strftime("%-H:%M")
    except Exception:
        return time_str

# ── HTTP helpers ──────────────────────────────────────────────────────────────


def fetch_url(url, timeout=TIMEOUT, retries=MAX_RETRIES, headers=None):
    """Fetch URL with retry logic. Returns bytes."""
    hdrs = {"User-Agent": USER_AGENT}
    if headers:
        hdrs.update(headers)
    last_error = None
    for attempt in range(retries + 1):
        if attempt > 0:
            time.sleep(2 ** (attempt - 1))
        try:
            req = urllib.request.Request(url, headers=hdrs)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except Exception as e:
            last_error = e
            log.warning(f"  Attempt {attempt + 1} failed: {e}")
    raise last_error


def fetch_json(url, timeout=TIMEOUT, retries=MAX_RETRIES):
    """Fetch JSON endpoint. Returns parsed dict/list."""
    data = fetch_url(url, timeout, retries, {"Accept": "application/json"})
    return json.loads(data)


# ── Source 1: Calendar API ────────────────────────────────────────────────────


def fetch_api_upcoming(days=7):
    """Fetch upcoming events from the calendar API's /upcoming endpoint.

    The Intel API now supports /api/calendar/upcoming?days=N which returns
    forward-looking events from both Forex Factory and FRED (with corrected
    per-release dates for 16 major releases).
    """
    url = f"{ECON_CALENDAR_BASE}/upcoming?days={days}"
    log.info(f"  Fetching upcoming calendar: {url}")
    data = fetch_json(url)
    items = _extract_events(data)
    log.info(f"  API returned {len(items)} upcoming events")
    return items


def fetch_api_today():
    """Fetch today's events from the calendar API."""
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    log.info(f"  Fetching today's calendar: {ECON_CALENDAR_BASE}/today")
    data = fetch_json(f"{ECON_CALENDAR_BASE}/today")
    items = _extract_events(data)
    for ev in items:
        if not ev.get("date"):
            ev["date"] = today_str
    log.info(f"  API returned {len(items)} events for {today_str}")
    return items


def _extract_events(data):
    """Normalize API response — handles list or dict with various keys."""
    if isinstance(data, list):
        items = data
    else:
        items = data.get("data", data.get("events",
                data.get("calendar", [])))
    if not isinstance(items, list):
        return []

    normalized = []
    for ev in items:
        normalized.append({
            "date": (ev.get("event_date") or ev.get("date")
                     or ev.get("market_date", "")),
            "time": ev.get("event_time") or ev.get("time", ""),
            "name": (ev.get("event_name") or ev.get("name")
                     or ev.get("event", "Unknown")),
            "impact": (ev.get("impact_level") or ev.get("impact", ""))
                      .strip().lower(),
            "forecast": ev.get("forecast") or ev.get("consensus", ""),
            "previous": ev.get("previous") or ev.get("prior", ""),
        })
    return normalized


# ── Source 2: Forex Factory scrape ────────────────────────────────────────────


class FFCalendarParser(HTMLParser):
    """Minimal parser for Forex Factory's calendar HTML."""

    def __init__(self):
        super().__init__()
        self.events = []
        self._in_row = False
        self._in_cell = False
        self._cell_class = ""
        self._current = {}
        self._current_date = ""
        self._cells = []
        self._cell_text = ""

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        cls = attrs_dict.get("class", "")

        if tag == "tr" and "calendar__row" in cls and "calendar_row" not in cls:
            self._in_row = True
            self._cells = []
            self._current = {}

        if tag == "td" and self._in_row:
            self._in_cell = True
            self._cell_class = cls
            self._cell_text = ""

        # Impact is often indicated by a span class
        if tag == "span" and self._in_cell and "calendar__impact-icon" in cls:
            if "high" in cls or "red" in cls:
                self._current["impact"] = "high"
            elif "medium" in cls or "ora" in cls or "orange" in cls:
                self._current["impact"] = "medium"
            elif "low" in cls or "yel" in cls or "yellow" in cls:
                self._current["impact"] = "low"

    def handle_data(self, data):
        if self._in_cell:
            self._cell_text += data.strip()

    def handle_endtag(self, tag):
        if tag == "td" and self._in_cell:
            self._in_cell = False
            cls = self._cell_class
            text = self._cell_text.strip()

            if "calendar__date" in cls and text:
                self._current_date = text
            if "calendar__time" in cls and text:
                self._current["time"] = text
            if "calendar__event" in cls and text:
                self._current["name"] = text
            if "calendar__forecast" in cls:
                self._current["forecast"] = text
            if "calendar__previous" in cls:
                self._current["previous"] = text
            if "calendar__currency" in cls:
                self._current["currency"] = text

        if tag == "tr" and self._in_row:
            self._in_row = False
            if self._current.get("name"):
                self._current.setdefault("date_raw", self._current_date)
                self._current.setdefault("impact", "low")
                self._current.setdefault("time", "")
                self._current.setdefault("forecast", "")
                self._current.setdefault("previous", "")
                self._current.setdefault("currency", "")
                self.events.append(self._current)


def fetch_forex_factory(start_date, end_date):
    """Scrape Forex Factory for next week's USD economic events."""
    log.info(f"  Scraping Forex Factory: {FOREX_FACTORY_URL}")
    html = fetch_url(FOREX_FACTORY_URL, timeout=15).decode("utf-8", errors="replace")

    parser = FFCalendarParser()
    parser.feed(html)

    # Filter to USD events only and map dates to our date range
    usd_events = [ev for ev in parser.events
                  if ev.get("currency", "").upper() in ("USD", "")]

    if not usd_events:
        raise RuntimeError("No USD events parsed from Forex Factory")

    # FF dates are like "Mon Mar 23" — resolve to full dates
    resolved = _resolve_ff_dates(usd_events, start_date, end_date)
    log.info(f"  Forex Factory: {len(resolved)} USD events for the week")
    return resolved


def _resolve_ff_dates(events, start_date, end_date):
    """Convert FF date strings (e.g., 'Mon Mar 23') to YYYY-MM-DD."""
    year = start_date.year
    resolved = []
    last_date = ""

    for ev in events:
        raw = ev.get("date_raw", "").strip()
        if raw:
            # Try parsing "Mon Mar 23" or "Mar 23" patterns
            for fmt in ("%a %b %d", "%b %d"):
                try:
                    parsed = datetime.datetime.strptime(raw, fmt).replace(year=year)
                    last_date = parsed.strftime("%Y-%m-%d")
                    break
                except ValueError:
                    continue

        if last_date:
            dt = datetime.datetime.strptime(last_date, "%Y-%m-%d").date()
            if start_date <= dt <= end_date:
                resolved.append({
                    "date": last_date,
                    "time": ev.get("time", ""),
                    "name": ev["name"],
                    "impact": ev.get("impact", "low"),
                    "forecast": ev.get("forecast", ""),
                    "previous": ev.get("previous", ""),
                })

    return resolved


# ── Source 3: DB historical fallback ──────────────────────────────────────────


def fetch_db_events(db_path, start_date, end_date):
    """Query the economic_events table for any forward data already collected."""
    if not db_path or not Path(db_path).exists():
        return []

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT market_date, event_time, event_name, impact, forecast, previous "
            "FROM economic_events "
            "WHERE market_date BETWEEN ? AND ? "
            "ORDER BY market_date, event_time",
            (start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")),
        ).fetchall()

        events = []
        for r in rows:
            events.append({
                "date": r["market_date"],
                "time": r["event_time"] or "",
                "name": r["event_name"],
                "impact": (r["impact"] or "").lower(),
                "forecast": r["forecast"] or "",
                "previous": r["previous"] or "",
            })
        log.info(f"  DB: {len(events)} events in range")
        return events
    finally:
        conn.close()


# ── Merge & deduplicate ──────────────────────────────────────────────────────


def merge_events(primary, secondary):
    """Merge two event lists, deduplicating by (date, name_normalized)."""
    seen = set()
    merged = []

    for ev in primary:
        key = (ev["date"], _normalize_name(ev["name"]))
        if key not in seen:
            seen.add(key)
            merged.append(ev)

    for ev in secondary:
        key = (ev["date"], _normalize_name(ev["name"]))
        if key not in seen:
            seen.add(key)
            merged.append(ev)

    # Sort by date then time
    merged.sort(key=lambda e: (e["date"], e.get("time", "") or "99:99"))
    return merged


def _normalize_name(name):
    """Lowercase, strip parentheticals, collapse whitespace."""
    name = re.sub(r"\(.*?\)", "", name).strip().lower()
    name = re.sub(r"\s+", " ", name)
    return name


# ── Notable absences ─────────────────────────────────────────────────────────


def find_absences(events):
    """Check which HEAVY_EVENTS are not present in the collected events."""
    all_names = " ".join(ev["name"] for ev in events).lower()
    absent = []
    for label, keywords in HEAVY_EVENTS:
        found = any(kw.lower() in all_names for kw in keywords)
        if not found:
            absent.append(label)
    return absent


# ── Markdown output ──────────────────────────────────────────────────────────


def write_calendar_md(events, absences, start_date, end_date, output_path,
                      sources, confidence):
    """Write the structured markdown calendar file."""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M PT")
    start_str = start_date.strftime("%B %-d")
    end_str = end_date.strftime("%B %-d, %Y")

    lines = [
        f"# Economic Calendar: {start_str}-{end_str}",
        f"Source: {' + '.join(sources)} | Collected: {now}",
        f"Confidence: {confidence.upper()}",
        "",
    ]

    # Group events by date
    current = start_date
    while current <= end_date:
        date_str = current.strftime("%Y-%m-%d")
        day_label = current.strftime("%A, %B %-d")
        day_events = [ev for ev in events if ev["date"] == date_str]

        lines.append(f"## {day_label}")

        if day_events:
            lines.append("")
            lines.append("| Time (ET) | Event | Impact |")
            lines.append("|-----------|-------|--------|")
            for ev in day_events:
                time_str = utc_to_et(ev.get("time", "") or "—")
                impact = (ev.get("impact", "") or "—").capitalize()
                name = ev["name"]
                lines.append(f"| {time_str} | {name} | {impact} |")
        else:
            lines.append("")
            lines.append("No major economic events scheduled.")

        lines.append("")
        current += datetime.timedelta(days=1)

    # Notable absences — critical for preventing hallucination
    lines.append("## NOTABLE ABSENCES")
    lines.append("")
    if absences:
        lines.append("These major releases are **NOT** scheduled this week:")
        for label in absences:
            lines.append(f"- {label}")
    else:
        lines.append("All major release types have events this week.")
    lines.append("")

    # Source notes
    lines.append("## DATA SOURCE NOTES")
    lines.append("")
    lines.append(f"- Sources queried: {', '.join(sources)}")
    lines.append(f"- Confidence level: {confidence}")
    lines.append(f"- Collected at: {now}")
    lines.append("- This file is the AUTHORITATIVE source for Week Ahead "
                 "economic data releases.")
    lines.append("- Do NOT override these dates with web search results.")
    lines.append("")

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text("\n".join(lines), encoding="utf-8")
    log.info(f"Wrote {output_path} ({len(events)} events, "
             f"{len(absences)} absences, confidence={confidence})")


# ── Main ─────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Collect next week's economic calendar for Eagle Eye")
    parser.add_argument("--start", required=True,
                        help="Start date (YYYY-MM-DD, typically Monday)")
    parser.add_argument("--end", required=True,
                        help="End date (YYYY-MM-DD, typically Friday)")
    parser.add_argument("--output", required=True,
                        help="Output markdown file path")
    parser.add_argument("--db", default=None,
                        help="Path to market.db (optional, for DB fallback)")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    start_date = datetime.datetime.strptime(args.start, "%Y-%m-%d").date()
    end_date = datetime.datetime.strptime(args.end, "%Y-%m-%d").date()

    log.info(f"Collecting economic calendar: {start_date} to {end_date}")

    all_events = []
    sources = []
    confidence = "low"
    days_ahead = (end_date - datetime.date.today()).days + 1

    # Source 1: Calendar API /upcoming (primary — FRED per-release + Forex Factory)
    # The Intel API now queries 16 individual FRED releases with corrected dates
    # and merges with Forex Factory for detail. This is the authoritative source.
    try:
        log.info("Source 1: Calendar API /upcoming (FRED + Forex Factory)")
        api_events = fetch_api_upcoming(days=max(days_ahead, 7))
        # Filter to our date range
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        api_events = [ev for ev in api_events
                      if start_str <= (ev.get("date") or "") <= end_str]
        if api_events:
            all_events = api_events
            sources.append("Calendar API")
            confidence = "high"
            log.info(f"  Filtered to {len(api_events)} events in range")
    except Exception as e:
        log.warning(f"  Calendar API /upcoming failed: {e}")

    # Source 2: SQLite DB (fallback — has per-day data from daily Morning Brief)
    if not all_events:
        try:
            log.info("Source 2: SQLite DB (daily-collected calendar data)")
            db_events = fetch_db_events(args.db, start_date, end_date)
            if db_events:
                all_events = db_events
                sources.append("SQLite DB")
                confidence = "medium"
        except Exception as e:
            log.warning(f"  DB query failed: {e}")

    # Source 3: Forex Factory direct scrape (last resort)
    if not all_events:
        try:
            log.info("Source 3: Forex Factory direct scrape")
            ff_events = fetch_forex_factory(start_date, end_date)
            if ff_events:
                all_events = ff_events
                sources.append("Forex Factory")
                confidence = "medium"
        except Exception as e:
            log.warning(f"  Forex Factory failed: {e}")

    if not all_events:
        log.error("All sources failed — no calendar data collected")
        # Write an empty calendar with warning
        write_calendar_md([], find_absences([]), start_date, end_date,
                          args.output, ["none"], "none")
        return 3

    absences = find_absences(all_events)
    write_calendar_md(all_events, absences, start_date, end_date,
                      args.output, sources, confidence)

    # Exit code based on confidence
    if confidence == "high":
        return 0
    elif confidence == "medium":
        return 1
    else:
        return 2


if __name__ == "__main__":
    sys.exit(main())

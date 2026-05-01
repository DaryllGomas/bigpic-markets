#!/usr/bin/env python3
"""
collect-market-data.py — Deterministic data collection for Morning Brief.

Hits all vetted APIs and RSS feeds, stores in SQLite, generates briefing file.
No web searching. No hallucination possible.

Usage:
    python3 collect-market-data.py              # Full collection + briefing file
    python3 collect-market-data.py --cleanup    # Prune old data + VACUUM
    python3 collect-market-data.py --briefing-only  # Regenerate briefing from existing DB
    python3 collect-market-data.py --date 2026-02-12  # Override market date

Exit codes:
    0 - Success (all critical data collected)
    1 - Partial (some sources failed, brief is usable)
    2 - Failed (critical data missing, brief not generated)

Dependencies: Python stdlib only
"""

import sqlite3
import urllib.request
import urllib.error
import json
import csv
import gzip
import io
import xml.etree.ElementTree as ET
import time
import datetime
import logging
import statistics
import os
import sys
import re


def utc_to_et(time_str):
    """Convert UTC HH:MM to Eastern Time. Calendar API stores UTC."""
    if not time_str or time_str in ("", "\u2014"):
        return time_str
    try:
        from zoneinfo import ZoneInfo
        from datetime import datetime, date as date_mod
        match = re.match(r"^(\d{1,2}):(\d{2})$", time_str.strip())
        if not match:
            return time_str
        hour, minute = int(match.group(1)), int(match.group(2))
        utc_dt = datetime(date_mod.today().year, date_mod.today().month,
                         date_mod.today().day, hour, minute,
                         tzinfo=ZoneInfo("UTC"))
        et_dt = utc_dt.astimezone(ZoneInfo("America/New_York"))
        return et_dt.strftime("%-H:%M")
    except Exception:
        return time_str

import subprocess
from pathlib import Path
from email.utils import parsedate_to_datetime

# ── Configuration ──────────────────────────────────────────────────────────────

BASE_DIR = Path.home() / "projects" / "bigpic-markets"
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "market.db"
LOG_DIR = DATA_DIR / "logs"
RESEARCH_DIR = BASE_DIR / "research"

SCHWAB_BASE = "http://192.168.10.60:8000"
ECON_CALENDAR_URL = "http://192.168.10.60:3000/api/calendar/today"
COINGECKO_URL = (
    "https://api.coingecko.com/api/v3/simple/price"
    "?ids=bitcoin,ethereum&vs_currencies=usd&include_24hr_change=true"
)
FRED_BASE = "https://fred.stlouisfed.org/graph/fredgraph.csv"

FAILURE_EMAIL = "daryll@bigpicsolutions.com"

SCHWAB_TIMEOUT = 8
EXTERNAL_TIMEOUT = 15
RSS_TIMEOUT = 10
MAX_RETRIES = 2
QUOTE_CHUNK_SIZE = 15
CHUNK_DELAY = 0.5  # 0.5s between light Schwab calls (quotes, SMA200, earnings)
TECH_DELAY = 1.0   # 1.0s between heavy Schwab calls (technicals)
YAHOO_DELAY = 2.0

ANOMALY_Z_THRESHOLD = 3.0
CROSS_VALIDATION_THRESHOLD = 0.005  # 0.5%

RETENTION_DAYS = {
    "quotes": 90, "technicals": 90, "anomalies": 90,
    "headlines": 14, "movers": 30, "levels": 30,
    "opus_tickers": 30, "opus_movers": 30, "opus_themes": 30,
    "opus_econ_events": 30, "opus_fed_signals": 30, "opus_sentiment": 30,
    "collections": 365, "source_health": 365,
    "cross_validations": 90, "economic_events": 90,
    "earnings": 90, "market_context": 90,
}

# ── Symbol Configuration ───────────────────────────────────────────────────────

SCHWAB_CORE = [
    # US Indices
    "$SPX", "$COMPX", "$DJI", "$RUT",
    # Volatility
    "$VIX",
    # Treasuries (raw value ÷ 10 = yield)
    "$TNX", "$TYX", "$IRX",
    # International
    "$N225", "$DAX", "$HSI", "$FCHI",
    # Commodities (root symbols — API resolves contract month)
    "/CL", "/BZ", "/GC",
    # Futures
    "/ES", "/NQ", "/YM", "/RTY",
    # ETF proxies
    "UUP", "FEZ", "IEV", "EWA",
]

# Human-readable names for briefing file
SYMBOL_NAMES = {
    "$SPX": "S&P 500", "$COMPX": "Nasdaq Composite", "$DJI": "Dow Jones",
    "$RUT": "Russell 2000", "$VIX": "VIX",
    "$TNX": "10Y Yield", "$TYX": "30Y Yield",
    "$N225": "Nikkei 225", "$DAX": "DAX", "$HSI": "Hang Seng", "$FCHI": "CAC 40",
    "/CL": "WTI Crude", "/BZ": "Brent Crude", "/GC": "Gold",
    "/ES": "S&P 500 Futures", "/NQ": "Nasdaq 100 Futures",
    "/YM": "Dow Futures", "/RTY": "Russell 2000 Futures",
    "UUP": "Dollar (UUP)", "FEZ": "Europe (FEZ)", "IEV": "Europe Broad (IEV)",
    "EWA": "Australia (EWA)",
    "BTC": "Bitcoin", "ETH": "Ethereum",
    "FTSE": "FTSE 100", "KOSPI": "Kospi", "DXY": "DXY",
    "DGS2": "2Y Yield", "DGS10": "10Y Yield", "DGS30": "30Y Yield",
    "SPY": "SPY", "QQQ": "QQQ", "IWM": "IWM", "DIA": "DIA",
}

STOOQ_SYMBOLS = {
    "FTSE": {"url": "https://stooq.com/q/l/?s=^ukx&f=sd2t2ohlcv&h&e=csv", "name": "FTSE 100"},
    "KOSPI": {"url": "https://stooq.com/q/l/?s=^kospi&f=sd2t2ohlcv&h&e=csv", "name": "Kospi"},
    "DXY": {"url": "https://stooq.com/q/l/?s=dx.f&f=sd2t2ohlcv&h&e=csv", "name": "DXY"},
}

FRED_SERIES = {"DGS2": "2Y Treasury"}

YAHOO_BACKUP = {
    "^FTSE": {"symbol": "FTSE", "name": "FTSE 100", "primary": "stooq"},
    "^KS11": {"symbol": "KOSPI", "name": "Kospi", "primary": "stooq"},
    "DX-Y.NYB": {"symbol": "DXY", "name": "DXY", "primary": "stooq"},
    "2YY=F": {"symbol": "DGS2", "name": "2Y Treasury", "primary": "fred"},
}

RSS_FEEDS = {
    "markets_macro": [
        ("CNBC Markets", "https://www.cnbc.com/id/10000664/device/rss/rss.html"),
        ("CNBC US Markets", "https://www.cnbc.com/id/100003114/device/rss/rss.html"),
        ("MarketWatch", "https://www.marketwatch.com/rss/topstories"),
        ("Yahoo Finance", "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^GSPC&region=US&lang=en-US"),
    ],
    "earnings_movers": [
        ("Benzinga", "https://www.benzinga.com/feed"),
        ("Seeking Alpha", "https://seekingalpha.com/feed.xml"),
    ],
    "fed_policy": [
        ("Fed Speeches", "https://www.federalreserve.gov/feeds/speeches.xml"),
        ("Fed Press Releases", "https://www.federalreserve.gov/feeds/press_all.xml"),
    ],
    "crypto": [
        ("CoinDesk", "https://www.coindesk.com/arc/outboundfeeds/rss/"),
    ],
    "defense_aerospace": [
        ("Defense.gov Contracts", "https://www.defense.gov/DesktopModules/ArticleCS/RSS.ashx?ContentType=1&Site=945"),
        ("Breaking Defense", "https://breakingdefense.com/feed/"),
    ],
    "space": [
        ("SpaceNews", "https://spacenews.com/feed/"),
        ("NASA", "https://www.nasa.gov/feed/"),
    ],
    "nuclear_energy": [
        ("ANS Nuclear Newswire", "https://www.ans.org/news/feed/"),
    ],
    "semiconductors": [
        ("Tom's Hardware", "https://www.tomshardware.com/feeds/all"),
        ("Semiconductor Engineering", "https://semiengineering.com/feed/"),
    ],
    "cybersecurity": [
        ("The Hacker News", "https://feeds.feedburner.com/TheHackersNews"),
        ("BleepingComputer", "https://www.bleepingcomputer.com/feed/"),
    ],
    "quantum_computing": [
        ("The Quantum Insider", "https://thequantuminsider.com/feed"),
        ("Quantum Computing Report", "https://quantumcomputingreport.com/feed/"),
    ],
    "critical_minerals": [
        ("Northern Miner", "https://www.northernminer.com/feed/"),
        ("Mining Technology", "https://www.mining-technology.com/feed"),
    ],
    "robotics_automation": [
        ("The Robot Report", "https://www.therobotreport.com/feed"),
        ("Robotics & Automation News", "https://roboticsandautomationnews.com/feed"),
    ],
    "energy_storage": [
        ("Energy Storage News", "https://energy-storage.news/feed"),
        ("CleanTechnica", "https://cleantechnica.com/feed"),
    ],
}

# Events that trigger HEAVY event load
HEAVY_EVENTS = [
    "FOMC", "Fed Funds Rate", "Federal Funds",
    "Nonfarm Payrolls", "NFP", "Employment Situation",
    "CPI", "Consumer Price Index",
    "GDP", "Gross Domestic Product",
    "PCE", "Personal Consumption",
    "PPI", "Producer Price Index",
]

# ── Watchlist ──────────────────────────────────────────────────────────────────

WATCHLIST = {
    "AI Infrastructure": {
        1: ["NVDA", "TSM", "AVGO", "VRT", "ANET"],
        2: ["MRVL", "MU", "ETN", "GLW", "PLTR"],
        3: ["ASML", "AMD", "CRWV", "PWR", "CIEN", "NOW"],
    },
    "Cybersecurity": {
        1: ["PANW", "CRWD", "FTNT", "ZS", "LDOS", "CACI"],
        2: ["NET", "OKTA", "S", "ESTC", "BAH", "PSN", "CHKP", "QLYS", "TENB"],
        3: ["SAIL", "TLS", "RPD", "BBAI"],
    },
    "Defense & Aerospace": {
        1: ["LMT", "RTX", "NOC", "LHX"],
        2: ["GD", "AVAV", "RKLB", "KTOS", "HII"],
        3: ["BA", "OLN", "CW"],
    },
    "Nuclear Energy": {
        1: ["CEG", "VST", "CCJ", "LEU"],
        2: ["TLN", "BWXT", "NXE", "UEC", "UUUU"],
        3: ["DNN", "OKLO", "SMR", "PEG"],
    },
    "Critical Minerals": {
        1: ["MP", "LYSCF", "FCX", "ALB"],
        2: ["SQM", "SCCO", "USAR"],
        3: [],
    },
    "Quantum Computing": {
        1: ["IBM", "HON", "IONQ"],
        2: ["GOOG", "RGTI"],
        3: ["QBTS", "QUBT"],
    },
    "Space": {
        1: ["PL", "RKLB", "LUNR"],
        2: ["IRDM", "SPIR"],
        3: ["RDW", "MNTS"],
    },
    "Robotics & Automation": {
        1: ["ISRG", "SYK", "SYM", "CGNX"],
        2: ["ROK", "TER", "AZTA"],
        3: ["OUST"],
    },
    "Energy Storage": {
        1: ["ALB", "SQM", "TSLA", "FLNC"],
        2: ["ENPH", "SEDG", "QS"],
        3: ["STEM", "BE"],
    },
}


def get_all_watchlist_tickers():
    """Returns {symbol: (sector, tier)} with highest tier per symbol."""
    tickers = {}
    for sector, tiers in WATCHLIST.items():
        for tier, symbols in tiers.items():
            for sym in symbols:
                if sym not in tickers or tier < tickers[sym][1]:
                    tickers[sym] = (sector, tier)
    return tickers


def get_tier_tickers(max_tier):
    """Get symbols up to and including max_tier."""
    return [s for s, (_, t) in get_all_watchlist_tickers().items() if t <= max_tier]


# ── Database Schema ────────────────────────────────────────────────────────────

SCHEMA = """
CREATE TABLE IF NOT EXISTS quotes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    name TEXT,
    source TEXT NOT NULL,
    price REAL,
    change_pct REAL,
    change_amt REAL,
    open_price REAL,
    high REAL,
    low REAL,
    close_price REAL,
    volume INTEGER,
    fetched_at TEXT NOT NULL,
    market_date TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_quotes_date_sym ON quotes(market_date, symbol);

CREATE TABLE IF NOT EXISTS economic_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    market_date TEXT NOT NULL,
    event_time TEXT,
    event_name TEXT NOT NULL,
    impact TEXT,
    actual TEXT,
    forecast TEXT,
    previous TEXT,
    source TEXT,
    fetched_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS earnings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    report_date TEXT,
    report_time TEXT,
    eps_estimate REAL,
    eps_actual REAL,
    revenue_estimate REAL,
    revenue_actual REAL,
    source TEXT,
    fetched_at TEXT NOT NULL,
    market_date TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS movers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    name TEXT,
    price REAL,
    change_pct REAL,
    volume INTEGER,
    mover_type TEXT NOT NULL,
    source TEXT,
    fetched_at TEXT NOT NULL,
    market_date TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS technicals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    rsi_14 REAL,
    sma_20 REAL,
    sma_50 REAL,
    sma_200 REAL,
    atr_14 REAL,
    bb_upper REAL,
    bb_lower REAL,
    macd REAL,
    macd_signal REAL,
    source TEXT,
    fetched_at TEXT NOT NULL,
    market_date TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS levels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    level_type TEXT NOT NULL,
    price REAL NOT NULL,
    strength INTEGER,
    source TEXT,
    fetched_at TEXT NOT NULL,
    market_date TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS market_context (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vix_level REAL,
    vix_regime TEXT,
    spy_trend TEXT,
    risk_appetite TEXT,
    spy_sma50_distance REAL,
    source TEXT,
    fetched_at TEXT NOT NULL,
    market_date TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS headlines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feed_name TEXT NOT NULL,
    feed_category TEXT NOT NULL,
    title TEXT NOT NULL,
    link TEXT,
    published_at TEXT,
    fetched_at TEXT NOT NULL,
    market_date TEXT NOT NULL,
    UNIQUE(link)
);

CREATE TABLE IF NOT EXISTS collections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    market_date TEXT NOT NULL,
    phase1_status TEXT,
    phase2_status TEXT,
    phase3_status TEXT,
    phase4_status TEXT,
    total_quotes INTEGER DEFAULT 0,
    total_headlines INTEGER DEFAULT 0,
    completeness_score REAL,
    exit_code INTEGER
);

CREATE TABLE IF NOT EXISTS source_health (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    status TEXT NOT NULL,
    response_time_ms INTEGER,
    error_message TEXT,
    data_points INTEGER DEFAULT 0,
    fetched_at TEXT NOT NULL,
    market_date TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS anomalies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    field TEXT NOT NULL,
    current_value REAL,
    avg_20d REAL,
    std_20d REAL,
    z_score REAL,
    flagged_at TEXT NOT NULL,
    market_date TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS cross_validations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data_point TEXT NOT NULL,
    source_a TEXT NOT NULL,
    value_a REAL,
    source_b TEXT NOT NULL,
    value_b REAL,
    discrepancy_pct REAL,
    flagged_at TEXT NOT NULL,
    market_date TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS opus_tickers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    market_date TEXT NOT NULL,
    ticker TEXT NOT NULL,
    analyzed_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_opus_tickers_date ON opus_tickers(market_date);

CREATE TABLE IF NOT EXISTS opus_movers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    market_date TEXT NOT NULL,
    ticker TEXT NOT NULL,
    direction TEXT,
    reason TEXT,
    headline TEXT,
    analyzed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS opus_themes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    market_date TEXT NOT NULL,
    sector TEXT NOT NULL,
    narrative TEXT,
    analyzed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS opus_econ_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    market_date TEXT NOT NULL,
    event TEXT NOT NULL,
    status TEXT,
    context TEXT,
    analyzed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS opus_fed_signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    market_date TEXT NOT NULL,
    signal TEXT NOT NULL,
    analyzed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS opus_sentiment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    market_date TEXT NOT NULL,
    sentiment TEXT NOT NULL,
    headline_count INTEGER,
    model_used TEXT DEFAULT 'opus',
    analyzed_at TEXT NOT NULL,
    UNIQUE(market_date)
);

CREATE TABLE IF NOT EXISTS watchlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL UNIQUE,
    company TEXT,
    sector TEXT NOT NULL,
    tier INTEGER NOT NULL,
    added_at TEXT NOT NULL
);
"""


def init_db():
    """Create database and tables if they don't exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


def clear_today(conn, market_date):
    """Remove today's data so re-runs are clean."""
    tables_with_date = [
        "quotes", "economic_events", "earnings", "movers", "technicals",
        "levels", "market_context", "headlines", "anomalies", "cross_validations",
        "opus_tickers", "opus_movers", "opus_themes",
        "opus_econ_events", "opus_fed_signals", "opus_sentiment",
    ]
    for table in tables_with_date:
        conn.execute(f"DELETE FROM {table} WHERE market_date = ?", (market_date,))
    conn.commit()


def populate_watchlist(conn, market_date):
    """Insert/update watchlist from WATCHLIST config."""
    now = datetime.datetime.now().isoformat()
    for sector, tiers in WATCHLIST.items():
        for tier, symbols in tiers.items():
            for sym in symbols:
                conn.execute(
                    "INSERT OR REPLACE INTO watchlist (symbol, sector, tier, added_at) "
                    "VALUES (?, ?, ?, ?)",
                    (sym, sector, tier, now),
                )
    conn.commit()


# ── HTTP Helpers ───────────────────────────────────────────────────────────────

def fetch_url(url, timeout=10, retries=MAX_RETRIES, headers=None):
    """Fetch URL with retry logic. Returns (data_bytes, elapsed_ms)."""
    hdrs = {"User-Agent": "BigPic-Markets/1.0"}
    if headers:
        hdrs.update(headers)
    last_error = None
    for attempt in range(retries + 1):
        if attempt > 0:
            time.sleep(2 ** (attempt - 1))
        start = time.monotonic()
        try:
            req = urllib.request.Request(url, headers=hdrs)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = resp.read()
                elapsed = int((time.monotonic() - start) * 1000)
                return data, elapsed
        except Exception as e:
            last_error = e
    raise last_error


def fetch_json(url, timeout=10, retries=MAX_RETRIES):
    """Fetch JSON endpoint. Returns (parsed_dict, elapsed_ms)."""
    data, elapsed = fetch_url(url, timeout, retries, {"Accept": "application/json"})
    return json.loads(data), elapsed


def fetch_csv_text(url, timeout=10, retries=MAX_RETRIES):
    """Fetch CSV text. Returns (text_string, elapsed_ms)."""
    data, elapsed = fetch_url(url, timeout, retries)
    return data.decode("utf-8", errors="replace"), elapsed


# ── Source Health Logging ──────────────────────────────────────────────────────

def log_health(conn, market_date, source, endpoint, status, elapsed_ms,
               error_msg=None, data_points=0):
    """Log an API call to source_health table."""
    conn.execute(
        "INSERT INTO source_health "
        "(source, endpoint, status, response_time_ms, error_message, data_points, "
        "fetched_at, market_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (source, endpoint, status, elapsed_ms, error_msg, data_points,
         datetime.datetime.now().isoformat(), market_date),
    )


# ── Quote Helpers ──────────────────────────────────────────────────────────────

def resolve_quote(quotes_dict, symbol):
    """Find quote by exact match or futures prefix match (/ES → /ESH26)."""
    if symbol in quotes_dict:
        return quotes_dict[symbol]
    for sym, q in quotes_dict.items():
        if sym.startswith(symbol) and len(sym) > len(symbol):
            return q
    return None


def extract_price(quote):
    """Get best available price from a Schwab quote."""
    return quote.get("lastPrice") or quote.get("mark") or quote.get("price")


def extract_change_pct(quote):
    """Get percentage change from a Schwab quote."""
    pct = quote.get("futurePercentChange") or quote.get("netPercentChange")
    if pct is not None:
        return pct
    last = extract_price(quote)
    prev = quote.get("closePrice") or quote.get("previousClose")
    if last and prev and prev != 0:
        return ((last - prev) / prev) * 100
    return None


# ── Phase 1: Schwab + Local APIs ──────────────────────────────────────────────

def collect_schwab_quotes(conn, market_date, log, extra_tickers=None):
    """Batch-fetch quotes for core symbols + all watchlist tickers + any extra tickers."""
    all_symbols = list(SCHWAB_CORE) + ["SPY", "QQQ", "IWM", "DIA"]
    watchlist_syms = list(get_all_watchlist_tickers().keys())
    extra = list(extra_tickers) if extra_tickers else []
    # Deduplicate
    seen = set()
    symbols = []
    for s in all_symbols + watchlist_syms + extra:
        if s not in seen:
            seen.add(s)
            symbols.append(s)

    total = 0
    chunks = [symbols[i:i + QUOTE_CHUNK_SIZE] for i in range(0, len(symbols), QUOTE_CHUNK_SIZE)]

    for i, chunk in enumerate(chunks):
        if i > 0:
            time.sleep(CHUNK_DELAY)
        sym_str = ",".join(chunk)
        endpoint = f"/api/quotes?symbols={sym_str}"
        url = f"{SCHWAB_BASE}{endpoint}"
        try:
            data, elapsed = fetch_json(url, timeout=SCHWAB_TIMEOUT)
            quotes = {}
            if "quotes" in data:
                quotes = {k: v for k, v in data["quotes"].items()
                          if k != "errors" and isinstance(v, dict)}
            elif "quote" in data:
                quotes = {chunk[0]: data["quote"]}

            now = datetime.datetime.now().isoformat()
            for sym, q in quotes.items():
                price = extract_price(q)
                change = extract_change_pct(q)
                conn.execute(
                    "INSERT INTO quotes (symbol, name, source, price, change_pct, "
                    "change_amt, open_price, high, low, close_price, volume, "
                    "fetched_at, market_date) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (sym, q.get("description", SYMBOL_NAMES.get(sym, sym)),
                     "schwab", price, change,
                     q.get("netChange"), q.get("openPrice"), q.get("highPrice"),
                     q.get("lowPrice"), q.get("closePrice") or q.get("previousClose"),
                     q.get("totalVolume"), now, market_date),
                )
                total += 1

            log_health(conn, market_date, "schwab", endpoint, "ok", elapsed,
                       data_points=len(quotes))
        except Exception as e:
            log.warning(f"Schwab quotes chunk {i+1} failed: {e}")
            log_health(conn, market_date, "schwab", endpoint, "error", 0,
                       error_msg=str(e))

    conn.commit()
    log.info(f"Schwab quotes: {total} symbols")
    return total


def collect_schwab_market_context(conn, market_date, log):
    """Fetch VIX regime, SPY trend, risk appetite."""
    endpoint = "/api/market/context"
    url = f"{SCHWAB_BASE}{endpoint}"
    try:
        data, elapsed = fetch_json(url, timeout=SCHWAB_TIMEOUT)
        now = datetime.datetime.now().isoformat()
        conn.execute(
            "INSERT INTO market_context (vix_level, vix_regime, spy_trend, "
            "risk_appetite, spy_sma50_distance, source, fetched_at, market_date) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (data.get("vix") or data.get("vixLevel") or data.get("vix_level"),
             data.get("vix_regime") or data.get("vixRegime"),
             data.get("spy_trend") or data.get("spyTrend"),
             data.get("risk_appetite") or data.get("riskAppetite"),
             data.get("spy_sma50_distance") or data.get("spySma50Distance"),
             "schwab", now, market_date),
        )
        conn.commit()
        log_health(conn, market_date, "schwab", endpoint, "ok", elapsed, data_points=1)
        log.info("Schwab market context: collected")
        return 1
    except Exception as e:
        log.warning(f"Schwab market context failed: {e}")
        log_health(conn, market_date, "schwab", endpoint, "error", 0, error_msg=str(e))
        return 0


def collect_schwab_technicals(conn, market_date, log, symbols=None):
    """Fetch technicals for given symbols (defaults to Tier 1 + ETF benchmarks)."""
    if symbols is None:
        symbols = get_tier_tickers(1) + ["SPY", "QQQ", "IWM", "DIA"]
    else:
        symbols = list(symbols)
    seen = set()
    symbols = [s for s in symbols if s not in seen and not seen.add(s)]

    total = 0
    for sym in symbols:
        endpoint = f"/api/technicals/{sym}"
        url = f"{SCHWAB_BASE}{endpoint}"
        try:
            data, elapsed = fetch_json(url, timeout=5, retries=0)
            tech = data.get("technicals", data)
            now = datetime.datetime.now().isoformat()
            conn.execute(
                "INSERT INTO technicals (symbol, rsi_14, sma_20, sma_50, sma_200, "
                "atr_14, bb_upper, bb_lower, macd, macd_signal, source, "
                "fetched_at, market_date) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (sym,
                 tech.get("rsi_14") or tech.get("rsi"),
                 tech.get("sma_20") or tech.get("sma20"),
                 tech.get("sma_50") or tech.get("sma50"),
                 tech.get("sma_200") or tech.get("sma200"),
                 tech.get("atr_14") or tech.get("atr"),
                 tech.get("bb_upper") or tech.get("bbUpper"),
                 tech.get("bb_lower") or tech.get("bbLower"),
                 tech.get("macd"),
                 tech.get("macd_signal") or tech.get("macdSignal"),
                 "schwab", now, market_date),
            )
            total += 1
            log_health(conn, market_date, "schwab", endpoint, "ok", elapsed, data_points=1)
        except Exception as e:
            log.debug(f"Schwab technicals {sym}: {e}")
            log_health(conn, market_date, "schwab", endpoint, "error", 0, error_msg=str(e))
        time.sleep(TECH_DELAY)

    conn.commit()
    log.info(f"Schwab technicals: {total}/{len(symbols)} symbols")
    return total


def collect_sma200(conn, market_date, log, symbols=None):
    """Calculate SMA200 from price history for given symbols.

    Uses /api/history (lightweight daily candles) instead of /api/levels
    (heavy options chain analysis) to be gentle on the proxy server.
    Defaults to Tier 1 + ETF benchmarks if no symbols provided.
    """
    if symbols is None:
        symbols = get_tier_tickers(1) + ["SPY", "QQQ", "IWM", "DIA"]
    else:
        symbols = list(symbols)
    seen = set()
    symbols = [s for s in symbols if s not in seen and not seen.add(s)]

    total = 0
    for sym in symbols:
        endpoint = f"/api/history/{sym}?period_type=year&period=1&frequency_type=daily&frequency=1"
        url = f"{SCHWAB_BASE}{endpoint}"
        try:
            data, elapsed = fetch_json(url, timeout=SCHWAB_TIMEOUT, retries=0)
            candles = data.get("candles", [])
            if len(candles) >= 200:
                closes = [c["close"] for c in candles[-200:]]
                sma200 = sum(closes) / 200
                now = datetime.datetime.now().isoformat()
                conn.execute(
                    "INSERT INTO levels (symbol, level_type, price, strength, "
                    "source, fetched_at, market_date) VALUES (?,?,?,?,?,?,?)",
                    (sym, "sma_200", round(sma200, 2), None, "schwab", now, market_date))
                total += 1
                log_health(conn, market_date, "schwab", f"/api/history/{sym}", "ok",
                           elapsed, data_points=1)
            else:
                log.debug(f"SMA200 {sym}: only {len(candles)} candles (need 200)")
                log_health(conn, market_date, "schwab", f"/api/history/{sym}", "ok",
                           elapsed, data_points=0)
        except Exception as e:
            log.debug(f"SMA200 {sym}: {e}")
            log_health(conn, market_date, "schwab", f"/api/history/{sym}", "error",
                       0, error_msg=str(e))
        time.sleep(CHUNK_DELAY)

    conn.commit()
    log.info(f"SMA200: {total}/{len(symbols)} symbols")
    return total


def collect_schwab_earnings(conn, market_date, log):
    """Fetch earnings calendar for Tier 1+2 tickers."""
    # Health check: try one symbol first, skip all if endpoint doesn't exist
    test_url = f"{SCHWAB_BASE}/api/calendar/SPY"
    try:
        fetch_json(test_url, timeout=5, retries=0)
    except Exception as e:
        log.info(f"Schwab earnings endpoint not available ({e}), skipping")
        log_health(conn, market_date, "schwab", "/api/calendar/*", "skipped", 0,
                   error_msg="endpoint not available")
        conn.commit()
        return 0

    symbols = get_tier_tickers(2)
    total = 0
    consecutive_empty = 0
    for sym in symbols:
        endpoint = f"/api/calendar/{sym}"
        url = f"{SCHWAB_BASE}{endpoint}"
        try:
            data, elapsed = fetch_json(url, timeout=5, retries=0)
            now = datetime.datetime.now().isoformat()

            # Proxy returns: {symbol, next_earnings, days_to_earnings,
            #   earnings_time, warning_level, has_earnings}
            items = data if isinstance(data, list) else [data]
            found = 0
            for item in items:
                report_date = (item.get("next_earnings") or item.get("reportDate")
                               or item.get("earnings_date") or item.get("date"))
                if not report_date or not item.get("has_earnings", True):
                    continue
                conn.execute(
                    "INSERT INTO earnings (symbol, report_date, report_time, "
                    "eps_estimate, eps_actual, revenue_estimate, revenue_actual, "
                    "source, fetched_at, market_date) VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (sym, report_date,
                     item.get("earnings_time") or item.get("reportTime") or item.get("time"),
                     item.get("epsEstimate") or item.get("eps_estimate"),
                     item.get("epsActual") or item.get("eps_actual"),
                     item.get("revenueEstimate") or item.get("revenue_estimate"),
                     item.get("revenueActual") or item.get("revenue_actual"),
                     "schwab", now, market_date),
                )
                found += 1
                total += 1

            if found > 0:
                consecutive_empty = 0
            else:
                consecutive_empty += 1
            log_health(conn, market_date, "schwab", endpoint, "ok", elapsed,
                       data_points=found)
        except Exception as e:
            consecutive_empty += 1
            log.debug(f"Schwab earnings {sym}: {e}")
            log_health(conn, market_date, "schwab", endpoint, "error", 0, error_msg=str(e))

        if consecutive_empty >= 5:
            log.info("Schwab earnings: 5 consecutive empty/failed, skipping remaining")
            break
        time.sleep(CHUNK_DELAY)

    conn.commit()
    log.info(f"Schwab earnings: {total} entries")
    return total


def collect_economic_calendar(conn, market_date, log):
    """Fetch today's scheduled economic releases."""
    endpoint = ECON_CALENDAR_URL
    try:
        data, elapsed = fetch_json(endpoint, timeout=SCHWAB_TIMEOUT)
        events = data if isinstance(data, list) else data.get("data", data.get("events", data.get("calendar", [])))
        if not isinstance(events, list):
            events = []

        now = datetime.datetime.now().isoformat()
        total = 0
        for ev in events:
            conn.execute(
                "INSERT INTO economic_events (market_date, event_time, event_name, "
                "impact, actual, forecast, previous, source, fetched_at) "
                "VALUES (?,?,?,?,?,?,?,?,?)",
                (market_date,
                 ev.get("event_time") or ev.get("time"),
                 ev.get("event_name") or ev.get("name") or ev.get("event", "Unknown"),
                 ev.get("impact_level") or ev.get("impact"),
                 ev.get("actual"),  # NULL = not released yet
                 ev.get("forecast") or ev.get("consensus"),
                 ev.get("previous") or ev.get("prior"),
                 ev.get("source", "econ_calendar"),
                 now),
            )
            total += 1

        conn.commit()
        log_health(conn, market_date, "econ_calendar", endpoint, "ok", elapsed,
                   data_points=total)
        log.info(f"Economic calendar: {total} events")
        return total
    except Exception as e:
        log.warning(f"Economic calendar failed: {e}")
        log_health(conn, market_date, "econ_calendar", endpoint, "error", 0,
                   error_msg=str(e))
        return 0


# ── Phase 2: External APIs ────────────────────────────────────────────────────

def collect_coingecko(conn, market_date, log):
    """Fetch BTC and ETH from CoinGecko."""
    try:
        data, elapsed = fetch_json(COINGECKO_URL, timeout=EXTERNAL_TIMEOUT)
        now = datetime.datetime.now().isoformat()
        total = 0
        for coin_id, name, sym in [("bitcoin", "Bitcoin", "BTC"), ("ethereum", "Ethereum", "ETH")]:
            if coin_id in data:
                coin = data[coin_id]
                conn.execute(
                    "INSERT INTO quotes (symbol, name, source, price, change_pct, "
                    "fetched_at, market_date) VALUES (?,?,?,?,?,?,?)",
                    (sym, name, "coingecko",
                     coin.get("usd"), coin.get("usd_24h_change"),
                     now, market_date),
                )
                total += 1

        conn.commit()
        log_health(conn, market_date, "coingecko", COINGECKO_URL, "ok", elapsed,
                   data_points=total)
        log.info(f"CoinGecko: {total} coins")
        return total
    except Exception as e:
        log.warning(f"CoinGecko failed: {e}")
        log_health(conn, market_date, "coingecko", COINGECKO_URL, "error", 0,
                   error_msg=str(e))
        return 0


def collect_stooq(conn, market_date, log):
    """Fetch FTSE, Kospi, DXY from Stooq CSV."""
    total = 0
    for sym_key, info in STOOQ_SYMBOLS.items():
        url = info["url"]
        try:
            text, elapsed = fetch_csv_text(url, timeout=EXTERNAL_TIMEOUT)
            reader = csv.reader(io.StringIO(text.strip()))
            header = next(reader, None)
            row = next(reader, None)
            if not row or len(row) < 7:
                raise ValueError(f"Unexpected CSV format: {text[:200]}")

            # Format: Symbol,Date,Time,Open,High,Low,Close,Volume
            close_price = float(row[6]) if row[6] and row[6] != "N/D" else None
            open_price = float(row[3]) if row[3] and row[3] != "N/D" else None
            if close_price is None:
                raise ValueError("No close price")

            change_pct = None
            if open_price and open_price != 0:
                change_pct = ((close_price - open_price) / open_price) * 100

            now = datetime.datetime.now().isoformat()
            conn.execute(
                "INSERT INTO quotes (symbol, name, source, price, change_pct, "
                "open_price, high, low, close_price, fetched_at, market_date) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (sym_key, info["name"], "stooq", close_price, change_pct,
                 open_price,
                 float(row[4]) if row[4] and row[4] != "N/D" else None,
                 float(row[5]) if row[5] and row[5] != "N/D" else None,
                 close_price, now, market_date),
            )
            total += 1
            log_health(conn, market_date, "stooq", url, "ok", elapsed, data_points=1)
        except Exception as e:
            log.warning(f"Stooq {sym_key} failed: {e}")
            log_health(conn, market_date, "stooq", url, "error", 0, error_msg=str(e))
        time.sleep(0.5)

    conn.commit()
    log.info(f"Stooq: {total}/3 symbols")
    return total


def collect_fred(conn, market_date, log):
    """Fetch 2Y/10Y/30Y Treasury yields from FRED CSV (batch request)."""
    series_ids = ",".join(FRED_SERIES.keys())
    end_date = market_date
    start_date = (datetime.date.fromisoformat(market_date) - datetime.timedelta(days=7)).isoformat()
    url = f"{FRED_BASE}?id={series_ids}&cosd={start_date}&coed={end_date}"

    try:
        text, elapsed = fetch_csv_text(url, timeout=EXTERNAL_TIMEOUT)
        reader = csv.DictReader(io.StringIO(text.strip()))
        rows = list(reader)
        if not rows:
            raise ValueError("Empty FRED response")

        # Use most recent row with non-empty values
        now = datetime.datetime.now().isoformat()
        total = 0
        for series_id, name in FRED_SERIES.items():
            value = None
            for row in reversed(rows):
                val = row.get(series_id, "").strip()
                if val and val != ".":
                    try:
                        value = float(val)
                        break
                    except ValueError:
                        continue

            if value is not None:
                conn.execute(
                    "INSERT INTO quotes (symbol, name, source, price, "
                    "fetched_at, market_date) VALUES (?,?,?,?,?,?)",
                    (series_id, name, "fred", value, now, market_date),
                )
                total += 1

        conn.commit()
        log_health(conn, market_date, "fred", url, "ok", elapsed, data_points=total)
        log.info(f"FRED: {total}/3 series")
        return total
    except Exception as e:
        log.warning(f"FRED failed: {e}")
        log_health(conn, market_date, "fred", url, "error", 0, error_msg=str(e))
        return 0


def collect_yahoo_backup(conn, market_date, log, failed_sources):
    """Last-resort backup for symbols whose primary source failed."""
    total = 0
    for yahoo_sym, info in YAHOO_BACKUP.items():
        # Only fetch if primary source failed
        if info["primary"] not in failed_sources:
            continue
        # Check if we already have this symbol from another source
        existing = conn.execute(
            "SELECT COUNT(*) FROM quotes WHERE symbol = ? AND market_date = ?",
            (info["symbol"], market_date),
        ).fetchone()[0]
        if existing > 0:
            continue

        url = f"https://query2.finance.yahoo.com/v8/finance/chart/{yahoo_sym}?interval=1d&range=1d"
        try:
            data, elapsed = fetch_json(url, timeout=EXTERNAL_TIMEOUT)
            result = data.get("chart", {}).get("result", [{}])[0]
            meta = result.get("meta", {})
            price = meta.get("regularMarketPrice")
            prev_close = meta.get("previousClose") or meta.get("chartPreviousClose")

            if price is None:
                raise ValueError("No price in Yahoo response")

            change_pct = None
            if prev_close and prev_close != 0:
                change_pct = ((price - prev_close) / prev_close) * 100

            now = datetime.datetime.now().isoformat()
            conn.execute(
                "INSERT INTO quotes (symbol, name, source, price, change_pct, "
                "close_price, fetched_at, market_date) VALUES (?,?,?,?,?,?,?,?)",
                (info["symbol"], info["name"], "yahoo", price, change_pct,
                 prev_close, now, market_date),
            )
            total += 1
            log_health(conn, market_date, "yahoo", url, "ok", elapsed, data_points=1)
        except Exception as e:
            log.warning(f"Yahoo {yahoo_sym} failed: {e}")
            log_health(conn, market_date, "yahoo", url, "error", 0, error_msg=str(e))
        time.sleep(YAHOO_DELAY)

    conn.commit()
    log.info(f"Yahoo backup: {total} symbols")
    return total


# ── Phase 3: RSS Feeds ────────────────────────────────────────────────────────

def parse_rss_items(xml_bytes):
    """Parse RSS 2.0 or Atom feed, return list of (title, link, published_at)."""
    items = []
    # Some servers force-gzip even without Accept-Encoding: gzip
    if xml_bytes[:2] == b"\x1f\x8b":
        try:
            xml_bytes = gzip.decompress(xml_bytes)
        except Exception:
            pass
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return items

    # RSS 2.0
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub = item.findtext("pubDate") or item.findtext("dc:date") or ""
        pub_dt = None
        if pub:
            try:
                pub_dt = parsedate_to_datetime(pub).isoformat()
            except Exception:
                pub_dt = pub.strip()
        if title:
            items.append((title, link, pub_dt))

    # Atom (if no RSS items found)
    if not items:
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        for entry in root.findall(".//atom:entry", ns) or root.findall(".//entry"):
            title = ""
            link = ""
            pub_dt = None
            t = entry.find("atom:title", ns) or entry.find("title")
            if t is not None and t.text:
                title = t.text.strip()
            l = entry.find("atom:link", ns) or entry.find("link")
            if l is not None:
                link = l.get("href", l.text or "").strip()
            p = entry.find("atom:published", ns) or entry.find("published") or \
                entry.find("atom:updated", ns) or entry.find("updated")
            if p is not None and p.text:
                pub_dt = p.text.strip()
            if title:
                items.append((title, link, pub_dt))

    return items


def collect_rss_feeds(conn, market_date, log):
    """Fetch all RSS feeds and store headlines from the last 24 hours only.

    Returns (total_headlines, failed_feeds) where failed_feeds is a list of
    (feed_name, feed_url, error) tuples. Individual feed failures are non-fatal;
    a warning email is sent and the pipeline continues with available headlines.
    Only a total of zero headlines triggers a hard abort.
    """
    total = 0
    skipped = 0
    failed_feeds = []
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=24)
    cutoff_naive = datetime.datetime.now() - datetime.timedelta(hours=24)
    now = datetime.datetime.now().isoformat()

    for category, feeds in RSS_FEEDS.items():
        for feed_name, feed_url in feeds:
            try:
                data, elapsed = fetch_url(feed_url, timeout=RSS_TIMEOUT)
                items = parse_rss_items(data)
                count = 0
                for title, link, pub_at in items[:25]:  # Max 25 per feed
                    # Filter: only keep headlines from last 24 hours
                    if pub_at:
                        try:
                            # Try parsing as ISO format (from Atom feeds or our own format)
                            pub_dt = datetime.datetime.fromisoformat(pub_at.replace("Z", "+00:00"))
                            if pub_dt.tzinfo:
                                if pub_dt < cutoff:
                                    skipped += 1
                                    continue
                            else:
                                if pub_dt < cutoff_naive:
                                    skipped += 1
                                    continue
                        except (ValueError, TypeError):
                            pass  # Unparseable date — keep it rather than lose it
                    try:
                        conn.execute(
                            "INSERT OR IGNORE INTO headlines "
                            "(feed_name, feed_category, title, link, published_at, "
                            "fetched_at, market_date) VALUES (?,?,?,?,?,?,?)",
                            (feed_name, category, title, link, pub_at, now, market_date),
                        )
                        count += 1
                    except sqlite3.IntegrityError:
                        pass  # Duplicate URL

                total += count
                log_health(conn, market_date, "rss", feed_url, "ok", elapsed,
                           data_points=count)
            except Exception as e:
                log.error(f"RSS {feed_name} FAILED: {e}")
                log_health(conn, market_date, "rss", feed_url, "error", 0,
                           error_msg=str(e))
                failed_feeds.append((feed_name, feed_url, str(e)))
            time.sleep(0.3)

    conn.commit()
    log.info(f"RSS feeds: {total} headlines stored, {skipped} older than 24h skipped")
    if failed_feeds:
        log.error(f"RSS feeds: {len(failed_feeds)} feed(s) FAILED")
    return total, failed_feeds


# ── Feed Analysis ─────────────────────────────────────────────────────────────

def get_big_movers(conn, market_date, threshold=3.0):
    """Auto-detect movers from quote data: symbols where |change_pct| > threshold."""
    cur = conn.execute(
        "SELECT symbol FROM quotes "
        "WHERE market_date = ? AND source = 'schwab' AND ABS(change_pct) > ?",
        (market_date, threshold),
    )
    return {row[0] for row in cur.fetchall()}


def analyze_headlines_with_opus(conn, market_date, log):
    """Feed today's headlines to Opus for structured intelligence extraction.

    Calls `claude -p --model opus` with all today's headlines grouped by category.
    Returns parsed JSON with tickers, movers, econ_events, fed_signals,
    sector_themes, and sentiment. Stores results in normalized opus_* tables.

    Falls back gracefully: returns empty dict on any failure.
    """
    # Query all headlines for today, grouped by category
    rows = conn.execute(
        "SELECT feed_category, feed_name, title FROM headlines "
        "WHERE market_date = ? ORDER BY feed_category, feed_name",
        (market_date,),
    ).fetchall()

    if not rows:
        log.warning("Opus analysis: no headlines to analyze")
        return {}

    # Build prompt with headlines grouped by category
    headline_count = len(rows)
    grouped = {}
    for row in rows:
        cat = row["feed_category"]
        if cat not in grouped:
            grouped[cat] = []
        grouped[cat].append(f"[{row['feed_name']}] {row['title']}")

    headline_block = ""
    for cat, items in grouped.items():
        headline_block += f"\n### {cat}\n"
        for item in items:
            headline_block += f"- {item}\n"

    prompt = f"""Analyze these financial news headlines from {market_date} and extract structured market intelligence.

{headline_block}

Return ONLY valid JSON (no markdown fences, no commentary) with this exact structure:
{{
  "tickers": ["SYM1", "SYM2"],
  "movers": [
    {{"ticker": "SYM", "direction": "up|down", "reason": "brief reason", "headline": "source headline"}}
  ],
  "econ_events": [
    {{"event": "CPI", "status": "pending|released", "context": "brief context"}}
  ],
  "fed_signals": ["signal summary 1"],
  "sector_themes": [
    {{"sector": "Sector Name", "narrative": "brief narrative"}}
  ],
  "sentiment": "one-line overall market sentiment"
}}

Rules:
- tickers: only real US stock ticker symbols mentioned or clearly implied by headlines
- movers: only include stocks with clear directional signal from news (earnings beat/miss, contract win, etc.)
- econ_events: only if headlines mention scheduled economic data releases
- fed_signals: only if headlines reference Fed officials or policy
- sector_themes: group related headlines into sector-level narratives
- sentiment: synthesize overall market mood from all headlines
- If a category has no relevant data, use an empty list or empty string
- Do NOT fabricate data. Only extract what is clearly stated in the headlines."""

    # Reset failure classification before each invocation
    analyze_headlines_with_opus.last_error = None

    try:
        log.info(f"Opus analysis: sending {headline_count} headlines to claude CLI...")
        # Clean env: remove CLAUDECODE var so claude CLI works when called from
        # inside a Claude Code session (e.g., during testing)
        clean_env = {k: v for k, v in os.environ.items() if not k.startswith("CLAUDE")}
        claude_bin = os.path.expanduser("~/.local/bin/claude")
        result = subprocess.run(
            [claude_bin, "-p", "--model", "opus", "--output-format", "json", prompt],
            capture_output=True, text=True, timeout=180, env=clean_env,
        )

        if result.returncode != 0:
            stderr_snip = (result.stderr or "")[:200]
            stdout_snip = (result.stdout or "")[:200]
            combined = (stderr_snip + " " + stdout_snip).lower()
            auth_keywords = ("invalid api key", "not authenticated", "please run /login",
                             "authentication", "credentials", "401", "403", "unauthorized")
            if any(kw in combined for kw in auth_keywords) or (
                result.returncode == 1 and not stderr_snip.strip() and not stdout_snip.strip()
            ):
                analyze_headlines_with_opus.last_error = (
                    "auth_failure",
                    "claude CLI exited 1 with empty output — credentials likely expired. "
                    "Run `claude /login` on the host.",
                )
            else:
                analyze_headlines_with_opus.last_error = (
                    "cli_error",
                    f"claude CLI exited {result.returncode}: {stderr_snip or '(no stderr)'}",
                )
            log.warning(f"Opus analysis: claude CLI exited {result.returncode}: {stderr_snip}")
            return {}

        # Parse the response — claude --output-format json wraps in {"result": ...}
        raw = result.stdout.strip()
        if not raw:
            log.warning("Opus analysis: empty response from claude CLI")
            return {}

        outer = json.loads(raw)
        # claude --output-format json returns {"result": "...text..."} or the content directly
        if isinstance(outer, dict) and "result" in outer:
            inner_text = outer["result"]
            # The result field contains the JSON string Opus produced
            if isinstance(inner_text, str):
                # Strip any markdown fences if Opus added them despite instructions
                inner_text = inner_text.strip()
                if inner_text.startswith("```"):
                    inner_text = re.sub(r"^```(?:json)?\s*", "", inner_text)
                    inner_text = re.sub(r"\s*```\s*$", "", inner_text)
                analysis = json.loads(inner_text)
            elif isinstance(inner_text, dict):
                analysis = inner_text
            else:
                log.warning(f"Opus analysis: unexpected result type: {type(inner_text)}")
                return {}
        elif isinstance(outer, dict) and "tickers" in outer:
            # Direct JSON output (no wrapper)
            analysis = outer
        else:
            log.warning(f"Opus analysis: unexpected response structure")
            return {}

        # Validate expected keys exist
        for key in ("tickers", "movers", "sector_themes", "sentiment"):
            if key not in analysis:
                analysis[key] = [] if key != "sentiment" else ""
        for key in ("econ_events", "fed_signals"):
            if key not in analysis:
                analysis[key] = []

        # Store in normalized tables
        now = datetime.datetime.now().isoformat()

        for ticker in analysis.get("tickers", []):
            conn.execute(
                "INSERT INTO opus_tickers (market_date, ticker, analyzed_at) VALUES (?,?,?)",
                (market_date, ticker, now),
            )

        for m in analysis.get("movers", []):
            conn.execute(
                "INSERT INTO opus_movers (market_date, ticker, direction, reason, headline, analyzed_at) "
                "VALUES (?,?,?,?,?,?)",
                (market_date, m.get("ticker", ""), m.get("direction"),
                 m.get("reason"), m.get("headline"), now),
            )

        for t in analysis.get("sector_themes", []):
            conn.execute(
                "INSERT INTO opus_themes (market_date, sector, narrative, analyzed_at) VALUES (?,?,?,?)",
                (market_date, t.get("sector", ""), t.get("narrative"), now),
            )

        for e in analysis.get("econ_events", []):
            conn.execute(
                "INSERT INTO opus_econ_events (market_date, event, status, context, analyzed_at) "
                "VALUES (?,?,?,?,?)",
                (market_date, e.get("event", ""), e.get("status"), e.get("context"), now),
            )

        for sig in analysis.get("fed_signals", []):
            conn.execute(
                "INSERT INTO opus_fed_signals (market_date, signal, analyzed_at) VALUES (?,?,?)",
                (market_date, sig, now),
            )

        sentiment = analysis.get("sentiment", "")
        if sentiment:
            conn.execute(
                "INSERT OR REPLACE INTO opus_sentiment "
                "(market_date, sentiment, headline_count, model_used, analyzed_at) "
                "VALUES (?,?,?,?,?)",
                (market_date, sentiment, headline_count, "opus", now),
            )

        conn.commit()

        ticker_count = len(analysis.get("tickers", []))
        mover_count = len(analysis.get("movers", []))
        theme_count = len(analysis.get("sector_themes", []))
        log.info(f"Opus analysis: {ticker_count} tickers, {mover_count} movers, "
                 f"{theme_count} themes from {headline_count} headlines")
        return analysis

    except subprocess.TimeoutExpired:
        analyze_headlines_with_opus.last_error = (
            "timeout", "claude CLI timed out after 180s")
        log.warning("Opus analysis: claude CLI timed out after 180s")
        return {}
    except json.JSONDecodeError as e:
        analyze_headlines_with_opus.last_error = (
            "parse_error", f"claude CLI returned non-JSON: {e}")
        log.warning(f"Opus analysis: failed to parse JSON: {e}")
        log.debug(f"Opus raw output: {result.stdout[:500] if 'result' in dir() else 'N/A'}")
        return {}
    except FileNotFoundError:
        analyze_headlines_with_opus.last_error = (
            "binary_missing", f"claude CLI not found at {claude_bin}")
        log.warning(f"Opus analysis: claude CLI not found at {claude_bin}")
        return {}
    except Exception as e:
        analyze_headlines_with_opus.last_error = (
            "unexpected", f"unexpected error: {e}")
        log.warning(f"Opus analysis: unexpected error: {e}")
        return {}


# ── Phase 4: Validation ───────────────────────────────────────────────────────

def detect_anomalies(conn, market_date, log):
    """Flag quotes with z-score > threshold against 20-day history."""
    flagged = 0
    now = datetime.datetime.now().isoformat()

    # Get today's quotes
    today_quotes = conn.execute(
        "SELECT DISTINCT symbol, price FROM quotes "
        "WHERE market_date = ? AND price IS NOT NULL AND source = 'schwab'",
        (market_date,),
    ).fetchall()

    for row in today_quotes:
        sym, current_price = row["symbol"], row["price"]
        # Get 20-day history (excluding today)
        history = conn.execute(
            "SELECT price FROM quotes "
            "WHERE symbol = ? AND market_date < ? AND price IS NOT NULL AND source = 'schwab' "
            "ORDER BY market_date DESC LIMIT 20",
            (sym, market_date),
        ).fetchall()

        if len(history) < 5:  # Need at least 5 data points
            continue

        prices = [h["price"] for h in history]
        try:
            avg = statistics.mean(prices)
            std = statistics.stdev(prices)
            if std == 0:
                continue
            z = (current_price - avg) / std
            if abs(z) > ANOMALY_Z_THRESHOLD:
                conn.execute(
                    "INSERT INTO anomalies (symbol, field, current_value, avg_20d, "
                    "std_20d, z_score, flagged_at, market_date) "
                    "VALUES (?,?,?,?,?,?,?,?)",
                    (sym, "price", current_price, avg, std, z, now, market_date),
                )
                flagged += 1
                log.info(f"ANOMALY: {sym} price={current_price:.2f} avg={avg:.2f} z={z:.1f}")
        except statistics.StatisticsError:
            continue

    conn.commit()
    log.info(f"Anomaly detection: {flagged} flagged")
    return flagged


def cross_validate(conn, market_date, log):
    """Check data points available from multiple sources for consistency.

    Note: 10Y/30Y cross-validation removed — Schwab ($TNX/$TYX) is real-time,
    FRED is prev-day close, so discrepancies are expected intraday movement,
    not data errors. FRED now only provides 2Y Treasury (no Schwab equivalent).
    """
    flagged = 0
    conn.commit()
    log.info(f"Cross-validation: {flagged} discrepancies")
    return flagged


def retry_failed_calls(conn, market_date, log):
    """Retry any Schwab API calls that failed during collection.

    Queries source_health for errors, retries each one with a longer timeout.
    Runs between validation checks and briefing generation so the final
    output has complete data.
    """
    failures = conn.execute(
        "SELECT id, source, endpoint, error_message FROM source_health "
        "WHERE market_date = ? AND status = 'error' AND source = 'schwab'",
        (market_date,),
    ).fetchall()

    if not failures:
        log.info("Retry check: 0 failures — nothing to retry")
        return 0

    log.info(f"Retry check: {len(failures)} failed call(s) found, retrying...")
    retried = 0
    recovered = 0
    retry_timeout = SCHWAB_TIMEOUT * 2  # double the timeout for retries

    for row in failures:
        health_id, source, endpoint, err_msg = row
        url = f"{SCHWAB_BASE}{endpoint}"
        sym = endpoint.rsplit("/", 1)[-1].split("?")[0]  # extract symbol from path

        # Determine endpoint type
        if "/api/technicals/" in endpoint:
            retry_type = "technicals"
            delay = TECH_DELAY
        elif "/api/history/" in endpoint:
            retry_type = "sma200"
            delay = CHUNK_DELAY
        elif "/api/calendar/" in endpoint:
            retry_type = "earnings"
            delay = CHUNK_DELAY
        elif "/api/quotes" in endpoint:
            retry_type = "quotes"
            delay = CHUNK_DELAY
        else:
            log.debug(f"  Retry skip: unknown endpoint type {endpoint}")
            continue

        retried += 1
        log.info(f"  Retrying {retry_type} for {sym} (original error: {err_msg})")
        time.sleep(delay)

        try:
            data, elapsed = fetch_json(url, timeout=retry_timeout, retries=0)
            now = datetime.datetime.now().isoformat()

            if retry_type == "technicals":
                tech = data.get("technicals", data)
                conn.execute(
                    "INSERT INTO technicals (symbol, rsi_14, sma_20, sma_50, sma_200, "
                    "atr_14, bb_upper, bb_lower, macd, macd_signal, source, "
                    "fetched_at, market_date) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (sym,
                     tech.get("rsi_14") or tech.get("rsi"),
                     tech.get("sma_20") or tech.get("sma20"),
                     tech.get("sma_50") or tech.get("sma50"),
                     tech.get("sma_200") or tech.get("sma200"),
                     tech.get("atr_14") or tech.get("atr"),
                     tech.get("bb_upper") or tech.get("bbUpper"),
                     tech.get("bb_lower") or tech.get("bbLower"),
                     tech.get("macd"),
                     tech.get("macd_signal") or tech.get("macdSignal"),
                     "schwab", now, market_date),
                )
                recovered += 1

            elif retry_type == "sma200":
                candles = data.get("candles", [])
                if len(candles) >= 200:
                    closes = [c["close"] for c in candles[-200:]]
                    sma200 = sum(closes) / 200
                    conn.execute(
                        "INSERT INTO levels (symbol, level_type, price, strength, "
                        "source, fetched_at, market_date) VALUES (?,?,?,?,?,?,?)",
                        (sym, "sma_200", round(sma200, 2), None, "schwab", now, market_date))
                    recovered += 1
                else:
                    log.info(f"  Retry {sym} SMA200: only {len(candles)} candles (need 200)")

            elif retry_type == "earnings":
                items = data if isinstance(data, list) else [data]
                for item in items:
                    report_date = (item.get("next_earnings") or item.get("reportDate")
                                   or item.get("earnings_date") or item.get("date"))
                    if not report_date or not item.get("has_earnings", True):
                        continue
                    conn.execute(
                        "INSERT INTO earnings (symbol, report_date, report_time, "
                        "eps_estimate, eps_actual, revenue_estimate, revenue_actual, "
                        "source, fetched_at, market_date) VALUES (?,?,?,?,?,?,?,?,?,?)",
                        (sym, report_date,
                         item.get("earnings_time") or item.get("reportTime") or item.get("time"),
                         item.get("epsEstimate") or item.get("eps_estimate"),
                         item.get("epsActual") or item.get("eps_actual"),
                         item.get("revenueEstimate") or item.get("revenue_estimate"),
                         item.get("revenueActual") or item.get("revenue_actual"),
                         "schwab", now, market_date),
                    )
                    recovered += 1
                    break  # one earnings entry per symbol

            # Mark the retry as successful in source_health
            log_health(conn, market_date, "schwab", endpoint, "ok",
                       elapsed, data_points=1, error_msg=f"retry OK (was: {err_msg})")
            log.info(f"  ✓ {sym} {retry_type} recovered")

        except Exception as e:
            log.info(f"  ✗ {sym} {retry_type} retry failed: {e}")
            log_health(conn, market_date, "schwab", endpoint, "error",
                       0, error_msg=f"retry failed: {e}")

    conn.commit()
    log.info(f"Retry complete: {recovered}/{retried} recovered")
    return recovered


def calculate_completeness(conn, market_date):
    """Calculate what fraction of expected data points we collected."""
    required = {
        "us_indices": (4, "SELECT COUNT(DISTINCT symbol) FROM quotes WHERE market_date = ? AND source = 'schwab' AND symbol IN ('$SPX','$COMPX','$DJI','$RUT')"),
        "futures": (4, "SELECT COUNT(DISTINCT symbol) FROM quotes WHERE market_date = ? AND source = 'schwab' AND symbol LIKE '/%'"),
        "vix": (1, "SELECT COUNT(*) FROM quotes WHERE market_date = ? AND symbol = '$VIX'"),
        "treasuries": (3, "SELECT COUNT(DISTINCT symbol) FROM quotes WHERE market_date = ? AND symbol IN ('$TNX','$TYX','DGS2','DGS10','DGS30')"),
        "commodities": (3, "SELECT COUNT(DISTINCT symbol) FROM quotes WHERE market_date = ? AND source = 'schwab' AND (symbol LIKE '/CL%' OR symbol LIKE '/BZ%' OR symbol LIKE '/GC%')"),
        "crypto": (2, "SELECT COUNT(DISTINCT symbol) FROM quotes WHERE market_date = ? AND symbol IN ('BTC','ETH')"),
        "international": (4, "SELECT COUNT(DISTINCT symbol) FROM quotes WHERE market_date = ? AND source = 'schwab' AND symbol IN ('$N225','$DAX','$HSI','$FCHI')"),
        "gap_fills": (3, "SELECT COUNT(DISTINCT symbol) FROM quotes WHERE market_date = ? AND symbol IN ('FTSE','KOSPI','DXY')"),
        "econ_calendar": (1, "SELECT COUNT(*) FROM source_health WHERE market_date = ? AND source = 'econ_calendar' AND status = 'ok'"),
        "market_context": (1, "SELECT COUNT(*) FROM market_context WHERE market_date = ?"),
        "opus_analysis": (1, "SELECT COUNT(*) FROM opus_sentiment WHERE market_date = ?"),
        "rss": (3, "SELECT MIN(3, COUNT(DISTINCT feed_name)) FROM headlines WHERE market_date = ?"),
        "watchlist_t1": (len(get_tier_tickers(1)), f"SELECT COUNT(DISTINCT symbol) FROM quotes WHERE market_date = ? AND source = 'schwab' AND symbol IN ({','.join('?' for _ in get_tier_tickers(1))})"),
    }

    total_expected = 0
    total_present = 0
    details = {}

    for key, (expected, query) in required.items():
        total_expected += expected
        params = [market_date]
        if key == "watchlist_t1":
            params += get_tier_tickers(1)
        row = conn.execute(query, params).fetchone()
        present = min(row[0], expected) if row else 0
        total_present += present
        details[key] = (present, expected)

    score = total_present / total_expected if total_expected > 0 else 0
    return score, details


# ── Briefing File Generator ───────────────────────────────────────────────────

def get_best_quote(conn, market_date, symbol):
    """Get highest-priority quote for a symbol. Priority: schwab > stooq > fred > coingecko > yahoo."""
    row = conn.execute(
        "SELECT *, CASE source "
        "  WHEN 'schwab' THEN 1 WHEN 'stooq' THEN 2 WHEN 'fred' THEN 3 "
        "  WHEN 'coingecko' THEN 4 WHEN 'yahoo' THEN 5 ELSE 9 END as prio "
        "FROM quotes WHERE market_date = ? AND (symbol = ? OR symbol LIKE ?)"
        "ORDER BY prio LIMIT 1",
        (market_date, symbol, f"{symbol}%"),
    ).fetchone()
    return row


def fmt_price(price):
    """Format price for display."""
    if price is None:
        return "—"
    if abs(price) >= 10000:
        return f"{price:,.0f}"
    if abs(price) >= 100:
        return f"{price:,.0f}"
    if abs(price) >= 1:
        return f"{price:.2f}"
    return f"{price:.4f}"


def fmt_change(pct):
    """Format percentage change."""
    if pct is None:
        return "—"
    return f"{pct:+.2f}%"


def determine_event_load(conn, market_date):
    """Determine LIGHT/MEDIUM/HEAVY based on economic calendar."""
    events = conn.execute(
        "SELECT event_name, impact FROM economic_events WHERE market_date = ?",
        (market_date,),
    ).fetchall()

    heavy_count = 0
    high_count = 0
    for ev in events:
        name = (ev["event_name"] or "").upper()
        impact = (ev["impact"] or "").upper()
        if any(h.upper() in name for h in HEAVY_EVENTS):
            heavy_count += 1
        if impact in ("HIGH", "3", "RED"):
            high_count += 1

    if heavy_count > 0 or high_count >= 3:
        return "HEAVY"
    elif high_count >= 1 or len(events) >= 5:
        return "MEDIUM"
    return "LIGHT"


def generate_briefing(conn, market_date, log):
    """Generate the structured briefing markdown file."""
    output_path = DATA_DIR / f"briefing-{market_date}.md"
    score, details = calculate_completeness(conn, market_date)
    event_load = determine_event_load(conn, market_date)
    now_str = datetime.datetime.now().strftime("%H:%M:%S PT")
    day_name = datetime.date.fromisoformat(market_date).strftime("%A, %B %-d, %Y")

    lines = []
    w = lines.append  # shorthand

    # ── Header ──
    w(f"# Morning Brief Data — {day_name}")
    w("")
    total_pts = sum(d[1] for d in details.values())
    present_pts = sum(d[0] for d in details.values())
    w(f"**Collection Time:** {now_str}")
    w(f"**Completeness Score:** {score:.0%} ({present_pts}/{total_pts} data points)")
    w(f"**Event Load:** {event_load}")
    w("")

    # ── Data Quality Notes ──
    w("> **Data Quality Notes:**")
    # Failed sources
    failures = conn.execute(
        "SELECT source, endpoint, error_message FROM source_health "
        "WHERE market_date = ? AND status = 'error' "
        "ORDER BY source",
        (market_date,),
    ).fetchall()
    if failures:
        seen_sources = set()
        for f in failures:
            src = f["source"]
            if src not in seen_sources:
                seen_sources.add(src)
                w(f"> - {src}: {f['error_message'][:80]}")
    # Anomalies
    anomalies = conn.execute(
        "SELECT symbol, current_value, z_score FROM anomalies WHERE market_date = ?",
        (market_date,),
    ).fetchall()
    for a in anomalies:
        w(f"> - ANOMALY: {a['symbol']} = {fmt_price(a['current_value'])} (z-score: {a['z_score']:.1f})")
    # Cross-validation discrepancies
    xvals = conn.execute(
        "SELECT data_point, source_a, value_a, source_b, value_b, discrepancy_pct "
        "FROM cross_validations WHERE market_date = ?",
        (market_date,),
    ).fetchall()
    for xv in xvals:
        w(f"> - DISCREPANCY: {xv['data_point']}: {xv['source_a']}={xv['value_a']:.3f} vs {xv['source_b']}={xv['value_b']:.3f} ({xv['discrepancy_pct']:.2f}% off)")
    if not failures and not anomalies and not xvals:
        w("> - All sources healthy, no anomalies detected")
    w("")
    w("---")
    w("")

    # ── Pre-Market Snapshot ──
    w("## Pre-Market Snapshot")
    w("")
    w("| Instrument | Level | Change | Source |")
    w("|-----------|-------|--------|--------|")

    snapshot_items = [
        ("/ES", "S&P 500 Futures"), ("/NQ", "Nasdaq 100 Futures"),
        ("/YM", "Dow Futures"), ("/RTY", "Russell 2000 Futures"),
        ("$VIX", "VIX"),
    ]
    for sym, name in snapshot_items:
        q = get_best_quote(conn, market_date, sym)
        if q:
            w(f"| {name} | {fmt_price(q['price'])} | {fmt_change(q['change_pct'])} | {q['source']} |")
        else:
            w(f"| {name} | — | — | — |")

    # Yields — special handling
    tnx = get_best_quote(conn, market_date, "$TNX")
    tyx = get_best_quote(conn, market_date, "$TYX")
    dgs2 = get_best_quote(conn, market_date, "DGS2")
    dgs10 = get_best_quote(conn, market_date, "DGS10")

    # 10Y: prefer Schwab (live), show FRED for comparison
    if tnx and tnx["price"]:
        y10 = tnx["price"] / 10
        w(f"| 10Y Yield | {y10:.3f}% | {fmt_change(tnx['change_pct'])} | schwab ($TNX÷10) |")
    elif dgs10 and dgs10["price"]:
        w(f"| 10Y Yield | {dgs10['price']:.3f}% | — | fred (prev close) |")
    else:
        w("| 10Y Yield | — | — | — |")

    # 2Y: FRED only
    if dgs2 and dgs2["price"]:
        w(f"| 2Y Yield | {dgs2['price']:.3f}% | — | fred (prev close) |")
    else:
        w("| 2Y Yield | — | — | — |")

    # 30Y: Schwab or FRED
    if tyx and tyx["price"]:
        y30 = tyx["price"] / 10
        w(f"| 30Y Yield | {y30:.3f}% | {fmt_change(tyx['change_pct'])} | schwab ($TYX÷10) |")
    else:
        dgs30 = get_best_quote(conn, market_date, "DGS30")
        if dgs30 and dgs30["price"]:
            w(f"| 30Y Yield | {dgs30['price']:.3f}% | — | fred (prev close) |")
        else:
            w("| 30Y Yield | — | — | — |")

    # 2s/10s spread (calculated)
    y2 = dgs2["price"] if dgs2 and dgs2["price"] else None
    y10_val = (tnx["price"] / 10) if (tnx and tnx["price"]) else (dgs10["price"] if dgs10 and dgs10["price"] else None)
    if y2 is not None and y10_val is not None:
        spread = y10_val - y2
        w(f"| 2s/10s Spread | {spread:+.3f}% | — | calculated |")
    else:
        w("| 2s/10s Spread | — | — | — |")

    # DXY
    dxy = get_best_quote(conn, market_date, "DXY")
    if dxy:
        w(f"| DXY | {fmt_price(dxy['price'])} | {fmt_change(dxy['change_pct'])} | {dxy['source']} |")
    else:
        uup = get_best_quote(conn, market_date, "UUP")
        if uup:
            w(f"| Dollar (UUP proxy) | {fmt_price(uup['price'])} | {fmt_change(uup['change_pct'])} | {uup['source']} |")
        else:
            w("| DXY | — | — | — |")

    # Commodities
    for sym, name in [("/CL", "WTI Crude"), ("/BZ", "Brent Crude"), ("/GC", "Gold")]:
        q = get_best_quote(conn, market_date, sym)
        if q:
            w(f"| {name} | {fmt_price(q['price'])} | {fmt_change(q['change_pct'])} | {q['source']} |")
        else:
            w(f"| {name} | — | — | — |")

    # Crypto
    for sym, name in [("BTC", "Bitcoin"), ("ETH", "Ethereum")]:
        q = get_best_quote(conn, market_date, sym)
        if q:
            w(f"| {name} | ${fmt_price(q['price'])} | {fmt_change(q['change_pct'])} | {q['source']} |")
        else:
            w(f"| {name} | — | — | — |")

    w("")
    w("---")
    w("")

    # ── Global Markets ──
    w("## Global Markets")
    w("")
    w("| Market | Level | Change | Source |")
    w("|--------|-------|--------|--------|")

    global_items = [
        ("$N225", "Nikkei 225"), ("$HSI", "Hang Seng"),
        ("$DAX", "DAX"), ("$FCHI", "CAC 40"),
        ("FTSE", "FTSE 100"), ("KOSPI", "Kospi"),
        ("FEZ", "Europe STOXX 50 (FEZ)"), ("IEV", "Europe Broad (IEV)"),
        ("EWA", "Australia (EWA)"),
    ]
    for sym, name in global_items:
        q = get_best_quote(conn, market_date, sym)
        if q:
            w(f"| {name} | {fmt_price(q['price'])} | {fmt_change(q['change_pct'])} | {q['source']} |")
        else:
            w(f"| {name} | — | — | — |")

    w("")
    w("---")
    w("")

    # ── US Indices (Previous Close) ──
    w("## US Indices (Previous Close)")
    w("")
    w("| Index | Level | Change | Source |")
    w("|-------|-------|--------|--------|")
    for sym, name in [("$SPX", "S&P 500"), ("$COMPX", "Nasdaq"), ("$DJI", "Dow"), ("$RUT", "Russell 2000")]:
        q = get_best_quote(conn, market_date, sym)
        if q:
            w(f"| {name} | {fmt_price(q['price'])} | {fmt_change(q['change_pct'])} | {q['source']} |")
        else:
            w(f"| {name} | — | — | — |")

    w("")
    w("---")
    w("")

    # ── Economic Calendar ──
    w("## Economic Calendar")
    w("")
    events = conn.execute(
        "SELECT * FROM economic_events WHERE market_date = ? ORDER BY event_time",
        (market_date,),
    ).fetchall()

    if events:
        w("| Time (ET) | Event | Impact | Forecast | Previous | Actual |")
        w("|-----------|-------|--------|----------|----------|--------|")
        for ev in events:
            actual = ev["actual"] if ev["actual"] is not None else "—"
            w(f"| {utc_to_et(ev['event_time'] or '—')} | {ev['event_name']} | {ev['impact'] or '—'} | {ev['forecast'] or '—'} | {ev['previous'] or '—'} | {actual} |")
        w("")
        w("**IMPORTANT:** Events with Actual = \"—\" have NOT been released yet. Do NOT report actual values for these events. Write \"Pending\" or \"Scheduled for [time]\".")
    else:
        w("No scheduled economic releases today.")
    w("")
    w("---")
    w("")

    # ── Market Movers (auto-detected from quotes) ──
    w("## Market Movers (Auto-detected: |change| > 3%)")
    w("")
    big_movers = conn.execute(
        "SELECT q.symbol, q.price, q.change_pct, w.sector, w.tier "
        "FROM quotes q LEFT JOIN watchlist w ON q.symbol = w.symbol "
        "WHERE q.market_date = ? AND q.source = 'schwab' AND ABS(q.change_pct) > 3.0 "
        "ORDER BY q.change_pct DESC",
        (market_date,),
    ).fetchall()
    if big_movers:
        w("| Symbol | Price | Change | Sector | Tier |")
        w("|--------|-------|--------|--------|------|")
        for m in big_movers:
            w(f"| {m['symbol']} | {fmt_price(m['price'])} | {fmt_change(m['change_pct'])} | {m['sector'] or '—'} | {m['tier'] or '—'} |")
        w("")
    else:
        w("No stocks moved more than 3% today.")
        w("")

    # ── Opus-identified movers (from normalized tables) ──
    opus_movers = conn.execute(
        "SELECT ticker, direction, reason, headline FROM opus_movers WHERE market_date = ?",
        (market_date,),
    ).fetchall()
    if opus_movers:
        w("### News-Driven Movers (Opus Analysis)")
        w("| Symbol | Direction | Reason | Headline |")
        w("|--------|-----------|--------|----------|")
        for om in opus_movers:
            w(f"| {om['ticker']} | {om['direction'] or '—'} | {om['reason'] or '—'} | {om['headline'] or '—'} |")
        w("")

    w("---")
    w("")

    # ── Market Intelligence (Opus Feed Analysis) ──
    themes = conn.execute(
        "SELECT sector, narrative FROM opus_themes WHERE market_date = ?",
        (market_date,),
    ).fetchall()
    econ = conn.execute(
        "SELECT event, status, context FROM opus_econ_events WHERE market_date = ?",
        (market_date,),
    ).fetchall()
    fed = conn.execute(
        "SELECT signal FROM opus_fed_signals WHERE market_date = ?",
        (market_date,),
    ).fetchall()
    sentiment_row = conn.execute(
        "SELECT sentiment FROM opus_sentiment WHERE market_date = ?",
        (market_date,),
    ).fetchone()

    if themes or econ or fed or sentiment_row:
        w("## Market Intelligence (Opus Feed Analysis)")
        w("")

        if themes:
            w("### Sector Themes")
            for t in themes:
                w(f"- **{t['sector']}:** {t['narrative'] or '—'}")
            w("")

        if econ:
            w("### Economic Context")
            for e in econ:
                status = f" ({e['status']})" if e["status"] else ""
                w(f"- {e['event']}{status}: {e['context'] or '—'}")
            w("")

        if fed:
            w("### Fed Signals")
            for f_row in fed:
                w(f"- {f_row['signal']}")
            w("")

        if sentiment_row:
            w("### Overall Sentiment")
            w(f"{sentiment_row['sentiment']}")
            w("")

        w("---")
        w("")

    # ── Earnings Calendar ──
    w("## Earnings Calendar")
    w("")
    earnings = conn.execute(
        "SELECT e.*, w.sector, w.tier FROM earnings e "
        "LEFT JOIN watchlist w ON e.symbol = w.symbol "
        "WHERE e.market_date = ? ORDER BY w.tier, e.report_time",
        (market_date,),
    ).fetchall()

    # Today's earnings
    today_earnings = [e for e in earnings if e["report_date"] == market_date]
    if today_earnings:
        w("### Reporting Today")
        w("| Symbol | Sector | Time | EPS Est | EPS Actual |")
        w("|--------|--------|------|---------|------------|")
        for e in today_earnings:
            actual = f"{e['eps_actual']:.2f}" if e["eps_actual"] is not None else "—"
            est = f"{e['eps_estimate']:.2f}" if e["eps_estimate"] is not None else "—"
            w(f"| {e['symbol']} | {e['sector'] or '—'} | {e['report_time'] or '—'} | {est} | {actual} |")
        w("")
        w("**IMPORTANT:** Earnings with EPS Actual = \"—\" have NOT been reported yet. Do NOT fabricate results.")
    else:
        w("No watchlist earnings reporting today.")
    w("")

    # Upcoming earnings (next 5 trading days)
    upcoming = [e for e in earnings if e["report_date"] and e["report_date"] > market_date]
    if upcoming:
        w("### Upcoming Watchlist Earnings")
        w("| Symbol | Sector | Date | Time | EPS Est |")
        w("|--------|--------|------|------|---------|")
        for e in upcoming[:20]:
            est = f"{e['eps_estimate']:.2f}" if e["eps_estimate"] is not None else "—"
            w(f"| {e['symbol']} | {e['sector'] or '—'} | {e['report_date']} | {e['report_time'] or '—'} | {est} |")
        w("")

    w("---")
    w("")

    # ── Watchlist Quotes ──
    w("## Thesis Watchlist — Tier 1 (with Technicals)")
    w("")
    w("| Symbol | Sector | Price | Change | RSI | SMA20 | SMA50 | SMA200 |")
    w("|--------|--------|-------|--------|-----|-------|-------|--------|")

    tier1 = get_tier_tickers(1)
    for sym in sorted(tier1):
        q = get_best_quote(conn, market_date, sym)
        tech = conn.execute(
            "SELECT * FROM technicals WHERE symbol = ? AND market_date = ?",
            (sym, market_date),
        ).fetchone()
        wl = get_all_watchlist_tickers().get(sym, ("—", 0))

        price_str = fmt_price(q["price"]) if q else "—"
        change_str = fmt_change(q["change_pct"]) if q else "—"
        rsi = f"{tech['rsi_14']:.0f}" if tech and tech["rsi_14"] else "—"
        sma20 = fmt_price(tech["sma_20"]) if tech and tech["sma_20"] else "—"
        sma50 = fmt_price(tech["sma_50"]) if tech and tech["sma_50"] else "—"
        sma200_val = tech["sma_200"] if tech and tech["sma_200"] else None
        if not sma200_val:
            lvl_row = conn.execute(
                "SELECT price FROM levels WHERE symbol = ? AND market_date = ? AND level_type = 'sma_200'",
                (sym, market_date),
            ).fetchone()
            if lvl_row:
                sma200_val = lvl_row["price"]
        sma200 = fmt_price(sma200_val) if sma200_val else "—"

        w(f"| {sym} | {wl[0]} | {price_str} | {change_str} | {rsi} | {sma20} | {sma50} | {sma200} |")

    w("")

    # Tier 2+3 (price only)
    w("## Thesis Watchlist — Tier 2/3 (Price Only)")
    w("")
    w("| Symbol | Sector | Tier | Price | Change |")
    w("|--------|--------|------|-------|--------|")

    tier23 = [(s, info) for s, info in get_all_watchlist_tickers().items() if info[1] >= 2]
    for sym, (sector, tier) in sorted(tier23, key=lambda x: (x[1][1], x[1][0], x[0])):
        q = get_best_quote(conn, market_date, sym)
        price_str = fmt_price(q["price"]) if q else "—"
        change_str = fmt_change(q["change_pct"]) if q else "—"
        w(f"| {sym} | {sector} | {tier} | {price_str} | {change_str} |")

    w("")
    w("---")
    w("")

    # ── Key Technical Levels ──
    w("## Key Technical Levels")
    w("")
    all_level_syms = conn.execute(
        "SELECT DISTINCT symbol FROM levels WHERE market_date = ? ORDER BY symbol",
        (market_date,),
    ).fetchall()

    if all_level_syms:
        w("| Symbol | Level Type | Price | Strength |")
        w("|--------|-----------|-------|----------|")
        for row in all_level_syms:
            sym = row["symbol"]
            lvls = conn.execute(
                "SELECT * FROM levels WHERE symbol = ? AND market_date = ? ORDER BY price",
                (sym, market_date),
            ).fetchall()
            for lvl in lvls:
                w(f"| {sym} | {lvl['level_type']} | {fmt_price(lvl['price'])} | {lvl['strength'] or '—'} |")
    else:
        w("No technical levels data available.")
    w("")
    w("---")
    w("")

    # ── Market Context ──
    w("## Market Context")
    w("")
    ctx = conn.execute(
        "SELECT * FROM market_context WHERE market_date = ? ORDER BY id DESC LIMIT 1",
        (market_date,),
    ).fetchone()

    if ctx:
        w(f"- **VIX Level:** {ctx['vix_level'] or '—'}")
        w(f"- **VIX Regime:** {ctx['vix_regime'] or '—'}")
        w(f"- **SPY Trend:** {ctx['spy_trend'] or '—'}")
        w(f"- **Risk Appetite:** {ctx['risk_appetite'] or '—'}")
        if ctx["spy_sma50_distance"]:
            w(f"- **SPY Distance from 50-day SMA:** {ctx['spy_sma50_distance']:.1f}%")
    else:
        w("Market context data unavailable.")
    w("")
    w("---")
    w("")

    # ── News Headlines ──
    w("## News Headlines (Last 24 Hours)")
    w("")
    for category, cat_label in [
        ("markets_macro", "Markets & Macro"),
        ("earnings_movers", "Earnings & Movers"),
        ("fed_policy", "Fed & Policy"),
        ("crypto", "Crypto"),
        ("defense_aerospace", "Defense & Aerospace"),
        ("space", "Space"),
        ("nuclear_energy", "Nuclear Energy"),
        ("semiconductors", "Semiconductors"),
        ("cybersecurity", "Cybersecurity"),
        ("quantum_computing", "Quantum Computing"),
        ("critical_minerals", "Critical Minerals"),
        ("robotics_automation", "Robotics & Automation"),
        ("energy_storage", "Energy Storage"),
    ]:
        headlines = conn.execute(
            "SELECT DISTINCT title, feed_name, link, published_at FROM headlines "
            "WHERE market_date = ? AND feed_category = ? "
            "ORDER BY published_at DESC LIMIT 10",
            (market_date, category),
        ).fetchall()
        if headlines:
            w(f"### {cat_label}")
            for h in headlines:
                pub = f" ({h['published_at'][:16]})" if h["published_at"] else ""
                w(f"- [{h['feed_name']}] {h['title']}{pub}")
            w("")

    w("---")
    w("")

    # ── Source Health Summary ──
    w("## Source Health Summary")
    w("")
    w("| Source | Calls | OK | Errors | Avg Response (ms) |")
    w("|--------|-------|-----|--------|-------------------|")
    health = conn.execute(
        "SELECT source, COUNT(*) as calls, "
        "SUM(CASE WHEN status = 'ok' THEN 1 ELSE 0 END) as ok, "
        "SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as errors, "
        "AVG(CASE WHEN status = 'ok' THEN response_time_ms END) as avg_ms "
        "FROM source_health WHERE market_date = ? GROUP BY source ORDER BY source",
        (market_date,),
    ).fetchall()
    for h in health:
        avg = f"{h['avg_ms']:.0f}" if h["avg_ms"] else "—"
        w(f"| {h['source']} | {h['calls']} | {h['ok']} | {h['errors']} | {avg} |")
    w("")

    # Write file
    content = "\n".join(lines) + "\n"
    output_path.write_text(content)
    log.info(f"Briefing file written: {output_path} ({len(content)} bytes)")
    return output_path


# ── Data Retention Cleanup ─────────────────────────────────────────────────────

def cleanup_old_data(conn, log):
    """Prune data older than retention period and VACUUM."""
    today = datetime.date.today()
    for table, days in RETENTION_DAYS.items():
        cutoff = (today - datetime.timedelta(days=days)).isoformat()
        try:
            cursor = conn.execute(f"DELETE FROM {table} WHERE market_date < ?", (cutoff,))
            if cursor.rowcount > 0:
                log.info(f"Pruned {cursor.rowcount} rows from {table} (older than {days} days)")
        except sqlite3.OperationalError:
            # Table might not have market_date (e.g., watchlist)
            pass

    # Prune briefing files older than 1 year
    cutoff_date = today - datetime.timedelta(days=365)
    for f in DATA_DIR.glob("briefing-*.md"):
        try:
            file_date = datetime.date.fromisoformat(f.stem.replace("briefing-", ""))
            if file_date < cutoff_date:
                f.unlink()
                log.info(f"Pruned old briefing: {f.name}")
        except ValueError:
            pass

    # VACUUM requires no open transaction
    conn.commit()
    conn.execute("VACUUM")
    log.info("Cleanup complete")


# ── Main Orchestrator ──────────────────────────────────────────────────────────

def setup_logging(market_date):
    """Configure logging to file and stdout."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / f"collect-{market_date}.log"

    log = logging.getLogger("collect")
    log.setLevel(logging.DEBUG)
    log.handlers.clear()

    # File handler (DEBUG level)
    fh = logging.FileHandler(str(log_file))
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    log.addHandler(fh)

    # Console handler (INFO level)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    log.addHandler(ch)

    return log


def send_warning_email(market_date, step, error_detail, log):
    """Send non-fatal warning email via msmtp.

    Called when a pipeline step has partial failures but can continue.
    """
    import shutil
    if not shutil.which("msmtp"):
        log.error("Cannot send warning email: msmtp not installed")
        return False

    hostname = os.uname().nodename
    log_file = LOG_DIR / f"collect-{market_date}.log"
    subject = f"[WARNING] Market Data Collection — {market_date}"

    body = f"""Market data collection hit a non-fatal issue on {hostname}.

Step: {step}
Date: {market_date}
Issue: {error_detail}

The pipeline is continuing with available data.

Log file: {log_file}
"""

    try:
        msg = (
            f"From: collect-market-data@{hostname}\n"
            f"To: {FAILURE_EMAIL}\n"
            f"Subject: {subject}\n"
            f"Content-Type: text/plain; charset=utf-8\n"
            f"\n"
            f"{body}"
        )
        result = subprocess.run(
            ["msmtp", FAILURE_EMAIL],
            input=msg, text=True, capture_output=True, timeout=30,
        )
        if result.returncode == 0:
            log.info(f"Warning email sent to {FAILURE_EMAIL}")
            return True
        else:
            log.error(f"msmtp failed (exit {result.returncode}): {result.stderr[:200]}")
            return False
    except Exception as e:
        log.error(f"Failed to send warning email: {e}")
        return False


def send_failure_email(market_date, step, error_detail, log):
    """Send failure notification email via msmtp.

    Called when any pipeline step fails fatally. Includes the step that failed,
    the error detail, and a pointer to the log file for full context.
    """
    import shutil
    if not shutil.which("msmtp"):
        log.error("Cannot send failure email: msmtp not installed")
        return False

    hostname = os.uname().nodename
    log_file = LOG_DIR / f"collect-{market_date}.log"
    tag = "AUTH" if "auth" in step.lower() else "FAILED"
    subject = f"[{tag}] Market Data Collection — {market_date}"

    body = f"""Market data collection failed on {hostname}.

Step: {step}
Date: {market_date}
Error: {error_detail}

Log file: {log_file}

This pipeline will need manual intervention before the morning brief can run.
"""

    try:
        msg = (
            f"From: collect-market-data@{hostname}\n"
            f"To: {FAILURE_EMAIL}\n"
            f"Subject: {subject}\n"
            f"Content-Type: text/plain; charset=utf-8\n"
            f"\n"
            f"{body}"
        )
        result = subprocess.run(
            ["msmtp", FAILURE_EMAIL],
            input=msg, text=True, capture_output=True, timeout=30,
        )
        if result.returncode == 0:
            log.info(f"Failure email sent to {FAILURE_EMAIL}")
            return True
        else:
            log.error(f"msmtp failed (exit {result.returncode}): {result.stderr[:200]}")
            return False
    except Exception as e:
        log.error(f"Failed to send email: {e}")
        return False


def get_market_date(override=None):
    """Get the market date (today, adjusted for weekends)."""
    if override:
        return override
    today = datetime.date.today()
    dow = today.isoweekday()  # 1=Mon, 7=Sun
    if dow == 6:  # Saturday
        today += datetime.timedelta(days=2)
    elif dow == 7:  # Sunday
        today += datetime.timedelta(days=1)
    return today.isoformat()


def main():
    # Parse args
    args = sys.argv[1:]
    cleanup_only = "--cleanup" in args
    briefing_only = "--briefing-only" in args
    date_override = None
    for i, arg in enumerate(args):
        if arg == "--date" and i + 1 < len(args):
            date_override = args[i + 1]

    market_date = get_market_date(date_override)
    log = setup_logging(market_date)
    log.info(f"=== Market Data Collection — {market_date} ===")

    conn = init_db()

    if cleanup_only:
        cleanup_old_data(conn, log)
        conn.close()
        return 0

    if briefing_only:
        generate_briefing(conn, market_date, log)
        conn.close()
        return 0

    def fail(step, detail):
        """Log failure, email notification, and exit."""
        log.error(f"PIPELINE FAILED at {step}: {detail}")
        send_failure_email(market_date, step, detail, log)
        conn.close()
        return 2

    try:
        # Fresh run — clear today's data and start clean
        clear_today(conn, market_date)
        populate_watchlist(conn, market_date)

        # Record collection start
        started_at = datetime.datetime.now().isoformat()
        conn.execute(
            "INSERT INTO collections (started_at, market_date) VALUES (?, ?)",
            (started_at, market_date),
        )
        conn.commit()
        collection_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        failed_sources = set()
        step_results = {}

        # ── STEP 1: RSS Feeds (FIRST — drives everything else) ──
        log.info("── Step 1: RSS Feeds ──")
        t0 = time.monotonic()
        s1_headlines, s1_failed = collect_rss_feeds(conn, market_date, log)
        s1_time = time.monotonic() - t0
        log.info(f"Step 1 complete: {s1_time:.1f}s (headlines={s1_headlines})")

        # Individual RSS feed failures are non-fatal — send a warning email
        # and continue with whatever headlines we got. Only abort if we got
        # zero headlines (i.e. every single feed failed or returned empty).
        if s1_failed:
            detail = "\n".join(f"  {name} ({url}): {err}" for name, url, err in s1_failed)
            log.error(f"RSS feeds: {len(s1_failed)} feed(s) FAILED:\n{detail}")
            send_warning_email(market_date, "Step 1 (RSS)",
                               f"{len(s1_failed)} feed(s) failed (continuing with {s1_headlines} headlines):\n{detail}", log)

        if s1_headlines == 0:
            return fail("Step 1 (RSS)", "Zero headlines collected — all feeds returned empty or failed")

        step_results["step1_rss"] = "ok"

        # ── STEP 2: Opus Analysis ──
        log.info("── Step 2: Opus Feed Analysis ──")
        t0 = time.monotonic()
        opus_analysis = analyze_headlines_with_opus(conn, market_date, log)
        opus_tickers = opus_analysis.get("tickers", [])
        s2_time = time.monotonic() - t0
        log.info(f"Step 2 complete: {s2_time:.1f}s (opus_tickers={len(opus_tickers)})")

        if not opus_analysis:
            err = getattr(analyze_headlines_with_opus, "last_error", None)
            if err and err[0] == "auth_failure":
                return fail("Step 2 (Opus auth)", err[1])
            elif err:
                return fail(f"Step 2 (Opus {err[0]})", err[1])
            else:
                return fail("Step 2 (Opus)",
                            "Opus feed analysis returned empty — claude CLI may be down or timed out")
        step_results["step2_opus"] = "ok"

        # ── STEP 3: Collect Numbers (Schwab + External APIs) ──
        log.info("── Step 3: Schwab + External APIs ──")
        t0 = time.monotonic()

        # Quick Schwab health check
        try:
            fetch_json(f"{SCHWAB_BASE}/api/quotes?symbols=$SPX", timeout=5, retries=0)
            schwab_ok = True
        except Exception as e:
            return fail("Step 3 (Schwab)", f"Schwab proxy unreachable at {SCHWAB_BASE}: {e}")

        # 3a. Quotes (watchlist + core + opus-discovered tickers)
        s3_quotes = collect_schwab_quotes(conn, market_date, log, extra_tickers=opus_tickers)

        if s3_quotes == 0:
            return fail("Step 3 (Quotes)", "Zero quotes returned from Schwab")

        # 3b. Auto-detect big movers from quote data
        big_movers = get_big_movers(conn, market_date, threshold=3.0)
        log.info(f"Auto-detected movers (|change| > 3%): {len(big_movers)} symbols")

        # 3c. Technicals + SMA200 for ALL quoted symbols (sequential, 1s delay each)
        all_quoted = {r[0] for r in conn.execute(
            "SELECT DISTINCT symbol FROM quotes WHERE market_date = ? AND source = 'schwab' "
            "AND symbol NOT LIKE '$%' AND symbol NOT LIKE '/%'",
            (market_date,),
        ).fetchall()}
        log.info(f"Technicals + SMA200 for {len(all_quoted)} quoted symbols (sequential)")
        s3_technicals = collect_schwab_technicals(conn, market_date, log, symbols=all_quoted)
        s3_levels = collect_sma200(conn, market_date, log, symbols=all_quoted)

        # 3e. Everything else
        s3_context = collect_schwab_market_context(conn, market_date, log)
        s3_earnings = collect_schwab_earnings(conn, market_date, log)

        s3_econ = collect_economic_calendar(conn, market_date, log)

        # External APIs
        s3_crypto = collect_coingecko(conn, market_date, log)
        s3_stooq = collect_stooq(conn, market_date, log)
        if s3_stooq < 3:
            failed_sources.add("stooq")
        s3_fred = collect_fred(conn, market_date, log)
        if s3_fred < 3:
            failed_sources.add("fred")
        s3_yahoo = collect_yahoo_backup(conn, market_date, log, failed_sources)

        s3_time = time.monotonic() - t0
        step_results["step3_data"] = "ok"
        log.info(f"Step 3 complete: {s3_time:.1f}s (quotes={s3_quotes}, tech={s3_technicals}, "
                 f"sma200={s3_levels}, earnings={s3_earnings}, econ={s3_econ}, "
                 f"crypto={s3_crypto}, stooq={s3_stooq}, fred={s3_fred}, yahoo={s3_yahoo})")

        # ── STEP 4: Validation + Retry ──
        log.info("── Step 4: Validation + Retry ──")
        t0 = time.monotonic()
        s4_anomalies = detect_anomalies(conn, market_date, log)
        s4_xval = cross_validate(conn, market_date, log)
        s4_recovered = retry_failed_calls(conn, market_date, log)

        # Check for remaining failures after retry — look at actual data gaps
        # Symbols that got a quote but still have no technicals
        missing_technicals = conn.execute(
            "SELECT q.symbol FROM quotes q "
            "WHERE q.market_date = ? AND q.source = 'schwab' "
            "AND q.symbol NOT LIKE '$%' AND q.symbol NOT LIKE '/%' "
            "AND q.symbol NOT IN ("
            "  SELECT t.symbol FROM technicals t WHERE t.market_date = ?"
            ")",
            (market_date, market_date),
        ).fetchall()

        if missing_technicals:
            syms = [r[0] for r in missing_technicals]

            # Exclude symbols where Schwab returned HTTP 400 (API doesn't
            # support technicals for that symbol, e.g. OTC/ADR).  These are
            # permanent rejections, not transient data gaps.
            http400_syms = set()
            for sym in syms:
                has_400 = conn.execute(
                    "SELECT 1 FROM source_health "
                    "WHERE market_date = ? AND source = 'schwab' "
                    "AND endpoint LIKE ? AND error_message LIKE '%400%' LIMIT 1",
                    (market_date, f'%/api/technicals/{sym}%'),
                ).fetchone()
                if has_400:
                    http400_syms.add(sym)
            if http400_syms:
                log.warning(
                    f"Excluding {len(http400_syms)} symbol(s) — Schwab technicals "
                    f"API returned HTTP 400 (unsupported): {', '.join(sorted(http400_syms))}")
            real_gaps = [s for s in syms if s not in http400_syms]

            if real_gaps:
                return fail("Step 4 (Data gaps)",
                            f"{len(real_gaps)} symbol(s) still missing technicals after retry: {', '.join(real_gaps)}")

        score, details = calculate_completeness(conn, market_date)
        s4_time = time.monotonic() - t0
        step_results["step4_validate"] = "ok"
        log.info(f"Step 4 complete: {s4_time:.1f}s (anomalies={s4_anomalies}, "
                 f"cross_val={s4_xval}, retried={s4_recovered}, completeness={score:.0%})")

        # Log completeness details
        for key, (present, expected) in details.items():
            status = "OK" if present >= expected else f"MISSING ({present}/{expected})"
            log.debug(f"  {key}: {status}")

        if score < 1.0:
            missing = [f"  {k}: {p}/{e}" for k, (p, e) in details.items() if p < e]
            return fail("Step 4 (Completeness)", f"Completeness {score:.0%} — not 100%:\n" + "\n".join(missing))

        # ── STEP 5: Generate Briefing File ──
        log.info("── Step 5: Generate Briefing ──")
        briefing_path = generate_briefing(conn, market_date, log)

        # ── Update collection record ──
        total_quotes = conn.execute(
            "SELECT COUNT(*) FROM quotes WHERE market_date = ?", (market_date,)
        ).fetchone()[0]
        total_headlines = conn.execute(
            "SELECT COUNT(*) FROM headlines WHERE market_date = ?", (market_date,)
        ).fetchone()[0]

        exit_code = 0

        conn.execute(
            "UPDATE collections SET finished_at = ?, phase1_status = ?, phase2_status = ?, "
            "phase3_status = ?, phase4_status = ?, total_quotes = ?, total_headlines = ?, "
            "completeness_score = ?, exit_code = ? WHERE id = ?",
            (datetime.datetime.now().isoformat(),
             step_results.get("step1_rss", "skipped"),
             step_results.get("step2_opus", "skipped"),
             step_results.get("step3_data", "skipped"),
             step_results.get("step4_validate", "skipped"),
             total_quotes, total_headlines, score, exit_code, collection_id),
        )
        conn.commit()

        # ── Daily cleanup (if data is old enough) ──
        cleanup_old_data(conn, log)

        conn.close()

        total_time = sum([s1_time, s2_time, s3_time, s4_time])
        log.info(f"=== Collection complete: {total_time:.1f}s total, "
                 f"completeness={score:.0%}, exit_code={exit_code} ===")

        return exit_code

    except Exception as e:
        log.exception(f"Unexpected error in pipeline: {e}")
        send_failure_email(market_date, "Unexpected exception", str(e), log)
        try:
            conn.close()
        except Exception:
            pass
        return 2


if __name__ == "__main__":
    sys.exit(main())

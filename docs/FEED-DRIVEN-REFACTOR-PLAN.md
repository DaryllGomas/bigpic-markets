# Plan: Opus-Driven Feed Analysis Pipeline

## Implementation Status

**Last updated:** 2026-02-13 (session 4 — Northern Miner verified, end-to-end test pass)
**Script:** `~/projects/bigpic-markets/scripts/collect-market-data.py`

### Changes — ALL 11 IMPLEMENTED
- [x] Change 1: RSS_FEEDS expanded from 9 → 26 feeds (13 categories)
- [x] Change 2: RSS moved to Step 1 (was Phase 3)
- [x] Change 3: `analyze_headlines_with_opus()` — new function
- [x] Change 4: `feed_analysis` DB table + retention + clear_today
- [x] Change 5: `collect_schwab_quotes()` accepts `extra_tickers` param
- [x] Change 6: `collect_schwab_technicals()` + `collect_sma200()` accept `symbols` param
- [x] Change 7: `get_big_movers()` — new function
- [x] Change 8: `collect_schwab_movers()` deleted (broken endpoint)
- [x] Change 9: Briefing movers section rewritten (auto-detected + Opus)
- [x] Change 10: Market Intelligence section added to briefing
- [x] Change 11: `main()` reordered to RSS → Opus → Schwab → Validate → Briefing

### Bugs Found & Fixed During Implementation
- **Quantum Computing Report feed:** URL needed trailing slash (`/feed` → `/feed/`), was getting 301 redirect with empty body
- **Gzip decompression:** Same feed's server force-gzips responses even without `Accept-Encoding: gzip`. Added gzip detection (magic bytes `\x1f\x8b`) + decompression in `parse_rss_items()`
- **`import gzip`** added to top-level imports
- **Nested Claude session:** `claude -p` fails inside Claude Code (`CLAUDECODE` env var detected). Fixed by passing clean env (`os.environ` minus `CLAUDE*` vars) to `subprocess.run()`
- **World Nuclear News feed too infrequent:** Most recent article was Feb 6 — zero headlines within 24h. Replaced with ANS Nuclear Newswire (`ans.org/news/feed/`) — publishes multiple times daily, premier US nuclear professional society (founded 1954)
- **Added `$IRX` to SCHWAB_CORE:** 13-week T-Bill rate (÷10 = yield). Real-time short-end rate from Schwab. 2Y Treasury (`DGS2`) stays on FRED — no real-time Schwab equivalent, prev-day close only.
- **FRED trimmed to 2Y only:** Removed DGS10/DGS30 from `FRED_SERIES` — Schwab `$TNX`/`$TYX` are real-time, FRED is prev-day close. Cross-validation of 10Y/30Y removed (discrepancies were normal intraday movement, not data errors).
- **Removed deep dive cap:** Was artificially capping technicals/SMA200 at 30 symbols, causing most Tier 1 stocks to miss technicals. Now hits ALL quoted symbols sequentially. No batching, no cap.
- **Split API delays:** `CHUNK_DELAY = 0.5s` for light endpoints (quotes, SMA200, earnings), `TECH_DELAY = 1.0s` for heavy endpoint (technicals). Tested: 0.5s caused timeouts on technicals (3/145), 1.0s works clean.
- **Added `retry_failed_calls()`:** Step 4 now queries `source_health` for errors, retries each failed Schwab call with 2x timeout before completeness check and briefing generation. Handles technicals, SMA200, and earnings endpoints. Tested: recovered IBM technicals + RTX earnings (2/2).
- **Added `send_failure_email()` + fail-fast in `main()`:** Any pipeline failure = email to `daryll@bigpicsolutions.com` via msmtp + stop. Checks: zero headlines, Opus failure, Schwab unreachable, zero quotes, data gaps after retry, completeness < 100%. Uncaught exceptions also trigger email. No more silent degradation.
- **Mining.com → Northern Miner:** Mining.com started returning 403 (blocked automated access). Replaced with Northern Miner (`northernminer.com/feed/`) — founded 1915, "the mining industry's bible," publishes daily, 20 items per fetch.
- **RSS failures now non-fatal (2026-02-27):** Individual feed failures send a `[WARNING]` email (via `send_warning_email()`) and the pipeline continues with available headlines. Only zero total headlines = hard abort. Previously any single feed failure was fatal — caused a full pipeline abort on 2026-02-27 when Northern Miner returned 403.

### Verification Progress
- [x] Syntax check — `py_compile` passes
- [x] Module load — all expected functions exist, `collect_schwab_movers` confirmed removed
- [x] RSS feed test — **26/26 OK**, re-verified after ANS swap: 251 headlines, all 13 categories populated (nuclear_energy: 4)
- [x] Opus analysis test — re-run: **250 headlines → 46 tickers, 17 movers, 12 themes, 47s** — JSON valid, DB stored in 6 normalized tables
- [x] Prompt size check — **~6,200 tokens input (~3.1% of Opus 200K context)**. Headlines-only approach is safe; would need 8,000+ headlines to approach 50%. No risk of context overflow.
- [x] Normalized DB — replaced `feed_analysis` JSON blob with 6 tables: `opus_tickers`, `opus_movers`, `opus_themes`, `opus_econ_events`, `opus_fed_signals`, `opus_sentiment`
- [x] 24-hour filter — RSS collection now skips headlines older than 24h (248 stored vs 483 before, 236 filtered). Each day's run adds that day's news. 14-day retention keeps history.
- [x] Step-by-step run (session 2) — Steps 1-5 run individually, each verified before proceeding
  - Step 1 (RSS): 251 headlines, 13/13 categories ✓
  - Step 2 (Opus): 250 headlines → 46 tickers, 17 movers, 12 themes, 47s ✓
  - Step 3 (Schwab): 157 quotes, 46/49 technicals, 47/49 SMA200, 7 errors (2 bad tickers, 5 timeouts) — timeouts caused by deep dive cap sending too many calls. **Fixed: removed cap, now hits all quoted symbols sequentially**
  - Step 4 (Validation): 0 anomalies, completeness 100% ✓
  - Step 5 (Briefing): 35KB briefing generated with all sections ✓
- [x] Clean full pipeline run — **PASSED**: 252 headlines, 68 tickers, 164 quotes, 143/145 technicals, 145/145 SMA200, 0 anomalies, 100% completeness, 37KB briefing. Total ~10.5min.
- [x] API delay tuning — tested 0.5s (3 timeouts on technicals), split to `TECH_DELAY=1.0s` + `CHUNK_DELAY=0.5s`
- [x] Clean run with split delays — **PASSED**: 251 headlines, 49 tickers, 18 movers, 13 themes, 156 quotes, 136/137 technicals, 137/137 SMA200, 0 anomalies, 100% completeness, 38KB briefing, 505s (~8.4min). 1 technicals timeout (IBM), 1 earnings timeout (RTX).
- [x] `run-morning-brief.sh` has no timeout on `collect-market-data.py` — confirmed OK (line 539, no timeout wrapper)
- [x] Briefing quality review — 35/36 Tier 1 had technicals (IBM timed out). **Fixed: added `retry_failed_calls()` to Step 4.** Retries any failed Schwab calls with 2x timeout before completeness check + briefing. Tested: recovered IBM technicals + RTX earnings (2/2).
- [x] Email failure alerts — `send_failure_email()` via msmtp to daryll@bigpicsolutions.com. Fail-fast: any failure = email + stop. No silent degradation.
- [x] Full pipeline with retry + email — **PASSED**: 238 headlines, 77 tickers, 169 quotes, 150/150 technicals (148+2 retried: IEV, BA), 150/150 SMA200, 65+1 earnings (ANET retried), 0 anomalies, 100% completeness, 39KB briefing, 553s (~9.2min). 3 failures, 3/3 recovered, no email sent.
- [x] Email delivery test — **PASSED**: test email sent and received at daryll@bigpicsolutions.com via msmtp
- [x] Completeness threshold — changed from 70% to 100%. Anything less = fail + email.
- [x] RSS graceful degradation — individual feed failures send `[WARNING]` email + continue (was fail-fast, changed 2026-02-27 after Northern Miner 403 killed the whole pipeline)
- [x] Mining.com → Northern Miner — feed swap, tested, VERIFIED-SOURCES.md updated, Mining.com added to blocked list
- [x] Full pipeline run with Northern Miner swap — **PASSED**: 247 headlines, 26/26 feeds, 53 tickers, 13 movers, 14 themes, 156 quotes, 137/137 technicals (135+2 retried: IEV, BA), 137/137 SMA200, 64+3 earnings (ANET, CGNX, ROK retried), 0 anomalies, 100% completeness, 36.7KB briefing, 526s (~8.8min). 7 failures, 7/7 recovered.
- [x] End-to-end test — collect (already done) → verify (passed, 1 correction: SPX futures) → HTML build (58KB, all sections) → archive index updated → git push. **Confirmed working.**
- [ ] FRED log cosmetic — shows "1/3 series" but only 1 series configured (minor)

### Known Issues
- **`script -qfc` wrapper in `run_claude()`:** Gets suspended (state T) when `run-morning-brief.sh` is launched from gnome-terminal inside a Claude Code session. Not an issue for cron (no parent Claude session). If manual testing is needed, strip `CLAUDECODE` env var: `env -u CLAUDECODE -u CLAUDE_CODE_SESSION bash scripts/run-morning-brief.sh`
- **Claude pipe buffering:** When Claude output is piped (e.g. `| tee`), output is fully buffered (no visible progress). The `script -qfc` wrapper exists to force line buffering. Works from cron; conflicts with interactive terminals launched from Claude Code.

---

## Context

The collection script (`collect-market-data.py`) works but has two problems:
1. RSS feeds are collected last (Phase 3) and dumped raw into the briefing — no intelligence extraction
2. The Schwab movers endpoint is broken (returns volume-sorted regardless of sort param)
3. Tickers for technicals/SMA200 are hardcoded to Tier 1 — misses news-driven names entirely

**The fix:** Move RSS feeds to Step 1, feed all headlines to Opus via `claude -p --model opus`, and let Opus extract structured intelligence (tickers, narratives, themes, sentiment). That intelligence drives what numbers to look up from Schwab.

**Previous plan (regex/dict-based extraction):** `~/.claude/plans/validated-noodling-elephant.md` — kept as reference.

---

## Workflow

```
STEP 1: Collect RSS → DB (~15-30s)
         │
         ▼
STEP 2: Opus analyzes headlines → structured JSON (~30-60s)
         │
         ▼
STEP 3: Build lookup lists from Opus output + watchlist + core macro
         │
         ▼
STEP 4: Collect numbers from Schwab/external APIs (~5 min)
         │
         ▼
STEP 5: Generate briefing file (Opus intelligence + verified numbers)
```

---

## Detailed Changes

### File: `~/projects/bigpic-markets/scripts/collect-market-data.py`

### Change 1: Expand RSS_FEEDS to all 26 feeds

Currently only 4 categories (9 feeds). Add sector feeds from VERIFIED-SOURCES.md:
- Defense (2), Space (2), Nuclear (1), Semi (2), Cyber (2), Quantum (2), Mining (2), Robotics (2), Energy Storage (2)

This gives Opus sector-level context, not just macro headlines.

### Change 2: Move `collect_rss_feeds()` to run FIRST

Currently Phase 3 (after all Schwab calls). Move to before any Schwab calls.

In `main()`, reorder:
```
OLD: Phase 1 (Schwab) → Phase 2 (External) → Phase 3 (RSS) → Phase 4 (Validate)
NEW: Step 1 (RSS) → Step 2 (Opus) → Step 3 (Schwab + External) → Step 4 (Validate)
```

### Change 3: New function `analyze_headlines_with_opus(conn, market_date, log)`

After RSS collection, query all today's headlines from DB, group by category, and call Opus:

```python
def analyze_headlines_with_opus(conn, market_date, log):
    """Feed today's headlines to Opus for structured intelligence extraction."""

    # Query all headlines for today
    headlines = query_todays_headlines(conn, market_date)

    # Build prompt with headlines grouped by category
    prompt = build_analysis_prompt(headlines, market_date)

    # Call Opus via claude CLI
    result = subprocess.run(
        ["claude", "-p", "--model", "opus", "--output-format", "json", prompt],
        capture_output=True, text=True, timeout=120
    )

    # Parse structured JSON response
    analysis = json.loads(result.stdout)

    # Store analysis in DB (new table: feed_analysis)
    store_analysis(conn, market_date, analysis)

    return analysis
```

**Opus returns JSON with:**
```json
{
  "tickers": ["CSCO", "ANET", "RIVN", "CGNX"],
  "movers": [
    {"ticker": "CSCO", "direction": "down", "reason": "Q2 miss, weak guidance",
     "headline": "Cisco posts worst day since 2022"}
  ],
  "econ_events": [
    {"event": "CPI", "status": "pending",
     "context": "markets expecting 2.8% YoY"}
  ],
  "fed_signals": ["Waller hints at June cut"],
  "sector_themes": [
    {"sector": "AI Infrastructure",
     "narrative": "ANET beats, hyperscaler capex rising"}
  ],
  "sentiment": "mixed - tech earnings strong, macro uncertain"
}
```

### Change 4: Normalized DB tables for Opus analysis

Originally planned as a single `feed_analysis` JSON blob table. Refactored during testing to 6 normalized tables:

```sql
-- opus_tickers: every ticker symbol Opus found in headlines
-- opus_movers: tickers with clear directional signal (up/down + reason + headline)
-- opus_themes: sector-level narratives (sector + narrative text)
-- opus_econ_events: scheduled economic data releases (event + status + context)
-- opus_fed_signals: Fed official statements or policy signals
-- opus_sentiment: overall market mood summary (one row per day, UNIQUE on market_date)
```

All tables have `market_date`, `analyzed_at`, and 30-day retention.

### Change 5: Modify `collect_schwab_quotes()` to accept dynamic symbol list

Currently hardcoded: `SCHWAB_CORE + all watchlist + ETF benchmarks`

New: also include `opus_tickers` (tickers Opus found in headlines that aren't already in the list).

```python
def collect_schwab_quotes(conn, market_date, log, extra_tickers=None):
    symbols = set(SCHWAB_CORE) | set(get_all_watchlist_tickers()) | set(ETF_BENCHMARKS)
    if extra_tickers:
        symbols |= set(extra_tickers)
    # ... rest unchanged
```

### Change 6: Modify `collect_schwab_technicals()` + `collect_sma200()` to accept `symbols` param

Previously: hardcoded to Tier 1 tickers + ETF benchmarks (~40 symbols)

Now: accepts any symbol list. In `main()`, queries ALL quoted Schwab symbols (excluding indices `$XXX` and futures `/XX`) and runs technicals + SMA200 for each one sequentially with 1s delay between calls. No cap — every stock that got a quote gets technicals.

```python
all_quoted = {symbols from quotes table where source='schwab', excluding $/$/ prefixes}
collect_schwab_technicals(conn, market_date, log, symbols=all_quoted)
collect_sma200(conn, market_date, log, symbols=all_quoted)
```

### Change 7: New function `get_big_movers(conn, market_date, threshold=3.0)`

Query quotes table for today, return symbols where `|change_pct| > threshold`.

```python
def get_big_movers(conn, market_date, threshold=3.0):
    cur = conn.execute("""
        SELECT symbol FROM quotes
        WHERE market_date = ? AND source = 'schwab'
        AND ABS(change_pct) > ?
    """, (market_date, threshold))
    return {row[0] for row in cur.fetchall()}
```

### Change 8: Remove `collect_schwab_movers()`

Delete the function. It calls the broken Schwab movers endpoint. Movers are now auto-detected from quote data (Change 7) + Opus analysis (Change 3).

Keep the `movers` table in schema for backwards compat but stop writing to it.

### Change 9: Rewrite briefing "Market Movers" section

In `generate_briefing()`, replace the current movers section (reads from `movers` table) with:

**Auto-detected movers** (from quotes, |change| > 3%):
```markdown
## Today's Movers (Auto-detected: |change| > 3%)
| Symbol | Price | Change | Sector | Tier |
```

**Opus-identified movers** (from feed_analysis, with narrative):
```markdown
## News-Driven Movers (Opus Analysis)
| Symbol | Direction | Reason | Headline |
```

### Change 10: Add Opus intelligence section to briefing

New section in `generate_briefing()` that includes Opus's structured analysis:

```markdown
## Market Intelligence (Opus Feed Analysis)

### Sector Themes
- AI Infrastructure: ANET beats, hyperscaler capex rising
- Nuclear: LEU drops on DOE policy uncertainty

### Economic Context
- CPI pending, markets expecting 2.8% YoY

### Fed Signals
- Waller hints at June cut

### Overall Sentiment
Mixed — tech earnings strong, macro uncertain
```

### Change 11: Reorder `main()`

```python
def main():
    # ... setup, args, DB init ...

    # STEP 1: RSS Feeds (FIRST)
    rss_count = collect_rss_feeds(conn, market_date, log)

    # STEP 2: Opus Analysis
    opus_analysis = analyze_headlines_with_opus(conn, market_date, log)
    opus_tickers = opus_analysis.get("tickers", [])

    # STEP 3: Collect Numbers
    # 3a. Quotes (watchlist + core + opus tickers, batched 15/call)
    collect_schwab_quotes(conn, market_date, log, extra_tickers=opus_tickers)

    # 3b. Auto-detect big movers from quotes (|change| > 3%)
    big_movers = get_big_movers(conn, market_date, threshold=3.0)

    # 3c. Technicals + SMA200 for ALL quoted symbols (sequential, 1s delay)
    all_quoted = {all schwab-sourced stock symbols from quotes table}
    collect_schwab_technicals(conn, market_date, log, symbols=all_quoted)
    collect_sma200(conn, market_date, log, symbols=all_quoted)

    # 3d. Everything else (unchanged)
    collect_schwab_market_context(conn, market_date, log)
    collect_schwab_earnings(conn, market_date, log)
    collect_economic_calendar(conn, market_date, log)
    collect_coingecko(conn, market_date, log)
    collect_stooq(conn, market_date, log)
    collect_fred(conn, market_date, log)

    # STEP 4: Validate
    detect_anomalies(conn, market_date, log)
    cross_validate(conn, market_date, log)
    completeness = calculate_completeness(conn, market_date)

    # STEP 5: Generate briefing
    generate_briefing(conn, market_date, log)
```

---

## Fallback: What if Opus fails?

If the `claude` CLI call fails (timeout, API error, malformed JSON):
1. Log the error
2. Set `opus_tickers = []` and `opus_analysis = {}`
3. Pipeline continues with watchlist + core macro only (same as current behavior)
4. Briefing generates without the "Market Intelligence" section
5. No crash — graceful degradation

---

## What does NOT change

- `run-morning-brief.sh` (invocation script)
- Database schema for existing tables (quotes, technicals, etc.)
- External API collection (crypto, stooq, CoinGecko)
- Economic calendar, earnings collection logic
- `verify-brief.py`
- Briefing file format (additive — new sections added, existing sections preserved)

## What DID change beyond original plan

- **FRED:** trimmed from 3 series (DGS2/DGS10/DGS30) to 1 (DGS2 only) — 10Y/30Y already real-time from Schwab
- **Cross-validation:** removed 10Y/30Y checks (FRED is prev-day close vs Schwab real-time = always different, not a data error)
- **`$IRX` added to SCHWAB_CORE:** 13-week T-Bill rate, real-time short-end yield
- **Nuclear feed:** World Nuclear News → ANS Nuclear Newswire (WNN published ~weekly, ANS publishes daily)
- **DB schema:** `feed_analysis` JSON blob → 6 normalized `opus_*` tables
- **Technicals/SMA200:** removed 30-symbol cap, now runs all quoted symbols sequentially (1s delay)

---

## Verification

1. ✅ **RSS collection** — 26/26 feeds OK, 251 headlines, all 13 categories populated
2. ✅ **Opus analysis** — 250 headlines → 46 tickers, 17 movers, 12 themes, ~47s. ~6,200 tokens (3.1% of 200K context)
3. ✅ **Step-by-step run** — Steps 1-5 individually verified
4. **Clean full pipeline run** — `python3 ~/projects/bigpic-markets/scripts/collect-market-data.py` with all fixes applied
5. **Briefing quality** — confirm all Tier 1 stocks have technicals populated (not blank)
6. **Schwab health** — confirm 0 timeouts with sequential 1s-delay approach
7. **Fallback test** — pipeline completes without Opus if CLI fails
8. **End-to-end** — collect → Claude brief → verify → HTML

# Economic Calendar Fix — 2026-03-27

**Problem:** The Eagle Eye "Week Ahead" section and Morning Brief were showing wrong economic release dates. W12 listed PCE on Friday Mar 27 and GDP on Thursday Mar 26 — both were actually rescheduled to April 9 by BEA after the Oct-Nov 2025 government shutdown. Michigan Consumer Sentiment (the only real release on Mar 27) was missed entirely.

**Root causes:**
1. **Intel API (upstream):** The `fredCalendar.ts` module used FRED's bulk `/releases/dates` endpoint, which returned stale pre-shutdown dates. It was also run manually once (Jan 12) and never wired into the scraper pipeline. PCE had the wrong FRED release ID (83 instead of 54).
2. **Eagle Eye pipeline:** The "Week Ahead" section had no deterministic data source. Claude agents used WebSearch and hallucinated dates using stereotypical day-of-week patterns (e.g., "GDP is usually Thursday").
3. **Morning Brief pipeline:** Rendered whatever the DB had from the API. Since the API served stale dates, the brief showed phantom events.

---

## What Changed

### Intel API (192.168.10.60:3000) — fixed at source
- Deleted broken `fredCalendar.ts` (bulk endpoint, wrong IDs, manual-only)
- Created `scraperFRED.ts` — per-release endpoint (`/release/dates?release_id=X`) for 16 major releases with 6-month lookahead
- Cleaned 17 stale FRED rows + 292 legacy investing.com rows from `market_calendar`
- FRED now runs in Phase 10 of the scraper pipeline (every cycle, not manual)
- New endpoint: `GET /api/calendar/upcoming?days=N` for forward-looking queries

### Eagle Eye pipeline (scripts/run-eagle-eye.sh)
- **New script:** `scripts/collect-weekly-calendar.py` — pre-collects next week's economic calendar from the API's `/upcoming` endpoint before the research phase
- **Calendar injection:** Research prompt now includes mandatory rules: "ONLY list releases from `next_week_calendar.md`, use EXACT dates, do NOT invent releases"
- **NOTABLE ABSENCES:** Calendar file explicitly lists which major releases are NOT this week (prevents the PCE/GDP hallucination pattern)
- **Verification:** STEP 2 now cross-checks Week Ahead dates against the calendar file
- **Post-check:** `scripts/verify-eagle-eye-calendar.py` runs a deterministic (non-LLM) comparison after EAGLE_EYE.md is generated

### Files added/modified

| File | Action | Purpose |
|------|--------|---------|
| `scripts/collect-weekly-calendar.py` | **NEW** | Pre-collects upcoming week's economic calendar for Eagle Eye |
| `scripts/verify-eagle-eye-calendar.py` | **NEW** | Deterministic post-check of Week Ahead vs calendar |
| `scripts/run-eagle-eye.sh` | **MODIFIED** | Calendar collection, prompt injection, verification |

### Data flow — BEFORE (broken)

```
Intel API (/api/calendar/today)
    │   fredCalendar.ts: bulk FRED endpoint, stale dates, manual-only, wrong PCE ID
    │
    └── collect-market-data.py → market.db → Morning Brief
            └── Shows phantom GDP/PCE on wrong days

Eagle Eye (run-eagle-eye.sh)
    └── 4 Claude agents use WebSearch
            └── Hallucinate "Week Ahead" dates (no calendar data source)
                    └── PCE on Friday, GDP on Thursday, miss Michigan entirely
```

### Data flow — AFTER (fixed)

```
Intel API (192.168.10.60:3000)
    │   scraperFRED.ts: 16 per-release FRED queries, 6-month lookahead, every cycle
    │   Forex Factory: current week detail (Fed speakers, UoM, weekly data)
    │
    ├── GET /api/calendar/today
    │       └── collect-market-data.py (daily 5:20 AM)
    │               └── market.db → Morning Brief ✓
    │
    └── GET /api/calendar/upcoming?days=7
            └── collect-weekly-calendar.py (Sunday 4 PM, before Eagle Eye)
                    └── $WEEK_DIR/next_week_calendar.md
                            │   ├── Day-by-day events table (date, time, impact)
                            │   └── NOTABLE ABSENCES (PCE, GDP, CPI, etc. NOT this week)
                            │
                            ├── Eagle Eye research prompt (MANDATORY: use exact dates)
                            │       └── EAGLE_EYE.md "Week Ahead" section
                            │
                            ├── STEP 2 verification (LLM cross-check)
                            │       └── VERIFICATION.md "Week Ahead Calendar Check"
                            │
                            └── verify-eagle-eye-calendar.py (deterministic post-check)
                                    └── Flags: wrong dates, phantom events, missing events
```

### FRED releases tracked (16)

| Release | FRED ID | Example: Next Date |
|---------|---------|-------------------|
| NFP (Employment Situation) | 50 | Apr 3 |
| CPI | 10 | Apr 10 |
| GDP | 53 | Apr 9 |
| PCE (Personal Income & Outlays) | 54 | Apr 9 |
| PPI | 46 | Apr 14 |
| Retail Sales | 9 | Apr 1 |
| Industrial Production | 13 | — |
| Housing Starts | 27 | — |
| Existing Home Sales | 291 | — |
| Durable Goods | 97 | — |
| ADP Employment | 194 | Apr 1 |
| Employment Cost Index | 11 | — |
| Import/Export Prices | 188 | — |
| Construction Spending | 229 | — |
| Jobless Claims | 180 | Apr 2, Apr 9 |
| Retail Trade | 63 | — |

---

## Verification

Tested against BEA/BLS official schedules:

| Release | API Date | Official Date | Source |
|---------|----------|---------------|--------|
| NFP | Apr 3 | Apr 3 | BLS |
| GDP (Third Est.) | Apr 9 | Apr 9 | BEA (rescheduled from Mar 27) |
| PCE Price Index | Apr 9 | Apr 9 | BEA (rescheduled from Mar 27) |
| CPI | Apr 10 | Apr 10 | BLS |
| Michigan Sentiment | Mar 27 | Mar 27 | UMich (confirmed actual: 53.3) |
| Today (Mar 27) | No GDP, no PCE | Correct | Phantom events removed |

Eagle Eye verification script against W12 report caught 9 discrepancies:
- PHANTOM: PCE on Friday (not scheduled)
- WRONG DATE: GDP on Thursday (actually Friday in the old data)
- WRONG DATE: Durable Goods on Wednesday (actually Tuesday)
- WRONG DATE: Flash PMI on Monday (actually Tuesday)
- MISSING: Michigan Consumer Sentiment, Unemployment Claims, ADP, others

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

### Data flow (after fix)

```
Intel API (FRED per-release + Forex Factory)
    │
    ├── /api/calendar/today → collect-market-data.py → market.db → Morning Brief
    │
    └── /api/calendar/upcoming?days=7 → collect-weekly-calendar.py
            → next_week_calendar.md → Eagle Eye research prompt
            → verify-eagle-eye-calendar.py → VERIFICATION.md
```

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

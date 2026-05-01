# scripts/ patch log — 2026-05-01

> Note: scripts/ is gitignored. This changelog lives on the host (192.168.10.61) only.
> If this machine is rebuilt, re-apply these fixes from `_Changelog/2026-05-01.md` in
> Capital Google Drive (which has the full reasoning + git diff context).

## Fix: Eagle Eye day-of-week off-by-one bug

**Symptom:** Eagle Eye W17 (week of 2026-04-26) had every day in the Week Ahead labeled
+1 day off. "Mon Apr 28" instead of "Tue Apr 28", "Wed Apr 30" instead of "Thu Apr 30",
"Thu May 1" instead of "Fri May 1", etc. Caused user-side confusion (May 1 framed as
NFP day; not actually NFP — that releases May 8).

**Root cause:**
- Claude (LLM) wrote day headers in EAGLE_EYE.md by computing day-of-week from date,
  and computed it wrong.
- `stamp-calendar.py parse_calendar()` skipped days that had no events table (e.g.,
  Monday Apr 27 — "No major economic events scheduled" prose only). So `cal_lookup`
  was missing Monday entirely, which would have prevented the date-correction patch
  from kicking in for that day.
- `stamp-calendar.py stamp()` matched calendar tables to report day headers using
  day NAME only — accepted Claude's wrong day name as canonical.
- `verify-eagle-eye-calendar.py` only checked day-name presence + event-name match;
  did NOT cross-check day-of-week against the date. Bug slid past every layer.

**Fixes applied:**

1. **scripts/stamp-calendar.py**:
   - `parse_calendar()`: changed `if current_day and current_table` to `if current_day`
     (3 occurrences). Days with no events table are now captured into `cal_days`.
   - `stamp()`: in the day_blocks loop, when injecting calendar table, also
     OVERWRITE the report's day header with the calendar's authoritative day name + date.
     Trailing parentheticals like "(FOMC Day 1)" are preserved if present.

2. **scripts/run-eagle-eye.sh** (`build_research_prompt`):
   - Added explicit instructions to read day headers verbatim from
     `next_week_calendar.md` instead of computing day-of-week from date.
   - Added rule: no parenthetical labels like "(FOMC Day)" in day headers; put
     those in the commentary paragraph below.

3. **scripts/verify-eagle-eye-calendar.py**:
   - Added `check_day_date_consistency()` function that parses every "### Day, Month N"
     header in the Week Ahead section, computes the actual day-of-week for that date,
     and flags any mismatch.
   - Wired into `verify()` as Check 4 (after Notable Absences check).

**Verification:**
- Live W17 EAGLE_EYE.md re-stamped 2026-05-01 14:08 ET (committed to public repo).
- Manual run confirmed all 5 day headers now correct.
- Verify script PASS on corrected; WARN with 5 findings on corrupted regression test.

**Backups:** `scripts/*.bak-2026-05-01` removed after fix verified.

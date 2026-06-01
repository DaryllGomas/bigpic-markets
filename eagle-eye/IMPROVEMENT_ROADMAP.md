# Eagle Eye Pipeline — Improvement Roadmap

**Generated:** 2026-05-31 (host `bp-cmd-c-01`)
**Method:** Multi-agent audit — 6 dimensions audited in parallel, every proposed fix independently
adversarially verified, then synthesized. 31 findings, all 31 confirmed by independent verification
(several sub-proposals downgraded/rejected within findings — see end).
**Status (updated 2026-05-31):** Quick wins (Ranks 1, 2, 3, 16, 19, 23) **implemented & verified**;
the deterministic price collector `scripts/collect-weekly-data.py` (Rank 5) is **built, QC-hardened, and
validated** but **NOT yet wired into `run-eagle-eye.sh`**. Remaining ranks are advisory.
Correctness/fabrication-resistance was weighted hardest per the explicit goal: *"I rely on this for
weekly grounding in my trading and I need it to be correct."*

---

## Executive Read

The pipeline produces a useful weekly narrative, but **its hard numbers are not trustworthy by
design**: every price, level, and most catalysts come from WebSearch agents with no deterministic
ground-truth anchor, and the only safety net is the model checking itself with **zero enforcement**
— the calendar verifier and all quality gates "always exit 0" on byte-size, never on data
correctness. W21 alone shipped a stale WTI ~$106 (vs ~$96), a year-old Moody's downgrade sold as a
fresh weekly catalyst (2025 read as 2026), an already-reported NVDA earnings stamped as an upcoming
HIGH-impact row, fabricated SPX support/resistance pushed into the trader's daily-touch Daily Notes,
and impossible 4:30 AM macro release times from a timezone double-conversion bug. Several of these
escaped purely by luck (a second report happening to disagree), not by any structural check.

**The 2-3 highest-leverage changes:** (1) Add a **deterministic price/level ground-truth step** that
pulls from the live Schwab/Wingman APIs (the same feeds the sibling morning brief already uses) and
stamps the Scorecard, commodities, and weekly deltas — killing the single worst failure mode.
(2) Add a **deterministic post-stamp consistency gate** (port the existing `verify-brief.py`) so a
known-wrong number is auto-corrected or flagged, not published silently. (3) **Fix the calendar
timezone double-conversion and add staleness/past-earnings guards** so the most-trusted "Week Ahead"
table stops shipping impossible times and already-happened events. Several quick wins (model pinning,
calendar year-boundary, pass-through-only levels in inject-weekly) are cheap and should ship
immediately.

> **Encouraging context:** the sibling **morning brief already solved most of this** — it has
> `collect-market-data.py` (deterministic Schwab/Wingman price pull, used at `run-morning-brief.sh`)
> and `verify-brief.py` (price fact-checking with tolerances). The weekly just doesn't use them. Much
> of the correctness backbone is a *port*, not greenfield.

---

## W21 Failure Evidence (motivating cases)

From `eagle-eye/W21_2026-05-24/VERIFICATION.md` and agent code-reads:

- **Stale "Friday close"** — Report 02 reported WTI ~$106 / Brent ~$109 as Friday close; actual
  ~$96–97 / ~$104. A stale early-week value presented as current. Caught only by cross-report disagreement.
- **Year confusion** — Report 02 framed a Moody's Aaa→Aa1 downgrade as "May 16, 2026, one week ago";
  it was **May 16, 2025**. A year-old event sold as a fresh weekly catalyst. Caught only by independent search.
- **Stale "authoritative" calendar** — `next_week_calendar.md` listed "NVDA Q1 FY2027" as upcoming
  Wed 5/27; NVDA already reported 5/20. `stamp-calendar.py` would inject that stale entry regardless.

---

## Prioritized Roadmap (correctness first, then feasibility)

| Rank | Change | Problem it fixes | Impact | Effort | Risk | Files |
|------|--------|------------------|--------|--------|------|-------|
| 1 | Pass-through-only levels in inject-weekly | Fabricated SPX support/resistance in daily-touch Daily Notes | correctness-critical | quick-win | low | `inject-weekly.sh` |
| 2 | Pin `--model opus` + log model/CLI version | Fabrication-sensitive run drifts to unpinned default model | correctness-moderate | quick-win | low | `run-eagle-eye.sh` |
| 3 | Year/date discipline rule in agent prompts (Half 1) | Year-old event sold as fresh weekly catalyst (Moody's) | correctness-critical | moderate* | low | `run-eagle-eye.sh` |
| 4 | Fix calendar TZ double-conversion (source-aware) | Impossible 4:30 AM macro prints (GDP/PCE/NFP off by 4h) | correctness-critical | moderate | medium | `collect-weekly-calendar.py` |
| 5 | Deterministic price ground-truth step (Scorecard/commodities, exact weekly via history) | Stale WTI-as-Friday-close; WebSearch-only hard numbers | correctness-critical | large | medium | `collect-weekly-*.py`, `run-eagle-eye.sh` |
| 6 | Deterministic post-compile price gate (port `verify-brief.py`) | Known-false numbers publish with no enforcement | correctness-critical | moderate | medium | `run-eagle-eye.sh`, new verify script |
| 7 | Calendar staleness / past-earnings guard (collect + verify WARN) | Already-reported NVDA stamped as upcoming HIGH row | correctness-critical | moderate | medium | `collect-weekly-calendar.py`, `verify-eagle-eye-calendar.py` |
| 8 | Pre-stamp freshness gate + advisory non-fatal verify exit | Stale calendar rows injected regardless of verification note | correctness-moderate | moderate | medium | `collect-weekly-calendar.py`, `verify-*.py`, `run-eagle-eye.sh` |
| 9 | Separate verify invocation + enforce-corrections gate | Self-verify with no machine check corrections landed | correctness-critical | moderate | medium | `run-eagle-eye.sh`, `enforce-corrections.py` |
| 10 | Scoped as-of provenance labels (commodities/crypto/FX) + cross-report reconciliation | Weekend "current" vs "Friday close" conflation | quality | moderate | low | `run-eagle-eye.sh` |
| 11 | Ground sector heatmap from rotation scanner (exact 5d returns) | WebSearched "down ~4%" approximations | correctness-moderate | moderate | medium | `collect-weekly-*.py`, new stamp |
| 12 | DB-anchored anomaly/diff gate on stamped numbers | No deterministic numeric sanity gate at all | correctness-moderate | large | medium | `collect-weekly-*.py`, `run-eagle-eye.sh` |
| 13 | Calendar dedup (exact twins + true-synonym map only) | FRED/Forex-Factory twin rows inflate event load | quality | quick-win | medium | `collect-weekly-calendar.py` |
| 14 | Confidence derived from data quality + soften "do NOT override" | Calendar self-labels HIGH/AUTHORITATIVE even when stale/malformed | correctness-moderate | moderate | medium | `collect-weekly-calendar.py`, `run-eagle-eye.sh` |
| 15 | Sourced Key Levels table (Wingman `/api/levels`, as-of-Friday labeled) | No actionable support/resistance/invalidation in report | quality | large | medium | new collect + stamp, `run-eagle-eye.sh` |
| 16 | FF fallback year-boundary fix | Jan releases mis-yeared/dropped at year-end | reliability | quick-win | low | `collect-weekly-calendar.py` |
| 17 | Retry loop on transient claude failures (mirror morning-brief) | W17 lost whole run to auto-resetting usage limit | reliability | moderate | medium | `run-eagle-eye.sh` |
| 18 | Positive success heartbeat + external dead-man's-switch | Silent total no-run is invisible | reliability | moderate | low | `run-eagle-eye.sh` |
| 19 | Backup cron (Mon 03:00 UTC) — idempotent no-op on success | Transient Sunday failure permanently skips the week | reliability | quick-win | low | `run-eagle-eye.sh`, crontab |
| 20 | Require weekly % per watchlist name via API quote step + tag held names | Tracker half-empty, disconnected from positions | quality | moderate | medium | `run-eagle-eye.sh` (+ quote step) |
| 21 | Single source of truth for Risk Radar + Conviction grid (author in MD) | Ranking/tags re-synthesized up to 3x, no verification | quality | moderate | low | `run-eagle-eye.sh`, `inject-weekly.sh` |
| 22 | "What Changed This Week" narrative block (scoped, archive-sourced) | No explicit week-over-week delta | convenience | moderate | medium | `run-eagle-eye.sh` |
| 23 | `env -u CLAUDECODE` guard on claude invocation | Nested-session crash on manual re-runs | convenience | quick-win | low | `run-eagle-eye.sh` |
| 24 | Year-dated log filenames + persistent cron log + prune | Per-week logs collide annually; /tmp log unrotated | convenience | quick-win | low | `run-eagle-eye.sh`, crontab |

\*Rank 3 is the prompt-rule half only (quick-win); the deterministic URL-year verifier half is deferred (see rejected list).

---

## (A) Correctness & Verification Hardening

**Deterministic post-compile price gate (Rank 6, EE-DATA-02 / EE-VERIFY-01).** Today verification is
advisory: `verify-eagle-eye-calendar.py` always exits 0 and only checks calendar string-presence;
quality gates check byte-size only. **Fix:** port the already-shipping `verify-brief.py` (run daily
by the morning brief at `run-morning-brief.sh:632`, with tolerances `PRICE_THRESHOLD 0.02`,
`MOVE_THRESHOLD 2.0`, `MACRO_THRESHOLD 0.005`) to fact-check the Scorecard/Commodities/Crypto tables
in `EAGLE_EYE.md` against live Schwab quotes. **Critical guardrails:** default to
**auto-correct-and-flag** (not hard-halt) and **skip assets Schwab can't price** (Brent/BTC/ETH map
to `None`) — a naive fail-closed gate would cause false weekend halts. Files: `run-eagle-eye.sh`, new
verify script.

**Separate verify invocation + enforce-corrections (Rank 9, EE-VERIFY-01).** Research+verify+compile
run in one invocation (`run-eagle-eye.sh:425`); the model audits itself and is merely told to
"incorporate any corrections" with no machine check they landed. **Fix:** add
`check-cross-report-consistency.py` (the deterministic check that would have caught the WTI/Brent
outlier model-independently), surface a verification summary in the notification, and add an
`enforce-corrections.py` gate. **Guardrail:** corrections are free-form prose today — require a
**machine-readable fenced corrections block** in `VERIFICATION.md` and roll out
**warn/email-first, fail-closed only after the contract is proven** (the pipeline currently never
blocks on content; a fragile parser could hard-block a good report).

**Year/date discipline (Rank 3, EE-DATA-04).** Ship **Half 1 now**: add a prompt rule — any event
described as "this week / N days ago" must cite a source URL dated inside that window; state full
date incl. **year**; otherwise label it historical context with its real date. Pure additive prompt
text, near-zero risk. (Half 2 — a URL-year deterministic check — is deferred; see rejected list.)

**As-of provenance + cross-report reconciliation (Rank 10, EE-DATA-03).** The good report already
does inline provenance voluntarily; the gap is enforcement. **Scoped fix:** require explicit as-of
labels for the genuinely ambiguous weekend-vs-Friday classes (**commodities, crypto, FX, futures**) —
never bare "Friday close" without a verifiable basis — and add an explicit cross-report
price-reconciliation step to the VERIFY prompt. (Do **not** mandate `(as-of, URL)` on every number —
too heavy, and it would not have caught the W21 WTI error, which carried a correctly-formatted but
stale label.)

## (B) Deterministic Data Grounding (Wingman / collect-market-data)

**Price ground-truth step (Rank 5, EE-DATA-01).** Build `collect-weekly-data.py` (stdlib-only,
mirroring `collect-market-data.py`) + a `stamp-scorecard.py` that overwrites the Market Scorecard the
way `stamp-calendar.py` owns the Week Ahead. **Verified implementation notes:** exact weekly % must
come from `/api/history/{sym}?frequency_type=weekly` (the weekend quote snapshot returns
`prevClose==last, netPct=None` for cash indices — see EE-DATA-06); **YTD must use
`period_type=year&period=2&frequency_type=daily`** (a 1-year lookback lands in May, not December;
`period_type=ytd` returns 0 candles); the scorecard table schema is **unstable week-to-week**, so the
stamper must fuzzy-match rows by index name and patch numeric cells, not overwrite by column
position. **Implemented:** persists to a dedicated `weekly_scorecard` table in `market.db`, keyed by
`(market_date, symbol)` — **no new JSON.** Note: `period_type=ytd` actually returns ~102 candles (not 0),
but it lacks the prior Dec-31 close needed to anchor YTD, so `year&period=2` is still the right path.
(Verify-gate caveat for Rank 6: for `source='etf_proxy'` commodity rows, trust only `weekly_pct`+`proxy_for`
— the stored `level` is the ETF price, not the commodity spot, so comparing it to the report's spot would false-flag.)

**Commodities/rates/FX grounding (folded into Rank 5, EE-DATA-02).** Extend the collector: futures
levels via `/api/quotes`, weekly treasury deltas via FRED `DGSx` 5-day lookback, commodity weekly
deltas via **ETF proxies (USO/BNO/GLD/UUP)** — `/api/history` on `/`-prefixed futures roots returns
0 candles. This is the exact data that produced the W21 stale-Brent failure; market.db already holds
`/BZN26` Friday closes that would have caught it.

**Sector heatmap from rotation scanner (Rank 11, EE-DATA-03-sector).** `localhost:8080/api/rotation/rankings`
returns exact 5d returns + trend + RS percentile for all 11 SPDRs; `/api/rotation/regime` gives the
cycle phase. Build a sector collect + `stamp-sectors.py`; **fail-open** (leave the WebSearched table
if the API is down). Tighten the prompt to lock the column schema.

**DB-anchored anomaly/diff gate (Rank 12, EE-DATA-05).** *Correctly scoped:* deterministically
**diff the stamped scorecard/commodity numbers against fresh market.db Friday quotes** and flag
divergences. **Do not** "reuse `cross_validate`" (it's a deliberate no-op now) or "reuse
`detect_anomalies`" (a z-score scan of the DB structurally can't see LLM prose transcription errors).
Handle futures front-month roll. Effort is **large/build-new**, not reuse.

## (C) Calendar Integrity

**TZ double-conversion (Rank 4, EE-CAL-01 / EE-DATA-05-cal).** `utc_to_et()` is applied
unconditionally at `collect-weekly-calendar.py:416`, but the API mixes UTC (`source=forex-factory`)
and already-ET (`source=fred`) times, so FRED's 08:30 becomes an impossible 04:30. **Fix:** carry the
`source` field through `_extract_events()` (dropped at lines 161-171) and only convert `forex-factory`
rows. **Refinements:** tag the `_resolve_ff_dates` fallback rows `source='forex-factory'` so the
fallback still converts; put the "no HIGH/MED US release before 7:00 ET" check as a **WARN in the
verifier, not a hard assert in the collector**.

**Staleness / past-earnings guard (Rank 7, EE-CAL-02 / EE-VERIFY-02).** No staleness logic exists
anywhere. **Fix (load-bearing prong):** treat `source=manual` earnings as date-unverified —
**annotate "(date unverified — confirm)" or quarantine out of the stamped macro table** (earnings
belong in the LLM "Earnings to Watch" subsection) — and add a deterministic verifier check that
cross-references earnings-style rows against the authoritative `earnings` SQLite table (already holds
NVDA `2026-05-20`), raising a WARN. **Drop the "date < today" prong** — it would not have caught NVDA
(5/27 was genuinely future). **Prefer annotate over silent drop** (AAPL WWDC is a legitimate manual
row the user expects).

**Pre-stamp freshness gate (Rank 8, EE-CAL-05).** Stamp runs *before* verify, and verify can't veto.
Run validity checks in the collector and physically annotate/drop offending rows **before**
`stamp-calendar.py` reads the file; let the verifier return a **non-fatal advisory code** that
`run-eagle-eye.sh` logs loudly and emails. (Note: `cal_exit=$?` currently captures `tee`'s exit, not
python's — fix with `pipefail` or restructure.)

**Confidence from data quality (Rank 14, EE-CAL-03).** Confidence is hard-coded HIGH on any non-empty
result; the "AUTHORITATIVE / Do NOT override" language is unconditional. **Highest-value piece:**
soften to "agents SHOULD cross-check if confidence=MEDIUM." Derive MEDIUM from missing heavy events /
failed time-sanity / duplicates / stale recency. (The exit-code tiers are currently dead code.)

**Dedup (Rank 13, EE-CAL-04).** `merge_events()` is dead code (`all_events = api_events` at line 500).
FRED/Forex-Factory twins ship verbatim every week. **Fix:** dedup by `(date, normalized-name)`
stripping `m/m`/`q/q` suffixes (collapses exact twins like Durable Goods Orders == Durable Goods
Orders m/m) **plus a true-synonym map limited to Unemployment Claims↔Jobless Claims and Prelim GDP
q/q↔GDP Report**. **Explicitly exclude PCE↔Core PCE and headline↔core Durable Goods** — those are
distinct releases; collapsing them deletes a real event.

**FF year-boundary (Rank 16, EE-CAL-06).** `year = start_date.year` mis-years January events at the
Dec/Jan boundary. **Fix:** pick the year (start_year or +1) that lands the date in `[start,end]`; skip
without carry-forward if neither fits; wrap `.replace(year=y)` in try/except for Feb 29. Latent
(fallback path has never fired), low-risk, ship it.

## (D) Ops / Reliability

- **Model pinning (Rank 2, EE-OPS-03):** add `--model opus` (both siblings already pin it) and **log
  the resolved model + `--version`** at run start — the higher-value half, so every log records what
  produced the report.
- **Retry loop (Rank 17, EE-OPS-02):** mirror morning-brief's `MAX_RESEARCH_ATTEMPTS=2` return-rc
  shape; idempotent skip guards make retry safe. **Drop/guard the "parse reset time and sleep"
  sub-proposal** (unparseable, risks negative/huge sleeps) — use a bounded fixed backoff. Preserve
  `set +e/set -e` discipline.
- **Backup cron (Rank 19, EE-OPS-05):** one-line Mon 03:00 UTC job; the existing `if [[ -f report.html ]]`
  guard makes it a true no-op on success and auto-recovers a transient Sunday failure (would have
  recovered W17). Same primary+backup pattern as `eod-wrapup.js`.
- **Heartbeat + dead-man's-switch (Rank 18, EE-OPS-01):** the in-repo success email is the quick part,
  but the only thing that catches a *total no-run* is an **external dead-man's-switch**
  (healthchecks.io / ntfy) — needed because the Monday inject-weekly backstop is gated on a flaky
  GDrive fuse mount (live I/O error observed) and can itself silently not run.
- **`env -u CLAUDECODE` (Rank 23, EE-OPS-04):** scope **down** from a full `env -i` port — the
  nested-session crash only ever hit *manual* re-runs (every cron run succeeded), and a wholesale
  `env -i` whitelisting just HOME/PATH risks regressing the 4-subagent research phase. Minimal
  `env -u CLAUDECODE` matches the error's own advice.
- **Log naming (Rank 24, EE-OPS-06):** year-date the filename and persist/prune the cron log. Pure
  hygiene — git already preserves per-run provenance (the "audit trail destroyed" framing was
  overstated: logs use `tee -a` append and are git-tracked).

## (E) Report Decision-Utility

- **Pass-through-only inject levels (Rank 1, EE-UTIL-01):** **the top item overall.**
  `inject-weekly.sh:127` hard-instructs a "Key levels table (SPX support/resistance...)" but feeds
  only `EAGLE_EYE.md`, which has no such levels — so Claude synthesized "Resistance 7,500 / Support
  7,400→7,300" from round numbers into the trader's daily-touch notes. Reword to **pass-through
  only**: include only levels explicitly in the report; otherwise render "— (no level call in
  report)". Quick, low-risk, kills a live fabrication on the most-touched surface.
- **Sourced Key Levels table (Rank 15, EE-UTIL-02):** the deeper fix behind Rank 1 — pull SPY/QQQ
  gamma/put/call walls from `/api/levels` (verified reachable on weekends) into a new collect+stamp
  step. **Must label "as of Friday close"** (near-DTE gamma decays fast). Removes the fabrication
  *pressure*, not just the symptom.
- **Single source of truth for Risk Radar + Conviction grid (Rank 21, EE-UTIL-05):** these structures
  exist only in `report.html`, fabricated at render time from prose, then re-derived a third time by
  inject-weekly. Author them as structured sections in `EAGLE_EYE.md` during compile (which
  incorporates verification), then render/inject as passthrough.
- **Watchlist weekly % via API quote step (Rank 20, EE-UTIL-03):** 8/25 rows are "n/a" because the
  pipeline has **no deterministic quote stage**. Add an API quote step (not "try harder on WebSearch"
  — that's the stale-price trap); optionally tag held names from the real `HOLDINGS.md` ledger. Mark
  genuinely-unavailable prices "not fetched," not "n/a".
- **"What Changed This Week" block (Rank 22, EE-UTIL-04):** **accept the narrative half only** —
  scoped to levels/stances present in both reports, labeled approximate, prior-week found via
  date-sorted archive glob (not `WEEK_NUM-1`, which breaks at ISO year rollover). **Drop the per-card
  delta-arrow half** — the conviction grid taxonomy changes week-to-week (per-ticker vs per-thesis),
  so there's no stable join key and arrows would reintroduce fabrication risk.

---

## Considered But Rejected / Overstated

- **Per-number `(as-of, source-URL)` on every number (EE-DATA-03):** Rejected as written. The W21 WTI
  error carried a correctly-formatted "as of Friday's close" label and was still stale — mandatory
  labeling would not have caught it. Downgraded to a scoped commodities/crypto/FX rule + cross-report
  reconciliation. *(correctness-critical → quality)*
- **Deterministic URL-year verifier for catalysts (EE-DATA-04 Half 2):** Deferred. The Moody's error
  lived outside the calendar verifier's scope; a real check needs a new pre-compile body verifier, and
  URL-path-year is a brittle soft signal (many valid sources have no year in the URL). Ship the prompt
  rule (Half 1); treat this as a design note dependent on the not-yet-built body verifier.
- **"date < today" calendar filter (EE-CAL-02):** Rejected — would not catch the actual incident
  (NVDA was mis-placed on a *future* day). Only the earnings cross-check prong is load-bearing.
- **Collapsing PCE↔Core PCE / headline↔core Durable Goods in dedup (EE-CAL-04):** Rejected — these are
  distinct releases; merging them deletes a real scheduled event, a fabrication-adjacent correctness
  failure. Limit synonyms to true twins only.
- **"Reuse `detect_anomalies` + `cross_validate`" (EE-DATA-05):** Rejected as a *reuse* claim —
  `cross_validate` is a deliberate no-op; a DB z-score scan can't see LLM prose/date errors. The
  correct fix (stamped-number vs DB-quote diff) is build-new, large effort, correctness-moderate.
- **Per-card conviction delta arrows (EE-UTIL-04):** Rejected — no stable join key across weeks
  (per-ticker vs per-thesis taxonomy), would force fuzzy-matching and reintroduce fabrication risk.
- **Full `env -i` clean-env port (EE-OPS-04):** Downgraded from reliability to convenience and scoped
  down — the crash only ever hit manual re-runs; every cron run succeeded. Use minimal
  `env -u CLAUDECODE`.
- **"Logs collide annually / audit trail destroyed" (EE-OPS-06):** Overstated — logs use `tee -a`
  (append) and are git-tracked, so provenance is preserved; "/tmp cleared on reboot" is false on this
  host (disk-backed; real risk is 30-day tmpfiles aging). Kept as a convenience hygiene fix only.
- **`eod_summary` as the levels source (EE-DATA-04 levels):** Rejected — the `spy_call_wall`/etc.
  fields are NULL in all 64 historical rows due to a never-working field-path bug in `eod-wrapup.js`.
  Source Key Levels from `/api/levels/{SYMBOL}` directly instead.

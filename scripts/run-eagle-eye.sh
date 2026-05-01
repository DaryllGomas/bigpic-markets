#!/usr/bin/env bash
#
# run-eagle-eye.sh - Automated weekly Eagle Eye macro report via cron
# Part of BigPic Markets (markets.bigpicsolutions.com)
#
# Runs Claude Code to generate the weekly Eagle Eye report, build HTML,
# and publish to GitHub Pages. Designed to run via cron at 4:00 PM PT on Sundays.
#
# Exit codes:
#   0 - Success
#   1 - Report generation failure
#   2 - Publish failure
#   3 - Missing dependency
#
set -euo pipefail

# ── Configuration ────────────────────────────────────────────────────────────
REPO_DIR="$HOME/projects/bigpic-markets"
EAGLE_DIR="$REPO_DIR/eagle-eye"
CLAUDE_BIN="$HOME/.local/bin/claude"
EMAIL_TO="daryll@bigpicsolutions.com"
TIMEOUT_RESEARCH=3600   # 60 minutes for research + verify + compile
TIMEOUT_HTML_1=900      # 15 minutes for HTML skeleton + first 5 sections
TIMEOUT_HTML_2=900      # 15 minutes for remaining 6 sections
TIMEOUT_PUBLISH=300     # 5 minutes for archive update + git push
DB_PATH="$REPO_DIR/data/market.db"
CALENDAR_SCRIPT="$REPO_DIR/scripts/collect-weekly-calendar.py"

# ── Date & week calculation ──────────────────────────────────────────────────
DOW=$(date +%u)  # 1=Mon, 7=Sun
if [ "$DOW" -eq 7 ]; then
    SUNDAY_DATE=$(date +%Y-%m-%d)
else
    DAYS_UNTIL_SUNDAY=$((7 - DOW))
    SUNDAY_DATE=$(date -d "+${DAYS_UNTIL_SUNDAY} days" +%Y-%m-%d)
fi

WEEK_NUM=$(date -d "$SUNDAY_DATE" +%V)
FRIDAY_DATE=$(date -d "$SUNDAY_DATE -2 days" +%Y-%m-%d)
WEEK_FOLDER="W${WEEK_NUM}_${SUNDAY_DATE}"
WEEK_DIR="$EAGLE_DIR/$WEEK_FOLDER"
LOG_DIR="$EAGLE_DIR/logs"
LOG_FILE="$LOG_DIR/eagle-eye-W${WEEK_NUM}.log"

# ── Logging ──────────────────────────────────────────────────────────────────
mkdir -p "$LOG_DIR" "$WEEK_DIR"

log() {
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] $1" | tee -a "$LOG_FILE"
}

log_error() {
    log "ERROR: $1"
}

cleanup() {
    local exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
        log_error "Script exited with code $exit_code"
    fi
}
trap cleanup EXIT

# ── Dependency checks ────────────────────────────────────────────────────────
check_deps() {
    local missing=0

    if [[ ! -x "$CLAUDE_BIN" ]]; then
        log_error "Claude binary not found at $CLAUDE_BIN"
        missing=1
    fi

    if ! command -v git &>/dev/null; then
        log_error "git is not installed"
        missing=1
    fi

    if [[ ! -d "$REPO_DIR/.git" ]]; then
        log_error "bigpic-markets repo not found at $REPO_DIR"
        missing=1
    fi

    if [[ $missing -ne 0 ]]; then
        exit 3
    fi
}

# ── Failure alert ────────────────────────────────────────────────────────────
send_failure_alert() {
    local reason="$1"
    local log_tail=""

    if [[ -f "$LOG_FILE" ]]; then
        log_tail=$(tail -50 "$LOG_FILE" | sed 's/&/\&amp;/g; s/</\&lt;/g; s/>/\&gt;/g')
    fi

    local alert_html
    alert_html=$(cat <<EOF
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"/></head>
<body style="background-color:#0a0f1a;color:#fdf6ec;font-family:sans-serif;padding:24px;">
<h1 style="color:#ef4444;">Eagle Eye Failed — W${WEEK_NUM} ($FRIDAY_DATE)</h1>
<p><strong>Reason:</strong> $reason</p>
<h2 style="color:#f4a261;">Last 50 Log Lines</h2>
<pre style="background:#12192e;border:1px solid rgba(232,184,125,0.18);padding:16px;overflow-x:auto;font-size:13px;color:#c9d6df;border-radius:12px;">$log_tail</pre>
</body>
</html>
EOF
    )

    if command -v msmtp &>/dev/null; then
        echo "$alert_html" | {
            echo "From: eagle-eye@$(hostname)"
            echo "To: $EMAIL_TO"
            echo "Subject: [FAILED] Eagle Eye W${WEEK_NUM} — $FRIDAY_DATE"
            echo "MIME-Version: 1.0"
            echo "Content-Type: text/html; charset=utf-8"
            echo ""
            cat -
        } | msmtp "$EMAIL_TO" 2>/dev/null || log_error "Failed to send failure alert email"
    else
        log_error "msmtp not available, cannot send failure alert"
    fi
}

# ── Auto-discover thesis files ───────────────────────────────────────────────
discover_theses() {
    THESIS_FILES=$(find "$REPO_DIR/research" -maxdepth 2 \( -name "THESIS.md" -o -name "CALENDAR.md" \) -type f | sort)
    THESIS_COUNT=$(echo "$THESIS_FILES" | wc -l)
    THESIS_LIST=$(echo "$THESIS_FILES" | sed 's/^/- /')
}

# ── Build research prompt (Invocation 1) ─────────────────────────────────────
build_research_prompt() {
    cat <<PROMPT_EOF
Run the Eagle Eye weekly macro report. This is a POINT-IN-TIME SNAPSHOT as of right
now ($SUNDAY_DATE). It covers two things: (1) the trading week ending $FRIDAY_DATE,
and (2) ANY breaking news or developments that have occurred since market close Friday
through right now (Saturday/Sunday). Weekend events are often market-moving — wars,
geopolitical crises, policy announcements, earnings surprises — and MUST be captured.
Store in $WEEK_DIR/

STEP 1 — RESEARCH: Spawn 4 agents using the Task tool (subagent_type: "general-purpose").
Launch ALL 4 in a SINGLE message so they run in parallel. Each agent uses WebSearch
to gather current data and writes its report to disk. Do NOT use TeamCreate or SendMessage.

CRITICAL: Each agent must search for BOTH weekly recap data AND breaking weekend news.
If a major event happened after Friday's close (geopolitical crisis, policy change,
corporate news, natural disaster, etc.), it MUST be prominently covered — not buried
or ignored because it falls outside the Mon-Fri trading week. Weekend developments
that will move Monday's open are MORE important than last Tuesday's sector rotation.

Agent 1 — Equities & Sectors (writes $WEEK_DIR/01_equities_sectors.md):
  Research: Major indices (SPX, NDX, DJIA, RUT) weekly performance with levels.
  Sector rotation and relative strength (XLK, XLE, XLF, XLV, XLI, etc.).
  Key earnings reports this week — beats/misses and guidance.
  Market breadth (advance/decline, new highs/lows, % above 200-day).
  VIX level and term structure. Put/call ratios.
  Thesis watchlist tickers — check each sector thesis for Tier 1/2 names, report
  weekly price action and any catalysts.
  **Weekend/breaking**: Search for any post-Friday developments affecting equities.
  Include Sunday night futures if available.
  Structure: ## Market Overview, ## Weekend Developments (if any), ## Sector Performance,
  ## Earnings, ## Breadth & Sentiment, ## Thesis Watchlist, ## Sources (linked URLs).

Agent 2 — Rates, Credit & Fed (writes $WEEK_DIR/02_rates_credit_fed.md):
  Research: Treasury curve (2Y, 5Y, 10Y, 30Y levels and weekly changes).
  Yield curve shape (2s10s, 3m10y spreads). Fed funds futures pricing.
  Fed speakers this week — quotes and hawkish/dovish lean.
  FOMC minutes if released. Credit spreads (IG, HY OAS).
  Bank lending conditions. TGA balance. ON RRP.
  **Weekend/breaking**: Search for any post-Friday Fed commentary, policy changes,
  or geopolitical events affecting rates/credit markets.
  Structure: ## Treasury Yields, ## Yield Curve, ## Fed Watch, ## Credit Markets,
  ## Liquidity, ## Weekend Developments (if any), ## Sources (linked URLs).

Agent 3 — Commodities & Forex (writes $WEEK_DIR/03_commodities_forex.md):
  Research: Crude oil (WTI, Brent) — price, inventory, OPEC news.
  Gold and silver levels. Copper (demand signal). Uranium/nuclear.
  Natural gas. Agricultural commodities if notable.
  DXY and major pairs (EUR/USD, USD/JPY, GBP/USD). EM currencies if notable.
  Supply chain indicators.
  **Weekend/breaking**: Search for any post-Friday geopolitical events, supply
  disruptions, or commodity-moving news. Include weekend proxy prices (OTC, futures
  if open) when available.
  Structure: ## Energy, ## Metals, ## Commodities, ## Forex,
  ## Weekend Developments (if any), ## Sources (linked URLs).

Agent 4 — Crypto & Alternative (writes $WEEK_DIR/04_crypto_alternative.md):
  Research: BTC and ETH price action, levels, dominance.
  Notable altcoin moves (SOL, AVAX, LINK, etc.).
  DeFi TVL trends. Stablecoin market cap and flows.
  Bitcoin/Ethereum ETF flows (IBIT, ETHA, etc.).
  Regulatory news. Institutional adoption signals.
  **Weekend/breaking**: Crypto trades 24/7 — report CURRENT prices as of now,
  not just Friday close. Include any weekend moves or liquidation events.
  Structure: ## Bitcoin, ## Ethereum, ## Altcoins & DeFi, ## ETF Flows,
  ## Regulation & Institutional, ## Weekend Developments (if any),
  ## Sources (linked URLs).

ALL agents must read these $THESIS_COUNT sector thesis files for watchlist tickers and context:
$THESIS_LIST

ECONOMIC CALENDAR FOR THE WEEK AHEAD:
Read $WEEK_DIR/next_week_calendar.md for context on what economic releases are scheduled.
NOTE: Economic event tables will be injected automatically into the final report by
a post-processing script (stamp-calendar.py). Do NOT write economic event tables in
the Week Ahead section — they will be overwritten. Instead, focus on:
- Market narrative and commentary for each day (why each event matters, what to watch)
- Earnings to watch (from your research)
- Fed speaker significance
- Notable absences and what their absence means for the week

STEP 2 — VERIFY (do this yourself, no agent spawn):
Read all 4 completed research reports from $WEEK_DIR/.
Cross-check ticker prices and percentage moves across reports for consistency.
Spot-check 5-10 key data points against their cited source URLs using WebFetch.
Flag outliers and inconsistencies. Sanity-check percentage moves.

Write $WEEK_DIR/VERIFICATION.md with pass/fail status and any corrections needed.
(Note: Week Ahead calendar verification is handled by stamp-calendar.py post-compilation.)

STEP 3 — COMPILE (do this yourself):
Read all 4 reports + VERIFICATION.md. Incorporate any corrections.
Write $WEEK_DIR/EAGLE_EYE.md with these sections:
- This Week's Take (2-3 paragraph executive summary — lead with the BIGGEST story,
  whether it happened Monday or Sunday morning. If a major weekend event will dominate
  Monday's open, that is the lede, not last week's sector rotation.)
- Weekend & Breaking Developments (if any major events occurred after Friday close —
  consolidate from all 4 agent reports. If nothing material, omit this section.)
- Market Scorecard (table: index, level, weekly change, YTD. Include Sunday futures if available.)
- Sector Heatmap (table: sector ETF, weekly return, trend)
- Thesis Watchlist Tracker (grouped by thesis with tier + weekly delta)
- Fed & Rates Outlook
- Commodities & Forex Snapshot
- Crypto Snapshot (use current weekend prices, not just Friday close)
- The Week Ahead (Write day headers ### Monday/Tuesday/etc with date, then a short
  commentary paragraph for each day about what to watch and why. Do NOT write economic
  event tables — they are injected automatically by stamp-calendar.py. Include
  ### Earnings to Watch and ### Notable Absences subsections.)
  CRITICAL — DAY HEADERS: Read $WEEK_DIR/next_week_calendar.md and use its day headers
  EXACTLY for the Week Ahead section. Do NOT compute day-of-week from the date yourself
  — read the day name + date verbatim from next_week_calendar.md. If the calendar says
  "## Tuesday, April 28", your header is "### Tuesday, April 28" — same day name, same
  date. Wrong day-of-week assignments (e.g., calling Tuesday "Monday") corrupt every
  day's commentary. The stamp-calendar.py script will OVERRIDE wrong dates with
  authoritative ones, but getting them right the first time keeps commentary aligned.
  Do NOT add parenthetical day labels like "(FOMC Day 1)" or "(GOOG Earnings AC)"
  in the day header — put those in the commentary paragraph below the table instead.
  The header is just "### {DayName}, {Month} {Day}" — nothing else.
- Positioning & Thesis Update (actionable takeaways incorporating weekend developments)
- Sources (consolidated from all reports)
PROMPT_EOF
}

# ── Build HTML Part 1 prompt (Invocation 2a) ─────────────────────────────────
build_html_part1_prompt() {
    cat <<PROMPT_EOF
Build the FIRST HALF of the Eagle Eye HTML report for W${WEEK_NUM} ($SUNDAY_DATE).
This report is a point-in-time snapshot covering the trading week ending $FRIDAY_DATE
plus any breaking weekend developments through $SUNDAY_DATE.

STEP 1 — READ: Read the compiled report at $WEEK_DIR/EAGLE_EYE.md

STEP 2 — HTML BUILD (Part 1): Generate $WEEK_DIR/report.html with the FULL page structure
and the FIRST 5 content sections. Match the BigPic Solutions site theme exactly:
- Background: #0a0f1a (deep navy), cards: rgba(18, 26, 46, 0.88)
- Accent gold: #e8b87d, amber: #f4a261, coral: #ef8354
- Text: #fdf6ec (primary), #c9d6df (secondary), #6b7d8e (muted)
- Borders: rgba(232,184,125,0.08) subtle, rgba(232,184,125,0.18) glow
- Fonts: Space Grotesk (sans), Newsreader (serif/accent)
- Green #22c55e for positive, Red #ef4444 for negative
- CRITICAL: Use align-items:stretch on .bar-chart (not flex-end) to prevent bar height bug
- Use completed sector HTML reports as quality reference

The file MUST include:
1. Full <!DOCTYPE html>, <head> with ALL CSS and JS (counters, heatmap, filters, etc.)
2. Fixed nav with back-arrow link to ../index.html (Eagle Eye archive page)
3. Hero/header section
4. Section: Market Scorecard (animated counters, table)
5. Section: Weekend & Breaking Developments (if present — coral accent border alert styling)
6. Section: This Week's Take (executive summary)
7. Section: Sector Heatmap (interactive heatmap viz)
8. Section: Fed & Rates Outlook (yield curve viz)
9. The EXACT marker <!-- CONTINUE HERE --> on its own line where the remaining sections will go
10. Footer and closing </body></html> tags

The marker <!-- CONTINUE HERE --> goes AFTER rates and BEFORE where watchlist would start.
The footer and page-closing tags go AFTER the marker.

Do NOT include these sections (they come in Part 2): watchlist tracker, commodities, crypto,
week ahead, positioning, sources.
PROMPT_EOF
}

# ── Build HTML Part 2 prompt (Invocation 2b) ─────────────────────────────────
build_html_part2_prompt() {
    cat <<PROMPT_EOF
Complete the SECOND HALF of the Eagle Eye HTML report for W${WEEK_NUM} ($SUNDAY_DATE).

STEP 1 — READ BOTH FILES:
- Read the compiled report at $WEEK_DIR/EAGLE_EYE.md (for content)
- Read the partial HTML at $WEEK_DIR/report.html (from Part 1)

STEP 2 — HTML BUILD (Part 2): Find the <!-- CONTINUE HERE --> marker in report.html
and REPLACE it with the remaining 6 content sections. Keep ALL existing content and
structure intact — only replace the marker line.

Insert these sections at the marker location:
1. Section: Thesis Watchlist Tracker (filterable cards grouped by thesis with tier + weekly delta)
2. Section: Commodities & Forex Snapshot
3. Section: Crypto Snapshot
4. Section: The Week Ahead (calendar layout — render the day-by-day tables and
   commentary exactly as they appear in EAGLE_EYE.md. Calendar data is pre-verified.)
5. Section: Positioning & Thesis Update (risk radar, actionable takeaways)
6. Section: Sources (collapsible, consolidated from all reports)

Use the SAME theme/styling already in the file. Match card styles, colors, spacing.
The <!-- CONTINUE HERE --> marker must be completely removed — do not leave it in the file.

IMPORTANT: Do NOT modify any content before the marker or after the footer. Only replace
the marker line with the new sections.
PROMPT_EOF
}

# ── Build publish prompt (Invocation 2c) ──────────────────────────────────────
build_publish_prompt() {
    cat <<PROMPT_EOF
Publish the Eagle Eye report for W${WEEK_NUM} ($SUNDAY_DATE).

STEP 1 — ARCHIVE: Add a new entry to $EAGLE_DIR/index.html for this week's report.
The archive page has entries between <!-- ARCHIVE_ENTRIES_START --> and <!-- ARCHIVE_ENTRIES_END -->.
Add a new entry BEFORE existing entries (latest first). Move the "Latest" badge from any
previous entry to the new one. Use this HTML format for the entry:
<a href="$WEEK_FOLDER/report.html" class="report-entry">
  <div class="info">
    <span class="week">Week ${WEEK_NUM} — [TITLE FROM EAGLE_EYE.md "This Week's Take" heading]</span>
    <span class="date">Week ending $FRIDAY_DATE</span>
  </div>
  <span class="badge">Latest</span>
  <span class="arrow">&rarr;</span>
</a>

Read $WEEK_DIR/EAGLE_EYE.md to get the title for the week entry.

STEP 2 — COMMIT & PUSH:
cd $REPO_DIR && git add -A && git commit -m "Eagle Eye W${WEEK_NUM} — snapshot $SUNDAY_DATE (week ending $FRIDAY_DATE)" && git push
PROMPT_EOF
}

# ── Run Claude with timeout ──────────────────────────────────────────────────
run_claude() {
    local phase_name="$1"
    local timeout_secs="$2"
    local prompt="$3"
    local claude_exit=0

    log "Running Claude [$phase_name] (timeout: ${timeout_secs}s)..."

    set +e
    timeout --kill-after=30 "$timeout_secs" "$CLAUDE_BIN" \
        -p "$prompt" \
        --dangerously-skip-permissions \
        2>&1 | tee -a "$LOG_FILE"
    claude_exit=${PIPESTATUS[0]}
    set -e

    if [[ $claude_exit -eq 124 ]]; then
        log_error "Claude [$phase_name] timed out (SIGTERM) after ${timeout_secs}s"
        send_failure_alert "Claude [$phase_name] timed out (SIGTERM) after ${timeout_secs} seconds" || true
        exit 1
    elif [[ $claude_exit -eq 137 ]]; then
        log_error "Claude [$phase_name] timed out (SIGKILL) after $((timeout_secs + 30))s — process ignored SIGTERM"
        send_failure_alert "Claude [$phase_name] had to be force-killed (SIGKILL) — ignored SIGTERM for 30s" || true
        exit 1
    elif [[ $claude_exit -ne 0 ]]; then
        log_error "Claude [$phase_name] exited with code $claude_exit"
        send_failure_alert "Claude [$phase_name] exited with code $claude_exit" || true
        exit 1
    fi

    log "Claude [$phase_name] finished successfully"
}

# ── Main ─────────────────────────────────────────────────────────────────────
main() {
    log "=== Eagle Eye W${WEEK_NUM} Started ==="
    log "Week ending: $FRIDAY_DATE"
    log "Output: eagle-eye/$WEEK_FOLDER/"

    check_deps
    log "All dependencies verified"

    # Skip if already generated this week
    if [[ -f "$WEEK_DIR/report.html" ]]; then
        log "Report already exists for W${WEEK_NUM} — skipping"
        exit 0
    fi

    # ── Invocation 1: Research + Verify + Compile ─────────────────────────
    if [[ ! -f "$WEEK_DIR/EAGLE_EYE.md" ]]; then
        discover_theses
        log "Found $THESIS_COUNT research files (sector theses + structural calendar)"

        # ── Pre-collect next week's economic calendar ─────────────────
        MONDAY_DATE=$(date -d "$SUNDAY_DATE +1 day" +%Y-%m-%d)
        NEXT_FRIDAY=$(date -d "$SUNDAY_DATE +5 days" +%Y-%m-%d)
        log "Collecting economic calendar for $MONDAY_DATE to $NEXT_FRIDAY..."
        python3 "$CALENDAR_SCRIPT" \
            --start "$MONDAY_DATE" --end "$NEXT_FRIDAY" \
            --output "$WEEK_DIR/next_week_calendar.md" \
            --db "$DB_PATH" 2>&1 | tee -a "$LOG_FILE"
        local cal_exit=$?
        if [[ $cal_exit -eq 0 ]]; then
            log "Calendar collected (full confidence)"
        elif [[ $cal_exit -le 2 ]]; then
            log "WARNING: Calendar collected with reduced confidence (exit=$cal_exit)"
        else
            log_error "Calendar collection failed — Week Ahead will have no ground truth"
        fi

        run_claude "research" "$TIMEOUT_RESEARCH" "$(build_research_prompt)"

        if [[ ! -f "$WEEK_DIR/EAGLE_EYE.md" ]]; then
            log_error "EAGLE_EYE.md not found at $WEEK_DIR/EAGLE_EYE.md"
            send_failure_alert "EAGLE_EYE.md was not created by Claude [research]" || true
            exit 1
        fi

        local md_size
        md_size=$(stat -c%s "$WEEK_DIR/EAGLE_EYE.md")
        log "EAGLE_EYE.md generated: $md_size bytes"

        if [[ $md_size -lt 500 ]]; then
            log_error "EAGLE_EYE.md too small ($md_size bytes), may be incomplete"
            send_failure_alert "EAGLE_EYE.md generated but suspiciously small ($md_size bytes)" || true
            exit 1
        fi

        # ── Stamp calendar data into Week Ahead (deterministic) ─────
        if [[ -f "$WEEK_DIR/next_week_calendar.md" ]]; then
            log "Stamping calendar into Week Ahead..."
            python3 "$REPO_DIR/scripts/stamp-calendar.py" \
                --report "$WEEK_DIR/EAGLE_EYE.md" \
                --calendar "$WEEK_DIR/next_week_calendar.md" \
                2>&1 | tee -a "$LOG_FILE"
            log "Calendar stamp complete"

            # Sanity check (informational only — always exit 0)
            log "Running post-stamp verification..."
            python3 "$REPO_DIR/scripts/verify-eagle-eye-calendar.py" \
                --report "$WEEK_DIR/EAGLE_EYE.md" \
                --calendar "$WEEK_DIR/next_week_calendar.md" \
                --verification "$WEEK_DIR/VERIFICATION.md" \
                2>&1 | tee -a "$LOG_FILE"
        fi
    else
        log "EAGLE_EYE.md already exists — skipping research phase"
    fi

    # ── Invocation 2a: HTML Build Part 1 (skeleton + first 5 sections) ───
    run_claude "html-build-1" "$TIMEOUT_HTML_1" "$(build_html_part1_prompt)"

    if [[ ! -f "$WEEK_DIR/report.html" ]]; then
        log_error "report.html not found after html-build-1"
        send_failure_alert "report.html was not created by Claude [html-build-1]" || true
        exit 1
    fi

    local html_size_1
    html_size_1=$(stat -c%s "$WEEK_DIR/report.html")
    log "report.html after Part 1: $html_size_1 bytes"

    if [[ $html_size_1 -lt 2000 ]]; then
        log_error "report.html too small after Part 1 ($html_size_1 bytes)"
        send_failure_alert "report.html after Part 1 is only $html_size_1 bytes — expected >2KB" || true
        exit 1
    fi

    # ── Invocation 2b: HTML Build Part 2 (remaining 6 sections) ──────────
    run_claude "html-build-2" "$TIMEOUT_HTML_2" "$(build_html_part2_prompt)"

    local html_size_2
    html_size_2=$(stat -c%s "$WEEK_DIR/report.html")
    log "report.html after Part 2: $html_size_2 bytes"

    if [[ $html_size_2 -lt 40000 ]]; then
        log_error "report.html too small after Part 2 ($html_size_2 bytes) — expected >40KB"
        send_failure_alert "report.html after Part 2 is only $html_size_2 bytes — expected >40KB" || true
        exit 1
    fi

    if grep -q '<!-- CONTINUE HERE -->' "$WEEK_DIR/report.html"; then
        log_error "<!-- CONTINUE HERE --> marker still present after Part 2 — sections not inserted"
        send_failure_alert "Part 2 did not replace the <!-- CONTINUE HERE --> marker" || true
        exit 1
    fi

    # ── Invocation 2c: Publish (archive entry + git push) ────────────────
    run_claude "html-publish" "$TIMEOUT_PUBLISH" "$(build_publish_prompt)"

    log "=== Eagle Eye W${WEEK_NUM} Complete ==="
    log "Published: markets.bigpicsolutions.com/eagle-eye/$WEEK_FOLDER/report.html"
    exit 0
}

main "$@"

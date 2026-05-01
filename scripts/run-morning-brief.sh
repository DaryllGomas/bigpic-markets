#!/usr/bin/env bash
#
# run-morning-brief.sh - Automated daily Morning Brief via cron
# Part of BigPic Markets (markets.bigpicsolutions.com)
#
# Generates the BigPic Morning Brief (markdown + themed HTML),
# publishes to GitHub Pages, and updates the archive index.
# Designed to run via cron at ~5:20 AM Pacific before markets open.
#
# Exit codes:
#   0 - Success
#   1 - Report generation failure
#   2 - Email delivery failure (alert)
#   3 - Missing dependency
#
set -euo pipefail

# ── Configuration ────────────────────────────────────────────────────────────
REPO_DIR="$HOME/projects/bigpic-markets"
BRIEF_DIR="$REPO_DIR/morning-brief"
PROJECT_DIR="$HOME/projects/bigpic-markets"
CLAUDE_BIN="$HOME/.local/bin/claude"
EMAIL_TO="daryll@bigpicsolutions.com"
TIMEOUT_RESEARCH=900    # 15 minutes for report writing (reads pre-collected data, no web search)
TIMEOUT_HTML=900        # 15 minutes for HTML build + publish
MAX_RESEARCH_ATTEMPTS=2
COLLECT_SCRIPT="$REPO_DIR/scripts/collect-market-data.py"
BRIEFING_DIR="$REPO_DIR/data"

# Agent teams no longer needed — single Claude invocation reads pre-collected data
# export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1

# ── Date calculation ─────────────────────────────────────────────────────────
DOW=$(date +%u)  # 1=Mon ... 5=Fri, 6=Sat, 7=Sun
if [ "$DOW" -le 5 ]; then
    TARGET_DATE=$(date +%Y-%m-%d)
elif [ "$DOW" -eq 6 ]; then
    TARGET_DATE=$(date -d "+2 days" +%Y-%m-%d)
else
    TARGET_DATE=$(date -d "+1 day" +%Y-%m-%d)
fi

DAY_NAME=$(date -d "$TARGET_DATE" +%a)
DAY_FULL=$(date -d "$TARGET_DATE" +%A)
DAY_DISPLAY=$(date -d "$TARGET_DATE" +"%B %-d")
MONTH=$(date -d "$TARGET_DATE" +%Y-%m)
MONTH_DIR="$BRIEF_DIR/$MONTH"
OUTPUT_MD="${TARGET_DATE}_${DAY_NAME}.md"
OUTPUT_HTML="${TARGET_DATE}_${DAY_NAME}.html"
LOG_DIR="$BRIEF_DIR/logs"
LOG_FILE="$LOG_DIR/brief-${TARGET_DATE}.log"
TRACKING_FILE="$LOG_DIR/run-history.csv"
RUN_START_EPOCH=$(date +%s)

# ── Logging ──────────────────────────────────────────────────────────────────
mkdir -p "$LOG_DIR" "$MONTH_DIR"

log() {
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] $1" | tee -a "$LOG_FILE"
}

log_error() {
    log "ERROR: $1"
}

# ── Run history tracking ────────────────────────────────────────────────────
track_run() {
    local status="$1"  # SUCCESS or FAILED
    local notes="${2:-}"

    local run_end_epoch duration
    run_end_epoch=$(date +%s)
    duration=$((run_end_epoch - RUN_START_EPOCH))

    # Create header if file doesn't exist
    if [[ ! -f "$TRACKING_FILE" ]]; then
        echo "date,status,duration_seconds,research_size_bytes,html_size_bytes,notes" > "$TRACKING_FILE"
    fi

    local md_size=0 html_size=0
    [[ -f "$MONTH_DIR/$OUTPUT_MD" ]] && md_size=$(stat -c%s "$MONTH_DIR/$OUTPUT_MD")
    [[ -f "$MONTH_DIR/$OUTPUT_HTML" ]] && html_size=$(stat -c%s "$MONTH_DIR/$OUTPUT_HTML")

    echo "${TARGET_DATE},${status},${duration},${md_size},${html_size},${notes}" >> "$TRACKING_FILE"
}

# ── Post-mortem diagnostics ─────────────────────────────────────────────────
dump_diagnostics() {
    local team_suffix="${1:-$TARGET_DATE}"
    local team_dir="$HOME/.claude/teams/morning-brief-${team_suffix}"
    local task_dir="$HOME/.claude/tasks/morning-brief-${team_suffix}"

    log "=== DIAGNOSTIC DUMP (team: morning-brief-${team_suffix}) ==="

    # Team config
    if [[ -f "$team_dir/config.json" ]]; then
        log "Team config:"
        cat "$team_dir/config.json" >> "$LOG_FILE" 2>/dev/null
        echo "" >> "$LOG_FILE"
    else
        log "No team config found at $team_dir/config.json"
    fi

    # Task statuses
    if [[ -d "$task_dir" ]]; then
        log "Task files:"
        for f in "$task_dir"/*.json; do
            [[ -f "$f" ]] || continue
            cat "$f" >> "$LOG_FILE" 2>/dev/null
            echo "" >> "$LOG_FILE"
        done
    fi

    # Inbox messages
    if [[ -d "$team_dir/inboxes" ]]; then
        log "Inbox messages:"
        for f in "$team_dir/inboxes"/*.json; do
            [[ -f "$f" ]] || continue
            log "  $(basename "$f"):"
            cat "$f" >> "$LOG_FILE" 2>/dev/null
            echo "" >> "$LOG_FILE"
        done
    fi

    # Partial research files
    for rf in "$MONTH_DIR/markets-research.md" "$MONTH_DIR/watchlist-research.md"; do
        if [[ -f "$rf" ]]; then
            local sz mod_time
            sz=$(stat -c%s "$rf")
            mod_time=$(stat -c '%y' "$rf" | cut -d. -f1)
            log "Partial research: $(basename "$rf") ($sz bytes, last modified $mod_time)"
        else
            log "Partial research: $(basename "$rf") — NOT CREATED"
        fi
    done

    log "=== END DIAGNOSTIC DUMP ==="
}

write_postmortem() {
    local exit_code="$1"
    local postmortem="$LOG_DIR/postmortem-${TARGET_DATE}.md"
    local team_dir="$HOME/.claude/teams/morning-brief-${TARGET_DATE}"
    local task_dir="$HOME/.claude/tasks/morning-brief-${TARGET_DATE}"

    {
        echo "# Post-Mortem: Morning Brief $TARGET_DATE"
        echo ""
        echo "**Status:** FAILED (exit code $exit_code)"
        echo "**Start:** $(head -1 "$LOG_FILE" 2>/dev/null | grep -oP '\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}' || echo 'unknown')"
        echo "**End:** $(date '+%Y-%m-%d %H:%M:%S')"
        echo ""

        echo "## Research Files"
        for rf in "$MONTH_DIR/markets-research.md" "$MONTH_DIR/watchlist-research.md" "$MONTH_DIR/$OUTPUT_MD"; do
            if [[ -f "$rf" ]]; then
                local sz mod_time
                sz=$(stat -c%s "$rf")
                mod_time=$(stat -c '%y' "$rf" | cut -d. -f1)
                echo "- \`$(basename "$rf")\`: $sz bytes, last modified $mod_time"
            else
                echo "- \`$(basename "$rf")\`: NOT CREATED"
            fi
        done
        echo ""

        echo "## Team Members"
        if [[ -f "$team_dir/config.json" ]]; then
            python3 -c "
import json, datetime
with open('$team_dir/config.json') as f:
    cfg = json.load(f)
for m in cfg.get('members', []):
    joined = m.get('joinedAt', 0)
    ts = datetime.datetime.fromtimestamp(joined / 1000).strftime('%H:%M:%S') if joined else '?'
    print(f\"- {m['name']} ({m['agentType']}), joined at {ts}\")
" 2>/dev/null || echo "- (could not parse config)"
        else
            echo "- No team config found"
        fi
        echo ""

        echo "## Task Statuses"
        if [[ -d "$task_dir" ]]; then
            for f in "$task_dir"/*.json; do
                [[ -f "$f" ]] || continue
                python3 -c "
import json
with open('$f') as fh:
    t = json.load(fh)
print(f\"- Task {t.get('id','?')}: {t.get('subject','?')} — status: {t.get('status','?')}\")
" 2>/dev/null
            done
        else
            echo "- No task directory found"
        fi
        echo ""

        echo "## Inbox Messages"
        if [[ -d "$team_dir/inboxes" ]]; then
            for f in "$team_dir/inboxes"/*.json; do
                [[ -f "$f" ]] || continue
                echo "### $(basename "$f" .json)"
                python3 -c "
import json
with open('$f') as fh:
    msgs = json.load(fh)
for m in msgs:
    ts = m.get('timestamp', '?')
    sender = m.get('from', '?')
    summary = m.get('summary', m.get('text', '')[:120])
    print(f'- [{ts}] from {sender}: {summary}')
" 2>/dev/null || echo "- (could not parse)"
            done
        else
            echo "- No inbox messages"
        fi
        echo ""

        echo "## Log Tail (last 50 lines)"
        echo '```'
        tail -50 "$LOG_FILE" 2>/dev/null
        echo '```'
    } > "$postmortem"

    log "Post-mortem written to $postmortem"
}

# ── Cleanup trap ────────────────────────────────────────────────────────────
cleanup() {
    local exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
        log_error "Script exited with code $exit_code"
        write_postmortem "$exit_code" 2>/dev/null || true
        track_run "FAILED" "exit_code=$exit_code" 2>/dev/null || true
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

# ── Stale team cleanup ──────────────────────────────────────────────────────
cleanup_stale_teams() {
    local stale_teams stale_tasks
    stale_teams=$(find "$HOME/.claude/teams" -maxdepth 1 -name "morning-brief-*" -type d 2>/dev/null || true)
    stale_tasks=$(find "$HOME/.claude/tasks" -maxdepth 1 -name "morning-brief-*" -type d 2>/dev/null || true)

    if [[ -n "$stale_teams" || -n "$stale_tasks" ]]; then
        log "Cleaning up stale team/task artifacts from previous runs..."
        for dir in $stale_teams; do
            log "  Removing stale team: $(basename "$dir")"
            rm -rf "$dir"
        done
        for dir in $stale_tasks; do
            log "  Removing stale tasks: $(basename "$dir")"
            rm -rf "$dir"
        done
    fi
}

# ── Failure alert ────────────────────────────────────────────────────────────
send_failure_alert() {
    local reason="$1"
    local log_tail=""
    local postmortem_content=""

    if [[ -f "$LOG_FILE" ]]; then
        log_tail=$(tail -50 "$LOG_FILE" | sed 's/&/\&amp;/g; s/</\&lt;/g; s/>/\&gt;/g')
    fi

    local postmortem_file="$LOG_DIR/postmortem-${TARGET_DATE}.md"
    if [[ -f "$postmortem_file" ]]; then
        postmortem_content=$(cat "$postmortem_file" | sed 's/&/\&amp;/g; s/</\&lt;/g; s/>/\&gt;/g')
    fi

    local alert_html
    alert_html=$(cat <<EOF
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"/></head>
<body style="background-color:#0a0f1a;color:#fdf6ec;font-family:sans-serif;padding:24px;">
<h1 style="color:#ef4444;">Morning Brief Failed — $TARGET_DATE</h1>
<p><strong>Reason:</strong> $reason</p>
<h2 style="color:#f4a261;">Post-Mortem</h2>
<pre style="background:#12192e;border:1px solid rgba(232,184,125,0.18);padding:16px;overflow-x:auto;font-size:13px;color:#c9d6df;border-radius:12px;">$postmortem_content</pre>
<h2 style="color:#f4a261;">Last 50 Log Lines</h2>
<pre style="background:#12192e;border:1px solid rgba(232,184,125,0.18);padding:16px;overflow-x:auto;font-size:13px;color:#c9d6df;border-radius:12px;">$log_tail</pre>
</body>
</html>
EOF
    )

    local subject_tag="FAILED"
    if [[ "$reason" == *"auth"* ]]; then
        subject_tag="AUTH"
    fi

    if command -v msmtp &>/dev/null; then
        echo "$alert_html" | {
            echo "From: morning-brief@$(hostname)"
            echo "To: $EMAIL_TO"
            echo "Subject: [$subject_tag] Morning Brief — $TARGET_DATE"
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
# Single Claude invocation — reads pre-collected briefing file + thesis files.
# No web searching. No agent teams. Data comes from collect-market-data.py.
build_research_prompt() {
    local briefing_file="$BRIEFING_DIR/briefing-${TARGET_DATE}.md"
    cat <<PROMPT_EOF
Write the BigPic Morning Brief for $DAY_FULL, $TARGET_DATE. Output to $MONTH_DIR/$OUTPUT_MD

DATA SOURCE: All market data has been pre-collected and verified. Read these files:

1. BRIEFING FILE (primary data source):
   $briefing_file

2. SECTOR THESIS FILES (for watchlist context and catalyst timelines):
$THESIS_LIST

CRITICAL RULES:
- Do NOT use WebSearch. All data you need is in the briefing file.
- If data is missing from the briefing file, write "[Data unavailable]" — do NOT guess or fabricate.
- If the Economic Calendar shows Actual = "—", the release has NOT happened yet.
  Write "Pending" or "Scheduled for [time]" — NEVER fabricate an actual value.
- If Earnings shows EPS Actual = "—", results have NOT been reported. Do NOT fabricate results.
- Every number in your report must come from the briefing file. Include the source attribution.

REPORT STRUCTURE:

## Event Load: [LIGHT|MEDIUM|HEAVY] — $DAY_FULL, $DAY_DISPLAY
(Use the Event Load from the briefing file header. Calibrate depth accordingly.)

## Pre-Market Snapshot
(Table from briefing file — futures, VIX, yields, DXY, commodities, crypto. Add brief color.)

## Overnight & Global Markets
(Asia session recap, Europe session recap from Global Markets table. Note any notable moves.)

## Today's Calendar
(Economic releases table. For unreleased data: "Scheduled [time] — Consensus: X, Prior: Y")

## Pre-Market Movers
(From Market Movers section. Flag any watchlist tickers that appear.)

## Thesis Watchlist Update
- Earnings reporting today (from Earnings Calendar)
- Notable Tier 1 moves (flag any with change > 3% or RSI extremes from technicals)
- Approaching catalysts (cross-reference thesis files for upcoming dates)
- Key technical levels (from briefing file if available)

## Market Context & Playbook
- VIX regime + trend assessment (from Market Context section)
- Today's bias (bullish/bearish/neutral) with rationale from the data
- Key levels to watch (from pre-market snapshot)
- Risk factors

## Sector Snapshot
(One-line summary per sector based on Tier 1 moves from watchlist table)

## News Highlights
(Top 3-5 headlines from each RSS category that are market-relevant. Skip noise.)

## Sources
List: "Data collected at [time] via BigPic automated pipeline. Sources: Schwab API,
CoinGecko, Stooq, FRED, RSS feeds. Completeness: [score from briefing header]."

DEPTH CALIBRATION:
- LIGHT: ~800-1200 words. Quick snapshot, no scenario analysis.
- MEDIUM: ~1500-2000 words. More detail on key events and watchlist.
- HEAVY: ~2500-3000 words. Full scenario analysis, detailed playbook, all sections expanded.
PROMPT_EOF
}

# ── OLD research prompt (agent team version) — kept for rollback ─────────────
# To revert: rename build_research_prompt_v2 → build_research_prompt
#            uncomment CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS export
#            change TIMEOUT_RESEARCH back to 2400
build_research_prompt_v2() {
    local team_suffix="${1:-$TARGET_DATE}"
    cat <<'OLD_PROMPT_EOF'
# [ARCHIVED] Agent team research prompt — replaced by briefing-file approach
# See git history for full content
OLD_PROMPT_EOF
}

# ── Build HTML prompt (Invocation 2) ─────────────────────────────────────────
# Fresh context — only reads the compiled markdown and generates HTML + publishes.
build_html_prompt() {
    cat <<PROMPT_EOF
Generate the HTML report and publish for $DAY_FULL, $TARGET_DATE.

STEP 1 — READ: Read the compiled markdown at $MONTH_DIR/$OUTPUT_MD

STEP 2 — HTML BUILD: Generate $MONTH_DIR/$OUTPUT_HTML from that markdown.
Match the BigPic Solutions site theme exactly:
- Background: #0a0f1a (deep navy), cards: rgba(18, 26, 46, 0.88)
- Accent gold: #e8b87d, amber: #f4a261, coral: #ef8354
- Text: #fdf6ec (primary), #c9d6df (secondary), #6b7d8e (muted)
- Borders: rgba(232,184,125,0.08) subtle, rgba(232,184,125,0.18) glow
- Fonts: Space Grotesk (sans), Newsreader (serif/accent)
- Green #22c55e for positive, Red #ef4444 for negative
- Radius: 12px cards, 20px large sections
Sections to include:
- Fixed nav bar with back-arrow link to ../../morning-brief/index.html (Morning Brief archive) and section anchors
- Hero: date, event load badge (green LIGHT / amber MEDIUM / red HEAVY), brief title
- Pre-market snapshot: color-coded grid (green up, red down)
- Overnight/Global: compact card layout
- Today's calendar: table with time, release, consensus, prior, significance
- Thesis watchlist: earnings table, key levels, pre-market movers (color-coded deltas)
- Approaching catalysts: timeline with priority color-coding
- Scenario analysis: only if HEAVY day — tabbed or card layout per scenario
- Today's playbook: bias card with watch-for and risk bullet points
- Collapsible sources section
- Footer with date and compilation note
Use scroll-reveal animations, hover effects on cards, and backdrop-filter: blur(20px).
Keep it lightweight — the daily brief should load fast and be scannable.

STEP 3 — PUBLISH: Add a new entry to $BRIEF_DIR/index.html for this brief.
The archive page has entries between <!-- ARCHIVE_ENTRIES_START --> and <!-- ARCHIVE_ENTRIES_END -->.
Entries are grouped by month (class="month-group"). If the current month group already exists,
add the new entry at the top of that group. Otherwise create a new month-group div before
existing groups. Move the "Latest" badge from any previous entry to the new one.
Use this HTML format for the entry:
<a href="$MONTH/$OUTPUT_HTML" class="report-entry">
  <div class="info">
    <span class="day">$DAY_FULL, $DAY_DISPLAY</span>
    <span class="meta">[1-line summary from the brief's event load / key events]</span>
  </div>
  <span class="load [heavy|medium|light]">[Heavy|Medium|Light]</span>
  <span class="badge">Latest</span>
  <span class="arrow">&rarr;</span>
</a>
Then commit and push:
cd $REPO_DIR && git add -A && git commit -m "Morning Brief — $DAY_FULL $TARGET_DATE" && git push
PROMPT_EOF
}

# ── Run Claude with timeout (non-exit version) ──────────────────────────────
# Usage: run_claude <phase_name> <timeout_seconds> <prompt>
# Returns: 0 on success, non-zero on failure (does NOT exit the script)
run_claude() {
    local phase_name="$1"
    local timeout_secs="$2"
    local prompt="$3"

    log "Running Claude [$phase_name] (timeout: ${timeout_secs}s)..."

    # Run Claude directly — output is appended to log file.
    # Note: script(1) PTY wrapper was removed — it gets suspended (state T)
    # in gnome-terminal contexts (cron + interactive). Direct execution works.
    local prompt_file
    prompt_file=$(mktemp /tmp/morning-brief-prompt-XXXXXX.txt)
    printf '%s' "$prompt" > "$prompt_file"

    set +e
    timeout --kill-after=30 "$timeout_secs" \
        "$CLAUDE_BIN" --model opus -p "$(cat "$prompt_file")" --dangerously-skip-permissions \
        >> "$LOG_FILE" 2>&1
    local claude_exit=$?
    set -e

    rm -f "$prompt_file"

    if [[ $claude_exit -eq 124 ]]; then
        log_error "Claude [$phase_name] timed out (SIGTERM) after ${timeout_secs}s"
        return 1
    elif [[ $claude_exit -eq 137 ]]; then
        log_error "Claude [$phase_name] timed out (SIGKILL) after $((timeout_secs + 30))s — process ignored SIGTERM"
        return 1
    elif [[ $claude_exit -ne 0 ]]; then
        log_error "Claude [$phase_name] exited with code $claude_exit"
        return 1
    fi

    log "Claude [$phase_name] finished successfully"
    return 0
}

# ── Main ─────────────────────────────────────────────────────────────────────
main() {
    log "=== Morning Brief Started ==="
    log "Date: $DAY_FULL, $TARGET_DATE"
    log "Output: morning-brief/$MONTH/$OUTPUT_MD + $OUTPUT_HTML"

    # Check dependencies
    check_deps
    log "All dependencies verified"

    # Clean up stale team/task artifacts from any previous failed runs
    cleanup_stale_teams

    # Skip if already generated today (check HTML — MD alone means a partial run)
    if [[ -f "$MONTH_DIR/$OUTPUT_HTML" ]]; then
        log "Brief already exists for $TARGET_DATE — skipping"
        exit 0
    fi

    # ── Step 1: Collect market data ──────────────────────────────────────────
    local briefing_file="$BRIEFING_DIR/briefing-${TARGET_DATE}.md"
    if [[ ! -f "$briefing_file" ]]; then
        log "Running data collection pipeline..."
        set +e
        python3 "$COLLECT_SCRIPT" --date "$TARGET_DATE" 2>&1 | tee -a "$LOG_FILE"
        local collect_rc=${PIPESTATUS[0]}
        set -e

        if [[ $collect_rc -eq 2 ]]; then
            local fail_line
            fail_line=$(grep -E "PIPELINE FAILED at" "$LOG_FILE" | tail -1 || true)
            if [[ "$fail_line" == *"auth"* ]]; then
                log_error "Data collection FAILED — claude CLI auth expired (run \`claude /login\` on host)"
                send_failure_alert "claude CLI auth expired — run \`claude /login\` on host and re-run" || true
            elif [[ -n "$fail_line" ]]; then
                local reason_msg="${fail_line#*PIPELINE FAILED at }"
                log_error "Data collection FAILED — ${reason_msg}"
                send_failure_alert "Data collection failed — ${reason_msg}" || true
            else
                log_error "Data collection FAILED (critical data missing)"
                send_failure_alert "Data collection failed — critical sources unreachable" || true
            fi
            exit 1
        elif [[ $collect_rc -eq 1 ]]; then
            log "Data collection PARTIAL — some sources failed, proceeding with available data"
        else
            log "Data collection complete — briefing file ready"
        fi

        if [[ ! -f "$briefing_file" ]]; then
            log_error "Briefing file not created at $briefing_file"
            send_failure_alert "Data collection completed but no briefing file generated" || true
            exit 1
        fi
    else
        log "Briefing file already exists — skipping data collection"
    fi

    # ── Step 2: Claude writes the morning brief (reads briefing file) ──────
    if [[ ! -f "$MONTH_DIR/$OUTPUT_MD" ]]; then
        discover_theses
        log "Found $THESIS_COUNT research files (sector theses + structural calendar)"

        local attempt=1
        local research_success=0

        while [[ $attempt -le $MAX_RESEARCH_ATTEMPTS && $research_success -eq 0 ]]; do
            if [[ $attempt -gt 1 ]]; then
                log "=== Report writing retry $attempt ==="
            fi

            set +e
            run_claude "report (attempt $attempt)" "$TIMEOUT_RESEARCH" "$(build_research_prompt)"
            local rc=$?
            set -e

            if [[ $rc -eq 0 && -f "$MONTH_DIR/$OUTPUT_MD" ]]; then
                local md_size
                md_size=$(stat -c%s "$MONTH_DIR/$OUTPUT_MD")
                if [[ $md_size -ge 500 ]]; then
                    research_success=1
                    log "Report attempt $attempt succeeded: $md_size bytes"
                else
                    log_error "Report attempt $attempt produced undersized output ($md_size bytes)"
                fi
            else
                log_error "Report attempt $attempt failed (rc=$rc, md exists=$([ -f "$MONTH_DIR/$OUTPUT_MD" ] && echo yes || echo no))"
            fi

            attempt=$((attempt + 1))
        done

        if [[ $research_success -eq 0 ]]; then
            send_failure_alert "Report writing failed after $MAX_RESEARCH_ATTEMPTS attempts" || true
            exit 1
        fi
    else
        log "Markdown already exists — skipping report writing"
    fi

    # ── Schwab fact-check: correct any hallucinated prices/moves ─────────────
    log "Running Schwab fact-check verification..."
    python3 "$REPO_DIR/scripts/verify-brief.py" "$MONTH_DIR/$OUTPUT_MD" 2>&1 | tee -a "$LOG_FILE" || true

    # ── Invocation 2: HTML Build + Publish ───────────────────────────────────
    set +e
    run_claude "html-publish" "$TIMEOUT_HTML" "$(build_html_prompt)"
    local html_rc=$?
    set -e

    if [[ $html_rc -ne 0 ]]; then
        send_failure_alert "Claude [html-publish] failed (rc=$html_rc)" || true
        exit 1
    fi

    # Verify HTML was created
    if [[ ! -f "$MONTH_DIR/$OUTPUT_HTML" ]]; then
        log_error "HTML file not found at $MONTH_DIR/$OUTPUT_HTML"
        send_failure_alert "HTML file was not created by Claude [html-publish]" || true
        exit 1
    fi

    local html_size
    html_size=$(stat -c%s "$MONTH_DIR/$OUTPUT_HTML")
    log "HTML generated: $html_size bytes"

    if [[ $html_size -lt 2000 ]]; then
        log_error "HTML too small ($html_size bytes), may be incomplete"
        send_failure_alert "HTML generated but suspiciously small ($html_size bytes)" || true
        exit 1
    fi

    log "=== Morning Brief Complete ==="
    log "Published: markets.bigpicsolutions.com/morning-brief/$MONTH/$OUTPUT_HTML"
    track_run "SUCCESS"
    exit 0
}

main "$@"

#!/usr/bin/env python3
"""Stamp verified economic calendar data into EAGLE_EYE.md.

Replaces LLM-generated calendar tables in the Week Ahead section with
deterministic data from next_week_calendar.md. Preserves LLM commentary,
earnings, and other non-calendar content.

Usage:
    python3 stamp-calendar.py --report EAGLE_EYE.md --calendar next_week_calendar.md

Exit codes:
    0 — Success (calendar stamped)
    1 — Fatal error (missing files, no Week Ahead section found)
"""

import argparse
import re
import sys
from pathlib import Path


# ── Parse calendar file ──────────────────────────────────────────────────────

def parse_calendar(text):
    """Parse next_week_calendar.md into day tables and absences.

    Returns:
        days: dict of {day_header: [table_lines]} where day_header is e.g. "Monday, March 30"
        absences: list of absence strings, or None if no absences section
    """
    days = {}
    absences = None

    current_day = None
    current_table = []
    in_absences = False

    for line in text.split("\n"):
        # Day header: ## Monday, March 30
        day_match = re.match(r"^##\s+((?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s+.+)", line)
        if day_match:
            # FIX 2026-05-01: Save day even with empty table (no-events days
            # like "Monday, Apr 27 - No major economic events scheduled" must
            # still register so cal_lookup includes them. Was: "if current_day and current_table".
            if current_day:
                days[current_day] = current_table
            current_day = day_match.group(1).strip()
            current_table = []
            in_absences = False
            continue

        # Notable Absences section
        if re.match(r"^##\s+NOTABLE ABSENCES", line, re.IGNORECASE):
            if current_day:
                days[current_day] = current_table
                current_day = None
                current_table = []
            in_absences = True
            absences = []
            continue

        # Data source notes — stop parsing
        if re.match(r"^##\s+DATA SOURCE", line, re.IGNORECASE):
            break

        if in_absences:
            # Absence items: "- CPI Report"
            absence_match = re.match(r"^-\s+(.+)", line)
            if absence_match:
                absences.append(absence_match.group(1).strip())
        elif current_day:
            # Table rows (header, separator, data)
            if line.strip().startswith("|"):
                current_table.append(line)

    # Save last day
    if current_day:
        days[current_day] = current_table

    return days, absences


def format_table_for_report(table_lines):
    """Format calendar table lines for the report.

    Bolds high-impact event names and impact labels to match report style.
    """
    formatted = []
    for line in table_lines:
        # Skip header and separator rows
        if "Event" in line and "Impact" in line and "Time" in line:
            formatted.append(line)
            continue
        if re.match(r"^\|[\s\-|]+$", line):
            formatted.append(line)
            continue

        # Parse table row: | time | event | impact |
        cells = [c.strip() for c in line.split("|")]
        # Split by | gives: ['', 'time', 'event', 'impact', '']
        if len(cells) >= 4:
            time_val = cells[1].strip()
            event_val = cells[2].strip()
            impact_val = cells[3].strip()

            # Bold high/medium impact events
            impact_lower = impact_val.lower().strip("* ")
            if impact_lower == "high":
                event_val = f"**{event_val.strip('* ')}**"
                impact_val = "**High**"
            elif impact_lower == "medium":
                event_val = f"**{event_val.strip('* ')}**"
                impact_val = "**Medium**"

            formatted.append(f"| {time_val} | {event_val} | {impact_val} |")
        else:
            formatted.append(line)

    return formatted


# ── Parse EAGLE_EYE.md Week Ahead section ────────────────────────────────────

def parse_week_ahead(text):
    """Parse the Week Ahead section from EAGLE_EYE.md.

    Returns:
        before: text before the Week Ahead section
        header: the "## The Week Ahead ..." line
        preamble: lines between header and first day (italics, notes)
        day_blocks: list of (day_header_line, commentary_lines) — commentary only, tables stripped
        subsections: list of (header_line, content_lines) for Earnings, etc.
        after: text after the Week Ahead section (from --- or next ## onward)
    """
    lines = text.split("\n")

    # Find Week Ahead section boundaries
    wa_start = None
    wa_end = None
    for i, line in enumerate(lines):
        if re.match(r"^##\s+The Week Ahead", line) and wa_start is None:
            wa_start = i
        elif wa_start is not None and re.match(r"^##\s+(?!#)", line) and i > wa_start:
            wa_end = i
            break
        elif wa_start is not None and line.strip() == "---" and i > wa_start + 2:
            wa_end = i
            break

    if wa_start is None:
        return None

    if wa_end is None:
        wa_end = len(lines)

    before = "\n".join(lines[:wa_start])
    header = lines[wa_start]
    after = "\n".join(lines[wa_end:])

    # Parse section content
    section_lines = lines[wa_start + 1:wa_end]

    preamble = []
    day_blocks = []       # [(header_line, [commentary_lines])]
    subsections = []      # [(header_line, [content_lines])]
    current_day_header = None
    current_lines = []
    in_table = False
    in_subsection = False
    current_sub_header = None
    current_sub_lines = []

    # Day header pattern: ### Monday, March 30 (optionally with extra text like "(Markets Closed...)")
    day_pattern = re.compile(
        r"^###\s+(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)"
    )
    # Non-day subsection: ### Earnings, ### Notable Absences, ### Structural, etc.
    subsection_pattern = re.compile(
        r"^###\s+(?!Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)"
    )

    for line in section_lines:
        if day_pattern.match(line):
            # Save previous day block
            if current_day_header:
                day_blocks.append((current_day_header, current_lines))
            # Save previous subsection
            if in_subsection and current_sub_header:
                subsections.append((current_sub_header, current_sub_lines))
                in_subsection = False

            current_day_header = line
            current_lines = []
            in_table = False
            continue

        if subsection_pattern.match(line):
            # Save previous day block
            if current_day_header:
                day_blocks.append((current_day_header, current_lines))
                current_day_header = None
                current_lines = []
            # Save previous subsection
            if in_subsection and current_sub_header:
                subsections.append((current_sub_header, current_sub_lines))

            in_subsection = True
            current_sub_header = line
            current_sub_lines = []
            continue

        if in_subsection:
            current_sub_lines.append(line)
            continue

        if current_day_header is None:
            # Before any day header = preamble
            preamble.append(line)
            continue

        # Inside a day block — separate tables from commentary
        if line.strip().startswith("|"):
            in_table = True
            continue  # Strip table lines — they'll be replaced
        elif in_table and line.strip() == "":
            in_table = False
            continue  # Strip blank line after table
        else:
            in_table = False
            current_lines.append(line)

    # Save final blocks
    if current_day_header:
        day_blocks.append((current_day_header, current_lines))
    if in_subsection and current_sub_header:
        subsections.append((current_sub_header, current_sub_lines))

    return before, header, preamble, day_blocks, subsections, after


def normalize_day_name(header_line):
    """Extract the day name from a header line for matching.

    '### Monday, March 30' → 'Monday'
    '### Friday, April 3 (Markets Closed — Good Friday)' → 'Friday'
    'Monday, March 30' → 'Monday'
    """
    match = re.search(
        r"(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)",
        header_line, re.IGNORECASE,
    )
    return match.group(1) if match else None


# ── Stamp ────────────────────────────────────────────────────────────────────

def stamp(report_text, calendar_text):
    """Stamp calendar data into the report's Week Ahead section."""

    cal_days, cal_absences = parse_calendar(calendar_text)
    parsed = parse_week_ahead(report_text)

    if parsed is None:
        print("ERROR: No '## The Week Ahead' section found in report", file=sys.stderr)
        return None

    before, header, preamble, day_blocks, subsections, after = parsed

    # Build day name → calendar table lookup
    cal_lookup = {}
    for cal_header, table_lines in cal_days.items():
        day_name = normalize_day_name(cal_header)
        if day_name:
            cal_lookup[day_name] = (cal_header, table_lines)

    # Reconstruct the Week Ahead section
    result_lines = []
    result_lines.append(header)

    # Preamble (holiday notes, source attribution, etc.)
    for line in preamble:
        result_lines.append(line)

    # Day blocks: inject calendar table + preserve commentary
    for day_header, commentary in day_blocks:
        day_name = normalize_day_name(day_header)

        result_lines.append("")
        # FIX 2026-05-01: Override LLM-generated day header with calendar-authoritative
        # day name + date. Claude has historically computed wrong day-of-week from date
        # (e.g., Eagle Eye W17 had every day off by +1: Mon Apr 28 instead of Tue Apr 28).
        # The calendar file is the source of truth for both day name AND date.
        # Trailing parentheticals like "(FOMC Day)" are preserved if present.
        if day_name and day_name in cal_lookup:
            cal_header_auth, _ = cal_lookup[day_name]
            trailing_match = re.search(r"(\([^)]+\))", day_header)
            trailing = " " + trailing_match.group(1) if trailing_match else ""
            result_lines.append(f"### {cal_header_auth}{trailing}")
        else:
            result_lines.append(day_header)

        # Inject calendar table
        if day_name and day_name in cal_lookup:
            cal_header, table_lines = cal_lookup[day_name]
            formatted = format_table_for_report(table_lines)
            for tline in formatted:
                result_lines.append(tline)
            result_lines.append("")
        else:
            result_lines.append("No major economic releases scheduled.")
            result_lines.append("")

        # Preserve LLM commentary (strip leading/trailing blank lines)
        stripped = []
        for line in commentary:
            stripped.append(line)
        # Remove leading blank lines
        while stripped and stripped[0].strip() == "":
            stripped.pop(0)
        # Remove trailing blank lines
        while stripped and stripped[-1].strip() == "":
            stripped.pop()
        for line in stripped:
            result_lines.append(line)

    # Calendar days not in the report (add them)
    report_day_names = {normalize_day_name(h) for h, _ in day_blocks}
    for day_name in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
        if day_name in cal_lookup and day_name not in report_day_names:
            cal_header, table_lines = cal_lookup[day_name]
            result_lines.append("")
            result_lines.append(f"### {cal_header}")
            formatted = format_table_for_report(table_lines)
            for tline in formatted:
                result_lines.append(tline)

    # Non-calendar subsections (Earnings, Structural Calendar, etc.)
    for sub_header, sub_content in subsections:
        # Replace Notable Absences with calendar version
        if "notable absences" in sub_header.lower():
            continue  # Will be added from calendar below
        result_lines.append("")
        result_lines.append(sub_header)
        for line in sub_content:
            result_lines.append(line)

    # Stamp Notable Absences from calendar
    if cal_absences:
        result_lines.append("")
        result_lines.append("### Notable Absences")
        result_lines.append("Per the verified economic calendar, these major releases are **NOT** scheduled this week:")
        for absence in cal_absences:
            result_lines.append(f"- {absence}")

    result_lines.append("")

    # Reassemble full document
    new_week_ahead = "\n".join(result_lines)
    return f"{before}\n{new_week_ahead}\n{after}"


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Stamp calendar into Eagle Eye report")
    parser.add_argument("--report", required=True, help="Path to EAGLE_EYE.md")
    parser.add_argument("--calendar", required=True, help="Path to next_week_calendar.md")
    args = parser.parse_args()

    report_path = Path(args.report)
    calendar_path = Path(args.calendar)

    if not report_path.exists():
        print(f"ERROR: Report not found: {report_path}", file=sys.stderr)
        sys.exit(1)
    if not calendar_path.exists():
        print(f"ERROR: Calendar not found: {calendar_path}", file=sys.stderr)
        sys.exit(1)

    report_text = report_path.read_text()
    calendar_text = calendar_path.read_text()

    result = stamp(report_text, calendar_text)
    if result is None:
        sys.exit(1)

    report_path.write_text(result)

    # Summary
    cal_days, cal_absences = parse_calendar(calendar_text)
    print(f"STAMPED: {len(cal_days)} days, {len(cal_absences or [])} absences injected into Week Ahead")


if __name__ == "__main__":
    main()

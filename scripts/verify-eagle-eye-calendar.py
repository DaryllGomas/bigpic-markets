#!/usr/bin/env python3
"""
verify-eagle-eye-calendar.py — Post-stamp sanity check for Week Ahead.

Verifies that stamp-calendar.py successfully injected calendar data into
EAGLE_EYE.md. Simple exact-string checks — no keyword extraction or fuzzy
matching.

Always exits 0. Writes findings to VERIFICATION.md for human review.

Usage:
    python3 verify-eagle-eye-calendar.py \
        --report /path/to/EAGLE_EYE.md \
        --calendar /path/to/next_week_calendar.md

Exit codes:
    0 — Always (findings logged, never fatal)
"""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path


def parse_calendar_days(text):
    """Parse calendar file into day names and high-impact event names."""
    days = {}
    absences = []
    current_day = None
    in_absences = False

    for line in text.split("\n"):
        line_stripped = line.strip()

        day_match = re.match(
            r"^##\s+(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)",
            line_stripped, re.IGNORECASE,
        )
        if day_match:
            current_day = day_match.group(1)
            days.setdefault(current_day, [])
            in_absences = False
            continue

        if re.match(r"^##\s+NOTABLE ABSENCES", line_stripped, re.IGNORECASE):
            in_absences = True
            current_day = None
            continue

        if line_stripped.startswith("## "):
            in_absences = False
            current_day = None
            continue

        # Table rows: | time | event | impact |
        if current_day and line_stripped.startswith("|"):
            cols = [c.strip() for c in line_stripped.split("|")[1:-1]]
            if len(cols) >= 3 and cols[1] and cols[1] not in ("Event", "---"):
                impact = cols[2].lower().strip()
                if impact in ("high", "medium"):
                    days[current_day].append(cols[1])

        if in_absences and line_stripped.startswith("- "):
            absences.append(line_stripped[2:].strip())

    return days, absences


def extract_week_ahead(text):
    """Extract the Week Ahead section text from EAGLE_EYE.md."""
    match = re.search(
        r"(## The Week Ahead.*?)(?=\n## [^#]|\Z)",
        text, re.DOTALL | re.IGNORECASE,
    )
    return match.group(1) if match else None


def check_day_date_consistency(week_ahead_text, current_year):
    """Verify each '### Monday, April 27'-style header has day-of-week matching the date.

    Returns a list of findings (empty if all pass). Catches the W17 off-by-one bug
    where Claude wrote '### Monday, April 28' (April 28 was actually Tuesday).

    FIX 2026-05-01: Added in response to Eagle Eye W17 incident where every day in
    the Week Ahead was labeled +1 day off (Mon Apr 28 instead of Tue Apr 28, etc.).
    """
    findings = []
    pattern = re.compile(
        r"^###\s+(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s+([A-Z][a-z]+)\s+(\d{1,2})",
        re.MULTILINE,
    )

    month_names = {
        "January": 1, "February": 2, "March": 3, "April": 4,
        "May": 5, "June": 6, "July": 7, "August": 8,
        "September": 9, "October": 10, "November": 11, "December": 12,
    }
    weekday_names = [
        "Monday", "Tuesday", "Wednesday", "Thursday",
        "Friday", "Saturday", "Sunday",
    ]

    for match in pattern.finditer(week_ahead_text):
        labeled_day, month_str, day_str = match.group(1), match.group(2), match.group(3)
        month_num = month_names.get(month_str)
        if not month_num:
            continue
        try:
            actual_dt = datetime(current_year, month_num, int(day_str))
        except ValueError:
            findings.append(
                f"INVALID DATE: '{labeled_day}, {month_str} {day_str}' is not a real date"
            )
            continue
        actual_day = weekday_names[actual_dt.weekday()]
        if labeled_day != actual_day:
            findings.append(
                f"DAY/DATE MISMATCH: header says '{labeled_day}, {month_str} {day_str}' "
                f"but {month_str} {day_str}, {current_year} is actually a {actual_day}"
            )

    return findings


def verify(report_text, calendar_text):
    """Run sanity checks. Returns (status, findings)."""
    findings = []

    week_ahead = extract_week_ahead(report_text)
    if not week_ahead:
        findings.append("FAIL: No '## The Week Ahead' section found in report")
        return "FAIL", findings

    cal_days, cal_absences = parse_calendar_days(calendar_text)

    # Check 1: Each calendar day has a header in the report
    for day_name in cal_days:
        if day_name.lower() not in week_ahead.lower():
            findings.append(f"MISSING DAY: {day_name} not found in Week Ahead section")

    # Check 2: Each high-impact event appears in the report (exact name match)
    for day_name, events in cal_days.items():
        for event in events:
            # Strip any bold markers for the search
            clean_event = event.strip("* ")
            if clean_event not in report_text:
                findings.append(f"MISSING EVENT: '{clean_event}' ({day_name}) not in report")

    # Check 3: Notable Absences section exists if calendar has absences
    if cal_absences and "notable absences" not in week_ahead.lower():
        findings.append("MISSING: Notable Absences section not found")

    # Check 4 (added 2026-05-01): Day-of-week labels match their dates.
    # Catches the W17 off-by-one bug deterministically.
    current_year = datetime.now().year
    day_date_findings = check_day_date_consistency(week_ahead, current_year)
    findings.extend(day_date_findings)

    if findings:
        return "WARN", findings
    return "PASS", []


def write_verification(findings, status, verification_path):
    """Write/update the Week Ahead Calendar Check section in VERIFICATION.md."""
    section = "\n## Week Ahead Calendar Check\n\n"
    if status == "PASS":
        section += "**PASS** — Calendar data stamped and verified.\n"
    else:
        section += f"**{status}** — {len(findings)} findings:\n\n"
        for f in findings:
            section += f"- {f}\n"
    section += "\n"

    if verification_path.exists():
        existing = verification_path.read_text(encoding="utf-8")
        existing = re.sub(
            r"\n## Week Ahead Calendar Check\n.*?(?=\n## |\Z)",
            "", existing, flags=re.DOTALL,
        )
        verification_path.write_text(
            existing.rstrip() + "\n" + section, encoding="utf-8",
        )
    else:
        verification_path.write_text(
            "# Eagle Eye Verification\n" + section, encoding="utf-8",
        )


def main():
    parser = argparse.ArgumentParser(
        description="Post-stamp calendar verification for Eagle Eye")
    parser.add_argument("--report", required=True)
    parser.add_argument("--calendar", required=True)
    parser.add_argument("--verification", default=None)
    args = parser.parse_args()

    report_path = Path(args.report)
    calendar_path = Path(args.calendar)

    if not report_path.exists():
        print(f"WARNING: Report not found: {report_path}", file=sys.stderr)
        sys.exit(0)
    if not calendar_path.exists():
        print(f"WARNING: Calendar not found: {calendar_path}", file=sys.stderr)
        sys.exit(0)

    report_text = report_path.read_text(encoding="utf-8")
    calendar_text = calendar_path.read_text(encoding="utf-8")

    status, findings = verify(report_text, calendar_text)

    if findings:
        print(f"{status}: {len(findings)} findings in Week Ahead:")
        for f in findings:
            print(f"  - {f}")
    else:
        print("PASS: Week Ahead calendar data verified.")

    if args.verification:
        write_verification(findings, status, Path(args.verification))

    # Always exit 0 — this is informational, never kills the pipeline
    sys.exit(0)


if __name__ == "__main__":
    main()

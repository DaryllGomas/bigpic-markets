# Eagle Eye HTML Split — 2-Part Generation

**Date:** 2026-03-08
**Script:** `scripts/run-eagle-eye.sh`
**Problem:** W10 HTML generation timed out at 900s — Claude producing ~80KB+ of themed HTML in one shot was too much.

## Solution

Split the single `[html-publish]` invocation into three sequential calls:

### Call 2a: `[html-build-1]` (timeout: 900s)
- Reads `EAGLE_EYE.md`
- Generates `report.html` with full page skeleton: `<!DOCTYPE>`, `<head>`, all CSS/JS, fixed nav, footer
- Fills in first 5 sections: **scorecard, breaking, take, sectors, rates**
- Leaves `<!-- CONTINUE HERE -->` marker where remaining sections go
- Validated: file must exist and be > 2KB

### Call 2b: `[html-build-2]` (timeout: 900s)
- Reads both `EAGLE_EYE.md` (content) and `report.html` (partial HTML from 2a)
- Replaces `<!-- CONTINUE HERE -->` marker with remaining 6 sections: **watchlist, commodities, crypto, ahead, positioning, sources**
- Validated: file must be > 40KB and marker must be removed

### Call 2c: `[html-publish]` (timeout: 300s)
- Updates `eagle-eye/index.html` archive entry (latest badge)
- `git add -A && git commit && git push`

## Section Split Rationale

| Part | Sections | Expected Size |
|------|----------|---------------|
| Part 1 | Scorecard, Breaking, Take, Sectors, Rates | ~40-50KB |
| Part 2 | Watchlist, Commodities, Crypto, Ahead, Positioning, Sources | ~40-50KB |

Split at the rates/watchlist boundary because:
- Roughly equal content volume on each side
- Scorecard + sectors have the heaviest CSS/JS (counters, heatmap, yield curve SVG)
- Watchlist has complex filterable cards, sources has collapsible sections

## First Run Results (W10, 2026-03-08)

| Step | Duration | Output Size |
|------|----------|-------------|
| `[html-build-1]` | ~5.5 min | 50KB |
| `[html-build-2]` | ~5.5 min | 100KB |
| `[html-publish]` | ~40 sec | — |
| **Total** | **~12 min** | **100KB** |

No timeouts. All validations passed. Previously timed out at 900s in a single call.

## Validation Gates

1. After Part 1: `report.html` exists and > 2KB (catches empty/failed writes)
2. After Part 2: `report.html` > 40KB (catches truncated output)
3. After Part 2: `<!-- CONTINUE HERE -->` marker absent (confirms sections were inserted)
4. Each step: fail-fast with email alert on any failure

## Functions Changed

| Old | New |
|-----|-----|
| `build_html_prompt()` | `build_html_part1_prompt()` |
| | `build_html_part2_prompt()` |
| | `build_publish_prompt()` |
| `TIMEOUT_HTML=900` | `TIMEOUT_HTML_1=900` |
| | `TIMEOUT_HTML_2=900` |
| | `TIMEOUT_PUBLISH=300` |

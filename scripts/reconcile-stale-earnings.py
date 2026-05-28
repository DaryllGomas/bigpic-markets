#!/usr/bin/env python3
"""
reconcile-stale-earnings.py — Calendar hygiene guard for the Morning Brief pipeline.

Prevents the recurring failure where a hand-curated (source='manual') earnings
event in economic_events is left on a stale/wrong date after a company's actual
report date moves. Example caught 2026-05-27: "NVDA: Q1 FY2027 Earnings" was
hand-seeded on 2026-05-27, but NVDA actually printed 2026-05-20. The morning brief
reads economic_events WHERE market_date = today, so the stale row made the brief
announce an earnings event that had already happened a week earlier.

The `earnings` table (Schwab next_earnings) is the authoritative source for report
dates. For the target date this guard deletes any manual earnings event that the
earnings table POSITIVELY contradicts, requiring ALL of:
  - source = 'manual'
  - event_name contains 'Earnings'
  - ticker (text before the first ':') is a KNOWN symbol in the earnings table
  - that ticker has NO earnings row with report_date = target date

Because the ticker must be a bare known symbol, strategy rows like
"AAPL ENTRY: Q2 FY26 Earnings (T-14)" (ticker parses to "AAPL ENTRY", not a symbol)
and non-earnings catalysts (GTC / I/O / OpEx / WWDC) are never touched. It also
never deletes when the earnings table lacks info for the ticker (errs toward keep).

Conservative, idempotent, non-fatal (always exits 0 so it can never break the cron).
"""
import argparse
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

DEFAULT_DB = Path(__file__).resolve().parent.parent / "data" / "market.db"


def today_et():
    return datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d")


def find_stale(conn, target_date):
    sql = """
        SELECT e.id, e.event_name, e.market_date
        FROM economic_events e
        WHERE e.market_date = ?
          AND e.source = 'manual'
          AND e.event_name LIKE '%Earnings%'
          AND instr(e.event_name, ':') > 0
          AND trim(substr(e.event_name, 1, instr(e.event_name, ':') - 1)) IN (
                SELECT DISTINCT symbol FROM earnings)
          AND trim(substr(e.event_name, 1, instr(e.event_name, ':') - 1)) NOT IN (
                SELECT symbol FROM earnings WHERE report_date = ?)
    """
    return conn.execute(sql, (target_date, target_date)).fetchall()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None, help="Target date YYYY-MM-DD (default: today ET)")
    ap.add_argument("--db", default=str(DEFAULT_DB), help="Path to market.db")
    ap.add_argument("--dry-run", action="store_true", help="Report only, delete nothing")
    args = ap.parse_args()

    target_date = args.date or today_et()
    db_path = Path(args.db)

    print(f"[reconcile-stale-earnings] date={target_date} db={db_path} dry_run={args.dry_run}")
    if not db_path.exists():
        print(f"[reconcile-stale-earnings] DB not found, skipping: {db_path}")
        return 0

    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        stale = find_stale(conn, target_date)
        if not stale:
            print("[reconcile-stale-earnings] No stale manual earnings events. OK.")
            conn.close()
            return 0
        for row in stale:
            print(f"[reconcile-stale-earnings] STALE: id={row['id']} "
                  f"\"{row['event_name']}\" (market_date={row['market_date']}) "
                  f"— earnings table shows this ticker is NOT reporting on {target_date}.")
        if args.dry_run:
            print(f"[reconcile-stale-earnings] DRY-RUN — would delete {len(stale)} row(s).")
            conn.close()
            return 0
        ids = [r["id"] for r in stale]
        conn.executemany("DELETE FROM economic_events WHERE id = ?",
                         [(i,) for i in ids])
        conn.commit()
        print(f"[reconcile-stale-earnings] Deleted {len(ids)} stale event(s): {ids}")
        conn.close()
        return 0
    except Exception as exc:  # never break the pipeline
        print(f"[reconcile-stale-earnings] WARNING: guard errored (non-fatal): {exc}")
        return 0


if __name__ == "__main__":
    sys.exit(main())

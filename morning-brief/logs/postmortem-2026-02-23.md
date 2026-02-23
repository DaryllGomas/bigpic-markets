# Post-Mortem: Morning Brief 2026-02-23

**Status:** FAILED (exit code 1)
**Start:** 2026-02-23 05:00:01
**End:** 2026-02-23 05:09:03

## Research Files
- `markets-research.md`: 21888 bytes, last modified 2026-02-12 05:26:09
- `watchlist-research.md`: 21847 bytes, last modified 2026-02-12 05:26:54
- `2026-02-23_Mon.md`: NOT CREATED

## Team Members
- No team config found

## Task Statuses
- No task directory found

## Inbox Messages
- No inbox messages

## Log Tail (last 50 lines)
```
2026-02-23 05:08:50,959 INFO Economic calendar: 2 events
2026-02-23 05:08:51,096 INFO CoinGecko: 2 coins
2026-02-23 05:08:55,200 INFO Stooq: 3/3 symbols
2026-02-23 05:08:55,469 INFO FRED: 1/3 series
2026-02-23 05:08:55,470 INFO Yahoo backup: 0 symbols
2026-02-23 05:08:55,470 INFO Step 3 complete: 453.5s (quotes=149, tech=126, sma200=129, earnings=71, econ=2, crypto=2, stooq=3, fred=1, yahoo=0)
2026-02-23 05:08:55,470 INFO ── Step 4: Validation + Retry ──
2026-02-23 05:08:55,471 INFO ANOMALY: $COMPX price=22886.07 avg=22614.63 z=3.5
2026-02-23 05:08:55,472 INFO ANOMALY: $HSI price=27081.91 avg=26629.78 z=4.1
2026-02-23 05:08:55,473 INFO ANOMALY: $SPX price=6909.51 avg=6846.33 z=3.4
2026-02-23 05:08:55,474 INFO ANOMALY: /GCJ26 price=5185.50 avg=4998.26 z=6.1
2026-02-23 05:08:55,476 INFO ANOMALY: BA price=230.39 avg=240.68 z=-3.1
2026-02-23 05:08:55,476 INFO ANOMALY: BBAI price=3.81 avg=4.09 z=-3.6
2026-02-23 05:08:55,478 INFO ANOMALY: CRWD price=383.96 avg=418.44 z=-4.9
2026-02-23 05:08:55,478 INFO ANOMALY: CRWV price=86.62 avg=95.20 z=-4.8
2026-02-23 05:08:55,479 INFO ANOMALY: ESTC price=57.82 avg=61.09 z=-4.7
2026-02-23 05:08:55,479 INFO ANOMALY: FCX price=64.42 avg=62.28 z=4.4
2026-02-23 05:08:55,480 INFO ANOMALY: GLW price=142.31 avg=131.91 z=9.1
2026-02-23 05:08:55,481 INFO ANOMALY: GOOG price=315.81 avg=305.91 z=3.6
2026-02-23 05:08:55,484 INFO ANOMALY: MP price=54.60 avg=57.82 z=-9.2
2026-02-23 05:08:55,484 INFO ANOMALY: NET price=176.00 avg=191.61 z=-3.8
2026-02-23 05:08:55,485 INFO ANOMALY: OKTA price=74.29 avg=84.67 z=-5.1
2026-02-23 05:08:55,487 INFO ANOMALY: PSN price=67.49 avg=63.56 z=3.1
2026-02-23 05:08:55,487 INFO ANOMALY: QBTS price=17.75 avg=19.08 z=-3.7
2026-02-23 05:08:55,487 INFO ANOMALY: QLYS price=92.00 avg=104.57 z=-18.0
2026-02-23 05:08:55,488 INFO ANOMALY: QUBT price=7.75 avg=8.25 z=-4.1
2026-02-23 05:08:55,488 INFO ANOMALY: RPD price=6.72 avg=7.15 z=-4.4
2026-02-23 05:08:55,489 INFO ANOMALY: SAIL price=14.02 avg=15.72 z=-5.9
2026-02-23 05:08:55,489 INFO ANOMALY: SCCO price=201.50 avg=195.35 z=3.0
2026-02-23 05:08:55,490 INFO ANOMALY: SMR price=13.13 avg=14.35 z=-7.8
2026-02-23 05:08:55,490 INFO ANOMALY: SYM price=53.20 avg=55.14 z=-3.9
2026-02-23 05:08:55,491 INFO ANOMALY: TENB price=20.41 avg=22.46 z=-4.7
2026-02-23 05:08:55,492 INFO ANOMALY: USAR price=16.99 avg=19.00 z=-4.1
2026-02-23 05:08:55,493 INFO ANOMALY: ZS price=159.57 avg=173.36 z=-4.1
2026-02-23 05:08:55,494 INFO Anomaly detection: 27 flagged
2026-02-23 05:08:55,494 INFO Cross-validation: 0 discrepancies
2026-02-23 05:08:55,495 INFO Retry check: 4 failed call(s) found, retrying...
2026-02-23 05:08:55,495 INFO   Retrying technicals for DIA (original error: timed out)
2026-02-23 05:08:56,865 INFO   ✓ DIA technicals recovered
2026-02-23 05:08:56,865 INFO   Retrying technicals for NVDA (original error: timed out)
2026-02-23 05:08:58,553 INFO   ✓ NVDA technicals recovered
2026-02-23 05:08:58,553 INFO   Retrying technicals for HLLGY (original error: HTTP Error 400: Bad Request)
2026-02-23 05:08:59,709 INFO   ✗ HLLGY technicals retry failed: HTTP Error 400: Bad Request
2026-02-23 05:08:59,709 INFO   Retrying technicals for FEZ (original error: timed out)
2026-02-23 05:09:01,107 INFO   ✓ FEZ technicals recovered
2026-02-23 05:09:01,109 INFO Retry complete: 3/4 recovered
2026-02-23 05:09:01,110 ERROR PIPELINE FAILED at Step 4 (Data gaps): 1 symbol(s) still missing technicals after retry: HLLGY
2026-02-23 05:09:02,132 INFO Failure email sent to daryll@bigpicsolutions.com
[2026-02-23 05:09:02] ERROR: Data collection FAILED (critical data missing)
[2026-02-23 05:09:03] ERROR: Script exited with code 1
```

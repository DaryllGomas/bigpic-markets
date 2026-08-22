# Market Structure Calendar — 2026

*Last updated: 2026-02-22*
*Disclaimer: Educational research — not investment advice.*

This calendar tracks recurring structural market events that create tradeable edges. These are events no API provides — they come from our own strategy research. The Morning Brief pipeline reads this file automatically.

---

## Triple Witching + S&P Rebalancing

Triple Witch (stock index futures, index options, and single stock options expire simultaneously) occurs on the 3rd Friday of Mar/Jun/Sep/Dec — the same day as S&P 500 quarterly rebalancing. Combined, these events move $5-6.5T in notional value.

**Strategy**: Long Monday open of witching week → exit Thursday close. Avoid witching Friday (14% win rate since 2021). Avoid the witching hour (3-4 PM, 31% win rate). Expect weakness in the following week.

| Expiration Date | T-9 (Positioning Starts) | T-3 to T-1 (Strongest Edge) | Week After (Bearish) |
|-----------------|--------------------------|------------------------------|----------------------|
| **Mar 20** | Mar 9 (Mon) | Mar 17-19 (Tue-Thu) | Mar 23-27 |
| **Jun 19** | Jun 8 (Mon) | Jun 16-18 (Tue-Thu) | Jun 22-26 |
| **Sep 18** | Sep 7 (Mon) | Sep 15-17 (Tue-Thu) | Sep 21-25 |
| **Dec 18** | Dec 7 (Mon) | Dec 15-17 (Tue-Thu) | Dec 21-24 |

**Key stats**: Pre-expiration rally averages +0.82% (T-9 to T-1). T-3 to T-1 averages +0.47% (134.59% annualized). Sep post-witch week is historically the worst.

**Full research**: `Strategies/TripleWitch.md`

---

## FOMC Meetings

8 scheduled meetings. Rate decision announced Day 2 at 2:00 PM ET. SEP meetings include dot plot and economic projections.

| Meeting Dates | Decision Day | Type | Notes |
|---------------|-------------|------|-------|
| Jan 27-28 | Jan 28 | Regular | **DONE** — Held at 3.50-3.75% (10-2 vote) |
| **Mar 17-18** | Mar 18 | **SEP** | First 2026 dot plot. CME: 60% hold / 38% cut |
| Apr 28-29 | Apr 29 | Regular | |
| **Jun 16-17** | Jun 17 | **SEP** | Coincides with Triple Witch week |
| Jul 28-29 | Jul 29 | Regular | |
| **Sep 15-16** | Sep 16 | **SEP** | Coincides with Triple Witch week |
| Oct 27-28 | Oct 28 | Regular | |
| **Dec 8-9** | Dec 9 | **SEP** | 10 days before Triple Witch |

**Current pricing**: 3 rate cuts (75 bps) priced by year-end. Fed Funds at 3.50-3.75%.

---

## AAPL Buyback Blackout Windows

Corporate buyback blackout begins 35 calendar days before earnings and lifts after the report. During blackout, the corporate bid is removed — creating structural weakness early/mid phase and recovery late phase.

**Strategy**: Verified +12.13% return on Jan 2026 AAPL cycle. See `Strategies/Buyback-Blackout-Earnings-Flow-Strategy.md`.

| Quarter | Expected Earnings | Blackout Start (~35 days prior) | Seasonality |
|---------|-------------------|--------------------------------|-------------|
| Q2 FY26 | ~Apr 30 | ~Mar 26 | Weak (April seasonality) |
| Q3 FY26 | ~Jul 30 | ~Jun 25 | **Strongest** (+3.46% historical) |
| Q4 FY26 | ~Oct 29 | ~Sep 24 | Moderate |
| Q1 FY27 | ~Jan 28 | ~Dec 24 | Moderate-Strong |

*Earnings dates are estimates based on AAPL's historical pattern. Confirm via earnings calendar closer to each date.*

---

## Russell Reconstitution

**NEW in 2026**: Russell US indices move to semi-annual reconstitution (was annual).

| Event | Date | Impact |
|-------|------|--------|
| Annual reconstitution (June) | **Jun 26** (4th Friday) | Full membership review. Historically generates ~$100B in rebalancing flows. |
| Semi-annual reconstitution (December) | **Dec 11** (2nd Friday) | New additions and membership changes. First-ever December reconstitution. Changes reflected at open Mon Dec 14. |

**Full research**: `Cycles/Index-Rebalancing-Calendar-Trading.md`

---

## Monthly Options Expiration (OpEx)

3rd Friday of each month. Quarterly dates (bolded) coincide with Triple Witch.

| Month | OpEx Date | Notes |
|-------|-----------|-------|
| January | 16 | |
| February | 20 | |
| **March** | **20** | **Triple Witch + S&P Rebalance** |
| April | 17 | |
| May | 15 | |
| **June** | **19** | **Triple Witch + S&P Rebalance + FOMC week** |
| July | 17 | |
| August | 21 | |
| **September** | **18** | **Triple Witch + S&P Rebalance + FOMC week** |
| October | 16 | |
| November | 20 | |
| **December** | **18** | **Triple Witch + S&P Rebalance** |

---

## Seasonal Edges

Statistical patterns from historical data. Use as context, not standalone signals.

| Window | Dates (2026) | Historical Edge | Notes |
|--------|-------------|-----------------|-------|
| January Effect | Jan 1-31 | Small-caps outperform large-caps | Tax-loss selling recovery |
| Turn-of-Month | Last trading day + first 3 of new month | +0.14% avg vs -0.04% rest of month | Payroll/pension fund flows |
| Sell in May | May 1 - Oct 31 | Weaker 6-month period historically | "Sell in May and go away" |
| September Weakness | Sep 1-30 | Worst calendar month historically | -0.5% avg return |
| Q4 Rally | Nov-Dec | Strongest 2-month period | Tax-loss selling ends, window dressing |
| Santa Claus Rally | Dec 24 - Jan 2 | +1.3% avg (since 1950) | Low volume, bullish sentiment |

---

## Presidential Cycle

2026 = Year 2 of presidential term (midterm year).

| Cycle Year | Historical Avg Return | Win Rate | 2026 Status |
|------------|----------------------|----------|-------------|
| Year 1 (post-election) | +7.0% | 60% | 2025 |
| **Year 2 (midterm)** | **+4.0%** | **55%** | **2026 ← Current** |
| Year 3 (pre-election) | +17.2% | 90% | 2027 |
| Year 4 (election) | +7.5% | 65% | 2028 |

Midterm years tend to front-load weakness (H1) with a strong rally from the midterm low (typically Oct-Nov) into Year 3.

**Full research**: `Cycles/Presidential Election Year Market Cycles.docx`, `Ideas/trump-media-etf-presidential-cycle-thesis.md`

---

## Key Convergence Dates

Dates where multiple structural events overlap — highest impact potential.

| Date | Events Converging |
|------|-------------------|
| **Mar 17-20** | FOMC (Mar 18) + Triple Witch (Mar 20) + S&P Rebalance (Mar 20) |
| **Jun 16-26** | FOMC (Jun 17) + Triple Witch (Jun 19) + S&P Rebalance (Jun 19) + Russell Reconstitution (Jun 26) |
| **Sep 15-18** | FOMC (Sep 16) + Triple Witch (Sep 18) + S&P Rebalance (Sep 18) |
| **Dec 8-18** | FOMC (Dec 9) + Russell Semi-Annual (Dec 11) + Triple Witch (Dec 18) + S&P Rebalance (Dec 18) |

---

*Update this calendar annually (December) or when new dates are confirmed. AAPL earnings dates should be verified each quarter. FOMC dates are tentative until confirmed at the preceding meeting.*

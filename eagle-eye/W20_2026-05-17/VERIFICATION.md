# Verification — W20 2026-05-17

Status: **PASS with minor corrections**. All four reports are internally coherent on the dominant narratives (Iran/Hormuz, hot CPI/PPI, Warsh confirmation, bear-steepener, oil shock, BTC break of 200-DMA). A handful of price discrepancies need to be reconciled in compilation.

## Cross-Report Consistency

| Data Point | Agent 1 (Equities) | Agent 2 (Rates) | Agent 3 (Commodities) | Agent 4 (Crypto) | Resolution |
|---|---|---|---|---|---|
| 10Y Treasury close (Fri) | 4.55% | 4.59% | n/a | 12-mo high cited | **Use 4.60%** (WolfStreet confirms) |
| 30Y close (Fri) | n/a | 5.12% | n/a | n/a | 5.12% ✓ |
| WTI close (Fri) | $105.42 | n/a | $105.66 | n/a | **Use ~$105.5** (sources differ by 24c) |
| Brent close (Fri) | $109.26 | $109.26 | $109-111 intraday | n/a | $109-111 range; Fortune confirms $111.04 intraday |
| CPI April YoY | 3.8% | 3.8% | hot (3.8%) | n/a | 3.8% ✓ confirmed |
| PPI April | 6.0% YoY | +1.4% MoM / 6.0% services YoY | "fastest since 2022" | 6.0% | **Use both**: headline +1.4% MoM, services +6.0% YoY |
| VIX (Fri close) | 18.43 | n/a | n/a | n/a | 18.43 (single source — accept) |
| Gold | n/a | n/a | $4,530-4,540 | n/a | ~$4,530 |
| Silver | n/a | n/a | $77.52 (-10.6% Fri) | n/a | $77.52 |
| DXY | n/a | n/a | 99.27 | n/a | 99.27 |
| BTC Sunday current | n/a | n/a | n/a | $78,010-78,160 | **Confirmed $77,987** via OKX spot-check |
| Warsh confirmation | n/a | 54-45 May 13 | 54-45 | n/a | 54-45 ✓ |

## Spot-Check Results (WebFetch)

1. **10Y/30Y Treasury (WolfStreet)** — Confirmed 10Y at **4.60%** (Equities report had 4.55%, off by ~5 bp; Rates report had 4.59%, within rounding). 30Y at **5.12%** matches Rates report exactly.
2. **BTC Current Price (OKX)** — Confirmed **$77,987.20** as of Sunday afternoon spot-check. Crypto report's $78,010-78,160 range is essentially correct.
3. **Brent Oil (Fortune)** — Confirmed Brent at **$111.04 intraday** (8:45am ET May 15). Commodities report's $109-111 range correct; Equities's $109.26 close is reasonable (different snapshot time).

## Corrections to Apply in Compilation

1. **10Y yield**: Use **4.60%** (not 4.55% from Equities, not 4.59% from Rates). +24bp weekly per WolfStreet narrative.
2. **WTI close**: Use **~$105.5/bbl** with weekly change "+11%" per Commodities Agent (Equities cites $105.42).
3. **Brent**: Use **$109-111/bbl Friday range**, +6-7% week per Commodities.
4. **BTC Sunday current**: Use **~$78,000** (matches OKX $77,987 confirmation).
5. The Equities Agent flagged several ⚠️ items (nuclear weekly returns CCJ/CEG/VST cited as cumulative not weekly) — Commodities Agent's CCJ -4.44% (week, Thurs print) is the better weekly number; **use CCJ -4.4% weekly**.
6. Multiple Tier 1/2 thesis tickers were "Data not located in available sources" (XLI, XLP, XLY, XLB, XLRE, XLC, FCX, AVGO/ANET/VRT, NET, OKTA, FLNC, EOSE, RUN, LEU, SMR, OKLO, BWXT, TLN, ISRG). Carry these forward as "n/a" rather than guessing.
7. **PPI**: When citing, clarify "+1.4% MoM headline / 6.0% YoY services" — both numbers are accurate but address different metrics.

## Sanity Checks on % Moves

- Cisco +13.4% Friday — extreme but consistent with multi-source coverage of AI-networking blowout. **Accept.**
- Silver -10.6% Friday — extreme but the broad metals risk-off narrative + multi-source confirmation supports it. **Accept.**
- BTC -6 to -8% weekly — consistent with $84K → $79K Fri close → $78K Sunday. **Accept.**
- RKLB +25.7% week / ATH $133.18 — large but consistent with Q1 print + listing upgrade + multiple PT raises. **Accept.**
- LMT, NOC down >20% trailing 3M despite Iran war — counterintuitive but confirmed in multiple sources; **flag as narrative-worthy** rather than data error.

## Weekend Story Triangulation

All four agents independently flag the **Strait of Hormuz / Iran fuel crisis** as the dominant weekend catalyst:
- Equities: Iran reasserted Hormuz blockade Sat May 16, gunboats fired on merchant vessels, India summoned Iran's ambassador.
- Rates: CNBC published Sat May 16 "bond market is flashing a warning over Iran"; G7 finance ministers meet Mon-Tue Paris.
- Commodities: UBS/JPMorgan/Aramco flagging "moment of truth in June" / "non-linear" price spike risk; OECD inventories approaching record lows; UK deployed Royal Navy warship + drones/fighters.
- Crypto: Macro inflation/yields narrative directly fed the BTC ~$700M liquidation cascade and break of 200-DMA.

This is a **3-axis convergence** (geopolitics + inflation + Fed transition) — confirmed as the lede for compilation.

## Items to Leave as Caveats in Final Report

- ⚠️ FOMC minutes (Apr 28-29) are scheduled for release Wed May 20 — **not yet out**, despite being in next_week_calendar.md as "High" impact. Flag in Week Ahead.
- ⚠️ Specific BTC ETF flow aggregates for week of May 11-15 not located (Farside displays but agent didn't surface). Acceptable to note "specific weekly aggregate not surfaced."
- ⚠️ THORChain exploit reference (in one liquidation source) — unverified, omit from compilation.

## Final Verdict

**Compile with corrections above applied.** Lede is the Hormuz/inflation/Warsh trifecta. Sector heatmap will be sparse (many ETFs unconfirmed) — present what's confirmed and use "n/a" elsewhere.

## Week Ahead Calendar Check

**PASS** — Calendar data stamped and verified.


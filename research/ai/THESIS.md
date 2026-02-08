# AI Infrastructure Investment Thesis

*Compiled: February 7, 2026*
*Source files: 01_Chips_Semiconductors.md, 02_DataCenters_Power.md, 03_Cloud_Inference.md, 04_Software_Models.md*

---

## Executive Summary

AI infrastructure is the defining capital expenditure cycle of the decade. The Big 5 hyperscalers will spend **~$650B in 2026 alone** (up from $241B in 2024), with ~75% directed at AI. This creates a massive addressable market across four layers: **chips/semiconductors** (NVIDIA at $187B TTM revenue, 86-97% GPU share), **physical infrastructure** (data centers, power, cooling, networking), **cloud/inference platforms** (CoreWeave $55.6B backlog, inference crossing 55% of AI compute), and **software/applications** (OpenAI $20B+ ARR, Anthropic $5B+, enterprise AI growing 20-60% YoY).

**Core thesis:** We are in a multi-year AI infrastructure supercycle with three investable layers — the picks-and-shovels infrastructure plays (highest visibility), the platform/cloud layer (high growth but leverage risk), and the application layer (longest duration but monetization still proving out). Power availability has become the #1 constraint, creating a parallel energy infrastructure thesis.

**The key tension:** $600B+ in infrastructure spend is generating only ~$25B in direct AI service revenue — a 4% monetization rate. The bull case requires this ratio to improve dramatically. The bear case says it won't, and 42% of companies abandoned AI initiatives in 2025.

**Critical risks:** Hyperscaler capex deceleration if AI ROI disappoints, NVIDIA margin compression from custom silicon (growing from 37% to 45% of AI chips by 2028), GPU depreciation risk at neoclouds, and a private-to-public valuation gap (25-30x vs 6x EV/Revenue) that must resolve.

---

## Industry Overview & Market Size

### The AI Spending Stack

| Layer | 2025 Size | 2026 Projected | Growth |
|-------|-----------|---------------|--------|
| Hyperscaler AI Capex | ~$443B | ~$650B | +47% |
| AI Chip Market (accelerators) | ~$167B | ~$220-250B | +35% |
| AI Server Market | ~$250B | ~$400B | +60% |
| Cloud AI Services (IaaS+PaaS) | ~$90-122B | ~$170B | +50% |
| AI Software (broad) | ~$515B | ~$644B | +25% |
| HBM Memory | ~$38B | ~$58B | +53% |
| Data Center Power Market | ~$35B | ~$41B | +17% |
| Liquid Cooling | ~$5-7B | ~$7-8B | +25% |

### Hyperscaler Capex — The Engine

| Company | 2024 | 2025 | 2026E |
|---------|------|------|-------|
| Amazon | $77B | $100-105B | ~$200B |
| Alphabet | $50B | $75B | $175-185B |
| Microsoft | $55B | $80B | ~$145B |
| Meta | $37B | $60-65B | $115-135B |
| Oracle | $10B | $20B | ~$40B |
| **Total** | **$241B** | **~$400B** | **~$650B** |

Amazon alone plans to spend more in 2026 ($200B) than all hyperscalers combined spent in 2024.

### Where the Money Goes

| Category | Share of AI Capex |
|----------|------------------|
| GPUs / AI Accelerators | 40-50% |
| Power / Cooling / Construction | 20-25% |
| Networking Equipment | 10-15% |
| Memory (HBM/DRAM) | 10-15% |
| Other (storage, software) | 5-10% |

---

## Key Sectors

### 1. Chips & Semiconductors

**NVIDIA dominates** with 86-97% discrete GPU share, $187B TTM revenue, and $4.5T market cap. The CUDA ecosystem creates massive switching costs. The Blackwell -> Rubin (2026, HBM4) -> Feynman (2028) roadmap maintains annual architecture cadence.

**The custom silicon threat is real but manageable.** Broadcom's XPU business is doubling annually ($20B to $46-50B), designing chips for Google, Meta, and 3 undisclosed hyperscalers. Custom silicon is projected to reach 45% of AI chip market by 2028 (up from 37%). But NVIDIA still dominates general-purpose training.

**HBM is the structural margin upgrade for memory.** $38B market in 2025 growing to $58B in 2026. SK Hynix leads (62% share), Micron is the best US-listed play (21% share, growing). HBM gross margins of ~70% vs 30-40% for commodity DRAM.

**TSMC and ASML are irreplaceable monopolies.** Every AI chip goes through TSMC (CoWoS packaging is the binding constraint, not fab capacity — expanding from 35K to 130K wafers/mo). ASML is the sole EUV lithography provider. No alternatives exist.

**Key data points:**
- NVIDIA controls 60% of TSMC's 2026 CoWoS capacity
- AMD AI accelerator revenue: ~$9.5B target for 2025, MI400 launching early 2026
- ARM Neoverse approaching 50% of hyperscaler CPU deployments
- China at 1-2% of US AI chip production capacity despite Huawei efforts

### 2. Data Centers & Power Infrastructure

**Power is the new bottleneck.** US data center power demand is projected to grow from ~40 GW to 134 GW by 2030. Grid spending needs: ~$720B. Transformer lead times: 2-4 years. This is the #1 constraint on AI growth.

**Nuclear renaissance for data centers:**
- Microsoft/Constellation: TMI restart (837 MW, 20-year PPA)
- Meta/Vistra: 2.6 GW nuclear deal
- Meta/Oklo: 1.2 GW SMR (first phase ~2030)
- Amazon/Talen: Susquehanna 1,920 MW through 2042

**Natural gas is the bridge** (2-3 year deploy vs 5-10+ for nuclear). Williams Companies committed $5.1B to data center power plants. Kinder Morgan moves 40% of US gas.

**Power equipment has massive backlogs:**
- Eaton (ETN): $15.3B backlog, DC orders +200% YoY
- Vertiv (VRT): $9.5B backlog, 1.4x book-to-bill
- Quanta Services (PWR): $39.2B backlog

**Networking is shifting:** Arista surpassed Cisco in DC switching share (27.5% vs 29.9%, from 3.5% vs 78% in 2012). 800G ports tripled sequentially.

**Fiber demand surging:** Corning optical revenue +39%, enterprise +58%. Ciena guiding $5.7-6.1B (+20-28%).

### 3. Cloud AI & Inference Platforms

**2026 is the inference crossover year** — inference spending exceeds training for the first time (55% vs 45%), heading to 75-80% by 2030. The inference market is $106B in 2025, growing to $255B by 2030.

**Hyperscaler AI revenue is accelerating:**
- Azure AI run rate: $26B (doubled in a single fiscal year)
- AWS Trainium: multi-billion $, 150% QoQ growth
- GCP Vertex AI: 20x YoY usage growth

**CoreWeave (CRWV) is the neocloud bellwether:** $5B 2025 revenue, $55.6B backlog, but $863M GAAP loss and 6-year GPU depreciation on hardware that faces 4-5x performance jumps every 2 years.

**Token price deflation is brutal:** 200x/year price decline post-Jan 2024. GPT-4 equivalent dropped from $60 to $0.40 per million tokens. Revenue growth requires volume to massively outpace price compression.

**Inference silicon is strategic:** NVIDIA acquired Groq for ~$20B, validating inference-specific ASICs. Cerebras at $23B valuation with Q2 2026 IPO planned.

### 4. Software, Models & Applications

**Foundation model layer is concentrating** into 3-4 winners:
- OpenAI: $20B+ ARR, targeting $100B by 2027-2029, $300-830B valuation
- Anthropic: $5B+ ARR (from $1B in early 2025), $183-350B valuation, ~33% enterprise share
- Google Gemini: 750M MAU, serving costs reduced 78%
- Meta Llama: Open-source strategy commoditizing the model layer

**Enterprise AI software is the monetization proof point:**
- Palantir (PLTR): $4.475B FY2025 (+56%), guided $7.2B FY2026 (+61%) — but 189x P/E
- Salesforce Agentforce: 330% ARR growth, 9,500+ paid deals
- ServiceNow: targeting $1B AI ACV in FY2026
- Databricks: $134B private valuation, $4.8B ARR (+55%), IPO expected H2 2026

**AI coding is the killer app:** $7.4B market. GitHub Copilot at 42% share (20M users). Cursor exploded from $1M to $500M ARR in 2 years. Gartner: 90% of enterprise devs using AI assistants by 2028.

**The 4% problem:** Only ~$25B in direct AI service revenue vs $600B+ infrastructure spend. 42% of companies abandoned AI initiatives in 2025. 70-85% of AI projects fail to meet expectations. The market is shifting from "promise phase" to "proof phase."

---

## Public Company Analysis

### Tier 1: Core Holdings (Structural Winners)

| Ticker | Company | Market Cap | Revenue | Growth | Key Thesis |
|--------|---------|-----------|---------|--------|------------|
| **NVDA** | NVIDIA | ~$4.5T | $187B TTM | +65% | GPU monopoly, CUDA moat, 73% gross margins. Expensive but justified by earnings power. |
| **TSM** | TSMC | ~$1.0T | $123B | +32% | Foundry monopoly. Every AI chip goes through TSMC. Reasonable valuation. |
| **AVGO** | Broadcom | ~$1.1T | $56B | +44% | Best custom silicon play. AI revenue doubling annually. Benefits regardless of NVIDIA vs custom outcome. |
| **VRT** | Vertiv | ~$50B | $10B+ | +24% | Power/cooling picks-and-shovels. $9.5B backlog. Mandatory infrastructure for every AI data center. |
| **ANET** | Arista Networks | ~$120B | $8.75B | +25% | #1 in 800G DC switching. Taking share from Cisco. Every GPU cluster needs networking. |

### Tier 2: High-Conviction Growth

| Ticker | Company | Market Cap | Revenue | Growth | Key Thesis |
|--------|---------|-----------|---------|--------|------------|
| **MRVL** | Marvell | ~$95B | $7.5B | +45% | Custom silicon + electro-optics. Celestial AI acquisition adds optical interconnect. |
| **MU** | Micron | ~$120B | $30B | +50% | Best US-listed HBM play. Cheapest valuation in AI semis. 70% HBM gross margins. |
| **ETN** | Eaton | ~$130B | $27.4B | +10% | $15.3B backlog, DC orders +200%. Power distribution monopoly position. $9.5B Boyd Thermal for cooling. |
| **CEG** | Constellation Energy | ~$111B | — | +11% rev | Largest US nuclear fleet. Microsoft TMI deal. 20-year PPA model. |
| **GLW** | Corning | ~$45B | $16B | +14% | Optical +39%, enterprise +58%. Every AI node needs fiber. Structural demand. |
| **PLTR** | Palantir | ~$350B | $4.5B FY25 | +56% | AIP as enterprise AI OS. 61% FY26 guided growth. 189x P/E is the debate. |

### Tier 3: Opportunistic / Speculative

| Ticker | Company | Market Cap | Revenue | Growth | Key Thesis |
|--------|---------|-----------|---------|--------|------------|
| **ASML** | ASML | ~$350B | EUR 32.7B | +20% | EUV monopoly. Essential but well-valued. |
| **AMD** | AMD | ~$220B | $34B | +14% | Gaining share but far behind NVIDIA. MI400 cycle is key catalyst. |
| **CRWV** | CoreWeave | ~$50B | $5B FY25 | +150% | $55.6B backlog but $863M loss, 6yr depreciation risk. Neocloud bellwether. |
| **PWR** | Quanta Services | ~$50B | $27.5B | +19% | $39.2B backlog. Grid modernization. Less pure AI play but strong execution. |
| **VST** | Vistra | ~$59B | — | — | 44 GW fleet, 2.6 GW Meta deal. Nuclear + gas diversification. |
| **CIEN** | Ciena | ~$12B | $4.77B | +19% | Optical networking. $5.7-6.1B FY26 guide. 800G/1.6T cycle. |
| **NOW** | ServiceNow | ~$230B | $13.6B | +22% | Targeting $1B AI ACV. Enterprise AI workflows. |
| **INTC** | Intel | ~$191B | $53.5B | -1% | Deep turnaround. CHIPS Act (govt owns 9.9%), 18A node. High risk, high optionality. |

### Tier: Avoid / Caution

| Ticker | Company | Reason |
|--------|---------|--------|
| **ARM** | ARM Holdings | Structural winner but ~70x forward P/E prices in perfection. Any stumble punished severely. |
| **SPCE-equivalent AI SPACs** | Various | Pre-revenue AI companies going public via SPAC. Space SPAC history (-65% avg) is the warning. |

### Key Private Companies to Watch

| Company | Valuation | Event |
|---------|-----------|-------|
| **OpenAI** | $300-830B | IPO late 2026/2027. $20B+ ARR. The defining AI company. |
| **Anthropic** | $183-350B | IPO discussions started. $5B+ ARR. Enterprise AI leader (~33% share). |
| **Databricks** | $134B | IPO H2 2026. $4.8B ARR (+55%). Data infrastructure backbone. |
| **Cerebras** | $23B | IPO Q2 2026. Wafer-scale inference silicon. |
| **Crusoe Energy** | $10B+ | 1.2GW Abilene campus. 30-50% lower energy cost. |

---

## Investment Timing Framework

### Now (Q1 2026) — Build Core Positions

The infrastructure layer has the highest revenue visibility:
- **NVDA/TSM/AVGO**: Semiconductor backbone — demand locked in via $650B capex
- **VRT/ETN**: Power equipment — $9.5B and $15.3B backlogs provide multi-year visibility
- **ANET**: Networking — 800G cycle just beginning, #1 position
- **MU**: HBM — cheapest valuation in AI semis, structural margin upgrade

### Mid-2026 — IPO Wave

The largest AI IPO cycle in history:
- **Databricks** (H2 2026): Evaluate at listing. $134B private = ~28x $4.8B ARR.
- **Cerebras** (Q2 2026): Inference silicon pure-play. Validate market reception.
- **OpenAI/Anthropic** (late 2026-2027): Will reprice entire AI software sector.

### 2026-2027 — Prove the Monetization

The 4% problem must improve. Watch for:
- Enterprise AI adoption converting from pilots to production
- Inference revenue scaling (volume must outpace 200x/yr price deflation)
- Hyperscaler capex guidance — any cuts = sector-wide correction
- AMD MI400/MI450 adoption (ROCm maturity determines if NVIDIA faces real competition)

### 2028-2030 — Energy & Next Wave

- SMRs come online (Oklo ~2028, NuScale ~2030)
- Data center power demand hits 134 GW (from 40 GW today)
- Agentic AI at scale (46% CAGR to $52.6B by 2030)
- Custom silicon reaches 45%+ of AI chip market

---

## Risk Factors

### High Risk

1. **Hyperscaler Capex Deceleration** — $650B in 2026 capex assumes AI ROI materializes. If 42% enterprise abandonment rate persists, capex cuts would cascade across the entire stack.

2. **The 4% Monetization Problem** — Only ~$25B AI service revenue on $600B+ infrastructure spend. If the ratio doesn't improve by late 2026, expect a narrative reset.

3. **NVIDIA Margin Compression** — Custom silicon growing from 37% to 45% share. Inference (more competitive, lower margin) overtaking training. 73% gross margins may not hold.

4. **GPU Depreciation Risk** — Neoclouds depreciating over 6 years while performance jumps 4-5x every 2 years. If older GPU utilization falls, write-downs could be significant (CoreWeave's $863M loss is a warning).

### Medium Risk

5. **Private/Public Valuation Gap** — AI private market at 25-30x EV/Revenue vs public SaaS at 6x. Either private corrects or public expands. IPO wave will test which.

6. **Export Control Whiplash** — US-China chip policy changes quarterly. Creates revenue uncertainty for NVIDIA, AMD, and equipment makers.

7. **Power Grid Bottleneck** — 134 GW demand by 2030 requires ~$720B in grid spending. Transformer lead times of 2-4 years. If power can't keep up, AI growth slows.

8. **Token Price Deflation** — 200x/year decline means inference providers face brutal margin pressure. Volume must massively outpace price compression.

9. **Open-Source Commoditization** — Meta's Llama strategy could commoditize the model layer, compressing margins for OpenAI/Anthropic and benefiting application-layer companies.

10. **Concentration Risk** — Top 5 hyperscalers represent the vast majority of AI chip demand. Any single company pulling back is material to the entire supply chain.

---

## Recommended Watchlist

### Tier 1: Core Infrastructure (Highest Visibility)
| Ticker | Thesis | Key Metric to Watch |
|--------|--------|---------------------|
| NVDA | GPU monopoly + CUDA moat | Data center revenue growth rate (decelerating from +142% to +66%) |
| TSM | Foundry monopoly, every AI chip | CoWoS capacity expansion, AI revenue share |
| AVGO | Custom silicon + networking | XPU customer count, AI revenue doubling |
| VRT | Power/cooling picks-and-shovels | Backlog growth, book-to-bill ratio |
| ANET | #1 800G DC switching | AI Center revenue, 800G port shipments |

### Tier 2: High-Growth AI Exposure
| Ticker | Thesis | Key Metric to Watch |
|--------|--------|---------------------|
| MU | Best US HBM play, cheapest AI semi | HBM revenue share, HBM4 qualification wins |
| ETN | Power distribution + cooling | DC orders growth, Boyd Thermal integration |
| CEG | Nuclear fleet for data centers | New PPA announcements, TMI restart timeline |
| PLTR | Enterprise AI platform | US Commercial growth rate, AIP adoption |
| GLW | Fiber demand from AI clusters | Optical/enterprise revenue acceleration |

### Tier 3: Opportunistic / Event-Driven
| Ticker | Catalyst |
|--------|----------|
| CRWV | Prove GAAP profitability path, utilization rates |
| AMD | MI400 launch and hyperscaler adoption |
| INTC | 18A node customer wins, IFS profitability |
| Databricks IPO | Evaluate at listing — $134B private valuation |
| Cerebras IPO | Inference silicon validation |
| OpenAI/Anthropic IPO | Sector-repricing events |

---

## Key Dates Calendar

| Date | Event | Impact |
|------|-------|--------|
| Q1 2026 | AMD MI400 launch | Tests NVIDIA GPU competition |
| Q2 2026 | Cerebras IPO (Nasdaq) | Inference silicon market validation |
| H1 2026 | Ciena WaveLogic 6 Nano GA | 800G pluggable volume |
| Mid-2026 | NVIDIA Rubin architecture | Next-gen GPU cycle begins |
| H2 2026 | Databricks IPO | Largest data/AI software IPO |
| H2 2026 | Lambda Labs IPO (tentative) | Neocloud market test |
| Late 2026 | OpenAI IPO filing (possible) | Defines AI software valuations |
| 2027 | Anthropic IPO (possible) | Enterprise AI market pricing |
| 2028 | Oklo first commercial SMR | Nuclear for data centers validation |
| 2028 | NVIDIA Feynman architecture | Next paradigm shift |
| 2030 | US DC power demand: 134 GW | Energy infrastructure test |

---

*This thesis is for research purposes only and does not constitute investment advice. All data sourced from company filings, earnings calls, SEC filings, MarketsAndMarkets, Grand View Research, Mordor Intelligence, IDC, Gartner, Goldman Sachs, and industry reports. Prices and valuations as of early February 2026.*

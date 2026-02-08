# AI Chips & Semiconductor Infrastructure

*Research compiled: February 2026*

---

## Table of Contents
1. [Market Overview & TAM](#market-overview--tam)
2. [NVIDIA (NVDA)](#nvidia-nvda)
3. [AMD (AMD)](#amd-amd)
4. [Broadcom (AVGO)](#broadcom-avgo)
5. [Marvell (MRVL)](#marvell-mrvl)
6. [Intel (INTC)](#intel-intc)
7. [ARM Holdings (ARM)](#arm-holdings-arm)
8. [Custom Silicon (Hyperscaler)](#custom-silicon-hyperscaler)
9. [Memory & HBM](#memory--hbm)
10. [Equipment & Supply Chain](#equipment--supply-chain)
11. [Export Controls & Geopolitics](#export-controls--geopolitics)
12. [Hyperscaler AI Capex](#hyperscaler-ai-capex)
13. [Key Risks & Themes](#key-risks--themes)

---

## Market Overview & TAM

### AI Chip TAM Estimates

| Metric | 2024 (Actual) | 2025 (Est.) | 2026 (Est.) | 2030 (Est.) |
|--------|--------------|-------------|-------------|-------------|
| AI Accelerator Market | ~$53-100B | ~$167B | ~$220-250B | ~$300-350B |
| AI Server Market | ~$140B | ~$250B | ~$400B | $800-850B |
| Total DC Silicon (accel+CPU+net+HBM) | — | — | — | $900B-1T |
| Lisa Su TAM Estimate (AI accel) | — | — | — | $1T |
| Jensen Huang AI Infra (5yr) | — | — | — | $3-4T |

**Key insight:** TAM definitions vary widely. The dedicated AI accelerator market (GPUs + ASICs) is ~$300-350B by 2030. Broader AI infrastructure (servers, networking, memory, power) approaches $1T+.

### Market Share — Data Center AI Chips (2024-2025)

| Company | 2023 Share | 2024-25 Share | Trend |
|---------|-----------|--------------|-------|
| NVIDIA | ~65% | ~86% (discrete GPU: 94-97%) | Consolidating dominance |
| AMD | ~11% | ~4-5% (growing in absolute $) | Gaining but far behind |
| Intel | ~22% (mostly CPU) | ~8.7% (Gaudi/CPU) | Declining in AI accel |
| Custom (Google/Amazon/Meta) | ~37% of total AI chip | ~40% (2025) | Rising to 45% by 2028 |

**GPU vs. ASIC split:** GPU revenue was ~$100B in 2024, projected to reach $215B by 2030. AI ASIC revenue expected to reach $84.5B by 2030. Custom silicon share rising from 37% to 45% by 2028.

---

## NVIDIA (NVDA)

### Financials

| Metric | FY2024 (Jan '24) | FY2025 (Jan '25) | FY2026 (trailing) |
|--------|-----------------|-----------------|-------------------|
| Total Revenue | $60.9B | $130.5B | ~$187B (TTM Oct '25) |
| Data Center Revenue | $47.5B | $115.2B | ~$165B (TTM) |
| Gross Margin | ~72% | ~75% | ~73.4% |
| Operating Margin | ~54% | ~64% | ~64.4% |
| Net Margin | — | — | ~53% |
| Market Cap | — | — | ~$4.5T (Feb '26) |

*Q4 FY2025: Record DC revenue of $35.6B (+93% YoY). Q2 FY2026: DC revenue $51.2B (+66% YoY).*

### GPU Product Stack & Pricing

| GPU | Architecture | HBM | Est. Purchase Price | Cloud $/hr |
|-----|-------------|-----|-------------------|------------|
| H100 | Hopper | 80GB HBM3 | $25,000-40,000 | $2.10-8.00 |
| H200 | Hopper | 141GB HBM3E | $30,000-40,000 | $2.50-10.60 |
| B200 | Blackwell | 192GB HBM3E | ~$40,000-60,000 | ~$6.25 |
| GB200 (NVL72) | Blackwell | 288GB/GPU | ~$3M/rack | — |

*DGX systems (8-GPU): ~$400-500K per system. ASPs trending up with each generation due to HBM cost increase.*

### Architecture Roadmap

| Architecture | Timeframe | Key Specs |
|-------------|-----------|-----------|
| **Blackwell** (B200/B300) | 2024-2025 | TSMC 4NP, HBM3E, NVLink 5 |
| **Blackwell Ultra** (B300) | H2 2025 | Enhanced Blackwell, 288GB HBM3E |
| **Rubin** | 2026 | HBM4, NVL144, 3.6 EFLOPS FP4, 13TB/s mem BW |
| **Rubin Ultra** | H2 2027 | 4 GPU dies/package, NVL576, 15 EFLOPS FP4, 365TB memory |
| **Feynman** | 2028 | Next-gen (details TBD) |

*Rubin NVL144 delivers 3.3x compute improvement over B300 NVL72.*

### Competitive Moat

- **CUDA ecosystem**: ~20 years of development, millions of developers, massive optimized library base. Switching costs are extremely high for training workloads.
- **94-97% discrete GPU market share** in AI data centers (Q2 2025).
- **Full-stack integration**: GPU + NVLink + NVSwitch + networking (Spectrum-X, ConnectX) + software (CUDA, cuDNN, TensorRT, NCCL, NIM).
- **CoWoS capacity lock-up**: ~60% of TSMC's CoWoS capacity for 2026 (~700K wafers).
- **Risk**: Custom silicon from hyperscalers growing share; inference market more open to competition than training.

---

## AMD (AMD)

### Financials & AI Revenue

| Metric | 2023 | 2024 | 2025 (Est.) |
|--------|------|------|-------------|
| Total Revenue | ~$22.7B | ~$25.8B | ~$34B |
| Data Center Revenue | — | ~$12.6B | ~$16B |
| AI Accelerator (Instinct) Revenue | <$1B | ~$5B+ | ~$9.5B |
| Market Cap | — | — | ~$220B (Feb '26) |

*Q2 2024: First $1B+ quarter for MI300X sales. AMD expects data center GPU revenue to double again by 2027.*

### Product Roadmap

| Product | Timeline | Key Specs |
|---------|----------|-----------|
| **MI300X** | 2024 (shipping) | CDNA 3, 192GB HBM3, 5.3TB/s BW |
| **MI325X** | Late 2024 | 256GB HBM3E |
| **MI350** | H1 2025 | CDNA 4, HBM3E |
| **MI400** | Early 2026 | CDNA "Next", 2x AI compute, 432GB HBM4 |
| **MI450** | 2026 | TSMC 2nm, direct Blackwell competitor |

### ROCm Software Ecosystem

- **ROCm 7** (2025): Improved inference throughput, distributed inference (prefill/decode decoupling), training performance improvements.
- **Microsoft conversion toolkits**: Microsoft created toolkits to convert CUDA models to ROCm code — significant adoption signal.
- **Weakness**: CUDA ecosystem remains far deeper. ROCm works for inference but training adoption is limited. Developer mindshare gap is still wide.
- **Opportunity**: Inference market (eventually larger than training) is where AMD's CUDA moat disadvantage matters less.

### Strategic Assessment

- Distant #2 in AI accelerators but absolute revenue growing fast ($5B+ in 2024).
- Xilinx acquisition adds FPGA/adaptive computing for edge AI. Pensando adds SmartNICs/DPUs.
- Target: 20-30% market share by 2027 via MI350/MI400 hyperscaler adoption.
- Risk: NVIDIA's rapid cadence (annual new architectures) makes catching up difficult.

---

## Broadcom (AVGO)

### AI Revenue & Custom ASIC Business

| Metric | FY2024 | FY2025 | FY2026 (Est.) |
|--------|--------|--------|---------------|
| AI Revenue | $12.2B | $19.9B (+63% YoY) | ~$46-50B (+134% YoY) |
| AI Semiconductor (Q4 FY2025) | — | $6.5B (+74% YoY) | — |
| Total Revenue | — | ~$56B | — |

### XPU / Custom ASIC Customers

| Customer | Program | Status |
|----------|---------|--------|
| Google | TPU (v5/v6/v7 Ironwood) | Exclusive partner since 2016, $10B+ annual |
| Meta | MTIA | Active XPU customer |
| Customer #3 | Undisclosed | Active |
| Customer #4 | Undisclosed | $10B XPU order (FQ3 '25) |
| Customer #5 | Undisclosed | $1B order (Q4 FY2025) |

*Q3 FY2025: $10B TPU rack order. Q4 FY2025: $11B follow-on order. Potential new customers include OpenAI and Anthropic (reported $121B revenue potential).*

### Networking Division

- **Memory Fabric / Ethernet switching**: Jericho3-AI, critical for AI cluster networking.
- **PCIe switches**: Essential for GPU/accelerator interconnect.
- Networking revenue benefits from same AI infrastructure buildout driving GPU demand.

### Strategic Assessment

- Best-positioned pure-play on custom silicon trend (hyperscalers building own chips).
- Benefits regardless of whether NVIDIA or custom silicon wins — Broadcom designs the custom chips.
- AI revenue doubling+ annually with expanding customer base.
- Risk: Customer concentration (Google is dominant). Hyperscalers could bring chip design in-house long-term.

---

## Marvell (MRVL)

### Financials & AI Revenue

| Metric | FY2023 | FY2024 | FY2025 | FY2026 (Est.) |
|--------|--------|--------|--------|---------------|
| AI Revenue | ~$200M | ~$550M | ~$1.5B | >$2.5B |
| Total Revenue | — | — | — | ~$7.5B+ |
| Data Center Rev Growth | — | — | +78% YoY | +63% YoY |

*Q3 FY2026: AI revenues $1.24B ($418M custom XPU + $819M electro-optics).*

### Business Segments

1. **Custom AI Silicon (XPU)**: Multi-year hyperscaler partnerships for custom accelerator design. Growing rapidly.
2. **Electro-Optics**: 800G PAM DSPs, 400G ZR DCI products. Critical for AI cluster connectivity. Projected +35% YoY growth in FY27.
3. **Data Center Connectivity**: Ethernet switches, PHYs, retimers for AI infrastructure.

### Strategic Moves

- **Celestial AI acquisition** (Dec 2025): Photonic Fabric technology for scale-up optical interconnect. Transformational for next-gen AI data center connectivity.
- Positioned at intersection of custom silicon + optical interconnect — both high-growth AI infrastructure segments.

### Assessment

- Smaller than Broadcom but faster-growing in AI.
- Electro-optics is a structural winner as AI clusters scale to millions of GPUs.
- Risk: Smaller scale, customer concentration, execution risk on Celestial AI integration.

---

## Intel (INTC)

### Leadership & Turnaround Status

- **CEO**: Lip-Bu Tan (former Cadence CEO, appointed March 2025, replacing Pat Gelsinger who retired late 2024).
- **Strategy**: "Foundry First" — restructured into Intel Products + Intel Foundry (IFS).
- **CHIPS Act**: $8.9B in grants converted to 9.9% direct US government equity stake (Aug 2025). US government is now largest shareholder.
- **Market Cap**: ~$191B (Feb 2026).

### Financials

| Metric | 2024 | 2025 (Est.) | 2026 (Est.) |
|--------|------|-------------|-------------|
| Revenue | ~$54B | ~$53.5B (-1%) | ~$55B (+3%) |
| Gross Margin (non-GAAP) | ~35% | ~40% | Improving |
| Q3 2025 Revenue | — | $13.7B (+3% YoY) | — |
| Forward P/E | — | — | ~22x |

*Turned cash-flow positive H2 2025. Double beat in Q3 2025.*

### AI Accelerator: Gaudi

| Product | Specs | Status |
|---------|-------|--------|
| **Gaudi 3** | 128GB HBM2e, 3.7TB/s BW, PCIe 5.0 | Shipping via Dell, HPE, Lenovo, Supermicro |
| **Jaguar Shores** | HBM4E memory | Expected 2026 |

- Gaudi 3 claims 70% better price-performance vs H100 for Llama 3 80B inference.
- Market share target: ~8.7% of AI training accelerator market by end 2025.
- Reality: Very small AI accelerator revenue vs. NVIDIA/AMD. Gaudi has not achieved meaningful scale.

### Foundry (IFS)

- **18A Process Node**: PowerVia (backside power) + RibbonFET (GAA transistors). Panther Lake (CES 2026) is first consumer CPU on 18A.
- **Customers**: Microsoft, AWS, Tesla, Qualcomm, NVIDIA (packaging services).
- **Risk**: IFS is still unprofitable. TSMC's lead in advanced packaging and yields is massive. Intel foundry is a multi-year bet.

### Assessment

- Turnaround story, not an AI growth story (yet). Deep discount to peers.
- CHIPS Act support de-risks the foundry bet. Government backing is real.
- Gaudi has not broken through. AI accelerator business is subscale.
- Optionality play: if 18A works and IFS wins external customers, massive upside. But execution risk is high.

---

## ARM Holdings (ARM)

### Financials

| Metric | FY2025 | FY2026 (Recent Q) |
|--------|--------|-------------------|
| Quarterly Revenue | ~$1B+ | $1.24B (Q3 FY2026, +26% YoY) |
| Royalty Revenue | — | $737M record (Q3, +27% YoY) |
| 4 consecutive quarters >$1B | Yes | Yes |
| Market Cap | — | ~$190-220B |

### AI & Data Center

- **Neoverse**: Over 1 billion Arm Neoverse cores shipped for AI/hyperscaler workloads.
- **Hyperscaler CPU share**: Expected to reach ~50% of top hyperscaler CPU deployments (vs ~10% a few years ago). AWS Graviton, Google Axion, Microsoft Cobalt all Arm-based.
- **Royalty mix shift**: Cloud/networking royalties trending from ~10% to 15-20% of total royalties, growing fast.
- **Armv9 + CSS**: Higher royalty rates per chip. Each generation shift = higher ASP for ARM.

### Valuation Concern

- Trades at extreme premium (~60-80x forward earnings).
- Revenue growth is real but valuation prices in near-perfect execution.
- Risk: Any deceleration in royalty growth or hyperscaler CPU adoption gets punished severely.

### Assessment

- Structural winner from the shift to Arm-based compute in data centers and edge AI.
- Every custom AI chip (Google, Amazon, etc.) mostly uses Arm cores, so ARM benefits from the custom silicon trend too.
- Valuation is the main concern — fundamentals are strong but priced for perfection.

---

## Custom Silicon (Hyperscaler)

### Google

| Product | Status | Specs |
|---------|--------|-------|
| **TPU v6 (Trillium)** | Volume production 2025-26, 1.6M+ units | 4.7x perf vs v5e, 67% better energy efficiency |
| **TPU v7 (Ironwood)** | GA early 2026 | Native FP8, 192GB HBM3e, 7.4TB/s BW |

- Designed by Broadcom, manufactured by TSMC.
- Anthropic, DeepMind, and internal Google workloads run on TPUs.
- Google's $185B commitment to AI infrastructure heavily features TPUs.

### Amazon

| Product | Status | Specs |
|---------|--------|-------|
| **Trainium2** | GA Dec 2024 | 30-40% better price-perf vs H100 (P5e instances) |
| **Inferentia2** | Production | Inference-optimized |

- Anthropic training on 500K+ Trainium2 chips (New Carlisle, Indiana facility).
- AWS offering Trainium2 instances to external customers.

### Microsoft

| Product | Status | Specs |
|---------|--------|-------|
| **Maia 100** | Announced Nov 2023 | 105B transistors, TSMC 5nm, 64GB HBM2E |

- No external availability announced. Used internally for Azure AI workloads.
- Microsoft also investing heavily in AMD MI300X as NVIDIA alternative.

### Meta

| Product | Status | Specs |
|---------|--------|-------|
| **MTIA v2i** | June 2025 | Inference-focused, 44% lower TCO vs NVIDIA for recommendation models |
| **MTIA v3** | Full deployment 2025-26 | Full-stack training + inference |

- Initially focused on recommendation/ranking (not LLM training).
- MTIA v3 expanding to broader AI training workloads.

### Market Impact

- Custom silicon projected to be 45% of AI chip market by 2028 (up from 37% in 2024).
- Prediction: >60% of AI compute on non-NVIDIA hardware by end of decade.
- Key nuance: Custom silicon mostly handles inference + specific workloads. NVIDIA still dominates general-purpose training.

---

## Memory & HBM

### HBM Market Size

| Metric | 2024 | 2025 | 2026 (Est.) |
|--------|------|------|-------------|
| HBM Market | ~$25B | ~$38B | ~$58B |
| Total Memory Market | — | — | >$440B |
| HBM Price Premium vs DDR | ~6x | ~6x | ~6-8x (HBM4) |
| HBM Gross Margins | — | ~70% | ~70% |

### Market Share (Q2 2025)

| Manufacturer | HBM Share | HBM4 Position |
|-------------|----------|---------------|
| **SK Hynix** | 62% | ~70% share for Rubin platform (UBS est.) |
| **Micron (MU)** | 21% | HBM4 36GB 12-high samples shipped |
| **Samsung** | 17% | Targeting >30% in 2026 |

### HBM Technology Roadmap

| Generation | Status | Key Details |
|-----------|--------|-------------|
| **HBM3** | Mature/declining | H100 memory |
| **HBM3E** | Volume production | H200/B200 memory, ~2/3 of 2026 HBM shipments |
| **HBM4** | Ramping H2 2026 | Rubin platform, 8x DDR pricing, 12-high stacks |
| **HBM4E** | 2027+ | Jaguar Shores (Intel) |

### Pricing Trends

- Samsung and SK Hynix planning ~20% HBM3E price hike for 2026 (NVIDIA H200 + ASIC demand).
- Supply remains tight through 2026; potential correction after 2026 as capacity expands.
- HBM is the most profitable memory product — structural shift in memory industry profitability.

### Investment Implications

- **SK Hynix**: Dominant position, highest margins. Not directly investable on US exchanges (Korean ADRs limited).
- **Micron (MU)**: Best US-listed HBM play. Growing from #3 to #2. HBM4 samples shipping.
- **Samsung**: Lagging in HBM but massive resources to catch up. Broader conglomerate dilutes HBM exposure.

---

## Equipment & Supply Chain

### TSMC (TSM)

| Metric | 2024 | 2025 | 2026 (Est.) |
|--------|------|------|-------------|
| Revenue | ~$90B | ~$122.9B (+31.6% YoY) | Q1 guide: $34.6-35.8B |
| Capex | — | $40.9B | $52-56B (+30%) |
| CoWoS Capacity (wafers/mo) | ~35K | ~70K | 125-130K |
| AI Accelerator Revenue Share | — | 17-19% of wafer rev | >20% |
| AI Accel Revenue CAGR (2024-29) | — | — | 54-56% |

- **NVIDIA controls ~60% of TSMC's 2026 CoWoS capacity** (~700K wafers for Blackwell).
- Advanced packaging revenue: ~8% of total in 2025, rising to >10% in 2026.
- Capex allocation: 70-80% advanced process, 10-20% packaging/testing, 10% specialty.
- **Bottleneck**: CoWoS packaging, not leading-edge wafer fab, is the binding constraint for AI chip supply.

### ASML (ASML)

| Metric | 2025 | 2026 (Guide) |
|--------|------|-------------|
| Revenue | EUR 32.7B | EUR 34-39B (+12% midpoint) |
| Gross Margin | 52.8% | — |
| EUV Growth | +39% YoY | Significant growth expected |
| Q4 2025 EUV Bookings | EUR 7.4B | — |

- **Monopoly on EUV lithography**. No competitor exists for sub-7nm manufacturing.
- EUV + immersion = 90% of system revenue.
- AI is the primary demand driver: every advanced AI chip requires EUV.
- High-NA EUV (next gen) ramping for 2nm and below.

### Samsung Foundry

- **2nm GAA**: Mass production began Nov 2025. Yields reportedly 55-60%.
- **Competition**: Distant #2 to TSMC. Struggling to win major AI chip customers.
- **Customers**: Mostly smaller AI startups (Charbright, DeepX), not hyperscalers.
- **Roadmap**: 2nm for mobile (2025), HPC (2026), automotive (2027). 1.4nm planned.
- **Assessment**: Not a realistic TSMC alternative for leading-edge AI chips in near term.

---

## Export Controls & Geopolitics

### Current US-China Chip Restrictions (as of Feb 2026)

| Date | Action |
|------|--------|
| Oct 2022 | Initial export controls on advanced chips to China |
| Oct 2023 | Expanded controls, closed loopholes |
| Mar 2025 | 42 PRC entities added to Export Control List |
| Apr 2025 | Trump announced H20 ban (reversed) |
| Jul 2025 | H20 sales allowed with 15% revenue share requirement |
| Sep 2025 | 23 more PRC entities added to ECL |
| Dec 2025 | Trump allows H200 sales to China |
| Jan 2026 | Commerce Dept. permits H200 + AMD MI325X sales to China |

### Impact Assessment

- **NVIDIA China revenue**: Significantly impacted but partially restored with H200 permission. 1M H200 shipments would increase China's AI compute by 250%.
- **Huawei Ascend chips**: Assessed by BIS (May 2025) as developed in violation of US controls. Next-gen chip (2026) reportedly less powerful than current best — SMIC stuck at 7nm.
- **China's AI compute gap**: Huawei producing only 62K-160K B300-equivalent units in 2026 vs. US production of 6.89M B300-eq units. China at 1-2% of US production capacity.
- **Key risk**: Policy whiplash creates uncertainty for chip companies' China revenue planning.

---

## Hyperscaler AI Capex

### Capital Expenditure by Company

| Company | 2024 | 2025 (Guide) | 2026 (Est.) |
|---------|------|-------------|-------------|
| Amazon (AWS) | ~$75B | ~$125B | >$150B |
| Google (Alphabet) | ~$50B | ~$85B | >$100B |
| Microsoft | ~$55B | ~$80B | >$100B |
| Meta | ~$35B | $66-72B | ~$100B |
| Oracle | ~$10B | ~$20B | ~$40B+ |
| **Total Big 5** | **~$256B** | **~$443B** | **>$600B** |

- **2026 total**: >$600B capex projected (+36% YoY), with ~75% ($450B) directly tied to AI infrastructure.
- Hyperscalers increasingly using debt markets to finance AI capex as it outpaces free cash flow.
- Every $1 of hyperscaler AI capex translates to roughly $0.50-0.60 flowing to semiconductor companies.

### Where the Money Goes

| Category | Est. Share of AI Capex |
|----------|----------------------|
| GPUs / AI Accelerators | ~40-50% |
| Networking Equipment | ~10-15% |
| Memory (HBM/DRAM) | ~10-15% |
| Power / Cooling / Construction | ~20-25% |
| Other (storage, software) | ~5-10% |

---

## Key Risks & Themes

### Bull Case Themes
1. **AI infrastructure spend is still early innings** — $600B in 2026 capex, with multi-year growth ahead.
2. **NVIDIA's moat is wider than perceived** — CUDA lock-in, annual architecture cadence, full-stack integration.
3. **HBM is a structural margin upgrade** for memory companies — 70% gross margins vs 30-40% for commodity DRAM.
4. **Custom silicon growth benefits Broadcom, Marvell, ARM** regardless of NVIDIA's share trajectory.
5. **TSMC and ASML are monopoly/oligopoly infrastructure picks** — must-own for any AI chip thesis.

### Bear Case Risks
1. **Hyperscaler capex deceleration** — if AI ROI disappoints, capex could plateau or decline.
2. **NVIDIA margin compression** — custom silicon, AMD competition, and inference commoditization could pressure 73% gross margins.
3. **Export control whiplash** — unpredictable policy creates revenue uncertainty for NVIDIA, AMD, equipment makers.
4. **CoWoS / HBM supply glut post-2026** — capacity buildout could overshoot demand, collapsing pricing.
5. **Concentration risk** — top 5 hyperscalers represent the vast majority of AI chip demand. Any single pullback is material.
6. **Inference vs. training shift** — as AI matures, inference (lower-margin, more competitive) grows faster than training (NVIDIA-dominated). Could reduce NVIDIA's pricing power.

### Key Metrics to Monitor
- NVIDIA data center revenue growth rate (decelerating from +142% to +66% — watch for further slowdown)
- Hyperscaler capex guidance revisions (any cuts = sector-wide correction)
- Custom silicon adoption rate (Broadcom XPU customer count)
- HBM supply/demand balance (pricing trends, inventory levels)
- AMD MI400/MI450 adoption (ROCm maturity, hyperscaler wins)
- Intel 18A customer wins and IFS profitability timeline
- China export policy changes

---

## Valuation Snapshot (Feb 2026)

| Company | Ticker | Market Cap | FY Rev (Latest) | Rev Growth | P/E (Fwd) | Key Role |
|---------|--------|-----------|-----------------|------------|-----------|----------|
| NVIDIA | NVDA | ~$4.5T | ~$187B (TTM) | +65% | ~35-40x | GPU monopoly |
| AMD | AMD | ~$220B | ~$34B | +14% | ~35x | GPU #2, inference |
| Broadcom | AVGO | ~$1.1T | ~$56B | +44% | ~30x | Custom ASIC + networking |
| Marvell | MRVL | ~$95B | ~$7.5B | +45% | ~45x | Custom silicon + optics |
| Intel | INTC | ~$191B | ~$53.5B | -1% | ~22x | Foundry turnaround |
| ARM | ARM | ~$200B | ~$4.5B | +25% | ~70x | Architecture licensing |
| TSMC | TSM | ~$1.0T | ~$123B | +32% | ~22x | Foundry monopoly |
| ASML | ASML | ~$350B | EUR 32.7B | +20% | ~28x | EUV lithography monopoly |
| Micron | MU | ~$120B | ~$30B | +50% | ~15x | HBM / memory |

*Note: Valuations are approximate and change daily. Revenue figures use most recent fiscal year or TTM.*

---

## Summary Investment Framework

### Tier 1 — Core Holdings (Structural Winners)
- **NVIDIA (NVDA)**: Dominant position, CUDA moat, annual cadence. Expensive but justified by earnings power. Risk is deceleration, not displacement.
- **TSMC (TSM)**: Foundry monopoly. Every AI chip goes through TSMC. Reasonable valuation for irreplaceable asset.
- **Broadcom (AVGO)**: Best custom silicon play. Revenue doubling annually. Benefits from both NVIDIA dominance AND custom silicon growth.

### Tier 2 — High-Conviction Growth
- **Marvell (MRVL)**: Custom silicon + electro-optics. Smaller but faster growing. Celestial AI acquisition adds optical interconnect.
- **Micron (MU)**: Best US-listed HBM play. Cheapest valuation in the space. HBM structural margin upgrade.
- **ASML (ASML)**: EUV monopoly. Essential infrastructure. Steady growth but already well-valued.

### Tier 3 — Speculative / Turnaround
- **AMD (AMD)**: Gaining share but far behind NVIDIA. ROCm improving. MI400/MI450 cycle is key catalyst.
- **Intel (INTC)**: Deep turnaround play. CHIPS Act support, 18A node, IFS customers. High risk, high optionality.
- **ARM (ARM)**: Structural winner but extreme valuation. Any stumble gets punished.

# SaaS Disruption & Software Moat Vulnerability: Research Analysis

**Date**: 2026-02-23
**Source Paper**: CitriniResearch "2028 Global Intelligence Crisis" (Feb 2026)
**Analyst**: BigPic Capital Research
**Disclaimer**: Educational research only -- not investment advice.

---

## Executive Summary

The CitriniResearch paper's thesis that AI coding tools will enable enterprises to replicate SaaS products in-house, destroying software moats, is not a speculative future scenario -- it is actively unfolding. As of February 2026, the evidence base is surprisingly robust: 35% of enterprises have already replaced at least one SaaS tool with a custom build, the IGV software ETF is down 23% YTD, and major credit investors (Apollo, Partners Group) are actively reducing software loan exposure. The thesis timeline of 2026-2028 appears plausible for mid-market and long-tail SaaS; mission-critical platforms with deep data moats face slower but still meaningful erosion.

---

## Claim-by-Claim Assessment

### 1. Agentic Coding Tools Can Replicate Mid-Market SaaS Core Functionality in Weeks

**Verdict: CONFIRMED -- and the timeline may be even faster than claimed.**

**Key Evidence:**

- **CNBC Monday.com clone demonstration (Feb 2026)**: Two CNBC reporters with no coding background used Claude Code to build a functioning Monday.com replacement in under one hour, at a cost of approximately $5-15 in compute credits. Monday.com has a ~$4B market cap. The stock dropped sharply following the demonstration.
- **AI coding tool capabilities have reached agentic maturity**: Tools like Claude Code, Codex, Cursor, and GitHub Copilot are no longer limited to autocomplete -- they now function as autonomous agents that understand entire repositories, make multi-file changes, run tests, and iterate with minimal human input.
- **Claude Code revenue trajectory**: Launched publicly May 2025, hit $1B annualized revenue by November 2025, and reached $2.5B ARR by February 2026 -- indicating explosive enterprise adoption.
- **Developer adoption**: ~85% of developers regularly use AI coding tools by end of 2025; 90% of teams now use AI in workflows, up from 61% one year prior. A UC San Diego/Cornell survey found Claude Code, GitHub Copilot, and Cursor as the three most widely adopted platforms.
- **Productivity impact**: Academic research and enterprise case studies consistently show 26-55% productivity improvements, with experienced developers seeing the largest gains.
- **A Google engineer publicly stated** that one year of Google's work was done in an hour by Claude Code.

**Assessment**: The paper's claim of "weeks" may actually be conservative for core functionality replication. Demonstrations show hours for basic clones, though production-grade replacements with full edge-case handling, security, compliance, and integrations would still take weeks to months. The directional claim is sound.

---

### 2. Enterprise Procurement Using AI-Build Threats as Negotiation Leverage

**Verdict: STRONGLY SUPPORTED by early evidence.**

**Key Evidence:**

- **Retool 2026 Build vs. Buy Report** (817 enterprise respondents, published Feb 2026):
  - 35% of teams have already replaced at least one SaaS tool with a custom build
  - 78% expect to build more custom internal tools in 2026
  - 60% of builders have built something outside of IT oversight in the past year (shadow IT)
  - Enterprises can now build custom tools in days rather than months
- **CIO behavior shift**: CIOs are consolidating vendors, not expanding. The "best of breed" era is ending as companies reduce complexity and move toward platform consolidation.
- **IT budget reallocation**: IT budget growth is decelerating to 3.4% in 2026, with funds being actively redirected from application software to AI infrastructure. Hyperscalers alone will spend $470B+ on AI infrastructure in 2026.
- **Practical shadow IT**: 31% of shadow builders cited speed as the reason, 25% cited unmet needs, 18% said IT's process was too slow. This creates a credible "build it ourselves" threat that procurement teams can leverage.

**Assessment**: Even if enterprises do not follow through on building replacements, the credible threat of doing so fundamentally shifts negotiation dynamics. SaaS vendors must now compete not just against other vendors but against the customer's own engineering capability amplified by AI tools. This is a structural change in bargaining power.

---

### 3. ServiceNow-Style Reflexivity: Per-Seat Pricing Collapse from AI-Driven Workforce Reduction

**Verdict: CONFIRMED -- actively occurring.**

**Key Evidence:**

- **Seat compression is real and accelerating**: In late 2025, enterprises began reporting significant seat compression during contract renewals. Companies that once required 500 licenses found they could achieve the same output with only 50 licenses by deploying autonomous AI agents.
- **ServiceNow stock impact**: Despite strong Q4 results, ServiceNow's stock dropped 11.4% after management admitted that "agentic workflows" were complicating long-term visibility of seat-based growth. The stock has fallen 43% from recent highs.
- **Salesforce seat compression**: Same dynamic -- if 10 AI agents can do the work of 100 sales reps, companies do not need 100 Salesforce seats. Salesforce's forward P/E compressed from 31.67x (Jan 2025) to 15.02x (Feb 2026).
- **Broader market pricing it in**: The iShares Expanded Tech-Software Sector ETF (IGV) is down over 23% YTD in 2026. Software price-to-sales ratios compressed from 9x to 6x -- levels not seen since mid-2015.
- **The reflexivity loop**: The paper's key insight about reflexivity is playing out precisely: AI reduces headcount -> fewer seats needed -> revenue declines -> stock drops -> cost-cutting pressure -> more AI adoption -> more seat compression. This is a self-reinforcing cycle.

**Assessment**: The per-seat pricing model -- the bedrock of SaaS valuations for two decades -- is structurally broken. Companies are scrambling to transition to usage-based or outcome-based pricing, but this introduces revenue variability and uncertainty that the market is not comfortable with. The reflexivity dynamic identified in the paper is among its strongest and most observable claims.

---

### 4. Long-Tail SaaS (Monday.com, Zapier, Asana) Most Vulnerable

**Verdict: CONFIRMED -- with real-time evidence.**

**Key Evidence:**

- **Monday.com**: Stock at $75.58 (Feb 2026) with $4B market cap, down significantly. The CNBC clone demonstration was a pivotal moment -- AI built its core product in one hour for under $15.
- **Asana**: Stock at ~$12.20 (Nov 2025 data), having shed more than two-thirds of its value since its recent high. Revenue growth slowing to ~10% YoY despite being in a market that historically grew 20%+.
- **Zapier**: As a workflow automation tool, it faces direct threat from AI agents that can handle integration tasks natively. Retool's report identified workflow automations and internal admin tools as leading categories being replaced.
- **Category vulnerability pattern**: Companies whose value proposition is primarily "automation of a simple task" are most exposed. Smaller and mid-cap SaaS players with narrow functionality, low feature utilization, or weak lock-in face the highest AI substitution risk.

**Most vulnerable categories** (per Retool data):
1. Workflow automations
2. Internal admin tools
3. CRMs (at the simpler end)
4. BI/reporting tools
5. Project management
6. Customer support

**Assessment**: The paper's identification of long-tail SaaS as the primary kill zone is well-supported. These companies lack the deep data moats, mission-critical positioning, and ecosystem lock-in that protect larger platforms. Their products are often "thin wrappers" around relatively simple logic that AI can replicate easily.

---

### 5. Differentiation Collapse as AI Makes Feature Development Trivial

**Verdict: PARTIALLY CONFIRMED -- nuanced reality.**

**Key Evidence Supporting:**

- AI coding tools deliver 26-55% productivity improvements, meaning feature parity is achievable faster and cheaper than ever.
- The cost of validating an idea has collapsed. AI agents can research competitors, identify main features, and recreate them (as demonstrated in the CNBC experiment).
- Feature moats are weakening: AI erodes workflow integration stickiness by making it trivially easy to rebuild any software feature.
- SaaS moats based on product features alone are "real but weak" -- switching costs are low enough to optimize for best-in-class per use case.

**Key Evidence Complicating:**

- Data moats remain durable: Proprietary data, deeply embedded workflows, and mission-critical platforms retain structural advantages. As Klarna's CEO noted, as the cost of writing code approaches zero, switching costs of data will create moats for software companies.
- Enterprise-grade requirements are hard to clone: Security certifications (SOC 2, HIPAA), compliance frameworks, audit trails, SLAs, 24/7 support, and integration ecosystems take years to build, not hours.
- Network effects in true platforms (e.g., Salesforce's AppExchange ecosystem) create multi-sided value that a clone cannot replicate.

**Assessment**: The paper is correct that feature-level differentiation is collapsing, especially for single-function tools. However, it underestimates the durability of moats built on data, compliance, ecosystem, and organizational inertia. The differentiation collapse is real for the long tail but overstated for mission-critical enterprise platforms.

---

### 6. PE-Backed SaaS Companies with Leveraged Buyouts Most at Risk

**Verdict: STRONGLY CONFIRMED -- major credit risk emerging.**

**Key Evidence:**

- **Bloomberg reported (Feb 2026)**: Private equity's giant software bet has been upended by AI, creating a "Darwinian moment" that could reshape technology investing and trigger portfolio losses.
- **Leverage and valuation exposure**: Many PE-backed SaaS companies were acquired at 10-20x recurring revenue with significant leverage layered on top. These valuations assumed perpetual ARR growth that is now decelerating.
- **Default risk forecasts**: UBS analyst Matthew Mish anticipates a potential default wave in the $3.5T leveraged loan and private credit markets, with defaults potentially ranging from $75B to $120B in 2026.
- **Major investors reducing exposure**:
  - Apollo cut its direct lending funds' software exposure almost by half in 2025, from ~20% to below 10%
  - Partners Group actively reduced software exposure below industry average, exiting some positions early
- **Maturity wall**: ~30% of outstanding software loans mature by 2028 (vs. 22% for overall leveraged loans). 46% of software debt comes due within four years (vs. <35% for the broader universe).
- **Estimated damage**: By mid-February 2026, an estimated $1 trillion in total enterprise software value had been destroyed.

**Assessment**: This is potentially the most consequential claim in the paper. The combination of (a) leveraged capital structures, (b) assumed perpetual ARR growth, (c) accelerating revenue deceleration, and (d) a maturity wall creates classic conditions for a credit event. The paper's thesis that PE-backed SaaS represents the most acute financial risk is well-supported by current market data and investor behavior.

---

## Plausibility Assessment: 2026-2028 Timeline

| Component | Plausibility | Timeline |
|---|---|---|
| AI tool capability to replicate SaaS | Already happening | NOW |
| Long-tail SaaS revenue pressure | Early stages visible | 2026 |
| Seat compression at scale | Actively occurring | 2026 |
| Enterprise build-vs-buy shift | 35% already started | 2026-2027 |
| PE/credit stress in software loans | Early warning signs | 2026-2027 |
| Mission-critical SaaS disruption | Slower, but beginning | 2027-2028+ |
| Full pricing model transformation | In transition | 2027-2029 |

**Overall timeline assessment**: The paper's 2026-2028 window is realistic for the initial and middle phases of this disruption. The most vulnerable segments (long-tail SaaS, PE-backed software) are already showing stress. Mission-critical platforms will take longer but are not immune.

---

## Early Warning Indicators for Investors

1. **Net revenue retention (NRR) trends**: Watch for NRR declining below 100% at mid-market SaaS companies, indicating seat compression exceeding upsells.
2. **Contract renewal dynamics**: Monitor commentary on earnings calls about renewal rates, discount pressures, and contract term shortening.
3. **Retool/shadow IT adoption metrics**: The build-vs-buy ratio is a leading indicator. Currently at 35% replacement; watch for acceleration past 50%.
4. **Software loan default rates**: UBS forecasts $75-120B in defaults. Watch leveraged loan default rates in the software sector specifically.
5. **IGV ETF and software multiples**: P/S compression from 9x to 6x has already occurred; further compression to 3-4x would signal deep structural repricing.
6. **AI coding tool revenue growth**: Claude Code's trajectory ($0 -> $2.5B ARR in 9 months) is a proxy for the speed of disruption. Continued hypergrowth confirms the thesis.
7. **CIO survey data on vendor consolidation**: Gartner, Forrester, and Morgan Stanley CIO surveys tracking planned SaaS vendor count changes.
8. **Pricing model transitions**: Companies announcing shifts from per-seat to usage-based pricing are acknowledging the seat compression thesis.
9. **PE fund markdowns**: Watch for PE firms marking down software portfolio company valuations in quarterly reports.
10. **Headcount announcements at SaaS companies**: Layoffs at SaaS vendors are both a symptom of pressure and a signal that the market sees structural (not cyclical) decline.

---

## Counter-Arguments: Why the Thesis Could Be Wrong or Overstated

### 1. Maintenance Burden of Custom-Built Software
Building a clone in an hour is not the same as maintaining, securing, updating, and supporting it for years. Enterprises that replace SaaS with internal builds inherit all the operational burden -- bug fixes, security patches, compliance updates, user support. The total cost of ownership for custom software often exceeds SaaS subscription costs over a 3-5 year horizon.

### 2. Data Moats and Switching Costs Remain "Brutal" for Mission-Critical Systems
Software controlling proprietary data, embedded in business-critical workflows tied to risk and compliance (e.g., ERP, core financials, cybersecurity posture management), has dramatically high switching costs. Few CIOs will outsource payroll or enterprise security to AI-generated code. Vertical market software wins by being embedded so deeply that switching is risky, painful, and expensive.

### 3. Compliance, Security, and Enterprise-Grade Requirements
SOC 2, HIPAA, FedRAMP, GDPR compliance; audit trails; SLAs with financial penalties; 24/7 support; disaster recovery -- these take years and millions to build. An AI-generated clone does not come with these out of the box. Regulated industries (healthcare, finance, government) cannot simply swap in custom-built alternatives.

### 4. Network Effects in True Platforms
Salesforce's AppExchange, ServiceNow's partner ecosystem, and similar multi-sided platforms create value that a standalone clone cannot replicate. The AI can clone the product but not the ecosystem.

### 5. Enterprise Procurement Inertia
Large organizations move slowly. Budget cycles, procurement processes, IT governance, change management, training -- these institutional frictions mean even acknowledged superior alternatives take 12-24 months to evaluate, pilot, and deploy. This buys incumbents time to adapt.

### 6. SaaS Companies Are Adapting
Incumbents are not standing still. Salesforce's Agentforce ($500M+ ARR, growing several hundred percent YoY), ServiceNow's agentic workflow capabilities, and others are embedding AI to create new value. The survivors may transition to AI-native platforms that are harder to replicate. The SaaS winners of 2028 may look very different from today, but the category will not disappear.

### 7. AI-Generated Code Quality and Liability
For mission-critical applications, who is liable when AI-generated code fails? Enterprise legal and risk teams may resist replacing proven vendor solutions with AI-generated alternatives, especially for systems handling financial transactions, personal data, or safety-critical operations.

### 8. The "76% Buy" Statistic
Despite the build-vs-buy narrative, 76% of enterprise AI use cases are still purchased rather than built internally. Most enterprises lack the engineering capacity to maintain dozens of custom-built replacements, even with AI assistance.

---

## Key Data Points Summary

| Metric | Value | Source |
|---|---|---|
| Developers using AI coding tools | ~85% | Multiple surveys, end of 2025 |
| Teams using AI in workflows | 90% (up from 61% prior year) | Industry surveys |
| Claude Code ARR | $2.5B (Feb 2026) | Anthropic/industry reports |
| Enterprises that replaced SaaS with custom build | 35% | Retool 2026 Report (n=817) |
| Enterprises expecting to build more in 2026 | 78% | Retool 2026 Report |
| IGV ETF YTD decline | -23% | iShares, Feb 2026 |
| Software P/S multiple compression | 9x to 6x | Market data |
| Enterprise software value destroyed | ~$1 trillion | Market estimates, mid-Feb 2026 |
| ServiceNow stock decline | -43% from highs | Market data |
| Salesforce forward P/E compression | 31.67x to 15.02x | Market data (Jan 2025 to Feb 2026) |
| Median SaaS revenue growth | 12.2% (down from 21%) | First Analysis, Q4 2025 |
| UBS software loan default forecast | $75-120B in 2026 | UBS |
| Apollo software lending exposure reduction | Cut nearly in half | Bloomberg, Feb 2026 |
| Software loan maturities by 2028 | 30% of outstanding | Credit market data |
| Monday.com clone build time | <1 hour, ~$5-15 cost | CNBC demonstration |
| Seat compression example | 500 licenses to 50 | Enterprise renewal reports |
| Agentforce ARR (Salesforce) | $500M+, growing hundreds of % YoY | Salesforce Q3 FY2026 |
| IT budget growth 2026 | 3.4% (decelerating) | Gartner |
| Hyperscaler AI infrastructure spend 2026 | $470B+ | Industry estimates |

---

## Conclusion

The CitriniResearch paper's SaaS disruption thesis is among its strongest and most empirically grounded claims. The evidence is not anecdotal or speculative -- it is showing up in earnings calls, stock prices, credit markets, CIO surveys, and enterprise behavior data. The thesis has three layers of confirmation:

1. **Technological capability**: AI coding tools can already replicate mid-market SaaS functionality quickly and cheaply. This is demonstrated, not theoretical.

2. **Market behavior**: Enterprises are acting on this capability. 35% have already replaced at least one SaaS tool. CIOs are consolidating vendors. Procurement teams have new leverage.

3. **Financial repricing**: The market is repricing the entire software sector. $1T in value destroyed, credit investors fleeing, default forecasts rising, PE firms cutting exposure.

The key nuance the paper may underemphasize is the bifurcation between (a) long-tail, single-function SaaS which faces existential threat on the paper's timeline, and (b) mission-critical, data-rich enterprise platforms which face margin pressure and slower growth but retain structural advantages that will take longer to erode. Investors should treat these as fundamentally different risk profiles rather than applying a blanket "SaaS is dead" thesis.

The PE/credit dimension is the most underappreciated systemic risk. Leveraged buyouts predicated on perpetual ARR growth, meeting a maturity wall, in a structurally declining demand environment -- this has the ingredients for a credit event that extends beyond individual companies to broader financial markets.

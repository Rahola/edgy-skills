---
pdf_options:
  margin: 15mm 20mm 15mm 20mm
  headerTemplate: '<div></div>'
  footerTemplate: '<div style="font-size:8px;text-align:center;width:100%;color:#888;">Intersection Group — EDGY 23 Analysis | <span class="pageNumber"></span> / <span class="totalPages"></span></div>'
  displayHeaderFooter: true
---

<style>
  .edgy-badge { display: inline-block; padding: 3px 10px; font-weight: bold; font-size: 0.85em; color: #222; margin: 1px 2px; }
  /* Outcome = rounded pill */
  .edgy-purpose { background: #80ffb7; border-radius: 12px; }
  .edgy-capability { background: #a6c0ff; border-radius: 12px; }
  .edgy-task { background: #ff99bd; border-radius: 12px; }
  /* Activity = pentagon arrow (clip-path) */
  .edgy-story { background: #80ffb7; clip-path: polygon(0% 0%, 85% 0%, 100% 50%, 85% 100%, 0% 100%); padding-right: 18px; border-radius: 0; }
  .edgy-process { background: #a6c0ff; clip-path: polygon(0% 0%, 85% 0%, 100% 50%, 85% 100%, 0% 100%); padding-right: 18px; border-radius: 0; }
  .edgy-journey { background: #ff99bd; clip-path: polygon(0% 0%, 85% 0%, 100% 50%, 85% 100%, 0% 100%); padding-right: 18px; border-radius: 0; }
  /* Object = sharp rectangle */
  .edgy-content { background: #80ffb7; border-radius: 2px; }
  .edgy-asset { background: #a6c0ff; border-radius: 2px; }
  .edgy-channel { background: #ff99bd; border-radius: 2px; }
  .edgy-brand { background: #ffd580; border-radius: 2px; }
  .edgy-product { background: #e599ff; border-radius: 2px; }
  .edgy-organisation { background: #80eaff; border-radius: 2px; }
  .edgy-map { display: flex; flex-wrap: wrap; gap: 8px; margin: 12px 0; }
  .edgy-card { padding: 10px 14px; font-size: 0.9em; color: #222; flex: 1 1 200px; min-width: 180px; }
  .edgy-card b { display: block; margin-bottom: 4px; }
  .edgy-card.outcome { border-radius: 16px; }
  .edgy-card.activity { border-radius: 0; clip-path: polygon(0% 0%, 85% 0%, 100% 50%, 85% 100%, 0% 100%); padding-right: 30px; }
  .edgy-card.object { border-radius: 2px; }
  /* shape-tag removed — badge shape itself communicates base type */
  .edgy-section { border-left: 4px solid; padding-left: 12px; margin: 16px 0; }
  .edgy-section.identity { border-color: #80ffb7; }
  .edgy-section.architecture { border-color: #a6c0ff; }
  .edgy-section.experience { border-color: #ff99bd; }
  .edgy-section.intersection { border-color: #e599ff; }
  .edgy-rel { font-size: 0.85em; color: #555; font-style: italic; }
  .coherence-strong { background: #d4edda; padding: 4px 10px; border-radius: 4px; font-weight: bold; }
  .coherence-good { background: #fff3cd; padding: 4px 10px; border-radius: 4px; font-weight: bold; }
  .coherence-weak { background: #f8d7da; padding: 4px 10px; border-radius: 4px; font-weight: bold; }
  .legend { display: flex; flex-wrap: wrap; gap: 10px; margin: 14px 0 20px 0; padding: 12px 16px; background: #f8f9fa; border-radius: 8px; border: 1px solid #e0e0e0; font-size: 0.85em; }
  .legend-item { display: flex; align-items: center; gap: 6px; }
  .legend-dot { width: 16px; height: 16px; border-radius: 4px; display: inline-block; border: 1px solid rgba(0,0,0,0.1); }
  .meta-table { font-size: 0.9em; margin: 8px 0 16px 0; }
  .meta-table td { padding: 2px 12px 2px 0; vertical-align: top; }
  .meta-table td:first-child { font-weight: bold; color: #555; white-space: nowrap; }
</style>

# Intersection Group — EDGY 23 Enterprise Design Analysis

<table class="meta-table">
  <tr><td>Source:</td><td>intersection.group website, public materials, conference information, course descriptions</td></tr>
  <tr><td>Method:</td><td>EDGY 23 Enterprise Design in a Box framework</td></tr>
  <tr><td>Analyst:</td><td>Claude (AI-assisted analysis)</td></tr>
</table>

<div class="legend">
  <div class="legend-item"><span class="legend-dot" style="background:#80ffb7"></span> Identity (Purpose, Story, Content)</div>
  <div class="legend-item"><span class="legend-dot" style="background:#a6c0ff"></span> Architecture (Capability, Asset, Process)</div>
  <div class="legend-item"><span class="legend-dot" style="background:#ff99bd"></span> Experience (Task, Channel, Journey)</div>
  <div class="legend-item"><span class="legend-dot" style="background:#ffd580"></span> Brand</div>
  <div class="legend-item"><span class="legend-dot" style="background:#e599ff"></span> Product</div>
  <div class="legend-item"><span class="legend-dot" style="background:#80eaff"></span> Organisation</div>
</div>

<div style="font-size:0.8em; color:#666; margin: -10px 0 16px 0;">
  <b>Badge shape = base element type:</b>
  <span style="display:inline-block; background:#ddd; border-radius:12px; padding:2px 10px; margin:0 4px;">Outcome</span> rounded (Purpose, Capability, Task)
  <span style="display:inline-block; background:#ddd; clip-path:polygon(0% 0%, 80% 0%, 100% 50%, 80% 100%, 0% 100%); padding:2px 16px 2px 8px; margin:0 4px;">Activity</span> arrow (Story, Process, Journey)
  <span style="display:inline-block; background:#ddd; border-radius:2px; padding:2px 10px; margin:0 4px;">Object</span> rectangle (Content, Asset, Channel, intersections)
</div>

---

## 1. Executive Summary

Intersection Group is a not-for-profit association headquartered in Vienna, Austria, founded formally in 2020 with roots tracing back to Milan Guenther's 2012 book "Intersection: How Enterprise Design Bridges the Gap between Business, Technology, and People." The organisation curates and promotes EDGY, an open-source enterprise design language, and fosters a global community of 7,000+ practitioners spanning designers, architects, advisors, executives, and researchers.

The EDGY analysis reveals strong <span class="edgy-badge edgy-purpose">Identity</span>–<span class="edgy-badge edgy-capability">Architecture</span> coherence — Intersection's purpose of democratising enterprise design is directly realised through its open-source framework curation and community-building capabilities. However, the <span class="edgy-badge edgy-task">Experience</span> facet shows development areas: the journey from free community member to paying course participant lacks clear progression mechanics, and channel strategy relies heavily on conferences and online courses with limited always-on engagement touchpoints. The intersection elements reveal a tension between the not-for-profit mission and the need for sustainable revenue through paid offerings (€950 courses, conference tickets), creating a <span class="edgy-badge edgy-product">Product</span>–<span class="edgy-badge edgy-purpose">Identity</span> coherence gap that needs deliberate management.

---

## 2. Identity Facet — Why does Intersection Group exist?

<div class="edgy-section identity">

### <span class="edgy-badge edgy-purpose">Purpose</span>
**"Help people create better enterprises that dare, deliver and delight"**

Intersection Group exists to bridge the gap between traditionally siloed disciplines — enterprise architecture, service design, organisational design, and strategic management — into a unified practice called Enterprise Design. The purpose is explicitly transformational: not merely providing tools, but changing how people think about and design enterprises. This positions Intersection uniquely as a discipline-builder rather than a consultancy or tool vendor, with a meta-level ambition to reshape how entire industries approach organisational transformation.

### <span class="edgy-badge edgy-story">Story</span>
**"From a book to a global movement — building Enterprise Design as a discipline"**

The story begins with Milan Guenther's 2012 book that coined the term "Enterprise Design" and articulated the need for interdisciplinary integration. The first Intersection Conference in 2014 brought practitioners together, creating momentum that led to the formal establishment of Intersection Group as a not-for-profit association in 2020. The release of EDGY 23 in 2023 marked a pivotal milestone — transforming conceptual thinking into a concrete, open-source toolset. Now heading toward its 12th global conference (Intersection 26 in Montreal, October 2026), the story arc follows a classic movement pattern: idea → community → institution → methodology → global adoption.

### <span class="edgy-badge edgy-content">Content</span>
**"Open, interdisciplinary, and practitioner-driven communication"**

Intersection's content strategy centres on openness and accessibility — EDGY is free to use, documentation is publicly available, and the community welcomes diverse perspectives. The communication tone is approachable yet intellectually rigorous, exemplified by marketing like "So easy you could play with your mom" for the EDGY toolset. Content includes blog articles, the "Enterprise Design Patterns" book (35 patterns), webinar recordings, course materials, and conference presentations. The content philosophy explicitly avoids vendor lock-in messaging and proprietary gatekeeping.

**Strength:** <span class="edgy-badge edgy-content">Content</span> strongly expresses <span class="edgy-badge edgy-purpose">Purpose</span> — the open-source, community-driven communication approach directly embodies the mission of helping people create better enterprises through accessible tools and shared knowledge.

</div>

<div class="edgy-map">
  <div class="edgy-card outcome" style="background:#80ffb7">
    <b>&#9645; Purpose</b>
    Democratising Enterprise Design — bridging design, architecture, and strategy into a unified discipline
  </div>
  <div class="edgy-card activity" style="background:#80ffb7">
    <b>&#9655; Story</b>
    2012 book → 2014 conference → 2020 association → 2023 EDGY release → global movement
  </div>
  <div class="edgy-card object" style="background:#80ffb7">
    <b>&#9647; Content</b>
    Open docs, patterns book, webinars, conference talks — approachable yet rigorous
  </div>
</div>

---

## 3. Architecture Facet — How does Intersection Group operate?

<div class="edgy-section architecture">

### <span class="edgy-badge edgy-capability">Capability</span>
| Capability | Nature | Level |
|------------|--------|-------|
| Framework curation & methodology development | Differentiating, in-house | Core |
| Training & certification programme design | Differentiating, in-house | Core |
| Community building & chapter management | Differentiating, in-house | Core |
| Conference organisation & production | Differentiating, partially outsourced | Core |
| Publishing & content production | Commodity, in-house | Supporting |
| Digital tool vendor accreditation | Differentiating, in-house | Supporting |
| Partnership management (5 tracks) | Commodity, in-house | Supporting |

**Note:** Intersection's capability portfolio is tightly focused on its core mission — four of seven capabilities are differentiating and core. The concentration of differentiating capabilities in framework curation and education is appropriate for a methodology-driven organisation. Risk lies in the dependency on a small team for framework evolution — as a not-for-profit, attracting and retaining talent for methodology R&D is challenging.

### <span class="edgy-badge edgy-asset">Asset</span>
- **EDGY methodology and intellectual property** — The EDGY 23 framework, including the language specification, stencils, SVG shapes, PowerPoint templates, and documentation. Open-source but curated by Intersection, this is the organisation's primary strategic asset and the foundation of all other activities.
- **Global practitioner community (7,000+ members)** — The network of practitioners, local chapters (Montreal, Paris, Australia, Germany, UK), and the conference alumni base. This community is both a distribution channel and a co-creation resource for methodology evolution.
- **Intersection Conference brand** — 11 editions since 2014, the conference is the flagship event that anchors the community's annual rhythm and generates visibility, revenue, and practitioner engagement.
- **Training curriculum and certification system** — Structured courses (EDGY Enterprise Scan, EDGY Language Foundations) and the EDGY Practitioner certification, representing codified knowledge and a credentialing system.

### <span class="edgy-badge edgy-process">Process</span>
- **Open-source framework development** — Continuous curation and evolution of EDGY through community input, practitioner feedback, and core team refinement. Includes version management, documentation updates, and tooling integration.
- **Cohort-based training delivery** — Structured 4–6 week online courses with scheduled cohorts, combining self-paced learning with live sessions and peer interaction. Includes assessment and certification issuance.
- **Conference production cycle** — Annual cycle of call for contributions, speaker selection, programme design, venue management, and event execution across global locations.
- **Community chapter support** — Enabling and coordinating local community chapters through shared resources, brand guidelines, and networking support.

**Strength:** Processes realise capabilities coherently — the open-source development process directly supports framework curation, cohort-based training delivers the education capability, and conference production enables community building. The process architecture is lean and appropriate for a not-for-profit scale.

</div>

<div class="edgy-map">
  <div class="edgy-card outcome" style="background:#a6c0ff">
    <b>&#9645; Capability: Framework Curation</b>
    EDGY 23 language development and refinement (Core, Differentiating)
  </div>
  <div class="edgy-card outcome" style="background:#a6c0ff">
    <b>&#9645; Capability: Training</b>
    Course design and practitioner certification (Core, Differentiating)
  </div>
  <div class="edgy-card outcome" style="background:#a6c0ff">
    <b>&#9645; Capability: Community</b>
    7000+ practitioners, global chapters (Core, Differentiating)
  </div>
  <div class="edgy-card object" style="background:#a6c0ff">
    <b>&#9647; Asset: EDGY IP</b>
    Framework spec, stencils, templates, documentation
  </div>
  <div class="edgy-card object" style="background:#a6c0ff">
    <b>&#9647; Asset: Community</b>
    7000+ members in local chapters worldwide
  </div>
  <div class="edgy-card activity" style="background:#a6c0ff">
    <b>&#9655; Process: Open-Source Dev</b>
    Community-driven framework evolution
  </div>
  <div class="edgy-card activity" style="background:#a6c0ff">
    <b>&#9655; Process: Cohort Training</b>
    4–6 week online courses with certification
  </div>
</div>

---

## 4. Experience Facet — What role does Intersection Group play in people's lives?

<div class="edgy-section experience">

### <span class="edgy-badge edgy-task">Task</span>
1. **Learn Enterprise Design fundamentals** — Practitioners new to the discipline seeking to understand the EDGY framework and its application (individual practitioners, consultants)
2. **Obtain EDGY practitioner certification** — Professionals wanting to validate their enterprise design competence for career advancement or client credibility (consultants, in-house architects)
3. **Network with interdisciplinary peers** — Practitioners seeking to connect with others who work at the intersection of design, architecture, and strategy (all segments)
4. **Apply EDGY in real enterprise transformation projects** — Practitioners and enterprises needing practical guidance on using EDGY in actual engagements (enterprises, consultancies)
5. **Contribute to Enterprise Design as a discipline** — Experienced practitioners wanting to advance the field through research, pattern documentation, and community leadership (senior practitioners, academics)

### <span class="edgy-badge edgy-channel">Channel</span>
| Channel | Type | Role |
|---------|------|------|
| Website (intersection.group) | Digital, asynchronous | Primary information and onboarding gateway |
| Online courses (cohort-based) | Digital, synchronous + asynchronous | Core learning and certification delivery |
| Intersection Conference | Physical, synchronous | Flagship engagement, networking, and knowledge exchange |
| Local chapters | Physical + digital, synchronous | Ongoing peer engagement and practice sharing |
| Social media & blog | Digital, asynchronous | Awareness, thought leadership, community updates |
| Webinars | Digital, synchronous | Topic-specific deep dives and community engagement |

### <span class="edgy-badge edgy-journey">Journey</span>
</div>

<div style="display:flex; align-items:center; gap:0; margin:16px 0; flex-wrap:wrap;">
  <div style="background:#e8f5e9; border-radius:8px 0 0 8px; padding:10px 16px; text-align:center; font-size:0.9em; flex:1; min-width:100px;"><b>Discover</b><br><span style="font-size:0.8em; color:#555;">web / social</span></div>
  <div style="font-size:1.2em; color:#888;">&#10142;</div>
  <div style="background:#e8f5e9; padding:10px 16px; text-align:center; font-size:0.9em; flex:1; min-width:100px;"><b>Explore</b><br><span style="font-size:0.8em; color:#555;">free resources</span></div>
  <div style="font-size:1.2em; color:#888;">&#10142;</div>
  <div style="background:#fff3cd; padding:10px 16px; text-align:center; font-size:0.9em; flex:1; min-width:100px;"><b>Learn</b><br><span style="font-size:0.8em; color:#555;">paid courses</span></div>
  <div style="font-size:1.2em; color:#888;">&#10142;</div>
  <div style="background:#fff3cd; padding:10px 16px; text-align:center; font-size:0.9em; flex:1; min-width:100px;"><b>Certify</b><br><span style="font-size:0.8em; color:#555;">EDGY Practitioner</span></div>
  <div style="font-size:1.2em; color:#888;">&#10142;</div>
  <div style="background:#d4edda; padding:10px 16px; text-align:center; font-size:0.9em; flex:1; min-width:100px;"><b>Practice</b><br><span style="font-size:0.8em; color:#555;">apply in projects</span></div>
  <div style="font-size:1.2em; color:#888;">&#10142;</div>
  <div style="background:#d4edda; border-radius:0 8px 8px 0; padding:10px 16px; text-align:center; font-size:0.9em; flex:1; min-width:100px;"><b>Contribute</b><br><span style="font-size:0.8em; color:#555;">speak / write / lead</span></div>
</div>

**Strength:** The journey reflects the <span class="edgy-badge edgy-purpose">Purpose</span> well — it moves from consumption to contribution, embodying the community-driven, open philosophy. However, the transition from free exploration to paid learning (the monetisation gateway) could be smoother — the jump from free resources to €950 courses is significant without intermediate paid offerings.

<div class="edgy-map">
  <div class="edgy-card outcome" style="background:#ff99bd">
    <b>&#9645; Task: Learn</b>
    Understand EDGY framework and enterprise design fundamentals
  </div>
  <div class="edgy-card outcome" style="background:#ff99bd">
    <b>&#9645; Task: Certify</b>
    Validate competence as EDGY Practitioner
  </div>
  <div class="edgy-card outcome" style="background:#ff99bd">
    <b>&#9645; Task: Network</b>
    Connect with interdisciplinary peers globally
  </div>
  <div class="edgy-card outcome" style="background:#ff99bd">
    <b>&#9645; Task: Apply</b>
    Use EDGY in real transformation projects
  </div>
  <div class="edgy-card outcome" style="background:#ff99bd">
    <b>&#9645; Task: Contribute</b>
    Advance the discipline through research and leadership
  </div>
</div>

---

## 5. Intersection Elements — Bridges Between Facets

<div class="edgy-section intersection">

### <span class="edgy-badge edgy-organisation">Organisation</span> (Identity ↔ Architecture)

**Not-for-profit association with a lean global structure**

Intersection Group operates as a formally registered not-for-profit association headquartered in Vienna, with a distributed global presence through local community chapters. The organisational model is deliberately light — a small core team manages framework development, training, and conference production, while community chapters operate semi-autonomously.

- <span class="edgy-rel">pursues</span> <span class="edgy-badge edgy-purpose">Purpose</span> (democratising enterprise design through open-source tools and community)
- <span class="edgy-rel">has</span> <span class="edgy-badge edgy-capability">Capabilities</span> (framework curation, training, community building, conference production)
- <span class="edgy-rel">performs</span> <span class="edgy-badge edgy-process">Processes</span> (open-source development, cohort training, conference cycle, chapter support)
- <span class="edgy-rel">builds</span> <span class="edgy-badge edgy-brand">Brand</span> (positioning Enterprise Design as a legitimate, accessible discipline)

**Coherence:** <span class="coherence-good">Good</span> — The not-for-profit structure aligns well with the open-source, community-driven identity. However, the lean organisation creates capacity constraints — scaling training delivery, supporting more chapters, and evolving the framework simultaneously stretches a small team. The tension between mission-driven operation and financial sustainability is a structural challenge.

### <span class="edgy-badge edgy-product">Product</span> (Architecture ↔ Experience)

**EDGY toolset, training courses, conference, and publications**

The product portfolio spans:
- **EDGY toolset** (free) — the core methodology, stencils, templates
- **Training courses** (€950) — EDGY Enterprise Scan (4 weeks), Language Foundations (6 weeks)
- **Certification** — EDGY Practitioner credential
- **Intersection Conference** (paid) — annual flagship event
- **Publications** — "Enterprise Design Patterns" book and educational materials

- <span class="edgy-rel">serves</span> customer <span class="edgy-badge edgy-task">Tasks</span> (learning, certification, networking, application, contribution)
- <span class="edgy-rel">features in</span> <span class="edgy-badge edgy-journey">Journey</span> stages (explore: free toolset; learn: courses; certify: credential; practice: toolset + patterns; contribute: conference)

**Coherence:** <span class="coherence-good">Good</span> — Products cover the full customer journey from discovery to contribution. The free EDGY toolset serves the mission and creates a large funnel. However, the gap between free tools and €950 courses creates a revenue-model tension — there is no intermediate paid offering (e.g., self-paced course at €99–199, or premium community membership). The product portfolio would benefit from a "middle tier" that captures value from the large free user base.

### <span class="edgy-badge edgy-brand">Brand</span> (Identity ↔ Experience)

**"Enterprise Design" — an open discipline, not a proprietary methodology**

Intersection positions Enterprise Design as a discipline rather than a product — comparable to how "Agile" is a movement rather than a company's offering. The EDGY brand is deliberately non-proprietary: open-source, community-owned in spirit, with the Intersection Group as steward rather than gatekeeper.

- <span class="edgy-rel">represents</span> <span class="edgy-badge edgy-purpose">Purpose</span> (making enterprise design accessible to all)
- <span class="edgy-rel">evokes</span> <span class="edgy-badge edgy-story">Story</span> (the movement from siloed disciplines to integrated enterprise design)
- <span class="edgy-rel">supports</span> customer <span class="edgy-badge edgy-task">Tasks</span> (the brand signals credibility and community belonging for certified practitioners)

**Coherence:** <span class="coherence-strong">Strong</span> — The brand–experience alignment is excellent. The open, non-proprietary positioning matches the free toolset and community-driven experience. Practitioners feel they are joining a movement rather than buying a vendor product. This creates genuine loyalty and advocacy. The risk is commoditisation — if Enterprise Design becomes widely adopted, Intersection's role as steward may become less visible.

</div>

<div class="edgy-map">
  <div class="edgy-card" style="background:#80eaff">
    <b>&#9647; Organisation</b>
    Not-for-profit, Vienna HQ, global chapters — Coherence: <b>Good</b>
  </div>
  <div class="edgy-card object" style="background:#e599ff">
    <b>&#9647; Product</b>
    EDGY toolset (free) + courses (€950) + conference + publications — Coherence: <b>Good</b>
  </div>
  <div class="edgy-card object" style="background:#ffd580">
    <b>&#9647; Brand</b>
    Enterprise Design as open discipline, not proprietary methodology — Coherence: <b>Strong</b>
  </div>
</div>

---

## 6. Strengths

1. **Purpose–Architecture coherence:** Intersection's purpose of democratising enterprise design is directly and coherently realised through its open-source framework, free toolset, and community-building capabilities. There is no gap between what the organisation says it does and how it actually operates.

2. **Unique positioning as discipline-builder:** Unlike consultancies or tool vendors, Intersection occupies a rare niche as the steward of a discipline. This is strategically defensible — you cannot easily replicate a decade-long community and the credibility that comes from creating the methodology itself.

3. **Community as a self-reinforcing asset:** The 7,000+ member community is both a distribution channel, co-creation resource, and credibility engine. Practitioners who adopt EDGY become advocates, trainers, and contributors, creating a virtuous cycle that reduces marketing costs and increases content production.

4. **Open-source strategy creating trust and adoption:** By making EDGY free and open, Intersection removes the primary barrier to adoption. This builds trust, accelerates spread, and positions paid offerings (training, certification, conferences) as value-added services rather than gatekeeping mechanisms.

5. **Journey-to-contribution model:** The customer journey explicitly culminates in contribution (speaking, writing, leading chapters), which is unusual and powerful. This converts consumers into producers, extending the organisation's reach and capability far beyond its paid team.

---

## 7. Development Areas and Gaps

### 7.1 Revenue model fragility (<span class="edgy-badge edgy-product">Product</span>–<span class="edgy-badge edgy-purpose">Identity</span> tension)
The not-for-profit mission combined with an open-source core product creates a structural revenue challenge. The organisation depends on three revenue streams — courses (€950), conference tickets, and partnerships — with no recurring revenue model (e.g., subscriptions, membership tiers). This makes financial planning difficult and creates vulnerability to external shocks (conference cancellations, training demand fluctuations). The absence of a mid-tier product between free tools and €950 courses means a large portion of the 7,000+ community generates no revenue.

### 7.2 Scalability of training and certification (<span class="edgy-badge edgy-process">Process</span>–<span class="edgy-badge edgy-capability">Capability</span> constraint)
Cohort-based training (4–6 weeks with live sessions) is high-quality but inherently unscalable. Each cohort requires instructor time, and the small team limits the number of concurrent cohorts. The EDGY Champion programme (mentorship) adds further instructor load. Without self-paced or asynchronous training options, the organisation cannot serve demand growth without proportional team growth — problematic for a not-for-profit with limited hiring capacity.

### 7.3 Channel gaps in always-on engagement (<span class="edgy-badge edgy-channel">Channel</span> gap)
Between conferences (annual) and courses (periodic cohorts), there is limited always-on engagement infrastructure. Local chapters provide some continuity but are inconsistent in activity level. The organisation lacks a community platform (forum, Slack/Discord, practice groups) that would maintain engagement between events and courses. This creates a "feast or famine" engagement pattern where practitioners may drift away between touchpoints.

### 7.4 Framework evolution governance (<span class="edgy-badge edgy-process">Process</span>–<span class="edgy-badge edgy-organisation">Organisation</span> gap)
As EDGY gains adoption, the governance model for framework evolution becomes critical. Currently, the core team drives changes, but as the community grows, there is no visible open governance process (RFC process, community voting, versioning roadmap). This risks either stagnation (too slow to evolve) or fragmentation (unofficial forks and extensions). The open-source analogy suggests that a formal governance model is needed as adoption scales.

### 7.5 Geographic concentration risk (<span class="edgy-badge edgy-organisation">Organisation</span>–<span class="edgy-badge edgy-channel">Channel</span> gap)
Despite global aspirations, active chapters are concentrated in Europe (Paris, Germany, UK, Vienna) with limited presence in North America (Montreal) and Australia. Asia, Africa, and South America are underrepresented. For a discipline that claims to help design "better enterprises" globally, this geographic concentration limits both credibility and applicability to diverse enterprise contexts.

---

## 8. Recommendations

| # | Recommendation | EDGY Element | Priority |
|---|---------------|--------------|----------|
| 1 | Introduce a mid-tier paid offering (self-paced online course at €99–199 or premium community membership) to capture value from the free user base and create recurring revenue | <span class="edgy-badge edgy-product">Product</span> | **High** |
| 2 | Develop a self-paced asynchronous version of EDGY Language Foundations to complement cohort training and enable scalable delivery | <span class="edgy-badge edgy-process">Process</span> <span class="edgy-badge edgy-capability">Capability</span> | **High** |
| 3 | Launch a persistent community platform (forum or Slack/Discord) with practice groups, Q&A, and case-sharing to maintain engagement between events | <span class="edgy-badge edgy-channel">Channel</span> | **High** |
| 4 | Establish a public framework governance process (RFC mechanism, versioning roadmap, community advisory board) for EDGY evolution | <span class="edgy-badge edgy-process">Process</span> <span class="edgy-badge edgy-organisation">Organisation</span> | Medium |
| 5 | Develop a "train the trainer" programme at scale, enabling certified practitioners to deliver EDGY training independently (licensed model) | <span class="edgy-badge edgy-capability">Capability</span> <span class="edgy-badge edgy-product">Product</span> | Medium |
| 6 | Create regional expansion strategy targeting Asia-Pacific and Latin America with localised content and chapter seeding | <span class="edgy-badge edgy-organisation">Organisation</span> <span class="edgy-badge edgy-channel">Channel</span> | Medium |
| 7 | Publish annual "State of Enterprise Design" report leveraging community data to strengthen thought leadership and brand visibility | <span class="edgy-badge edgy-content">Content</span> <span class="edgy-badge edgy-brand">Brand</span> | Low |
| 8 | Develop digital tool vendor integration programme more actively to embed EDGY into enterprise software platforms | <span class="edgy-badge edgy-product">Product</span> <span class="edgy-badge edgy-asset">Asset</span> | Low |

---

## 9. Diagrams

The following EDGY 23 diagrams are delivered with this analysis (in draw.io format):

| File | Content |
|------|---------|
| `intersection-all-facets.drawio` | Top-level overview of all facets and intersection elements |
| `intersection-identity.drawio` | Detailed Identity facet map |
| `intersection-architecture.drawio` | Detailed Architecture facet map |
| `intersection-experience.drawio` | Detailed Experience facet map |

Diagrams follow the official EDGY 23 colour palette and element shapes. Open `.drawio` files in the draw.io application or at app.diagrams.net.

---

*Analysis based on publicly available information from intersection.group, course descriptions, conference materials, and community documentation. Internal organisational information may add depth especially to Architecture and Organisation elements.*

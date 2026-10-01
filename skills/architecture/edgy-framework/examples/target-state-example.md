# Target state: Acme Transit ticketing renewal (fictional worked example)

**Scope:** Acme Transit, ticketing and travel accounts · **Horizon:** 2028 · **Status:** hypothesis H1

This example shows the eight target-state artefacts at the length the skill
expects. Acme Transit is a fictional regional public-transport authority.

## 1 Purpose map (PUR-xx, OUT-xx)

Diagram: `purpose-map.drawio` (edgy-diagram `map_type: purpose`, see the
input *purpose-hierarchy-map.txt* among edgy-diagram's examples).

Mission PUR-01 *Sustainable everyday mobility* and vision PUR-02 *Most trusted
way to move in the region by 2030* sit on top. Focus areas PUR-11 *Seamless
travel chains*, PUR-12 *Affordable and fair fares* and PUR-13 *Zero-emission
fleet* are sub-purposes. KPIs are Outcomes: OUT-01 door-to-door time −15 %,
OUT-02 single ticket covers 95 % of trips, OUT-03 fare satisfaction ≥ 4.0,
OUT-04 CO2 per passenger-km −40 %.

## 2 Capability map and cards (CAP-xx)

Diagram: `capability-map.drawio` (`map_type: capability`, four areas, twelve
capabilities; first-round decision units highlighted: CAP-03, CAP-06).

### CAP-03 Travel account
**Area:** 1 Customer and identity · **Level:** 2 · **Nature:** differentiating · **Sourcing:** in-house
**What must be possible:** a passenger pays as they go and is charged the best fare afterwards, in every channel, independent of the ticketing supplier.
**Requirements:** R-1 one account across app, web and validators · R-2 best-fare capping per day and month · Q-1 charge visible within 10 s · Q-2 accessible (WCAG 2.2 AA)
**Data owned / master:** travel account and charges (master: this capability); customer identity (master: CAP-01)
**Current implementer(s):** none — card-based season tickets in AST-01 Legacy fare engine
**Change pressure:** contract for AST-01 ends 2027; open-loop payments expected by passengers
**Measured by:** OUT-02, OUT-03
**Guardrails:** G-3 one master per data set · G-5 open interfaces · G-7 no passenger lock-in to one channel

## 3 Guardrails (G-x)

| Id | Guardrail | Justified by |
|----|-----------|--------------|
| G-3 | Every data set has exactly one master | OUT-02 (one ticket needs one account) |
| G-5 | Open, documented interfaces; no supplier-private data formats | PUR-11 (travel chains across operators) |
| G-7 | A passenger is never locked into one channel | PUR-12, OUT-03 |

## 4 Building-block hypothesis (BB-xx)

Diagram: `reference-architecture.drawio` (`map_type: reference`, transition
overlay; see *reference-architecture-map.txt* among edgy-diagram's examples).

| Block | Covers capabilities | Guardrails tested | Outcomes served | Change | Open decision |
|-------|---------------------|-------------------|-----------------|--------|---------------|
| BB-02 Account-based ticketing platform | CAP-03, CAP-05, CAP-06 | G-3 ✓ G-5 ✓ G-7 ✓ | OUT-02, OUT-03 | new | — |
| BB-04 Open-loop payment gateway | CAP-03 | G-5 ✓ G-7 ? | OUT-03 | decide | ADR-004 |
| BB-01 Legacy fare engine | CAP-05 (until 2027) | G-5 ✗ | — | remove | — |
| BB-10 Integration bus | all L2–L4 | G-5 ✓ | OUT-01 | new | — |

## 5 Work packages (WP-xx)

### WP-02 Account-based ticketing platform
**Scope:** BB-02 from current (none) to target (in production for app and web) · **Outcome:** OUT-02
**Options:** A incumbent extends AST-01 · B re-tender, incumbent may bid · C new supplier via framework agreement · D shared service with neighbouring authority
**Dependencies:** WP-10 integration bus; ADR-004 · **Deadline:** contract end 2027-06 · **Decision by:** 2026-12

## 6 Decisions (ADR-xxx)

| Id | Decision | Status |
|----|----------|--------|
| ADR-001 | Account-based travel is the target model; card season tickets are migrated, not kept in parallel | decided |
| ADR-004 | Open-loop (bank card) payments: own gateway vs. payment service provider | open |

## 7 Role model

Diagram: `organisation-roles.drawio` (`map_type: organisation`, roles as
columns). Finding: the eight-person Platform team performs *define* and
*produce* for WP-02, WP-04 and WP-10 in the same half-year — three
simultaneous responsibilities; the load view is attached to the roadmap.

## 8 Summary for stakeholders

Diagram: `summary.drawio` (`map_type: summary`).

The capability map tells us what Acme Transit must be able to do regardless
of supplier; about ten building blocks say how we propose to do it; each work
package moves one block from today to the target and is measured by one KPI.
The first decision is the account-based ticketing platform (WP-02), because
the current fare engine's contract ends in 2027 and every other block depends
on the travel account. Open-loop payments remain an open decision (ADR-004)
until the gateway question is settled.

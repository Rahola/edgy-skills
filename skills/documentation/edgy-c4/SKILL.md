---
name: edgy-c4
version: "0.1.0"
description: >
  C4 model diagrams (Simon Brown) for one application of an EDGY architecture, as pages of an
  edgy-diagram delivery: the L1 system context derived from the EDGY document graph (Persons,
  partner systems) and L2 container pages written by hand, linked to the EDGY model by the
  application's id. A notation handler for edgy-diagram (extension contract 1): draw.io output,
  static shapes, rules C001–C006. Use it only for applications in a decided building block.
category: documentation
tags: [diagram, drawio, c4, software-architecture, documentation, edgy, en]
languages: [en]
agents:
  - claude-code
  - generic
requires: [edgy-diagram]
install: directory
inputs:
  - name: level
    type: enum
    values: [context, container]
    description: >
      context = L1 system context, derived from the EDGY graph; container = L2, from the
      containers and relationships written on the page.
  - name: system
    type: text
    description: The id of the application asset the page describes (e.g. APP-07)
outputs:
  - type: file
    description: C4 pages inside the edgy-diagram draw.io file (and its preview and presentation)
examples:
  - input: examples/c4-fare-engine.txt
    output: draw.io pages c4-context-app-07 and c4-container-app-07
---

# edgy-c4 — C4 for one application

## Purpose

C4 (Simon Brown, c4model.com, CC BY 4.0) describes the software of one system at zoom levels.
edgy-c4 draws **levels 1 and 2** for an application asset of an EDGY model. It is a *notation
handler* of edgy-diagram (`notation.json`, extension contract 1): a page with `notation: c4` is
drawn by `scripts/edgy_c4.py`, never by the EDGY parser, and its content never enters the EDGY
document graph. EDGY stays the model; C4 is one more view of one of its applications.

**When.** Only for applications in a *decided* building block (edgy-target-state): C4 describes
how a system is built, which is wasted on an application whose future is still open.

**Install.** edgy-c4 needs the whole skill directory and edgy-diagram (`requires:`). The
claude-code and generic adapters install both; Vibe, Cursor and curl mode install SKILL.md only
and refuse edgy-c4 with a message.

## Agent Instructions

1. Confirm the application is in a decided building block; otherwise propose the EDGY views only.
2. Make sure the EDGY model gives the application an id, its users (*interacts with* or
   *performs* → *requires*) and its *transfers* with data and technology.
3. Add an L1 page (`level: context`); add an L2 page (`level: container`) only when the
   containers are known — ask, never invent them. Name boundary crossings with `{container:}`.
4. Generate with edgy-diagram and `--preview --qa`, fix every C-rule error and warning, and look
   at every C4 page before delivery.

## L1 — system context (derived)

```text
  - name: "Fare engine — system context"
    notation: c4
    level: context
    system: APP-07
```

Or one page per application: `expand: per-application` with `notation: c4` and `level: context`.
The page is derived from the EDGY graph:

| C4 | From the EDGY model |
|----|---------------------|
| Software System (centre) | the application asset `system:` |
| Person | people / organisations that *interact with* it |
| Person, **inferred** (dashed, lighter) | people / organisations that *perform* a process that *requires* it — a stakeholder, not an observed user |
| Software System (partners) | the other end of its *transfers*; `[external]` ones grey |
| Relationship | the transfers: data names and `[technology]` |

A system without any Person is a **note** (the page still passes strict lint): add an
*interacts with* or *performs* link to the model when the users are known. Model elements
written on an L1 page (`- person: "Fare analyst" {id: PEO-02}`, `- system: … {id: APP-05}`) are
added to the derived ones; such a hand-written page must list its own `system:` (C005).

## L2 — containers (written on the page)

```text
  - name: "Fare engine — containers"
    notation: c4
    level: container
    system: APP-07
    elements:
      - container: "Fare API - Answers price queries" {id: C-FARE-API, technology: Kotlin}
      - container: "Fare rules store" {id: C-FARE-DB, technology: PostgreSQL}
    relationships:
      - "C-FARE-API" -> "C-FARE-DB": "reads and writes fare rules" {technology: JDBC}
```

- Container ids are unique in the document, follow the id pattern and are at most 64
  characters.
- Every relationship has a description and `{technology:}`.
- **Boundary crossings** come from the EDGY model: `{container: C-FARE-API}` on a *transfers*
  of the system names the container the transfer enters or leaves. A transfer between two
  decomposed applications names both: `{container: "C-WEB; C-FARE-API"}`. The key is inert on
  EDGY pages, in the ArchiMate export and in an EDGY-only delivery. In a delivery with C4 pages
  every `{container:}` must resolve (C001): for an L1-only delivery, add the L2 page or leave the
  keys out of the model.
- The L2 page links back to its L1 page, and the L1 system card links to its L2 page.

## Rules

| Rule | Severity | Checks |
|------|----------|--------|
| C001 | error | `{container:}` names an unknown or invalid container, or one of neither endpoint; an L2 relationship names an undeclared id |
| C002 | warning | a relationship without a description |
| C003 | warning | an L2 relationship (or boundary crossing) without a technology |
| C004 | error | `system:` is not an application asset, or is a platform / integration kind; `level:` is not `context` or `container` |
| C005 | warning | `system:` is not drawn on its hand-written L1 page |
| C006 | error | a container id declared twice, or two pages for the same level and system |
| C007 | error | a line of an `elements:` or `relationships:` section that cannot be read (a missing brace, a stray item) — never dropped silently |

An error stops the generator (exit 2, no file). C001 and C006 are checked in the notation
prepass over all C4 pages, so page order never matters.

## Output

draw.io only (C4-PlantUML is planned for 0.2.0). Static styled rectangles and the `person`
shape, `edgyNotation=c4` on every cell, page ids `c4-context-<system>` and
`c4-container-<system>`. Every page carries the legend **"C4 model (Simon Brown, CC BY 4.0)"**.
The native preview, the presenter and `edgy_lint.py` draw and check the pages through the
generic renderer; `--qa` and strict lint apply as for EDGY pages.

```bash
python3 <edgy-diagram>/scripts/edgy_generator.py examples/c4-fare-engine.txt --output c4.drawio --preview --qa
```

Look at the preview before delivery, as for every edgy-diagram page.

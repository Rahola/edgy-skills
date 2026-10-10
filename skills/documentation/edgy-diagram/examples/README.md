# Example inputs and expected outputs

Every `.txt` here is an input for `scripts/edgy_generator.py`; the matching
`expected-*.drawio` is what the current generator produces (regenerate after
generator changes with `bash tools/regen-examples.sh`, never edit by hand).
`check.sh` lints every expected file.

| Input | Expected output | Shows |
| `identity-facet.txt` | `expected-identity.drawio` | single facet with container, intersection elements below |
| `architecture-facet.txt` | `expected-architecture.drawio` | single facet |
| `experience-facet.txt` | `expected-experience.drawio` | single facet |
| `full-edgy-map.txt` | `expected-full-edgy.drawio` | facet: all — three containers, Organisation/Product between facets, Brand below |
| `activity-map.txt` | `expected-activity.drawio` | sequence |
| `process-map.txt` | `expected-process.drawio` | sequence |
| `outcome-map.txt` | `expected-outcome.drawio` | grid + tree |
| `asset-map.txt` | `expected-asset.drawio` | grid |
| `channel-map.txt` | `expected-channel.drawio` | grid |
| `content-map.txt` | `expected-content.drawio` | grid |
| `story-map.txt` | `expected-story.drawio` | grid |
| `people-map.txt` | `expected-people.drawio` | grid (person shape) |
| `task-map.txt` | `expected-task.drawio` | grid |
| `brand-map.txt` | `expected-brand.drawio` | hub-and-spoke |
| `product-map.txt` | `expected-product.drawio` | hub-and-spoke |
| `object-map.txt` | `expected-object.drawio` | hub-and-spoke |
| `purpose-map.txt` | `expected-purpose.drawio` | hub-and-spoke (PlantUML output too) |
| `purpose-map.txt` | `expected-purpose.puml` | hub-and-spoke (PlantUML output too) |
| `multipage-map.txt` | `expected-multipage.drawio` | `pages:` → two draw.io pages in one mxfile |
| `capability-areas-map.txt` | `expected-capability-areas.drawio` | `group:` area containers with ids and highlight |
| `channel-matrix-map.txt` | `expected-channel-matrix.drawio` | matrix `rows:` × `columns:` — official channel map 2 × 2 |
| `transition-roadmap-map.txt` | `expected-transition-roadmap.drawio` | roadmap (extension): waves × areas with the transition overlay |
| `product-portfolio-map.txt` | `expected-product-portfolio.drawio` | product map as a portfolio tree (`contains`) |
| `outcome-web-map.txt` | `expected-outcome-web.drawio` | outcome web: layered left → right by link direction |
| `capability-areas-nested-map.txt` | `expected-capability-areas-nested.drawio` | three tiers (area → sub-area → capability) with nested `group:`, `group_style: official`, 40 capabilities |
| `purpose-hierarchy-map.txt` | `expected-purpose-hierarchy.drawio` | purpose hierarchy with Outcomes |
| `organisation-roles-map.txt` | `expected-organisation-roles.drawio` | organisation role model |
| `transition-overlay.txt` | `expected-transition-overlay.drawio` | transition overlay strokes, relationship options |
| `triad-all-facets.txt` | `expected-triad-all-facets.drawio` | `map_type: triad` (extension) for `facet: all`: planned ring of 12 primaries with all 24 core links, "Further" panels, strip legend — 0 visual findings |
| `triad-architecture.txt` | `expected-triad-architecture.drawio` | `map_type: triad` for one facet: intersection A on top, three primaries as a triangle, intersection B below, panels for 19 further elements |
| `lanes-map.txt` | `expected-lanes.drawio` | `lane:` bands |
| `task-stakeholder-map.txt` | `expected-task-stakeholder.drawio` | `map_type: task` in two pages: stakeholder **inventory** (lanes × `stages:` columns, no edges) and **path** (tasks → journey / channels) |
| `reference-architecture-map.txt` | `expected-reference-architecture.drawio` | `reference` layout (extension) |
| `summary-map.txt` | `expected-summary.drawio` | `summary` layout (extension) |
| `archimate-positioned.txt` | `expected-archimate-positioned.drawio` | `layout_from:` positions from an ArchiMate view (`current-state.archimate`) |

Larger fictional inputs for the eval set are in `eval/`; `official/` holds the
Intersection Group example maps (CC BY-SA 4.0) used as layout references.

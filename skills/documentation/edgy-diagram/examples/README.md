# Example inputs and expected outputs

Every `.txt` here is an input for `scripts/edgy_generator.py`; the matching
`expected-*.drawio` is what the current generator produces (regenerate after
generator changes, never edit by hand). `check.sh` lints every expected file.

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
| `purpose-hierarchy-map.txt` | `expected-purpose-hierarchy.drawio` | purpose hierarchy with Outcomes |
| `organisation-roles-map.txt` | `expected-organisation-roles.drawio` | organisation role model |
| `transition-overlay.txt` | `expected-transition-overlay.drawio` | transition overlay strokes, relationship options |
| `lanes-map.txt` | `expected-lanes.drawio` | `lane:` bands |
| `reference-architecture-map.txt` | `expected-reference-architecture.drawio` | `reference` layout (extension) |
| `summary-map.txt` | `expected-summary.drawio` | `summary` layout (extension) |
| `archimate-positioned.txt` | `expected-archimate-positioned.drawio` | `layout_from:` positions from an ArchiMate view (`current-state.archimate`) |

Larger fictional inputs for the eval set are in `eval/`; `official/` holds the
Intersection Group example maps (CC BY-SA 4.0) used as layout references.

# Eval set

Fictional inputs that exercise the generator at the sizes real work needs.
`tools/edgy-eval.py` generates and lints each one and prints a metrics table;
`check.sh` runs it (`edgy-eval`) and fails on any lint error.

| Input | Exercises |
|-------|-----------|
| `large-capability-map.txt` | 9 area containers, 60 capabilities with ids |
| `large-reference-architecture.txt` | 4 lanes, 19 blocks, ~30 edges, transition overlay, actors and externals |
| `large-architecture-facet.txt` | 19 elements in one facet + 4 products + 1 organisation, 30 core links — the field case behind `docs/development-plan-2026-10.md` §2.1 (edges through boxes, labels on boxes, lint 0/0) |
| `fixture-f1-ports-waypoints.txt` | several edges on one side of a box with distributed ports and `via:` waypoints computed for the centre port; all four sides (F1: diagonal end segments) |
| `fixture-f2-labels.txt` | `label: source / middle / target` on three long edges (F2: renderer placed every label at the midpoint) |
| `fixture-f4-long-bold-title.txt` | long bold titles with descriptions, ids, tags and size classes in all three shapes (F4: constant-factor text metrics, bold inherited by descriptions) |
| `fixture-f5-purpose-tree.txt` | parent + 4 sub-purposes + 4 measuring Outcomes, a second level, mixed sizes (F5: parent over the leftmost child, branches through sibling boxes) |

The table printed by `edgy-eval.py` has two columns for these fixtures:
**H/W** (page height / width of the worst page) and **Visual** (count of the
visual rules W111–W114 — the same set `edgy_lint.py --visual` prints).
| `../multipage-map.txt` | two pages in one mxfile |
| `../full-edgy-map.txt` | all 12 elements with facet containers |
| `../purpose-hierarchy-map.txt` | purpose hierarchy with Outcomes |
| `../organisation-roles-map.txt` | role model |

Add an input here whenever a field problem is fixed, so it stays fixed.

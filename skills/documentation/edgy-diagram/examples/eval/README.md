# Eval set

Fictional inputs that exercise the generator at the sizes real work needs.
`tools/edgy-eval.py` generates and lints each one and prints a metrics table;
`check.sh` runs it (`edgy-eval`) and fails on any lint error.

| Input | Exercises |
|-------|-----------|
| `large-capability-map.txt` | 9 area containers, 60 capabilities with ids |
| `large-reference-architecture.txt` | 4 lanes, 19 blocks, ~30 edges, transition overlay, actors and externals |
| `../multipage-map.txt` | two pages in one mxfile |
| `../full-edgy-map.txt` | all 12 elements with facet containers |
| `../purpose-hierarchy-map.txt` | purpose hierarchy with Outcomes |
| `../organisation-roles-map.txt` | role model |

Add an input here whenever a field problem is fixed, so it stays fixed.

# Extension contract 1

What edgy-diagram (2.8.0 and later) publishes for code that builds on it
without patching it: a notation skill such as `edgy-c4` (v2.5.0), the
presenter effects (F6b), or a companion project. The graph/SVG/notation contract below is covered by `scripts/test_contract.py`,
which runs in `tools/check.sh`. The additive browser navigation API (§7) is
exercised by `tools/test-walkthrough.cjs`, separately required in CI. Breaking
changes must fail here rather than in an extension.

**Versioning.** The contract number is `1`. Adding an optional key, a new
`data-role` value or a new element type is compatible and keeps the number.
Removing or renaming anything listed below, or changing its meaning, raises
the number; extensions declare the number they were built for
(`notation.json` → `"contract": 1`) and are refused by a core with another
number (E013).

## 1. Style markers on draw.io cells

Every element cell the generator writes carries these keys in its `style`
(draw.io keeps unknown style keys when the file is edited):

| Key | Value | Meaning |
|-----|-------|---------|
| `edgyId` | model id: `[A-Za-z0-9][A-Za-z0-9._:/-]*` | the element this cell draws — the `{id:}` of the input, or a slug |
| `edgyIdSource` | `slug` (absent = explicit) | the id is `<type>:<name-slug>`; fine on a standalone page, **never** used to connect views |
| `edgyType` | one of the 16 EDGY element types | exact type (the linter prefers it over colour + shape) |
| `edgyKind` | `[a-z0-9-]+` | asset kind (`application`, `platform`, `integration`, `data`, …); absent when none |
| `edgyFacet` | `identity` \| `architecture` \| `experience` \| `intersection` \| `base` | facet of the type |
| `edgyOcc` | `<page id>/<cell id>` | this occurrence: the draw.io `<diagram id>` and the cell id |
| `edgyNotation` | `[a-z0-9-]+` | written by a notation handler on every cell of its page (§4); absent on EDGY cells |
| `edgyRole` | `badge`, `badge-key`, `header`, `chip`, `matrix` | decorations — not elements, never interactive |

Grammar of one style: `key=value;` pairs; values never contain `;` or `=`.
Edges carry no identity markers: their endpoints are the `source` / `target`
cells, whose `edgyId` names the model elements. An edge label's **first line**
is the verb; a second line (`<br>`, 9 px) carries data names and technology.

**Identity rules** (document graph, `scripts/edgy_graph.py`):

- the same id on several pages is one model element with several occurrences;
- the same id with another type or name on another page → **E014**;
- a duplicate id on one page → **E014**;
- a relationship whose endpoint is on no page → **E015** (dangling);
- a rename keeps the id; the model diff reports it as a rename.

## 2. Document graph JSON

`edgy_generator.py --graph out.json` writes, and `edgy_present.py` embeds, the
graph in the shape of `assets/edgy-graph.schema.json`:

```json
{"contract": 1,
 "elements": [{"id": "CAP-05", "id_source": "explicit", "type": "capability", "name": "Ticketing",
               "description": "…", "kind": null, "attributes": {}, "change": "keep", "tags": [],
               "occurrences": [{"page": "Capability map", "page_id": "capability-map", "cell": "7"}]}],
 "relationships": [{"source": "CAP-05", "target": "AST-02", "verb": "requires", "kind": "link",
                    "attributes": {"primary": true}, "page": "Model"}]}
```

`occurrences` lists drawn pages only (a `draw: false` model page has none);
`cell` is the draw.io cell id, so `page_id` + `cell` equals `edgyOcc`.

## 3. Native SVG (`edgy_render.page_to_svg`)

The SVG of one page groups what belongs together:

| Group | Attributes | Content |
|-------|-----------|---------|
| `<g class="el">` | `data-id` (model id), `data-occ`, `data-type`, `data-kind`, `data-facet`, `data-change`, `data-id-source` (`slug` only) | the shape and its label lines |
| `<g class="edge">` | `data-src`, `data-tgt` (model ids), `data-verb` (first label line, lower case), `data-kind` (`link` \| `flow` \| `tree` \| `influence`), `data-change` | the path and its label |
| `<g class="deco">` | `data-role` (`legend`, `badge`, `header`, `chip`, `matrix`, `container`, `lane`) | everything else |

Cells without `edgyId` (hand-drawn) are drawn but get no `data-id`: not
interactive. **Sanitising:** colours must match `#[0-9a-fA-F]{3,8}` or `none`,
numbers must parse as floats, anything else falls back to a default; every
text and attribute value is escaped. An SVG may be inlined into HTML as is.

## 4. Notation handlers

A page in another notation is drawn and validated by a handler: a skill with
a `notation.json` next to its `SKILL.md`:

```json
{"notation": "c4", "contract": 1, "module": "scripts/edgy_c4.py"}
```

The module may define:

```python
def generate_page(page_text: str, graph) -> str: ...      # mxGraphModel XML of one page
def lint_page(cells: dict, page_name: str) -> list: ...   # [(level, rule, message, cell_id)]
```

Optional additions in edgy-diagram 2.9.0, still `contract: 1` (a v2.4.0
handler keeps working unchanged):

```python
def generate_page(page_text, graph) -> (str, list): ...   # (xml, [(severity, rule, message, subject)])
def prepass(pages: list, graph) -> dict | (dict, list): ...  # every page of the notation, before any is drawn
def page_id(page_text: str, graph) -> str: ...            # a fixed draw.io page id, e.g. c4-context-app-07
```

- **Findings channel.** `severity` is `error`, `warning` or `note`. An
  error stops the run (exit 2, no file); a warning is printed and recorded
  in `qa.json`. A prepass finding may carry the page name as a fifth item.
- **Failures.** An exception in `generate_page` or `prepass` is one E013
  error naming the page (or the prepass) and the handler: exit 2, no file,
  no traceback.
- **Prepass and index.** `prepass([(page name, page text)], graph)` runs
  once per notation, before any of its pages is drawn; what it returns is
  `graph.notation_index[notation]` (pages by level and system, containers
  by id), so page order never matters.
- **Isolation.** The EDGY parser sees only the header keys of a
  `notation:` page (`notation`, `level`, `system`, `focus`, `title` …).
  Its body goes to the handler alone and never enters the document graph:
  no foreign elements or edges, no vocabulary warnings, no E014.
- **`expand:`** on a notation page calls the handler once per target, each
  page text starting with `focus: <id>`; without a handler it is E013 on
  one page, never an empty page per target.
- **Drawing.** A handler writes static styled cells (rectangles and the
  existing `person` shape). The preview, the presenter and the linter draw
  them through the generic renderer: there is no shape hook.

A TXT page says `notation: c4`; the handler writes `edgyNotation=c4` on every
cell. **Fail closed:** the EDGY rules E009, W102 and W105 are off only on the
cells of a registered *and installed* handler. An unknown notation, or a
known one whose handler is missing or cannot be loaded, is **E013** in the
generator and the linter — never a clean pass. EDGY and foreign cells on one
page are **E012**. Handlers are found in `$EDGY_NOTATION_PATH`, next to the
installed edgy-diagram skill, or in the repository (`scripts/edgy_notation.py`).

## 5. Entry points

| Function | Returns |
|----------|---------|
| `edgy_document.parse_document(text, with_graph=True)` | `([(page name, parser)], graph)` — the pages to draw and the document graph |
| `edgy_document.load_graph(text)` | the document graph (`edgy_graph.DocumentGraph`, `.to_json()`) |
| `edgy_render.page_to_svg(edgy_render.Page(model), title)` | SVG text of one page (§3) |
| `edgy_document.load_pages_from_file(path)` | `[(page name, mxGraphModel element)]` of a `.drawio` file |
| `edgy_notation.handlers()` | registered notation handlers |

Scripts of another skill find edgy-diagram with `$EDGY_DIAGRAM_SCRIPTS`, then
the installed sibling `<skills dir>/edgy-diagram/scripts`, then the
repository path (edgy-assessment `scripts/edgy_paths.py`).

## 6. Designed against two consumers

The contract was written for two consumers before it was frozen, so it is
not shaped by one of them:

| Need | edgy-c4 (v2.5.0) | Presenter effects (F6b) | Changed because of the second consumer |
|------|------------------|--------------------------|-----------------------------------------|
| Model ids | system / container ids across pages | cross-view highlight, morph | `edgyOcc` (page + cell) instead of an id alone: the presenter needs *where* an element is drawn, not only *which* it is |
| Graph | L1 context derivation | impact trace, counters on view cards | `occurrences` in the JSON; `kind` on relationships |
| SVG | C4 pages as static styled cells, drawn by the generic renderer (no shape hook) | `data-*` groups, decorations separated | `data-role` decorations, so effects never animate a legend or badge as if it were an element |
| Notation | `notation.json`, `generate_page`, `lint_page`, E012 / E013 | must ignore foreign pages it does not understand | `edgyNotation` on every foreign cell, so a consumer can skip a page without loading its handler |
| Change state | — | current ↔ target filter, later the paired-page morph | `data-change` on elements and edges; the paired-page morph (`{state: current \| target}`) stays outside contract 1 until F6b is built |

## 7. Composition navigation API 1 (edgy-diagram 2.10.0)

A standalone presentation or a **same-origin** embedding exposes
`window.EDGY_PRESENT` after its script loads. Await iframe `load`, check
`api.contract === 1`, then await `api.ready`. This is an additive navigation
seam over the existing five effects, not a sixth effect or a content platform.
No `postMessage`, network command listener or arbitrary script evaluation exists.
Cross-origin/sandboxed embeddings cannot access this API; link to the standalone
HTML instead. Keep the generated CSP; a srcdoc parent must permit its exact
script/style hashes and required local frame, never `unsafe-inline`.

| Member | Result / meaning |
|---|---|
| `contract` | `1` (navigation API version, independent of the graph contract). |
| `ready` | Promise of initial state after optional initial route settles. |
| `openElement(id)` | Promise<boolean>; open an explicit model ID's trace page, otherwise a drawn occurrence and inspector. Missing, malformed, slug-only or undrawn IDs return false without changing the view. IDs are data, not CSS selectors. |
| `navigate(route)` | Promise<boolean>; accepted routes below; malformed/unavailable targets return false and retain the view. |
| `back()` | Promise<boolean>; previous local route (including its change-state filter), false at start. Works even if native browser History is unavailable in srcdoc. |
| `getState()` | Fresh plain object `{contract, route, pageId, elementId, canGoBack, history}`; elementId is the inspected target, otherwise the trace focal ID, otherwise null; null page when absent; `history` is `browser` until a History call fails, then `local`. It is not an estimate of browser Back availability. |

### Which window owns the API?

The API belongs to the **generated atlas document**. Open generated atlas HTML
standalone and use `window.EDGY_PRESENT`. In a narrative that embeds the same
atlas in an iframe, use `frame.contentWindow.EDGY_PRESENT`; the parent narrative
window does not acquire the API automatically. Both forms are supported. Keep
cross-origin access restrictions intact.

For a single-file composition, embed the generated atlas HTML as local data and
set `frame.srcdoc` (as the fictional Acme fixture does). Attach the load handler
**before** setting srcdoc; await `api.ready`, then target an explicit ID. The
parent CSP must allow the exact embedded atlas script/style hashes, its own
script/style hashes, and the local frame. JSON-encode/escape embedded data; do
not interpolate arbitrary atlas text into a script literal. The repository's
`docs/examples/executive-walkthrough/build.py` shows hash generation and safe
base64 storage; it is a fixture reference, not an installed site engine.

- `openElement(id)` means "show this model element", choosing its trace or a
  drawn occurrence. Prefer it when the narrative knows the model ID.
- `navigate(route)` means "go to this explicit destination". A successful new
  destination records a navigation step; it does not mean return to a predecessor.
- `back()` follows the previously visited **local** navigation entry. Use it for
  an explicit in-frame Back button, not `navigate(previousGuess)`. It is distinct
  from browser `history.back()` and does not leave the atlas document.
- Repeated route strings retain distinct entry identities. Native Back/Forward
  synchronises the local cursor through namespaced `history.state.edgyNavigation`
  metadata; unrelated object state fields are preserved. A document-session
  marker prevents trusting stale cursors after reload. Srcdoc retains the same
  local predecessor semantics when native History is unavailable.
- Trace navigation restores the focal element's inspector, including Back and
  native history return. An explicitly targeted occurrence on another trace's
  page continues to identify that occurrence. Trace routes also carry an optional
  change-state query, so current/target filters survive local and native return.

Public command promises are serialised, so callers can submit several commands
without stale animations selecting the wrong element. Always await a command
before reading its settled state. Reopening the same target does not add a
history step. Explicit local Back does not call browser `history.back()`.
Browser Back/Forward still work in standalone HTML; in opaque local srcdoc
origins they may not. Put a clearly labelled in-composition Back button next to
the frame. Returning to the narrative is the composition's job: save section,
selection and focus independently of atlas history.

Routes (IDs are encoded with `encodeURIComponent`):

- `#/` — all views;
- `#/view/<page-id>` or `#/view/<page-id>/<element-id>`;
- optionally `?state=current` or `?state=target` on a view or trace route;
- `#/trace` or `#/trace/<element-id>[/<element-id>…]`, optionally `/+above`
  or `/+below` for an available list page.

Use exported `page_id`/model IDs; do not guess slugs. A view's element target
must actually occur on that view. A trace route must name available trace pages.
For initial srcdoc routing, set `data-edgy-start` on the embedded document's
`<html>` before loading (HTML-escape the attribute). A standalone fragment takes
precedence. Invalid initial routes leave the wall visible. Alternatively call
`openElement` after load, which needs no knowledge of page IDs.

```js
frame.addEventListener('load', async () => {
  const api = frame.contentWindow.EDGY_PRESENT;
  if (!api || api.contract !== 1) return; // show an honest unsupported message
  await api.ready;
  const opened = await api.openElement('CAP-02');
  // If false, tell the reader the target is absent; do not imply a successful drill.
});
```

For example, after generating `atlasHTML` with the normal presenter pipeline:

```js
// These listeners are in the narrative's hash-pinned script.
const frame = document.querySelector('iframe');
let atlasReady;
atlasReady = new Promise((resolve, reject) => {
  frame.addEventListener('load', () => {
    const api = frame.contentWindow.EDGY_PRESENT;
    if (!api || api.contract !== 1) return reject(new Error('Unsupported atlas'));
    api.ready.then(() => resolve(api), reject);
  }, {once: true});
});
frame.srcdoc = atlasHTML; // generated HTML, embedded safely with the required CSP hashes
exploreButton.addEventListener('click', async () => {
  const api = await atlasReady;
  if (!await api.openElement('CAP-02')) showUnavailableMessage();
});
atlasBackButton.addEventListener('click', async () => {
  await (await atlasReady).back();
});
```

The composition supplies `atlasHTML`, controls and its own unavailable-message
UI; this example is not a new rendering or content-manifest API. If the atlas is
opened standalone, simply await `window.EDGY_PRESENT.ready` in that atlas context.

The exported graph, SVG attributes (§2–3) and generated atlas remain the shared
source. Explicit model IDs connect views and survive a rename. A fallback slug
is not a cross-view identity. This contract does **not** promise permanent website
URLs, published-version archives, ID migrations, approval workflows or source
freshness. External platforms own those concerns. API/graph breaking changes need
versioned contracts; additions must preserve existing consumers and tests.

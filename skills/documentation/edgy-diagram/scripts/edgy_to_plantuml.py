#!/usr/bin/env python3
"""EDGY -> PlantUML emitter.

Converts an EDGYParser instance into a PlantUML source file that uses the
`<edgy/edgy>` stdlib library (https://plantuml.com/stdlib).

Element types map 1:1 to EDGY-lib macros. Relationship verbs are classified
via EDGY_CORE_LINKS / FLOW_RELATIONSHIPS / TREE_RELATIONSHIPS (reused from
edgy_parser) into `$link`, `$flow`, `$tree`, or `influence` (dashed open
arrow — rendered as raw PlantUML since <edgy/edgy> has no $influence macro).
"""

from edgy_parser import (
    EDGY_CORE_LINKS,
    FLOW_RELATIONSHIPS,
    TREE_RELATIONSHIPS,
    ALL_ELEMENT_TYPES,
)


def _escape(text: str) -> str:
    return text.replace('"', '\\"')


def _classify(label: str) -> str:
    label_lower = label.lower().strip()
    if label_lower in FLOW_RELATIONSHIPS:
        return 'flow'
    if label_lower in TREE_RELATIONSHIPS:
        return 'tree'
    if label_lower in EDGY_CORE_LINKS:
        return 'link'
    return 'influence'  # ohjaa/mahdollistaa — katkoviiva, avoin nuoli


_LEGEND = '''\
legend right
  **EDGY 23 — Elements**
  <back:#80ffb7> Identity (Purpose, Story, Content) </back>
  <back:#a6c0ff> Architecture (Capability, Asset, Process) </back>
  <back:#ff99bd> Experience (Task, Channel, Journey) </back>
  <back:#ffd580> Brand </back>
  <back:#e599ff> Product </back>
  <back:#80eaff> Organisation </back>
  --
  **Relationship types**
  --> Link (core link, 24 official)
  ->> Flow (data/value transfer)
  --- Tree (hierarchy, no arrow)
  -[dashed]-> Influence (guides/enables)
endlegend'''


def generate_plantuml(parser) -> str:
    """Render parsed EDGY model as PlantUML source using <edgy/edgy>."""
    lines = ['@startuml', '!include <edgy/edgy>', '']

    for element_id, element in parser.elements.items():
        etype = element['type']
        value = _escape(element['value'])
        if etype not in ALL_ELEMENT_TYPES:
            lines.append(f'rectangle "{value}" as {element_id}')
            continue
        lines.append(f'${etype}("{value}", {element_id})')

    if parser.relationships:
        lines.append('')

    for rel in parser.relationships:
        kind = rel.get('kind') or _classify(rel['label'])
        label = _escape(rel['label'])
        if kind == 'influence':
            lines.append(f'{rel["source"]} -[dashed]-> {rel["target"]} : {label}')
        else:
            lines.append(f'${kind}({rel["source"]}, {rel["target"]}, "{label}")')

    lines.append('')
    lines.append(_LEGEND)
    lines.append('')
    lines.append('@enduml')
    return '\n'.join(lines) + '\n'

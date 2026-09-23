# Authorized project-local physical tap source

The owner authorized a separately versioned source variant based on verified
physical tap dimensions, followed by validation. The pinned IHP models,
rules and original CDL/SPICE views remain unchanged. Explicit bulk VSS and
signal interfaces remain held. This is a design-source change, not a reader
normalization or waiver. No extracted parameter is used as a golden value.

First audit raw native active, implant, well, substrate and exclusion geometry
with integer-DBU polygon arithmetic. Identify each source tap by cell,
hierarchy path, TIE/WELL connections and unique owned geometry. Preserve
unresolved or overlapping ownership instead of assigning shapes by desired
area. Enumerate polygon hulls/holes, exact area and boundary perimeter;
separately classify rectangles, rectangular rings and other shapes. Bind
all current native instances and the source-only current-digital successor.

Electrical interpretation is a separate gate. The pinned rectangle symbol
uses area and single total perimeter in conductance, whereas the ring symbol
uses twice its already-total perimeter. Original supplied SPI resistances
remain a control. Do not infer arbitrary-shape applicability, select a formula
to obtain LVS, modify cards, or confuse dimension matching with electrical,
power-sequencing or ESD qualification. Coordinate the independently justified
electrical variant with the sequencing worker before affected simulation.

Required controls include exact reconstruction/reversal; unchanged non-tap
device/model/terminal records; per-tap one-to-one geometry ownership;
coordinate/implant/net-swap negative controls; independent dimension
arithmetic; original strict failures retained; and unchanged-deck strict
fullchip comparison with current digital source. All are initially **not run**.
Model/rule edits and remote upstream writes are **not applicable** here.

Primary pinned semantics:

- [General layer and tap marker derivation](https://raw.githubusercontent.com/IHP-GmbH/IHP-Open-PDK/84374023ee8b4b126bebbba67fcbada0a9c0ff0b/ihp-sg13g2/libs.tech/klayout/tech/lvs/rule_decks/general_derivations.lvs)
- [Tap geometry exclusions](https://raw.githubusercontent.com/IHP-GmbH/IHP-Open-PDK/84374023ee8b4b126bebbba67fcbada0a9c0ff0b/ihp-sg13g2/libs.tech/klayout/tech/lvs/rule_decks/tap_derivations.lvs)
- [Unmodified tap connection semantics](https://raw.githubusercontent.com/IHP-GmbH/IHP-Open-PDK/84374023ee8b4b126bebbba67fcbada0a9c0ff0b/ihp-sg13g2/libs.tech/klayout/tech/lvs/rule_decks/tap_connections.lvs)

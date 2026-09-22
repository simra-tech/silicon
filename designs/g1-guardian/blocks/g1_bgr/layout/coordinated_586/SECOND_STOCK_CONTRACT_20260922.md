# Source-bound HBT contact and remaining MOS LVS gate

Five HBT prototypes cover all301 literal source586 HBTs, including the nine
already present all-ground dummies. Native Activ/GatPoly is unchanged and every
contact bbox is within its native+2µm reservation. Source C/B/E/substrate nodes
are preserved. Emitter-to-substrate returns use two Via1 cuts. No new dummy
devices are added to the golden source.

Run exactly five isolated HBT stock hard/recommended/off-grid/angle DRC and five
stock LVS checks, plus stock LVS for the six MOS prototypes not covered by the
first gate. All use unchanged pinned decks, normal tap extraction and strict
top ports. Each child is limited to180seconds, one CPU,0.15GiB batch allowance.
Require completed zero-marker DRC reports and explicit LVS success with every
cross-reference entry exactly Match, not MatchWithWarning. Inspect the previous
two MOS LVS databases against the same strict rule without rerunning them;
this is an additional check, not a retroactive change to their first contract.

No blanket exception for all-ground dummy simplification: report actual stock
cross-reference outcomes and retain any failure. Source-native emitter geometry
is independently bound to the original PCell, not inferred from a simplified
LVS result. These isolated results do not prove chip-scale substrate return,
guard-ring connectivity, R1 star routing, mismatch matching or full-macro fit.
Density, antenna, extracted simulation and production adoption are **not run**;
seed is **not applicable**. PDK84374023ee8b4b126bebbba67fcbada0a9c0ff0b,
KLayout0.30.9. Preserve all first-gate evidence and frozen inputs.

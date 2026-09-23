# Current-digital reference successor

This is a distinct source-only successor to the owner-authorized explicit-VSS
I/O reference. Replace only the `BEGIN_DIGITAL` source block with the exact
digital subcircuit already used in the strict native standalone comparison.
The original I/O libraries, explicit bulk derivative, tap models/A/P, top
instance records and all other macros remain byte-identical. No three-dummy
projection is implicit. Original references and failed comparisons remain.

Prospective controls: bind canonical functional Verilog `6181b988`, the
physical Verilog `4fd0b616`, source-mapped standalone reference `3cb199c1`
and its strict result. Independently prove every functional instance/pin/net
is retained in the physical view; separately inventory any physical-only
instances and their native library definitions. Reparse every replacement
record against physical Verilog. Restore only the already-declared digital
port spelling; require the original and new ordered 46-port interfaces to
agree under the existing reversible bus spelling convention. Prove exact
inverse replacement of the old source block and byte preservation of every
other source byte. Negative controls must reject a changed functional
connection, missing source instance, and swapped ordered interface.

Current geometry is the independently terminal-audited rerouted full-chip
`9a52cc71`; old `ae62bf68` comparison counts do not transfer. This preparation
does not extract geometry, alter rules/models or establish full-chip LVS.
Tap A/P interpretation and the independently recorded substrate/interface
limitations remain unresolved; no warning is promoted to a match.

Status: implementation/controls **not run**; final strict comparison **not
run**; model/rule modifications **not applicable**.

# Shared VDDA candidate: frozen geometry gates

The provisional10 mA total-pad target is an engineering layout-screen
assumption including the SENSE branch, not an operating limit or verified
worst-case load. Existing SENSE remains its own <=2 mA leaf; its narrow bridge
must not be the aggregate series path. BGR's branch remains1 mA exploratory.
No compact model, native primitive, logical port or existing PDN feeder changes.

The native-only screen r5 found a clear stepped M3 route after preserving
failed straight alternatives r1–r4. The own-pad collector is10 µm wide at
x1083.29–1093.29/y381.105–405.875 µm. A10.2 µm M3 bridge uses centerline
(1088.19,392.04)→(1072,392.04)→(1072,395.82)→(1053,395.82)→
(1053,401.5)→(1048,401.5). Full-width bends avoid alternating frozen lower
PDN landings. The left endpoint isx1046.1 µm, including the landing.

At(1048,401.5), arrays contain64 Via3,64 Via4,16 TopVia1 and4 TopVia2 cuts.
TM2 width2.2 µm reachesx1060, theny922, then the existing BGR handoff743.4/922.
There is no new cut through either east TM1 supply ring. Any same-VDDA contact
with the existing SENSE feed is a physical join, never a label-based union.

Freeze the accepted screen's exact integer polygon recipe before generation.
Independently rerun the finite9-rail/60-cut head ladder for10 µm collector and
392.04 µm feed center; the previous6 µm result is not inherited. Preserve its
ideal-window/lower-reference and missing2D/lower-stack limitations.

Build gates: exact parent GDS hash, native polygon/text additive saved XOR,
flattened seven-metal/six-cut physical verification, pad07/BGR/SENSE VDDA
join and VDD/VSS distinct. Required followups:148 individual new-cut removals,
isolated unchanged stock DRC, actual native-neighbor stock comparison, final
obstacle-aware signal routing and complete source-terminal accounting.
Via-only half-table capacities11.2 mA and worst one-cut10.5 mA are arithmetic,
not current-sharing proof. Wire/current crowding, full pad lower-stack
distribution, actual load partition, IR/EM/PVT and lifetime remain independent
unqualified gates; the105°C/11year table cannot certify125°C lifetime.

Generation is bounded to360 s/one CPU with0.25 GiB expected output growth.
No canonical adoption or rule/model modification is included.

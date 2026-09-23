# GATE core-rail feed candidate

This partial source-held overlay connects GATE `vdd` to core VDD and `vss` to
VSS. Analog `vdda` remains distinct and unpowered. It does not change the
held-off/unsafe-IO electrical assumptions or qualify a powered GATE output.
The actual parent remains r4 decap-PDN SHA256
`88e5911aeaa4f0ae9c3c4712f4f2430563affa32bae0fe6c6c48c142e9611bdb`.

Reserved VDD handoff is root TM1 `(750,546)`: native GATE M3 `(767.32,546)`
rises through 12 Via3 cuts, then follows a 1.10 µm M4 bridge west, 12 Via4
cuts and four TopVia1 cuts. Reserved VSS handoff is root TM1 `(774,600)`:
native M3 `(778.65,600)` follows a 2.20 µm M3 bridge, then 12 Via3, 12 Via4
and four TopVia1 cuts. No root conductor, native device or pin is moved.

Exploratory targets are VDD 1 mA and VSS 2 mA. These are not measured current
envelopes or qualified full-return bounds. Old integrated nominal sampled
peaks (VDD 0.684049 mA and VDDA 1.50611 mA) do not establish VSS partition,
coincident peak, current sharing, pulse lifetime or worst-case PVT behavior.

Prospective gates cover actual native/r4-PDN metal and via clearance, native
source-net ownership, saved polygon/text preservation, correct physical core
ring binding while VDDA remains separate, 56 one-cut removal tests, stock
isolated and complete-core checks, and frozen neighboring signal/feed context.
The long new bridges have half-table arithmetic capacities 1.10/2.20 mA;
via-only targets are 2.4 mA and at least 2.1 mA after any single cut loss.
The public table applies at 105°C for 11 years; 50% is only an engineering
target. Internal contacts, wire necks, IR/EM and 125°C lifetime are unqualified.

All candidate construction and checks are initially not run. No shared VDDA
bus, electrical adoption, full-chip LVS or complete field PEX is implied.

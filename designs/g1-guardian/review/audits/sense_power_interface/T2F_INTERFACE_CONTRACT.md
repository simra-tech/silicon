# T2F core-rail feed candidate

This partial additive candidate connects only source-bound T2F `vdd12` (core
VDD) and `vss` (VSS). Analog `vdd` (VDDA) remains separately unpowered. Native
geometry, source cards, all logical ports and root PDN shapes are held.

The actual r4 decap-PDN parent is SHA256
`88e5911aeaa4f0ae9c3c4712f4f2430563affa32bae0fe6c6c48c142e9611bdb`.
The VDD12 native M3 point `(1044,1047.6)` rises through 12 Via3 cuts to a
1.10 µm M4 bridge east to the reserved root VDD TM1 ring handoff
`(1061.92,1047.6)`, then through 12 Via4 and four TopVia1 cuts. M4 is chosen
so this bridge does not block a possible future VDDA M3 east escape.

Native T2F VSS at M3 `(1039.2,954.3)` rises through 12 Via3, 12 Via4 and four
TopVia1 cuts into the reserved root VSS TM1 handoff at the same point. No
TopVia2 or shared VDDA trunk is created.

Prospective gates are exact actual native/PDN metal and cut clearance,
physical source-net ownership, no other-net capture, source polygon/text
preservation, saved connectivity to the correct rings, stock overlay and
native-context DRC, frozen neighboring feed/signal context and all 56
single-cut removal tests. T2F VDDA must remain distinct from both core rings.
No canonical or electrical adoption is implied by partial power geometry.

The 1 mA target is exploratory for each implemented branch; it is not a
qualified full T2F return-current bound. VSS eventually includes analog VDDA
return as well as VDD12 current. The rounded final586 VDD12 mean (up to
0.329860 µA in the recorded nominal-process temperature controls) is not a
peak/PVT bound. The combined BGR+T2F VDDA means do not isolate T2F and may not
be summed with another BGR value.

New M4 bridge half-table capacity is 1.10 mA; ideal-sharing via-only targets
are 2.4 mA, at least 2.1 mA after any one cut loss. The table applies at
105°C/11 years and 50% is an engineering target, not foundry derating.
Internal native wire/contact division, current crowding, full return load,
IR, EM, 125°C lifetime and actual VDDA distribution remain unqualified.

Construction and all candidate checks are initially not run. Failures are
retained; no model/deck, root-spine or native-source changes are permitted.

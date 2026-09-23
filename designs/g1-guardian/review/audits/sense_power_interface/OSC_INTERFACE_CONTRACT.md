# OSC native power-interface candidate

The oscillator VDD pin belongs to core VDD, not VDDA. The source-bound native
OSC point `(772,1089.57)` on M3 is routed west by a 1.10 µm M3 bridge to the
reserved root VDD TM1 handoff `(750,1089.57)`. Native OSC VSS at M3 `(774,954)`
is stacked directly into the reserved root VSS TM1 handoff at that point.
Each stack proposes 12 Via3, 12 Via4 and four TopVia1 cuts. No TopVia2 or TM2
is added, including near the north TM2 VSS ring at y1071.3–1086.3.

The parent is actual decap-PDN r4 SHA256
`88e5911aeaa4f0ae9c3c4712f4f2430563affa32bae0fe6c6c48c142e9611bdb`.
Its main and maximal stock DRC now passed with zero markers. Native source,
device geometry, port annotations and all existing PDN shapes are held.
The generic builder is `build_bgr_interface.py --macro osc`; its BGR r3
completed source snapshot and artifacts remain immutable in that run.

Prospective acceptance requires exact native net ownership, actual r4 metal
and cut clearance, saved native polygon/text preservation, both OSC supplies
connected only to their proper core rings, stock overlay and native-context
checks, and single-cut removal connectivity. Frozen signal/SENSE/BGR overlays
must be screened before integration. No canonical adoption follows from an
isolated candidate pass.

The branch target is 1 mA exploratory. Existing baseline OSC simulation
observed 110.682 µA mean and 400.665 µA sampled peak at nominal 27°C, code8,
ideal 1.2 V, during 2–5.8 µs. The separate immediate-clock receiver fixture's
20.517 mA peak is not OSC macro current. Neither value is a worst-case PVT
bound. Internal OSC wire/contact distribution and aggregate ring capacity
remain separate unqualified gates.

At the declared 50% engineering target against the PDK 105°C/11-year table,
the new M3 bridge carries 1.10 mA, lower via arrays 2.4 mA (2.2 after one cut
loss), and TopVia1 arrays 2.8 mA (2.1 after one cut loss). These are arithmetic
capacities with ideal sharing, not measured distribution or 125°C lifetime.
All construction/checks are initially not run; failures must remain recorded.

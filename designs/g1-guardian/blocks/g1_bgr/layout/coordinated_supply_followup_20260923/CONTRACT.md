# Source-held supply follow-up

Pinned runtime image:
`sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2`.
The runtime checks retain KLayout 0.30.9, ngspice 46 and public IHP PDK commit
`84374023ee8b4b126bebbba67fcbada0a9c0ff0b`. No rule deck or model card changes.

The previous conditional nominal result used the unchanged 1036-device source
and the `1f32630e` isolated geometry. It retained a simulated 13.253897 mV VREF
difference from its exact zero-resistance control; this is not accepted as a
qualified design result. The actual positive-edge network identifies supply
routing drops, rather than a reason to alter compact models or calibration.

## Isolated geometry and full-parent context

Three VDD M4 widening proposals fail actual foreign-metal/cut clearance and
are not implemented. Passed finite proposals add the following metal, in local
micrometres, without changing native devices, placement, footprint or nine ports:

- VDD M5 `[287,145.63,418.8,147.63]`.
- VSS M5 `[417.81,15.06,419.76,143.4]`.
- VDD M5 `[286,171.66,288,225.78]`, with two M4 landing pads centred at
  `(287,172.44)` and `(287,225)`, each 0.72 by 1.56, and eight Via4 cuts each.
  Cuts are 0.19 square on 0.42 pitch, with 0.055 enclosure.

The isolated candidate is
`e3ecfc6208fcae71c6b2f4223b7db3900677acfe30987b50ba6365c720297feb`.
Its local main/maximal DRC and strict LVS pass; all 336 source MOS junction
fields must also pass before a new numerical network is used.

The assembled context is independently held to
`ae62bf68aa001144c08a37c58ac3553c6e5f2013a6824b340218e84962066aca`.
Its original BGR placement is translation `(331,732)` with exact native geometry
and text parity to `6d86b9d4`. The upper VDD riser conflicts with ten generated
M5 fill squares. The original failure is retained. An isolated, explicitly
authorized context candidate excludes exactly those ten 67/22 rectangles at
global x618..622 and y900..904, repeated at 6 micrometre pitch through y954..958.
This removes 160 square micrometres from one 560-repetition fill array; its other
550 repetitions and all other fill remain. The cumulative BGR overlay is audited
separately, including the preceding DVBE improvements, with 733.166 square
micrometres of layer-summed addition.

Require forward/inverse all-layer XOR, unchanged functional hierarchy/text/ports,
saved-GDS reload parity, independently mapped 55 source nets, and actual full
parent foreign-metal/cut clearance. Evaluate ownership on the parent *before*
adding routes, so accidental captures cannot become self-justifying same-net
results. Include datatype22 material conservatively. Preserve the earlier
hierarchical-coordinate harness failure and its exact-flat recovery controls.
Run unchanged full-parent main, maximal, antenna and density checks, and actual
terminal connectivity. Separate source/model full-chip LVS failures are not waived.
No other fill removal, automatic regeneration or final integration is authorized
by this isolated experiment.

## Prospective conditional electrical checks

After the physical/source gates, recompute both unchanged LEF and KPEX positive
metal networks at the identical 3355 published attachment points. Require every
positive edge, all 55 components, source-device mapping and reconstruction.
Canonical source `586ffb58` remains 1036 devices and 329 historical capacitors.
The extraction reference remains 1027 extracted devices plus nine separately
proved grounded physical dummies, never a claim of 1036 extracted devices.

Exact zero-resistance parity must cover all 2842 parameters, 3885 raw fields and
original OP bytes before one matched nominal KPEX OP with a 600 second limit.
Use actual split-terminal voltages to map MOS direction. Save complete finite
node/terminal data and compare against the preceding collector and original
native diagnostics. Preserve exact maximum-principle failures without changing
tolerances. No automatic retry ladder or tuning is implied.

Published HBT M2 emitter planes are held. The fitted resistor native-M1 plane,
399 ideal resistor substrate terminals, historical capacitor attachment and
complete resistor external-field coverage remain unqualified. No compact-model
resistance is subtracted. Changed routing/fill changes capacitance; DC-only
results do not qualify startup, transient, stability, mismatch, PVT or final PEX.

Use the sole explicitly assigned CPU0 lease with a fresh 50%-availability gate
before every batch, the current coordinator budget floor, RAM/disk/inode and
growth reservations. Preserve each failed run and explicit not-run checks.

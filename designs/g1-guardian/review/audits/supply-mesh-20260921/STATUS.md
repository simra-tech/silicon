# Paused V18 supply-model work

The nominal top-metal network calculation completed. All 36 sampled macro
access points connect to the declared source interfaces, and all modeled
full-width segments are covered by the delivered GDS. These are model
construction checks, not loaded whole-chip IR compliance. Maximum linear
solve residual is 5.6844e-14 for the unit-current solutions.

The model covers TopMetal1/2 plus selected via arrays only. Sources are the
VDDA feed/mesh interface and VDD/VSS bottom core-ring points, not package or
bondpad voltage sources. Off-center vias are omitted (VDDA 0, VDD 91, VSS 59);
that simplification removes possible parallel connections. Stack resistance
at the mesh contact is reported separately. Internal macro/bar spreading,
IO-pad access, package/board/regulator resistance and temperature/process
resistance corners remain outside this calculation.

The optional jog estimate currently assumes 0.5 um width for Metal2; actual
VSS jogs are 0.55 um. LS rails are on Metal1, requiring an additional Via1
array at the pin (typically 4 ohm for five cuts), beyond the reported 14 ohm
stack at the stripe. Metal3 jogs still need their recorded widths applied:
T2F VSS 2.6 um, GATE VDD 0.5 um. Do not treat the current mesh/stack values as
complete loop resistance.

Aggregate current assignment, full DC headroom/current budget, dynamic
impedance sensitivity harness, package/decap model and loaded electrical
qualification are **not run**. Work paused at user request. Earlier
`supply-mesh-20260921-r1-incomplete` omitted implicit 1x1 vias and is retained
only as failed/incomplete model-development evidence; its values are superseded.

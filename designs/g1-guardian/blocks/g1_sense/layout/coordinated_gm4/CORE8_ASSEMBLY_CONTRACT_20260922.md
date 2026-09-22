# Next bounded assembly: eight large main-OTA MOS

Preparation only. Retain all completed buffer/stacked controls and failures.
This candidate combines the two logical stacked input devices with the six
large folded/current-mirror MOS at their exact r4 native positions. It excludes
the eleven smaller MOS, RZ and CC; those thirteen native shapes are obstacles,
not absent by assumption. Source, model, PDK and native W/L/ng stay unchanged.

The existing separate row substrate rings cannot be blindly superimposed:
their horizontal segments nearly overlap in the fixed inter-row gaps and may
create contact-spacing violations. Replace only the two stacked-pair added
p+ rings and their ring-attached ground escapes with one candidate core p+
ring, inner box `(1,4.5)-(229,114.5)`µm, and four contacted substrate strips
at y18.5,32.5,86.0,99.5µm. The native PCells, end dummies, pair NWell/body strips,
source/drain/gate routes and seven original trunk coordinates remain fixed.
All new p+ geometry is checked against every actual gate polygon, not exempted
from the native-channel invariant. Substrate conductor is general VSS, not a
precision shunt return. This is a new guard assembly requiring new stock checks.

For XM3/XM4 use exact native W320/L4/ng40 arrays; source-even strips connect
through top M1 rails, drain-odd strips through bottom M1 rails, and all gates
through bottom M2 bars. For XM14/XM11/XM15/XM12 use exact W384/L4/ng48 arrays
with the same physical source/drain convention. Preserve native junction
geometry and source defaults; no D/S parameter fitting. Place L4 poly-only end
dummies at0.20µm Activ separation; the candidate global ring lies beyond them.

The four large PMOS arrays share bulk VDD. Join their native NWell rectangles
inside `(9.11,34.38)-(220.89,84.12)`µm and add contacted n+ strips centered
y45.75,59.25,72.75µm between rows. These give symmetric body-tie locations,
but matching, substrate noise and finite body resistance remain unqualified.
Do not connect this well through either intervening NMOS row to the two input
pair wells. All VDD body strips receive explicit metal connections.

Extend the seven existing M3 trunks only as required by new same-net terminal
connections. Add six M3 trunks x6.8/8.0/9.2/10.4/11.6/12.8µm for
vbn/mir/vbpc/pc1/pc2/out1. Each local M1 rail joins M2, then only its declared
M2-to-M3 trunk via. Gate/drain/source exits use their distinct row heights.
Avoid interpreting touching labels as conductive connections. No lower-stage
routing or capacitor integration is implied by these temporary core ports.

After a fresh0.10GiB resource gate: exactly one CPU7 geometry process,180s,
4GiB memory reservation only. Save under a fresh ID and preserve any failure.
Require all400 real channels/408 diffusion strips, eight source-device
identities, native W/L/ng/default geometry and input centroids, no unintended
gate/Activ intersections, source-net terminal graph,5nm grid,230×164µm bounds,
and zero same-layer overlap with the other thirteen source-native devices.
Report200nm proximity separately from universal foundry spacing. Re-read the
saved GDS before acceptance. Stock DRC/LVS, density/antenna, full-main/SENSE,
new-layout PEX, intrinsic shared-junction applicability, matching/current/IR and
adoption remain **not run**. Seed **not applicable**. No automatic retry or
stock launch follows a preparation pass.

# One full 301-HBT fixed-position routing preparation

Scope: generate and independently audit one candidate, not stock verification
or analog qualification. Preserve the exact source586, fixed pack, all native
devices, nine dummies and all 50 macro replicated centroid records. Inputs and
tool identities are inherited by exact hashes from the completed two-contact
return controls and the completed 34-HBT pilot, not from mutable source names.
One CPU0 / 180 s / 4 GiB reservation / 0.20 GiB HOME preparation after a fresh
resource gate. Preserve any failure. No automatic second candidate or stock run.

## Source-exact contacts and terminals

301 native npn13G2 units retain their fixed native origins and original
`we=0.07u le=0.9u Nx=1 m=1` source cards. The 192 DVBE-emitter and 24
VD2-emitter units use original contact prototypes03/04. Nine all-ground dummies
use original prototype00 unchanged. The 76 functional VSS emitters use the
passed separated-return controls01/02. Only contact01's observed text names
are mapped from representative VBE to actual VBE3 for XQ60 and VD2 for XQ62;
all polygons and native cells remain exact. The source CDL retains all 301
original source terminal tuples and eight electrical nets.

Every C/B/E/substrate seed (1204 incidences) and eight ports is audited through
actual M1/M2/M3/M4 and Via1/Via2/Via3, without text-driven joins. All additional
transitions use two 0.19 µm cuts at 0.42 µm pitch with 0.055 µm enclosure;
horizontal landings are 0.72 × 0.30 µm. Distinct collector Via1 arrays use
vertical 0.30 × 0.72 µm landings, preserving the passed worst-row remedy.
Via3 stock acceptance of this candidate is not run.

## Explicit row/channel assignment

Move all 76 functional grounded-emitter collections to M4 inside their native
row bodies. This removes the extra return roles from the failed 4.4-in-4.0 µm
inter-row extrapolation. Local E access stays M2, then a two-cut Via2/Via3
stack joins the M4 row branch. XQ56, XQ60 and XQ67 branches lie at the native
origin Y; XQ62 lies at origin Y+1.2 µm. Only XQ62 coexists with other grounded
emitter families in a row; the 1.2 µm separation allows 0.8 µm branches with
0.4 µm edge spacing. Distinct-C/B XQ67 uses origin Y, avoiding its collector
landing at Y+1.5. XQ62 is diode-connected and has no distinct collector landing.

| Inter-row owner | M3 centers relative to lower row native top | Width |
| --- | --- | --- |
| Up to three distinct C / non-VSS-E roles, sorted | +0.15, +0.75, +1.35 µm | 0.30 µm |
| Lower-row general guard collector | +2.20 µm | 0.80 µm |
| Upper-row base roles, sorted from upper boundary down | +3.65, +3.05 µm | 0.30 µm |

This allocation has at least 0.30 µm between unlike adjacent M3 track edges.
It uses the absence of native M3 in the gap, not a claim of 0.30 µm clearance
to every lower-layer boundary. M2 stems / Via2 landings must independently
pass the physical component and added-route-to-other-role spacing checks.
Above-row E/C stems terminate below the guard and next-row base landings;
the previously problematic opposing stem / horizontal Via1 overlap is not
accepted merely because the M3 track count fits.

Seven non-VSS source-net trunks use M2 at x=190.8+1.1*i µm (i=0..6), sorted
source names. General VSS uses x=198.5 µm. Source-port escapes end at x=200.5
µm, outside all fixed MOS reservation rectangles. Four independent return
trunks use M2 x=1.2 (XQ56), 2.6 (XQ60), 4.0 (XQ67), 5.4 (XQ62), each 0.8 µm
wide. General guard VSS is carried left on M3 at y=134 µm, then down M2 x=7.2.
No return branch touches a native local guard before the declared star.

## One finite star, consistent with resistor-bank r2

The existing R1 precision/general join is x=16 µm, between M3 y=15.06 and
16.26 µm. XQ56 arrives on M4 at (16,16.26), through Via3 to the precision
point. The remaining branches reach a single general-star M3 hub
`x=13.2..17.6, y=14.66..15.46 µm`, using this noncrossing M4 staircase:

| Branch | Left trunk turn Y | Hub terminal X at Y=15.06 |
| --- | ---: | ---: |
| XQ60 | 15.06 | 13.6 |
| XQ67 | 13.86 | 14.8 |
| XQ62 | 12.66 | 16.0 |
| General guard / dummies | 11.46 | 17.2 |

Each M4 branch is 0.8 µm wide and has its own Via3 interface at the hub.
The precision M3 point and general hub share only the declared M2 x=16
segment between 15.06 and 16.26, with redundant Via2 at each end. This is a
finite metal region with shared impedance, not an ideal zero-impedance point.
No IR, matching, noise, startup or current-margin credit follows from topology.

Remove each of the five declared Via3 interfaces separately in an independent
metal extraction and require the entire selected return/guard tree to separate
from the hub while all other intended source connections remain. Remove all
five together and require five separate VSS route-role components plus the
star-port component. Retain all dummy/general local ties during these tests.
This rules out an unrecorded second return join in the generated bank.

## Independent preparation gates

Freeze hashes of source586, pack, five original HBT contacts, two revised
contacts/control receipt, all eight MOS contacts/manifest, and resistor-bank
r2 GDS/manifest. Validate source count/positions/centroids, native per-layer
copy XOR, exact controlled text map, 5 nm grid and macro bounds. Re-read saved
GDS for the final source-net graph and all five individual/all-interface cut
tests. Check every added conductor belongs to its declared physical role when
the star interfaces are cut; verify every cut has metal enclosure.

Check added routes and landings against other physical-role native/route
polygons with a 0.30 µm same-layer screen. Separately screen all 336 exact MOS
contact polygons and their reserved-native rectangles, plus the actual routed
399-resistor-bank r2 on M1–M4/Via1–Via3. The only declared resistor-bank
intersection exception is the intentional star interface rectangle
`x=13.0..18.2, y=14.4..16.8 µm`; report its intersections explicitly. No
unknown ring geometry is imported; do not claim upper-metal ring qualification.

| Check | Prospective status |
| --- | --- |
| Read-only new row-channel arithmetic | passed scoped planning; worst old demand failure retained |
| Full candidate source/native/terminal/grid/neighbor audits | not run |
| Stock DRC / strict LVS, density, antenna, full-macro integration | not run |
| PEX, analog, matched routing/current/noise/IR budgets | not run |
| Upper-metal ring assembly and future MOS routing | not run |
| Simulation seed | not applicable |

Generation may fail any gate. A generated candidate is not adopted and no
stock invocation is authorized until the root review of the actual audits.

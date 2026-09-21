# V18 supply resistance, current accounting and transient sensitivity

The latest nominal armed GATE/pad extension gives an incomplete subtotal of
**5.681 mW**, or **5.965 mW** with the stated digital clock scaling.
It still does not qualify whole-chip power or IR. Details of the later GATE
extension appear below; earlier partial accounting is retained for comparison.

The corrected geometric model connects all **36 sampled macro supply accesses**.
An incomplete near-room current sum gives **4.642 mW**, or **4.925 mW** with the
stated digital clock scaling. The conditional known-load DC drop bound reaches
**27.88 mV** at nominal resistance. These calculations do **not** establish
whole-chip power below 10 mW or loaded IR compliance: active GATE/TRIP, actual
IO loads, activity and reference interactions remain missing.

## Evidence and model scope

[Mesh r3](supply-mesh-20260921-r3/mesh.json) pins the delivered GDS, final assembly
DEF and macro/technology LEFs by SHA-256. Delivered GDS remains
`38c1d6d13bbfee4ed0e3c01477742c3d2d28317d9215d9e5bd9a35551285ae59`.
PDK commit is `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`; KLayout 0.30.9.
The model uses actual DEF top-metal route centerlines and widths, via-array
cut counts, and translated macro LEF supply pins. All modeled top-metal and
access-jog full widths are covered by GDS conductors. Linear solve residual
is at most `5.69e-14`; reciprocal transfer-resistance asymmetry is below
`1.56e-15`. These check the approximate resistor network, not complete PEX.

The technology LEF supplies nominal sheet resistance: TopMetal1 0.021,
TopMetal2 0.0145, Metal2–5 0.103 and Metal1 0.135 ohm/square. Via1–4 are
20 ohm/cut, TopVia1 4 and TopVia2 2.2. Omitted DEF ROWCOL means one cut,
not zero. Metal3-to-TopMetal1 access stacks contribute 10 ohm. The level
shifter Metal2 stack contributes 14 ohm plus its actual Metal1 pin Via1
array (4 ohm) and jog. Actual LS jog widths are 0.5 um on VDD/VDDA and
0.55 um on VSS; GATE VDD jog is 0.5 um; T2F VSS jog is 2.6 um.
The r3 model measures jog length to the actual pin or Via1 landing and
records shared LS stripe stacks explicitly.

Source interfaces are VDDA TopMetal1 (946.02,389.34), VDD TopMetal2
(395,354.66) and VSS TopMetal2 (507,334.66), in um. They are not package
pins. An additional approximate VDDA padbare-feed resistance of 1.630 ohm
uses parallel M4/M5, six TopVia1 cuts and 400-cut Via3/Via4 arrays. The small
M3 patch spreading, IO M2/Via2, bondpad/package/board/regulator are excluded.
The graph omits off-center parallel via connections (VDDA 0, VDD 91,
VSS 59); macro interiors and bar spreading are also excluded. These omissions
and centerline approximations prevent interpreting the result as a guaranteed
complete-chip resistance bound.

[Budget r1](supply-budget-20260921-r1/budget.json) gives each contact and both
parallel-mesh and single-path estimates. Selected parallel-mesh **supply plus
return** single-access estimates, including modeled access and VDDA feed:

| Macro | Rail | Calculated loop resistance |
|---|---|---:|
| BGR | VDDA | 27.23 ohm |
| SENSE | VDDA | 24.29–25.97 ohm |
| T2F | VDDA / VDD | 30.45 / 26.51 ohm |
| TRIP | VDDA / VDD | 25.59–27.59 / 22.37–23.03 ohm |
| GATE | VDDA / VDD | 26.59–26.62 / 42.69 ohm |
| OSC | VDD | 22.90–22.91 ohm |
| Three input level shifters | VDDA / VDD | 48.87–58.12 / 53.86–54.61 ohm |

This does not multiply the full chip current by every local stack: mesh current
is shared; each macro's access resistance carries its own current. The three
LS branches share a stripe stack, identified in the retained model.
Earlier results are preserved. `supply-mesh-20260921-r1-incomplete` omitted
implicit one-cut vias and is invalid for resistance conclusions.
`supply-mesh-20260921` restored them but lacked the final pin/jog corrections;
use r3 for the values above.

## Current and power accounting

These are simulated block currents and vectorless digital estimates, not
measurements or one coherent whole-chip operating point. Input manifests and
summaries are hash-pinned in the budget JSON; each underlying campaign retains
its own deck, model and waveform provenance.

| Component / fixture | Near-room value used | Limitations |
|---|---:|---|
| SENSE, TT/typ, 3.3 V, 27 C, CM 0, shunt 50 mV | 1.008220 mA VDDA | Ideal VREF/PTAT, three OTAs, fixture output load |
| BGR + T2F + three actual LS, 3.3/1.2 V, 27 C | 63.4176 uA VDDA + 0.242405 uA VDD | Ideal 1 V IPTAT clamp, estimated route RC, 50 fF output |
| OSC code 0, TT/typ, 1.2 V, 27 C | 112.5622 uA VDD | Fixture load; simulated frequency 12.926776 MHz |
| CTRL retained run7, TT, 1.2 V, 25 C | 0.970059 mW | Vectorless estimate, 100 ns clock constraint; activity factors unestablished |

BGR is included in the joint current and is not added again. Near-room known
currents sum to 1.071638 mA VDDA and 0.921187 mA VDD. Total is 4.641829 mW.
Scaling all CTRL internal and switching power by 12.926776/10 while leaving
leakage unchanged gives 4.925103 mW. This is a frequency sensitivity assumption;
not every digital net must follow OSC, and workload activity remains unknown.
The fastest retained OSC screen is 16.776615 MHz, so the near-room adjustment
is not a corner envelope.

Combining separate selected screen maxima gives an incomplete 6.714383 mW.
That combines SENSE 1.39743 mA at 3.6 V/125 C, thermal joint, OSC and digital
maxima from different fixtures/corners; it is not a coherent PVT simulation.
The arithmetic unallocated portion of 10 mW is 5.358171 mW near room or
3.285617 mW for this mixed selection, **not qualified remaining power budget**.
GATE's separate 216-case power screen has 156 completed cases, 22 solver
failures and 38 timeouts; EN was low, so its retained currents cannot fill
active GATE power. Real-FET runs did not save supply currents. Active TRIP,
real IO/package loads, SENSE transient supply current and actual reference-bias
interaction also remain unqualified here.

## Later actual-GATE and two-pad fixture extension

[Gate supply r2](gate-supply-20260921-r2/summary.json) integrates the retained
nominal `fet_20260921T165316Z_0f0cfcb4/power_wave.tsv`. This includes actual
GATE, 30 mA GATE pad, 4 mA FAULT pad and vendor FET gate loading. The external
5 V / 4 A load source power is excluded. The fixture uses 0.5-ohm series
supply resistors and 1 nF local capacitance on both rails. Currents below are
from the upstream ideal sources, not instantaneous internal device currents.

| Window | Combined 3.3 V source mean | 1.2 V source mean | Total source power |
|---|---:|---:|---:|
| Armed, 2–4 us | 314.992 uA | 1.729 nA | 1.039476 mW |
| Tripped, 8–12 us | 1.196 nA | 1.397 nA | 5.622 nW |

The enable event (0.19–1 us) has sampled 3.3 V source peak 29.6125 mA and
4.47866 nC excess source charge. Trip (4.99–6 us) has peak 4.47301 mA and
11.6735 pC excess charge. Excess subtracts a piecewise steady baseline:
disabled/armed around 0.2 us for enable, armed/tripped around 5 us for trip.
The corresponding 1.2 V sampled peaks are 0.136766 and 0.359673 mA.
Minimum local 3.3 V fixture voltage is 3.28519 V. Charge integration uses
trapezoids with interpolated exact window endpoints; retained source-current
versus resistor-drop residual is below `1.8e-15 A`. Source traces include local
capacitor charging; changes in capacitor energy are recorded separately.

**Rail assignment matters.** Actual top CDL connects both output pads to
IOVDD/IOVSS; the core uses VDDA/VSS. This fixture joins those 3.3 V supplies
and returns. Consequently its combined current cannot be assigned to the
modeled GATE core VDDA loop. Its 0.5-ohm source fixture also does not establish
assembled dynamic impedance. The CDL is hash-pinned with the rail connections
in the extraction result. Separate core/IO current sensing and an IOVDD/IOVSS
impedance model are needed for that calculation.

[Budget r3](supply-budget-20260921-r3/budget.json) adds the armed fixture power
to the earlier cross-fixture subtotal: **5.681305 mW**, or **5.964579 mW** with
nominal OSC frequency scaling. Per-rail mesh/DC bounds are intentionally
unchanged because the fixture does not split VDDA from IOVDD. This nominal
extension does not fill active TRIP, other pad loads, realistic workload,
reference interaction or PVT coverage. No new whole-chip acceptance is claimed.
R1 and r2 extraction/budget evidence remain preserved; r3 budget consumes the
r2 extraction with explicit CDL rail provenance and resistor consistency check.

Reproduce to fresh directories:

```sh
python3 designs/g1-guardian/review/audits/analyze_gate_supply.py --run designs/g1-guardian/blocks/g1_gate/sim/campaigns/fet_20260921T165316Z_0f0cfcb4 --output build/scratch/gate-supply-repeat
python3 designs/g1-guardian/review/audits/analyze_supply_budget.py --mesh designs/g1-guardian/review/audits/supply-mesh-20260921-r3/mesh.json --gate-current build/scratch/gate-supply-repeat/summary.json --output build/scratch/supply-budget-gate-repeat
```

## Conditional DC voltage and headroom

For a passive resistor graph, transfer resistance from an arbitrary positive
current injection to an observed node does not exceed that node's self
resistance. The budget uses this property to bound modeled-grid drop from the
known global rail current, adds local access drop from the known macro load,
and includes shared return current. Because the joint BGR/T2F/LS waveform does
not split each member's current, each observation conservatively allows the
entire combined group through that member's access. Those per-observation
bounds are not a simultaneous assignment of duplicated currents.

Maximum known-load VDDA/return bound is 27.610 mV using the retained 10 MHz
CTRL estimate, or 27.878 mV with near-room OSC scaling. Doubling modeled
resistance and adding an assumed 5-ohm common external loop gives 66.901 mV
for the latter scenario. These values exclude all missing loads and do not
qualify the full rail network. GATE/TRIP local current bounds are omitted
explicitly because active currents are missing.

At 3.3 V source and a 3.0 V previously tested pin-voltage floor, a simple
20/40/80-ohm loop allows 15/7.5/3.75 mA before using that 0.3 V headroom.
At 1.2 V and a 1.08 V floor, the corresponding values are 6/3/1.5 mA.
At a source already equal to the previous tested floor, any positive IR drop
leaves that qualification range. This is not proof of functional failure;
blocks require qualification with the loaded supply/return voltages.

## Passive dynamic sensitivity

[72-case RLC sweep](supply-rlc-20260921-r1/summary.json) models
`Z(s) = (R + sL) / (1 + sRC + s^2 LC)` from load current to incremental droop.
R is 20/40/80 ohm, L is an assumed 0/1/5/10 nH, and local C is an assumed
0/10/100 pF. A 1 mA trapezoid has assumed 1/10 ns edges and a 100 ns hold.
These ranges are sensitivities, not extracted or measured package/decoupling
values. No PDK transient simulator was used.

Calculated peak droop over these cases is 20–90 mV for 1 mA, 10–45 mV for
0.5 mA, and 100–450 mV for 5 mA by linear scaling. The 90 mV case has
R=80 ohm, L=10 nH, C=0 and a 1 ns rising edge. It is an assumed idealized
no-capacitance limit. This incremental droop must be combined with a separately
specified DC operating point; large-droop linear scaling does not qualify
nonlinear transistor behavior.

All poles are stable; all 72 plateau checks pass. An independent first-order
RC closed-form comparison has maximum error `7.15e-16 V`; halving the timestep
in the largest-peak finite-L/C case changes the peak by `7.66e-14` relative.
[Representative traces](supply-rlc-20260921-r1/sensitivity.svg) use L=5 nH,
C=10 pF and 1 ns edges; CSV and PNG are retained and the PNG was visually
checked. NumPy 2.5.1, SciPy 1.18.0, Matplotlib 3.11.1.

## Reproduction and remaining checks

Use new output directories; runners refuse overwriting existing evidence.
The mesh requires the pinned EDA image/PDK; the budget is Python standard
library; RLC uses the Python numerical packages in that image.

```sh
G1_CPUS=2 flow/run.sh env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 designs/g1-guardian/review/audits/model_supply_mesh.py --output build/scratch/supply-mesh-repeat
python3 designs/g1-guardian/review/audits/analyze_supply_budget.py --mesh build/scratch/supply-mesh-repeat/mesh.json --output build/scratch/supply-budget-repeat
G1_CPUS=2 flow/run.sh env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 designs/g1-guardian/review/audits/simulate_supply_rlc.py --output build/scratch/supply-rlc-repeat
```

| Check | Status |
|---|---|
| Corrected sampled supply-access geometry coverage / resistor solve | passed |
| Conditional current accounting and passive RLC numerical checks | passed within stated analytical scope |
| Retained abstract OpenROAD VDDA connectivity | failed; separate GDS probes connect reported residues |
| Activity-annotated whole-chip power below 10 mW | not run |
| Full loaded analog/digital/IO/package IR and dynamic impedance | not run |
| Functional simulations using loaded local rail voltages | not run |
| Candidate full IO LVS | failed; candidate remains unpromoted |

Next electrical work is to split active GATE core/IO rail currents, retain
active TRIP currents, establish
actual digital/IO activity and load conditions, specify package/regulator
impedance and decoupling, then apply the combined loads to a complete resistor
network and qualify blocks at the resulting local voltages. See
[the retained power audit](VDDA_AND_POWER_20260921.md) for why the existing
assembly IR report omits loads; it is not a whole-chip acceptance result.

## Later core/pad current separation

[Split-current audit](GATE_SPLIT_POWER_20260921.md) and budget r4 separate the
nominal armed load: core VDDA 94.577 pA, core VDD 1.04134 nA, pad VDD
687.884 pA and pad IOVDD 314.991997 uA. The 1.039 mW addition is supplied
power including the driven external 10-kohm gate pulldown, **not on-die heat**.
The per-core-rail DC change is negligible; IOVDD/IOVSS loaded IR remains
not run. Steady KCL passes, while fine switching-event charge conservation
fails the original 0.1 pC criterion and is retained honestly as a limitation.

## Transistor-level DC rail perturbation

[SENSE supply anchor](SENSE_SUPPLY_ANCHOR_20260921.md) runs copied schematic
fixtures with the modeled14.838-ohm supply and11.135-ohm return, nominal/2x
resistance and3.3/3.0V sources. All54 selected OP and18 gain checks pass;
minimum local rail2.948695V and maximum incremental global input-referred
output shift50.5uV occur at3.0V/2x. This is TT27C, ideal reference/bias,
SENSE-only DC evidence; dynamic, joint and IO IR remain not run. Failed runner
setup and superseded ill-conditioned control currents are preserved and
explicitly dispositioned; corrected ideal controls reproduce original data.

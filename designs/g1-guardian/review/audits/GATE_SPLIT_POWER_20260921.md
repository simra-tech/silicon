# GATE core and pad supply-current separation

The retained nominal vendor-FET run with four zero-volt branch probes separates
core VDDA/VDD from pad IOVDD/VDD while keeping its common upstream 0.5-ohm,
1 nF fixture. **Armed steady-state KCL passes; switching-event integrated KCL
fails the initial 0.1 pC absolute diagnostic criterion.** This is not independent
assembled-rail or package qualification.

Input is `g1_gate/sim/campaigns/fet_20260921T165800Z_38f6131f`, TT/27 C,
3.3/1.2 V, external 5 V / nominal 4 A vendor-FET fixture. The original campaign
pins ngspice46, PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`, model hashes,
image and deck. [Extraction r2](gate-split-supply-20260921-r2/summary.json)
hashes both source and branch waveforms, deck, log and original run record.
Currents through probes are positive toward the load. Source currents are
sign-inverted before conservation checks.

| Armed 2–4 us branch | Mean current | Mean delivered branch power |
|---|---:|---:|
| Core VDDA | 94.577 pA | 0.312 nW |
| Core VDD | 1.04134 nA | 1.250 nW |
| Pads VDD | 687.884 pA | 0.825 nW |
| Pads IOVDD | 314.991997 uA | 1.039424 mW |

The 1.039424 mW branch total is rail-supplied power including driven external
load. The 10-kohm external gate-to-source pulldown accounts for most armed
IOVDD draw. It is **not on-die dissipation**. The prior upstream-source total
1.039476 mW additionally includes the fixture supply resistor loss. No thermal
power estimate is claimed; computing it would require accounting for output
terminal energy and all external loads separately.

Actual top CDL connects pads to IOVDD/IOVSS separately from core VDDA/VSS.
The fixture joins their supplies/returns at the local source nodes, and probes
only supply branches. It does not establish the separate physical return
currents or IO rail impedance.

| Event / branch | Sampled peak | Excess charge over piecewise steady baseline |
|---|---:|---:|
| Enable core VDDA | 1.684 mA | 1.001 pC |
| Enable core VDD | 0.1640 mA | 0.1580 pC |
| Enable pads IOVDD | 29.468 mA | 4.47748 nC |
| Enable pads VDD | 0.08394 mA | 0.04139 pC |
| Trip core VDDA | 1.269 mA | 0.9527 pC |
| Trip core VDD | 0.4326 mA | 0.2706 pC |
| Trip pads IOVDD | 5.766 mA | 10.3119 pC |
| Trip pads VDD | 0.2343 mA | 0.1010 pC |

These switching values are sampled diagnostics; the charge precision is limited
by the failed conservation check. Windows are 0.19–1 us around enable at
0.2 us and 4.99–6 us around trip at 5 us. The baseline is disabled/armed
before/after enable and armed/tripped before/after trip. Currents in different
branches need not peak simultaneously.

Integrated KCL compares upstream source charge minus core/pad branch charge
minus `1 nF * (V_end - V_start)`, using trapezoids and interpolated endpoints.
Armed maximum residual is 2.64e-22 C. Dynamic maximum is 0.589449 pC over the
full trace; that is 0.00982% of the 3.3 V source charge. However the trip VDD
window has 0.0260465 pC residual, **6.53%** of its small source charge, and
trip 3.3 V has 0.251359 pC residual, **1.70%**. Fine event-charge partition
therefore needs a tighter-step/numerical rerun. The existing 1 ns maximum
step and integration tolerance are not sufficient evidence for a precise
sub-pC conservation claim. The first assertion failure is preserved in r1;
r2 reports all results without changing the original criterion.

[Budget r4](supply-budget-20260921-r4/budget.json) uses only the passing armed
steady split for its new per-rail extension. Core VDDA receives 94.577 pA,
VDD receives core plus pad VDD current; IOVDD receives 314.991997 uA for these
two outputs only. The IOVDD current is excluded from the core VDDA/return
model. The nominal known-load VDDA bound remains about 27.88 mV. Other IO,
TRIP, realistic activity, shared substrate/return effects and PVT coverage
remain absent. Whole-chip power/IR acceptance is **not run**.

```sh
python3 designs/g1-guardian/review/audits/analyze_gate_split_supply.py --run designs/g1-guardian/blocks/g1_gate/sim/campaigns/fet_20260921T165800Z_38f6131f --output build/scratch/gate-split-repeat
python3 designs/g1-guardian/review/audits/analyze_supply_budget.py --mesh designs/g1-guardian/review/audits/supply-mesh-20260921-r3/mesh.json --gate-current designs/g1-guardian/review/audits/gate-supply-20260921-r2/summary.json --gate-split build/scratch/gate-split-repeat/summary.json --output build/scratch/supply-budget-split-repeat
```

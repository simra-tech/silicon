# VDDA connectivity and retained power evidence — 2026-09-21

The retained OpenROAD VDDA check **failed**. Independent delivered/candidate
GDS conductor probes **passed** for the reported pad residue and sampled macro
supply stacks. Whole-chip power and loaded assembly IR compliance are **not
verified** by these reports.

## VDDA discrepancy and physical check

`assembly-1350/22-openroad-generatepdn/analog_straps.log` reports six
unconnected shapes on VDDA: Metal2/3/4/5 at (1206,360)–(1209,430) µm;
TopMetal1/2 at (1206,360)–(1279,430) µm. The two instances are
`pad07_vdda/pad` and `IO_BOND_pad07_vdda/pad`; the log ends the check with
`PSM-0069`. The zero aggregate and per-VDDA metrics do not represent this result.

`audit_vdda_connectivity.py` extracts only physical Metal1–TopMetal2 and
Via1–TopVia2 connectivity, without labels, virtual/global connections,
same-name merging or device conductance. Six probes at (1207.5,395), one on
each reported stub layer, join both bondpad center points (1244,395) and
(1248,395), the padbare feed (1029.1,389), the M5 feed strap (980,389.34),
and BGR/SENSE/T2F/TRIP/GATE/LS supply-stack probes. All 16 probes occupy
**one physical cluster** in each GDS. Exact coordinates and hashes are in
[vdda-delivered-20260921.json](vdda-delivered-20260921.json) and
[vdda-candidate-20260921.json](vdda-candidate-20260921.json).

The delivered hash is
`38c1d6d13bbfee4ed0e3c01477742c3d2d28317d9215d9e5bd9a35551285ae59`;
the unpromoted candidate hash is
`2d895efbb0e1c35ed7c891d376b010e041005d731ecd6d5448d872adfe55c9ca`.
KLayout 0.30.9. Reproduce each view with:

```sh
G1_CPUS=2 flow/run.sh python3 designs/g1-guardian/review/audits/audit_vdda_connectivity.py designs/g1-guardian/blocks/g1_padring/layout/g1_chip_top.gds build/scratch/vdda-delivered-repeat.json
G1_CPUS=2 flow/run.sh python3 designs/g1-guardian/review/audits/audit_vdda_connectivity.py build/scratch/pad-outward-dummy-clean-20260921/g1_chip_top.gds build/scratch/vdda-candidate-repeat.json
```

These probes support a pad LEF abstraction limitation for the reported
residue. They do not prove every transistor supply terminal, rail resistance,
or current capacity. No geometry change is justified by these particular
markers. The older isolation check proves absence of multiple distinct
pin labels on one conductor; it alone does not prove continuity.

The signoff collector now gives raw supply errors precedence over aggregate
metrics. Fresh `signoff-collector-20260921-r6/check_status.json` records
`retained_supply_grid: failed`, and collection exits 1 while preserving other
check statuses. Four collector regression tests passed, including a raw VDDA
failure with metric zero and missing completion signatures. The originating `flow/run_dryrun.sh` hardcoded coordinate exception was also
removed. `flow/update_pdn_metrics.py` now counts failed or incomplete checked
nets, requires explicit success, and prevents a previous zero from hiding a
new failure. Three regression tests passed, including the actual retained
log yielding one failed net; shell syntax passed. The wrapper also retains nonzero LibreLane exits while continuing evidence
collection, then returns failure. The actual wrapper passed four disposable tool-fixture scenarios (first
LibreLane failure, resumed LibreLane failure, CDL failure and successful
completion), checking continued netlist evidence and final exit status.
Shell syntax also passed; a fresh whole assembly flow was **not run**. Existing run metrics were not rewritten. Older reports remain unchanged. README/INTEGRATION
claims were corrected to distinguish the failed abstract check from this
independent physical evidence.

## Retained power and IR scope

`audit_power_evidence.py` hashes the actual retained run inputs (ODB, netlists,
DEF, SDC and SPEF), configurations, commands and reports into
[power-evidence-20260921.json](power-evidence-20260921.json). This is a
read-only audit, not a new simulation. Values below are **vectorless estimates**;
retained STA/IR logs and configurations do not establish VCD/SAIF annotation.
The engine's numerical default activity factors have not been established.

| Retained run | TT STA power | Fast STA power | Slow STA power | TT IR load |
|---|---:|---:|---:|---:|
| CTRL run7 | 0.970059 mW | 1.204539 mW | 0.771732 mW | 0.970 mW |
| Assembly 1350 | 0.931766 mW | 1.159566 mW | 0.744466 mW | 0.143 mW |

CTRL uses 100 ns OSC/SCLK timing clocks and 0.05 pF output loads. Assembly
uses 100 ns SCLK/internal OSC constraints and 0.006 pF on selected digital
outputs. These constraints do not establish realistic switching workloads.

Assembly STA reads the digital macro's expanded netlist and SPEF, but logs
BGR, DOSE, DUT, GATE, LS, OSC, SENSE, T2F and TRIP as black boxes. Its Macro
power category is exactly zero. The assembly IR flow instead reads the ODB
with the digital macro timing abstract; that Liberty has **zero internal-power
or leakage-power groups**. Its log cannot find the internal OSC clock buffer,
and reports a virtual clock. Thus even the digital load represented in the
assembly STA number is not fully present in assembly IR, while analog and
level-shifter loads remain absent. The 0.143 mW IR load cannot qualify the
0.932 mW STA scenario, much less the complete chip.

| Retained IR scope | Worst VDD drop | Worst VSS rise |
|---|---:|---:|
| CTRL run7, its represented load | 0.416613 mV | 0.109865 mV |
| Assembly, incomplete load | 0.0297665 mV | 0.0253102 mV |

Both IR reports analyze only VDD and VSS. Loaded VDDA, IOVDD and IOVSS IR
checks are **not run**. The installed unchanged `irdrop.tcl` source/hash is
preserved in `installed-irdrop-tcl-20260921.json`; it reads the ODB and loops
the configured power/ground nets. The VDD `drop__average` metric contains
approximately 1.2 V (average voltage), so the raw report and explicitly named
worst-drop metrics are used here instead.

Whole-chip power below 10 mW, activity-annotated power, macro-loaded assembly
IR, and loaded analog/IO rail IR remain **not run**. Partial analog transient
supply currents cannot fill omitted RTL/oscillator/output-driver power without
an independently specified model and workload.

## Subsequent conditional supply model

[V18 supply model](V18_SUPPLY_MODEL_20260921.md) adds corrected pin/jog access,
nominal route/via resistance, explicitly incomplete current accounting and a
72-case passive RLC sensitivity. All 36 sampled accesses connect in that model.
These scoped analytical checks do not replace the missing activity-annotated,
macro-loaded electrical IR and functional qualification above.

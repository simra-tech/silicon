# DUT and DOSE VSS-only feed contract

Candidate additive geometry only. Source models, native cells, logical ports,
root spines and all existing geometry remain fixed. These blocks have a VSS
feed only; no VDD or VDDA connection is invented.

Source PNL/OpenDB inventory binds `i_core.u_dut.vss` and `i_core.u_dose.vss`
to VSS. Native M3 windows are respectively x733–767/y400–402 µm and
x733–763/y450–452 µm. Proposed source-owned access and root lane5 handoffs
are (736.8,401) and (736.8,451) µm, M3 to TM1. Each stack has12 Via3,
12 Via4 and4 TopVia1 cuts. No TopVia2 or TM2 is added.

Prospective gates: native component membership, no foreign metal/cut capture,
actual frozen PDN clearance, exact additive saved polygon/text comparison,
physical VSS-ring connection with VDD remaining distinct, every-new-cut-open
connectivity, isolated stock main DRC and affected core main/maximal DRC.
Existing signal context may fail and must be repaired by actual final routing,
not waived. No unchanged baseline rerun is required.

The1 mA branch target is an exploratory geometry assumption, not a measured
or verified injection/return-current bound. Via-only half-table arithmetic is
2.4 mA before loss and2.1 mA after worst single-cut loss; actual current sharing,
native internal necks, DUT test current, dose measurement current, IR/EM and
worst-PVT qualification remain not run. The foundry current table applies at
105°C/11years only;50% is a declared engineering target, not foundry derating.

Each build is bounded to150 s/one CPU and preserves failures. Stock/cut checks
use90 s children; affected core checks use the existing bounded stock runner.
No canonical adoption or source/model/rule modification is authorized here.

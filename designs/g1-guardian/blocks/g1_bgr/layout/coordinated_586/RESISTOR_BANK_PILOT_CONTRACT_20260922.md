# Fixed-placement resistor-bank routing pilot — prospective

Implement all399 resistors from exact source586 at their refreshed-pack native
origins, without changing resistor dimensions, substrate nodes, intermediate
net names or replicated centroids. This is a connectivity-first isolated pilot,
not a selected final parasitic/matching design.

Use40 source-net M3 collectors in the lower row's body-height window, plus a
separate physical collector for XR16 precision-return ends. Row0 uses M2 drops;
row1 uses M4 drops. Two end columns per native slot are offset−0.30/+0.30µm
from head center. Row1 access stacks are above all row0 drops. All via arrays
have two vertical0.19µm cuts on0.42µm pitch, with0.30×0.84µm landings.
Collectors are0.30µm wide with1µm pitch; the two VSS-role collectors are0.8µm
wide and1.2µm apart. The XR16 branch joins general VSS at one declared left
star point; the reference-HBT branch is not implemented by this resistor pilot.
No new electrical net or resistor is introduced by route-role tags.

M3/M4 routing over resistor bodies introduces unqualified capacitance and
asymmetry. No low-parasitic, matched-current, full R1/HBT star, current-margin,
temperature-coefficient or new electrical claim follows. Full extraction and
route optimization are later gates. No M5/TopMetal/TopVia is introduced.

Before stock checks require exact399 source bindings/native bboxes/PolyRes
geometry, explicit798 metal-terminal probes plus40 source-net ports and guard
connection, one physical connected component per source net, no shorts, fixed
positions and5nm grid. Check exact finite macro bounds420×132µm; other BGR
devices start outside this envelope but chip-scale guards/feeds remain not run.
Keep the source-derived CDL separate from extraction. Freeze geometry, command,
source/PDK hashes and terminal ledger before any stock DRC/LVS invocation.

The first generation/audit is one CPU,180seconds,0.15GiB growth after a fresh
resource gate. Stock DRC/LVS require subsequent review; density, antenna,
PEX, analog simulation and adoption are **not run**. Seed is **not applicable**.

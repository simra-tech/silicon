# Stacked pair r2: move substrate ring outside poly-only end dummies

The r1 geometry gate failed before GDS adoption. An output-only replay captured
exactly four added Activ/GatPoly intersections,1.908µm² each, at the substrate
ring sidewalls. There were no removed native channels or native Activ. The
poly-only end dummies extend from xActiv−2.20 to−0.20µm and from
xActivEnd+0.20 to+2.20µm. The r1 ring inner sidewalls at±1.45µm cross those
dummies, creating unintended gate/active intersections. This is a real geometry
failure, not an audit tolerance issue.

One explicit geometry revision: move the substrate ring inner x coordinates
from±1.45 to±2.50µm relative to the unchanged active ends. Ring width remains
0.30µm, leaving0.30µm between the dummy end and ring Activ. Horizontal ring
segments lengthen accordingly, and the existing ring-attached VSS escape moves
with its returned center coordinate. Keep ring y coordinates, all native cells,
NWell/body strips, dummy polygons, gates, sources, drains and seven trunk
coordinates unchanged. Source/card/PDK edits are prohibited.

After a fresh0.05GiB resource gate: one CPU7 geometry child,60seconds, at most
50MiB output. All original source, centroid, junction-bookkeeping, physical
terminal, native-channel and19-other-native overlap checks remain mandatory.
Capture failures under a new ID. The existing before/after channel assertion
must pass without excluding the guard region. No stock/PEX/analog launch or
automatic further revision; neighboring complete contacts, full-main fit and
shared-junction model applicability remain **not run**. Seed **not applicable**.

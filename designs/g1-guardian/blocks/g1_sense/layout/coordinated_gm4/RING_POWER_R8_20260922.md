# SENSE r8: wide-ring parallel-spacing correction

The preceding r7 passed isolated stock checks and whole-core no-short/ring
distinctness, but whole-core main DRC **failed** one `TM2.bR` marker. Its
parallel segment exceeded50 µm beside a conductor wider than2.5 µm, requiring
5 µm clearance rather than the2 µm minimum used by the r7 placement screen.
The failed r7 whole-core run took111.724 s; maximal checks were **not run**
after that main failure. Frozen r7 and the parent's failure reports remain.

R8 changes only the two affected VDD pods/backbone from x36 to x40 µm using
an exact derived adapter; source, cards, rules, all native devices and all nine
external pins remain held. Saved TM2 minimum local x37.92 maps under R90
at(1031,331) to global y368.92, giving6.76 µm clearance above ring top362.16.
The independent saved audit requires local TM2/TopVia2 x≥36.16. Full-core
integration still requires the parent's actual geometry/deck checks; this
coordinate assertion alone is not signoff.

Final isolated GDS is `sense-ring-routing-20260922-r8a/g1_sense_physical.gds`,
top `g1_sense_physical`, SHA256
`8060e30ac14a1c4aeb1cf62204c9e95d9a68dbad3d73412fbb34c6a33be8b4f7`.
Canonical source `baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877`
and CDL `e3e3c22fa0e59c61f5acc79f3733833ec2a144fe3f133ed09f7922a395deec20`
remain unchanged. VDD pin is134/2 at(383,218), VSS126/2 at(383,226), with
datatype25 labels and unchanged4×4 µm pin boxes. Seven M4 signal annotations
are exact r7 copies; all nine are distinct and drawing-covered.

| Isolated check | Status | Result |
|---|---|---|
| Build / source134 graph | passed | 17.769 s; no opens/shorts |
| Independent saved native/source reference | passed | 17.714 s; all58MOS/835channels/893strips/98R/3MIM, centroids and defaults |
| Saved delta / pins / wide-ring keepout | passed | 14.194 s; only declared upper routing layers changed |
| Unchanged stock main DRC, density excluded | passed | 0 markers,35.007 s |
| Strict hierarchical stock LVS | passed | 4.120 s; comparison and all9pins Match |
| Via-only capacity / cut graph | passed topology inventory | 17.994 s; no supply single-cut articulations |
| Stock written A/P attribution | failed | Same51failed/7passed, separately audited9.089 s; combiner cause documented separately |
| Actual branch/contact/metal lifetime margin | not run | Combined source+body observations do not separate physical islands |
| Whole-core checks | not run here | Parent owns integration and stock run |
| Full PEX / shared-intrinsic applicability / adoption | not qualified / not run / not run | No inheritance from geometry-only gates |

## Explicit affected MIM neighborhood

All native plates and their inner1.5 µm M5/TopMetal1/Vmim context have XOR0
against r7. The XBUF **outer5 µm context changes**, adding2.64 µm² M5 and
6.974 µm² TopMetal1 inside that window. These are changed extrinsic coupling
geometry, not intrinsic capacitor edits. No old unchanged5 µm-context claim,
previous field value or electrical margin is inherited. A supported qualified
field extraction must cover these changes once the independent MIM model/
extractor-composition blocker is resolved.

Reproduction uses `build_ring_power_revision_r8.py` and
`audit_ring_power_revision_r8.py` plus the unchanged power reference, stock,
capacity and junction auditors. Exact adapter/derived source snapshots, stock
commands, deck hashes and portable-prefix provenance are in the r8 evidence.
Built against pinned IHP SG13G2 `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`,
KLayout0.30.9, versions established by runtime gate. No ngspice or PEX process
was launched for this geometry revision; stock LVS extraction did run.

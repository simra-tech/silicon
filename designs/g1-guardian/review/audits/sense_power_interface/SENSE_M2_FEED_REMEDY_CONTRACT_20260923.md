# Isolated source-held SENSE M2 feed remedy

The candidate changes only four Metal2 source feeders and adds eight Via1
cuts to each existing Metal1 source bar. It does not change a primitive,
contact, Metal1 polygon, pin annotation, source parameter, model or rule.
The original r8 GDS and all previous evidence are preserved.

## Frozen inputs and selection

Source SHA256: `baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877`.
Original GDS: `8060e30ac14a1c4aeb1cf62204c9e95d9a68dbad3d73412fbb34c6a33be8b4f7`.
Candidate GDS: `4b8a82d4a19127e5975d558381cd0f1057235cf51dfbbc58e2219b0f0c4a8bd1`.

XM14/XM11 source feeds are 214.82 um long; XM4/XM3 are 198.50 um.
Their original 0.4 um width gives actual positive-graph bridge edges of
55.31615/51.11375 ohm, respectively. Each separates all 575/483 proven
source contacts of one logical device from the rest of its supply graph.
The four candidate widths are 4 um. All 6 um trials failed the conservative
foreign-net spacing screen; this is a discrete feasibility screen, not a
claim that 4 um is the mathematical maximum legal width.

## Prospective acceptance

1. Saved native geometry: exact additive M2/Via1 accounting; all other
   polygons, text and hierarchy unchanged; all 134 source nets and 229
   physical components retained; no new foreign contact.
2. Independent native/source audit: 58 MOS, 835 channels, 893 diffusion
   strips, exact W/L/ng/default junction allocation and matching centroids;
   98 resistors, three MIMs, nine ports, 5 nm grid, fixed 385 by 240 um box.
   Source CDL must remain byte-exact SHA256
   `e3e3c22fa0e59c61f5acc79f3733833ec2a144fe3f133ed09f7922a395deec20`.
3. Unchanged pinned stock main and maximal DRC, zero markers, 120 s each;
   conditional strict stock LVS, 120 s, explicit match and every cross-reference
   object matched. Retain original 51 source-oriented A/P annotation failures
   and require no new annotation delta; strict LVS does not waive them.
4. Re-extract exact all-contact ordinary-metal topology with unchanged
   material/via assumptions and exact retained contact footprints. Compare
   source-component bijection, positive edges, four feed cuts and rail bounds.
   No compact-model contact weights or current injection is introduced.

Initial geometry preparation passed. Independent source/reference, stock,
junction comparison and new resistance checks are **not run** at contract
freeze. Fullchip adoption, affected field/coupling, intrinsic model boundary,
zero-R/electrical parity and physical IR/EM acceptance remain **not run**.
The resistance result is a graph-domain statement, not a physical current
bound or an accepted voltage-drop prediction.

## Completed disposition

All four scoped gates above completed: independent native/CDL reference,
main and maximal zero-marker stock DRC, strict LVS, exact 58-record A/P
annotation delta (original 51 failures retained), and all-contact positive
metal-R graph/bound comparison. The separate review gives exact result
scope. The complete physical/electrical/adoption gates remain not run;
the original prospective not-run status above describes contract freeze,
not the completed disposition.

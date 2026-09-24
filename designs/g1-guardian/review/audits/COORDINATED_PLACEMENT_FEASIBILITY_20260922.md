# Coordinated placement feasibility: bounded, not adopted

Retained-PDN legal fit is **not established**. A source-bound rectangle placement now accommodates the BGR and gm4 SENSE proposals, all other macros and all 4,662 decaps inside a proposed **1,414 × 1,414 µm = 1.999396 mm²** outline. This is preparation evidence for a geometry gate, not DRC/LVS/PEX, routing, matching, current-margin or tape-out acceptance. No design GDS has been generated or saved by this study.

**Inherited SENSE buffer source-finger fidelity failed on review.** The reused OTA generator realizes MB2/MB6 as one 8 µm finger instead of the exact source's two 4 µm fingers, and MB3/MB5 as two 8 µm fingers instead of four 4 µm fingers. This affects XBUF/XREF as well as the inherited main OTA. The existing CDL conversion drops `ng`; total-W/L LVS cannot certify finger count or junction A/P applicability. Consequently the two reused buffer rectangles below remain space reservations, not qualified source-faithful buffers. A separate delivered-polygon/native-source audit and isolated faithful buffer implementation are required. Earlier packing/ring results are preserved with this limitation, not retrospectively changed into fit evidence.

## Exact sources and reproducibility

BGR source SHA-256 `53513ab43c62ead3a4c171f5a026b165e2a0bfda2b5b0cb5b104a30aae33a4e2` has 24 full units in each selected PTAT branch, four Qref units and fixed 53.465 µm R2 units. The separate two-device HV-length derivative `586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b` is not silently substituted; its verified native footprint increase is only 0.408 µm², but source applicability remains separately reviewed. SENSE is exact gm4comp3 source `baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877`.

[Packing source](prepare_coordinated_bbox_pack.py) and [ring-aware r4 result](coordinated-bbox-pack-20260922-r4.json) provide every native device rectangle, source line, retained decap correspondence, macro placement and corridor. The packing calculation reads qualified KLayout 0.30.9 inventories and runs only rectangle arithmetic; it does not instantiate a production layout. Reproduce with:

```sh
python3 designs/g1-guardian/review/audits/prepare_coordinated_bbox_pack.py --floorplan ring-aware --corridor-plan compact --decap-packing site-greedy --output build/scratch/coordinated-bbox-pack.json
```

The output must not already exist. Exact native upper-metal comparisons use pinned KLayout 0.30.9 and unchanged PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`, in memory only.

## Constructive native packing

BGR is 420 × 354 µm. It contains **1,036 exact source instances**: 235 PMOS, 101 NMOS, 301 HBT and 399 resistors. Every native rectangle is on the 5 nm grid and non-overlapping. The 50 replicated groups (40 PTAT, 10 Qref) have explicitly checked point-symmetric centroids. MOS/HBT rectangles retain 2 µm engineering reservations; these are not asserted to be sufficient foundry well/contact/guard clearances. Resistors retain 1.9 µm column pitch, including full 53.465 µm PolyRes bodies verified separately. Reducing the earlier 360 µm height to 354 µm removes only empty exterior space: all unchanged native-plus-margin boxes end at or below 351.24 µm.

The gm4 SENSE proposal is 385 × 240 µm locally, rotated as a whole to 240 × 385 µm at top level. Its 230 × 164 µm main OTA keeps all complete native arrays, including 211.78 µm-wide devices, rather than assuming folded smaller footprints. Eight large devices occupy symmetric rows; all remaining native devices and the 69 × 23 µm compensation capacitor are separately placed. Two unchanged 97.85 × 51.2 µm OTAs sit side by side. The original 52-column/two-row resistor bank retains 2.5 µm pitch and its source-derived 132.5 × 170.48 µm ring envelope. New gate contacts, guards, signal/power routes, capacitor-tab connection and extracted matching are **not run**.

## Proposed macro locations

All coordinates are µm. R90 denotes whole-macro rotation, not individual device resizing.

| Macro | Lower-left | Upper-right | Orientation |
|---|---|---|---|
| Digital, unchanged | (367,364) | (727,724) | R0 |
| BGR candidate | (331,732) | (751,1086) | R0 |
| SENSE candidate | (791,331) | (1031,716) | R90 |
| TRIP, unchanged | (771,736) | (1000,943) | R0 |
| OSC, unchanged | (771,953) | (937,1090.57) | R0 |
| T2F, unchanged | (953,953) | (1045,1055.6) | R0 |
| GATE, unchanged | (731,545) | (781.65,675.68) | R90 |
| DUT, unchanged | (733,400) | (767,434) | R0 |
| DOSE, unchanged | (733,450) | (763,480) | R0 |
| Three level shifters | (733/753/773,490) | each 9.2 × 11.7 | R0 |

Reserved signal corridors are an 8 µm horizontal spine at y724–732, a 12 µm upper analog spine at x755–767, an 8 µm digital/SENSE interface at x783–791, and top/bottom corridors for the rotated SENSE ports. Supplies remain intended for upper-metal PDN; critical analog routes would need layer-assigned M2–M4 tracks and shielding reviewed against actual net counts. These corridors are empty rectangles, **not demonstrated route capacity or connected routes**.

All 4,645 decap_8 and 17 decap_4 instances are individually assigned from the original placement inventory. Their pinned LEF sizes are 3.36 × 3.78 and 1.92 × 3.78 µm, on 0.48 × 3.78 µm CoreSite. The r4 site-aware allocation has **5,611 decap_8-sized sites**, 949 more than required, while avoiding 3 µm macro halos, the named signal corridors and ten 6 µm PDN-access lanes. Native GDS bbox overlap from legal standard-cell abutment is not used as extra area. Actual power-domain membership, new row ties and PDN access for each decap are **not run**; retaining their count is not equivalent to reconnecting them correctly.

## Ring control and failures retained

The original 43 µm power-ring band cannot be ignored or declared an unconditional all-layer exclusion. [Actual delivered-layer control](fit-ring-layer-screen-20260922-r2.json) identifies eight existing 15 µm ring conductors and proves every baseline macro has zero same-layer overlap. All-layer exclusion leaves only 470,884.1641 µm² at the earlier arithmetic 1,414.21 µm side, against 520,995.2772 µm² of proposed macros plus decap LEF area, before corridors: **failed**.

The earlier IO-window [r3 rectangle pack](coordinated-bbox-pack-20260922-r3.json) passed capacity but [failed the actual-net ring screen](fit-ring-net-screen-20260922-r1.json): the translated digital power stripes intersect a different source power net over 658.5796 µm² on west TopMetal1 and 378.5824 µm² on south TopMetal2. Source-net identities came from seven-metal physical connectivity, not labels. This failure motivated the separate ring-aware r4 placement; r3 is not retained-PDN fit evidence.

The native BGR proposal has no Metal5, TopMetal1/2 or TopVia1/2 geometry. The exact gm4 native MIM and two unchanged buffers have TopMetal1 and TopVia1, but no TopMetal2/TopVia2. [Ring-aware native/fill/via screen](fit-ring-net-screen-20260922-r3.json) found zero different-source-net intersections and passed a conservative 5 µm box-clearance screen for actual unchanged macro upper-metal drawing/local fill, projected TopVia1/2 cuts, exact BGR/gm4 native upper layers and the external MIM-tab reservation. The eight original ring rectangles were expanded in memory by 64 µm; this is not a generated or stock-checked new ring. The 5 µm screen conservatively covers stock TM1.b 1.64 µm, TM2.b 2 µm, filler-to-drawing 3 µm and wide/long TM2.bR 5 µm. It does not replace the complete decks. New BGR/SENSE fill, chip-level global fill, power-feed connectivity, contact access and under-ring coupling are **not run**.

For the revised 1,414 µm ring-aware outline, the separate all-layer-exclusion area condition still fails: 518,475.2772 µm² required versus 470,596 µm² available, before corridors. The bounded layer-aware screen is not a waiver of that failed alternative or permission to assume arbitrary lower-metal placement beneath the ring.

Earlier wide-corridor r1 and compact fixed-column r2 decap allocations failed at 3,735 and 4,323 sites. Their outputs and generator snapshot remain. Their legacy `retained_decap_counts` fields record the requested original inventory, not successful placement; status is failed and their actual placement arrays are incomplete. A source-hash literal typo stopped the first ring helper before reading geometry and is retained as a separate guard failure.

The 1,414 µm proposal replaces the unfillable 1,414.21 µm arithmetic outline. Stock IO fillers are **20, 10 and 2 µm** wide (names Filler4000, Filler2000, Filler400); pinned IO LEF SHA-256 `1100f050cd477b0db6072e1b2b53ee1e13d7e5473e7b5d20f27534cc27806320`. A 64 µm added row length can use unchanged stock fillers, e.g. three 20 µm plus two 2 µm cells. Ring/edge-seal generation, abutment connectivity, pad/bond geometry and full stock checks are **not run** for that outline.

## Required before a retained-PDN fit claim

The next gate must include exact expanded-ring/native upper-metal and via obstruction, actual different-net no-short and spacing, legal well/contact/guard placement, source-preserving device and decap accounting, explicit macro power access, connected signal corridors and under-ring coupling review. Then generate isolated candidate geometry and run unchanged stock DRC/LVS/antenna/density and affected extraction. Those steps require separate runtime/scope authorization; this report does not authorize them. Original full-IO failure and prior extraction/convergence failures remain unchanged. No broad MC investment or physical adoption is justified by rectangle arithmetic alone.

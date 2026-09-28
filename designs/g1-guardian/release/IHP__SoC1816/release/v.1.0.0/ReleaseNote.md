# SoC1816 release v.1.0.0

Release of the G1 guardian chip of record, revision r4 (adopted 2026-09-28 in
https://github.com/simra-tech/silicon).

| File | sha256 | Derived from |
| --- | --- | --- |
| `gds/SoC1816.gds` | `eb3e51a820c471a8991d23c2316c55c3c81fd47d11d4cd84d8e2081d6af4ff53` | `designs/g1-guardian/blocks/g1_padring/layout/g1_chip_top_1414_r4.gds` (`225d0b535321ed312594bb13d97b7271014f487162564a56c874572de715173a`): top cell renamed `g1_chip_top` -> `SoC1816`, re-saved with the IHP KLayout save options; geometry identical (304 cells, 1 284 438 shapes, 55 646 instances compared; `doc/provenance/compare_r4_vs_SoC1816.json`) |
| `netlist/SoC1816.cdl` | `755910c3338a0d1e68f39ed734fbe33fc80a4874847c24557c92018fc8925331` | `designs/g1-guardian/blocks/g1_padring/netlist/g1_chip_top_1414_r4.cdl` (`e060c0c59a168e5b69b0c47dc31cbfe4f4444d2ec8af62960c339c1230a2c99f`): one comment line added, top `.SUBCKT` renamed to `SoC1816` |

Sign-off on the source GDS (`225d0b53...`, top `g1_chip_top`, PDK decks at `84374023`, KLayout 0.30.9;
`doc/signoff-1414r4-20260927/README.md`):

| Check | Status |
| --- | --- |
| KLayout DRC main, maximal, precheck, density, antenna | passed, 0 markers each |
| IHP dev-branch DRC deck (`4fd47c5e`), same five | passed, 0 markers each |
| LVS against the projected reference (3 all-VDD pad dummy PMOS removed) | passed, 62 956 devices, 22/22 pins |
| LVS against the canonical netlist (`netlist/SoC1816.cdl` before rename) | **failed**: 14 IO / level-shifter sub-cells NoMatch; cause in the PDK IO-cell reference netlist semantics (IHP-Open-PDK issues #1218, #1130) |
| DRC / LVS re-run on `SoC1816.gds` itself | not run (geometry identity proven instead) |
| Full-chip PEX, IR/EM, timing of the final GDS | not run |
| IHP intake checks | not run |
| Physical measurement | not run |

Known points for the foundry review: see the source repository
`designs/g1-guardian/review/TAPEIN_PACKAGE_20260924.md` section 8 (IO-cell LVS, `Ant.e` on
`sg13g2_IOPadIn`, PolyRes on design-local IO cell copies, no DigiBnd around the standard-cell
macro, GFil.g margin 918.98 um2).

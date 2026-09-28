# SoC1816-main

Top cell `SoC1816` of the G1 guardian chip. The design sources (xschem schematics, block
layouts, simulation decks, LibreLane digital flow) live in https://github.com/simra-tech/silicon
under `designs/g1-guardian/`; they are not duplicated here.

- `verification/drc/`: copies of the KLayout DRC runs on the source GDS `g1_chip_top_1414_r4.gds`
  (`225d0b53...`): `drc_main`, `drc_maximal`, `precheck`, `density`, `antenna` (stock decks at PDK
  `84374023`) and `devdeck_check` (IHP dev-branch deck). All 0 markers. Copied, not re-run.
- `verification/lvs/`: `lvs_projected` (passed) and `lvs_canonical` (failed on 14 IO / level-shifter
  sub-cells, PDK IO reference semantics). Copied, not re-run.
- Report file names and log lines refer to the source GDS name and top cell `g1_chip_top`;
  the release GDS differs only in the top-cell name (see `release/v.1.0.0/doc/provenance/`).

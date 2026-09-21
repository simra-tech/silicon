# assembly-1350-r1 — superseded

Evidence of the first assembly run of record (2026-09-19 14:44–14:50, final GDS
sha256 `5325b02f454ad7e9862d3648dda1afbd9583c5a1068f0e77f141c3338576b121`).
Its KLayout DRC, density, antenna, routing, connectivity and STA results are
the ones listed here; they were all clean, and the layout was nevertheless
electrically wrong: the core-only KLayout LVS (`core_lvs/` of the superseding
run) found the supply nets VDDA, VSS and VDD joined. The causes, all in
`flow/analog_straps.tcl` version 1 (`INTEGRATION.md`, "Shorts found by LVS"):

1. the 8 µm TopMetal2 VDDA feed strap (y 384.2–392.2) covered the first
   horizontal VSS TopMetal2 stripe (y 385.36–387.56, x 324.8–1025.4) — VDDA–VSS;
2. the feed's Metal3/Metal4/Metal5/TopMetal1 patches reached 1.2 µm into the
   pad cell (x 1031–1032.2), onto the pad's vdd rail (Metal3) and vss rails
   (Metal4, Metal5, TopMetal1) — VDDA–VDD and VDDA–VSS;
3. the level shifters' vdd jog ran to the VDD TopMetal1 stripe at x = 529.1,
   which lies over `g1_osc`; the via stack landed on the oscillator's internal
   Metal3 at (529.1, 870.0) — VDD to an oscillator node.

None of the sign-off checks of the flow sees same-layer overlaps of different
nets (KLayout DRC merges them, `check_power_grid` tests each net alone, the
router's DRC does not cover special wires). Two geometric checks were added
(`flow/lvs/pdn_net_overlap.py`, `flow/lvs/pdn_macro_overlap.py`) and the
core-only LVS is the arbiter. The superseding run is `reports/assembly-1350/`.

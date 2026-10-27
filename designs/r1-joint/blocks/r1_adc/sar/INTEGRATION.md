# r1_adc_sar: integration into r1_adc layout B5 (T2j, D21)

This note tells ADC layout B5 how to place and connect the `r1_adc_sar` sub-macro. The release files are in
`<G1_RESULTS_ROOT>/r1_adc_sar/release-t2j-h/` (GDS, LEF, gate-level netlists, SDF, SPEF, `SHA256SUMS`). The source
of every number is the hardening run of record, `t2j-ll-h2312-h` (README "Status").

## 1. Box and placement

1. The macro is 439.0 × 23.12 µm (five 3.78 µm rows; the core is y 3.78–22.68 µm). The D21 box (439 × 15 µm) is
   too small: README "Area" gives the reason. B4 gives a free north band of 10.7 µm only (r1_adc README "North row
   for the SAR sub-macro"). Thus B5 must make the ADC box taller by 12.42 µm at least, or make the band below the
   macro free. The recommended option: extend the ADC box north by 23.12 µm (box 439.0 × 205.42 µm). Put the
   macro at (0, 182.3), orientation R0. Its north edge is then the ADC north edge. This changes the ADC box in the
   chip floor plan (open issue S2, README).
2. The macro x origin is the ADC x origin. The north pins are at the x positions of the ADC north pins of layouts
   A–B4, so the top-level routes to `r1_ctrl` do not change (`flow/pins.md`; the largest shift is 1.28 µm).
3. The south pins are at the x of the slice pins of layout B3 that they connect to (`flow/slice_pin_targets.json`,
   `reports/b3_sar_labels.txt`). B5 routes each south pin down to its slice port. Use Metal2 / Metal3 in the band
   between the macro and the slices; the macro routes use Metal1–Metal4 only (no Metal5, no TopMetal).
4. Keep the `r1_cmp4_clkgen` out of the macro box. The recommended B4 option (move it into the free band or under
   the decoupling MIM) still applies. Route `mclk` from the clock generator to the macro pin `mclk` on one short
   wire. `mclkb` is not used by the macro.

## 2. Pins

All signal pins are Metal2, 0.96 µm slots. North edge (y = 23.12): `adc_hold`, `is_smp`, `clk`, `adc_start`,
`cur_trk`, `adc_sel`, `adc_valid_a`, `adc_raw_a[0..13]`, `adc_valid_b`, `adc_raw_b[0..13]`, `por_n`. South edge
(y = 0): the 52 CDAC lines, the 8 comparator clocks, the 8 comparator outputs (`oap`, `oan`, `oanp`, `oann`,
`obp`, `obn`, `obnp`, `obnn`), `mclk` and the 4 track switches. The full table is `flow/pins.md`.

| Pin group | Connect to |
| --- | --- |
| `cpa[k]`, `cna[k]`, `cpb[k]`, `cnb[k]` | slice CDAC driver gate rails `sar_cpXk`, `sar_cnXk` (k = 12 is the first decision) |
| `clka`, `clkab`, `clkna`, `clknab` (and `b`) | `r1_cmp4` / `r1_cmp5n` clock and complement inputs of the slice |
| `oap`, `oan`, `oanp`, `oann` (and `b`) | comparator outputs. `oan`, `oann`, `obn`, `obnn` end on a dummy-load buffer so that both comparator outputs have the same load |
| `trka0`, `trka1`, `trkb0`, `trkb1` | track switch controls of the two slices (input pair 0 = SIN/COS, 1 = ISA/ISB) |
| `mclk` | `r1_cmp4_clkgen` output |
| north pins | the ADC north pins of the same name; `cur_trk` is new (open issue S1) |

## 3. Supplies

1. `VDD` (1.2 V) and `VSS` are eight Metal4 straps each, 1.6 µm wide, from y 3.56 to y 22.90 µm (LEF). `VDD` at
   x = 14.08 + 54 n, `VSS` at x = 17.28 + 54 n (n = 0 … 7), left edges. Every strap is a LEF pin, ≥ 1 µm wide (D21).
2. Connect `VDD` to the ADC `vdd` net (1.2 V). Drop Via4 arrays from a Metal5 bus to each `VDD` strap.
3. Supply current: see README "Status" (power report of the sign-off STA, typ). The switching current flows only
   in the `VDD` / `VSS` straps of the macro.

## 4. Ground separation

1. Connect `VSS` to the top-level `vss` sheet (TopMetal1) through its own drops: Metal4 strap → Via4 → Metal5
   island → TopVia1, one drop per `VSS` strap at least, as the eight slice drops of B4.
2. Do not join `VSS` to the slice `gnd` straps or to the Kelvin ground `gnd@K` inside the ADC box. The only common
   point is the top-level `vss` sheet. Reason: the CDAC drivers and the comparators share `gnd` (r1_adc README
   § Layout B), and the digital switching current must not flow in it.
3. The macro has no substrate tap pin. The standard cells tie the substrate to `VSS` through their own taps, so
   keep the slice guard ring between the macro and the slices.

## 5. LVS of the ADC with the macro

1. The ADC LVS reference gets the macro as a subcircuit: use `<release>/r1_adc_sar.lvs.spice` (the LibreLane
   `final/spice` netlist of the macro, with the antenna diode cell). Do not use `r1_adc_sar_gl_sim.spice` for LVS:
   it leaves the antenna cell out (simulation only). The extracted layout contains the standard cells as flat
   devices.
2. Use the PDK LVS deck with the two comparer search limits after `align` (`max_depth(8)`,
   `max_branch_complexity(100)`), as `r1_safe/layout/run_checks.sh` and `r1_top/lvs/run_lvs_top.sh`. These are
   comparer search limits only, no rule change. Run the stock deck as well and record both results: the stock
   deck crashed on the mixed `r1_safe` layout (r1_safe README failure 5).
3. The macro itself is LVS clean on its own (LibreLane netgen LVS, README "Status").

## 6. Checks after the integration (B5)

| Check | How |
| --- | --- |
| DRC main and maximal of the ADC with the macro | `layout/run_checks.sh` |
| LVS with the comparer-limit deck (and the stock deck) | § 5 |
| Pin check: every south pin reaches its slice port | B5 pin check against `flow/pins.json` |
| Post-layout mixed-signal: the r5 mux deck with the extracted ADC and the gate-level macro | `sim/gen_gl_deck.py` (the deck of record uses the schematic core) |

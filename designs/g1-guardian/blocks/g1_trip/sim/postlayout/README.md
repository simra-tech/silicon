# G1_TRIP post-layout netlists

`g1_trip_pex.spice` is the original macro (documented in the block README, "Post-layout").
`g1_trip_nf4_pex.spice` is the TRIP macro **as placed in the frozen chip**: soft comparator input pair
NF4 folded (W12/L0.34 -> W24/L0.68, four 6 um fingers) and hard comparator `g1_cmp_regenpair4`
(regenerative NMOS 6/0.26). It has the same `.subckt g1_trip` name and pin order as `g1_trip_pex.spice`,
so a deck can swap the include. Status: extraction and the comparator check **run**; DAC deck,
schematic-reference comparator runs, RC extraction, MC **not run** for NF4.

## Provenance (2026-09-24)

| Item | Identity |
| --- | --- |
| Source GDS | full-chip `soft-inputpair4-parent-20260924-r3/candidate.gds`, sha256 `60730627d24e1fb6b880138edc3e50fdd7c14624bb2dfbbc631e084b7415eca1` (the candidate of `reports/soft-inputpair4-folded-physical-20260924-r1`) |
| Macro cut | cell `__rz_port_text_033_retained_g1_trip` subtree copied by `reports/pex/nf4/cut_macro.py` (KLayout); top renamed `g1_trip`, sub-cells `__rz_port_text_03{5,4,3}_*` renamed `g1_cond`/`g1_cmp`/`g1_cmp_regenpair4`; geometry, layers and labels unchanged. Result `g1_trip_nf4.gds` sha256 `c8efefe331724ae7f9de075c15059cbd17d461ac8ce1d56640058ad4e04ed384` (bulk, not committed) |
| CDL | `reports/pex/nf4/g1_trip_nf4_lvs.cdl` = lines 2884-4031 (`BEGIN/END_SOURCE g1_trip`) of `candidate.cdl` (sha256 `984f82dd...8027f73`) verbatim plus one comment line; sha256 `fcc439a93cfeb5b2d8a202ba7bc86b2589dc7aec7258b26cd2c0b9047acfbb11` |
| Tools | pinned image `sha256:ddeb6957...b2`, PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`, KLayout 0.30.9, kpex (klayout-pex) 0.3.12, ngspice-46 (reported by the tools in the container) |

## Checks

| Check | Status | Evidence |
| --- | --- | --- |
| Block LVS, PDK `run_lvs.py --topcell=g1_trip --run_mode=deep` (options of `layout/run_checks.sh lvs`) | **passed** (netlists match, 0 errors, 5.8 s) | `reports/pex/nf4/lvs_g1_trip.log` |
| DAC LVS `--topcell=g1_dac8 --no_series_res` | **passed** (4.9 s) | `reports/pex/nf4/lvs_g1_dac8_noseries.log` |
| kpex 2.5D CC | run, rc 0, **761 s** (12.7 min) on one CPU | `reports/pex/nf4/kpex_cc.log` |
| kpex internal LVS | failed (expected, same as the original run: flat, MIM-less input, `no_simplify`); not signoff | same log |
| Comparator post-layout, tt 1.2 V 27 C and ss 1.08 V -40 C, 5 MHz | run, all decisions right | `results_postlayout_nf4.txt`, `logs/nf4pex_*` |

PEX input and extraction (bulk directory `${BULK}`; the internal labels `vth_soft`, `vth_hard`, `icmp`,
`cmp_clk_n` were stripped by chip integration and are re-added to the PEX input only, at the original
macro's coordinates, from `reports/pex/nf4/g1_trip_nf4_pexlabels.txt` placed next to the GDS; the
resulting nets were checked against device gates):

```
G1_WORKDIR=designs/g1-guardian/blocks/g1_trip/layout flow/run.sh klayout -b -r pex_input.py -rd gds=${BULK}/g1_trip_nf4.gds -rd out=${BULK}/pex/g1_trip_nf4_pexin.gds
flow/run.sh kpex --pdk ihp_sg13g2 --gds ${BULK}/pex/g1_trip_nf4_pexin.gds --cell g1_trip --schematic ${BULK}/g1_trip_nf4_lvs.cdl --2.5D --mode CC --out_dir ${BULK}/pex/cc
python3 make_pex_netlist.py trip ${BULK}/pex/cc/g1_trip_nf4_pexin__g1_trip/g1_trip_k25d_pex_netlist.spice g1_trip_nf4_pex.spice
```

kpex netlist sha256 `0d0a864a99229559ae2a8b1f39024e2dc7f66b315d7d7fc2c929d47c005eee51`; `g1_trip_nf4_pex.spice`:
1246 MOS (the folded pair extracts as 4+4 fingers of 6/0.68), 1080 resistors, 18 333 parasitic
capacitors, 3 re-inserted `cap_cmim`. Simulated wiring capacitance: soft input-pair drains 15.32/15.30 fF
(2.44/2.41 fF to clock; original 12.43/12.40 and 2.69/2.66), `vth_soft` 15.1 fF (11.9), `icmp` 29.0 fF (25.9).

## Comparator (simulated, kpex CC netlist, same deck as the original)

`G1_WORKDIR=designs/g1-guardian/blocks/g1_trip/sim PEXNET=postlayout/g1_trip_nf4_pex.spice PEXTAG=nf4pex RESULTS=postlayout/results_postlayout_nf4.txt flow/run.sh bash postlayout/run_postlayout.sh cmppex`

| Corner, overdrive | original PEX: od at 1st strobe / eff. od / delay | NF4 PEX: od at 1st strobe / eff. od / delay |
| --- | --- | --- |
| tt 1.2 V 27 C, 50 mV | -51.1 / 49.1 mV / 0.579 ns | -52.9 / 49.7 mV / 0.675 ns |
| tt 1.2 V 27 C, 5 mV | -6.0 / 4.19 mV / 0.708 ns | -7.4 / 4.77 mV / 0.796 ns |
| tt 1.2 V 27 C, 1 mV | -2.02 / 0.20 mV / 0.856 ns | -3.89 / 0.77 mV / 0.859 ns |
| ss 1.08 V -40 C, 50 mV | -50.6 / 49.3 mV / 0.845 ns | -51.8 / 49.9 mV / 1.014 ns |
| ss 1.08 V -40 C, 5 mV | -5.6 / 4.39 mV / 1.245 ns | -6.9 / 4.95 mV / 1.435 ns |
| ss 1.08 V -40 C, 1 mV | -1.61 / 0.40 mV / 1.778 ns | -2.88 / 0.95 mV / 1.694 ns |

Every first strobe decided low and every second strobe high. Systematic offset bracket (tt), referred to
the comparator input `icmp` (divide by about 10 for shunt voltage: 1 LSB = 1.962 mV at `icmp` = 0.196 mV shunt): between
-3.9 mV and +0.77 mV (original -2.0 / +0.2 mV); the bracket is set by the kick residue, not resolved
further. The strobe kick on `vth_soft` is larger: minimum 0.670 V vs 0.719 V (tt, -81 mV vs -33 mV from
0.7515 V), still -11 mV at 70 ns (original -4 mV). Wiring resistance, mismatch and the DAC deck are not run.
The strobe-train section below measures what this does over continuous operation.

## Kickback over a continuous strobe train (simulated)

`tb_trip_kick_train.cir` (run by `run_kick_train.sh`, analysed by `kick_train.py`; numbers in
`results_postlayout_nf4.txt`): 5 MHz clock, 21 soft + 21 hard strobes (4.25 us), DAC at the reset
defaults (soft 0x99, `vth_soft` 0.8006 V; hard 0xFE, `vth_hard` 0.9988 V), ISENSE an ideal source with
`icmp` 1 LSB (VREF/530 = 1.962 mV) below the DC threshold of the comparator under test. Node values are
taken just before each strobe edge, minus the DC operating point. "Shift" = dvth - dicmp referred to
`icmp`; referred to the shunt it is /10. The residual reaches steady state by the second strobe, so
worst equals steady state to within 0.01 mV.

| Corner | Extraction | soft strobe: dvth_soft / dicmp / shift (mV) | hard strobe: dvth_hard / dicmp / shift (mV) | soft / hard decided high at -1 LSB |
| --- | --- | --- | --- | --- |
| tt 1.2 V 27 C | old | +0.70 / +0.01 / +0.69 (0.35 LSB) | +0.06 / +0.09 / -0.03 | 0/21, 21/21 |
| tt 1.2 V 27 C | NF4 | +2.05 / +2.30 / -0.25 (0.13 LSB) | +0.06 / -3.80 / +3.86 (1.97 LSB) | 11/21, 21/21 |
| ss 1.08 V -40 C | old | +0.52 / -0.00 / +0.53 (0.27 LSB) | +0.03 / +0.08 / -0.05 | 0/21, 21/21 |
| ss 1.08 V -40 C | NF4 | +1.52 / +1.86 / -0.34 (0.18 LSB) | +0.03 / -3.18 / +3.22 (1.64 LSB) | 10/21, 21/21 |
| ff 1.32 V 125 C | old | +0.97 / -0.05 / +1.02 (0.52 LSB) | +0.13 / +0.01 / +0.12 | 0/21, 21/21 |
| ff 1.32 V 125 C | NF4 | +2.94 / +2.81 / +0.13 (0.07 LSB) | +0.14 / -5.04 / +5.17 (2.64 LSB) | 10/21, 21/21 |

Measured just before the strobe edges, the steady-state shift with the NF4 pair stays under 1 LSB on the
soft path; the old extraction is at most 0.52 LSB at ff. On the hard path it is 1.6-2.6 LSB (0.32-0.52 mV shunt), and the
worst is ff. `vth_soft` alone moves by 1.0-1.5 LSB, and in the hard-condition runs it moves by -0.9 to -1.9
LSB. The edge samples leave out part of the effect, and the decision counts show it:
- soft, NF4: about half of the strobes trip at 1 LSB below threshold and none at 2 or 3 LSB (tt), so the
  soft path trips 1-2 LSB early (0.2-0.4 mV shunt). The old extraction trips none at 1, 2 or 3 LSB.
- hard, **both extractions**: every strobe trips at 1, 2, 3, 4 and 6 LSB below threshold (tt, 8-strobe
  runs), so the hard path trips more than 6 LSB early (more than 12 mV at `icmp`, 1.2 mV shunt). The
  hard strobe edge coincides with the soft comparator's reset edge. Within 0.5 ns of that edge,
  icmp - vth_hard jumps by +40 mV (old) and +116 mV (NF4) while the hard comparator decides (waveforms
  in the tt runs). This problem already existed with the old macro, and the NF4 pair makes it worse.
  This 8-strobe run does not bracket the hard threshold; the strobe-train bench in "Effective trip
  point" below does (hard path 40–56 LSB below code with NF4, simulated).

Explicit capacitance on these nodes: `vth_soft`, `vth_hard` and `icmp` each have one 26 x 26 um `cap_cmim`
hold capacitor (CHS, CHH, and CH in `g1_cond`, about 1 pF each). They are behind the DAC string and the
25 kOhm divider. These capacitors could be made larger, and that would lower the between-strobe residual.
The what-if section below shows that a larger CH/CHH/CHS also reduces the effect of the coincident-edge kick. Layout is not changed.
The ISENSE source is ideal (a real sense-amplifier output impedance adds to the icmp kick); mismatch is not
included.

## Effective trip point, strobe-train bench (simulated)

`kick_threshold.py` (the driver) runs `run_kick_train.sh` with 0.8 us trains, 4 strobes per comparator. The first strobe is
skipped. A run trips when at least 2 of strobes 1-3 are high. The driver brackets the underdrive of `icmp`
below the DC threshold with coarse steps (hard 8, 12, 16, 24, 32, 48, 64; soft 0, +/-2, ...), then bisects to 1
LSB. The table gives "code - N" with N the largest underdrive that still trips; the effective threshold lies
between N and N+1 LSB below the code. 1 LSB = 0.196 mV of shunt voltage. Soft code 0x99. Raw rows are in
`results_postlayout_nf4.txt`. Mixed decisions (1 of 3 or 2 of 3) occurred only at the NF4 soft N = 1 and the
old hard tt code-200 N = 18 points.

| Path, code | Extraction | tt 1.2 V 27 C | ss 1.08 V -40 C | ff 1.32 V 125 C | spread |
| --- | --- | --- | --- | --- | --- |
| hard 0xFE | old | 254 - 20 (-3.92 mV) | 254 - 17 (-3.34 mV) | 254 - 23 (-4.51 mV) | 6 LSB |
| hard 0xFE | NF4 | 254 - 51 (-10.01 mV) | 254 - 46 (-9.03 mV) | 254 - 56 (-10.99 mV) | 10 LSB |
| hard 200 | old | 200 - 18 (-3.53 mV) | 200 - 15 (-2.94 mV) | 200 - 21 (-4.12 mV) | 6 LSB |
| hard 200 | NF4 | 200 - 46 (-9.03 mV) | 200 - 40 (-7.85 mV) | 200 - 51 (-10.01 mV) | 11 LSB |
| soft 0x99 | old | 153 + 1 (+0.20 mV) | 153 + 1 (+0.20 mV) | 153 + 1 (+0.20 mV) | 0 |
| soft 0x99 | NF4 | 153 - 0 (0.00 mV) | 153 - 1 (-0.20 mV) | 153 - 1 (-0.20 mV) | 1 LSB |

The soft path stays within 1 LSB of its code value, and its spread across corners is at most 1 LSB. The hard path trips early in
both extractions: 15-23 LSB with the old macro and 40-56 LSB with NF4, which is 7.9-11.0 mV of shunt voltage. The early
trip also depends on the code: it is 2-5 LSB smaller at code 200 than at 0xFE. Across corners it varies by 6 LSB
(old) and 10-11 LSB (NF4), which is more than 2 LSB, so a single room-temperature calibration does not absorb
it. The mechanism is the coincident edge described in the previous section: the soft comparator's reset kick lands on
`icmp` while the hard comparator decides. The bench has an ideal ISENSE source and no mismatch. The
threshold was bracketed at DAC codes 254 and 200 only. Corners other than tt/ss/ff (above) are **not run**.

## What-if: larger hold capacitors, delayed hard clock (simulation only, no layout change)

`make_variant.py` writes derived copies of `g1_trip_nf4_pex.spice`; the extraction itself is unchanged.
- `caps=K` adds K-1 identical 26x26 `cap_cmim` in parallel with CHS, CHH and CH.
- `hclk=D` disconnects `cmp_clk_n` from the clock inverter and drives it from an ideal source: the inverted
  bench clock, delayed D ns. `d0` is that ideal clock with no delay.

The trip points use the bisection bench above; mV are shunt voltage.

| Variant | hard 0xFE tt / ss / ff | hard 200 tt / ss / ff | soft 0x99 tt / ss / ff |
| --- | --- | --- | --- |
| x1 (as extracted) | -51 / -46 / -56 LSB (spread 10) | -46 / -40 / -51 (11) | 0 / -1 / -1 |
| x2 | -26 / -24 / -28 (spread 4; -4.71..-5.49 mV) | -23 / -21 / -25 (spread 4; -4.12..-4.91 mV) | 0 / 0 / 0 |
| x4 | -11 / -11 / -12 (spread 1; -2.16..-2.35 mV) | -10 / -9 / -10 (spread 1; -1.77..-1.96 mV) | +1 / +1 / +1 |
| x8 | -4 (-0.78 mV) | -4 (-0.78 mV) | +1 |
| ideal hard clock, delay 0 / 5 / 10 / 20 ns (x1 caps) | -3 / -47 / -41 / -30 | not run | not run |

Side effects, tt, x1 / x2 / x4 / x8 (`tb_trip_settle.cir`, clock static, no strobe kicks):
- `vth_hard` within 1 LSB after the DAC step 254 -> 200: 104 / 154 / 263 / 487 ns.
- `icmp` within 1 LSB after a 100 ns ISENSE ramp (to 10 LSB above the code-200 threshold): 227 / 358 / 626 / 1168 ns
  from the start of the ramp.
- `icmp` crosses `vth_hard` (code 200) after 157 / 229 / 380 / 688 ns for the 10-LSB fault, and after
  96 / 118 / 168 / 274 ns for the 2.2 V fault. The hard path needs 4 consecutive decisions, so its detection
  latency is the crossing time + up to 200 ns to the next strobe + 600 ns.
- Comparator delay deck (`tb_trip_cmp_pex.cir`, nominal 5 mV step 1 ns after a strobe):
  - x1: 0.796 ns at an effective overdrive of 4.77 mV.
  - x2: 0.805 ns at 4.96 mV.
  - x4, tt: 0.851 ns at 2.67 mV.
  - x4, ss: 1.632 ns at 3.03 mV.

  With x4, `icmp` settles only about halfway within one 200 ns period. The 1 mV step then reaches the strobe as
  -0.07 mV at tt, so no rising decision occurs (the delay deck assumes a settled input). Later runs: x2 ss 1.474 ns at 5.22 mV. x8: only 0.04 mV (tt) and 0.28 mV (ss)
  reach the strobe, so there is no rising decision at tt, and at ss the delay is 2.44 ns.

MIM area:
- The PDK `cmim_core` has 1.5 fF/um2 plus 40 aF/um of perimeter (`cornerCAP.lib`, `capacitors_mod.lib`), so
  26x26 um gives 1.018 pF and 4 pF needs about 2660 um2 (51.6 um square).
- Existing MIM in the macro: three 26x26 squares, 2028 um2. The macro footprint is 47 403 um2.
- 42 818 um2 is free of drawn Metal5, TopMetal1 and MIM, counting both the macro and the full-chip shapes over it.
  The full-chip Metal5 and TopMetal1 fill over the macro (15 585 and 1 917 um2) is not counted as blocking.
- Greedy packing of 26x26 squares with 1.5 um margin: 3 fit in the top strip (y >= 151 um; at x 8, 129.5 and 199 um,
  next to g1_cond, the soft and the hard comparator), 20 in the whole footprint.
- So x2 (3 extra squares) fits beside the existing caps. x4 (9 extra) fits only over the DAC arrays. x8 (21 extra)
  does not fit.
- Plate connections to the nodes and fill regeneration are extra layout work that is not estimated here. The squares
  near the comparators would lie over circuitry.

### Unadopted layout candidate nf4_hold2x (2x)

`layout/candidates/nf4_hold2x/` holds this candidate; it is **not adopted**. Three 26x26 cmim are drawn in
parallel with the hold capacitors. PDK DRC (main + maximal) passed, and LVS against the explicitly edited CDL
passed. Its kpex extraction is `g1_trip_nf4_hold2x_pex.spice`. The extraction input is identical to the NF4
one, because the added layers are removed before kpex, so this netlist equals the x2 parallel-cap variant.
Its tt brackets confirm that: hard 0xFE 254 - 26, hard 200 200 - 23, soft 153 - 0.

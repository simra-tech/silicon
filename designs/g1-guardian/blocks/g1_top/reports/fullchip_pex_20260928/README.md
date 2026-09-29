# Full-chip parasitic extraction of the r4 GDS (track T1, 2026-09-28)

Chip of record r4, `blocks/g1_padring/layout/g1_chip_top_1414_r4.gds` (SHA-256 `225d0b53…`, top
`g1_chip_top`, same geometry as the submitted `SoC1816.gds`). Every value here is **extracted from
layout or simulated**. Nothing is measured.

**Result in one paragraph.** A flat kpex 2.5D extraction of the whole chip does not finish: the
bounded attempt on the fill-free r4 GDS was still in the first (substrate-overlap) pass at the 12 h
bound (§2), and its own progress extrapolates to about 6 days for that pass alone. The hierarchical route was taken
instead (§3): block extractions as before, plus a new extraction of the **top-level routing with
series R and C for every top-level net, the supply nets included** (KLayout's R extractor on the
routing view, Kron-reduced to pin nodes, joined with the kpex 2.5D C of the same view). The chip
deck (`run_top_cdl.py --interconnect extracted-rc`) runs with it. Simulated results (§4): the extracted R+C changes the chip's trip timing by
at most 0.2 ns (c_mid 1.8×, `GATE` < 1 V at tt / ss 125 °C / ff −40 °C: 1.54318 / 1.72631 /
1.43361 µs against 1.54315 / 1.72629 / 1.43340 µs with the C-only interconnect); 1.25× and `q` still do not trip.
New finding: the top-level route R moves both DAC thresholds of G1_TRIP down by 4.3-5.2 mV
(`vth_hard`) because the TRIP block draws about 40 µA from `VREF_BUF` through its 136 Ω route
(5.2-6.1 mV drop), and ISENSE arrives 1.9-2.4 mV lower at the TRIP pin; net, the hard threshold
moves about 0.43-0.47 mV (about 2 LSB) lower referred to the shunt (derived). The per-part bench calibration
absorbs this. The `VREF` mean is unchanged; its clock ripple is 43 mV p-p at the BGR and 48 mV at the SENSE pin (tt).
With the transistor-level oscillator clocking the RTL the decision lands 5.6-8.9 ns later (ff −40 °C, tt), a
clock-phase effect of a 0.03-0.05 % lower oscillator frequency; at ss 125 °C that case did not run to completion (numerical).

## Built against

| Item | Value | How established |
|---|---|---|
| Layout | `blocks/g1_padring/layout/g1_chip_top_1414_r4.gds` `225d0b535321ed31…` | `sha256sum`; `strip_fill_r4.json` `input_sha256` |
| Chip netlist | `blocks/g1_padring/netlist/g1_chip_top_1414_r4.cdl` `e060c0c59a168e5b…` | `sha256sum`; `run_top_cdl.py --cdl-sha256` |
| PDK | IHP-Open-PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` | `flow/run.sh` commit check, every run log header |
| Container | `tapeoutbench-eda:latest` `sha256:ddeb6957…` | `flow/run.sh` image check |
| KLayout | 0.30.9 (also `klayout.pex` R extractor) | `klayout -v` in the container |
| kpex | 0.3.12, 2.5D engine, `--mode CC`; tech `ihp-sg13g2_tech.pb.json` `6ece2ac7…` | `kpex --version`, `sha256sum` |
| ngspice | 46, with the PDK OSDI models; Icarus Verilog 14.0 for the RTL co-simulation | `ngspice -v`, `iverilog -V` |
| numpy / scipy (Kron reduction, effective R) | 2.5.1 / 1.18.0 | `python3 -c 'import numpy, scipy'` in the container |
| CPUs | 73-88 (`taskset`, `flow/launch_pinned.sh`, one CPU per run, nice 0) | campaign brief allocation |

Bulk outputs are under `${BULK}/pex/` (`${BULK}` = the post-submission campaign root).

## Status

| Check | Status | Evidence |
|---|---|---|
| Fill strip of r4 | passed (279 947 fill shapes removed, nothing else) | §1, [strip_fill_r4.json](strip_fill_r4.json) |
| Whole-chip kpex 2.5D CC, fill-free, 12 h bound | **not run to completion** (29.7 % of the first of three passes at 12 h; about 6 days extrapolated) | §2 |
| Whole-chip kpex with fill | not run (the fill-free run already cannot finish) | §2 |
| Top-interconnect view of r4 (net identity, shorts) | passed (0 shorts; opens as known) | §3.1 |
| Top-level C, kpex 2.5D CC on the view | passed (ran; identical to the 25 Sep r1-geometry lumps on all 57 routed nets) | §3.2 |
| Top-level R, pin-to-pin networks for every net incl. supplies | passed (ran, 346 nets) | §3.3, [rnet_summary.json](rnet_summary.json) |
| kpex `--mode RC` on the view | ran; output not usable (0 pins) | §3.3 |
| Per-net R and C file for T3 | written (`${BULK}/pex/top_rc_nets.json`, copy [top_rc_nets.json](top_rc_nets.json)) | §3.3 |
| Chip deck with distributed R+C, `c_mid` 1.8×, tt / ss 125 °C / ff −40 °C | passed (simulated) | §4 |
| `c_mid` 1.25×, three corners | passed, no trip (simulated) | §4 |
| `q`, three corners | passed, no trip (simulated) | §4 |
| `osc` (transistor-level oscillator), tt | passed (simulated; reltol 5e-4 after two numerical failures) | §4 |
| `osc`, ff −40 °C | trip measured, then **failed (numerical)** at 18.24 µs after the trip (numbers usable) | §4 |
| `osc`, ss 125 °C | **not run to completion** (numerical failure at 1.81 µs; other settings reached at most 3.45 µs of 19 µs in 3.9 h) | §4 |
| `VREF`/`VREF_BUF`/`ISENSE` driver-side and receiver-side levels and ripple, three corners | passed (simulated) | §4 |
| Full-chip netlist simulation (every device extracted, digital at transistor level) | not run (no full-chip extraction exists; see §2) | — |

## 1. Fill removal

`flow/pex/strip_fill.py` removed every datatype-22 shape (PDK `<layer>.filler`) from a copy of r4:
279 947 flat shapes (Activ 28 568, GatPoly 30 516, Metal1 49 962, Metal2 60 648, Metal3 32 154,
Metal4 32 361, Metal5 33 156, TopMetal1 5 640, TopMetal2 6 942), 4 907 262 → 4 627 315 flat shapes,
5.1 s. Output `g1_chip_top_1414_r4_nofill.gds` `208f2103…` (bulk). Report:
[strip_fill_r4.json](strip_fill_r4.json). Nothing but fill was removed.

## 2. Whole-chip kpex 2.5D CC (not run to completion)

Why the 25 Sep attempt stopped, from its logs (`${BULK}/../fullchip-pex-20260925/kpex_nofill/`):
`run.log` and `run2.log` exited with rc 1 on `Layout.top_cell` "multiple top cells" (an unplaced
device-abstract cell `D$sg13_hv_pmos$33` in the LVSDB; peak RSS 2.5 / 3.8 GB, so not memory);
`run3.log` (`kpex_named_top.py`, top cell by name) reached the 2.5D engine and was killed by hand at
its 2 h time box, with no output. The instrumented copy showed the cause: the substrate-overlap pass
visits every polygon and subtracts a shielded region that grows with each visit, so its cost is
quadratic in the polygon count. Memory was never the limit.

This run: `kpex_progress_probe.py` (= `kpex_named_top.py` plus counters, results identical) with
`--gds` on the fill-free r4 and `--schematic` the r4 CDL, one CPU (73), wall bound 43 200 s (12 h).
The LVS stage and layer preparation took about 2.5 min; the 2.5D engine then started the
substrate-overlap pass over 477 498 merged polygons (GatPoly 172 646, Metal1 154 814, Metal2 83 934,
Metal3 45 047, Metal4 10 171, Metal5 7 928, TopMetal1 1 934, TopMetal2 986, 38 others). At the
bound (42 986 s of engine time) it had visited 142 000 of them (29.7 %) of the first of its three
passes; no output file was written. A quadratic fit of the 71 progress points (t = 798 − 0.055·n +
2.37·10⁻⁶·n² s, largest residual 1 022 s) extrapolates the first pass alone to **5.2·10⁵ s ≈ 6.0 days**
(the 25 Sep estimate on r1: 5.5 days). Peak RSS 2.71 GB (the machine has 755 GB): memory is not
the limit, the algorithm is. As on 25 Sep, when the bound expired the host-side launcher exited but
the containerised process kept running with no `.rc` file; it was stopped by hand at 02:13 (12 h 3 min).
Progress log: [kpex_full_progress.txt](kpex_full_progress.txt). The hierarchical route (§3) was
therefore used, as the campaign brief prescribes; it was run in parallel from the start.

## 3. Hierarchical route: top-level routing R and C of every top-level net

### 3.1 View and net identity

`flow/pex/prepare_top_interconnect.py` on the fill-free r4 with the r4 CDL: the top cell's own
shapes and the routing-only cells are kept; every block macro, level shifter, IO cell and standard
cell is replaced by its pin shapes. 15 435 pin shapes, 1 222 connected clusters, 345 carry a CDL
name, **0 shorts**. Opens are the known ones (IO-cell pin stacks on several layers, the IO ring
supplies, which run inside the `sg13g2_io` cells, and T2F `vref`). XOR of the r4 view against the
25 Sep r1 view: 22 Metal1 polygons, 2.2 µm², all unlabelled pin shapes inside the TRIP macro
(`nf4_novclk`), none touching a route ([xor_view_r1_r4.txt](xor_view_r1_r4.txt)).

### 3.2 Capacitance: kpex 2.5D CC on the view

`make_view_lvsdb.py` + `kpex_named_top.py --mode CC`, one CPU: 6 min 55 s wall, 2.33 GB peak RSS,
6 228 capacitors. `make_top_interconnect_spice.py` gives the same lumps as the 25 Sep extraction for
**all 57 routed signal nets (R and C identical to 0.001)**: the r4 routing is the r1 routing.

### 3.3 Resistance: pin-to-pin networks, supplies included

New tool `flow/pex/top_route_rnet.py`: KLayout's `klayout.pex.RNetExtractor` (the engine behind
`kpex --mode RC`; square counting on wires, R per via cut) on every labelled net of the view, with
the black-box pin shapes as ports, kpex ihp-sg13g2 sheet and via tables converted as kpex does.
346 nets, 7.9 s, 162 MB. kpex's own `--mode RC` on the view was also run (8 min 22 s, 2.8 GB): it
reports "found 0 pins" (the view LVSDB has no circuit pins), so its 62 599 resistors have no port
anchors and are **not used**.

Per-net route R (effective, from the reference pin: the driving block, or the pad for chip-pin
nets; all other pins open) and C (kpex, fF). The full list of 57 nets, with pins and couplings, is
[top_rc_nets.json](top_rc_nets.json) (also at `${BULK}/pex/top_rc_nets.json` for T3);
the networks per net are summarised in [rnet_summary.json](rnet_summary.json).

| Net | series-R upper bound (Ω) | effective R from the reference pin (Ω) | C to ground (fF) | C to other nets (fF) | total C (fF) |
|---|---|---|---|---|---|
| `i_core_isense` | 140 | trip 140 | 6.4 | 58.1 | 64.5 |
| `i_core_vref` | 447 | sense 141; Xpad18_vref 259 | 35.6 | 135.2 | 170.8 |
| `i_core_vref_buf` | 137 | trip 136 | 10.3 | 34.5 | 44.8 |
| `i_core_iptat` | 158 | sense 157 | 13.4 | 31.0 | 44.4 |
| `i_core_pbias` | 233 | t2f 232 | 9.9 | 129.5 | 139.4 |
| `i_core_pcasc` | 232 | t2f 231 | 20.6 | 75.0 | 95.7 |
| `SENSE_P` | 172 | Xpad08_sense_p 170 | 30.9 | 0.5 | 31.3 |
| `SENSE_N` | 106 | Xpad09_sense_n 105 | 20.0 | 0.3 | 20.3 |
| `i_core_cmp_soft` | 541 | trip 483; antenna cell@1021.440,891.000 491; antenna cell@1022.880,891.000 492 | 39.0 | 230.8 | 269.7 |
| `i_core_cmp_hard` | 422 | gate 88; trip 380 | 24.3 | 156.4 | 180.7 |
| `i_core_cmp_clk` | 283 | trip 280 | 34.3 | 88.2 | 122.5 |
| `i_core_osc_clk` | 417 | osc 415 | 21.9 | 123.1 | 145.0 |
| `i_core_tripped` | 364 | gate 82; antenna cell@1027.200,891.000 351 | 28.0 | 115.3 | 143.2 |
| `i_core_trip_d` | 57 | gate 56 | 2.0 | 24.2 | 26.2 |
| `gate_o` | 216 | Xpad10_gate 215 | 20.8 | 59.2 | 80.0 |
| `fault_n_o` | 290 | Xpad11_fault_n 287 | 36.5 | 24.9 | 61.4 |
| `en_i` | 478 | gate 101; Xpad12_en 389; antenna cell@1020.000,891.000 348 | 43.1 | 78.6 | 121.7 |
| `i_core_sclk_i` | 412 | Xpad14_sclk 410 | 54.3 | 103.6 | 157.9 |
| `i_core_sdi_i` | 709 | Xpad15_sdi 383; antenna cell@1024.320,891.000 704 | 105.1 | 60.3 | 165.4 |

Supply routes, R from the ideal pad-ring node to each block supply pin (Ω; the ring rails inside
the IO cells are not in the view):

| Net | digital | trip | sense | gate | osc | t2f | ls_en | ls_mode | ls_r4 | dose | dut |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `VDD` | 2.7 | 3.9 | — | 4.9 | 5.2 | 4.7 | 15.8 | 16.7 | 14.5 | — | — |
| `VDDA` | — | 4.3 | 2.9 | 9.8 | — | 7.1 | 23.9 | 19.5 | 21.7 | — | — |
| `VSS` | 2.4 | 3.2 | 2.0 | 3.2 | 6.6 | 4.5 | 10.5 | 9.4 | 10.2 | 3.4 | 3.4 |

The BGR supply pins are not on the top-level supply routes in this view (they are joined inside the BGR macro and its overlay), so no BGR row value is given; the BGR sees the ideal pad-ring node in the deck. IOVDD/IOVSS have no core-level routes (the ring only).

### 3.4 Distributed RC netlist for the chip deck

`flow/pex/make_top_rc_spice.py` builds element lines for the deck-local `g1_chip_top`:

- each fragment's resistor network is Kron-reduced onto its pin nodes (exact at DC);
- every block pin on a routed net gets its own node `<net>__<instance>` (88 pin renames on 20
  instances, listed in the map JSON); IO-cell supply pins and chip-pin pads stay on the net node;
- networks that reach no other pin (BGR `vdd`/`vss`, `dvbe`, T2F `vref`, the analog pads' unused
  `padres` nets) are merged into the net node (14 cases, `tied_to_N` in the map);
- the kpex C: every entry with a routed fragment on one side (as in the 25 Sep lumps), placed on the
  fragment's pin nodes, couplings to the nearest pin node of the other net. Bondpad C and
  pin-to-pin C inside IO cells are left out, as before.

Result: 334 R and 4 759 C, `sim/postlayout/top_interconnect_rc_r4_20260928b.spice` with
`…_map.json` (hash-bound in `run_top_cdl.py`). The first version (`…_20260928.spice`, option
`--interconnect extracted-rc-v1`, runs at tt and ff) tied those 14 networks to their net by a 1 mΩ
resistor instead; at ss/125 °C that made the operating point take 12-21 min and the transient
crawl (0.3-0.8 µs per 1000 s), so revision b merges them. The two versions are electrically the
same network (1 mΩ versus 0 Ω on pins with no other connection).

## 4. Chip deck with the new parasitics (simulated)

Deck: the r4 full-chip CDL deck of [`../../sim/FULLCHIP_CDL_R4_20260927.md`](../../sim/FULLCHIP_CDL_R4_20260927.md)
(r4 CDL, blockset `c1414r4`: BGR586 kpex, SENSE R100 partial C, TRIP `nf4_novclk` kpex, GATE PEX,
T2F PEX, OSC CPEX with `--osc tl`; ECO RTL co-simulated; IO pads without `dantenna`; T2F on) with
`--interconnect extracted-rc` in place of `--interconnect extracted` (C only). The reference is the
same deck with `--interconnect extracted`, the `c1414r4` extracted-interconnect runs of the r4
campaign (`r4a`/`r4b`/`r4c`) or, where none existed, a reference run made here (tag `t1rc`, `_icx`).

"v1" rows ran with the first RC netlist (now `--interconnect extracted-rc-v1`), "rev. b" rows with
`--interconnect extracted-rc` (§3.4); the two differ only by 1 mΩ on pins without another connection.

Times from the load event, `trip_d` / `tripped` / `GATE` < 1 V / `GATE` < 0.33 V (µs); cause 2 = hard.
Run tags: `cdl_<case>_pex_<corner>_gear_…_icxrc…_t1rc` (RC) in `sim/logs/`, extracts `.tail.txt` there,
full logs in `${BULK}/pex/logs_sim/` (`MANIFEST.json` with their SHA-256), decks in `${BULK}/pex/decks/` (`SHA256SUMS`; each run JSON carries its `deck_sha256`). All values simulated. Summary file: [sim_results.json](sim_results.json).

### 4.1 Trip timing and no-trip cases

| Case | Corner | Extracted R+C (this work) | C-only reference | Δ `GATE` < 1 V | Status |
|---|---|---|---|---|---|
| `c_mid` 1.8× | tt 27 °C | 1.16387 / 1.16664 / **1.54318** / 1.77922 (v1, 1 ns, `--tstop 19`) | 1.16386 / 1.16662 / 1.54315 / 1.77919 (`r4b`) | +0.03 ns | passed |
| `c_mid` 1.8× | ss 125 °C | 1.16377 / 1.16775 / **1.72631** / 2.05966 (rev. b, 2 ns, `--tstop 19`); 1 ns: 1.16374 / 1.16772 / 1.72628 / 2.05963 | 1.16377 / 1.16774 / 1.72629 / 2.05965 (`r4a`, 5 ns) | +0.02 ns | passed |
| `c_mid` 1.8× | ff −40 °C | 1.16386 / 1.16579 / **1.43361** / 1.61275 (v1, 1 ns) | 1.16367 / 1.16560 / 1.43340 / 1.61255 (`r4a`) | +0.21 ns | passed |
| `c_mid` 1.25× (31.25 mV) | tt | no trip; `tripped` max 11.0 mV, `GATE` min 3.298 V (v1, `--tstop 19`) | no trip; 7.2 mV (`r4b`) | — | passed |
| `c_mid` 1.25× | ss 125 °C | no trip; 12.0 mV, 3.299 V (rev. b, 2 ns, `--tstop 19`) | no trip; 10.4 mV (`r4a`, 5 ns) | — | passed |
| `c_mid` 1.25× | ff −40 °C | no trip; 7.6 mV, 3.297 V (v1, 2 ns, reltol 5e-4) | no trip; 5.9 mV (`r4c`) | — | passed |
| `q` 44 µs, 1 A | tt | no trip; 9.2 mV, 3.298 V; VDDA 1461.6 µA (v1, 31 645 s) | no trip; 7.6 mV; 1462.5 µA (`r4a`) | — | passed |
| `q` | ss 125 °C | no trip; 13.8 mV, 3.299 V; VDDA 1726.8 µA (rev. b, 2 ns) | no trip; 9.7 mV; 1727.7 µA (`t1rc`, 5 ns, reltol 5e-4; the default-tolerance attempt failed at 9.86 µs, BGR `xq736`) | — | passed |
| `q` | ff −40 °C | no trip; 7.6 mV, 3.297 V; VDDA 1278.7 µA (v1) | no trip; 6.0 mV; 1279.7 µA (`t1rc`) | — | passed |
| `osc` (transistor-level oscillator) | tt | f_osc 9.43668 MHz; 1.13003 / 1.13280 / **1.50932** / 1.74536, cause 2 (rev. b, 1 ns, reltol 5e-4, 32 009 s); v1 and rev. b at default tolerance failed (numerical) at 7.49 and 9.51 µs, before the event (BGR `xq736`) | f_osc 9.44144 MHz; 1.12112 / 1.12388 / 1.50040 / 1.73644 (`r4a`) | +8.9 ns | passed |
| `osc` | ff −40 °C | f_osc 12.0458 MHz; 0.90800 / 0.90994 / **1.17777** / 1.35692, cause 2 (rev. b, 1 ns, `--tstop 19`); then timestep too small at 18.24 µs (BGR `xq736`); the v1 28 µs attempt failed at 13.76 µs, before the event | f_osc 12.0498 MHz; 0.90247 / 0.90440 / 1.17221 / 1.35136 (`r4c`) | +5.6 ns | trip passed; run **failed (numerical)** after the trip, numbers usable |
| `osc` | ss 125 °C | **not run to completion**, five attempts: v1 5 ns reltol 5e-4 stopped at 0.33 µs after 4 055 s; rev. b 5 ns reltol 5e-4 stopped at 0.56 µs after 3 665 s; rev. b 5 ns stopped at 1.35 µs after 7 326 s; rev. b 5 ns `--tstop 19` failed (numerical, BGR `xq736`) at 1.81 µs; rev. b 2 ns `--tstop 19` stopped at 3.45 µs after 13 940 s (all before the event at 16 µs) | f_osc 7.4914 MHz, `GATE` < 1 V 2.1337 µs (`r4c`) | — | not run to completion |

The `osc` shifts of +8.9 ns (tt) and +5.6 ns (ff) are the decision landing later on the free-running
transistor-level clock (its frequency changes by −0.05 % / −0.03 % with the extracted clock-net R and C); it is
not a change of the analog path, whose timing moves by ≤ 0.2 ns in the ideal-clock rows.

Numerical notes. The BGR HBT `xq736`/`xq760` "timestep too small" failures are the ones of the r4
campaign; they recur with the new parasitics at ss 125 °C with 5 ns steps (both `c_mid` cases at
11.24 µs, `q` at 7.85 µs) and in the `osc` runs, and were resolved by 2 ns or 1 ns steps (ss) and
reltol 5e-4 (tt `osc`). Failed attempts are kept in `sim/logs/` with status `failed`; runs stopped
by hand have status `interrupted`.

### 4.2 Quiet operating point, 2 µs before the event (`QUIET`, window 14-16 µs)

| Corner | `VREF` (V) RC / ref | `ISENSE` at SENSE (V) RC / ref | `icmp` Δ (mV) | `vth_hard` (V) RC / ref | `vth_soft` (V) RC / ref | VDDA (µA) RC / ref |
|---|---|---|---|---|---|---|
| tt 27 °C | 1.04502 / 1.04501 | 1.50773 / 1.50691 (+0.82 mV) | −0.32 | 0.892481 / 0.897207 (**−4.73 mV**) | 0.799835 / 0.804002 (−4.17 mV) | 1461.3 / 1462.8 |
| ss 125 °C | 1.04684 / 1.04682 | 1.51080 / 1.51004 (+0.76 mV) | −0.17 | 0.894563 / 0.898867 (**−4.30 mV**) | 0.801512 / 0.805282 (−3.77 mV) | 1727.0 / 1727.9 |
| ff −40 °C | 1.04208 / 1.04208 | 1.50409 / 1.50320 (+0.89 mV) | −0.44 | 0.889460 / 0.894612 (**−5.15 mV**) | 0.797251 / 0.801802 (−4.55 mV) | 1279.3 / 1279.4 |

### 4.3 Driver side and receiver side (`--node-ripple`, `c_mid` to 16.2 µs, window 14-16 µs)

Mean / peak-to-peak (mV p-p) at the driving block and at the receiving block pin. In the C-only
reference both ends are one node.

| Corner | `VREF` at BGR | `VREF` at SENSE | `VREF_BUF` at SENSE | `VREF_BUF` at TRIP | `ISENSE` at SENSE | `ISENSE` at TRIP |
|---|---|---|---|---|---|---|
| tt, R+C (v1) | 1.04502 / 43.2 | 1.04502 / 47.6 | 1.04489 / 12.2 | **1.03928** / 11.6 | 1.50773 / 11.7 | **1.50562** / 12.0 |
| tt, C only | 1.04501 / 42.9 | (same node) | 1.04489 / 9.2 | (same node) | 1.50691 / 11.1 | (same node) |
| ss 125 °C, R+C (rev. b, 2 ns) | 1.04684 / 46.2 | 1.04684 / 50.5 | 1.04670 / 11.4 | **1.04154** / 10.8 | 1.51080 / 10.5 | **1.50895** / 10.7 |
| ss 125 °C, C only (5 ns, reltol 5e-4; the 2 ns attempt failed at 9.5 µs) | 1.04681 / 46.3 | (same node) | 1.04670 / 8.8 | (same node) | 1.51004 / 10.5 | (same node) |
| ff −40 °C, R+C (rev. b) | 1.04208 / 40.4 | 1.04208 / 44.9 | 1.04196 / 13.9 | **1.03586** / 14.3 | 1.50409 / 12.5 | **1.50170** / 12.9 |
| ff −40 °C, C only | 1.04208 / 39.5 | (same node) | 1.04197 / 9.2 | (same node) | 1.50320 / 12.4 | (same node) |

### 4.4 Findings

1. **Timing.** With series R and C on every top-level net, supplies included, the hard-fault
   response moves by +0.02 to +0.21 ns (ideal clock) against the C-only interconnect: negligible
   against the 1.43-1.73 µs response. The no-trip cases stay silent at all three corners.
2. **`VREF_BUF` IR drop into TRIP (new).** The TRIP block's `vref` pin sits 5.2-6.1 mV below the
   SENSE buffer output: about 41 µA (derived: 5.6 mV / 136 Ω at tt) flows through the 136 Ω
   `i_core_vref_buf` route. Both DAC thresholds scale with it: `vth_hard` −4.3 to −5.2 mV,
   `vth_soft` −3.8 to −4.6 mV at the comparator.
3. **`ISENSE` route.** `ISENSE` is 0.76-0.89 mV higher at the SENSE output (the unequal
   `SENSE_P`/`SENSE_N` routes, 170 / 105 Ω) and 1.9-2.4 mV lower at the TRIP pin (140 Ω route); the
   comparator input `icmp` moves by −0.2 to −0.4 mV only.
4. **Net threshold effect (derived, not simulated as a bracket).** `vth_hard` − `icmp` shrinks by
   4.1-4.7 mV. With the chip's `icmp` slope of about 10.1 mV per shunt mV (tt: 0.1442 V between
   25.0 mV and the 39.25 mV code-200 nominal), the hard trip point moves about 0.43-0.47 mV
   (2.2-2.4 LSB of 0.198 mV) lower, shunt-referred. This is inside the ±6 LSB bracket resolution of
   the r4 campaign and inside what the per-part bench calibration (spec, host rule H6) absorbs; no
   bracket was re-run with the R+C deck.
5. **`VREF` ripple.** The mean is unchanged (≤ 0.02 mV). The clock ripple is 43-46 mV p-p at the
   BGR output, as with C only, and 4-5 mV larger at the SENSE `vref` pin, behind the 141 Ω route.
6. **Supply routes.** Largest top-level supply resistance from the pad ring: 24 Ω (VDDA to the
   `ls_en` level shifter), 10 Ω (VDDA to GATE), 6.6 Ω (VSS to OSC); the analog blocks TRIP and
   SENSE see 2.0-4.3 Ω. IR drop and EM are T2's scope.

## Not run / limitations

| Item | Status | Reason |
|---|---|---|
| Whole-chip flat kpex (any fill option) | not run to completion | quadratic substrate pass, about 6 days (§2) |
| Full-chip netlist with every device extracted, digital at transistor level | not run | no such extraction; the deck keeps block PEX + RTL digital |
| Coupling between top-level wires and macro-internal metal | not run | the view replaces macros by their pin shapes (as on 25 Sep) |
| Fill in the top-level C | not run | fill removed for the extraction; floating fill would add C |
| IO-ring rails inside the `sg13g2_io` cells; bondpad and pad-cell metal C | not run | ideal ring node per supply; bondpad C excluded as before (T2 covers ring R) |
| Block `vdd`/`vss` of BGR, T2F `vref` connection | not applicable to the top-level R | joined inside the macros, not by top-level routes; merged into the net node |
| `osc` at ss 125 °C with R+C | not run to completion | numerical (see §4.1) |
| Hard-threshold brackets and calibration rehearsal with R+C | not run | the threshold shift is derived in §4.4, not bracketed |
| Field-solver cross-check of any net | not run | — |
| Digital macro SPEF in the chip deck | not run | the deck co-simulates RTL; STA with the routes is T3 |

Placement assumptions of the RC netlist (stated, not verified against a finer model): C sits on the
pin nodes of each network fragment (not along the wire); couplings go to the nearest pin node of the
other net; the level-shifter supply meters `vm_ls`/`vm_lsd` are shared by `ls_en` and `ls_mode`, so
those two pins are joined at the `ls_en` route node (0 Ω between two nodes 1-4 Ω apart).

## Commands (repository root; `B=${BULK}/pex`)

```
python3 flow/pex/strip_fill.py --input designs/g1-guardian/blocks/g1_padring/layout/g1_chip_top_1414_r4.gds \
  --output $B/nofill/g1_chip_top_1414_r4_nofill.gds --report $B/nofill/strip_fill.json
flow/launch_pinned.sh 73 . 43200 $B/kpex_full/run.log sh -c "/usr/bin/time -v python3 /work/flow/pex/kpex_progress_probe.py \
  --pdk ihp_sg13g2 --threads 1 --gds $B/nofill/g1_chip_top_1414_r4_nofill.gds --cell g1_chip_top \
  --schematic /work/designs/g1-guardian/blocks/g1_padring/netlist/g1_chip_top_1414_r4.cdl --2.5D --mode CC --out_dir $B/kpex_full/out"
python3 flow/pex/prepare_top_interconnect.py --input $B/nofill/g1_chip_top_1414_r4_nofill.gds \
  --cdl designs/g1-guardian/blocks/g1_padring/netlist/g1_chip_top_1414_r4.cdl --output $B/topic/g1_top_interconnect_view_r4.gds --report $B/topic/prepare.json
python3 flow/pex/make_view_lvsdb.py $B/topic/g1_top_interconnect_view_r4.gds $B/topic/kpex/view.lvsdb g1_chip_top
python3 flow/pex/kpex_named_top.py --pdk ihp_sg13g2 --threads 1 --lvsdb $B/topic/kpex/view.lvsdb --cell g1_chip_top --2.5D --mode CC --out_dir $B/topic/kpex/out
python3 flow/pex/kpex_named_top.py … --mode RC --out_dir $B/topic/kpex_rc/out          # ran; 0 pins, not used
python3 flow/pex/top_route_rc.py $B/nofill/g1_chip_top_1414_r4_nofill.gds $B/topic/g1_top_interconnect_view_r4.gds <kpex tech json> $B/topic/route_rc.json
python3 flow/pex/make_top_interconnect_spice.py <kpex csv> $B/topic/route_rc.json $B/topic/prepare.json $B/topic/top_interconnect_r4.spice $B/topic/top_interconnect_r4_summary.json
python3 flow/pex/top_route_rnet.py $B/topic/g1_top_interconnect_view_r4.gds $B/topic/prepare.json <kpex tech json> $B/topic/rnet.json
python3 flow/pex/make_top_rc_spice.py $B/topic/rnet.json <kpex csv> $B/topic/prepare.json $B/topic/route_rc.json \
  designs/g1-guardian/blocks/g1_top/sim/postlayout/top_interconnect_rc_r4_20260928b.spice designs/…/top_interconnect_rc_r4_20260928b_map.json
python3 flow/pex/top_rc_nets.py $B/topic/top_interconnect_r4_summary.json $B/topic/prepare.json $B/top_rc_nets.json \
  --rnet $B/topic/rnet.json --rc-spice designs/…/top_interconnect_rc_r4_20260928b.spice
# chip deck (W=designs/g1-guardian/blocks/g1_top/sim); C as in FULLCHIP_CDL_R4_20260927.md without --interconnect/--run-id:
flow/launch_pinned.sh <cpu> $W 39600 <log> python3 run_top_cdl.py c_mid --timeline compact [--fault-mult 1.25] [--osc tl] \
  {--maxstep-ns 1 [--tstop 19]|--corner ss --temp 125 --maxstep-ns 5|--corner ff --temp -40 --maxstep-ns 1} \
  [--extra-options reltol=5e-4] --interconnect {extracted-rc|extracted-rc-v1|extracted} --timeout 39200 --run-id t1rc $C
flow/launch_pinned.sh <cpu> $W 39600 <log> python3 run_top_cdl.py q <corner> --interconnect … --run-id t1rc $C
flow/launch_pinned.sh <cpu> $W 39600 <log> python3 run_top_cdl.py c_mid --timeline compact <corner> --tstop 16.2 --node-ripple \
  --interconnect {extracted-rc|extracted} --run-id t1rip $C
```

Every command ran inside `flow/run.sh` with an explicit `G1_CPUSET` from CPUs 73-88.

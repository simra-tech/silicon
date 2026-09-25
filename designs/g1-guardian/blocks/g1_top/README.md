# G1_TOP — chip-level simulation of the breaker path

> **Current state (2026-09-26).** The chip of record is r3
> (`../g1_padring/layout/g1_chip_top_1414_r3.gds`, `7d07a784…`, digital = ECO RTL, register
> map 1.2). Unless a row names the ECO RTL (`--rtl-dir eco_20260925`, runs `eco_*`), the
> chip-level runs below use the pre-ECO RTL `../g1_ctrl/rtl` (map 1.1, the digital of r1/r2) with
> the analog block netlists, which are unchanged in r3. The chip-of-record analog results are in the section
> "2026-09-24 chip-of-record deck (`--blockset c1414`)" below and in
> [sim/campaigns/RESULTS_20260925.md](sim/campaigns/RESULTS_20260925.md). The State
> paragraph that follows, the "What it is" section and the clock description there
> (9.919 MHz schematic, 8.994 MHz post-layout) describe the **legacy** 2026-09-19 deck
> on the superseded Sep-19 block netlists; they are kept as history.

Legacy state (2026-09-19): **chip-level mixed-signal simulation of the breaker path built and run (2026-09-19), schematic
netlists of the analog blocks**: external shunt and load → `SENSE_P`/`SENSE_N` analog pads (PDK
`sg13g2_IOPadAnalog` models) → G1_BGR → G1_SENSE → G1_TRIP → G1_GATE at transistor level → external
FET gate (5 nF + 10 Ω) → load switch, closed loop, with the real digital RTL (`g1_digital`,
`blocks/g1_ctrl/rtl` + `blocks/g1_seu/rtl`) co-simulated inside ngspice through the XSPICE `d_cosim`
code model and Icarus Verilog. The soft path is therefore the **real RTL** at chip level, not a
behavioural stand-in. No layout exists for this block; the post-layout repeat with the kpex block
netlists and the temperature cases are listed as *not run* where no log exists. Every number below is
simulated. Two things the deck does **not** contain at transistor level are stated up front, because
the request asked for them: the `GATE`/`FAULT_N` output pads and the `EN`/`SCLK`/`SDI` input pads are
behavioural stand-ins fitted to (or bypassing) the PDK pad models, and the clock delivered to the
RTL is an ideal source at G1_OSC's block-simulated frequency; the reasons are numerical and are
documented with evidence in "Numerical notes". Both pads and the transistor-level oscillator are
simulated in their own chip-context runs (cases `g*` and `osc`).

**Recovery finding (2026-09-20): earlier chip-level timing results are not
accepted verification evidence.** The clock's 0.55–0.65 V ADC band can deliver
two RTL rising edges during one analog edge. The isolated regression in
[sim/bridge_probe/README.md](sim/bridge_probe/README.md) reproduces this and
verifies a separate 0.6 V single-threshold clock receiver. Corrected runs use
`_clockfix` tags; original logs are retained. All historical trip/no-trip
observations below require revalidation. The affected in-flight runs were
stopped before restarting with the corrected receiver.

## 2026-09-25 extracted top-level interconnect (`--interconnect extracted`)

The top-level wiring between blocks is taken from the extraction
`sim/postlayout/top_interconnect_20260925.spice` ([sim/postlayout/README_top_interconnect_20260925.md](sim/postlayout/README_top_interconnect_20260925.md))
instead of the estimated `Cw_*` wire elements. Simulated, tt/27 °C:

| Case (run tag `c1414icx`) | Deck | Result (extracted interconnect) | Estimate-based reference | Status | Log |
| --- | --- | --- | --- | --- | --- |
| `c_mid` compact, 1.8× hard fault | `--interconnect extracted`, `bgr=sch`, `inpads nodcn`, ideal clock | `trip_d` 1.05778 µs, `GATE` < 1 V 1.34544 µs | like-for-like compact `c1414fullc` 1.05788 / 1.34544 µs: < 0.1 ns (the earlier "+about 10 ns" compared the default-timeline run 1.049 / 1.334 µs) | passed | `c_mid_pex_c1414_tl_tt_27C_icx_ovr-bgrsch_nodcn_clockfix_compact_functional_c1414icx.log` |
| `q`, nominal 1 A | same | no trip; `VDDA` 1421.1 µA | 1421.1 µA (unchanged) | passed | `q_pex_c1414_tl_tt_27C_icx_ovr-bgrsch_nodcn_clockfix_functional_c1414icx.log` |
| `c_mid` 1.25×, SENSE_P/N route resistances 171/106 Ω | same, `srr` | `trip_d` 1.270 µs, `GATE` < 1 V 1.557 µs; `ISENSE` +0.68 mV (about 34 µV input-referred, route mismatch) | like-for-like reference not run (the earlier "+about 10 ns" compared different timelines) | passed | `c_mid_pex_c1414_tl_tt_27C_fm1p25_icx_srr_ovr-bgrsch_nodcn_clockfix_compact_functional_c1414icx.log` |
| `osc`, transistor-level oscillator clocking the RTL | `--interconnect extracted`, BGR586 extraction (not `bgr=sch`), gear, 2 ns maximum step, relaxed tolerances | f_osc 9.875 MHz with the extracted clock load | 9.742 MHz (estimate-based, 2 ns step) | passed | `osc_pex_c1414_tl_tt_27C_icx_gear_…_c1414icx.log` |
| `q` with `--t2f tl`, gear | `c1414icx2` (and reference `c1414icx2ref`) | **failed**: timestep too small at 40.8 µs (`xbgr.xq56`), before the end-of-run measurements | reference without extracted interconnect: completed, no trip, QUIET `VREF` 1.04499 V | failed (numerical); reference passed | `q_pex_c1414_tl_tt_27C_icx_ovr-bgrsch_t2ftl_nodcn_gear_clockfix_functional_c1414icx2.log` |

`VREF` on the on-chip node carries clock ripple: 46.2 mV p-p with the ideal clock,
33.1 mV p-p with the real oscillator; the mean is unchanged (1.0454–1.0455 V) and the
averaged QUIET values are within 0.05 mV of the estimate-based runs. The `VREF` pad with
10 nF does not see this ripple. The extracted interconnect is C only (SENSE route R only in the `srr` run) and is an
extraction of r1 geometry (`629d303a`); it applies to r3 because r3 differs from r1/r2 only
inside the digital macro and in fill (r2 → r3 XOR). All runs use the pre-ECO RTL (map 1.1).
The 1.25× case trips below the programmed 39.2 mV code
value because of the documented hard-comparator kick offset (effective threshold
30–31 mV, §4), not because of the wiring. All values simulated, tt/27 °C.

## 2026-09-25 full-chip deck from the chip CDL (`run_top_cdl.py`)

Summary of [sim/FULLCHIP_CDL_20260925.md](sim/FULLCHIP_CDL_20260925.md) (simulated,
tt/27 °C, ideal clock). `sim/run_top_cdl.py` builds the deck from the canonical
`g1_chip_top_1414.cdl` itself (hash-bound), with all blocks extracted (`--netlist pex`),
the real IO pads from the CDL, and the RTL co-simulated; `EN`/`SCLK`/`SDI` reach the RTL
through the real `IOPadIn` outputs.

- `c_mid` compact, pex, gear (`cdlv1`): **passed**. `trip_d` 1.0578 µs (identical to the
  hand-wired deck), `GATE` < 1 V **1.437 µs** vs 1.345 µs hand-wired, < 0.33 V 1.673 vs
  1.661 µs. The fitted 47 Ω `GATE` driver of `run_top.py` is therefore about 7 % optimistic
  on `GATE` < 1 V: the real `sg13g2_IOPadOut30mA` sinks about 27 mA into the 5 nF gate.
- QUIET values and supply currents match the hand-wired deck with `--t2f tl` within 0.01 %.
- The CDL omits `ng` on 34 SENSE devices and on the NF4 input pair: a simulation-source
  limitation (LVS compares total width). SENSE current is −7.7 % in the CDL deck; timing unaffected.
- T2F-on decks need gear (trap failed in every T2F-on deck).
- Power-up, core first, real `EN`/`SCLK`/`SDI` pads, `por_n` from the CDL tie-high (`cdlpwr`,
  `pads nodcn`): gB and gB_pd passed at tt/27 and ss/125 °C, gB_pd at ff/−40 °C (`GATE` ≤ 0.27 mV
  while EN low, 3.28–3.30 V after EN); gB ff/−40 °C failed numerically at 7.42 µs (`xbgr.xq784`);
  stock-diode pads stalled at 1.377 µs (not run to completion). Finding: without `IOVDD` the `EN`
  pad output floats to 0.84–0.92 V (> 0.6 V 2.34–5.70 µs at tt), `por_n` releases at 2.0 µs, and
  the RTL and G1_GATE trip latches set spuriously until `IOVDD` passes 1.1 V (5.67 µs); `GATE`
  never rises. The inhibit rule (spec §6 P2) stands.
- `q` full length (44 µs, T2F on) on the CDL deck (`cdlpwr`): completed, no trip, `VDDA` 1462 µA.
- The CDL deck is the r1 CDL (`af5a4dbd`, projected-LVS-matched; canonical LVS fails on the IO cells)
  with the pre-ECO RTL (map 1.1); r3's digital adds about one clock (1.166 vs 1.049 µs on the
  hand-wired deck). r3 on the CDL deck: not run.

## 2026-09-24 chip-of-record deck (`--blockset c1414`)

`run_top.py --blockset c1414` builds the same deck with the analog block
netlists of `g1_chip_top_1414.gds` (r1, `629d303a…`; the analog blocks are unchanged in r2 and r3). It uses the
block-to-netlist map of `../g1_padring/reports/signoff-1414-20260924/README.md`.
`--blockset legacy` (default) keeps the Sep-19 paths below. Every c1414 netlist is
bound by SHA-256 in `BLOCKSET_SHA256`; a changed file is refused. Subckt name
and port order are checked against the deck instance, so no wrapper subckt is used.
Deck headers and logs name every netlist used and carry a `NOTE`/`WARNING`/`OVERRIDE` line per substitution.

| Block | `sch` view | `pex` view | Note |
| --- | --- | --- | --- |
| G1_BGR (BGR586) | `../g1_bgr/layout/coordinated_full_closure/evidence/pex-preparation-20260922-r1/controls/r1/baseline_586.spice` `586ffb58` | `../g1_bgr/sim/postlayout/g1_bgr586_pex.spice` `01227a3d` (kpex 2.5D CC of `bank.gds`, 978 C) | the `sch` file carries 329 historical Sep-19 capacitors, not an extraction of the BGR586 layout |
| G1_SENSE (comp45 + R100) | `../g1_trip/sim/qualification/joint586-softinputpair4-nf4-roomcal-s73133-20260924-r1/sense.spice` `bb933fda` | `../g1_sense/sim/postlayout/g1_sense_r100_partialc.spice` `ffb14762` | partial-field C; OTA internals exposed as `__pex_*` ports; unbound VSUBS C excluded; field acceptance not established |
| G1_TRIP (regenpair4 + NF4) | `…/joint586-softinputpair4-nf4-roomcal-s73133-20260924-r1/trip.spice` `f5f0a90a` | `../g1_trip/sim/postlayout/g1_trip_nf4_pex.spice` `ba86b7b2` | NF4 `sch` has no parasitics |
| G1_OSC (R0.95) | none (falls back to `pex`, with a WARNING) | `../g1_osc/sim/qualification/fulltree_r095_load_20260924/common/osc.spice` `8efd7a09` (isolated macro CPEX) | the ideal clock runs at the loaded nominal trim-8 frequency 9.436194721 MHz |
| G1_GATE | Sep-19 `g1_gate.spice` | Sep-19 `g1_gate_pex.spice` | baseline on the chip; this extraction is bound to the chip GATE layout `ddf2c44a` by XOR, block LVS and re-extraction (`../g1_gate/sim/postlayout/README_chip_binding_20260925.md`) |
| G1_T2F + 2 × `g1_ls_up` (`--t2f tl` only) | — | `../g1_t2f/sim/postlayout/g1_t2f_pex.spice` `441edabc`; `../g1_ctrl/ls/sim/netlist/g1_ls_up.spice` `5567c807` | wired as `g1_chip_top_1414.cdl`; `fout` into 1 pF, `TEMP_OUT` pad not modelled |

New options (`python3 run_top.py --help`):

| Option | Effect |
| --- | --- |
| `--blockset legacy\|c1414` | netlist set, above |
| `--view-override BLOCK=VIEW[,…]` | per-block `sch`/`pex` after `--netlist`, e.g. `bgr=sch`; hash and port checks unchanged; tag suffix `_ovr-…` |
| `--t2f off\|tl` | adds G1_T2F and its two level shifters, driven by the RTL `t2f_en`/`t2f_mode` through `rtl/g1_dig_cosim_t2f.v`; transistor-level front end, functional cases only |
| `--inpads nodcn` | **documented deviation**: `SENSE_P`/`SENSE_N` use a deck-local copy of `sg13g2_IOPadAnalog` without its `dantenna` parts (`sg13g2_DCNDiode`, SecondaryProtection `D1`). Clamps, `DCPDiode`, 587 Ω + `dpantenna`, ptap resistors and `padres` are kept. The VREF pad and the PDK file are unchanged. See "Pad-diode finding" below |
| `--osc-rx bridge\|schmitt` | diagnostic clock receiver between the transistor-level `osc_clk` and the `adc_bridge` (±50 mV hysteresis) |
| `--extra-options "…"` | diagnostic `.option` line after the solver line; tag suffix `_opt…` |
| `--osc-supply-r`, `--osc-decap`, `--save-extra` | diagnostic OSC supply elements and extra saved vectors |

Also changed: `--timeline compact` accepts `c`, `c_fast`, `e20` and `osc` besides
`c_mid`. The `QUIET` values are now 2 µs window averages before the event, with
the single-instant samples kept as `*_inst`. Repeated identical PWL points in the
serial stimulus are removed.

Connectivity audit: `sim/check_cdl_vs_deck.py` compares every pin of every
block instance in `g1_chip_top_1414.cdl` with the generated deck (default: the
compact `c_mid` `c1414v1` deck). Rerun 2026-09-25 on the committed `c1414v1` and
`c1414fullc` decks, output committed as
[sim/campaigns/cdl_vs_deck_20260925.txt](sim/campaigns/cdl_vs_deck_20260925.txt):
exit 0 on both, **0 unexplained differences**. Every remaining difference is
documented (single board ground for `VSS`/`IOVSS`, `EN` via the `d_source`). Device
fingerprints: `c1414v1` (BGR586/TRIP schematic) identical to the CDL for `g1_bgr`,
`g1_sense`, `g1_trip`, `g1_gate` (1036/159/2305/78 devices); `c1414fullc` identical
except `g1_trip` (extraction lists 1080 `rppd` vs 1070 and 57 vs 43 `sg13_lv_nmos`,
split/folded devices: the NF4 soft pair is drawn as four fingers and the string
resistors as series segments, which the extractor lists individually; the macro LVS
pass on the same layout (`g1_trip/reports/pex/nf4/lvs_g1_trip.log`) shows the device
sets are equivalent).

Deck record: the generated deck of every c1414 run is committed under
`sim/decks/<tag>.cir` and is the authoritative record of that run's netlist.
2026-09-25 check: 279 of the 281 c1414 run JSONs in `sim/logs/` have a tracked
deck whose SHA-256 equals the JSON `deck_sha256` (279/279 match); the other two
(`*_cdlref1`) were committed later (by `7219e7e5`). Each run JSON also logs the runner version
as `runner_sha256`. The c1414 runs used ten runner versions (`bc15450b`,
`38fdf715`, `ac9c1c45`, `f9e56cae`, `d6bd5574`, `9147f75b`, `dcc31f41`,
`25f47d21`, `8d87feef`, `4438037a`); only `bc15450b` is a committed
`run_top.py`. A run is reproduced from its committed deck, not by regenerating it
with the current runner.

Results (simulated; tt, 27 °C unless the row says otherwise; logs in `sim/logs/`, summaries appended to `sim/results_top.txt`;
the 2026-09-24/25 campaign tables are in [sim/campaigns/RESULTS_20260925.md](sim/campaigns/RESULTS_20260925.md)):

| Case | Deck | Result | Status | Log |
| --- | --- | --- | --- | --- |
| c_mid compact, deck generated from the chip CDL | `run_top_cdl.py --netlist pex --method gear` (`cdlv1`): all blocks extracted, real IO pads | `trip_d` 1.0578 µs; `GATE` < 1 V **1.437 µs**, < 0.33 V 1.673 µs | passed | [sim/FULLCHIP_CDL_20260925.md](sim/FULLCHIP_CDL_20260925.md) |
| c_mid compact (28 µs), 1.8 A/45 mV in-range hard fault, code 200 | `--netlist pex`, transistor-level front end, **BGR586 and TRIP NF4 extractions** (`c1414fullc`), ideal clock, fitted behavioural output pads (about 7 % optimistic on `GATE` < 1 V) | hard trip (cause 2); `GATE` < 1 V 1.34544 µs, < 0.33 V 1.66141 µs after the fault (legacy 1350 µm set: 1.410 µs) | passed | `c_mid_pex_c1414_tl_tt_27C_clockfix_compact_functional_c1414fullc.log` |
| same, run tag `c1414v1` | `--netlist pex` requested, but **BGR586 and TRIP fell back to the schematic netlists** (JSON `blockset_warnings`: no pex netlist existed at launch); BGR `sch` carries 329 Sep-19 capacitors | hard trip (cause 2); `GATE` < 1 V 1.345 µs, < 0.33 V 1.661 µs | passed (schematic BGR/TRIP) | `c_mid_pex_c1414_tl_tt_27C_clockfix_compact_functional_c1414v1.log` |
| b, 1.5× held, default `SOFT_TIME` (≈ 1 ms) | `--netlist pex --front beh` | soft trip (cause 1) at 1.059 ms; `GATE` < 1 V at 1059.37 µs | passed | `b_pex_c1414_beh_tt_27C_clockfix_functional_c1414n1.log` |
| a, 1.5× for 100 µs then back | `--netlist pex --front beh` | no trip, `GATE` stays 3.3 V, `SOFT_PEAK` 3 | passed | `a_pex_c1414_beh_tt_27C_clockfix_functional_c1414n1.log` |
| d, 100 µs bursts to 1.4× at 50 % duty | `--netlist pex --front beh` | no trip | passed | `d_pex_c1414_beh_tt_27C_clockfix_functional_c1414n1.log` |
| gB, core first, EN low until 12 µs | `--netlist pex --front beh`, PDK pad models on `GATE`/`FAULT_N`, **ideal `EN` copy** (with the `EN` pad model the latch state is undefined until `IOVDD` > 1.1 V; inhibit required, `../../review/redteam-20260925/ELECTRICAL_SYSTEM.md` M1) | `GATE` ≤ 0.0725 V while EN low; 3.3 V after EN | passed | `gB_pex_c1414_beh_tt_27C_clockfix_functional_c1414n1.log` |
| gB_pd, as gB with 10 kΩ `GATE` pull-down | same | `GATE` ≤ 0.0090 V while EN low | passed | `gB_pd_pex_c1414_beh_tt_27C_clockfix_functional_c1414n1.log` |
| gA, gA_pd, IO first | same, `--pads nodcn`, `bgr=sch` (run tag `c1414pwr`; ss/125 °C and ff/−40 °C `_r3_c1414m`) | `GATE` 3.28–3.30 V for 4.2–4.4 µs while EN is low (from `IOVDD` up until `VDD` is up), with or without 10 kΩ pull-down; 1 A load flows. Stock pads (`c1414n1`): timeout | failed as a safety condition, expected: confirms P1; the pull-down alone does not hold `GATE` low. Details in [sim/campaigns/RESULTS_20260925.md](sim/campaigns/RESULTS_20260925.md) §5 | `gA*_pex_c1414_beh_*_padsnodcn_*` |
| q prefix 4 µs | `--netlist pex` | completed | passed (prefix only) | `q_pex_c1414_tl_tt_27C_clockfix_t4_prefix_c1414v1.log` |
| q prefix 6 µs with `--t2f tl`, gear | `--netlist pex --method gear` | completed to 6 µs | passed (prefix only) | `q_pex_c1414_tl_tt_27C_t2ftl_gear_clockfix_t6_prefix_c1414t2fgear.log` |
| q prefix 6 µs with `--t2f tl`, trap | `--netlist pex` / `--netlist sch` | timestep too small at 0.62 µs (`xbgr.xq736`) / 1.61 µs (`xt2f.xq42`) | failed | `q_pex_c1414_tl_tt_27C_t2ftl_clockfix_t6_prefix_c1414t2f.log`, `q_sch_c1414_tl_tt_27C_t2ftl_clockfix_t6_prefix_c1414t2fsch.log` |
| q, a_s, b_s, c, c_fast, c_mid, e20, f, f_mid, hard_pulse, full length | `--netlist pex`, run tag `c1414n1` | stopped (ngspice exit −15 at about 2935 s; the 8800 s timeout was not reached) | not run to completion | `*_pex_c1414_tl_tt_27C_clockfix_functional_c1414n1.log` |
| q, c_mid full length, BGR586 **and** TRIP extractions | run tag `c1414full`; compact c_mid `c1414fullc` | compact c_mid: hard trip, `GATE` < 1 V 1.345 µs, < 0.33 V 1.661 µs (19 264 s). Full-length q and c_mid reached 33.2/33.3 µs in 25 000 s | compact passed; full length not run to completion | `*_c1414full.log`, `c_mid_*_compact_functional_c1414fullc.log` |
| same cases with `--view-override bgr=sch`, stock SENSE pads | run tag `c1414n2` | q, a_s, hard_pulse: no trip; b_s: soft trip, `GATE` < 1 V 27.934 µs; c_mid: `GATE` < 1 V 1.334 µs; f_mid: trip and re-arm. c, c_fast, e20, f: stopped externally (exit −15) at 25–28 µs, before the event | q, a_s, b_s, c_mid, f_mid, hard_pulse passed; c, c_fast, e20, f not run to completion | `*_ovr-bgrsch_clockfix_functional_c1414n2.log` |
| corner/temperature matrix (q, c_mid, f_mid at ss/ff × −40/85 °C), stock SENSE pads, `bgr=sch` | run tag `c1414k1` | c_mid `GATE` < 1 V 1.333–1.335 µs; q no trip; f_mid ss/85 and ff/85 trip and re-arm | 10 passed; f_mid ss/−40 and ff/−40 not run to completion (timeout at 48.9/46.4 µs) | `*_c1414k1.log` |
| c and e20 at 27/85/125 °C (tt), c at ss/125 °C, c/c_mid at ff/−40 °C, `--inpads nodcn`, `bgr=sch`, default and compact timelines | run tag `c1414hot_*` | hard trip in every completed run; `GATE` < 1 V 1.333–1.334 µs (default), 1.345–1.346 µs (compact) | 13 passed; c tt/85, e20 tt/85, c ss/125 default timeline not run to completion (timeout; the compact runs of the same points passed) | `*_nodcn_*c1414hot*.log` |
| supply ±10 % on the chip netlists (c_mid, q; VDD 1.08/1.32 V × VDDA=IOVDD 3.0/3.6 V at tt/27 °C, ss/125 °C low-low, ff/−40 °C high-high), `inpads nodcn`, `bgr=sch` | night campaign `_r3_c1414m` | c_mid `GATE` < 1 V 1.306–1.310 µs at 3.0 V, 1.358–1.361 µs at 3.6 V; q no trip | 12 passed | `*_vdd1p*_vdda3p*_r3_c1414m.log` |
| night matrix: q, c_mid, c, e20, f_mid, b_s × tt/ss/ff × −40/27/85/125 °C, `inpads nodcn`, `bgr=sch` | night campaign (`sim/campaigns/night_20260924.json`) | hard cases `GATE` < 1 V 1.333–1.335 µs, b_s soft trip 27.93 µs, q no trip, f_mid re-arms | 72/72 cells completed and passed (the last 12 as `_r4`, including q ss/125 °C); no cell failed | [sim/campaigns/RESULTS_20260925.md](sim/campaigns/RESULTS_20260925.md) §1 |
| hard-threshold sweep at code 200 (39.25 mV), 1.10–1.70× nominal, tt/27 °C | run tags `c1414thr`, `c1414thr3` | no trip at ≤ 30.00 mV, hard trip at ≥ 31.25 mV: effective threshold 8.0–9.25 mV below the code | simulated characterization (calibration requirement, not a gate) | [sim/campaigns/RESULTS_20260925.md](sim/campaigns/RESULTS_20260925.md) §4 |
| T2F on, q, tt at −40/27/125 °C, gear | night `q_t2f_*_r3`, `c1414t2fv2`, `c1414t2fv3` | 1.518 MHz at 27 °C, 1.997 MHz at 125 °C; no trip | 27/125 °C passed; −40 °C not run to completion: failed numerically three times (twice with `bgr=sch`, BGR HBT `xq56`; once with the BGR586 extraction at 11.80 µs, T2F HBT `xq42`) | [sim/campaigns/RESULTS_20260925.md](sim/campaigns/RESULTS_20260925.md) §7 |
| `osc`: transistor-level G1_OSC clocking the RTL | legacy netlists, gear (`dbg0924_b30`, `b41`) | completes; 10.059 MHz (`sch`), 9.035 MHz (`pex`) measured in the deck | passed (legacy netlists only) | `osc_sch_tl_tt_27C_gear_…_b30_osc_gear_loose_xtrtol7_ms1.log`, `osc_pex_tl_tt_27C_gear_…_b41_osc_pex_loose_ms1.log` |
| `osc` on the c1414 set (R0.95), transistor-level oscillator clocking the RTL | night `osc_*_r3`, `c1414osc2_*` | tt/27 °C 9.443–9.483 MHz at 0.5 ns step (ideal clock 9.436 MHz); 9.742 MHz at 2 ns; ss/125 °C 7.61 MHz, ff/−40 °C 12.43 MHz (2 ns step, uncorrected) | completed at tt, ss/125 and ff/−40 (nominal VDD); gear supply-corner osc failed (timestep too small, `xosc.xd52`); trap re-run `c1414oscv2` ff/−40 °C 1.32 V completed at 12.41 MHz; ss/125 °C 1.08 V trap re-run `c1414oscv3`: **not run to completion** (timeout at the 14 000 s wall bound, 17.82 µs of 36 µs, no numerical failure; no `CLOCK` line in the log; an earlier launch was refused by the evidence-overwrite guard) | [sim/campaigns/RESULTS_20260925.md](sim/campaigns/RESULTS_20260925.md) §6 |

Quiet operating point with the chip netlists (compact c_mid deck): `VREF`
1.04547 V, `ISENSE` 1.50732 V at 1 A. The c1414 set takes more supply current
because BGR586 draws 319.7 µA (block PEX, tt/27 °C) against 22.04 µA for the Sep-19 bandgap.
A chip-level `VDDA` current from a completed transistor-level `q` run on the
c1414 set, case q, `bgr=sch`, `inpads nodcn`: 1421.1 µA at tt/27 °C (BGR 319.7 µA,
SENSE 1101.4 µA), 957 µA at ss/−40 °C to 2188 µA at ff/125 °C, all simulated
([sim/campaigns/RESULTS_20260925.md](sim/campaigns/RESULTS_20260925.md) §1). The BGR586 extraction gives the same 319.704 µA (`c1414fullc`).

Full campaign record, including invalid and superseded runs: [sim/campaigns/RESULTS_20260925.md](sim/campaigns/RESULTS_20260925.md).

### Pad-diode finding

The PDK `dantenna`/`dpantenna` diodes (area diode model `darea`) switch formula
at a reverse bias of −3·n·V<sub>t</sub>: about 78 mV at 27 °C and about 103 mV
at 125 °C. The current is discontinuous there. The probe measured steps of
1e-16 → 4e-11 A at 78 mV/27 °C, 2e-14 → 2e-10 A at 93 mV/85 °C and 1e-12 → 4e-10 A
at 104 mV/125 °C. When a large fault drives the `SENSE_P`/`SENSE_N` pad diodes
through that point, the transient stalls ("timestep too small"). This happens
for faults ≥ 2.3× nominal. It is the same diode family that stalls the BGR/VREF pad
startup in `../g1_bgr/sim/system_checks_20260924/RESULTS.md` and the output pads
in "Numerical notes" 3. The deck deviation `--inpads nodcn` removes only the `dantenna`-based parts
of the two SENSE pads. The leakage removed is < 1 nA per pad at 125 °C, behind the 1 Ω
Kelvin trace. This is a simulator work-around, not a statement about silicon;
the stock pad model is not verified by these runs.

## What it is

`sim/run_top.py` generates and runs one ngspice deck per case (copies in `sim/decks/`, logs in
`sim/logs/`, decimated waveforms in `sim/results/waves/`, one summary block per run appended to
`sim/results_top.txt`; `sim/summarize.py` turns the logs into `sim/results/summary.md`).

```
board:  I_load(t) = profile(t) x sw(V_FET_gate)      sw = 0.5 (1 + tanh((V - 1.5 V)/0.15 V))   (load switch on the external FET gate)
        R_shunt 25 mOhm (1 A nominal = 25 mV = DAC code 128), R_gnd 10 mOhm (low-side return), 1 Ohm Kelvin traces,
        FET gate 10 Ohm + 5 nF, FAULT_N 20 pF, 10 nF on the VREF pin, EN / SCLK / SDI 3.3 V PWL sources with 2 ns edges,
        one 3.3 V rail -> VDDA (pin 7) and IOVDD (pin 3) each through 0.5 Ohm + 1 nF, 1.2 V VDD through 0.5 Ohm + 1 nF
pads:   sg13g2_IOPadAnalog x3: SENSE_P, SENSE_N on the bare pad terminal, VREF on the padres terminal (padframe/README.md)
chain:  g1_bgr (r4 = 0) -> VREF, IPTAT -> g1_sense -> ISENSE -> g1_trip (DAC codes from the RTL, strobe cmp_clk from the RTL)
        -> cmp_soft, cmp_hard -> RTL g1_digital (256/128 SEU) -> trip_d, clr_d, fast_en -> g1_gate -> gate_core, fault_core, tripped
digital: g1_dig_cosim.v (sim/rtl) wraps g1_digital; ports matched by position to an XSPICE d_cosim instance (Icarus shim ivlng);
        adc_bridge 0.6/0.6 V on osc_clk; 0.55/0.65 V on cmp_soft, cmp_hard, tripped; dac_bridge 0/1.2 V, 0.3 ns edges on every RTL output;
        EN, SCLK, SDI reach the RTL as an XSPICE d_source stimulus with the same edge times as the pad PWLs
clock:  (legacy deck) ideal 1.2 V square wave at the Sep-19 G1_OSC block-simulated frequency (9.919 MHz schematic, 8.994 MHz post-layout; c1414 decks: 9.436194721 MHz),
        enabled at 0.1 us by the RTL's osc_en; case osc runs the transistor-level g1_osc on the chip VDD with the RTL
outputs: GATE pad = 47 Ohm driver to IOVDD/0 switched by gate_core (fitted to the g1_gate block results with the
        sg13g2_IOPadOut30mA model: 5 nF + 10 Ohm fall 90-10 % 606 ns, arming 677 ns); FAULT_N = 500 Ohm driver
```

Timeline of every functional case (operating point at t = 0, supplies on): oscillator enable 0.1 µs,
`EN` high at 3.07 µs, one serial write frame `INRUSH` = 0x00 at 18.2–21.3 µs (SPI mode 0, 4.96 MHz,
`f_SCLK` = `f_OSC`/2), register update seen at 21.4 µs (`STATUS.INRUSH_ACTIVE` falls), load event at
30 µs. `INRUSH` = 0 is the one register the host writes: with the reset value 0x14 both trip paths are
masked for 1.0 ms after `EN`, which would make every fast case a 1 ms run. Every other register keeps
its reset value (`DAC_SOFT` 0x99 = 30.0 mV, `DAC_HARD` 0xFE = 49.8 mV, `SOFT_TIME` 0x0027 ≈ 1 ms,
`HARD_N` 4, `MODE` 0x03) unless the case says otherwise (`c_fast`: `MODE` = 0x23; `a_s`, `b_s`,
`d_s`: `SOFT_TIME_L` = 0x01). Case-specific waveforms are in `sim/run_top.py` (`make_cases`).

## Simulated

Toolchain: `flow/run.sh` container (`PLAN.md` §2), ngspice 46 with the PDK OSDI models loaded by
`sim/.spiceinit`, Icarus Verilog 14.0 (`iverilog -g2005`, `vvp` library `/foss/tools/iverilog/lib` on
`LD_LIBRARY_PATH` for the `ivlng` shim), PDK commit `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` (every
log header records the PDK commit, the ngspice and iverilog version lines and the sha256 of every
netlist and RTL file used). Run from the repository root:

```
G1_WORKDIR=designs/g1-guardian/blocks/g1_top/sim flow/run.sh python3 run_top.py --list
G1_WORKDIR=designs/g1-guardian/blocks/g1_top/sim flow/run.sh python3 run_top.py q c c_fast e f a_s b_s d_s
G1_WORKDIR=designs/g1-guardian/blocks/g1_top/sim flow/run.sh python3 run_top.py --front beh a b d
G1_WORKDIR=designs/g1-guardian/blocks/g1_top/sim flow/run.sh python3 run_top.py --temp 125 c e
G1_WORKDIR=designs/g1-guardian/blocks/g1_top/sim flow/run.sh python3 run_top.py --netlist pex c e q
G1_WORKDIR=designs/g1-guardian/blocks/g1_top/sim flow/run.sh python3 run_top.py osc gA gB gA_pd gB_pd
python3 designs/g1-guardian/blocks/g1_top/sim/summarize.py
```

Block netlists (`--netlist sch`, the frozen schematic netlists; `--netlist pex`, the kpex 2.5D
capacitance netlists of the laid-out macros):

| Block | schematic | post-layout |
| --- | --- | --- |
| G1_BGR | `../g1_bgr/xschem/g1_bgr.spice` | `../g1_bgr/sim/postlayout/g1_bgr_pex.spice` |
| G1_SENSE | `../g1_sense/sim/netlist/g1_sense.spice` | `../g1_sense/sim/postlayout/g1_sense_pex.spice` |
| G1_TRIP | `../g1_trip/sim/netlist/g1_trip.spice` | `../g1_trip/sim/postlayout/g1_trip_pex.spice` |
| G1_OSC (case `osc`) | `../g1_osc/sim/netlist/g1_osc.spice` (revision 5) | `../g1_osc/sim/postlayout/g1_osc_pex.spice` |
| G1_GATE | `../g1_gate/sim/netlist/g1_gate.spice` | `../g1_gate/sim/postlayout/g1_gate_pex.spice` |
| digital | `../g1_ctrl/rtl/*.v`, `../g1_seu/rtl/*.v` (register map 1.1 RTL, the source of run7 and of the r1/r2 macro; r3 uses `../g1_ctrl/rtl_eco_20260925` via `--rtl-dir eco_20260925`) | — (RTL, not the gate-level netlist) |
| pads | `$PDK_ROOT/$PDK/libs.ref/sg13g2_io/spice/sg13g2_io.spi` | — |

Model lines (all decks): `cornerMOSlv.lib`/`cornerMOShv.lib` `mos_tt`, `cornerRES.lib` `res_typ`,
`cornerCAP.lib` `cap_typ`, `cornerHBT.lib` `hbt_typ`, `cornerDIO.lib` `dio_tt`; `--corner ss|ff` selects
`mos_ss res_wcs cap_wcs hbt_wcs` / `mos_ff res_bcs cap_bcs hbt_bcs` (not run). Solver, transistor-level
front end: `method=trap reltol=0.001 abstol=1e-10 vntol=1e-6 chgtol=1e-14 rshunt=1e12 itl4=100`,
maximum step 5 ns; behavioural front end and power-up cases: `method=gear reltol=0.002 abstol=1e-8
vntol=1e-4 chgtol=1e-12 rshunt=1e12` (see "Numerical notes" for why).

Measurements per run (all in the log, `QUIET`/`CLOCK`/`SUPPLY_uA`/`TRIP`/`CHARGE`/`REARM`/`POWERUP`
lines): quiet values after the register write (VREF, ISENSE, comparator input `icmp`, the two DAC
outputs, load current, GATE, the DAC codes read back from the analog code lines, `INRUSH_ACTIVE`),
oscillator and strobe frequency, supply currents averaged over the armed quiet window (rail totals and
per block through 0 V sources on every block supply pin), and after the load event: `tripped` (G1_GATE
latch), `trip_d` (RTL latch), first crossing of `GATE` below 1 V and below 0.33 V, minimum and final
`GATE`, peak and final load current, cause code read from the RTL (`trip_cause`), `SOFT_PEAK`
register, charge passed after the event.

### Results — waveform library (schematic netlists, tt, 27 °C)

Historical tt, 27 °C schematic runs (times relative to the load event; simulated, **pending revalidation of the clock**):

| Case | Functional result | GATE < 0.33 V | Evidence in `sim/logs/` |
| --- | --- | --- | --- |
| q, nominal load | observed no trip; revalidation required | not applicable | `q_sch_tl_tt_27C.log` |
| a_s, short 1.5× pulse | observed no trip; revalidation required | not applicable | `a_s_sch_tl_tt_27C.log` |
| b_s, held 1.5× load, shortened timer | observed soft trip; revalidation required | 26.86 µs | `b_s_sch_tl_tt_27C.log` |
| c, 3× step | observed hard trip; revalidation required | 1.96 µs | `c_sch_tl_tt_27C.log` |
| c_fast, 3× step with FAST_EN | observed hard trip; revalidation required | 0.95 µs | `c_fast_sch_tl_tt_27C.log` |
| e20, 4× step with 20 ns rise | observed hard trip; revalidation required | 1.55 µs | `e20_sch_tl_tt_27C.log` |
| f, trip then EN toggle | observed re-arm to 1 A; revalidation required | 1.96 µs before re-arm | `f_sch_tl_tt_27C.log` |

The complete parsed measurements, including incomplete and failed attempts, are
in [sim/results/summary.md](sim/results/summary.md). The e20 waveform does not
validate the original e case's 100 ns rise.

### Quiet operating point and supply currents (armed, nominal 1 A load, before the event)

Case q (legacy netlists, Sep-19 bandgap) reports simulated VREF 1.03785 V,
ISENSE 1.4967 V and VDDA current 1055.33 µA (BGR 22.04 µA, SENSE 1033.29 µA).
The chip-of-record bandgap BGR586 draws 319.7 µA (simulated, tt/27 °C,
`../g1_bgr/sim/postlayout/README_bgr586_pex.md`), so the chip `VDDA` total is higher;
see the c1414 section above. RTL and ideal-clock supply
currents are not physical estimates. See the generated summary for all values.

### Clock case `osc` (transistor-level G1_OSC clocking the RTL on the chip VDD)

Legacy netlist suite: **not run to completion**. No completed `osc` log exists. Block oscillator results do not establish this chip-context check. On the c1414 set, see the `osc` row of the c1414 section.

### Power-up (case g)

Legacy netlist suite: **not run**. No completed `gA`, `gB`, `gA_pd` or `gB_pd` log exists in this suite. The separate G1_GATE pad/power-up evidence remains block-level evidence. On the c1414 set, see the c1414 section.

### Temperature and post-layout

The c and e schematic runs at 125 °C **failed** with timestep collapse near
30.020 µs and 30.066 µs respectively (`sim/logs/*125C.log`). Partial measurements
from these runs are not functional verdicts. Post-layout chip-path checks are
**not run to completion**; a c-case run was started during recovery on 2026-09-20.

## Behavioural front end (`--front beh`)

Used for the three long-window cases (a), (b), (d) at the default `SOFT_TIME` (≈ 1 ms) and as the
cross-check column of the table above. G1_BGR, G1_SENSE and G1_TRIP are replaced by their block-level
transfer functions: VREF 1.0399 V fixed; ISENSE = 0.9992 V + 19.99 × (SENSE_P − SENSE_N) through a single
pole at 4.19 MHz (`../g1_sense/sim/results_sense.txt`); conditioning divider ISENSE/2 with 25 kΩ into
1 pF; DAC taps VREF × (255 + code)/530 from the RTL codes; two ideal clocked comparators (2 mV wide
tanh decision, sampled by XSPICE `d_dff` on the rising / falling `cmp_clk` edge like the StrongARM
pair). G1_GATE and the pads are the same as in the transistor-level deck. What this front end cannot
show: comparator kickback, offset, sense-amplifier settling, supply coupling, DAC settling — those are
the transistor-level runs' job; what it shows is the RTL's window/decay logic against the load profile
at chip level with the real GATE path.

## Numerical notes (what was tried, with the evidence under `build/g1_top/dbg/` while it exists)

These decide what the deck contains and are the reason for every deviation from "everything at
transistor level":

1. **`d_cosim` is available in this ngspice build** (`digital.cm` carries `d_cosim`, the Icarus shim
   `ivlng.so`/`ivlng.vpi` and the Verilator helper `vlnggen` are installed). The Icarus route works once
   the top module carries a `` `timescale `` directive (without it the shim delivers no events: a 4-bit
   counter test stayed at zero) and `libvvp.so` is on `LD_LIBRARY_PATH`. The RTL's clock, comparator
   and latch inputs go through `adc_bridge`; the RTL outputs through `dac_bridge`. Verilator was not used.
2. **The analog operating point is computed with the digital outputs at zero**: XSPICE does not run
   the co-simulator during the OP, so the RTL's reset values (DAC codes, `osc_en`, trim) arrive 0.3 ns
   into the transient and the DAC strings settle in the first microsecond (visible as `vth` = 0.499 V
   at t = 0 in the waveform files). Nothing is measured before 21 µs.
3. **PDK IO-pad models and the StrongARM comparators need incompatible integration settings.** The
   `sg13g2_IOPadOut30mA`/`IOPadIn` models stop the solver ("timestep too small", always on an
   internal node of one of their `dantenna`/`dpantenna` diodes, whose model cards carry
   rs = 0.2–1.7 MΩ per unit and tt = 700 ns) whenever an XSPICE event lands on one of their switching
   edges, unless the integration is gear with `chgtol` = 1e-12 (`w3`, `x1..x4`, `beh_d1n` tests).
   With that setting the StrongARM comparators of G1_TRIP decide **wrongly at 250 mV overdrive** (the
   `kb*`/`kbe*` tests: with gear, `reltol` ≥ 0.002 and `chgtol` = 1e-12 the hard comparator resolved in
   the wrong direction in about one strobe of three; the block decks use `tran 0.2n`, trap, default
   tolerances and are right). Attempts to have both: bridge hysteresis, bridge delays, `itl4`, `gmin`,
   `rshunt`, tolerances, 10 ns pad edges, threshold-aligned PWL corners, a breakpoint train through
   the strobes — all fail on one side or the other (`z*`, `w*`, `x*`, `kbe_*` logs). The decision was
   to keep the analog chain exact and take the pads out of the transistor-level decks: the `EN`/`SCLK`/
   `SDI` pads become ideal 3.3 → 1.2 V level copies, the `GATE`/`FAULT_N` pads become drivers fitted to
   the g1_gate block results with the real pad models (`../g1_gate/sim/results_gate.txt`), and the
   transistor-level runs use trap with `chgtol` = 1e-14. The pad models themselves are exercised
   in the power-up cases and in the behavioural runs (gear, `chgtol` 1e-12), where no comparator exists.
4. **The transistor-level oscillator cannot drive the RTL in the full deck.** With g1_osc on the chip
   VDD and the RTL clocked from its output, the solver aborts within a few µs after `EN` or at the
   oscillator start, blamed on the bandgap's `XQD1` HBT (VBIC) or a pad diode, in every one of
   fourteen variants (tolerances, integration method, bandgap post-layout netlist, VREF isolation,
   local decoupling, separate supplies: `z0..z17`); the same deck runs with an ideal clock of the same
   frequency (`y1`), or without G1_TRIP (`y2`), or without the co-simulation (`y4`). The RTL clock is
   therefore an ideal source at the block-simulated frequency; case `osc` runs the transistor-level
   oscillator with the RTL, G1_BGR and G1_SENSE (no G1_TRIP, no pads).
5. **Oscillator frequency is time-step dependent** (schematic g1_osc alone, gear): maximum step 20 ns
   → +9.6 %, 5 ns → +3–4 %, 1 ns → +1 %, 0.2 ns → 9.94 MHz (block value 9.92). With the XSPICE bridge
   attached the 5 ns figure is +5–9 %. Hence the 5 ns maximum step everywhere and the ideal clock at
   the block value for the trip runs; the `osc` case reports its own measured frequency.
6. **XSPICE forces `trtol` = 1** ("Reducing trtol to 1 for xspice 'A' devices"); an explicit `trtol` in
   `.option` does not override it. With `trtol` = 7 and `reltol` = 0.005 even the block-level
   comparator deck decides wrongly at a 5 ns maximum step.
7. **Bridge unknown states double-count as clock edges**: The recovery regression also confirmed this on `osc_clk`; its receiver now uses one 0.6 V threshold. Historical clock and trip-timer results require reruns. Original finding: an `adc_bridge` whose input passes through the
   0.55–0.65 V band at an analog time point emits `U`, which the RTL sees as `x` (0→x→1 = two
   `posedge`s); a serial frame then loses its framing. The RTL's `EN`/`SCLK`/`SDI` are therefore a
   digital `d_source` stimulus; the analog copies of the same edges still drive G1_GATE.
8. ngspice control language: a `>` inside a `let` expression is an output redirection (files named
   `0.6)` appeared); `gt`/`lt` are used instead. Only the last `.save` line of a deck counts.
9. **Speed**: the transistor-level deck (≈ 1500 MOS, 1150 resistors, 19 000 nodes with the trip
   block's DAC trees) runs 36 µs in 23–27 min on the emulated container at load; 1 ms would take
   about 12 h per case, which is why the ≈ 1 ms `SOFT_TIME` cases use the behavioural front end and the
   transistor-level soft-path cases use `SOFT_TIME` = 0x0001 (256 osc_clk) with the load timing scaled
   by the same factor.

## Scope statement

| Part | Level | Netlist / model |
| --- | --- | --- |
| G1_BGR, G1_SENSE, G1_TRIP (both comparators, both DACs, level shifters, conditioning divider), G1_GATE (latch, level shifters) | transistor level | schematic netlists (`--netlist sch`); post-layout kpex CC netlists where the table says `pex` |
| `SENSE_P`, `SENSE_N`, `VREF` pads | transistor level | PDK `sg13g2_IOPadAnalog` (ESD clamps and diodes) |
| digital core (register file, serial interface, trip timer, SEU monitor) | RTL, co-simulated | `g1_digital` RTL of the hardened macro; not the gate-level netlist, no SDF |
| `GATE`, `FAULT_N` output pads | behavioural, fitted | 47 Ω / 500 Ω drivers switched by `gate_core`/`fault_core`; timing from the g1_gate block runs with the PDK models |
| `EN`, `SCLK`, `SDI` input pads | behavioural | ideal 3.3 → 1.2 V level copies (pad delay ≈ 1 ns not modelled) |
| RTL clock | ideal source | at the g1_osc block frequency (schematic 9.919 MHz, post-layout 8.994 MHz); g1_osc itself transistor-level in case `osc` only |
| load, shunt, FET gate, board decoupling | behavioural | current-source profile × tanh switch on the FET gate; RC elements |
| long-window cases (a), (b), (d) | behavioural front end | block transfer functions, ideal clocked comparators, real RTL, real G1_GATE, PDK output pads |
| power-up cases (g) | pads at transistor level, front end behavioural | PDK pad models for `EN`, `GATE`, `FAULT_N`, `SCLK`, `SDI`; supply ramps |

Not simulated: the full-chip extracted netlist (no chip-level PEX), the chip-level routing parasitics
between macros (300 fF on ISENSE and 20–100 fF on the digital nets are estimates), the digital
macro's supply current (LibreLane estimate 0.97 mW at 10 MHz, `../g1_ctrl/README.md`), package and
bond-wire parasitics, the board beyond the elements listed, process corners and mismatch at chip
level, the `TRIP_SET` pad path (not built), `SDO` and `TEMP_OUT` pads.

## Checks

| Check | Status | Evidence |
| --- | --- | --- |
| Nominal schematic cases q, a_s, b_s, c, c_fast, e20, f | failed clock validation; reruns not run to completion | waveform table and `sim/logs/` |
| Schematic c/e at 125 °C | failed, solver timestep collapse | `sim/logs/*125C.log` |
| d_s and original e at 27 °C | not run to completion | logs have no completion footer |
| Default-window behavioural a/b/d | not run to completion; started during recovery | `sim/logs/` |
| Post-layout c | not run to completion; started during recovery | `sim/logs/` |
| Post-layout q/e, osc, power-up suite, process corners | not run | no completed logs |
| c1414: compact c_mid hard trip; beh a/b/d; core-first power-up gB/gB_pd | passed | c1414 section above |
| c1414: CDL-vs-deck connectivity audit | passed (0 unexplained) | `sim/check_cdl_vs_deck.py` |
| c1414: `--t2f tl` with trap | failed (timestep too small) | c1414 section above |
| c1414: full-length tl cases (`c1414n1`) | not run to completion | c1414 section above |
| c1414: corner/temperature matrix (72 cells, `nodcn`, `bgr=sch`, ideal clock) | passed 72/72 (last 12 as `_r4`, including `q_ss_125C_r4_c1414m`); failed 0 | [sim/campaigns/RESULTS_20260925.md](sim/campaigns/RESULTS_20260925.md) §1 |
| c1414: supply ±10 % (c_mid, q) | passed (12/12) | [sim/campaigns/RESULTS_20260925.md](sim/campaigns/RESULTS_20260925.md) §2 |
| c1414: `bgr=sch` nominal reruns (`c1414n2`) | passed q, a_s, b_s, c_mid, f_mid, hard_pulse; c, c_fast, e20, f not run to completion | [sim/campaigns/RESULTS_20260925.md](sim/campaigns/RESULTS_20260925.md) §3a |
| c1414: stock-pad corners (`c1414k1`), hot `nodcn` cases (`c1414hot`) | passed 10 + 13; not run to completion 2 + 3 | [sim/campaigns/RESULTS_20260925.md](sim/campaigns/RESULTS_20260925.md) §3b, §3c |
| c1414: both BGR586 and TRIP extractions | compact c_mid passed; full-length q/c_mid not run to completion | [sim/campaigns/RESULTS_20260925.md](sim/campaigns/RESULTS_20260925.md) §3d |
| c1414: IO-first power-up gA/gA_pd (`pads nodcn`) | failed as a safety condition (`GATE` 3.28–3.30 V for 4.2–4.4 µs, also with 10 kΩ): expected, confirms P1 | [sim/campaigns/RESULTS_20260925.md](sim/campaigns/RESULTS_20260925.md) §5 |
| c1414: core-first power-up gB/gB_pd at ss/125 °C, ff/−40 °C (`pads nodcn`) | passed (`GATE` ≤ 0.014 V) | [sim/campaigns/RESULTS_20260925.md](sim/campaigns/RESULTS_20260925.md) §5 |
| c1414: effective hard threshold at code 200 | simulated characterization: 30.00–31.25 mV (8.0–9.25 mV below code); calibration requirement | [sim/campaigns/RESULTS_20260925.md](sim/campaigns/RESULTS_20260925.md) §4 |
| c1414: `--t2f tl` with gear, full q | passed 27/125 °C; −40 °C not run to completion (timestep too small in all three attempts, including `c1414t2fv3` with the BGR586 extraction) | [sim/campaigns/RESULTS_20260925.md](sim/campaigns/RESULTS_20260925.md) §7 |
| c1414: transistor-level OSC R0.95 clocking the RTL | completed tt/27 °C (step study), ss/125 °C, ff/−40 °C; gear supply corners failed (timestep too small); ff/−40 °C 1.32 V trap completed (12.41 MHz); ss/125 °C 1.08 V trap not run | [sim/campaigns/RESULTS_20260925.md](sim/campaigns/RESULTS_20260925.md) §6 |
| Full-chip PEX and physical measurements | not run | no extracted chip or measured sample |
| Layout DRC/LVS of this simulation-only block | not applicable | chip layout evidence is in G1_PADRING |

## Unverified

- Full-chip extracted netlist (no chip-level PEX exists yet) and the inter-macro wiring; package,
  bond wire and board parasitics beyond the lumped elements above.
- The PDK output/input pad SPICE models together with the transistor-level comparators in one
  transient (numerical incompatibility, note 3); the fitted drivers reproduce the block-level pad
  timing into 5 nF + 10 Ω only.
- The transistor-level oscillator clocking the RTL inside the full chain (note 4); its frequency
  and current in the chip supply context come from case `osc`.
- Process corners and supply ±10 % at chip level: run on the c1414 set with the ideal clock, the
  fitted `GATE` driver (about 7 % optimistic on `GATE` < 1 V), estimate-based interconnect (extracted runs differ by < 0.1 ns like-for-like) and the `nodcn`/`bgr=sch` deviations ([sim/campaigns/RESULTS_20260925.md](sim/campaigns/RESULTS_20260925.md)); mismatch not run.
- The default 1 ms `SOFT_TIME` window at transistor level (behavioural front end only, note 9).
- Comparator decisions at small overdrive at chip level beyond the single tt/27 °C hard-threshold
  sweep at code 200. That sweep puts the effective hard threshold at 30.00–31.25 mV, 8.0–9.25 mV below the
  code ([sim/campaigns/RESULTS_20260925.md](sim/campaigns/RESULTS_20260925.md) §4). The offset is the
  soft comparator's reset kick at the hard strobe (`../g1_trip/sim/postlayout/README.md`). The soft path
  and mismatch are not swept at chip level.
- Digital core at gate level with timing (the RTL is co-simulated; the macro's gate-level regression is
  in `../g1_ctrl/sim`).
- Power-up with the analog blocks' real behaviour under supply ramps (the power-up cases use the
  behavioural front end; g1_bgr and g1_sense start-up are block-level results).

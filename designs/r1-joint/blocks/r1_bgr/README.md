# r1_bgr — compact bandgap reference with PTAT current (R1)

State (2026-10-21): **schematic simulated** (revision r1). **Layout done** (2026-10-21): DRC 0, antenna 0,
LVS clean, post-layout simulated (see "Layout (T7, 2026-10-21)"). All numbers are simulated (ngspice 46);
nothing is measured.

## What it is

The G1 Sep-19 op-amp-less cascoded HBT bandgap (`designs/g1-guardian/blocks/g1_bgr/xschem/g1_bgr.spice`,
sha256 `fa925507…`), re-proportioned for mismatch (PLAN.md D5). Outputs: `vref` (1.045 V), `iptat`
(4.2 µA PTAT leg), and the mirror rails `pbias`/`pcasc` for the T2F. Monitor pins `vbe`, `dvbe`.
Supply: VDDA 3.0–3.6 V (thick-oxide `sg13_hv_*` MOS, `npn13G2`, `rppd`, `rhigh`).

Why the G1 cell was not enough: the PDK HBT mismatch model draws **one 10 % area factor per instance,
independent of `Nx`** (`sg13g2_hbt_mod_mismatch.lib`: `qarea = agauss(1, 0.1, 1)`). Only separate unit
instances average it. The Sep-19 cell (Q1 = 1 unit, Q2 = 8 units) gave σ(V<sub>REF</sub>) = 1.84 %.
BGR586 averaged by copying the whole loop (301 HBT, 0.148 mm²). r1_bgr averages only the ΔV<sub>BE</sub>
pair and adds a mirror current ratio, which raises ΔV<sub>BE</sub> and lowers the PTAT gain:

| Item | G1 Sep-19 | r1_bgr |
| --- | --- | --- |
| Q1 / Q2 / Q3 unit instances | 1 / 8 / 1 | **12 / 48 / 4** |
| Q1-branch mirror legs (current ratio) | 1 (1:1) | **8 (8:1)** |
| ΔV<sub>BE</sub> = V<sub>T</sub> ln(M·N2/N1) at 27 °C | 55.1 mV (ln 8) | **91.1 mV** (ln 32) |
| R1 / R2 (`rppd`, w = 1 µm) | 51.5 / 315 µm | **84 / 347.5 µm** |
| RB / RX / start-up | 500 / 192 µm, kick on `pbias` | unchanged |
| Unit PMOS leg (mirror + cascode) | 10/4 µm, ≈ 4.1 µA | unchanged (T2F legs stay compatible) |
| `r4` 1:4 test mode | yes | **removed** (not in the R1 interface) |

Expected mismatch budget before simulation (1σ on V<sub>REF</sub>): HBT pair 3.5 mV, Q3 1.3 mV,
R1/R2 1.0 mV, mirror 0.5 mV → 3.9 mV (0.37 %). Simulated: 4.18 mV (0.40 %).

Pins: `vdd vss vref iptat pbias pcasc vbe dvbe`.

## Files

| Path | What |
| --- | --- |
| `schematic/gen_r1_bgr.py` | netlist generator (parameters n1, n2, n3, m, r1, r2, rb, rx) |
| `schematic/r1_bgr.spice` | frozen netlist, sha256 `c19a7425d605906962724fdda21add8ae3926dc9a097c6f835a16f05f92c0c26` (108 devices: 66 `npn13G2`, 26 HV PMOS, 11 HV NMOS, 5 resistors) |
| `sim/tb_r1_bgr.spice.tmpl`, `sim/run_bgr.py`, `sim/.spiceinit` | testbench template and runner (suites `size temp mc psrr startup op`; `stb` and `noise` added 2026-10-21) |
| `sim/tb_stb_toy.cir` | toy loop for the loop-gain method check (copy of the r1_afe deck) |
| `sim/probe/` | unit-device mismatch probe |
| `layout/r1_bgr_layout.py` | layout generator (KLayout batch, SG13_dev PCells); writes the three files below |
| `layout/r1_bgr.gds` | layout, top cell `r1_bgr`, 96.0 × 194.3 µm, sha256 `324e3c27477a77c4a32d6760366d8d1fb82bea4887ae26b905cd7022aac54005` |
| `layout/r1_bgr_lvs.cdl` | LVS reference: netlist of record plus the layout dummies (38 HBT, 4 PMOS, 2 NMOS), sha256 `c4d175ee…fae2b` |
| `layout/r1_bgr_layout_meta.json` | bounding box, trunks, channel use |
| `layout/run_checks.sh`, `layout/write_runjson.py` | generator + PDK DRC + PDK LVS, run.json per run |
| `layout/pex_build.py` | device-level RC netlist: KLayout `RNetExtractor` wiring R + kpex 2.5D CC capacitance |
| `layout/pex_paths.py` | effective resistance and IR drop of the precision paths from the extracted networks |
| `sim/run_bgr_post.py` | pre- vs post-layout runner (op, TC, start-up, core loop) |
| `sim/results/<run-id>.json` | summaries; `sim/runs/<run-id>/run.json` per run; raw decks, logs, waveforms at `<G1_RESULTS_ROOT>/r1_bgr/<run-id>/` |

Loads in every deck (as on G1): `iptat` sinks into a 1.0 V source, `vref` carries 1 pF.
Corner names: `hbt_typ/bcs/wcs`, `mos_tt/ss/ff`, `res_typ/bcs/wcs`.

## Built against

| Item | Value | Established by |
| --- | --- | --- |
| PDK | IHP SG13G2 open PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` | `/foss/pdks/ihp-sg13g2/COMMIT` in the container (checked by `flow/run.sh`) |
| ngspice | 46 (KLU), PSP 103 and R3 via OSDI | `ngspice -v` in the container |
| Container | `tapeoutbench-eda:latest` `sha256:ddeb6957…` | `flow/run.sh` image check |
| xschem | not used (netlist generator) | — |
| KLayout | 0.30.9 (layout generator, PDK DRC/LVS decks, `RNetExtractor`) | `klayout -v` in the container |
| kpex | 0.3.12 (2.5D CC capacitance only) | `kpex --version` in the container |
| Python (extraction post-processing) | numpy 2.5.1, scipy 1.18.0 | import in the container |

Command (from the repository root): `G1_CPUSET=116,117 G1_CPUS=2 G1_WORKDIR=designs/r1-joint/blocks/r1_bgr/sim G1_RESULTS_ROOT=<G1_RESULTS_ROOT> flow/run.sh python3 run_bgr.py <suite> <run-id>`.

## Status

| Check | Criterion | Status | Evidence |
| --- | --- | --- | --- |
| Unit-device mismatch probe | record | run: PMOS 10/4 σ(I) 0.41 %, `rppd` 1×51.5 µm 0.31 %, HBT 10 % per instance (model) | `bgr-probe-mismatch-20261020` |
| R2 for zero TC and V<sub>REF</sub> 1.045 V | record | run: R2 = 347.5 µm | `bgr-size-20261020-d` |
| V<sub>REF</sub> at tt/27 °C | 1.045 V | **passed**: 1.0449 V (3.0 / 3.3 / 3.6 V identical to 0.01 mV) | `bgr-temp-20261020-b` |
| TC box −40…125 °C, nominal | ≤ 30 ppm/°C | **passed**: 8.4 ppm/°C | same |
| TC box, 27 process corners × 3 supplies | ≤ 30 ppm/°C | **failed** 9/81: hbt_wcs + res_bcs gives 34.4–35.1 ppm/°C; other 72 runs 8.3–25.8 | same |
| V<sub>REF</sub> spread over corners | record | 1.0359–1.0558 V at 27 °C (±0.95 %) | same |
| Supply current | ≤ 100 µA | **passed**: 51.8 µA tt/27 °C; max 79.6 µA (res_bcs, 125 °C) over 81 runs × −40…125 °C | same, `bgr-op-20261020-b` |
| Mismatch, 50 samples, 27 °C, 3.3 V | σ(V<sub>REF</sub>) ≤ 0.5 % | **passed**: σ 4.18 mV = 0.40 %, range 1.0332–1.0546 V, 50/50 completed | `bgr-mc-20261020-b` |
| TC under mismatch (same 50 samples) | ≤ 30 ppm/°C | **passed**: 50/50, mean 13.4, max 27.6 ppm/°C | same |
| `iptat` | record | 4.20 µA at 27 °C (3.71–4.81 µA over res corners); σ 1.08 % (MC) | `bgr-temp-…-b`, `bgr-mc-…-b` |
| Start-up, 5 corner/temperature points × {1 ms, 10 µs} ramp to 3.0 V | starts, ends 0.95–1.15 V | **passed** 10/10; 1 % settled 0.55–0.66 ms (1 ms ramp), 7.9–8.7 µs (10 µs ramp); overshoot ≤ 1.115 V (ss/−40 °C, 10 µs ramp) | `bgr-startup-20261020-b` |
| PSRR 20 kHz / 1 MHz (tt27, ss125 @3.0 V, ff−40 @3.6 V, tt27 @3.0 V, tt125 @3.0 V) | no limit specified | **run**: 20 kHz −54.2…−56.8 dB; 1 MHz −26.1…−27.3 dB; DC ≤ −100 dB | `bgr-psrr-20261020-b` |
| Device headroom (5 corners × −40/27/125 °C × 3.0/3.6 V) | record | run, 30/30 converged: mirror V<sub>DS</sub> ≥ 0.42 V, Q2 V<sub>CE</sub> 0.51–0.83 V | `bgr-op-20261020-b` |
| Loop stability, 5 loop cuts × (tt/27 °C/3.3 V, ss/125 °C/3.0 V, ff/−40 °C/3.6 V, 9 × hbt_wcs + res_bcs at 27 °C, mos tt/ss/ff × 3.0/3.3/3.6 V) | PM ≥ 60°, GM ≥ 10 dB | **passed** 60/60 (details in "Loop stability and noise (T7)"). Core loop (`pbias` gate cut): PM 131.7–132.7°, GM 20.2–21.2 dB (ss/125: no −180° crossing to 10 GHz). Other cuts have no unity crossing; GM ≥ 20.4 dB (`pcasc`), ≥ 25.6 dB (`vb2`), 12.9 dB (`vbe`, DC loop gain −0.225). Start-up detector loop is open in the on state (\|T\| < −240 dB at all 12 corners). Smallest min\|1+T\| 0.774. | `bgr-stb-20261021-b`, `sim/results/summary-20261021.json` |
| Supply-step transient, 3.3 → 3.0 V, 100 ns edge, tt/27 °C and ss/125 °C | within 1 % in ≤ 50 µs, at most one overshoot | **passed**: `vref` dips 10.3 mV (0.986 %, tt) and 10.7 mV (1.020 %, ss) at 0.2 µs after the edge. ss is outside 1 % for 0.14 µs. No overshoot. 0.1 % in 0.6 / 0.7 µs, 10 µV in 1.4 / 1.6 µs. Net change −1.8 / −2.7 µV. | `bgr-stb-20261021-b` |
| Loop-gain method check (toy loop) | matches the exact return ratio | **passed**: max relative error 4.7e-8, PM 88.61° both ways | `bgr-stb-20261021-b` (`toy.log`) |
| Noise of `vref`, 10 Hz–10 MHz, tt/27 °C and ss/125 °C (1 pF load) | record (no limit) | **run**: 10 Hz–100 kHz 57.1 µV rms (tt), 73.7 µV (ss/125); 10 Hz–10 MHz 158 / 189 µV; 1/f corner 6.0 / 6.9 kHz. 0.25 LSB (110 µV): met only if the buffer pole is ≤ 0.62 MHz (tt) or ≤ 0.28 MHz (ss/125), estimate. | `bgr-noise-20261021-b` |
| Mismatch at −40 / 125 °C and at corners | — | **not run** (TC per sample covers −40…125 °C at tt only) | — |
| Load: ADC reference buffer, r1_safe DAC, T2F with r1_bgr rails | — | **not run** | — |
| DRC, PDK deck, main + `sg13g2_maximal` tables, `--run_mode=deep --no_density` | 0 markers | **passed**: 0. Density is waived at block level; it is checked at chip level after fill. | `layout-drc-20261021-c` |
| Antenna, PDK deck `--antenna_only` | 0 markers | **passed**: 0 | `layout-ant-20261021-c` |
| LVS, PDK deck vs netlist of record + dummies | match | **passed**: 108 + 44 dummy devices; after series/parallel combination 4 `rppd`, 1 `rhigh`, 27 PMOS, 5 NMOS, 6 `npn13G2` (104 units), 28 nets | `layout-lvs-20261021-c` |
| Pins on the boundary, Metal3, no TopMetal | 8 pins | **passed**: `vdd vss vref iptat pbias pcasc vbe dvbe` on Metal3 at the edge; top layer used is Metal4 | `layout/r1_bgr_layout.py` |
| Area | ≤ 0.020 mm² | **passed**: 96.0 × 194.3 µm = 0.01865 mm² | `layout/r1_bgr_layout_meta.json` |
| PEX (RC, device level) | extracted | **passed**: 2730 R, 372 C (866 fF) | `pex-rc-20261021-b` |
| Post-layout V<sub>REF</sub>, TC, current, start-up, core loop | as schematic rows | **passed** (table in "Layout") | `bgr-post-20261021-a`, `sim/results/bgr-post-20261021-a.json` |
| Fill, LEF, chip-level density | — | **not run** | — |
| Runs `bgr-size-20261020-a/b/c`, `bgr-temp-20261020-a` | — | **invalid**, kept as record: RB generated as 130 µm instead of 500 µm (unit error in the runner) | `sim/runs/*/run.json` |

## Loop stability and noise (T7, 2026-10-21)

All numbers are simulated (ngspice 46, schematic level, no layout parasitics). The netlist is the frozen one
(sha256 `c19a7425…0c26`, checked by the runner for every run). Loads: `vref` 1 pF, `iptat` into 1.0 V.
Runs: `bgr-stb-20261021-b`, `bgr-noise-20261021-b`. Runs `-a` of both suites are kept and marked superseded.
Raw decks and waveforms: `<G1_RESULTS_ROOT>/r1_bgr/<run-id>/`. Summaries: `sim/results/summary-20261021.json`.

### Loop-gain method

1. The method is the r1_afe one: Tian double injection, Wiedmann form, `T = -1/(1 - 1/(2(i1 v2 - v1 i2) + v1 + i2))`.
2. The runner inserts a probe into a copy of the netlist. A 0 V source (AC voltage injection) and a current source (AC current injection) sit at the cut. The driver side keeps the net name. The receiver pins move to `<net>_rx`.
3. The toy loop agrees with the exact return ratio (error 4.7e-8).
4. Margins: PM is the angle between the phase at \|T\| = 1 and the −1 point. GM is −\|T\| in dB where the phase is an odd multiple of 180°. If the loop is positive at DC (T(0) < 0), GM at DC is −\|T(0)\|. The check for a right-half-plane pole (phase rising > 30° before unity) is used only when a unity crossing exists.

| Cut | Pins moved (count) | Loop it tests |
| --- | --- | --- |
| `pbias` | gates of `XMP*` mirror devices (13) | core loop through the 1:8 and 1:1 mirrors |
| `pcasc` | gates of `XMC*` PMOS cascodes (12) | cascode bias through `RB` and `XMNC2` |
| `vb2` | gates of `XMNC*` NMOS cascodes (9) | `MP5/MC5/RX/QD1/QD2` bias into the Q1 and Q2 cascodes |
| `vbe` | bases of the 48 Q2 units (48) | PTAT loop through V<sub>BE</sub> and the ΔV<sub>BE</sub> pair |
| `kick` | gate of `XMKFB` (1) | start-up detector (`XMPS`, `XRDET`, inverter, `XMKFB`) |

`vref` has no feedback path to the bias network. It is an output, so it has no loop of its own.

### Results (60 loop-gain runs, 0.1 Hz to 10 GHz)

| Corner | `pbias` PM / GM | `pcasc` peak \|T\| / GM | `vb2` GM | `vbe` GM (DC) | min \|1+T\| |
| --- | --- | --- | --- | --- | --- |
| tt / 27 °C / 3.3 V | 132.4° / 21.2 dB | −1.9 dB / 21.1 dB | 26.9 dB | 12.95 dB | 0.775 |
| ss / 125 °C / 3.0 V | 131.7° / no −180° crossing | −3.1 dB / 24.1 dB | 25.6 dB | 12.95 dB | 0.775 |
| ff / −40 °C / 3.6 V | 132.7° / 20.2 dB | −2.0 dB / 20.4 dB | 28.4 dB | 12.95 dB | 0.775 |
| hbt_wcs + res_bcs, 9 combinations at 27 °C | 132.1–132.5° / 20.6–20.8 dB | −1.9 dB / 20.4–20.9 dB | 26.3–26.8 dB | 12.93–12.94 dB | 0.774–0.799 |

Notes:

1. The core loop has 54.5–56.1 dB gain at DC and a unity crossing at 2.3–2.8 MHz. The phase at the crossing is about −48°.
2. `pcasc`, `vb2` and `vbe` have \|T\| < 1 at all frequencies. PM does not apply. The `pcasc` gain peaks within 1.9 dB of unity near 4 MHz, with positive phase, so GM and min\|1+T\| are the meaningful numbers.
3. The `vbe` cut has a positive-feedback loop at DC with gain 0.225 (12.95 dB below unity). This is the smallest GM. It does not depend on the corner. It is a DC property of the PTAT loop, so layout parasitics will not change it much.
4. The `kick` cut is open in the on state (\|T\| below −240 dB at all 12 corners). The detector does not load the loop once started. The start-up behaviour itself is in the start-up row.
5. A cut sees all loops that pass through it. The different cuts do not give one number. The worst PM and GM over cuts are the criterion values.
6. The hbt_wcs + res_bcs combinations give `vref` = 1.0558 V at every mos corner and supply. The loop margins do not change with the TC failure.

### Supply-step transient

| Case | `vref` before | Dip at the edge | Time of dip | 1 % | 0.1 % | 10 µV | Overshoot |
| --- | --- | --- | --- | --- | --- | --- | --- |
| tt / 27 °C | 1.044902 V | −10.30 mV (0.986 %) | 0.20 µs | never outside | 0.59 µs | 1.44 µs | none |
| ss / 125 °C (hbt_wcs, res_wcs) | 1.049035 V | −10.70 mV (1.020 %) | 0.20 µs | 0.14 µs | 0.69 µs | 1.64 µs | none |

The dip is edge coupling (≈ 3.4 % of the 0.3 V step; consistent with PSRR −26 dB at 1 MHz). The recovery is monotonic. The ss dip is 0.02 % beyond the 1 % band for 0.14 µs. The criterion is met (settling is far below 50 µs). The ADC reference buffer must tolerate a 10 mV dip when VDDA steps by 0.3 V in 100 ns.

### Noise

| Quantity | tt / 27 °C / 3.3 V | ss / 125 °C / 3.0 V |
| --- | --- | --- |
| rms 10 Hz–1 kHz | 30.8 µV | 41.1 µV |
| rms 10 Hz–100 kHz | **57.1 µV** | **73.7 µV** |
| rms 10 Hz–10 MHz (ngspice `onoise_total` 158.11 / 188.53 µV) | 158.1 µV | 188.5 µV |
| Density at 10 Hz / 1 kHz / 100 kHz | 5.29 µV/√Hz / 397 nV/√Hz / 139 nV/√Hz | 7.08 µV/√Hz / 528 nV/√Hz / 174 nV/√Hz |
| White floor (density at 200 kHz) | 135 nV/√Hz | 168 nV/√Hz |
| 1/f corner (density² = 2 × floor²) | 6.0 kHz | 6.9 kHz |
| Slope 10–100 Hz | f<sup>−1.15</sup> | f<sup>−1.15</sup> |
| Roll-off −3 dB (1 pF load, ≈ 180–200 kΩ source) | 0.88 MHz | 0.80 MHz |

Estimate against 0.25 LSB (110 µV rms, 12 bit, 0.9 V full scale). This is a first-order low-pass at the buffer pole applied to the simulated spectrum, integrated 10 Hz to 10 MHz:

| Buffer pole | 100 kHz | 300 kHz | 1 MHz | 3 MHz | 10 MHz | pole for 110 µV |
| --- | --- | --- | --- | --- | --- | --- |
| tt / 27 °C | 63.5 µV | 89.5 µV | 122.8 µV | 144.7 µV | 155.4 µV | 0.62 MHz |
| ss / 125 °C | 81.2 µV | 112.3 µV | 150.6 µV | 174.6 µV | 185.7 µV | 0.28 MHz |

1. A buffer that settles 0.42 pC in 33 ns needs a bandwidth of several MHz. At 1 MHz or more the noise is 123–151 µV. This is **above** 110 µV. The 0.25 LSB target is **not met** without a filter.
2. A filter at the buffer input fixes this. A pole at or below 0.28 MHz meets 110 µV at both corners. With the ≈ 180 kΩ source, 5 pF to ground at `vref` gives about 0.18 MHz. This is an estimate. The area is about 0.003 mm² (MIM). The filter must not slow the start-up or the supply-step recovery by more than a few µs.
3. The source of the noise (which devices) is not known. A per-device split was not run.
4. The estimate ignores sampling and aliasing in the ADC and the noise of the buffer. It also ignores the correlation of the `vref` noise between bit cycles (low-frequency noise is common to all bits of one conversion and acts as a gain error). Treat it as a bound.

### Failures and mistakes

| # | What happened | Class | Evidence |
| --- | --- | --- | --- |
| 1 | The first probe decks read `v(xbgr.pbias)`. `pbias`, `pcasc` and `vbe` are subcircuit ports and are top-level nets. ngspice printed "vector not available". Three of five cuts gave no data. Fixed with a port list. | tooling | scratch decks (not kept) |
| 2 | The first gain-margin code used `lim = L + 180` for odd multiples of 180°. It found the −180° crossing at the wrong phase. It reported GM 1.99 dB for `pcasc` where the true value is 21.1 dB. Found by comparing with the printed Bode data. Fixed before any run of record. | functional-bug | `run_bgr.py` `curve_margins` |
| 3 | The r1_afe right-half-plane check (phase rise > 30°) flagged `pcasc`, which has a LHP zero and no unity crossing. The flag only has meaning at a unity crossing. Fixed: check only with a crossing. | verification-gap | `run_bgr.py` |
| 4 | Loops with positive feedback at DC (`vb2`, `vbe`) were first reduced with a phase reference that hid the 180° start. Rewritten with an absolute phase and a DC special case. | planning | `run_bgr.py` |
| 5 | Noise run `-a`: the "white floor" was the minimum density in 100 Hz–1 MHz. That minimum is on the roll-off at the band edge, so the 1/f corner came out at 385 / 480 kHz. The definition of the corner was not in the task. Run `-b` uses the density at 200 kHz (corner 6.0 / 6.9 kHz). Run `-a` kept as superseded. | spec-ambiguity | `bgr-noise-20261021-a` |
| 6 | Transient run `-a` reported only the 1 % settling time (0.0 / 0.14 µs). That hides the recovery. Run `-b` adds 0.1 %, 100 µV and 10 µV times. Run `-a` kept as superseded. | verification-gap | `bgr-stb-20261021-a` |
| 7 | Open issue 4 gives a `vref` source impedance of ≈ 90 kΩ. The simulated noise roll-off (0.8–0.9 MHz with 1 pF) implies ≈ 180–200 kΩ including parasitics. The 90 kΩ figure was an estimate and is too low by about 2×. This section uses the simulated roll-off. | estimation | `bgr-noise-20261021-b` |
| 8 | A helper command `flow/run.sh python3 /dev/stdin` with a here-document did nothing, because the container gets no stdin. Scripts must be files under the repository or the results root. | tooling | — |
| 9 | The r3_cmc resistor model prints "voltage greater than vmax" warnings (`rppd`, `rhigh`) in noise and transient logs. They also appear in the earlier `op` and `mc` logs, but not in AC runs. Not investigated. The AC and noise results do not depend on them in any visible way. | verification-gap | `bgr-noise-20261021-b/noise_tt27.log` |
| 10 | No per-device noise split and no Monte Carlo of the loop gain were run (time budget). | verification-gap | — |

## Layout (T7, 2026-10-21)

### Files and built-against

Generator `layout/r1_bgr_layout.py` writes `layout/r1_bgr.gds`, `layout/r1_bgr_lvs.cdl` and
`layout/r1_bgr_layout_meta.json`. Tools: KLayout 0.30.9, kpex 0.3.12, ngspice 46, PDK
`84374023ee8b4b126bebbba67fcbada0a9c0ff0b` (see "Built against"). Each run directory has a `run.json`
(command, tool versions, PDK commit, GDS/CDL/netlist sha256).

Commands (from the repository root, POSIX sh):

1. `G1_CPUSET=100-102; export G1_CPUSET; G1_RESULTS_ROOT=<G1_RESULTS_ROOT>; export G1_RESULTS_ROOT`
2. `sh designs/r1-joint/blocks/r1_bgr/layout/run_checks.sh <tag>` (generator, DRC, LVS, run.json).
3. `flow/run.sh kpex --pdk ihp_sg13g2 --gds <gds> --cell r1_bgr --schematic <cdl> --2.5D --mode CC --out_dir <pex-cc dir>`
4. `flow/run.sh klayout -b -r designs/r1-joint/blocks/r1_bgr/layout/pex_build.py -rd kpexdir=<pex-cc dir>/r1_bgr__r1_bgr -rd gds=<gds> -rd out=<pex-rc dir>`
5. `G1_WORKDIR=designs/r1-joint/blocks/r1_bgr/sim flow/run.sh python3 run_bgr_post.py <run-id> <pex-rc run-id>`
6. `flow/run.sh python3 designs/r1-joint/blocks/r1_bgr/layout/pex_paths.py <pex-rc dir> <post dir>`

### Floorplan

Bottom to top: `vss` bus; resistor row (30 `rppd` columns: RB 12 units, R1 2 + R2 8 units interleaved
`R2 R2 R1 R2 R2 R2 R2 R1 R2 R2`, RX 4 units, dummy at each group end, all units carry current bottom to
top); `rhigh` RDET (15 units + 2 dummies); HBT bank 8 × 13 cells (66 active `npn13G2` Nx=1, 38 dummies,
common centroid for Q1 12, Q2 48, Q3 4; same cell orientation and emitter contact as G1); NMOS row
(interdigitated `D A×8 B×2 A×8 D`, then MNI, MKFB); two cascode rows; PMOS mirror row (`D MP5 MP1_0..3 MP2
MP3 MP1_4..7 MP4 MPS D`); `vdd` bus. Each device group has a p+ guard ring. Routing uses Metal1–Metal4:
Metal3 horizontal tracks, Metal4 vertical trunks. Metal5 and TopMetal are not used.

Precision returns: the Q1/Q3/QD2 emitters return on a separate `vssq` Metal3 track and a 2 µm Metal4 trunk
to the top head of R1 (the star). The trunk then goes to the `vss` bus. The Q2 emitters (`dvbe`) go on
their own Metal3 tracks and a 1 µm trunk to the bottom head of R1. `vbe` has a sense track (Q1 and Q2
bases, pin) and a force track (Q1 collectors from MNC1). This follows the G1 BGR586 lesson (metal
resistance in the emitter return).

### Extraction method

kpex RC mode leaves the devices on unsplit net nodes, and Magic RC leaves every `npn13G2` emitter on an
isolated node. Thus `layout/pex_build.py` builds the RC netlist itself:

1. It reads the kpex LVS database and the kpex 2.5D CC capacitances (373 C).
2. It extracts each net with `klayout.pex.RNetExtractor` (square counting). Sheet resistance: Metal1
   0.110 Ω/sq, Metal2–Metal4 0.088 Ω/sq, Via1–Via3 9 Ω per cut (PDK ITF typical values).
3. It puts one port on Metal1 at each device terminal and one port at each pin label.
4. It writes the layout devices with layout geometry (MOS AS/AD/PS/PD, resistor units, 104 HBT units).

Result: 197 devices, 64 nets, 372 terminal ports, 2730 R (0 negative, 0 open), 372 C, 866 fF.
Not modelled: contact resistance inside the PCells (Cont, EmWind, `rppd` heads are in the model).
The `dev` view is the layout devices + C with the wiring R shorted; `rc` is the full netlist.

### Pre- vs post-layout (simulated, `bgr-post-20261021-a`)

| Quantity | Condition | Schematic | Layout devices + C | Full RC |
| --- | --- | --- | --- | --- |
| V<sub>REF</sub> | tt/27 °C/3.3 V | 1.04489 V | 1.04565 V (+0.76 mV) | 1.04601 V (+1.12 mV, +0.11 %) |
| TC box −40…125 °C | tt/3.3 V | 8.4 ppm/°C | 9.3 ppm/°C | 9.9 ppm/°C |
| Supply current | tt/27 °C | 51.80 µA | 51.63 µA | 51.49 µA |
| `iptat` | tt/27 °C | 4.203 µA | 4.190 µA | 4.178 µA |
| ΔV<sub>BE</sub> (`dvbe`) | tt/27 °C | 91.13 mV | 91.13 mV | 91.35 mV |
| Start-up, 10 µs ramp to 3.0 V | tt/27 °C | end 1.0449 V, max 1.0645 V, 1 % at 8.2 µs | not run | end 1.0460 V, max 1.0734 V, 1 % at 10.1 µs |
| Start-up, 10 µs ramp to 3.0 V | ss/−40 °C | end 1.0469 V, max 1.1154 V, 1 % at 8.6 µs | not run | end 1.0477 V, max 1.1291 V, 1 % at 10.2 µs |
| Core loop (`pbias` gate cut, 13 gates) | tt/27 °C/3.3 V | PM 132.4°, GM 21.2 dB, f<sub>u</sub> 2.68 MHz | not run | PM 127.1°, no −180° crossing, f<sub>u</sub> 2.36 MHz |
| Core loop | ss/125 °C/3.0 V | PM 131.7°, f<sub>u</sub> 2.33 MHz | not run | PM 126.5°, f<sub>u</sub> 2.04 MHz |

All criteria of the schematic rows still pass (V<sub>REF</sub> within 0.11 %, TC ≤ 30 ppm/°C, start-up
ends 0.95–1.15 V, PM ≥ 60°). The V<sub>REF</sub> shift is mostly in the device view (+0.76 mV). A likely
cause is the `rppd` head resistance: R2 has 16 heads and R1 has 4 (ratio 4) while the body ratio is 4.137.
This split was not run. The wiring adds +0.36 mV.

### Precision-path resistance from the extraction (`pex-rc-20261021-b/pex_paths.json`)

| Path | Effective R | IR drop at tt/27 °C (min / mean / max over units) |
| --- | --- | --- |
| 48 Q2 emitters (`dvbe`) to R1 bottom head, all units together | 21.1 Ω | 86.2 / 90.0 / 94.0 µV |
| one Q2 emitter alone to R1 bottom head | 28.4–37.0 Ω | — |
| R1 bottom head to `dvbe` pin (sense only) | 33.5 Ω | no current |
| 12 Q1 emitters to the star (R1 top head) | 15.7 Ω | 20.4 / 34.9 / 51.1 µV |
| one Q1 emitter alone to the star | 19.2–22.5 Ω | — |
| star to `vss` pin | 16.3 Ω | 186 µV (common to Q1 and R1, outside ΔV<sub>BE</sub>) |
| Q1 bases to Q2 bases (`vbe`) | 2.5 Ω | 15.9 µV (mean) |
| 4 Q3 collectors to R2 bottom head (`vbe3`) | 29.9 Ω | — |
| R2 top head to `vref` pin | 32.4 Ω | — |

Most of the per-emitter resistance is in the via stack (9 Ω per cut). The net error in the ΔV<sub>BE</sub>
seen by R1 is estimated at −39 µV (0.04 % of 91.4 mV). This is an estimate from the port voltages.

### Open issues (layout)

1. Contact and EmWind resistance inside the PCells are not in the extracted wiring network. Their effect
   is in the device models only.
2. `rppd` head ratio (16:4) differs from the body ratio (4.137). It is a probable cause of the +0.76 mV
   device-view shift. A split run (head vs body) was not run.
3. Fill and density: not run at block level (waived). The chip-level fill must keep fill away from the
   HBT bank and the R1/R2 columns, or the chip-level run must check the shift.
4. No LEF and no abstract: not run. The chip integrator needs one.
5. The LVS reference (`r1_bgr_lvs.cdl`) adds 44 dummy devices to the netlist of record. The netlist of
   record itself is unchanged.
6. Post-layout mismatch, corner TC, PSRR and noise: not run. Only the rows in the table above were run.
7. Start-up overshoot at ss/−40 °C rises from 1.115 V to 1.129 V post-layout. The reference buffer input
   range must cover 1.13 V.

### Failures and mistakes

| # | What happened | Class | Evidence |
| --- | --- | --- | --- |
| 1 | The generator did not update the last x position for dummy NMOS fingers. MNI was placed over the last dummy. LVS shorted `det` and `kick` to `vss`. Fixed in run b. | functional-bug | `layout-lvs-20261021-a` |
| 2 | Run b had 50 DRC markers: M3.c1 41, M4.c1 5, M3.d 3, V2.b 1 (track-end enclosure, short-track area, Via2 spacing of same-net taps). The generator self-check covered only Metal2/Metal4 spacing. Fixed in run c. | verification-gap | `layout-drc-20261021-b` |
| 3 | Channel stubs of different nets collided (NC `pcasc`/`n1`, C12/DC tie taps). The first channel plan had no track-order rule. Fixed by track order and tap offset. | planning | generator self-check output in `layout-gen-20261021-b` |
| 4 | kpex RC mode does not split nets at device terminals, so it gives no device-level wiring R (G1 recorded the same). | tooling | `pex-rc-20261021-a` |
| 5 | Magic RC leaves every HBT emitter on an isolated node. | tooling | `pex-magic-20261021-a` |
| 6 | `RNetExtractor` with the tesselation method gave 24397 negative and 17771 open elements and `inf` values in ngspice. Square counting gives 0 and 0. | numerical | `pex-rc-20261021-b/pex_build.log` |
| 7 | kpex clears its `--out_dir`. It deleted the console log that was written there. Logs now go next to the run directory. | tooling | `pex-cc-20261021-a.console.log` |
| 8 | Wrong use of the KLayout 0.30 `RNode` API (type is a method; `decompose_convex` returns shapes). Some ports fell outside Metal1 until the convex-piece fix. | tooling | `layout-debug-20261021` |

## Area and current

| Quantity | Value | Basis |
| --- | --- | --- |
| Area | **0.01865 mm² (laid out)**, 96.0 × 194.3 µm | `layout/r1_bgr.gds` bounding box. The estimate before layout was 0.016–0.020 mm². |
| Comparison | Sep-19 0.0104 mm², BGR586 0.148 mm² | G1 README |
| VDDA current | 51.8 µA (tt/27 °C), 35.5–79.6 µA over corners and −40…125 °C | simulated |

Current split at tt/27 °C (4.2 µA per unit leg): Q1 branch 8 legs 33.6 µA, Q2, cascode bias, `vref`, `iptat`
and start-up detector one leg each.

## Open issues

1. **Corner TC** fails 30 ppm/°C at hbt_wcs + res_bcs (35 ppm/°C). It is a shift of the zero-TC point
   with no trim. Options: a 2-bit tap on R2 (±1 % range), or accept, because the ADC full scale is
   absorbed by host weights and the AFE gain register (spec D11). Owner decision.
2. **Q2 current density** is 0.088 µA per unit at 27 °C (Q1 2.8 µA, Q3 1.05 µA). The model card states
   V<sub>BE</sub> 0.65–0.96 V as its fitted range; Q1 runs at 0.56–0.78 V and Q2 at about 0.44–0.71 V (V<sub>BE1</sub> − ΔV<sub>BE</sub>) over corners and −40…125 °C. The
   ΔV<sub>BE</sub> at low density is a model extrapolation. G1 Sep-19 ran Q2 at 0.5 µA per unit.
3. **PSRR at 1 MHz** is about −26 dB (10 mV ripple gives ≈ 0.5 mV on `vref`). The ADC reference
   buffer and its MIM decoupling must filter it; a `vref` RC filter is not in this revision.
8. **Noise against 0.25 LSB**: the unfiltered `vref` noise (158 / 189 µV rms to 10 MHz) is above 110 µV. See "Loop stability and noise (T7)" for the filter estimate.
4. `vref` is unbuffered (≈ 90 kΩ source). Every consumer needs a buffer (INTERFACES: ADC reference buffer).
5. Start-up overshoot to 1.115 V with a 10 µs supply ramp at ss/−40 °C settles in 8.6 µs; check the
   reference buffer input range.
6. The `r4` HBT-ratio test mode of G1 is removed. If the T2F RATIO mode is wanted on R1, it must come back.
7. Mismatch at corners and joint T2F simulation with these rails: not run.
9. Layout open items: see "Layout (T7, 2026-10-21)", open issues.

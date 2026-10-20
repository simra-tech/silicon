# r1_afe — encoder analog front end (sine and cosine channels)

State (2026-10-20): **schematic level, revision D, simulated (ngspice, corners, cross corners, mismatch, loop gain). Not laid out.**
Revision C is superseded; its record follows the revision-D section ("Revision C record"). Revision B is superseded; its
record is kept at the end ("Revision B record").
All numbers in this file are **simulated** unless they are marked estimated. Nothing is measured.

Track T3 of `../README.md`. Specification row: `../../specification/R1_TOP_LEVEL_SPECIFICATION.md` §2 (`r1_afe`),
§4 (encoder input), gate V1. Input standard and accuracy budget: `../../specification/studies/S1_ENCODER_CHAIN_20261020.md`.

## Revision D (2026-10-20, track T3 revision D) — current state

Netlist of record: `schematic/r1_afe.spice` (revision D, sha256 `f32486ce…146b`). Revision C is kept as
`schematic/r1_afe_revC.spice`; its record follows below ("Revision C record"). All numbers are **simulated**
(ngspice-46, IHP SG13G2 `84374023`), at schematic level. LSB = 1.8 V / 4096 = 0.439 mV (D16) unless stated.

### What changed (revision C → D)

| # | Change | Why | Evidence (screen) |
| --- | --- | --- | --- |
| 1 | Stage-2 input string 17.5 kΩ → 19.44 kΩ (`LS2` 74.79 µm): gain 36/35 and 144/35 | D16: 1.44 Vpp differential output = 80 % of the ADC ±0.9 V full scale | `dev-revd-ocm-01` (variant `base`) |
| 2 | OTA2 bias references `XMB0 XMB1 XMB4 XMC3 XMC4` 4/1 µm → 8/2 µm | Open issue 3. The cause of the rev-C output-CM error was the mirror length: the OTA2 sinks (l = 2 µm) mirrored l = 1 µm references, so the mirror ratios moved with the corner and the CMFB pair had to absorb the difference. The fixed/CMFB sink split only made it visible (less CMFB gm). | `dev-revd-ocm-01` (`l2`) |
| 3 | OTA1 Miller cap fixed part 22 → 25 µm square, plus cross-coupled caps `XCX1` (cz1 → outn) and `XCX2` (cz2 → outp), 13 µm square | Open issue 2. A cross cap adds to the Miller cap for CM and subtracts for DM. The stage-1 CM loop gets more compensation at ×8/×32, while the DM compensation (and f_c) stays nearly the same. | `dev-revd-cm1-02`, `dev-revd-cm1ac-02/03`, `dev-revd-comb-ac-02` |
| 4 | OTA1 NMOS input pair 80 → 160 µm wide (l = 2 µm, ng 32) | Open issue 5: flicker noise at ×32 | `dev-revd-noise-01` (`np2`) |
| 5 | OTA2 output stage `W2P/W2N` 80/40 → 120/60 µm (+50 % current); output per-side caps `WCOS` 18.3 → 30 µm | Open issue 4: smallest worst-case settling error that was found inside the cost limit | `dev-revd-settle-01…05` |

Driver and flow changes: `sim/run_afe.py` freezes the netlist, every template and itself into
`$G1_RESULTS_ROOT/r1_afe/<run-id>/frozen/` at campaign start and simulates only those copies (`run.json` field
`netlist_sha256`, `frozen_inputs`). It also adds the D16 LSB, the 1 % overload threshold of 1.44 V, the `dev:<kind>:<variants>`
development campaign (`devvar()` lists every variant as netlist edits), subckt-scoped edits, cross corners `sf fs ssx ffx`,
the campaign `stbx`, an overshoot count in the CM-step reduction, and a validity flag `pm_valid` for loop-gain results.
The flag is false when the broken-loop phase rises more than 30° above its DC value (right-half-plane pole), and the
reduction then counts the margin as failed. New helpers: `sim/dev_summary.py` (development-sweep summary) and
`sim/apply_revd.py` (writes the screened variant into the netlist of record, so the netlist is exactly what was screened).
`sim/report_afe.py` has the revision-D LSB, the noise-margin criterion, the `stbx` reduction and the CM-step overshoot fields.

### Built against (revision D)

Same as revision C (table below): PDK commit `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` (checked by `flow/run.sh`
before every run), ngspice-46 (container build of 2026-07-27, banner read into each `run.json`), container image
`sha256:ddeb6957…bab2`. The cross corners use the PDK sections `mos_sf`/`mos_fs` (`cornerMOShv.lib`, listed in the
container on 2026-10-20). Run with `G1_CPUSET=106-108`, `G1_CPUS=3`.

### Status (revision D, run suffix `20261020d`)

Evidence: `sim/runs/<run-id>/run.json` (question, result, disposition, input sha256), `sim/results/<run-id>.json`,
reduced numbers in `sim/results/summary-20261020d.json`; raw decks, logs and waveforms in `<G1_RESULTS_ROOT>/r1_afe/<run-id>/`.

| Check | Criterion | Status | Evidence (run id) |
| --- | --- | --- | --- |
| Output swing (D16) | 1.44 Vpp differential at full input | **passed**: gain ×1 1.012–1.028 (36/35 = 1.029; TG and string tolerance), ×32 32.16–32.66; output 1.43–1.46 Vpp at 1.4 Vpp input; outputs 0.238–0.955 V in the THD runs | `r1afe-ac-20261020d`, `r1afe-tran-20261020d` |
| Output CM, all gains, corners, input CM | 0.600 V ± 30 mV | **passed**: 0.5935–0.5973 V at tt/ss/ff, every step, input CM 0.5/2.5/2.8 V (revision C 0.577–0.648 V); 0.594–0.597 V in the THD runs | `r1afe-ac-20261020d` |
| Stage-1 CM loop (OTA1, output break) | PM ≥ 60° at every step, tt/ss/ff, input CM 0.5/2.5/2.8 V, track and hold load | **passed**: worst 62.4° (ss, ×32, CM 0.5 V); ×8 worst 66.2 | `r1afe-stb-20261020d` |
| Stage-1 DM loop | PM ≥ 55° | **passed**: worst 64.4° (ff, ×8), GM ≥ 15.5 dB | `r1afe-stb-20261020d` |
| Stage-2 DM loop | PM ≥ 55° | **passed**: worst 67.7° (ff, ×1, hold load), GM ≥ 10.0 dB | `r1afe-stb-20261020d` |
| Stage-2 CM loop | PM ≥ 60° | **passed**: worst 61.3° (ff, ×16, hold load), GM ≥ 21.7 dB | `r1afe-stb-20261020d` |
| CMFB-node breaks (`cmfb1`, `cmfb2`) | informational (not a valid Nyquist break, see revision C finding 2) | **not applicable**: flagged `pm_valid = false` by the new check, as expected | `r1afe-stb-20261020d` |
| Loop gain at cross corners, ×1 and ×32, input CM 0.5/2.5 V | same PM limits at tt, ss, ff, sf, fs, ssx (ss, 3.6 V, −40 °C), ffx (ff, 3.0 V, 125 °C) | **failed at ffx**: dm1 52.8° (×1, CM 0.5 V), cm1 54.3° (×32, CM 2.5 V), cm2 59.6° (×32); **passed** at tt, ss, ff, sf, fs, ssx (worst: sf/fs cm1 64.3°, ss cm1 62.4°, ff cm2 62.7°) | `r1afe-stbx-20261020d`; candidate fix `dev-revd-ffx-02` |
| Anti-alias f_c | ≥ 1.0 MHz at every step, corner, input CM | **passed**: min 1.020 MHz (ss, ×32, CM 0.5 V); peaking ≤ 0.0001 dB | `r1afe-ac-20261020d` |
| CM-step transient (pin CM 2.45→0.6→2.45 V, vcm2 +50 mV, VDDA −0.2 V, full-scale sine), tt/ss/ff, ×1/×32 | no sustained oscillation (≤ 1 mV pp before the next event); the test flags `dev-revb-02` | **passed**: ≤ 0.24 mV pp; `dev-revb-02` 1490 mVpp. Recorded (not a criterion here, see the trade-off table): pin step settles to 5 mV in ≤ 596 ns, up to 3 excursions beyond 5 mV at ×32 (large signal: 200–360 mV stage-1 CM excursion); vcm2 step ≤ 1 overshoot, ≤ 82 ns to 2 % | `r1afe-cmstep-20261020d` |
| Settling into the r1_adc T/H (2.8 pF/side, top plate 0 V, 250 ns), 5 levels, tt/ss/ff, ×1/×32 | total error ≤ 0.25 LSB (INTERFACES.md) | **failed**: worst 0.38 LSB (tt ×32); ss ×1 0.37, ss ×32 0.28, ff ×32 0.23 LSB. Revision C: 1.29 LSB (at its 0.488 mV LSB) | `r1afe-settle_adc-20261020d` |
| Same, non-linear residual after a linear gain/offset fit | ≤ 0.25 LSB (accepted criterion, see settling decision) | **passed**: ≤ 0.005 LSB; linear part a gain error of −0.023 % to +0.024 %, equal in both channels | `r1afe-settle_adc-20261020d` |
| Noise ×32, input-referred, 1 Hz–100 MHz | ≤ 35 µV rms with ≥ 5 % margin at ss (≤ 33.25 µV) | **passed**: 31.0 µV ss (11 % margin), 26.1 tt, 23.3 ff | `r1afe-noise-20261020d` |
| Noise ×1, output | ≤ 0.41 LSB rms (180 µV at the D16 LSB) | **passed**: 164 µV = 0.37 LSB (ss); 145 tt, 132 ff | `r1afe-noise-20261020d` |
| THD at 100 kHz, 1.44 Vpp out, ×1/×32, tt/ss/ff | ≤ 0.1 % | **passed**: worst 0.025 % (−72.0 dB, ss ×1) | `r1afe-tran-20261020d` |
| Gain steps ×1–×32, both channels | steps present; ratio error recorded | **passed**: step-ratio error ≤ 1.41 % (×32) | `r1afe-ac-20261020d` |
| Pole matching, 20 MC samples per corner, every step | \|Δf3\| ≤ 1 % | **passed**: worst 0.961 % (ss), σ ≤ 0.36 %; phase mismatch at 100 kHz ≤ 0.078°; gain mismatch ≤ 1.01 % (removed by GAIN_RATIO). Margin 0.04 % | `r1afe-ac_mc-20261020d` |
| Temperature −40/27/125 °C at tt | f_c ≥ 1 MHz; gain recorded | **passed**: f_c min 1.371 MHz (125 °C, ×32); gain spread ≤ 0.53 % (×32) | `r1afe-temp-20261020d` |
| Input CM 0–3.3 V with the stock analog pad | gain within 2 %; pad current < 1 µA at 2.8 V | **passed**: gain variation ≤ 1.54 % (ss ×32); pad current ≤ 4.1 nA at 2.8 V, 13 nA at 3.0 V | `r1afe-cm-20261020d` |
| PSRR from VDDA, 20 kHz and 1 MHz (20 MC samples, tt), at the 1.44 Vpp swing | ≥ 40 dB | **passed**: worst 54.3 dB (20 kHz), 54.7 dB (1 MHz). Recorded: VDDA → output CM −41.5 to −43.1 dB at 20 kHz (revision B −58 to −61 dB), −28 to −31 dB at 1 MHz; the `l2` bias change raised the low-frequency CM supply coupling (10 mV ripple → ≈ 85 µV CM, no DM effect) | `r1afe-psrr-20261020d` |
| Input overload ±1.0 V differential, recovery | recorded (1 LSB = 0.439 mV, 1 % = 14.4 mV) | **recorded**: ×32 recovery to 1 LSB ≤ 1236 ns (ss), to 1 % ≤ 882 ns; ×1 ≤ 842 ns to 1 LSB. Output CM falls to 0.148 V during ×32 overload (revision C 0.06 V) | `r1afe-overload-20261020d` |
| Source impedance 0/100/300/1000 Ω per pin | gain change recorded | **recorded**: at 1 kΩ ×1 −2.4 to −2.8 %, ×8/×32 −16.6 to −18.8 %; at 100 Ω ≤ 2.3 % | `r1afe-rsrc-20261020d` |
| Loop-gain method check (toy loop) | matches an exact return ratio | **passed** (re-run, independent of the netlist) | `r1afe-stbval-20261020d` |
| Gain-switch transients, bias from r1_bgr, c1..c4 level shifters | — | **not run** | — |
| Layout, DRC, LVS, PEX, post-layout | — | **not run** | — |

### Settling decision (item 4; deviation from INTERFACES.md for the coordinator)

INTERFACES.md (AFE → ADC) asks for a total settling error ≤ 0.25 LSB in the 250 ns track window. Revision D does
**not** meet it. The worst total error is 0.38 LSB (tt ×32). The output-stage option was tried first, inside the cost
limit of 1 mA and 0.02 mm². OTA2 output current ×1.5 or ×2 and per-side reservoir caps of 30 or 40 µm reached 0.12–0.30 LSB
at ss ×32 alone. But at three corners the worst total stayed at 0.38 LSB (WCOS 30 µm) or 0.79 LSB (WCOS 40 µm). The error is
the sum of two terms with opposite signs, an RC tail through R_o and the OTA2 recovery from the CDAC kick. A
cancellation at one corner does not hold at the others. A switched OTA2 Cc reached 0.20 LSB, but it made OTA2
marginally stable (DM2 PM 39.8°) and was rejected. Revision C's development data needed +0.8 mA for 0.36 LSB (old LSB).

The decision is therefore the fallback that the task allows: the linear part (a gain error of −0.023 % to +0.024 %,
equal in both channels, stable within a chip at a given corner) is calibrated by the ADC/host gain correction (the per-step GAIN_RATIO
registers). The accepted criterion is the non-linear residual, ≤ 0.25 LSB; simulated ≤ 0.005 LSB. Residual risk: the
linear part drifts with temperature by up to about 0.05 % (≈ 0.4 LSB at full scale, tt→ss spread) if the gain calibration is done at one
temperature only. **Coordinator action**: change the AFE → ADC row of INTERFACES.md from "settling ≤ 0.25 LSB" to "non-linear
settling residual ≤ 0.25 LSB; linear settling gain error ≤ 0.03 % removed by the gain calibration", or reject and
ask for an output buffer (estimated > 1 mA).

### Item 3 trade-off (stage-1 CM phase margin vs f_c)

| Netlist | CM1 PM ×8 / ×32, worst over tt/ss/ff and input CM (°) | f_c min (MHz) | Note |
| --- | --- | --- | --- |
| Revision C | 54.1 / 54.3 | 1.023 | failed PM |
| D16 + `l2`, no stage-1 change | 54.1 / 54.5 | 1.034 | `dev-revd-cm1-01` |
| Cross Miller `cx26.3_14.4` (alone) | 68.3 / 64.4 | 0.977 | failed f_c |
| **Revision D** (`cx25_13` + `np2`) | 66.2 / 62.4 | 1.020 | both met at tt/ss/ff; ffx cross corner 54.3° (×32) failed |

Both targets are met at tt/ss/ff, so the CM-step fallback acceptance is not used. The CM-step data are recorded in the status table.

### Regression check list (every item that passed in revision C, re-run in revision D)

| Revision-C pass | Revision-D result | Run |
| --- | --- | --- |
| Loop-gain method (toy loop) | passed | `r1afe-stbval-20261020d` |
| Stage-1 DM PM ≥ 55° (rev C 68.0°) | passed, 64.4° (lower: cross caps, still > 55°) | `r1afe-stb-20261020d` |
| Stage-2 DM PM ≥ 55° (65.6°) | passed, 67.7° | `r1afe-stb-20261020d` |
| Stage-2 CM PM ≥ 60° (63.2°) | passed, 61.3° (lower, margin 1.3°) | `r1afe-stb-20261020d` |
| Loop-gain coverage (tt/ss/ff, CM 0.5/2.5/2.8 V, six steps, track and hold load) | passed, same coverage | `r1afe-stb-20261020d` |
| CM-step test, no sustained oscillation, detects `dev-revb-02` | passed | `r1afe-cmstep-20261020d` |
| Gain steps present, ratio error recorded (1.70 %) | passed, 1.41 % | `r1afe-ac-20261020d` |
| f_c ≥ 1 MHz (1.023 MHz) | passed, 1.020 MHz (margin 2.0 %) | `r1afe-ac-20261020d` |
| Pole matching ≤ 1 % (0.96 %) | passed, 0.961 % | `r1afe-ac_mc-20261020d` |
| THD ≤ 0.1 % (0.032 %) | passed, 0.025 % | `r1afe-tran-20261020d` |
| Settling non-linear residual (0.082 LSB) | passed, 0.005 LSB | `r1afe-settle_adc-20261020d` |
| Noise ×32 ≤ 35 µV (34.8 µV) | passed, 31.0 µV | `r1afe-noise-20261020d` |
| Noise ×1 ≤ 0.41 LSB (0.36 LSB at 0.488 mV) | passed, 0.37 LSB at 0.439 mV | `r1afe-noise-20261020d` |
| Temperature f_c ≥ 1 MHz (1.371 MHz) | passed, 1.371 MHz | `r1afe-temp-20261020d` |
| Input CM with pad: gain ≤ 2 %, pad current < 1 µA (1.56 %, 49 nA) | passed, 1.54 %, 4.1 nA | `r1afe-cm-20261020d` |
| PSRR ≥ 40 dB (51.0 dB) | passed, 54.3 dB | `r1afe-psrr-20261020d` |
| Overload, source impedance (recorded) | recorded | `r1afe-overload-20261020d`, `r1afe-rsrc-20261020d` |

Rule for later revisions: a change is not done until every row of this list is re-run and still passes. The output-CM
failure of revision C was a regression of this kind (revision B passed, revision C failed, and no list caught it).

### Area and current (revision D)

| Item | Value | Basis |
| --- | --- | --- |
| Area, both channels with VCM1 divider | ≈ 0.099 mm² (MOS 0.029, rppd 0.033, MIM 0.038); revision C 0.091 | **estimated**, `sim/area_estimate.py` → `sim/results/area_estimate_revD.json` |
| of which item 5 (noise, `np2`) | ≈ +0.003 mm² (MOS) | estimated; limit 0.01 mm² |
| of which item 4 (settling: output stage ×1.5, WCOS 30 µm) | ≈ +0.004 mm²; +0.2 mA | estimated / simulated; limit 0.02 mm², 1 mA |
| of which item 2 (`l2`), item 3 (cross Miller) | ≈ +0.0002 mm² (MOS), ≈ +0.0025 mm² (MIM) | estimated |
| VDDA current, both channels | 1.71–2.00 mA (tt 1.76–1.95, ss 1.71–1.90, ff 1.93–2.00); revision C 1.53–1.86 mA | simulated, operating points in `r1afe-ac-20261020d` |
| Power | 5.1–7.2 mW | simulated current × VDDA |

### Open issues (revision D)

1. **Cross corner ffx (ff, 3.0 V, 125 °C) fails**: dm1 52.8° (×1, CM 0.5 V), cm1 54.3° (×32, CM 2.5 V), cm2 59.6°.
   Candidate fix for dm1: OTA1 switched Miller part 20.4 → 24 µm (`ccb24`, dm1 → 56.7°, f_c unchanged,
   `dev-revd-ffx-02`). cm1 and cm2 at ffx need a further change (the larger cross cap gives only +0.9°). Not applied:
   the campaign of record was running.
2. **Settling total error 0.38 LSB** against 0.25 LSB in INTERFACES.md: the decision above needs the coordinator
   (interface change or output buffer).
3. **Stage-2 CM PM margin is 1.3°** (61.3°, ff ×16 hold load) and f_c margin is 2 % (1.020 MHz). Layout parasitics
   at the OTA2 output and at the stage-1 summing nodes will move both.
4. **CM-step large-signal ringing**: the 1.85 V pin-CM step at ×32 gives up to 3 excursions beyond 5 mV and settles in
   ≤ 596 ns (no sustained oscillation). Head CM steps of this size are not expected in operation.
5. Revision-C open issues 6–7 stay open: source impedance (5 kΩ input units at ×8–×32), interfaces not designed here
   (PGA_GAIN decoder and level shifters, `vcm2` from r1_adc, bias from r1_bgr), VCM1 from VDDA.
6. Checks marked **not run** in the status table.

### Failures and mistakes (revision D)

| # | What happened | Class | Record |
| --- | --- | --- | --- |
| 1 | Revision C attributed the output-CM error to the OTA2 fixed/CMFB sink split. The cause was the OTA2 mirror length (l = 2 µm sinks and sources from l = 1 µm references). Revision B had the same error at a smaller size (+28 mV ss). The split only made it larger. | estimation | `dev-revd-ocm-01` |
| 2 | Revision C failed output CM after revision B passed it; no regression list existed. | regression | regression list above |
| 3 | CM-only Miller caps cz → vcms (`cmm8/14/20`) formed a local positive loop. The broken-loop return ratio had a right-half-plane pole, and the Bode PM came out above 360°. The idea was wrong. | functional-bug | `dev-revd-cm1-01` |
| 4 | The loop-gain reduction did not detect a right-half-plane pole and printed PM > 360° without a warning. Fixed: `pm_valid` flag; an invalid margin counts as failed. | verification-gap | `run_afe.py` `stb_post` |
| 5 | The cross-Miller arithmetic (DM cap = F² − X² kept at 22² µm²) predicted no f_c change; f_c fell 3–6 %. | estimation | `dev-revd-cm1ac-02`, `-03` |
| 6 | Switched OTA2 Cc (`c2sw`) was screened for settling before its loop gain. It gave 0.12–0.20 LSB, but DM2 PM fell to 39.8° (at high frequency the stage-2 feedback factor is set by Cf2 and is near 1 at every step). Two combined campaigns were spent on it. | planning | `dev-revd-settle-01…03`, `dev-revd-comb-*-01` |
| 7 | Settling screens at one corner (ss ×32) suggested 0.12–0.14 LSB; at three corners the same variants gave 0.38–0.79 LSB (cancellation of two opposite terms). | verification-gap | `dev-revd-settle-04`, `-05` |
| 8 | First `dev_summary.py` split variant names at `_`, and a shell filter (`grep -v cm2`) also removed every `cm2.5` line; a summary was misread for one step (no wrong decision taken). | tooling | — |
| 9 | Run `dev-revd-ffx-01` aborted before any job: the variant name `cxs14.5` matched the `cx` branch first. Re-run as `-02`. | tooling | `runs/dev-revd-ffx-01/run.json` |
| 10 | Revision C ran campaigns on the live netlist (`r1afe-settle_adc-20261020c` aborted after an edit). Fixed: per-campaign frozen copies. | process-hygiene | `run_afe.py` `freeze()` |
| 11 | Two campaigns shared CPUs 106–108 for 6 minutes (`dev-revd-ffx-02` next to `20261020d`); the allocation was not exceeded, wall time only. | planning | — |
| 12 | "The two mixed corners" in the task is ambiguous. Taken as the MOS corners sf and fs (3.3 V, 27 °C); the supply/temperature cross terms ssx and ffx were added. | spec-ambiguity | `r1afe-stbx-20261020d` |

### Files (revision D additions)

| Path | Content |
| --- | --- |
| `schematic/r1_afe.spice` | revision D netlist of record |
| `schematic/r1_afe_revC.spice` | revision C netlist (runs `r1afe-*-20261020c2`) |
| `sim/run_afe.py` | driver (freeze, D16 LSB, `dev:` campaigns, `devvar()`, `stbx`, cross corners, `pm_valid`) |
| `sim/report_afe.py` | reductions (revision D LSB and criteria, `stbx`, CM-step overshoots) |
| `sim/run_all.sh` | campaign set, revision D default list |
| `sim/dev_summary.py`, `sim/apply_revd.py` | development-sweep summary; writes the screened variant into the netlist |
| `sim/results/summary-20261020d.json`, `sim/results/area_estimate_revD.json` | reduced numbers and area estimate of revision D |
| `sim/runs/r1afe-*-20261020d/`, `sim/runs/dev-revd-*/` | run records (campaign of record; development screens) |

Reproduce: `G1_RESULTS_ROOT=<bulk results root>; export G1_RESULTS_ROOT`, then
`sh designs/r1-joint/blocks/r1_afe/sim/run_all.sh 20261020d` and `cd designs/r1-joint/blocks/r1_afe/sim && python3 report_afe.py 20261020d`.

---

# Revision C record (superseded by revision D)

## Built against

| Item | Version | How established |
| --- | --- | --- |
| PDK | IHP SG13G2 open PDK, commit `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` | `flow/run.sh` checks `/foss/pdks/ihp-sg13g2/COMMIT` before every run; copied into each `run.json` |
| ngspice | ngspice-46 (container build of 2026-07-27) | `ngspice -v` banner, read by `sim/run_afe.py` into each `run.json` |
| Container image | `sha256:ddeb6957…bab2` (`tapeoutbench-eda:latest`) | identity verified by `flow/run.sh` |
| Models | `cornerMOShv.lib`, `cornerMOSlv.lib`, `cornerRES.lib`, `cornerCAP.lib`, `cornerDIO.lib`; PSP 103 / r3_cmc OSDI (`sim/.spiceinit`) | deck headers (`sim/common_head.inc`) |
| IO cell | `sg13g2_IOPadAnalog` from `libs.ref/sg13g2_io/spice/sg13g2_io.spi` (stock, with the `dantenna` diodes) | `sim/tb_afe_cm.cir` |
| xschem / KLayout / CACE | not used in this step | — |

The IHP `TO_Nov2024` BG/OTA was not used (single-ended; this block needs a fully differential OTA), so it is not
cloned into `third_party/`. The G1 `g1_sense` OTA (`designs/g1-guardian/blocks/g1_sense/sim/netlist/g1_ota.spice`)
is the style reference for bias and cascode generation; no G1 file is copied.

## What it is

Two identical channels (sine `XSIN`, cosine `XCOS`). Each channel has two inverting, fully differential stages and
an output R-C:

```
 SIN_P/N pads              stage 1: PGA (rail-to-rail OTA1)          stage 2: filter + level shift (OTA2)      to r1_adc T/H
 (0.5-2.8 V CM)         Rf1 = 40k || Cf1 1.44 pF (pole ~2.8 MHz)    Rf2 = 20k || Cf2 2.85 pF (pole ~2.8 MHz)
      o--[n1 x 40k]--[TG]--+--|\                 +--[1 or 4 x 14k]--[TG]--+--|\              R_o 3k
                           |  |OTA1>-- out CM 1.0 V ---                   |  |OTA2>-- out CM --/\/\--+-- OUT_P/N
      o--[n1 x 40k]--[TG]--+--|/      (VDDA x 0.30)                       +--|/   0.6 V (vcm2)        |   C_o 3 pF diff
                     n1 = 1, 2, 4, 8                       gain 8/7 or 32/7                            + 0.5 pF/side
```

- Overall gain = step × 8/7 (revision C, D11), so 1.4 Vpp at ×1 and 43.75 mVpp at ×32 give **1.6 Vpp differential**
  at the output. Revision B used 10/7 (2.0 Vpp). D16 (2026-10-20, after the revision-C campaigns started) sets the
  ADC full scale to ±0.9 V and the AFE target to 1.44 Vpp: revision C keeps 8/7, so the ADC sees 1.6 Vpp = 89 % of
  its full scale (open issue 1).
- Gain steps: stage 1 uses n1 parallel 40 kΩ units against one 40 kΩ feedback unit. Every unit, including the
  feedback unit, has the same transmission gate in series, so the TG on-resistance cancels in the ratio. Stage 2
  uses one or four 17.5 kΩ strings against 20 kΩ (revision B: 14 kΩ).

| PGA_GAIN code | Step | n1 (stage 1) | stage 2 | c1 c2 c3 c4 |
| --- | --- | --- | --- | --- |
| 0 | ×1 | 1 | 8/7 | 0 0 0 0 |
| 1 | ×2 | 2 | 8/7 | 1 0 0 0 |
| 2 | ×4 | 4 | 8/7 | 1 1 0 0 |
| 3 | ×8 | 8 | 8/7 | 1 1 1 0 |
| 4 | ×16 | 4 | 32/7 | 1 1 0 1 |
| 5 | ×32 | 8 | 32/7 | 1 1 1 1 |

- Anti-alias filter: one real pole per stage, set by Rf·Cf and independent of the gain step, plus the OTA
  closed-loop poles and the output R-C (≈ 6 MHz). The two channels are matched by layout symmetry of identical
  rppd units and MIM capacitors.
- Input common mode: in an inverting stage the OTA input sees (V_in,cm·G + V_out,cm)/(G + 1). At ×8 this follows
  the pin almost fully (0.5–2.8 V), so OTA1 has NMOS and PMOS input pairs (rail-to-rail) into one folded cascode.
  OTA2 sees an almost constant input CM (0.84–0.94 V) and has a PMOS pair only (lower noise).
- Level shift: stage 1 runs at 1.0 V output CM, stage 2 at 0.6 V. The resistor network carries
  (1.0 − 0.6) V / (R_in2 + R_f2) ≤ 15 µA per side (revision C). Revision A first used 1.65 V for stage 1. The 51 µA level-shift
  current then starved the stage-1 output device (THD 2.9 % at ff, run `dev-quick2-06`).
- Revision-C compensation (from the loop-gain analysis): OTA1 Miller capacitance 22 µm square fixed plus 20.4 µm
  square switched in by `c3b` (connected for n1 < 8: ×1, ×2, ×4, ×16; open at ×8 and ×32), zero resistor 3.4 kΩ,
  CMFB sense capacitors 22 µm square (lead at the CM sense node), PMOS-pair tail 90 µA (was 60 µA). OTA2: CMFB pair
  32/1, fixed sink 20 µm (from `ibias`) and CMFB sink 10 µm (the CMFB controls part of the sink current, not all),
  sense capacitors 14 µm square, Cc 18 µm square, zero resistor 1.6 kΩ. The OTA1 subcircuit has two new ports
  `cen cenb` (driven by `c3b c3` inside the channel); the top-level ports are unchanged.
- Output common mode 0.6 V: **assumption** from the r1_adc spec row (1.2 V domain, 2.4 Vpp differential FS) and the
  r1_adc schematic of 2026-10-20 (`../r1_adc/schematic/r1_adc.spice`: top-plate sampling on the CDAC, PMOS
  comparator input for a CM falling from 0.6 V toward 0 V). `vcm2` is a port. It must come from the r1_adc
  reference (VREF/2), not from this block.
- Bias: 10 µA into each OTA (`ib_s1`, `ib_s2`, `ib_c1`, `ib_c2`) from r1_bgr. The testbenches use ideal sources.
- Gain controls `c1..c4` are 3.3 V signals. The decoder from `PGA_GAIN` and the 1.2 V → 3.3 V level shifters are
  not in this block (open issue 6).

Ports of `r1_afe` (`schematic/r1_afe.spice`, unchanged in revision C): `sinp sinn cosp cosn` (pads), `souts_p souts_n soutc_p soutc_n`
(to the T/H), `vcm2` (0.6 V), `ib_s1 ib_s2 ib_c1 ib_c2` (10 µA each, sunk), `c1 c2 c3 c4`, `vdd` (VDDA), `vss`.
Connect the AFE input to the `pad` terminal of `sg13g2_IOPadAnalog`, not to `padres`. The 587 Ω secondary
resistor would add to the 5 kΩ input units without a matching feedback part.

## Status (revision C, run suffix `20261020c2`; LSB = 2.0 V / 4096 = 0.488 mV unless stated)

All numbers are **simulated** (ngspice-46, IHP SG13G2 `84374023`). Evidence: `sim/runs/<run-id>/run.json` and
`sim/results/<run-id>.json`; reduced numbers in `sim/results/summary-20261020c2.json`.

| Check | Criterion | Status | Evidence (run id) |
| --- | --- | --- | --- |
| Loop-gain method | Tian double injection matches an exact return ratio | **passed**: max relative error 4.7e-8, 10 Hz–1 GHz | `r1afe-stbval-20261020c` |
| Stage-1 differential loop (OTA1, broken at its outputs) | PM ≥ 55° | **passed**: worst PM 68.0° (ff, ×8), worst GM 14.8 dB | `r1afe-stb-20261020c2` |
| Stage-1 common-mode loop (CMFB and the CM path through the input pairs) | PM ≥ 60° | **failed**: worst PM 54.3° (ss, ×32, input CM 2.5 V), GM ≥ 16.2 dB. The u3 netlist reached ≥ 64.1° but failed f_c (see row "Anti-alias f_c"; open issue 2) | `r1afe-stb-20261020c2`; u3: `r1afe-stb-20261020c` |
| Stage-2 differential loop (OTA2) | PM ≥ 55° | **passed**: worst PM 65.6° (ff, ×1, hold load), worst GM 10.8 dB | `r1afe-stb-20261020c2` |
| Stage-2 common-mode loop | PM ≥ 60° | **passed**: worst PM 63.2° (ss, ×16, CM 0.5 V), GM ≥ 22.0 dB | `r1afe-stb-20261020c2` |
| Loop-gain coverage | tt/ss/ff, input CM 0.5/2.5/2.8 V, all six steps, track load (100 Ω + 2.8 pF) and hold load | **passed**: 12 jobs × 6 steps × 6 breaks; input CM 1.65 V and the input-node cross-check breaks ran on u3 only | `r1afe-stb-20261020c2`, `r1afe-stb-20261020c` |
| Method check on revision B | revision B and the `dev-revb-02` variant that oscillated | **recorded**: revision B worst CM PM 13.2° (ss ×32), DM PM 16.2° (×1); `dev-revb-02` CM PM −11.1° (tt ×32), so the analysis predicts the oscillation | `r1afe-stb_revb-20261020c` |
| CM-step transient (pin CM 2.45→0.6→2.45 V, vcm2 +50 mV, VDDA −0.2 V, full-scale 100 kHz sine), tt/ss/ff, ×1/×32 | no sustained oscillation: CM ≤ 1 mV pp before the next event; the test must flag `dev-revb-02` | **passed**: ≤ 0.31 mV pp; pin-CM step settles to 5 mV in ≤ 614 ns; `dev-revb-02` shows a sustained 1.49 Vpp stage-1 CM oscillation | `r1afe-cmstep-20261020c2` |
| Gain steps ×1–×32, both channels, tt/ss/ff, CM 0.5/2.5/2.8 V | steps present; ratio error recorded | **passed**: step-ratio error ≤ 1.70 % (×32) vs 2^k; host calibration per step | `r1afe-ac-20261020c2` |
| Anti-alias f_c | ≥ 1 MHz at every step, corner, CM | **passed**: min 1.023 MHz (ss, ×32, CM 0.5 V); peaking ≤ 0.0001 dB | `r1afe-ac-20261020c2` |
| Pole matching, 20 MC samples per corner (tt/ss/ff), every step | \|Δf3\| ≤ 1 % | **passed**: worst 0.96 % (ss), σ ≤ 0.43 %; phase mismatch at 100 kHz ≤ 0.080°; gain mismatch ≤ 1.18 % (removed by GAIN_RATIO) | `r1afe-ac_mc-20261020c2` |
| THD at 100 kHz, 1.6 Vpp out, ×1 and ×32, tt/ss/ff | ≤ 0.1 % | **passed**: worst 0.032 % (−70.0 dB, ss ×1); outputs 0.179–1.041 V | `r1afe-tran-20261020c2` |
| Settling into the INTERFACES.md T/H (2.8 pF/side, top plate 0 V, 250 ns), 5 levels (±FS, ±FS/2, FS/4) | total error ≤ 0.25 LSB | **failed**: error at full scale ≤ 1.29 LSB (ss ×32), 0.25 LSB (tt ×1). With the D16 LSB (1.8 V/4096 = 0.439 mV): ≤ 1.44 LSB | `r1afe-settle_adc-20261020c2` |
| Same, after removing a linear gain/offset fit | non-linear residual ≤ 0.25 LSB | **passed**: ≤ 0.082 LSB (0.091 LSB at the D16 LSB); the linear part is a gain error ≤ 0.079 % that is the same in both channels | `r1afe-settle_adc-20261020c2` |
| Noise ×32, input-referred, 1 Hz–100 MHz | ≤ 35 µV rms | **passed (small margin)**: 34.8 µV ss, 28.1 µV tt, 24.8 µV ff | `r1afe-noise-20261020c2` |
| Noise ×1, output | ≤ 0.41 LSB rms | **passed**: 178 µV = 0.36 LSB (ss); 0.41 LSB at the D16 LSB | `r1afe-noise-20261020c2` |
| Temperature −40/27/125 °C at tt (3.3 V) | f_c ≥ 1 MHz; gain recorded | **passed**: f_c min 1.371 MHz (125 °C, ×32); gain spread ≤ 0.59 % (×32) | `r1afe-temp-20261020c2` |
| Input overload: ±1.0 V differential (2 Vpp), 10 µs each polarity, then +FS/2 | recovery time recorded | **recorded**: ×32 recovery to 1 LSB ≤ 1232 ns (ss), to 1 % ≤ 872 ns; ×1 ≤ 840 ns. Output CM falls to 0.06 V during ×32 overload | `r1afe-overload-20261020c2` |
| Source impedance 0/100/300/1000 Ω per pin | gain change recorded | **recorded**: at 1 kΩ, ×1 −2.1 to −2.8 %, ×8–×32 −14.7 to −18.8 % (5 kΩ input units); 100 Ω: ≤ 2.3 % | `r1afe-rsrc-20261020c2` |
| Input CM 0–3.3 V with the stock analog pad | gain within 2 %; pad current < 1 µA at 2.8 V | **passed**: gain variation ≤ 1.56 %; pad current ≤ 49 nA at 2.8 V | `r1afe-cm-20261020c2` |
| PSRR from VDDA, 20 kHz and 1 MHz (20 MC samples, tt) | ≥ 40 dB (derived in revision B) | **passed**: worst 51.0 dB | `r1afe-psrr-20261020c2` |
| Output CM | 0.6 V ± 30 mV (limit set in revision B) | **failed**: 0.577–0.648 V (ss +48 mV). Revision B: 0.600–0.628 V. Cause: the OTA2 fixed-sink split that lowers the CM loop gain (open issue 3) | `r1afe-ac-20261020c2` |
| Output swing 1.44 Vpp (D16, ±0.9 V ADC full scale) | stage-2 gain ≈ 36/35 | **not run**: D16 arrived during the final campaign; revision C keeps 8/7 (1.6 Vpp = 89 % of ±0.9 V) | — |
| Supply-corner cross terms, sf/fs MOS corners, gain-switch transients | — | **not run** | — |
| Bias from r1_bgr, level shifters for c1..c4 | — | **not run** (blocks not available) | — |
| Layout, DRC, LVS, PEX, post-layout | — | **not run** | — |

Corners: tt = mos_tt/res_typ/cap_typ, 3.3 V, 27 °C; ss = mos_ss/res_wcs/cap_wcs, 3.0 V, 125 °C; ff = mos_ff/res_bcs/
cap_bcs, 3.6 V, −40 °C.

### Stability findings (revision C)

1. Revision B was far from the targets. The stage-1 differential loop had a PM of 15–17° (GM 2.5 dB) at ×1 at all
   corners. The closed-loop AC check could not see this, because the loop crosses unity near 80 MHz, where the
   closed-loop response is already about 30 dB down. The stage-1 CM loop had a PM of 13° at ss ×32. The CMFB
   variant `dev-revb-02` had a negative CM margin, which matches its oscillation in the transient runs.
2. The CMFB return ratio at the CM sense node has a DC phase of 180° at several operating points. When the PMOS-pair
   tail of the rail-to-rail OTA1 loses headroom (OTA input CM 1.7–2.3 V), the input pairs form a positive CM loop
   with a gain above 1. A break at the CMFB input therefore does not give a valid Nyquist test. The CM criterion uses
   the break at the OTA outputs, which contains all CM paths. The DM break at the outputs gives the same result as
   the break at the inputs (cross-check in `r1afe-stb-20261020c`).
3. Fixes: a larger Miller capacitor and zero resistor (DM1); CM-sense feed-forward capacitors (they cancel the pole
   of the 200 kΩ sense resistors and the CMFB-pair gate); and in OTA2, a CMFB that controls only part of the sink
   current (CM2 changes from 30° to 63°). The full Miller capacitor reduced f_c at ×8/×32 with input CM 0.5 V
   (only the PMOS pair is active) to 0.836 MHz. Part of the capacitor is therefore switched off at n1 = 8. This
   costs CM1 margin at ×8/×32 (54° instead of 64°).
4. Development sweeps: `dev-stbsweep1..6-01`, `dev-fcsweep-01`, `dev-ccsw-01` to `dev-ccsw4-01` (each `run.json` gives
   the question and the result).

### Numbers (simulated, revision C)

Gain and f3 (AC, input CM 2.5 V; f3 min over CM 0.5/2.5/2.8 V and all corners in the last column):

| Step | gain tt | f3 tt (MHz) | f3 ss (MHz) | f3 ff (MHz) | f3 min (MHz) |
| --- | --- | --- | --- | --- | --- |
| ×1 | 1.134 | 1.652 | 1.297 | 2.119 | 1.286 |
| ×2 | 2.263 | 1.623 | 1.271 | 2.082 | 1.238 |
| ×4 | 4.514 | 1.565 | 1.204 | 2.014 | 1.144 |
| ×8 | 9.017 | 1.543 | 1.177 | 1.998 | 1.125 |
| ×16 | 18.031 | 1.462 | 1.111 | 1.889 | 1.038 |
| ×32 | 36.008 | 1.439 | 1.081 | 1.874 | 1.023 |

Noise (1 Hz–100 MHz): ×1 output 157/178/142 µV rms (tt/ss/ff); ×32 input 28.1/34.8/24.8 µV rms; ×32 input density at
1 kHz / 100 kHz / 1 MHz at ss: 171 / 29 / 19 nV/√Hz. At ss the ×32 margin is 0.6 %. The 8/7 stage-2 gain and the
OTA2 changes moved it from 35.3 to 33.7 µV (u3), and the switched Miller capacitor and the larger PMOS tail moved it
back to 34.8 µV. The input pair and the first-stage resistors were not changed, so this item has no area cost.

THD at 100 kHz (1.6 Vpp out): tt 0.012 / 0.009 %, ss 0.032 / 0.027 %, ff 0.007 / 0.006 % (×1 / ×32).

Settling into the r1_adc T/H, 250 ns track (error at the end of track; LSB 0.488 mV):

| Corner | ×1 error at FS (LSB) | ×32 error at FS (LSB) | ×32 gain error (%) | non-linear residual, worst (LSB) |
| --- | --- | --- | --- | --- |
| tt | 0.25 | 0.97 | 0.057 | 0.082 |
| ss | 0.22 | 1.29 | 0.079 | 0.045 |
| ff | 0.12 | 0.51 | 0.030 | 0.065 |

The error at the end of track is the sum of a slow under-settling tail and an overshoot left by the kick (the 2.8 pF
CDAC charges from 0 V on each side; only 0.5 pF per side of the output network is a CM reservoir). In the
development sweeps (`dev-settlesweep1-01`, `dev-settlesweep2-01`, ss, +FS), a reservoir or OTA2 output-stage changes
reduce the ×32 error to 0.36–0.52 LSB. The 0.36 LSB case needs three times the OTA2 output current (+0.8 mA). The
low values in some variants come from cancellation of the two terms with opposite signs between ×1 and ×32, so they
are not robust. Revision C keeps the revision-B output network.

## Area and current (revision C)

| Item | Value | Basis |
| --- | --- | --- |
| Area, both channels with VCM1 divider | ≈ 0.091 mm² (MOS 0.025, rppd 0.033, MIM 0.034) | **estimated**, `sim/area_estimate.py` → `sim/results/area_estimate_revC.json` (revision B: 0.0835 mm²). The +0.007 mm² is MIM: the OTA1 Miller and CM-sense capacitors and the OTA2 sense capacitors |
| VDDA current, both channels | 1.53–1.86 mA (tt 1.59–1.78, ss 1.53–1.72, ff 1.78–1.86) | simulated, operating points in `r1afe-ac-20261020c2`. The OTA1 PMOS tail adds about 0.06 mA to revision B |
| Power | 4.6–6.7 mW | simulated current × VDDA |

## Open issues (revision C)

1. **D16 output target 1.44 Vpp (±0.9 V ADC full scale) is not applied.** Revision C keeps stage-2 gain 8/7 (1.6 Vpp
   = 89 % of full scale). To apply D16, set R_in2 to 19.44 kΩ (gain 36/35 and 144/35), then re-run the gain-step,
   settling, loop-gain (stage 2) and noise decks.
2. **Stage-1 CM loop PM 54.3° at ×8/×32 (target 60°)**, with GM ≥ 16 dB. The CM-step test shows no ringing problem
   (settling ≤ 614 ns, ≤ 0.31 mV residual). Candidate fixes: a CMFB with its own compensation, or a
   rail-to-rail input stage whose tail current does not depend on the input CM (it now forms a positive CM loop near
   the PMOS-pair cut-off).
3. **Output CM 0.577–0.648 V** (limit ±30 mV set in revision B). This comes from the OTA2 fixed/CMFB sink split. A
   bandgap-referenced fixed sink, or a smaller fixed fraction with retuned sense caps, would restore the accuracy.
   Confirm the ADC input CM tolerance with the r1_adc owner.
4. **Settling: the total error at full scale is ≤ 1.29 LSB**, and it is linear: the residual is ≤ 0.082 LSB and both
   channels have the same gain error. If the per-step GAIN_RATIO calibration is not accepted as the remedy, an
   output buffer per side or about 0.8 mA more OTA2 output current is needed (see the settling paragraph).
5. **×32 noise margin is 0.6 % at ss** (34.8 µV). To add margin: input units of 20 kΩ (halves the input impedance)
   or a larger NMOS pair for flicker noise.
6. **Source impedance**: the 5 kΩ input units at ×8–×32 give −16.6 % gain at 1 kΩ (tt). The effect is the same in
   both channels for equal head impedance, but it depends on the temperature of the head.
7. Revision-B items 5–8 (step accuracy, interfaces not designed here, input impedance, VCM1 from VDDA) stay open.
8. Checks marked **not run** in the status table.

Run-record notes: the revision-C first pass (`r1afe-*-20261020c`, u3 netlist without the switched capacitor) is
kept as superseded. `r1afe-settle_adc-20261020c` was aborted after the netlist changed during the campaign. The
`r1afe-stb_revb-20261020c` run and the revision-B rows of `r1afe-cmstep-20261020c` remain valid.

## Files

| Path | Content |
| --- | --- |
| `schematic/r1_afe.spice` | revision C source (netlist of record): OTA1 (`r1_afe_ota`, with the switched Miller part), OTA2 (`r1_afe_ota2`), TG, inverter, resistor units, stage sides, channel, top |
| `schematic/r1_afe_revB.spice` | revision B source (runs `r1afe-*-20261020b`), superseded |
| `schematic/r1_afe_revA.spice` | revision A source (runs `r1afe-*-20261020a`) |
| `sim/common_head.inc`, `sim/gain_codes.inc` | model/corner header and gain-code table, inserted into every deck |
| `sim/tb_afe_ac.cir` | (a) gain, −3 dB, phase, peaking at every step, both channels; with `NMC > 1` the mismatch loop |
| `sim/tb_afe_tran.cir` | (b) 100 kHz full-scale sine, THD (fourier), swing, CM ripple |
| `sim/tb_afe_noise.cir` | (c) noise at every step (×1, ×32 required), spectra to the bulk directory |
| `sim/tb_afe_cm.cir` | (d) input CM 0–3.3 V with the stock analog pad on all four pins |
| `sim/tb_afe_psrr.cir` | (e) PSRR from VDDA at 20 kHz and 1 MHz |
| `sim/tb_afe_settle.cir`, `sim/tb_afe_settle_adc.cir` | 2 MSPS track-and-hold load: generic model (revisions A/B) and r1_adc-matched model (LSB a substitution since revision C) |
| `sim/tb_afe_stb.cir` | loop gain (Tian), six breaks: stage-1/2 DM and CM at the OTA outputs, CMFB sense node, stage-1 inputs; probes inserted by `run_afe.py` into a copy of the netlist |
| `sim/tb_stb_toy.cir` | validation of the loop-gain formula against an exact return ratio |
| `sim/tb_afe_cmstep.cir` | CM-step transient (pin CM, vcm2, VDDA steps with a full-scale sine) |
| `sim/tb_afe_overload.cir` | 2 Vpp input overload and recovery |
| `sim/tb_afe_rsrc.cir` | gain and f3 vs source impedance (derived from `tb_afe_ac.cir`) |
| `sim/stb_print.py`, `sim/stb_worst.py`, `sim/ccsw_summary.py` | print helpers for the loop-gain development runs |
| `sim/run_afe.py` | driver: campaigns, deck rendering, parallel ngspice, `results/<run-id>.json`, `runs/<run-id>/run.json` |
| `sim/run_all.sh` | the campaign set (revision C default list; `CAMPAIGNS=` selects) |
| `sim/report_afe.py`, `sim/summarize.py` | reduction to the numbers above; fills question/result/disposition in `run.json` |
| `sim/area_estimate.py` | area estimate |
| `sim/results/summary-20261020c2.json` | all reduced numbers of revision C (first pass: `summary-20261020c.json`; revision B: `summary-20261020b.json`; revision A: `summary-20261020a.json`) |
| `sim/results/area_estimate_revC.json` | area estimate of revision C (revision B: `area_estimate_revB.json`) |
| `sim/runs/*/run.json` | one record per run. `dev-*` runs are development iterations on earlier netlists, labelled superseded |
| `sim/dev/` | three early hand decks (smoke, CM check, device currents) used before the driver existed |

`sim/run_afe.py`, `sim/report_afe.py` and `sim/run_all.sh` were edited after the `20261020b` runs to remove a machine
path (usage text and an environment default only). The sha256 in each `run.json` refers to the version that ran.

Raw decks, logs, waveforms and noise spectra: `$G1_RESULTS_ROOT/r1_afe/<run-id>/` (bulk storage, not in git).

Revision C changed `sim/run_afe.py` (per-job netlist edits, loop-gain probes, post-processing, new campaigns),
`sim/report_afe.py` (revision-C reductions), `sim/tb_afe_settle_adc.cir` (LSB substitution) and `sim/area_estimate.py`
(optional netlist argument). Each `run.json` records the sha256 of the inputs that ran, and the netlist edits of each job.
In the revision-C result files the bulk-root path was replaced by `$G1_RESULTS_ROOT` after the runs (the driver now
writes it that way). The loop-gain probes and development variants are applied to a copy of the netlist in the raw directory
(`<job>_netlist.spice`). The netlist of record is not edited for them.

Reproduce (repository root):

```
G1_RESULTS_ROOT=<bulk results root>; export G1_RESULTS_ROOT
sh designs/r1-joint/blocks/r1_afe/sim/run_all.sh <suffix>        # revision C: 20261020c2
cd designs/r1-joint/blocks/r1_afe/sim && python3 report_afe.py <suffix>
```

`run_all.sh` sets `G1_CPUSET=106-108 G1_CPUS=3 G1_WORKDIR=designs/r1-joint/blocks/r1_afe/sim`, requires the bulk
`G1_RESULTS_ROOT`, then calls `flow/run.sh python3 run_afe.py <campaign> r1afe-<campaign>-<suffix>`.

## Revision B record (superseded by revision C)

Kept as history. Netlist `schematic/r1_afe_revB.spice`, runs `r1afe-*-20261020b`. The LSB in this record is 2.4 V / 4096.

### Status (revision B)

| Check | Criterion | Status | Evidence (run id → `sim/runs/<id>/run.json`) |
| --- | --- | --- | --- |
| Gain steps ×1–×32, both channels, tt/ss/ff, input CM 0.5/2.5/2.8 V | steps present; ratio error recorded | **passed** (step-ratio error ≤ 1.87 % vs ideal 2^k; calibrated by the host) | `r1afe-ac-20261020b` |
| Anti-alias f_c ≥ 1 MHz at every step, corner, CM | f3 ≥ 1 MHz | **passed**, min 1.057 MHz (ss, ×32, CM 0.5 V); no peaking (max 0.000 dB) | `r1afe-ac-20261020b` |
| Pole matching between channels, 20-sample MC (`mm_ok=1`, mismatch sections of MOS, rppd, MIM) at tt/ss/ff, every step | \|Δf3\| ≤ 1 % | **passed**, worst 0.895 % (tt ×32), σ ≤ 0.40 %; phase mismatch at 100 kHz ≤ 0.067° | `r1afe-ac_mc-20261020b` |
| THD and swing, 100 kHz full scale (2.0 Vpp out), ×1 and ×32, tt/ss/ff | THD ≤ 0.1 % (−60 dB), set in this step from the angle budget (H3 0.1 % → 0.06° el) | **passed**, worst 0.054 % (−65.4 dB, ss ×1); outputs 0.105–1.117 V; CM ripple ≤ 0.03 mV | `r1afe-tran-20261020b` |
| Noise ×1 (output, 1 Hz–100 MHz) | ≤ 240 µV rms (0.41 LSB): AFE keeps chain ENOB ≥ 11 with an ENOB-11.5 SAR | **passed**, worst 205 µV rms (0.35 LSB, ss) | `r1afe-noise-20261020b` |
| Noise ×32 (input-referred) | ≤ 35 µV rms: σ_φ ≤ 0.1° el per sample at 40 mVpp (S1 allocates 0.15° el to electronics) | **failed (marginal)**: 35.3 µV ss; 28.6 µV tt, 25.3 µV ff | `r1afe-noise-20261020b` |
| Input CM 0–3.3 V, operation inside 0.5–2.8 V, stock `sg13g2_IOPadAnalog` on all pins | gain within 2 % of its 1.65 V value; pad current < 1 µA at 2.8 V (limits set in this step) | **passed**: gain variation ≤ 1.62 %; output CM unchanged | `r1afe-cm-20261020b` |
| Pad ESD-diode leakage up to 3.0 V (spec open item 4) | record | **recorded**: 2.8 V: ≤ 4.1 nA; 3.0 V: ≤ 13 nA (ss, VDDA 3.0 V, 125 °C); 3.3 V at VDDA 3.0 V: 34 µA (diode forward) | `r1afe-cm-20261020b` |
| PSRR from VDDA at 20 kHz and 1 MHz | no spec limit; derived ≥ 40 dB set after the run (10 mVpp ripple below the ×32 input noise) | **passed against the derived limit**: worst 54.9 dB (MC, tt); symmetric netlist > 200 dB | `r1afe-psrr-20261020b` |
| Settling into a 2 MSPS T/H, generic model (2 pF/side, reset to 0.6 V, 250 ns track) | non-linear residual ≤ 0.5 LSB | **passed**: error at +FS ≤ 0.75 LSB, of which all but ≤ 0.056 LSB is a linear gain error (≤ 0.045 %) | `r1afe-settle-20261020b` |
| Settling into the r1_adc-matched T/H (2.8 pF/side CDAC, top plate reset to 0 V, 250 ns track) | non-linear residual ≤ 0.5 LSB | **failed (marginal)**: residual 0.506 LSB (tt ×32), error at +FS ≤ 1.94 LSB | `r1afe-settle_adc-20261020b` |
| CM loop stability (output and stage-1 CM ripple in the full-scale transients) | no oscillation | **passed** at tt/ss/ff ×1 and ×32. Two earlier variants oscillated (`dev-quick-03`, `dev-revb-02`); see open issue 3 | `r1afe-tran-20261020b` |
| Output CM | 0.6 V ± 30 mV (set in this step) | **passed**: 0.600–0.628 V | `r1afe-ac-20261020b` |
| Loop-gain phase margin (Middlebrook / stb) of OTA1 and OTA2, differential and CM | — | **not run**. Only closed-loop peaking and transient CM ripple are checked | — |
| Temperature sweep beyond the corner temperatures (−40 °C ff, 27 °C tt, 125 °C ss) | — | **not run** | — |
| Supply-corner cross terms (ss at 3.6 V, ff at 3.0 V), sf/fs MOS corners | — | **not run** | — |
| Overload recovery (input above full scale for the selected step), gain-switch transients | — | **not run** | — |
| Input-source impedance (head output impedance against the 5–40 kΩ input units) | — | **not run** | — |
| Bias from r1_bgr (ideal 10 µA sources here), digital level shifters for c1..c4 | — | **not run** (blocks not available) | — |
| Layout, DRC, LVS, PEX, post-layout | — | **not run** | — |

Revision A (`schematic/r1_afe_revA.spice`, runs `r1afe-*-20261020a`) failed pole matching (1.52 %) and ×32 noise
(40.6 µV, ss). Revision B fixed both, the second only to the margin shown above. Revision A was not run with the
r1_adc-matched T/H. Its records stay as history (disposition "superseded").

### Numbers (simulated, revision B, run suffix `20261020b`)

Corners: tt = mos_tt/res_typ/cap_typ, 3.3 V, 27 °C; ss = mos_ss/res_wcs/cap_wcs, 3.0 V, 125 °C;
ff = mos_ff/res_bcs/cap_bcs, 3.6 V, −40 °C. Input CM 2.5 V (AC) or 2.45 V (transients: pins stay ≤ 2.8 V at 1.4 Vpp).
Load 2 pF per output unless the T/H model is used.

Gain and −3 dB bandwidth (AC, input CM 2.5 V; sine and cosine identical in the nominal runs):

| Step | gain tt | f3 tt (MHz) | f3 ss (MHz) | f3 ff (MHz) | f3 min over CM 0.5/2.5/2.8 V, all corners (MHz) |
| --- | --- | --- | --- | --- | --- |
| ×1 | 1.411 | 1.655 | 1.301 | 2.120 | 1.296 |
| ×2 | 2.816 | 1.644 | 1.292 | 2.107 | 1.279 |
| ×4 | 5.618 | 1.623 | 1.269 | 2.081 | 1.241 |
| ×8 | 11.225 | 1.575 | 1.216 | 2.029 | 1.164 |
| ×16 | 22.437 | 1.530 | 1.188 | 1.967 | 1.151 |
| ×32 | 44.814 | 1.472 | 1.121 | 1.906 | 1.057 |

Phase at 100 kHz (both channels, CM 2.5 V): −4.1° (ff ×1) to −7.8° (ss ×32). It depends on the gain step and the corner,
and it is common to both channels.

Channel matching, 20 mismatch samples per corner (two seeds × 10), every step:

| Corner | worst \|Δf3\| (%) | σ(Δf3) (%) | worst \|Δphase\| at 100 kHz (°) | worst \|Δgain\| (%) |
| --- | --- | --- | --- | --- |
| tt | 0.895 (×32) | 0.40 | 0.066 | 0.97 |
| ss | 0.829 (×32) | 0.40 | 0.067 | 1.06 |
| ff | 0.606 (×32) | 0.28 | 0.034 | 0.91 |

The S1 budget uses 0.06° el at 100 kHz for 1 % pole matching. The simulated worst phase difference of 20 samples
is 0.067°, so the 1 % criterion and the 0.06° figure do not agree exactly. The gain difference (≤ 1.06 %) is
removed by the GAIN_RATIO calibration.

Noise (1 Hz–100 MHz, source impedance 0):

| Corner | ×1 output (µV rms / LSB) | ×1 input (µV rms) | ×32 input (µV rms) | ×32 input density at 1 kHz / 100 kHz / 1 MHz (nV/√Hz) |
| --- | --- | --- | --- | --- |
| tt | 180 / 0.31 | 127 | 28.6 | 124 / 22 / 16 |
| ss | 205 / 0.35 | 146 | 35.3 | 172 / 29 / 19 |
| ff | 163 / 0.28 | 115 | 25.3 | 100 / 17 / 13 |

At ×32 the 1 Hz–100 kHz part is mostly flicker noise of the stage-1 path. The NMOS input pair is the active pair at
the usual 2.5 V head CM.

Transient, 100 kHz, 2.0 Vpp differential output (THD of both channels identical):

| Corner | THD ×1 | THD ×32 | output range (V) | output CM (V) |
| --- | --- | --- | --- | --- |
| tt | 0.022 % (−73.4 dB) | 0.025 % (−72.1 dB) | 0.118–1.105 | 0.612 |
| ss | 0.054 % (−65.4 dB) | 0.050 % (−66.0 dB) | 0.138–1.117 | 0.627 |
| ff | 0.011 % (−79.0 dB) | 0.018 % (−75.1 dB) | 0.105–1.096 | 0.600 |

Track-and-hold settling, 250 ns track (2 MSPS), error at the end of track for +FS input (LSB = 0.586 mV differential):

| Model | ×1 tt/ss/ff | ×32 tt/ss/ff | linear gain error ×32 (worst) | non-linear residual (worst) |
| --- | --- | --- | --- | --- |
| generic (2 pF, reset 0.6 V) | 0.07 / 0.08 / 0.03 | 0.43 / 0.75 / 0.18 | 0.045 % | 0.056 LSB |
| r1_adc-matched (2.8 pF, reset 0 V) | 0.38 / 0.30 / 0.17 | 1.94 / 1.81 / 1.37 | 0.116 % | 0.506 LSB |

The error repeats identically every cycle, and it is almost proportional to the output. It therefore acts as a gain
error that is equal in both channels to within the matching above. The residual is computed from +FS, −FS and +FS/2.

Input CM sweep with the stock pad (×1 and ×32): gain varies ≤ 1.62 % across 0.5–2.8 V. The cause is the
transmission-gate on-resistance, which changes with the summing-node voltage while the feedback TG does not see the
same voltage. Pin current into the AFE: −11 µA (0.5 V) to +43 µA (2.8 V) per pin at ×32 (5 kΩ effective input
unit), −6 to +26 µA at ×1 (40 kΩ); worst values over the three corners.

PSRR (input-referred, A_dm / A_VDDA): with mismatch ≥ 54.9 dB at 20 kHz and 1 MHz, ×1 and ×32 (tt, 20 samples).
VDDA to output CM: −58 to −61 dB at 20 kHz and −25 to −28 dB at 1 MHz. The VCM1 divider is VDDA-referred, and its
2 pF filter pole is ≈ 0.5 MHz.

### Area and current

| Item | Value | Basis |
| --- | --- | --- |
| Area, both channels with VCM1 divider | ≈ 0.084 mm² (MOS 0.025, rppd 0.032, MIM 0.027) | **estimated**: drawn device area from the netlist × overhead (MOS ×4, rppd ×2, MIM ×1.3), `sim/area_estimate.py` → `sim/results/area_estimate_revB.json`. No layout. Budget in S3: 0.06–0.08 mm² |
| Revision A area (w = 2 µm resistors) | ≈ 0.123 mm² | same script on `schematic/r1_afe_revA.spice` |
| VDDA current, both channels | 1.53–1.79 mA (tt 1.59–1.71, ss 1.53–1.66, ff 1.75–1.79), depends on gain step and input CM | simulated, operating points in `r1afe-ac-20261020b` |
| Power | 5.0–6.4 mW (S3 estimate for the AFE: ≈ 4.3 mW, uncertain) | simulated current × VDDA |

### Open issues

1. **×32 noise at ss is 35.3 µV rms against 35 µV** (marginal). Remedies: lower the flicker of the stage-1 path
   (longer CMFB-controlled sinks gave −2 µV in `dev-revb-01` but made the CM loop oscillate, see 3), more OTA1 input-pair
   current, or a 4 % lower f_c (the ss ×32 margin is 5.7 %).
2. **Settling into the r1_adc-matched T/H: residual 0.506 LSB at tt ×32** (marginal). The T/H model is my reading of
   the r1_adc schematic of 2026-10-20 (2.8 pF CDAC per side, top plate near 0 V at the start of track). Confirm the
   track time, the start-of-track top-plate voltage and the sampling capacitance with the r1_adc owner. A larger
   C_o (now 3 pF differential + 0.5 pF per side) or a longer track time reduces the kick.
3. **CM-loop stability of OTA1 is fragile.** It oscillated (stage-1 CM ≈ 1.3–1.5 Vpp) when the folding-node
   capacitance grew (`dev-quick-03`, `dev-revb-02`). It was found only in transients, because AC with a differential
   stimulus does not excite the CM loop. A CM loop-gain (stb) analysis with phase margin at all corners is not run
   and is needed before layout. Layout parasitics at `fn`/`fp` will move it.
4. **Area ≈ 0.084 mm² and power 5.0–6.4 mW exceed the S3 estimates** (0.06–0.08 mm², ≈ 4.3 mW). The largest items
   are the four OTAs (≈ 0.4 mA each), the rail-to-rail stage-1 OTA, the 200 kΩ CMFB sense resistors and the MIM
   filter and output capacitors.
5. **Gain step accuracy** is 1.9 % at ×32 relative to 32 × (×1 gain), and gain varies 1.6 % with input CM (TG
   on-resistance). This is not a matching problem, because both channels see the same CM and code. The host
   calibration must be repeated per gain step (S1 register set: GAIN_RATIO and OFFSET per step, not one value).
6. **Interfaces not designed here**: the PGA_GAIN → c1..c4 decoder (table above) with 1.2 V → 3.3 V level shifters;
   `vcm2` (0.6 V) from the r1_adc reference; four 10 µA bias currents from r1_bgr (ideal in all runs; bias-path
   PSRR not included).
7. **Input impedance** is 40 kΩ (×1) down to 5 kΩ (×8 to ×32) per pin to a virtual ground near the pin CM. DC pin
   current is up to 43 µA at 2.8 V CM. Heads with a kΩ-level source impedance get a gain error, equal in both
   channels to first order. Not simulated with a source impedance.
8. **VCM1 is derived from VDDA** (1.0 V at 3.3 V; 0.91–1.09 V over 3.0–3.6 V). This is acceptable for the stage-1
   CM, but a bandgap-derived reference would remove the VDDA → CM path at 1 MHz.
9. Checks marked **not run** in the status table: loop-gain margins, temperature sweep, cross corners, overload and
   gain-switch transients, source impedance, layout and post-layout.

# r1_afe — encoder analog front end (sine and cosine channels)

State (2026-10-20): **schematic level, revision B, simulated (ngspice, corners and mismatch). Not laid out.**
All numbers in this file are **simulated** unless they are marked estimated. Nothing is measured.

Track T3 of `../README.md`. Specification row: `../../specification/R1_TOP_LEVEL_SPECIFICATION.md` §2 (`r1_afe`),
§4 (encoder input), gate V1. Input standard and accuracy budget: `../../specification/studies/S1_ENCODER_CHAIN_20261020.md`.

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
                     n1 = 1, 2, 4, 8                       gain 10/7 or 40/7                           + 0.5 pF/side
```

- Overall gain = step × 10/7, so 1.4 Vpp at ×1 and 43.75 mVpp at ×32 give **2.0 Vpp differential** at the output
  (80 % of the 2.4 Vpp SAR full scale). The 10/7 factor is a choice of this step (the spec row lists only ×1–×32).
- Gain steps: stage 1 uses n1 parallel 40 kΩ units against one 40 kΩ feedback unit. Every unit, including the
  feedback unit, has the same transmission gate in series, so the TG on-resistance cancels in the ratio. Stage 2
  uses one or four 14 kΩ strings against 20 kΩ.

| PGA_GAIN code | Step | n1 (stage 1) | stage 2 | c1 c2 c3 c4 |
| --- | --- | --- | --- | --- |
| 0 | ×1 | 1 | 10/7 | 0 0 0 0 |
| 1 | ×2 | 2 | 10/7 | 1 0 0 0 |
| 2 | ×4 | 4 | 10/7 | 1 1 0 0 |
| 3 | ×8 | 8 | 10/7 | 1 1 1 0 |
| 4 | ×16 | 4 | 40/7 | 1 1 0 1 |
| 5 | ×32 | 8 | 40/7 | 1 1 1 1 |

- Anti-alias filter: one real pole per stage, set by Rf·Cf and independent of the gain step, plus the OTA
  closed-loop poles and the output R-C (≈ 6 MHz). The two channels are matched by layout symmetry of identical
  rppd units and MIM capacitors.
- Input common mode: in an inverting stage the OTA input sees (V_in,cm·G + V_out,cm)/(G + 1). At ×8 this follows
  the pin almost fully (0.5–2.8 V), so OTA1 has NMOS and PMOS input pairs (rail-to-rail) into one folded cascode.
  OTA2 sees an almost constant input CM (0.84–0.94 V) and has a PMOS pair only (lower noise).
- Level shift: stage 1 runs at 1.0 V output CM, stage 2 at 0.6 V. The resistor network carries
  (1.0 − 0.6) V / (R_in2 + R_f2) ≤ 17 µA per side. Revision A first used 1.65 V for stage 1. The 51 µA level-shift
  current then starved the stage-1 output device (THD 2.9 % at ff, run `dev-quick2-06`).
- Output common mode 0.6 V: **assumption** from the r1_adc spec row (1.2 V domain, 2.4 Vpp differential FS) and the
  r1_adc schematic of 2026-10-20 (`../r1_adc/schematic/r1_adc.spice`: top-plate sampling on the CDAC, PMOS
  comparator input for a CM falling from 0.6 V toward 0 V). `vcm2` is a port. It must come from the r1_adc
  reference (VREF/2), not from this block.
- Bias: 10 µA into each OTA (`ib_s1`, `ib_s2`, `ib_c1`, `ib_c2`) from r1_bgr. The testbenches use ideal sources.
- Gain controls `c1..c4` are 3.3 V signals. The decoder from `PGA_GAIN` and the 1.2 V → 3.3 V level shifters are
  not in this block (open issue 6).

Ports of `r1_afe` (`schematic/r1_afe.spice`): `sinp sinn cosp cosn` (pads), `souts_p souts_n soutc_p soutc_n`
(to the T/H), `vcm2` (0.6 V), `ib_s1 ib_s2 ib_c1 ib_c2` (10 µA each, sunk), `c1 c2 c3 c4`, `vdd` (VDDA), `vss`.
Connect the AFE input to the `pad` terminal of `sg13g2_IOPadAnalog`, not to `padres`. The 587 Ω secondary
resistor would add to the 5 kΩ input units without a matching feedback part.

## Status (gate V1 items and block checks, revision B)

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

## Numbers (simulated, revision B, run suffix `20261020b`)

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

## Area and current

| Item | Value | Basis |
| --- | --- | --- |
| Area, both channels with VCM1 divider | ≈ 0.084 mm² (MOS 0.025, rppd 0.032, MIM 0.027) | **estimated**: drawn device area from the netlist × overhead (MOS ×4, rppd ×2, MIM ×1.3), `sim/area_estimate.py` → `sim/results/area_estimate_revB.json`. No layout. Budget in S3: 0.06–0.08 mm² |
| Revision A area (w = 2 µm resistors) | ≈ 0.123 mm² | same script on `schematic/r1_afe_revA.spice` |
| VDDA current, both channels | 1.53–1.79 mA (tt 1.59–1.71, ss 1.53–1.66, ff 1.75–1.79), depends on gain step and input CM | simulated, operating points in `r1afe-ac-20261020b` |
| Power | 5.0–6.4 mW (S3 estimate for the AFE: ≈ 4.3 mW, uncertain) | simulated current × VDDA |

## Open issues

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

## Files

| Path | Content |
| --- | --- |
| `schematic/r1_afe.spice` | revision B source: OTA1 (`r1_afe_ota`), OTA2 (`r1_afe_ota2`), TG, inverter, resistor units, stage sides, channel, top |
| `schematic/r1_afe_revA.spice` | revision A source (runs `r1afe-*-20261020a`) |
| `sim/common_head.inc`, `sim/gain_codes.inc` | model/corner header and gain-code table, inserted into every deck |
| `sim/tb_afe_ac.cir` | (a) gain, −3 dB, phase, peaking at every step, both channels; with `NMC > 1` the mismatch loop |
| `sim/tb_afe_tran.cir` | (b) 100 kHz full-scale sine, THD (fourier), swing, CM ripple |
| `sim/tb_afe_noise.cir` | (c) noise at every step (×1, ×32 required), spectra to the bulk directory |
| `sim/tb_afe_cm.cir` | (d) input CM 0–3.3 V with the stock analog pad on all four pins |
| `sim/tb_afe_psrr.cir` | (e) PSRR from VDDA at 20 kHz and 1 MHz |
| `sim/tb_afe_settle.cir`, `sim/tb_afe_settle_adc.cir` | 2 MSPS track-and-hold load: generic model and r1_adc-matched model |
| `sim/run_afe.py` | driver: campaigns, deck rendering, parallel ngspice, `results/<run-id>.json`, `runs/<run-id>/run.json` |
| `sim/run_all.sh` | the campaign set used for `20261020a` and `20261020b` |
| `sim/report_afe.py`, `sim/summarize.py` | reduction to the numbers above; fills question/result/disposition in `run.json` |
| `sim/area_estimate.py` | area estimate |
| `sim/results/summary-20261020b.json` | all reduced numbers of revision B (revision A: `summary-20261020a.json`) |
| `sim/runs/*/run.json` | one record per run. `dev-*` runs are development iterations on earlier netlists, labelled superseded |
| `sim/dev/` | three early hand decks (smoke, CM check, device currents) used before the driver existed |

`sim/run_afe.py`, `sim/report_afe.py` and `sim/run_all.sh` were edited after the `20261020b` runs to remove a machine
path (usage text and an environment default only). The sha256 in each `run.json` refers to the version that ran.

Raw decks, logs, waveforms and noise spectra: `$G1_RESULTS_ROOT/r1_afe/<run-id>/` (bulk storage, not in git).

Reproduce (repository root):

```
G1_RESULTS_ROOT=<bulk results root>; export G1_RESULTS_ROOT
sh designs/r1-joint/blocks/r1_afe/sim/run_all.sh <suffix>
cd designs/r1-joint/blocks/r1_afe/sim && python3 report_afe.py <suffix>
```

`run_all.sh` sets `G1_CPUSET=106-108 G1_CPUS=3 G1_WORKDIR=designs/r1-joint/blocks/r1_afe/sim`, requires the bulk
`G1_RESULTS_ROOT`, then calls `flow/run.sh python3 run_afe.py <campaign> r1afe-<campaign>-<suffix>`.

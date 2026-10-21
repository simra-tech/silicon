# r1_isense — two low-side shunt sense channels (3.3 V / 1.2 V, auto-zero)

State (2026-10-21; follow-ups 2026-10-20 and the `stb` suite of 2026-10-21): **schematic level, simulated.** No layout, no extraction. All numbers below are
**simulated** (ngspice-46, pinned PDK), at schematic level, with ideal reference sources (marked in each
deck). Nothing is measured.

## What it is

Each channel is a resistive difference amplifier around a fully differential two-stage OTA, with an
input-referred pedestal and an auto-zero (AZ) loop.

```
OUTP - OUTN = G * ((ISP - ISN) - VPED)        G = RF/RIN = 14,  VPED = VREF/26 = 40.38 mV at VREF = 1.05 V
-20 mV .. +100 mV  ->  -0.845 V .. +0.836 V differential, output common mode about 0.57 V (VCM input 0.6 V)
```

- Input: differential Kelvin pins ISx_P/ISx_N through RIN = 4 kΩ (`rppd` unit w = 2 µm, l = 30.8 µm). RF = 14 units,
  pedestal arms RP = 26 units. All three are made of one unit, so G and VPED/VREF are unit ratios.
- Stage 1 (VDDA 3.3 V): thick-oxide PMOS input pair (w 40 / l 1 µm, 20 µA each, bulk = tail) that works with an input
  common mode near 0 V; folded cascode; CMFB on 2/3 of the variable part of the folding sinks.
- Stage 2 (VDD 1.2 V core): thick-oxide NMOS common source, thin-oxide PMOS current-source load, Miller CC 0.22 pF
  with a nulling resistor. **OUTP/OUTN cannot rise above VDD (≤ 1.32 V).** The outputs are therefore safe for the
  thin-oxide ADC multiplexer and comparator inputs, also in overload (G1 lesson: G1 spec §4 "Absolute maximum shunt
  voltage", where a 3.3 V output drove a thin-oxide comparator input to 1.644 V).
- Auto-zero of the whole channel. AZ runs only while the shunt carries no current (low-side FET off, outside dead
  time). During AZ (`az`): the output ends of both RF arms move from the outputs to VCM, and both pedestal arms open.
  During `azh` (inside `az`): two 1 pF hold caps follow the stage-1 outputs, and an auxiliary PMOS pair
  (gm ≈ gm1/12) nulls the stage-1 output. The stored correction cancels the OTA offset **and** the resistor-network
  error at Vod = 0 (0.6 V output common mode through mismatched RF/RIN ratios, about 150 µV σ). An OTA-only AZ left
  ±200 µV (development run `dev-mc-01`, failed).
- AZ phases `az_lv`, `azh_lv` are 1.2 V logic from r1_ctrl, level-shifted in the block. Sequence: `azh` falls at
  least one clock cycle (33 ns) before `az`. The output is invalid during AZ and for the recovery time after it.
  r1_safe must blank over that window.

Interface assumptions (to confirm with r1_adc and r1_bgr):

| Item | Assumption in this step |
| --- | --- |
| ADC input | differential, 1.2 V domain, 2.4 Vpp FS; this block uses ±0.845 V (70 % of FS) so that both outputs stay in 0.15–1.02 V at VDD = 1.08 V |
| ADC load | 2 pF per output (T/H sampling cap through the multiplexer) |
| VCM | 0.6 V from the r1_adc reference (ideal source here); it sinks or sources ≈ 10 µA per RF arm during AZ |
| VREF | 1.05 V, **buffered** (ideal source here); load 2 × 4 µA per channel (pedestal arms) |
| IBIAS | 5 µA PTAT (5 µA × T/300 K) per channel from the r1_bgr PTAT branch (ideal source here) |
| AZ window | ≥ 2.05 µs AZ per PWM period while the low-side FET is off, ≥ 100 ns before the sample strobe |

Why G = 14 and not 20 ("100 mV → about 2.0 Vpp"): at VDD = 1.08 V the thin-oxide load needs ≈ 60 mV of headroom,
and the output common mode is 0.57 V. A gain of 14 keeps the full −20…+100 mV range linear at ss/125 °C/1.08 V.
At G = 14 with a 40 mV pedestal, the 120 mV range maps to 1.68 Vpp (0.5 bit of ADC range unused).

## Status

| Check | Status | Evidence |
| --- | --- | --- |
| Settling to ±0.5 % within 300 ns after 0→100 mV, −20→100 mV, 100→0 and 100→−20 mV edges, 2 pF load, tt/ss/ff/ss_cold/ff_hot | **passed**: worst 206 ns (ss 125 °C, 1.08/3.0 V) | `sim/results/isense-step-20261020-r1/` |
| Closed-loop bandwidth ≥ 1 MHz, 5 corners | **passed**: 9.1–15.2 MHz, no peaking | `sim/results/isense-noise-20261020-r1/` |
| Residual offset after AZ ≤ 100 µV, 50-sample mismatch MC (`mm_ok=1`), tt 27 °C | **passed**: 50/50, σ 16.2 µV, worst 35.5 µV (raw before AZ σ 2.57 mV) | `sim/results/isense-mc-20261020-r1/` |
| Gain, pedestal, INL over −20…+100 mV after AZ, 5 corners | **passed** (report): G 13.9999–14.0076, INL ≤ 0.023 % of span, pedestal 40.307–40.342 mV | `sim/results/isense-dc-20261020-r1/` |
| Same at Kelvin common mode −0.1 V and +0.1 V (tt) | **passed** (report): pedestal moves ≤ 1.2 µV | `isense-dc-cmm100-…`, `isense-dc-cmp100-…` |
| Negative excursion: −20 mV linear; −200 mV and +200 mV for 300 ns, recovery to ±0.5 % | **passed** (report): in range linear; recovery 132–184 ns | `isense-step-20261020-r1` |
| Output nodes ≤ VDD in all runs, including overload | **passed**: max 1.310 V at VDD 1.32 V (ff_hot) | `isense-step-20261020-r1` |
| Noise (continuous time, AZ held), 5 corners | run (report): 25–37 nV/√Hz white, 1/f corner ≈ 70 kHz, 53–80 µV rms in 10 kHz–5 MHz | `isense-noise-20261020-r1` |
| Residual offset after AZ ≤ 100 µV, mismatch MC at ss 125 °C (30 samples, seed 4) and ff −40 °C (30 samples, seed 5) | **passed**: ss 30/30, σ 15.6 µV, worst 42.7 µV (raw σ 3.14 mV); ff 30/30, σ 23.3 µV, worst 48.2 µV (raw σ 2.46 mV) | `sim/results/isense-mc-ssff-20261020-r1/` |
| MC of the CM-to-differential error after AZ | **not run** | — |
| AZ hold droop over one 50 µs PWM period at zero current (gmin 1e-15), tt / ss 125 °C / ff_hot 125 °C, and ss / ff at 150 °C | **passed** (limit 50 µV input-referred): output drift ≤ 0.004 µV input-referred; hold-node droop ≤ 1.75 µV (125 °C), ≤ 11.4 µV (150 °C), common to both caps; mismatch bound (one cap droops, the other not, /12 aux gm ratio) ≤ 0.15 µV (125 °C), ≤ 0.95 µV (150 °C) | `sim/results/isense-droop-20261020-r1/`, `sim/results/isense-droop-150C-20261020-r1/` |
| AZ with noise folding (sampled noise) | **not run** (estimate: hold-cap kT/C 64 µV per node → ≈ 7 µV input-referred) | — |
| Auto-zero loop gain (return ratio during AZ hold, loop broken at the aux-pair gates), 5 corners | **passed** (limit 45°): differential phase margin 92.8–96.5°, unity gain 0.74–1.14 MHz, DC loop gain 47.9–56.9 dB, gain margin 29.6–33.4 dB; common mode: loop gain ≤ −47 dB at all frequencies (the aux pair rejects CM; no CM AZ loop) | `sim/results/isense-azloop-20261020-r1/` |
| Loop gain (Tian double injection, as r1_afe) of the main differential loop, normal state (az = azh = 0), break at the OTA outputs, shunt 0 / +100 / −20 mV, tt, ss 125 °C 3.0 V, ff −40 °C 3.6 V, sf, fs; load = joint path fixture of r1_safe (2 pF per output, OC and NEG comparators of the channel) | **passed** (PM ≥ 60°, GM ≥ 10 dB): worst PM / GM per corner tt 74.8° / 18.7 dB, ss 79.0° / 21.4 dB, ff 72.2° / 17.3 dB, sf 74.7° / 18.6 dB, fs 75.0° / 18.8 dB (worst at 0 mV); unity gain 2.2–9.6 MHz | `sim/results/isense-stb-20261021-r1/` |
| Same loop, cross-check with the break at the input-pair gates | **passed**: PM and GM equal the output break within 0.05° / 0.2 dB, all 5 corners | same |
| Common-mode / CMFB loop, normal state (output break, symmetric injection: CMFB path plus the CM path through the input pair and the network), same corners, levels and load | **failed** (PM ≥ 60° not met in any corner; GM ≥ 10 dB not met at ff): worst PM / GM tt 41.5° / 11.3 dB, ss 49.5° / 13.8 dB, ff 35.5° / 9.7 dB, sf 41.3° / 11.2 dB, fs 41.7° / 11.4 dB (worst at 0 mV; at +100 / −20 mV tt 51.6° / 52.3°, ss 66.3° / 66.9°); unity gain 6.5–20.5 MHz | same |
| CMFB path alone (break at the sense node, other loops closed) | informational (not a valid Nyquist break when the input-pair CM loop is also > 1): equals the CM loop above within 0.1° | same |
| Input-pair CM path (symmetric injection at the input gates) | **not applicable**: loop gain ≤ −49 dB at all frequencies (the CM loop is the CMFB) | same |
| CM-step cross-check (VCM reference +20 mV after AZ, output common-mode overshoot) | informational, agrees with the loop-gain ranking: overshoot tt 36 %, ss 25 %, ff 44 %, sf 37 %, fs 36 % (2nd-order equivalent PM 34–44°) | `sim/results/isense-stbcm-20261021-r1/` |
| Loop gain with the auto-zero closed (az = azh = 1): AZ servo (break at the aux-pair gates), 5 corners | **passed**: PM 92.6–96.5° (tt 95.1, ss 92.6, ff 96.5, sf 95.1, fs 95.0), GM 30.2–33.5 dB, unity gain 0.83–0.94 MHz (the AZ loop result of 2026-10-20 reproduced with the new method within 0.4° at tt, ss, ff) | `sim/results/isense-stbaz-20261021-r1/` |
| Loop gain with the auto-zero closed: CM / CMFB loop (outputs free, RF arms at VCM) | **failed**: PM 21.4–41.5° (tt 29.7, ss 41.5, ff 21.4, sf 29.7, fs 29.7), GM 8.6–19.9 dB (ff 8.6 dB fails GM); unity gain 10.7–15.1 MHz | same |
| Loop gain with the auto-zero closed: differential output break; CM path of the aux pair | **not applicable**: loop gain ≤ −142 dB (no external differential loop while the RF arms are at VCM); aux-pair CM ≤ −44 dB | same |
| Load sensitivity: ADC load 100 Ω + 2.8 pF + 0.2 pF wiring per output (INTERFACES.md CDAC), normal state, tt and ss | run: DM loop PM 72.5° / 77.3°, CM loop 37.2° / 45.8° (tt / ss; 4° lower than with 2 pF) | `sim/results/isense-stb-load28-20261021-r1/` |
| Comparator-state sensitivity: both comparators at the calibration point (code 14 / 49), tt and ss | run: PM within 0.3° of the code-44 runs | `sim/results/isense-stb-c14-20261021-r1/` |
| Loop gain in the intermediate state az = 1, azh = 0 (hold open, outputs free); mismatch spread of the loop gain; channel b and the second comparator pair in the fixture | **not run** (the CMFB loop of the AZ-closed state is the same loop without the AZ servo) | — |
| Step 0 → 100 mV shunt, 10 ns edge, after AZ, joint load fixture, tt and ss 125 °C | **passed**: settling to ±0.5 % in 102 ns (tt) and 205 ns (ss) from the edge start, no overshoot (peak 0.000 %), 0 overshoots (limit 1) | `sim/results/isense-stbstep-20261021-r1/` |
| Supply rejection (report) | run: VDDA→Vod −72…−85 dB, VDD→Vod ≤ −83 dB at 1 MHz (nominal, no mismatch) | `isense-noise-20261020-r1` |
| Real VREF/VCM/IBIAS sources, level-shifter timing, pads (`dantenna`) | **not run** (ideal sources; pad diodes left out at block level per the ngspice pad-diode note) | — |
| Layout, DRC, LVS, PEX | **not run** | — |

## Numbers (simulated, schematic level)

| Quantity | tt 27 °C | ss 125 °C | ff −40 °C | ss −40 °C | ff 125 °C |
| --- | --- | --- | --- | --- | --- |
| Supplies VDDA / VDD (V) | 3.3 / 1.2 | 3.0 / 1.08 | 3.6 / 1.32 | 3.0 / 1.08 | 3.6 / 1.32 |
| Settling 0→100 mV, ±0.5 % (ns) | 98 | 203 | 65 | 105 | 119 |
| Settling, worst 100/120 mV edge (ns) | 99 | 206 | 66 | 106 | 123 |
| Settling 0→−20 mV (small step, ns) | 121 | 286 | 75 | 126 | 162 |
| −3 dB bandwidth (MHz) | 12.0 | 9.1 | 15.2 | 10.4 | 12.6 |
| Gain (LSQ fit) | 14.008 | 14.007 | 14.005 | 14.007 | 14.000 |
| Pedestal error vs VREF/26 (µV) | −54 | −74 | −44 | −43 | −78 |
| INL (% of the −20…100 mV output span) | 0.004 | 0.021 | 0.002 | 0.002 | 0.023 |
| Output common mode (V) | 0.570 | 0.582 | 0.565 | 0.559 | 0.588 |
| Input noise at 1 MHz (nV/√Hz) | 30 | 37 | 25 | 27 | 36 |
| Input noise 10 kHz–5 MHz (µV rms) | 65 | 80 | 53 | 57 | 76 |
| IDDA (3.3 V) / IDD (1.2 V) per channel (µA) | 170 / 407 | 213 / 502 | 143 / 340 | 131 / 292 | 225 / 569 |

Mismatch MC (50 samples, tt): raw offset before AZ σ 2.57 mV (−5.66…+8.51 mV); residual after AZ mean −0.4 µV,
σ 16.2 µV, range −34.0…+35.5 µV; pedestal 40.32 mV σ 0.10 mV; gain 14.012 σ 0.028.
At ss 125 °C (30 samples): raw σ 3.14 mV (worst 7.56 mV), residual σ 15.6 µV (worst 42.7 µV), pedestal σ 0.11 mV,
gain σ 0.032. At ff −40 °C (30 samples): raw σ 2.46 mV (worst 4.96 mV), residual σ 23.3 µV (worst 48.2 µV),
pedestal σ 0.10 mV, gain σ 0.030.

Auto-zero loop (return ratio during AZ hold): differential DC loop gain 56.4 dB (tt), 54.6 (ss), 55.5 (ff), 56.9
(ss_cold), 47.9 (ff_hot); unity gain 0.87 / 0.96 / 0.89 / 0.74 / 1.14 MHz; phase margin 95.3 / 92.8 / 96.5 / 95.4 / 94.1°.
The closed AZ loop time constant is about 1/(2π · 0.74 MHz) ≈ 0.22 µs, so the 2.0 µs `azh` phase is ≥ 9 time constants.

The pedestal error (−43…−78 µV systematic, 0.10 mV σ under mismatch) is not an offset of the amplifier: AZ
removes everything except the pedestal itself, and the ADC reads the pedestal at zero current. A host or r1_ctrl
zero-current reading per part therefore removes it. Its drift between AZ cycles is the resistor-ratio drift only.

Power per channel (tt): 0.56 mW from VDDA + 0.49 mW from VDD ≈ 1.05 mW (G1 sense: 3.6 mW).

## Area (device area, from `schematic/area.py`)

| Item | µm² per channel |
| --- | --- |
| `rppd` (2 + 28 + 52 units of 62 µm²) | 5058 |
| MIM (2 × 1 pF hold, 2 × 0.22 pF CC, 2 × 64 µm² CM bypass) | 1768 |
| thick-oxide MOS | 1156 |
| `rhigh` CM sense | 300 |
| thin-oxide MOS | 21 |
| **Total** | **8304 (0.0083 mm²)** |

With an analog layout factor of 3–4, the estimate is 0.025–0.033 mm² per channel (target ≈ 0.04 mm²; G1 cell
0.092 mm²). The estimate is not a layout.

## Open issues

1. **Noise.** 30 nV/√Hz white (tt) gives about 1.5 ADC LSB rms (input-referred LSB 42 µV) over 5 MHz. Options:
   more input-pair current, longer folding sinks, digital averaging of two samples. No noise target is specified;
   r1_adc and the system budget must set one.
2. **Output common mode** is 0.56–0.59 V, not 0.60 V (CMFB pair offset). This costs 10–40 mV of bottom headroom.
3. **AZ dependency on the gate timing.** AZ is valid only while the shunt current is zero. r1_gate/r1_ctrl must give
   an AZ window inside the high-side on-time, outside dead time, and r1_safe must blank the comparators over AZ +
   ≈ 100–200 ns. At duty cycles with no such window (low-side on ≈ 100 %), the hold caps must keep the correction.
   Droop (simulated, model leakage only): worst-case mismatch bound ≤ 0.95 µV input-referred per 50 µs at 150 °C,
   so about 100 periods (5 ms) without AZ stay within a 100 µV budget at 150 °C (estimate from the bound).
   r1_safe revision 3 also uses the zero-current window after AZ for its calibration search (r1_safe README).
4. **Kelvin common-mode change between AZ and sampling** converts through RF/RIN mismatch (estimate: σ ≈ 3.7 µV per mV
   of CM change). Board rule proposal: tie chip VSS close to the shunt ground side.
5. **Ideal sources.** VREF must be buffered (pedestal arms are 104 kΩ). VCM must sink/source the RF-arm current during
   AZ. IBIAS is assumed PTAT.
6. **CMFB loop margin (failed, 2026-10-21).** A CMFB share of 8/3 of the folding current oscillated at 46 MHz
   (development run `dev-step-11`); the share of 2/3 is stable in all corners, but the loop-gain run shows a phase
   margin of 35–50° in normal mode and 21–42° with the auto-zero closed (criterion 60°, GM 10 dB), with a crossover
   (6.5–20 MHz) above the differential crossover. A CM-step transient confirms the ringing (overshoot 25–44 %). The
   netlist of record is unchanged. Candidates (not simulated): smaller CMFB pair or tail current (lower CM gain), more
   CM-sense bypass, or a CM-only Miller part as in r1_afe revision D. The differential loop and the AZ servo pass.
7. **r1_safe drive.** The sense outputs drive the four r1_safe comparator gates directly (thick PMOS, no DC load).
   The joint deck `r1_safe/sim/tb_safe_joint3.cir` checks thresholds and delay through the real sense output.

## Built against

| Item | Version | How established |
| --- | --- | --- |
| PDK | IHP-Open-PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` | checked by `flow/run.sh` before every run |
| ngspice | ngspice-46 (OSDI PSP 103, `r3_cmc`) | `flow/run.sh ngspice -v` banner, 2026-10-20; `sim/.spiceinit` loads the OSDI models |
| Container | `tapeoutbench-eda:latest`, id `sha256:ddeb6957…` | checked by `flow/run.sh` |
| xschem / KLayout / LibreLane / CACE | not used in this step | — |

## Files and reproduction

- `schematic/r1_isense.spice.tmpl` + `schematic/gen_isense.py` → `schematic/r1_isense.spice` (generated; sha256
  prefix `5db34e0a8f7c` for all evidence runs). `schematic/area.py` gives the device area.
- Decks: `sim/tb_isense_step.cir`, `sim/tb_isense_dc.cir`, `sim/tb_isense_mc.cir`, `sim/tb_isense_noise.cir`,
  `sim/tb_isense_droop.cir`, `sim/tb_isense_azloop.cir` (from `sim/gen_tb_isense_azloop.py`: a deck-local copy of
  `r1_isense_ch` with the AZ loop broken at the aux-pair gates);
  analyzers `sim/analyze_*.py`; runner `sim/run_deck.py` (corner substitution, `flow/run.sh`, `run.json`).
- Campaign: `sh designs/r1-joint/blocks/r1_isense/sim/campaign_20261020.sh` from the repository root
  (CPU set 109–111); follow-ups (ss/ff MC, AZ loop gain, droop): `sim/campaign_20261020_fu.sh`. A `TEMP` override
  (150 °C droop run) is recorded in `run.json` under `overrides`. Raw waveforms: `<G1_RESULTS_ROOT>/r1_isense/<run-id>/`.
- `sim/results/<run-id>/run.json` and `summary.json` per run. Runs named `dev-*` are development runs on earlier
  netlist states (their `run.json` holds the netlist hash). They are kept as a record, not as evidence; `dev-mc-01`
  to `dev-mc-03` (OTA-only AZ, failed) and `dev-step-06`/`dev-step-11` (CM loop unstable) are the failed designs.

## `stb` suite (2026-10-21, T4 follow-up c)

Decks are generated by `sim/gen_tb_isense_stb.py` from the netlist of record (deck-local copy `r1_isense_ch_stb` with
probe sources; the record is included unchanged): `tb_isense_stbpre.cir` (auto-zero on the channel alone, prints the
hold-cap voltages `HOLDVALS`), `tb_isense_stb.cir` (normal state; the hold caps are tied at DC to the post-AZ voltages by
1 GH, open for AC), `tb_isense_stbaz.cir` (AZ closed), `tb_isense_stbc14.cir` (comparators at the calibration point),
`tb_isense_stbstep.cir`, `tb_isense_stbcm.cir`. Analyzers `sim/analyze_stb.py`, `analyze_stbstep.py`, `analyze_stbcm.py`.
Runner: `sim/run_deck.py` with the new `--pre` option (pre-run deck, fills `@@VH1@@`/`@@VH2@@`), the corners `sf`, `fs`, and
`included_netlists` (sha256 of every `.include`d netlist) in `run.json`. Campaign: `sim/campaign_20261021_stb.sh`
(CPU set 109–110; the CM-step run was started by hand, command in its `run.json`). Netlists of record in every `stb`
`run.json`: r1_isense sha256 `5db34e0a8f7c…` and r1_safe `812f886dce2b…` (both match the records). Raw files:
`<G1_RESULTS_ROOT>/r1_isense/<run-id>/`. `dev-stb-01` is the first development run (kept, not evidence).
Criterion: PM ≥ 60° and GM ≥ 10 dB per loop, corner and shunt level (worst reported). Corners: tt 27 °C 3.3 V / 1.2 V,
ss 125 °C 3.0 V / 1.08 V, ff −40 °C 3.6 V / 1.32 V, sf and fs 27 °C at the tt supplies.

### Failures and mistakes (stb suite)

| # | What happened | Class | Evidence |
| --- | --- | --- | --- |
| 1 | The earlier statement "CMFB share 2/3 is stable in all corners" rested on transients only. The loop-gain run shows 35–50° (normal) and 21–42° (AZ closed). The 60° criterion fails for the CM loop; the netlist of record stays unchanged. | verification-gap | `isense-stb-20261021-r1`, `isense-stbaz-20261021-r1`, `isense-stbcm-20261021-r1` |
| 2 | The brief listed a CMFB, a main loop and an AZ loop, and the AZ loop was measured before (45° limit) with a 1 GH / 1 F break. Re-measured here with the Tian method at the stricter 60° limit; both agree within 0.4°. | planning | `isense-azloop-20261020-r1`, `isense-stbaz-20261021-r1` |
| 3 | First idea for the normal-state operating point was to tie each hold node to its stage-1 output by 1 GH. That closes the AZ servo at DC and removes the pedestal (output ≈ 0 V instead of −0.565 V). Found before the first run; replaced by a pre-run that supplies the post-AZ hold voltages. | numerical | `sim/tb_isense_stbpre.cir` |
| 4 | The generator's own assertion for the CM-step deck contradicted the deck text and aborted after the run directory was created; the rerun stopped with "run id exists" until the empty directory was removed. | tooling | development only |
| 5 | `r1_isense` and `r1_safe` each carry a private copy of `run_deck.py` (they differ in the `NET` handling only). The `stb` additions were applied to both by hand. Drift risk; a shared runner is the cleaner fix. | process-hygiene | `sim/run_deck.py` in both blocks |
| 6 | Not covered: the intermediate state az = 1, azh = 0, a mismatch spread of the loop gain, channel b. | verification-gap | status table |

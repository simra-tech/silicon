# R1_ADC — 12-bit SAR ADC with two simultaneous track-and-holds (schematic level, step 1)

State on 2026-10-20: **schematic written and simulated at schematic level only.** No layout, no PEX, nothing
measured. Every number in this file is **simulated** with ngspice 46 and the PDK models named below, unless it is
marked *estimated* or *derived*. The reference is an **ideal source** in this step. The SAR logic and the timing
generator are **behavioural** (XSPICE digital cells and ideal pulse sources).

## What it is

The ADC of R1 (specification row `r1_adc`, PLAN.md D3, study S1 "ADC choice" and addendum, S4 MIM data):

- 12-bit differential SAR in the 1.2 V domain. Full scale ±VREF·C_T/(C_T + C_par) ≈ ±1.163 V differential
  with VREF = 1.2 V (2.33 Vpp differential, input common mode 0.6 V).
- One conversion frame of 1 µs at the 30 MHz `r1_osc` clock holds 30 cycles: slice A converts in cycles 0–11,
  slice B in cycles 12–23, both slices track in cycles 24–29. This is 2 MSPS (two conversions per µs) and
  1 MSPS per channel.
- **Two track-and-holds sampled on one edge.** Each track-and-hold is a top-plate-sampled CDAC (slice A, slice B).
  The falling edge of `trk_enc` opens the sampling switches of both slices together. Slice B holds its sample
  for 0.4 µs while slice A converts.
- **Input multiplexer, 4 differential inputs on 2 slices.** Slice A samples `SIN` (encoder mode) or `ISA`
  (current mode); slice B samples `COS` or `ISB`. Each input has its own bootstrapped switch pair, so the
  multiplexer adds no series switch. `trk_enc` samples SIN and COS together, `trk_cur` samples ISA and ISB
  together. Between encoder frames the controller can insert current frames (PLAN.md D3).
- **One SAR logic block** for both slices; **one dynamic comparator per slice** (the comparator is small; a
  shared comparator would need a multiplexer on the high-impedance top plates). This is an interpretation of
  D3 "one SAR, two track-and-holds": the expensive parts that D3 removes (a second reference buffer, a second
  logic block, a second calibration set) stay single; the CDAC is the track-and-hold and is therefore doubled.
- **Split 6+6 bridge MIM CDAC**, unit `cap_cmim` 3.78 × 3.78 µm = 22.04 fF (S4). MSB array on the top node:
  16, 8, 4, 2, 1 Cu (weights 1024 … 64 LSB). Bridge Cb = 1 Cu. LSB array on the LSB node: 32, 16, 8, 4, 2, 1 Cu
  (63 Cu, no dummy, so Cb/(63 Cu + Cb) = 1/64 exactly). 95 units per side, 2.09 pF per side, top-node
  capacitance ≈ 0.70 pF.
- **Monotonic switching** (Liu 2010, AnalogAcademy module 3). Bottom plates sit at VREF during sampling. After
  each decision, the capacitor of the higher side steps VREF → GND. The LSB nodes reset to VREF in track so that
  they stay inside 0 … 1.2 V.
- **Bootstrapped NMOS sampling switches** (Abo-Gray type, 11 devices, 200 fF boost capacitor, every device
  sees ≤ VDD between any two terminals).
- **Dynamic comparator:** double-tail, PMOS input pair 16/0.2 µm (4 fingers) so that the input common mode can
  fall from 0.6 V to ≈ 0 V during monotonic switching.
- **SAR logic:** XSPICE `d_dff` register with one P flag and one N flag per decision (scheme of the AnalogAcademy
  `sar_logic.v`), comparator clock gating `mclk AND win`, output latch. Timing from ideal sources
  (`sim/r1_adc_timing.inc`, stand-in for `r1_ctrl`).

### Block diagram

```
                   trk_enc  trk_cur                      mclk winA winB rst lat stb0..23   (r1_ctrl; ideal here)
                      |        |                                    |
 SIN_P/N --[BSW]--+   |        |                         +----------v-----------------------------+
                  +--> top_A (P,N) ---------> r1_cmp A --> | r1_sar_logic (XSPICE)                 |
 ISA_P/N --[BSW]--+    CDAC A (6+6 bridge) <-- drivers <-- |  P/N flags A (23 DFF) + latch (12)    |--> codeA[11:0]
                          ^ lsb reset to VREF               |  P/N flags B (23 DFF) + latch (12)    |--> codeB[11:0]
 COS_P/N --[BSW]--+       |                                 |  clkA = mclk & winA, clkB = mclk & winB|
                  +--> top_B (P,N) ---------> r1_cmp B --> |                                       |
 ISB_P/N --[BSW]--+    CDAC B (6+6 bridge) <-- drivers <-- +---------------------------------------+
                                                 ^
                                  VREF (ideal source in this step; reference buffer not designed)
 BSW = bootstrapped switch pair; drivers = 22 bottom-plate inverters per slice between VREF and GND
```

## Files

| Path | Content |
| --- | --- |
| `schematic/gen_r1_adc.py` | Generator; all device sizes are here. Writes the two SPICE libraries below. |
| `schematic/r1_adc.spice` | SPICE source as simulated: `r1_bootsw`, `r1_offsw`, `r1_drv`, `r1_drv_sw`, `r1_cdac_side`, `r1_cdac_side_mc`, `r1_cmp`, `r1_th`, `r1_th_fast`, `r1_sar_logic`, `r1_adc_core`, `r1_adc_core_fast`, `r1_adc_core_fast_a`. |
| `schematic/r1_adc_mm.spice` | Same, every MOS instance with `mm_ok={mmos}` for MOS-mismatch decks. |
| `sim/gen_timing.py`, `sim/r1_adc_timing.inc` | Ideal timing sources (30 MHz, 1 µs frame). |
| `sim/tb_quick.cir` | Functional smoke test, 8 held inputs, both slices. |
| `sim/tb_adc_static.cir` | (a) slow differential ramp, histogram DNL and code-transition INL (campaign deck). |
| `sim/tb_adc_static_v2.cir` | Same with tstep 1 ns and binary code output (open issue 9); not used in the campaign. |
| `sim/tb_adc_dyn.cir` | (b) sine on SIN, cosine on COS, full rate, coherent FFT. |
| `sim/gen_tb_th_skew.py`, `sim/tb_th_skew_nominal.cir`, `sim/tb_th_skew_mc20.cir` | (c) sampling skew between the two track-and-holds (nominal and MOS-mismatch MC). |
| `sim/gen_tb_cdac_mc.py`, `sim/tb_cdac_mc.cir` | (d) CDAC MIM-mismatch MC, 50 samples, `cap_typ_mismatch`, `mm_ok=1`. |
| `sim/run_ngspice.py` | Runs one deck through `flow/run.sh`, writes `sim/runs/<run-id>/run.json`. |
| `sim/run_static.sh`, `sim/run_windows.sh`, `sim/run_resume.py` | Static ramp in parallel segments; corner windows; restart after a numerical abort. |
| `sim/post_adc.py`, `sim/post_windows.py`, `sim/post_cdac_mc.py`, `sim/post_skew.py`, `sim/post_vref_load.py`, `sim/rawread.py` | Post-processors (Python 3.6, numpy). |
| `sim/results/` | JSON summaries and small text tables (DNL/INL per code, spectra). |
| `sim/runs/<run-id>/` | `run.json`, expanded deck, ngspice log (cut to 400 lines when long). |
| `third_party/README.md` | AnalogAcademy commit and what was used from it (the clone itself is gitignored). |

Raw waveforms and code files are in the bulk results root under `r1_adc/<run-id>/` (`run.json` field
`raw_results`).

How to run (from the repository root, CPU set of track T2):

```
G1_RESULTS_ROOT=<bulk results root>; export G1_RESULTS_ROOT
python3 designs/r1-joint/blocks/r1_adc/schematic/gen_r1_adc.py
cd designs/r1-joint/blocks/r1_adc
python3 sim/run_ngspice.py --deck sim/tb_quick.cir --run-id <new id> --cpuset 103
sim/run_static.sh <tag> mos_tt 27 1.2 142e-6 2940 103 104 105
```

## Built against

| Item | Value | How established |
| --- | --- | --- |
| PDK | IHP SG13G2 open PDK commit `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` | `flow/run.sh` checks `/foss/pdks/ihp-sg13g2/COMMIT` before every run |
| Container image | `sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2` (`tapeoutbench-eda:latest`) | `flow/run.sh` identity check |
| ngspice | ngspice-46, KLU, XSPICE `digital.cm`, PSP 103.6 OSDI | banner in every `sim/runs/*/ngspice.log`; `.spiceinit` in the block root |
| Models | `cornerMOSlv.lib` `mos_tt` / `mos_ss` / `mos_ff` / `mos_tt_mismatch`; `cornerCAP.lib` `cap_typ` / `cap_typ_mismatch` | deck headers in `sim/runs/*/deck.cir` |
| xschem, KLayout, LibreLane, CACE | not used in this step | — |
| Reference design | IHP-AnalogAcademy commit `133ecf65…` (Apache-2.0) | `third_party/README.md` |

## Status

All results are from the schematic-level decks on 2026-10-20 (tt = `mos_tt`, `cap_typ`, 27 °C, VDD = VREF = 1.2 V
unless stated). "Fast core" means the conversion decks use `r1_th_fast`: the deselected input pair is reduced to the
main switch device, and the bottom-plate drivers are ideal 400 Ω conductances (`r1_drv_sw`). The static decks use
slice A only (`r1_adc_core_fast_a`). With ideal supplies and an ideal reference, slice B does not act on slice A.

| Check | Status | Number (simulated unless marked) | Evidence |
| --- | --- | --- | --- |
| Functional smoke test, 8 held inputs, both slices | passed | codes symmetric (A: +0.3 V → 2576, B: −0.3 V → 1519); full scale ±1.163 V differential (top-plate parasitic ≈ 3 %) | `sim/runs/quick-tt-01/` |
| Solver options against reltol 1e-4 / tmax 1 ns | passed | 41 codes at 0.1 LSB steps identical for all option sets and both driver models | `sim/runs/acc-window-*` |
| (a) Static ramp, tt, codes 0–2154 (lower half and 106 codes past mid-scale), 4 hits per code | passed | DNL −0.25 … +0.25 LSB (= the 0.25 LSB resolution); INL −0.02 … +0.49 LSB (end-point over codes 1–2153); no missing codes; monotonic; LSB 567.9 µV; mid-scale offset +0.10 mV | `sim/results/static_tt27.json`, `static_tt27_A_dnl_inl.txt`; runs `static-tt27b-s0/s1/s2` and `*-s0r/s1r/s2r-*` |
| (a) Static ramp, tt, upper half (codes 2155–4095) | not run | covered by symmetry at nominal only (code(−vd) = 4095 − code(vd), checked at 8 points in `quick-tt-01`) | — |
| (a) Static, ss / 125 °C, windows ±12 codes at 512, 1024, 1536, 1984, 2048 | passed with remark | DNL −0.49 … +0.28 LSB; codes 1023 and 2047 get 2 of 4 hits (tt: 3 and 4); no missing codes | `sim/results/static_windows_ss125.json` |
| (a) Static, ff / −40 °C, same windows | passed | DNL −0.24 … +0.01 LSB; no missing codes (frame 0 of the 2048 window skipped after a numerical abort) | `sim/results/static_windows_ffm40.json` |
| (a) Full ramp and INL at ss / ff; VDD 1.08 / 1.32 V | not run | budget; VREF = 1.2 V is not possible at VDD = 1.08 V (open issue 2) | — |
| (b) Dynamic, tt, fin 100.59 kHz, −0.48 dBFS, 1024 points per channel, 2 MSPS | passed (no device noise) | slice A (sine): SNDR 72.57 dB, SFDR 79.47 dB, THD −79.32 dB, ENOB 11.76; slice B (cosine): SNDR 72.32 dB, SFDR 78.31 dB, ENOB 11.72 | `sim/results/dyn_tt27_n1024.json`, spectra `dyn_tt27_n1024_*_spectrum.txt`; run `dyn-tt27-n1024` |
| (b) ENOB with thermal noise | not run (estimate only) | *derived*: simulated SNDR + kT/C (107 µV) → ENOB 11.55; with comparator noise 60 / 120 µV → 11.50 / 11.35 | `sim/results/noise_budget_tt.json` |
| (b) Dynamic at corners | not run | — | — |
| (c) Skew A–B, nominal, full `r1_th` slices, ±0.7 V levels, ±20 mV/ns | passed | 0.00 ps for equal inputs; effective sampling instant −103 … −380 ps from the trk edge, level- and slope-dependent (277 ps spread, so sine and cosine at different levels can differ by up to 0.28 ns) | `sim/results/th_skew_nominal_tt.json`; run `skew-nominal-tt-c` |
| (c) Skew A–B, MOS mismatch MC (20 copies, `mos_tt_mismatch`, `mm_ok=1`) | passed | mean +0.65 ps, σ 7.6 ps, max \|skew\| 22.9 ps (target < 0.5 ns) | `sim/results/th_skew_mc20_tt.json`; run `skew-mc20-tt-c` |
| (d) CDAC MIM mismatch MC (50 samples × 2 sides, `cap_typ_mismatch`, `mm_ok=1`) | **failed** (DNL ≤ 0.5 LSB) | max \|DNL\| per sample: median 0.94 LSB, max 1.56; 5/50 samples ≤ 0.5 LSB; 12/50 with missing codes; σ(DNL) 0.66 LSB at codes 1024/3072, 0.59 LSB at 2047/2048; max \|INL\|: median 1.03, max 2.30 LSB | `sim/results/cdac_mc50_tt.json`; run `cdac-mc50-tt-ac` |
| (d) Reproducibility of the draws | passed | rerun gives identical weights (fixed default seed); a second set of 50 draws is not run | run `cdac-mc50-tt-ac-rerun` |
| (d) Unit-size sensitivity | *derived*, not simulated | 88 fF unit: 50 % of samples ≤ 0.5 LSB; 198 fF: 82 %; 353 fF: 96 % | same file, `derived_unit_scaling` |
| Reference load (ideal VREF) | measured in simulation; buffer not designed | 2.1–2.5 pC per frame (2.5 µA average at 2 MSPS); up to 0.42 pC in one 33 ns bit cycle, signal-dependent | `sim/results/vref_load_quick_tt.json` |
| Comparator noise, comparator offset and its common-mode dependence | not run | ngspice has no device noise in transient; *estimated* 120 µV rms | — |
| Current-channel conversion (`trk_cur`, ISA / ISB) | not run | the inputs exist in `r1_th`; conversion decks tie `trk_cur` low | — |
| Conversion with transistor drivers `r1_drv` and full `r1_th` | not run | `r1_drv` / full `r1_th` used only in the skew decks | — |
| xschem sheets, layout, DRC, LVS, PEX | not run | — | — |

Failed and abandoned runs stay in `sim/runs/` with their `run.json` (`static-tt27-*` with the earlier `sw`
driver, `cdac-mc50-tt` transient version, `skew-*-tt` and `skew-*-tt-b` with test-bench errors).

## Numbers

| Item | Value | Class |
| --- | --- | --- |
| Resolution / rate | 12 bit; 2 MSPS (two conversions per 1 µs frame at 30 MHz), 1 MSPS per channel | specified, simulated at 30 MHz |
| Full scale | ±1.163 V differential (2.33 Vpp), input common mode 0.6 V; LSB 567.9 µV | simulated |
| Static, tt | DNL within ±0.25 LSB (resolution), INL ≤ 0.49 LSB, no missing codes | simulated |
| Dynamic, tt, 100.59 kHz | ENOB 11.76 / 11.72, SFDR ≥ 78.3 dB (no device noise) | simulated |
| ENOB with kT/C and comparator noise | 11.35–11.55 | derived |
| Skew A–B | 0 ps nominal; σ 7.6 ps under MOS mismatch; ≤ 0.28 ns level-dependent aperture difference | simulated |
| CDAC mismatch DNL | median max \|DNL\| 0.94 LSB; 24 % of samples with missing codes | simulated |
| Supply current VDD (comparators, bootstrap, track buffers) | 3.8 µA at 2 MSPS (4.5 µW) | simulated |
| Reference charge | 2.5 µA average (3.0 µW from an ideal source) | simulated |
| SAR logic and timing | ≈ 20–50 µW | estimated |
| Reference buffer | 0.5–1 mA (0.6–1.2 mW), dominates ADC power | estimated (S1), not designed |

### Area (estimated)

| Part | Basis | Area |
| --- | --- | --- |
| CDAC MIM, 2 slices × 2 sides × 95 units | 380 × 14.29 µm² = 5 430 µm² drawn; ≈ 29 µm² per unit cell with MIM spacing and routing | ≈ 0.011 mm² |
| Boost capacitors, 8 × 200 fF | MIM 8 × 133 µm² with overhead | ≈ 0.0015 mm² |
| Switches, drivers, comparators, track buffers | 8 bootstrapped switches (separate n-wells), 88 driver inverters, 2 comparators; × 1.5 for routing | ≈ 0.003 mm² |
| SAR logic | 70 `sg13g2_dfrbp_1` (52.6 µm² each) + ≈ 20 gates, 75 % utilisation | ≈ 0.005 mm² |
| Reference buffer and its decoupling | S1 estimate, not designed | ≈ 0.02 mm² |
| **Total** | | **≈ 0.04 mm²** (S1 budget for the ADC pair with reference ≈ 0.12 mm²; D3 saving included) |

A CDAC with 9 × larger units (open issue 1, option c) adds ≈ 0.09 mm².

## Open issues

1. **CDAC matching (gate V2 fails on DNL).** In a 6+6 bridge array, one MSB-array unit carries 64 LSB. A 22 fF unit
   (σ 0.26 %) therefore gives σ(DNL) ≈ 0.66 LSB at the major transitions. S4 derived the 22 fF minimum for a full
   binary array; it does not hold for the bridge array. Options: (a) calibrate the five MSB-array weights (host-loaded
   correction words, measured by the ADC itself at start-up), with (b) one or two redundant decisions so that
   missing codes become recoverable; (c) MSB-array units of ≈ 200–350 fF (derived: 82–96 % yield on 0.5 LSB).
   Recommendation: (a) + (b). This needs a specification decision.
2. **Reference buffer load and level.** Up to 0.42 pC per 33 ns bit cycle, and the charge depends on the signal.
   A passive decoupling capacitor alone needs ≈ 2.9 nF for 0.25 LSB droop (*derived*), which is not possible on chip.
   The buffer must settle within each bit cycle; S1's 0.5–1 mA is not verified. VREF = 1.2 V cannot come from
   VDD = 1.08 V (minimum). A lower VREF (≈ 1.0 V) makes the full scale ≈ 1.94 Vpp, against the 2.4 Vpp in S1.
   Alternatively, supply the buffer from the 3.3 V domain. This is a specification decision.
3. **Comparator noise.** Not simulated (no device noise in an ngspice transient). With the simulated SNDR and kT/C,
   the comparator may add ≤ 60 µV rms for ENOB 11.5. The estimate for the present comparator is ≈ 120 µV.
   Next step: periodic-noise estimate or transient noise sources at the input pair, then a larger input pair or
   a longer integration time.
4. **Comparator offset versus common mode.** Monotonic switching moves the comparator input common mode from 0.6 V
   to ≈ 0 V. Under mismatch, the offset changes with the common mode and adds INL. Not run. If it is too large,
   use a common-mode-keeping switching scheme (split-capacitor monotonic).
5. **ss / 125 °C at the major transitions.** Codes 1023 and 2047 get 2 of 4 hits (DNL ≈ −0.5 LSB at 0.25 LSB
   resolution). The cause is not isolated. Next step: a finer window (0.05 LSB) at ss / 125 °C.
6. **Signal-dependent aperture.** The bootstrapped NMOS has its body at ground, so the effective sampling instant
   moves by 277 ps over ±0.7 V. This sets THD ≈ −79 dB at 100 kHz and up to 0.28 ns sine–cosine time difference.
   Inside the 0.5 ns target.
7. **Clock rate.** The frame needs 30 cycles of 30 MHz. The untrimmed oscillator (−30 %) gives 1.43 MSPS. The
   oscillator must be trimmed (S5) before the ADC meets 2 MSPS; alternatively shorten the track phase.
8. **D3 interpretation.** This design doubles the CDAC (it is the track-and-hold) and keeps one SAR logic block
   and one reference. The comparator is per slice, so the sine and cosine channels have different offsets
   (host offset calibration per channel, S1). The coordinator should confirm this reading of D3.
9. **Numerical aborts in ngspice.** Long conversion decks stopped with "Timestep too small" (8 times). Root cause:
   transient step argument `tstep` = 1 µs (used only for `linearize`). The same frame runs in a fresh run, so
   `sim/run_resume.py` restarts at the aborted frame. `sim/tb_adc_static_v2.cir` (tstep 1 ns, binary code output)
   removes the reproducible abort (run `tsteptest-ffm40-c2048`). Use it, and the same change in `tb_adc_dyn.cir`,
   for new runs. A post-processor for the binary output is still to be written.
10. **Current inputs.** The current channels share the 0.6 V common mode and the ±1.163 V full scale. `r1_isense`
    must drive that range and settle the 0.70 pF top node in the 200 ns track phase.

# R1_ADC — 12-bit SAR ADC with two simultaneous track-and-holds (schematic level, revisions 1 to 5)

State on 2026-10-21: **schematic written and simulated at schematic level only.** No layout, no PEX, nothing
measured. Every number in this file is **simulated** with ngspice 46 and the PDK models named below, unless it is
marked *estimated* or *derived*. The reference is an **ideal source** in revision 1 and in most revision-2 decks;
revision 2 adds the buffer `r1_refbuf` and simulates it in two decks. The SAR logic and the timing generator are
**behavioural** (XSPICE digital cells and ideal pulse sources).

## Revision 5 (2026-10-21, schematic level)

Revision 5 is a new netlist and new decks next to revisions 1–4, which are unchanged. All numbers in this section
are **simulated** at schematic level with ngspice 46 unless they are marked *derived* or *estimated*. Nothing is
laid out or measured. The coordinator decisions of 2026-10-21 apply: the comparator input CM stays at 0.6 V; the
reference buffer has no input divider (`r1_refbuf4h` + 10 pF input filter is the baseline); every reference deck
uses the bandgap output impedance (190 kΩ) and the r1_bgr noise spectrum as the source model.

### What changed

| Item | Revision 4 | Revision 5 |
| --- | --- | --- |
| Decision 0 comparator | `r1_cmp4` (PMOS input pair) for all 14 decisions. Fails at ss / 125 °C / CM 0.6 V (no headroom) | New `r1_cmp5n`: NMOS-input mirror of the same double-tail topology (variant n16rl: input 16 µm / 0.5 µm × 4, tail 8 µm, integration capacitors 30 µm × 4 µm, reset 16 µm, bias `rppd` 1 × 160 µm). It makes decision 0 only (CM 0.6 V). Clock gated `mclk AND win AND NOT fv0`. Decisions 1–13 stay on `r1_cmp4` (CM ≤ 0.35 V) |
| Reference | `r1_refbuf4` (input divider); fix `r1_refbuf4h` proposed | Baseline `r1_refbuf5h` (= `r1_refbuf4h`) + `r1_reffilt5` (10 pF, MIM 82 × 82 µm). **Chosen: R2-4 option 3 `r1_refbuf5`** (separate LSB-array reference: second follower group msfl 8 / mibl 40 on the same gate, own decoupling, `vrefl` drives C7…C0) with ndec 4 + ndecl 2 (same MIM cell count as the baseline). Option 2 `r1_refps5` (per-slice capacitor, isolated in conversion) simulated and rejected |
| Source model | ideal vbg in the R2-4 decks | Thevenin 190 kΩ + 10 pF filter + TRNOISE white and 1/f sources fitted to the r1_bgr density (tt floor 135 nV/√Hz, ss 168 nV/√Hz; 1/f fitted at 1 kHz; `sim/results/r5/trnoise_cal.json`). NT 47.3 ns (off the clock grid) |
| Simulator options | gmin 1e-10 / 1e-9 and rshunt 1e12 | PDK-default gmin, no rshunt. The ADC idles in track from t = 0, so no node floats at the operating point |
| Runner | `run_points4.py`: resumed after aborts, skipped frames | `run_points5.py` + `run_ngspice5.py` + `run_q5.sh`: one job per call, no resume, no resubmission, non-zero exit on any failure (details below) |
| Input steps | PWL corners on the clk30 grid | PWL corners 5 ns after the clk30 falling edge (from 04:25 CEST; field `pwl_shift_ns` in `run.json`) |

### Files (revision 5)

| Path | Content |
| --- | --- |
| `schematic/gen_r1_adc_r5.py`, `schematic/r1_adc_r5.spice`, `schematic/r1_adc_r5_mm.spice` | Generator and library: `r1_cmp5n(_s1)`, `r1_cmp5n_bias`, `r1_sar5_logic`, `r1_adc5_core`, `r1_adc5_core_fast`, `r1_adc5_core_fast_mc`, `r1_refbuf5h`, `r1_refbuf5` (option 3), `r1_refps5` (option 2), `r1_reffilt5`. Revision-2/3/4 cells are reused unchanged. Frozen: `sim/r5/FROZEN_NETLIST_SHA256.txt` |
| `sim/r5/tb_adc5_points.cir`, `sim/r5/run_points5.py`, `sim/r5/run_ngspice5.py`, `sim/r5/run_q5.sh` | Held-input deck (reference model, noise, gmin, rshunt, op-only by option; `--mcs K`: sampled MIM mismatch on the nominal core); runner; ngspice wrapper; job queue |
| `sim/r5/gen_timing_r5.py`, `sim/r5/r1_adc_timing_r5_*.inc` | D18 timing as revision 4, track high from t = 0; `_cq` = track edge 0.3 ns after the clock edge |
| `sim/r5/gen_cmp5_decks.py`, `tb_cmp5n_mem(_c).cir`, `tb_cmp5n_noise(_c).cir`, `run_cmp5.sh`, `post_cmp5.py` | NMOS comparator sweep: memory and decision time with the clkgen clock, noise (method A) |
| `sim/r5/tb_trnoise_cal.cir`, `sim/r5/post_trnoise_cal.py` | Calibration of the TRNOISE source levels against the r1_bgr density |
| `sim/r5/post_ref5.py`, `sim/r5/sum_ref5.py` | R2-4 metric and option summary (`ref5_options.json`, estimated areas) |
| `sim/r5/post_sweep5.py` | Decision-0 64-input sweep |
| `sim/r5/gen_points5.py`, `sim/r5/place_windows5.py`, `sim/r5/post_mc5.py`, `sim/r5/points/*.json` | MC weight calibration: locate inputs, window placement check, 14-weight fit, DNL, check of the fitted weights against the r1_ctrl register widths |
| `sim/r5/jobs_*.txt` | Job files of the campaign (CPU 103–105) |
| `sim/r5/gen_timing_pre5.py`, `sim/r5/r1_adc_timing_r5_*_pre*.inc` | T2: timing with one start-up hold pulse on `trk0` (first-conversion fix test) |
| `sim/r5/tb_adc5_dyn.cir`, `sim/r5/tb_adc5_isa.cir`, `sim/r5/tb_refbuf5_noise.cir` | T2 decks: dynamic test (chunks), mux sequence with the full core and supply currents, reference noise |
| `sim/r5/run_deck5.py`, `sim/r5/run_qt2.sh`, `sim/r5/jobs_t2_*.txt` | T2 runner for the non-points decks (same `run.json` and exit rules), queue, job files |
| `sim/r5/gen_points_t2.py`, `sim/r5/points/{ff2,fixtt,cornwin5,inlramp5,inlramp5a,inlramp5b}.json` | T2 input sets (every set starts with an unused start-up frame) |
| `sim/r5/post_t2.py`, `sim/r5/post_refnoise5.py` | T2 post-processing: first conversion, static windows, dynamic, mux and currents, INL; reference noise |
| `sim/r5/refreeze_t2.py` | Regenerates the library with the `r1_refbuf5` bias pin, checks that nothing else changed, renews the freeze |
| `sim/results/r5/` | Result JSON (all < 1 MB). Raw files: `<G1_RESULTS_ROOT>/r1_adc/<run-id>/`; run records `sim/runs/r5-*/run.json` |

### Pins for the layout track (revision 5)

Cells of record: `r1_adc5_core` (both slices, comparators, SAR, clkgen), `r1_refbuf5` (reference buffer, option 3c:
`ndec=4 ndecl=2`) and `r1_reffilt5` (10 pF input filter). The SAR logic is behavioural; on chip, r1_ctrl and the SAR
sequencer replace the timing ports.

| Pin | Cell | Direction | Domain | Connects to / value |
| --- | --- | --- | --- | --- |
| `sinp sinn cosp cosn` | `r1_adc5_core` | in, analog | 1.2 V | r1_afe outputs (CM 0.6 V, ±0.72 V differential) |
| `isap isan isbp isbn` | `r1_adc5_core` | in, analog | 1.2 V | r1_isense outputs (CM 0.60 V, ±0.85 V) |
| `trka0 trka1 trkb0 trkb1`, `clk30`, `wina winb`, `lata latb`, `stba0…13 stbb0…13` | `r1_adc5_core` | in, digital | 1.2 V | r1_ctrl frame timing (D18); start-up hold phase on `trk*0` (open issue 1) |
| `rawa rawb` | `r1_adc5_core` | out | 1.2 V | behavioural raw word; on chip 14 decision bits + `valid` per slice to r1_ctrl |
| `topap topan topbp topbn` | `r1_adc5_core` | probe | — | CDAC top plates (simulation probes; no pad) |
| `vrefa vrefb` | `r1_adc5_core` | in, reference | — | `r1_refbuf5` `vref` (MSB array) |
| `vrefla vreflb` | `r1_adc5_core` | in, reference | — | `r1_refbuf5` `vrefl` (LSB array, lsb-node reset) |
| `vdd`, `gnd` | `r1_adc5_core` | supply | 1.2 V | core supply |
| `vbg` | `r1_refbuf5`, `r1_reffilt5` | in | — | r1_bgr `vref` (≈ 190 kΩ source) and the 10 pF filter |
| `vref`, `vrefl` | `r1_refbuf5` | out | — | `vrefa vrefb` / `vrefla vreflb` of the core |
| `nb` (**new**, T2 2026-10-21) | `r1_refbuf5` | in, bias current | VDDA | r1_bias `ib_adc_ref`: 5.07 µA at tt (3.5–7.7 µA PVT) sourced into the diode XMB0 (2 / 1 µm); pin voltage 0.82 V at tt (r1_bias README) |
| `vdda`, `gnd` | `r1_refbuf5` | supply | 3.3 V | buffer supply |

### Built against (revision 5)

| Item | Value | How established |
| --- | --- | --- |
| PDK | IHP SG13G2 open PDK commit `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` | `flow/run.sh` commit check; `pdk_commit` in every `sim/runs/r5-*/run.json` |
| Container image | `sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2` | `container_image` in `run.json` |
| ngspice | ngspice-46 (creation date 27 Jul 2026), KLU, XSPICE, PSP 103.6 OSDI | `ngspice_version` in every `run.json` |
| Netlist identity | `r1_adc_r5.spice` sha256 `340c0e6a…bb0988d6`, `r1_adc_r5_mm.spice` `3bc50331…0426ae0` since the `r1_refbuf5` bias pin (T2, 2026-10-21 10:04 CEST). Before: `a2c3c9a2…c34c99e8` / `cfa754bf…1b454ba2`; only the `r1_refbuf5` port differs (the comparator sweep decks ran before the first freeze and carry their own sha256) | `netlist_sha256` and `frozen_netlist_check` in `run.json`; `sim/r5/FROZEN_NETLIST_SHA256.txt` |
| Models | `cornerMOSlv/hv.lib` `mos_tt` / `mos_ss` / `mos_ff`, `cornerCAP.lib` `cap_typ` / `cap_typ_mismatch`, `cornerRES.lib` `res_typ` | deck headers in `sim/runs/r5-*/deck.cir` |
| Options | `reltol=1e-4 vntol=1e-6 abstol=1e-12 method=trap klu`, seed, tmax 0.2 ns, PDK-default gmin unless a run sets `gmin`, no rshunt | `substitutions` and `gmin` in `run.json` |
| xschem, KLayout, LibreLane, CACE | not used | — |

### Status (revision 5, simulated at schematic level)

`<G1_RESULTS_ROOT>` is the results root of the campaign (raw files, not in git). Evidence paths are relative to this block directory.

| Item | Check | Result | Status | Evidence |
| --- | --- | --- | --- | --- |
| 1 R2-4 | Reference settling ≤ 0.25 LSB comparator-input error, ±0.88 V, buffer in the loop, both slices, tt | Chosen option 3c: 0.209 LSB (cross-check 0.145 LSB). Baseline `r1_refbuf5h`: 0.620 LSB | **passed** (option 3c); baseline **failed** | `sim/results/r5/ref5_options.json`, `ref5_tt_*.json`; runs `r5-ref-tt-*` |
| 1 R2-4 | Same at ss / 125 °C / 1.08 V | Option 3c: 0.163 LSB (cross-check 0.131). Baseline: 0.437 LSB | **passed** (option 3c) | `sim/results/r5/ref5_ss125_opt3c.json`, `ref5_ss125_buf.json`; runs `r5-ref-ss125-opt3c`, `r5-ref-ss125-buf-p` |
| 1 R2-4 | Same at ff / −40 °C / 1.32 V | Option 3c: 0.186 LSB (cross-check 0.167). Baseline: 0.572 LSB | **passed** (option 3c) | `sim/results/r5/ref5_ffm40_opt3c.json`, `ref5_ffm40_buf.json`; runs `r5-ref-ffm40-*` |
| 1 R2-4 (T2) | Same at ssx (ss / −40 °C / 1.32 V), base run at the buffer DC value 1.0488 V | Option 3c: 0.164 LSB (cross-check 0.115). With a base run at 1.0505 V the metric gave 0.858 LSB: the step-scaling artefact of failure 7 (buffer 1.7 mV below the base) | **passed** | `sim/results/r5/ref5_ssx_opt3c.json`, `ref5_ssx_opt3c_interp.json`; runs `t2-ref-ssx-*-f` |
| 1 R2-4 (T2) | Same at ffx (ff / 125 °C / 1.08 V), base run at the buffer DC value 1.0526 V | Option 3c: 0.194 LSB (cross-check 0.189, extrapolated above 1.0505 V). Bandgap noise model: ss125 density at both cross corners (conservative) | **passed** | `sim/results/r5/ref5_ffx_opt3c.json`, `ref5_ffx_opt3c_interp.json`; runs `t2-ref-ffx-*-f` |
| 1 R2-4 (T2) | Bias pin `nb` of `r1_refbuf5` (coordinator 2026-10-21, r1_bias `ib_adc_ref`, PTAT 5.07 µA at tt): regression at 5 µA from the pin, tt | 0.209 LSB (cross-check 0.145), identical to the internal-source run `r5-ref-tt-opt3c-cq` (0.209 LSB); vref 1.050271 V as before | **passed** (pure port change) | `sim/results/r5/ref5_tt_opt3c_ib5.json`; runs `t2-op-tt-opt3c-ib5`, `t2-ref-tt-opt3c-ib5` |
| 1 R2-4 (T2) | Bias current 3.5 µA (low end of the r1_bias PVT range), tt, base run at the buffer DC value 1.05052 V | 0.179 LSB (cross-check 0.169); buffer IDDA 0.741 mA | **passed** | `sim/results/r5/ref5_tt_opt3c_ib35.json`; runs `t2-op-tt-opt3c-ib35`, `t2-ref-tt-opt3c-ib35`, `t2-ref-tt-ideal-ib35-f` |
| 1 R2-4 (T2) | Bias current 7.7 µA (high end of the range), tt, base run at the buffer DC value 1.04993 V | 0.201 LSB (cross-check 0.115); buffer IDDA 1.593 mA | **passed** | `sim/results/r5/ref5_tt_opt3c_ib77.json`; runs `t2-op-tt-opt3c-ib77`, `t2-ref-tt-opt3c-ib77`, `t2-ref-tt-ideal-ib77-f` |
| 1 R2-4 | Option 2: per-slice capacitor (2 + 2 cells), charged in track, isolated in conversion, tt | 88.98 LSB (droop during the MSB decisions). Variant with 6 cells (`r5-ref-tt-opt2b-cq`): run marked failed (singular-matrix warning); not used | **failed** (option rejected) | `sim/results/r5/ref5_tt_opt2a.json`; run `r5-ref-tt-opt2a-cq` |
| 1 R2-4 | Option 3 variants, tt (3a ndec 6 + ndecl 1; 3b second buffer; 3d msfl 16; 3e tail lt 32 µm, ncg 2; 3 with ncg 8) | 0.206 / 0.219 / 0.207 / 0.112 / 0.189 LSB | passed (all) | `sim/results/r5/ref5_tt_opt3*.json` |
| 1 | VREF static value after the slow error amplifier, option 3c (vbg 1.045 V) | vref 1.05035 / 1.05059 / 1.05074 V (tt / ss / ff): +5.4 to +5.7 mV, gain error ≈ 0.5 % (≈ 10 LSB at full scale). Error left after a gain fit: 0.143 / 0.144 / 0.171 LSB | gain calibration removes it (derived from the R2-4 runs) | `sim/results/r5/ref5_*_opt3c.json` (`max_abs_error_after_gain_fit_lsb`) |
| gmin | Operating point at the PDK-default gmin and at gmin 1e-15 (full reference + ADC, tt) | vref 1.050271 V in both; largest node difference 1 µV (0.002 LSB) | **passed** (≤ 0.05 LSB) | `sim/results/r5/gmin_op5.json`; runs `r5-op-buf-gdef-c`, `r5-op-buf-g15-c` |
| gmin | R2-4 baseline transient at the default gmin and at gmin 1e-15 (tt, input steps off the clock grid) | Same codes; largest difference 0.0024 LSB (worst-case 0.6195 / 0.6194 LSB) | **passed** | `sim/results/r5/gmin_tran5.json`; runs `r5-ref-tt-buf-p`, `r5-ref-tt-buf-g15-p` |
| 2 | Decision 0 at CM 0.6 V, ss / 125 °C / 1.08 V, 64-input sweep, `r1_cmp5n` | Frames 1–63: largest error 1.02 LSB against the straight-line fit (redundancy 30.6 LSB); decision 0 resolves at all 16 inputs between −12 and +3 mV; monotonic. Frame 0 (first conversion after t = 0): error 113 LSB (A) / 99 LSB (B); a repeat run shows that only the first frame is wrong (start-up, open issue 1) | **passed** (63 of 64 frames); start-up frame **failed** | `sim/results/r5/sweep5_ss125.json`; runs `r5-sweep-ss125`, `r5-dbg-ss-slot0` |
| 1 (T2) | First conversion after enable: root cause. Instrumented first frame at ss / 125 °C / 1.08 V, −0.90 V in frames 0 and 1: bootstrap capacitor, switch gate, top and bottom plates, lsb nodes, comparator clocks and outputs, SAR clocks | Bottom plates (1.045 V), lsb nodes, comparator reset, SAR flags and clocks are correct in frame 0. The bootstrap capacitor of the in0 switch holds 0.117 V at the end of the first track window (charged: 0.923 V). The N-side switch gate is 1.022 V with the input at 1.050 V, so the switch is off. `topan` is 0.991 V instead of 1.050 V. Frame 0 − frame 1: +123 LSB (A), +107 LSB (B) | cause found (see open issue 1) | `sim/results/r5/firstconv5.json`; run `t2-ff-ss-inst1` |
| 1 (T2) | Fix test: one start-up hold pulse on `trk0` (10, 33 or 67 ns from 106 ns), then track until the first sampling edge (r1_ctrl sequence; netlist unchanged; timing `sim/r5/gen_timing_pre5.py`) | ss, −0.90 V: frame 0 − frame 1 = 0 LSB (A) and +1 LSB (B) for all three widths. tt, 0 V: ±1 LSB with and without the pulse (0 V lies on the 2047/2048 transition; both inputs of each switch are at 0.6 V, so an open switch does not show). Full core, mux sequence with a 33 ns pulse: frame 0 converts on the straight line at tt, ss and ff (rows below) | **passed** (with the r1_ctrl sequence) | `sim/results/r5/firstconv5.json`; runs `t2-ff-ss-pre10`, `-pre33`, `-pre67`, `t2-ff-tt-pre33`, `t2-ff-tt-nopre` |
| 2 R2-3 | Comparator noise ≤ 60 µV at ss / 125 °C, `r1_cmp5n` (method A) | 57.0 µV (tt 43.5, ff 34.4 µV). Decisions 1–13 keep `r1_cmp4` (55.9 µV, revision 4) | **passed** | `sim/results/r5/cmp5n_c.json` (variant n16rl) |
| 2 | Decision time inside the 33 ns tick, `r1_cmp5n`, CM 0.5 / 0.6 / 0.7 V, all corners | 8/8 correct at every corner and CM. Slowest 15.46 ns (ss, CM 0.5 V); 12.41 ns at ss, CM 0.6 V. Margin to the strobe ≥ 15.0 ns | **passed** | `sim/results/r5/cmp5n_c.json` |
| 2 | Comparator variant set b (n8, n8s, n8c, n16) | Memory test 4/8 (large integration capacitors, weak reset) or noise above 60 µV (n8c) | failed (variants rejected) | `sim/results/r5/cmp5n_b.json` |
| 3 R2-11 | MC window placement checked on the nominal circuit before the MC | Locate run: LSB ≈ 455 µV; decision-0 toggle −0.25…+0.25 mV inside window 2048; windows at the transitions 1023/1024, 2047/2048, 3071/3072 (outer ones extrapolated, ≈ ±466 mV) | **passed** | `sim/results/r5/mc_window_check.json`, `sim/r5/points/mccal5.json`; run `r5-locate-tt` |
| 3 R2-11 | Weight calibration on the circuit: MIM-mismatch MC, 12 slice samples (6 seeds × 2 slices, sampled mismatch, open issue 2), all 14 weights fitted per sample (known-input least squares, 65 conversions: 14 spread + 3 windows of ±2 LSB at 4 points per LSB; frame 0 excluded) | Fit residual 0.11–0.15 LSB rms; all weights positive. Design weights: major-transition \|DNL\| median 0.75, max 1.0 LSB, 5/12 ≤ 0.5 LSB, 4 samples non-monotonic, 2 missing codes. Fitted weights: max \|DNL\| 0.25 LSB (the resolution) on 11/12 and 0.5 LSB on 1/12, all monotonic, no missing code. Cross-check MAP fit (one offset per window, PDK-mismatch prior): same result. The fit and the DNL use the same conversions | **passed** | `sim/results/r5/mc5_summary.json`; runs `r5-mcs1-tt-s1…s6` |
| 3 (T2) | INL with fitted weights on 2 MC slice samples (seed 1, slices A and B, the sampled mismatch of `r5-mcs1-tt-s1`), tt, ideal VREF. **Reduced ramp**, not a full ramp: 96 inputs per slice over ±0.90 V (one per 40.6 LSB, sub-LSB random offsets) | Fitted weights: max |INL| 1.56 / 1.42 LSB (A / B, integer codes, includes ±0.5 LSB quantisation), 1.17 / 1.20 LSB on the unrounded weighted sum; cubic part (smooth INL) 1.10 / 0.96 LSB. Design weights: 1.96 / 1.83 LSB. Monotonic along the ramp: yes | **run**; code-level INL between the ramp points not resolved | `sim/results/r5/inl5_tt_s1.json`; runs `t2-inl-tt-s1a`, `t2-inl-tt-s1b` |
| 3 | Full-ramp INL (≥ 4096 conversions per sample) | — | not run (≈ 60 CPU-h at 55 s per frame; see failure 27) | — |
| 3 | Fitted weights against the r1_ctrl register widths (R1_REGISTER_MAP.md 0.4, section 4.11: WW(i) = 3…14 bit, 1/4 LSB, unsigned) | 12/12 samples × 14 weights fit; no saturation, no negative weight. Largest fraction of the register range used, register index 13 → 0: 0.497, 0.248, 0.249, 0.249, 0.249, 0.154, 0.155, 0.157, 0.169, 0.158, 0.159, 0.161, 0.200, 0.143 | **passed** | `sim/results/r5/mc5_summary.json` (`register_width_check`) |
| 4 | Runner: non-zero exit on any failed job, no automatic resubmission, no silent frame skipping | Implemented (see "Runner fix"). Exercised: 35 runs of this campaign failed or were stopped (debug runs included). Each one stopped its job and returned 1. None was resubmitted; every rerun has a new run id | **passed** | `sim/r5/run_ngspice5.py`, `run_points5.py`, `run_q5.sh`; queue logs `<G1_RESULTS_ROOT>/r1_adc/r5-q-*.log` |
| 5 | Buffer at ss / ff | R2-4 rows above (baseline and option 3c) | **passed** (option 3c) | see R2-4 rows |
| 5 (T2) | Static windows ss / 125 °C / 1.08 V: ±6 LSB at 2047/2048 and 3071/3072, 1.95 conversions per LSB, ideal VREF 1.045 V, design weights | A: max |DNL| 0.54 LSB, monotonic, missing none; B: max |DNL| 0.54 LSB, monotonic, missing none | **passed** | `sim/results/r5/win5_ss125.json`; run `t2-win-ss125` |
| 5 (T2) | Static windows ff / −40 °C / 1.32 V (same windows) | A: max |DNL| 0.54 LSB, monotonic, missing none; B: max |DNL| 0.54 LSB, monotonic, missing none | **passed** | `sim/results/r5/win5_ffm40.json`; run `t2-win-ffm40` |
| 5 (T2) | Dynamic ss / 125 °C / 1.08 V: N 256 (two chunks of 128 frames, start-up frame of each chunk not used), fin 101.207 kHz (19/256 of the frame rate), 0.85 V, ideal VREF, design weights, no device noise | SNDR 70.20 / 70.45 dB (A / B), ENOB 11.37 / 11.41, SFDR 74.6 / 75.2 dB, THD -74.5 / -75.0 dB | **run** (no limit in the brief) | `sim/results/r5/dyn5_ss125_n256.json`; runs `t2-dyn-ss125-c0`, `-c1` |
| 5 (T2) | Dynamic ff / −40 °C / 1.32 V (same test) | SNDR 66.71 / 66.65 dB (A / B), ENOB 10.79 / 10.78, SFDR 68.1 / 68.1 dB, THD -68.1 / -68.0 dB. Third harmonic 0.73 LSB amplitude (ss: 0.30–0.39 LSB); it sets the ff result (open issue 12). Chunk c0 is labelled failed: a singular-matrix warning at the operating point, resolved by gmin stepping; the transient is complete, and the two chunks agree within 0.2 dB (sine fit per chunk), so c0 is used | **run** (no limit in the brief) | `sim/results/r5/dyn5_ffm40_n256.json`; runs `t2-dyn-ffm40-c0` (labelled failed), `-c1` |
| 5 (T2) | Mux sequence e c e e, full core `r1_adc5_core`, option 3c with the r1_bgr model, 33 ns start-up hold pulse, tt / ss / ff (`sim/r5/tb_adc5_isa.cir`) | Codes in the correct order and frame at all three corners (SIN/COS, ISA/ISB ±0.85 V at CM 0.60 V, SIN/COS); latch 14.02 ticks after the sampling edge. Errors against the nominal line (LSB 454.9 µV × VREF / 1.045 V): tt: max error 3.66 LSB, gain 0.9982, residual after a gain fit 0.45 LSB, track ≥ 257.8 ns; ss: max error 5.22 LSB, gain 0.9975, residual after a gain fit 0.39 LSB, track ≥ 257.7 ns; ff: max error 0.96 LSB, gain 0.9997, residual after a gain fit 0.65 LSB, track ≥ 257.8 ns | **passed** | `sim/results/r5/isa5_tt.json`, `isa5_ss125.json`, `isa5_ffm40.json`; runs `t2-isa-tt`, `t2-isa-ss125-b`, `t2-isa-ffm40-b` |
| 3 (T2) | Reference noise of option 3c at the CDAC, 10 Hz–10 MHz, criterion 110 µV rms: r1_bgr spectrum (run `bgr-noise-20261021-b`) through H(f) of Rs 190 kΩ + 10 pF filter + buffer, plus the buffer's own noise (`sim/r5/tb_refbuf5_noise.cir`, `post_refnoise5.py`) | vref / vrefl: tt 87.6 / 88.6 µV, ss / 125 °C 108.5 / 109.7 µV (VDDA 3.3 V; 108.4 / 109.7 µV at 3.0 V). Source at 180 kΩ: tt 88.1 / 89.1 µV, ss 109.1 / 110.3 µV. Buffer self-noise 62.4 µV (tt), 74.9 µV (ss). Note (coordinator 2026-10-21): r1_t2f in mode 0 lowers the bandgap vref by 2.1 mV; this is a gain error (0.2 %) that the weight calibration absorbs; nothing run | **passed** at tt; ss **marginal**: passed at 190 kΩ; at 180 kΩ vrefl is 0.3 µV above 110 µV (vrefl reaches the comparator through the bridge, so the criterion is conservative for it) | `sim/results/r5/refnoise5.json`; runs `t2-refn-*-b`, `t2-refn-*-rs180` |
| 5 (T2) | Full-core supply current (both slices, transistor drivers, bootstrapped switches, `r1_cmp4` × 2 + `r1_cmp5n` × 2 + both biases, clkgen; option 3c buffer with 5 µA), time average over the four mux frames | tt IDD 0.903 mA at 1.2 V, IDDA 1.034 mA at 3.3 V; ss / 125 °C IDD 0.595 mA at 1.08 V, IDDA 1.029 mA at 3.3 V; ff / −40 °C IDD 1.300 mA at 1.32 V, IDDA 1.043 mA at 3.3 V. The SAR logic is behavioural and draws no current here | **run** (no limit in the brief) | `sim/results/r5/isa5_*.json` (`idd_mA`, `idda_mA`; ngspice `meas` in the run logs agrees) |
| — | Layout, PEX | — | not run | — |

### R2-4 options (tt, 10 test inputs at up to ±0.88 V, both slices at the same time, bandgap model, PDK-default gmin)

Metric (`post_ref5.py`): comparator-input error 25 ns into each tick for decisions 5…13 along the common decision
path, against an ideal-reference run at 1.0505 V (the buffer DC value is 1.0503–1.0508 V). The small remaining VREF
difference is removed with steps proportional to VREF, separately for the MSB array (vref) and the LSB array
(vrefl). Cross-check: per-slot interpolation between two ideal runs (1.045 V and 1.0505 V); it is valid only where
both ideal runs take the same bits (all slots at decisions 5–11, 1–5 of 9 slots at decisions 12–13). Pass needs
both values ≤ 0.25 LSB. Frame 0 (start-up) is not counted. Areas are *estimated* from device sizes.

| Option | Worst-case (LSB) | Cross-check (LSB) | After gain fit (LSB) | IDDA (mA) | Area (mm², est.) | ≤ 0.25 LSB |
| --- | --- | --- | --- | --- | --- | --- |
| Baseline `r1_refbuf5h` (msf 32, mib 160, 6 Cd cells, ncg 1, tail mt 1 / lt 8 µm) + 10 pF filter | 0.620 | 0.612 | 0.367 | 0.842 | 0.0407 | no |
| Baseline, ncg 4 | 0.476 | 0.434 | 0.277 | 0.843 | 0.0482 | no |
| Option 2: baseline with 2 Cd cells + per-slice capacitor 2 cells (`r1_refps5`) | 88.983 | 88.935 | 34.207 | 0.832 | 0.0411 | no |
| Option 3a: `r1_refbuf5` defaults (ndec 6, LSB group msfl 8 / mibl 40, ndecl 1) | 0.206 | 0.142 | 0.146 | 1.051 | 0.0459 | yes |
| Option 3b: second complete buffer for vrefl (msf 8, mib 40, 1 Cd cell) | 0.219 | 0.182 | 0.176 | 1.058 | 0.0477 | yes |
| **Option 3c (chosen)**: `r1_refbuf5`, ndec 4, ndecl 2 | 0.209 | 0.145 | 0.143 | 1.046 | 0.0410 | yes |
| Option 3d: msfl 16, mibl 80, ndecl 2 | 0.207 | 0.143 | 0.145 | 1.255 | 0.0511 | yes |
| Option 3e: tail lt 32 µm, ncg 2 | 0.112 | 0.096 | 0.128 | 1.052 | 0.0484 | yes |
| Option 3: ncg 8, msfl 16, mibl 80, ndecl 2 | 0.189 | 0.113 | 0.085 | 1.257 | 0.0686 | yes |

Corners (option 3c and baseline, same metric):

| Corner | Option 3c worst-case / cross-check (LSB) | Baseline worst-case / cross-check (LSB) | IDDA 3c / baseline (mA) |
| --- | --- | --- | --- |
| tt / 27 °C / 1.2 V | 0.209 / 0.145 | 0.620 / 0.612 | 1.046 / 0.842 |
| ss / 125 °C / 1.08 V | 0.163 / 0.131 | 0.437 / 0.357 | 1.037 / 0.834 |
| ff / −40 °C / 1.32 V | 0.186 / 0.167 | 0.572 / 0.735 | 1.061 / 0.854 |

Mechanism: in the baseline the error peaks at decision 6 (0.61 LSB). The LSB-array drivers switch C7…C0 on the
same vref node as the MSB array, and the slow error amplifier integrates the dip onto the follower gate. With a
separate LSB-array follower (option 3) the MSB node sees only the MSB switching, and the error falls to
0.11–0.22 LSB. Option 2 fails by droop: the per-slice capacitor alone (2 × 2 cells) loses about 20–90 LSB during the
MSB decisions, because it is isolated from the buffer during the conversion.

Choice (recommended option, recorded): **option 3c** (`r1_refbuf5`, ndec 4, ndecl 2, msfl 8, mibl 40). It passes with
the smallest area of the passing options: 0.0410 mm² (estimated, same as the baseline 0.0407 mm²), IDDA 1.046 mA at
tt (+0.20 mA against the baseline). Option 3e (error-amplifier tail lt 32 µm, ncg 2) has more margin (0.11 LSB) at
0.0484 mm² and is the fallback.

### Runner fix (item 4)

1. `run_ngspice5.py` exits 1 when the run status is not `completed`.
2. A run is `failed` on any of: "timestep too small", "aborted", "singular matrix", "did not converge", gmin or source
   stepping failed, an error line, or a missing or empty expected output (`--expect`).
3. `run_points5.py` runs one segment from t = 0. It does not resume and does not skip frames. If the run fails,
   `segments` stays empty and the post-processors refuse the run.
4. `run_q5.sh` runs the jobs of a file one after the other. A failed job is logged as `FAILED` and is not
   resubmitted. The queue exits 1 at the end if any job failed.
5. Every `run.json` records the command, PDK commit, ngspice version, netlist sha256, frozen-netlist check and a
   disposition label.

### Area and power (revision 5)

| Part | Area (mm², estimated) | Current (simulated) |
| --- | --- | --- |
| CDAC, both slices (unchanged from revision 3) | 0.0185 | — |
| Comparators `r1_cmp4` × 2 + bias + clkgen (decisions 1–13, revision 4) | 0.003 | included in IDD |
| Comparators `r1_cmp5n` × 2 + bias (decision 0, new) | 0.001 | continuous clock, 3 comparators + bias: 1.38 / 0.87 / 2.25 mA (tt / ss / ff); in the ADC it is clocked one tick per frame (included in the full-core IDD) |
| Switches, drivers, SAR logic (behavioural; area from revision 3) | 0.012 | included in IDD |
| Reference option 3c `r1_refbuf5` (ndec 4 + ndecl 2 cells 70 × 70 µm, Cg 50 × 50 µm, two follower groups) + input filter `r1_reffilt5` 10 pF (82 × 82 µm) | 0.0410 | IDDA 1.046 / 1.037 / 1.061 mA at 3.3 V (tt / ss / ff) |
| **Total** | **≈ 0.0755** | Full core (T2, mux runs, time average): IDD 0.903 / 0.595 / 1.300 mA at 1.2 / 1.08 / 1.32 V, IDDA 1.034 / 1.029 / 1.043 mA at 3.3 V (tt / ss / ff); ≈ 4.5 mW at tt. Revision 4 IDD corrected to 0.86 mA at tt (failure 30) |

The baseline reference (`r1_refbuf5h` + filter) is 0.0407 mm² and 0.842 mA, so option 3c costs +0.0003 mm² and
+0.20 mA. All areas are estimates from device sizes; nothing is laid out.

### Open issues (revision 5)

1. Start-up frame: **cause found (T2, 2026-10-21)**. The bootstrap capacitor (200 fF) of each in0 sampling switch
   (`r1_bootsw`) charges only while its track signal is low. The ADC idles in track (revision-5 timing; r1_ctrl
   `adc_hold` = 0 in reset). So after enable, after a reset or after a long idle, the first track window starts with
   an uncharged capacitor (0.12 V in the DC state at ss / 125 °C, 0 V at power-up). The switch gate is then only about
   0.1 V above the input. For inputs near VDD the switch is off, and the top plate stays at a leakage value (towards
   the in1 port at 0.6 V). The error depends on the input: +123 / +107 LSB at −0.90 V at ss, none at 0 V. Revision 4
   did not have the fault, because its track signal was low at t = 0 (failure 20).
   Fix (simulated, recommended option, recorded): r1_ctrl drives one hold phase of ≥ 1 tick after reset or enable,
   then ≥ 250 ns track before the first sampling edge. 10 ns is enough at ss. The ADC netlist does not change.
   INTERFACES.md row "ADC → ctrl, first conversion" now states this sequence; the discard rule stays only until
   r1_ctrl implements it (r1_ctrl 0.5). ADC-side alternative for revision 6, only if r1_ctrl cannot do it: an enable
   input that holds the in0 bootstraps in their hold state while the ADC is disabled (new port; not designed).
   Not simulated: how long the capacitor keeps its charge in a long idle in track (the DC state is the end point).
   The in1 (current) switches idle in hold and are not affected. All metrics still skip frame 0.
2. The PDK-agauss MC core (`r1_adc5_core_fast_mc`, one `cap_cmim` per unit capacitor) has no DC operating point. It
   fails at the default gmin, at gmin 1e-9, with rshunt 1e12, and also with `cap_typ` (no mismatch); the nominal core
   converges (runs `r5-dbg-opmc-*`). The MC therefore uses sampled mismatch (`run_points5.py --mcs`): the nominal core
   with per-capacitor scale factors from the PDK formula (σ = 1 % / √(unit area in µm²) per unit). The perimeter part
   of the MIM capacitance is scaled by √k instead of k, so the simulated mismatch is about 5 % too small (estimated).
3. R2-4 margin of option 3c is small (0.16–0.21 LSB against 0.25 LSB). Option 3e (tail lt 32 µm, ncg 2: 0.11 LSB at
   tt, +0.0074 mm²) is the fallback; it was run at tt only.
4. vrefl of option 3c dips by up to 70 mV during decisions 5–6 and recovers before the strobe. The comparator-input
   metric includes this, but the dip makes the result depend on the LSB-follower size. A corner MC of the follower
   is not run.
5. The slow error amplifier gives a static VREF offset of +5.4 to +5.7 mV (gain error ≈ 0.5 %). Gain calibration
   must remove it. Start-up and drift time of the slow loop are not simulated.
6. Reference noise of option 3c (T2): tt 87.6 / 88.6 µV, ss 108.5 / 109.7 µV (vref / vrefl) against 110 µV. The ss
   margin is ≤ 1.5 µV; with a 180 kΩ source vrefl is 110.3 µV. The sampling and aliasing of the noise by the ADC are not
   modelled (as in revision 4). A larger input filter would add margin (estimate, not run).
7. Not run: layout, PEX, a full ramp (T2 ran a reduced ramp), the dynamic test with the buffer and noise at ss / ff
   (the T2 dynamic runs use an ideal VREF), static windows at the cross corners.
8. The R2-4 cross-check (two-run interpolation) covers all slots for decisions 5–11, but only 1–5 of 9 slots for
   decisions 12–13. The primary metric covers all slots.

9. Bias pin `nb` of `r1_refbuf5` (T2, coordinator 2026-10-21). The r1_bias output `ib_adc_ref` (PTAT, 5.07 µA at tt,
   3.5–7.7 µA over PVT) sources into the diode XMB0. R2-4 at tt: 0.179 LSB at 3.5 µA, 0.209 LSB at 5 µA, 0.201 LSB at
   7.7 µA. Buffer IDDA 0.74 / 1.05 / 1.59 mA. The combination of the current extremes with the process and temperature
   corners was not run. r1_bias recommends a filter on `nb` (RC between the diode and the mirrors, or a MOS capacitor),
   because `nb` is mirrored ×160 and ×40 into the followers. Revision 5 adds only the port (coordinator: pure port
   change). The filter and the buffer's sensitivity to `nb` ripple are revision-6 items (not simulated).
10. With the start-up hold pulse, slice B gives frame 0 − frame 1 = +1 LSB at ss (−0.88 V), for 10, 33 and 67 ns. A
   conversion after an idle and a conversion after a conversion differ by 1 LSB. Within the redundancy; cause not
   investigated.
11. Gain against the nominal line (LSB 454.9 µV × VREF / 1.045 V): −0.25 % (ss), −0.18 % (tt), −0.03 % (ff) in the mux
   runs. The gain calibration removes it.
12. Third harmonic at ff / −40 °C / 1.32 V: HD3 amplitude 0.73 LSB at 0.85 V (THD −68.1 dB, SNDR 66.7 dB) against
   0.30–0.39 LSB at ss (SNDR 70.2–70.5 dB). The reference is ideal in these runs, so the source is in the sampling or
   the CDAC (candidates, not separated: switch on-resistance against the input at ff / −40 °C, junction capacitance on
   the top plate). Not investigated (time budget). Revision-4 tt with the buffer: THD −72.9 dB.
13. Reduced-ramp INL at tt with fitted weights (seed-1 samples): max 1.17 / 1.20 LSB on the unrounded weighted sum
   (A / B), 1.56 / 1.42 LSB on integer codes. A cubic fit holds 1.10 / 0.96 LSB of it: a smooth bow that the linear
   weight fit does not remove (revision 2: INL ±1.3 LSB). The source is probably the same as in issue 12 (sampling or
   top-plate non-linearity); not separated. The 96-point ramp does not resolve code-level INL.

### Failures and mistakes (revision 5)

| # | What happened | Class | Effect and fix |
| --- | --- | --- | --- |
| 1 | `run_ngspice5.py` computed the block path one level too high and created empty `sim/sim/runs` directories | tooling | Path fixed; empty directories removed (own files) |
| 2 | `@RAW@` inside a substituted value was not replaced (runs `r5-op-*`) | tooling | Second replace pass; runs labelled failed |
| 3 | The OP probes were written to an empty `op.txt` (save list excluded them, runs `r5-op-*-b`) | tooling | `save all` for op-only runs and the `--expect` check; runs relabelled invalid |
| 4 | Every transient stopped with "timestep too small": the track edge on the clk30 grid and the TRNOISE step (50 ns = 1.5 ticks) put breakpoints on clock edges. Revision 4 had hidden this with gmin 1e-9 and rshunt | numerical | `_cq` timing (track edge 0.3 ns after the clock edge) and NT 47.3 ns. First batch (`jobs_ref_tt_q*`) recorded as failed |
| 5 | Later runs with noise stopped at 2.25 µs (`r5-ref-ss125-buf`, `r5-ref-tt-buf-g15-cq`, `r5-ref-tt-buf-cg8`): an input PWL corner lay on a clk30 falling edge | numerical | PWL corners moved 5 ns off the edge; the gmin pair and the ss baseline were rerun (`*-p`); `r5-ref-tt-buf-cg8` not rerun |
| 6 | The final-residue metric used the ideal run's bits on diverged paths (11 LSB artefact) | functional-bug (post-processing) | Buffer run's own bits |
| 7 | The first R2-4 numbers compared the buffer (1.0505 V) with an ideal run at 1.045 V; the non-proportional part of the CDAC steps gave ≈ 1.4 LSB artefact proportional to the input. Revision 4 had recorded that the ideal run must be at the buffer DC value | regression / verification-gap | Ideal runs at 1.0505 V at all corners; two-run interpolation as a cross-check. Superseded numbers are not used |
| 8 | A first two-run model averaged the step sizes over all slots; the differences were too noisy (2 LSB artefact on slice B) | numerical (post-processing) | Replaced by the 1.0505 V base run and the per-slot interpolation |
| 9 | The locate inputs were first scaled for a 1.0 V reference (451–459 mV) | planning | Found before the run; rescaled to 471–482 mV |
| 10 | The outer code transitions (≈ ±466 mV) lay outside the locate range; the placement check refused to write the MC points | estimation | Extrapolated from the local slope; recorded in `mc_window_check.json` |
| 11 | `r5-ref-tt-opt2b-cq` (option 2, 6 cells) was marked failed by a singular-matrix warning, although ngspice returned 0 | numerical | Not used; option 2 is rejected on `opt2a` (89 LSB) |
| 12 | The revision-4 R2-4 values (0.45–0.79 LSB) depended on gmin and rshunt; revision 5 gives 0.62 LSB for the same circuit at the default gmin, independent of gmin | regression | Revision-4 values superseded |
| 13 | The revision-4 README called a PMOS-input comparator "not designed", but `r1_cmp4` already has a PMOS input pair. The missing part was an NMOS pair for CM 0.6 V | spec-ambiguity | `r1_cmp5n` designed |
| 14 | Hypothesis that the error-amplifier gate capacitor (Cg) kick sets the R2-4 error: ncg 4 gave only 0.62 → 0.48 LSB | estimation | The LSB-array switching on the shared node was the main term; option 3 fixes it |
| 15 | The MC was queued without an OP test of the MC deck; three MC runs (`r5-mc-tt-s1…s3`) failed in the first 15 s and CPU 103 was idle for 15 min | verification-gap | Sampled-mismatch MC (`--mcs`) after an OP test (`r5-dbg-opmcs-2`) |
| 16 | A chain for MC seed 2 was started three times by mistake (one already existed) | process-hygiene | The three duplicates were stopped by PID before they ran a job. Note: ngspice ignores SIGTERM; a run is stopped with SIGKILL on its own PID |
| 17 | `r5-dbg-opmcs-2` is labelled failed: the op-only probe names do not exist in MC decks. The OP itself converged | tooling | Recorded; the OP log is the evidence |
| 18 | The sampled MC with two instances in one deck advanced about 10 times slower than one instance (0.36 µs of 48.8 µs in 15 min). The first estimate (2.2 h per run) assumed linear scaling | estimation | Runs `r5-mcs-tt-s1…s3` stopped by PID after 25 min (labelled failed); six runs with one instance each (`r5-mcs1-tt-s1…s6`, 12 slice samples), speed checked first (`r5-dbg-mcspeed-*`) |
| 19 | The first MC post-processing included frame 0 (the start-up frame of open issue 1) in the 14-weight fit: fit residual 2.6–5.1 LSB, negative weights, 38 missing codes | verification-gap | Frame 0 excluded in `post_mc5.py` (as in the other post-processors); fit residual 0.11–0.15 LSB |
| 20 | The first-conversion candidates of open issue 1 (SAR flags, `fv0` gate, clkgen) were correct in frame 0. The cause was the in0 bootstrap capacitor: the revision-5 timing (track high from t = 0, for the DC operating point) removed the hold phase that charged it before the first sample in revision 4 | regression | Found by the instrumented run `t2-ff-ss-inst1`; fix = r1_ctrl start-up hold phase (open issue 1). A change of the idle state must be checked against every circuit that charges in that state |
| 21 | Open issue 1 stated "13 LSB at tt with 0 V". T2 gives ±1 LSB at tt with 0 V (the fault cannot show when both inputs of the switch are at 0.6 V). The source of the 13 LSB figure was not found in the run records | verification-gap | Statement replaced by the T2 numbers |
| 22 | The reference-noise deck used `klu`; ngspice 46 does not run a noise analysis with KLU. Runs `t2-refn-tt27-v33`, `-ss125-v30`, `-ss125-v33` failed | tooling | `sparse` in `tb_refbuf5_noise.cir`; reruns `-b` |
| 23 | The mux deck did not save `i(vdda)`, so its IDDA `meas` failed. Runs `t2-isa-ss125`, `t2-isa-ffm40` are labelled failed (their codes are valid) | tooling | Reruns `-b` with `i(vdda)` saved |
| 24 | The cross-corner R2-4 jobs used the default `--save codes`; the metric needs the top plates. Runs `t2-ref-ssx-opt3c`, `t2-ref-ffx-opt3c`, `t2-ref-ffx-ideal10505` completed but cannot be used; `t2-ref-ffx-ideal` was stopped by SIGKILL | planning | Job lines were not copied from the revision-5 job files. Reruns `-f` with `--save full` |
| 25 | The cross-corner base runs were at 1.0505 V, but the buffer gives 1.0488 V (ssx) and 1.0526 V (ffx). The primary metric gave 0.858 LSB at ssx: the artefact of failure 7 again | regression | Base runs at the buffer DC value: 0.164 / 0.194 LSB. `run_points5.py --vref op:<run>` sets the base from an op-only run |
| 26 | The sine-input dynamic chunks ran at 0.6–0.9 µs of simulated time per minute, slower than planned. The queues were stopped by PID and replaced several times (logs `t2-q*.log`) to rebalance, to fix job lines and to add the bias-pin work | estimation | No job was resubmitted. A running job continued; the next queue waited for its `run.json` |
| 27 | The brief's INL fallback "4 conversions per LSB" needs ≥ 16 384 conversions per sample (≈ 250 CPU-h at 55 s per frame); one per LSB needs ≈ 60 CPU-h. The intended reading was not clear | spec-ambiguity | Reduced ramp: 96 inputs per slice (one per 40.6 LSB), recorded as reduced |
| 28 | A `pgrep -f` pattern matched the agent's own shell. The `kill` ended that shell, not the queue | process-hygiene | No run affected; later PIDs taken from `ps` with an exact match |
| 29 | The first mux post-processing used 466.5 µV (the point-placement scale in `mc_window_check.json`) as the LSB and showed a false +2.4 %% gain | functional-bug (post-processing) | LSB 454.9 µV from the transition spacing of the locate run |
| 30 | Revision 4 reported IDD 2.29 / 1.51 / 3.42 mA (tt / ss / ff) from an unweighted mean over non-uniform time steps (`sim/r4/post_isa4.py`). The ngspice `meas avg` in the same logs gives 0.859 / 0.573 / 1.256 mA | numerical (post-processing) | `post_t2.py isa` uses a time-weighted average; it agrees with `meas` (0.903 mA in `t2-isa-tt`) |
| 31 | The bias pin was added during the campaign. Runs before the change carry `r1_adc_r5.spice` `a2c3c9a2…`, runs after it `340c0e6a…`. Only the `r1_refbuf5` port line, its internal source and comments differ (`sim/r5/refreeze_t2.py` checks this) | coordination | The freeze file keeps the previous hashes; the frozen-netlist check reports "frozen (previous freeze)" for them |
| 32 | Run `t2-dyn-ffm40-c0` is labelled failed: a singular-matrix warning at the operating point (node `xadc.xtha.xs0p.xm8`), resolved by dynamic gmin stepping; the transient ran to the end | numerical | Used, because chunk c1 (no warning) agrees within 0.2 dB; the label stays |

## Revision 4 (2026-10-21, schematic level)

Revision 4 is a new netlist and new decks next to revisions 1–3, which are unchanged. All numbers in this section
are **simulated** at schematic level with ngspice 46 unless they are marked *derived* or *estimated*. Nothing is
laid out or measured. It implements D18: the encoder pair {SIN, COS} is converted every 22-tick frame at 30 MHz,
one decision per tick (14 decisions), track ≥ 250 ns per slice; the current pair {ISA, ISB} replaces one encoder
frame per PWM period. Both slices convert in parallel with their own comparator and register. The two decisions
per tick of revision 3 and its undesigned 3 ns delay cell are removed. Kept from revision 3: CDAC (14 decisions),
reference buffer circuit, E-source decks, weight method W, D16 full scale.

### What changed

| Item | Revision 3 | Revision 4 |
| --- | --- | --- |
| Decision rate | two per tick (16.67 ns), comparator strobe 13.0 ns after evaluation start, local 3 ns delay cell (not designed) | one per clk30 tick (33.3 ns). Strobe at the next rising clk30 edge − 0.6 ns |
| Comparator clock | ideal `mclk` source from r1_ctrl | `r1_cmp4_clkgen` (new, transistor level): one-shot from the rising clk30 edge (5 inverters 0.5 µm long + NAND). Reset width 1.38 / 2.27 / 0.91 ns (tt / ss-125 °C / ff-−40 °C); the comparator evaluates for the rest of the tick: 31.35 / 30.46 / 31.82 ns to the strobe. r1_ctrl supplies clk30 and the strobes only |
| Comparator | `r1_cmp3` (c32c): 32 µm × 4 µm integration capacitors, reset NMOS 8 µm, `rppd` 1 × 160 µm bias | `r1_cmp4` (v80): 80 µm × 4 µm, reset NMOS 20 µm, same bias. Chosen in a 6-variant sweep with the clkgen clock (`sim/results/r4/cmp4_a.json`) |
| Frame | 36 ticks, two 18-tick slots, conversion 7.0 ticks, track 327 ns | 22 ticks: conversion 14 ticks (latch 14 T + 0.5 ns), track 8 T − 6 ns minus a 2 ns edge = 258.7 ns (simulated 257.8–259.5 ns, all corners); mux frames e/c per D18 |
| SAR logic | one strobe set for both slices | `r1_sar4_logic`: one strobe set per slice (`stba*`, `stbb*`), so slice B can run N ticks after slice A (R2-4 option 1) |
| LSB-array reference | VREF | port `vrefl` for the LSB-array drivers C7…C0 and the lsb-node reset (tied to VREF in all decks; R2-4 option 3 not run) |
| Reference buffer | `r1_refbuf3` | `r1_refbuf4`: same circuit, error-amplifier tail as parameters (`mt` fingers of 2 µm / `lt`). Chosen option: msf 32, mib 160, 6 decoupling cells, ncg 1, **mt 1, lt 8 µm** (tail ≈ 0.6 µA instead of 10 µA). **Recommended fix** (open issue 8): `r1_refbuf4h` without the input divider, plus a 10 pF input filter |
| MSB pre-switch (option, `schematic/r1_adc_r4p.spice`) | — | Both C12 bottom plates go to GND while decision 0 waits (top-plate CM about 0.1 V). Tested at ss and **rejected**: large inputs lose charge (status table). Not in the chosen design |
| Input common mode | 0.6 V | 0.6 V in all decks except one test. **Recommended: 0.45 V** (decision 0 at ss resolves; contract change for the AFE and isense outputs, not applied) |
| Simulator options | gmin default | gmin 1e-10 (R2-4 option runs, 64-input ss sweep) or 1e-9 (all runs from 23:45 CEST): the revision-4 operating point does not converge at the default 1e-12 (runs `r4-dbg-op-a…c`, `r4-dbg-opmc-a…c`) |

### Files (revision 4)

| Path | Content |
| --- | --- |
| `schematic/gen_r1_adc_r4.py`, `schematic/r1_adc_r4.spice`, `schematic/r1_adc_r4_mm.spice` | Generator and library: `r1_cmp4(_s1)`, `r1_cmp4_bias`, `r1_cmp4_clkgen`, `r1_th4`, `r1_th4_fast`, `r1_th4_fast_mc`, `r1_sar4_logic`, `r1_adc4_core`, `r1_adc4_core_fast`, `r1_adc4_core_fast_mc`, `r1_refbuf4`. Frozen for the campaign: sha256 in `sim/r4/FROZEN_NETLIST_SHA256.txt` |
| `schematic/gen_r1_adc_r4p.py`, `schematic/r1_adc_r4p.spice` | MSB pre-switch option: `r1_sar4p_logic`, `r1_adc4p_core_fast`, `r1_adc4p_core` (include after `r1_adc_r4.spice`) |
| `sim/r4/gen_timing_r4.py`, `sim/r4/r1_adc_timing_r4_*.inc` | Ideal D18 sources (clk30, windows, per-slice strobes, latches, track); `_n<N>` stagger N ticks; `_mux_n0` frames e c e e; `_cq` track falling 0.3 ns after the clock edge |
| `sim/r4/tb_adc4_points.cir`, `sim/r4/tb_adc4p_points.cir`, `sim/r4/tb_adc4h_points.cir`, `sim/r4/run_points4.py` | Held-input deck (one input per frame and slice; `--mc K` for MIM-mismatch instances); runner (resumes only after a numerical abort inside a later frame; stops on any other failure) |
| `sim/r4/tb_adc4_isa.cir`, `sim/r4/tb_adc4_dyn.cir` | D18 mux sequence with the full core and `r1_refbuf4`; dynamic deck (chunks of an N 256 record) |
| `sim/r4/gen_cmp4_decks.py`, `tb_cmp4_mem.cir`, `tb_cmp4_noise.cir`, `post_cmp4.py` | Comparator sweep: decision time and memory with the clkgen clock, noise (method A) |
| `sim/r4/post_ref4.py` | R2-4 metrics (see below) |
| `sim/r4/post_sweep4.py`, `post_win4.py`, `post_isa4.py`, `post_dyn4.py`, `p4common.py`, `sum_ref4.py` | Post-processors; `sum_ref4.py` collects the R2-4 options into `ref4_options.json` |
| `sim/r4/gen_points4.py`, `sim/r4/points/*.json` | Input sets: `ref10`, `ss_sweep64`, `ss_cm_test32`, `cornwin2/3`, `mcwin3`, `mcwin0` |
| `sim/r4/run_cmp4.sh`, `run_ref4.sh`, `run_queue_r4.sh`, `run_queue_r4b.sh` | Campaign helpers (CPU 103–105) |
| `schematic/gen_r1_refbuf4h.py`, `schematic/r1_refbuf4h.spice` | `r1_refbuf4h`: `r1_refbuf4` without the input divider (error-amplifier gate on vbg, vref = vbg); `r1_reffilt4`: input filter MIM w × w |
| `sim/r4/tb_refbuf4_noise.cir`, `sim/r4/post_refnoise4.py` | Reference DC and noise at the CDAC with a Thevenin model of r1_bgr (source R, spectrum from the r1_bgr results) |
| `sim/results/r4/` | Result JSON (all < 1 MB). Raw files: `<G1_RESULTS_ROOT>/r1_adc/<run-id>/`; run records `sim/runs/r4-*/run.json` |

### Built against (revision 4)

| Item | Value | How established |
| --- | --- | --- |
| PDK | IHP SG13G2 open PDK commit `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` | `flow/run.sh` commit check; `pdk_commit` in every `sim/runs/r4-*/run.json` |
| Container image | `sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2` | `container_image` in `run.json` |
| ngspice | ngspice-46 (creation date 27 Jul 2026), KLU, XSPICE, PSP 103.6 OSDI | `ngspice_version` in every `run.json` (established with `flow/run.sh ngspice -v` on 2026-10-20) |
| Netlist identity | `r1_adc_r4.spice` sha256 `22e53bb9…cb9f4` for the campaign (comparator and R2-4 option runs before the freeze carry their own sha256); `r1_adc_r4p.spice` separately | `netlist_sha256` in `run.json`; `sim/r4/FROZEN_NETLIST_SHA256.txt` |
| Models | `cornerMOSlv/hv.lib` `mos_tt` / `mos_ss` / `mos_ff`, `cornerCAP.lib` `cap_typ` / `cap_typ_mismatch`, `cornerRES.lib` `res_typ` | deck headers in `sim/runs/r4-*/deck.cir` |
| Options | `reltol=1e-4 vntol=1e-6 abstol=1e-12 method=trap klu rshunt=1e12`, gmin 1e-10 or 1e-9 (see above), tmax 0.2 ns, `interp` for code-only decks | `substitutions` in `run.json` |
| xschem, KLayout, LibreLane, CACE | not used | — |

### Status (revision 4, simulated at schematic level)

`<G1_RESULTS_ROOT>` is the results root of the campaign (raw files, not in git). Evidence paths are relative to this block directory.

| Item | Check | Result | Status | Evidence |
| --- | --- | --- | --- | --- |
| 1 R2-4 | Reference settling ≤ 0.25 LSB at ±0.88 V, buffer, both slices, tt | Chosen buffer: worst-case comparator input error 0.79 LSB, test-input error 0.33 LSB, code difference 2 LSB (gain). Best value of all options: 0.28 LSB (tail lt 32 µm, ncg 2). No option meets 0.25 LSB | **failed** | `sim/results/r4/ref4_options.json`, `ref4_tt_*.json`; runs `r4-ref-tt-*` |
| 1 R2-4 | Option 1: stagger (N = 2 ticks) | Worst-case error 4.21 LSB (worse than N = 0: 2.82 LSB with the same buffer) | **failed** | `sim/results/r4/ref4_tt_n2_buf32.json` |
| 1 R2-4 | Recommended fix `r1_refbuf4h` (no input divider) with the bandgap model (190 kΩ) and the 10 pF input filter, tt, gmin 1e-9 | vref 1.0507 V; worst-case 0.742 LSB, test-input 0.173 LSB, code diff 1 LSB, IDDA 0.843 mA | **failed** (same as the chosen cell; DC fixed) | `sim/results/r4/ref4_tt_n0_bufh.json`; runs `r4-ref-tt-n0-bufh-g9-*` |
| 1 R2-4 | Option 2: per-slice decoupling | — | not run | — |
| 1 R2-4 | Option 3: separate LSB-array reference (`vrefl`) | — | not run (port exists, tied to VREF) | — |
| 1 R2-4 | Chosen buffer at ss / 125 °C / 1.08 V and ff / −40 °C / 1.32 V (VDDA 3.3 V, gmin 1e-9) | ss: worst-case 0.714 LSB, test-input 0.293 LSB, code diff 2 LSB, IDDA 0.831 mA. ff: worst-case 0.858 LSB, test-input 0.309 LSB, code diff 0 LSB, IDDA 0.851 mA | **failed** (same as tt) | `sim/results/r4/ref4_ss125_n0_bufsel.json`, `ref4_ffm40_n0_bufsel.json`; runs `r4-refc-*` |
| 1 | Reference noise at the CDAC, 10 Hz–10 MHz, target 110 µV rms (0.25 LSB, coordinator 2026-10-21). r1_bgr spectrum (run `bgr-noise-20261021-b`) through the buffer, plus the buffer's own noise | Chosen `r1_refbuf4`: its input divider (≈ 344 kΩ) loads the unbuffered bandgap: vbg 1.045 → 0.673 V, vref 0.652 V with a 190 kΩ source (0.800 V with 90 kΩ). With the high-impedance input `r1_refbuf4h` and input filter Cf 10 pF (MIM 82 × 82 µm): tt 88.2 µV, ss / 125 °C 109.2 µV (190 kΩ source); 117.3 µV at ss with a 90 kΩ source. No filter: 111.6 / 133.2 µV. Buffer self-noise 63.1 / 75.9 µV (error-amplifier 1/f and white) | `r1_refbuf4`: **failed** (DC). `r1_refbuf4h` + 10 pF: **passed** at tt; ss **marginal** (passed at 190 kΩ, failed at 90 kΩ) | `sim/results/r4/refnoise4.json`; runs `r4-refn-*` |
| 2 R2-3 | Comparator noise ≤ 60 µV, ss / 125 °C, 33 ns tick | 55.9 µV (tt 44.9, ff 36.5 µV); method A, T_int = t_dec − 1 ns | **passed** | `sim/results/r4/cmp4_a.json` |
| 2 | Decision time, small input after a 30 mV input, all corners | tt 26.4 / 18.8 / 18.0 ns, ss — / 22.3 / 20.5 ns, ff 20.3 / 18.0 / 17.5 ns at CM 0.60 / 0.35 / 0.10 V; time to the strobe 31.35 / 30.46 / 31.82 ns | passed at CM ≤ 0.35 V; **failed** at ss, CM 0.6 V (0/8) | `sim/results/r4/cmp4_a.json` |
| 2 | Decision 0 at ss, CM 0.6 V, 64-input sweep | Decision 0 does not resolve for −40 mV ≲ Vin < 0; unresolved reads as 1. Inputs −19.1 mV (A) and −38.3 mV (B): error 27 and 70 LSB. The redundancy (≈ 30 LSB) does not cover it | **failed** | `sim/results/r4/sweep4_ss125.json`; run `r4-sweep-ss125` |
| 2 | Fix test: input CM 0.45 V, ss, 32 inputs (17 near the toggle) | Decision 0 resolves at all 17 near-toggle inputs; errors ≤ 2.2 LSB against the fit, ≤ 2.6 LSB against the nominal line over ±0.88 V; monotonic | **passed** (needs a contract change, see open issues) | `sim/results/r4/sweep4_ss125_cm045.json`; run `r4-sweep-ss125-cm045` |
| 2 | Fix test: MSB pre-switch (`r1_adc_r4p.spice`), CM 0.6 V, ss | Decision 0 resolves (near-toggle errors ≤ 4.3 LSB), but inputs beyond ±0.55 V lose charge: errors up to 108 LSB at ±0.88 V. Cause (not proven): the top plate goes below ground during decision 0 | **failed** (option rejected) | `sim/results/r4/sweep4_ss125_pre.json`; run `r4-sweep-ss125-pre` |
| 3 | Full D18 frame, mux sequence e c e e, full core `r1_adc4_core`, `r1_refbuf4`, tt | Codes in the correct order and frame (SIN/COS, then ISA/ISB ±0.85 V, then SIN/COS). Track 258.0 / 259.5 ns (B / A) ≥ 250 ns. Latch 14.02 ticks after the sampling edge. Errors against the nominal line ≤ 10.2 LSB, proportional to Vin: VREF 1.0052–1.0056 V (gain, not removed) | **passed** (sequence, track, latch) | `sim/results/r4/isa4_tt.json`; run `r4-isa-tt-cq2` |
| 3 | Mux sequence at ss / 125 °C / 1.08 V and ff / −40 °C / 1.32 V (same deck) | Codes in the correct order and frame at both corners; track ≥ 257.8 ns; latch 14.02 ticks. Errors ≤ 10.6 LSB (ss) and ≤ 8.5 LSB (ff) against the nominal line (gain, VREF 1.0055–1.0060 V). IDD 1.51 mA (ss) / 3.42 mA (ff), IDDA 0.83 / 0.84 mA | **passed** | `sim/results/r4/isa4_ss125.json`, `isa4_ffm40.json`; runs `r4-isa-ss125-cq2`, `r4-isa-ffm40-cq2` (`r4-isa-ss125-cq` stopped at its last time point, TSTOP 3.35 µs; rerun with 3.31 µs) |
| 4 R2-11 | Weight calibration on the circuit, MIM mismatch, ≥ 10 MC slice samples, reduced windows (±3.5 to ±5 LSB, 4 points per LSB), DNL at the major transitions | 12 slice samples (3 seeds × 2 instances × 2 slices). Design weights: max \|DNL\| 1.0 LSB, 8/12 ≤ 0.5 LSB, 2 non-monotonic, 5 missing codes. After the fit: max \|DNL\| 0.25 LSB (the resolution) on 12/12, monotonic, no missing code. Limitation: each sample fits one weight (W1 at the decision-1 transitions for 8 samples, W0 at the decision-0 transition for 4), because the first window set held no decision-0 toggle (failure 16). The fit and the DNL use the same conversions | **passed** (with the limitation) | `sim/results/r4/mc4_summary.json`, `mc4_tt_s11.json`, `mc4_tt_s12b.json`, `mc4_tt_s13w0.json`; runs `r4-mc-tt-s11`, `r4-mc-tt-s12b`, `r4-mc-tt-s13w0` |
| 5 | Static windows ss / 125 °C / 1.08 V (±6 LSB at codes 2048 and 3072, 2 points per LSB, ideal VREF) | Monotonic; max \|DNL\| 0.5 LSB (resolution 0.5 LSB). Slice A: code 3064 has no hit (width < 1 LSB; a DNL down to −1 is not excluded at this resolution) | **passed** (monotonic); missing-code check inconclusive | `sim/results/r4/win4_ss125.json`; run `r4-win-ss125` |
| 5 | Static windows ff / −40 °C / 1.32 V (same windows) | Monotonic; no missing code; max \|DNL\| 0.5 LSB (resolution 0.5 LSB), both slices | **passed** | `sim/results/r4/win4_ffm40.json`; run `r4-win-ffm40` |
| 5 | Dynamic, tt, N ≥ 256, fin 101.17 kHz (19/256 × frame rate; 100.6 kHz is not coherent), 0.85 V, `r1_refbuf4`, design weights, no device noise | Coherent FFT, 256 frames per slice: SNDR 63.05 / 63.03 dB (A / B), ENOB 10.18, SFDR 73.0 dB, THD −72.9 dB. Revision 3 (N 32) gave 70.9 dB. The loss matches the R2-4 reference-settling error (about 1 LSB rms); not separated further | **run** (no limit in the brief); below the 12-bit ideal (≈ 73 dB at this level) | `sim/results/r4/dyn4_tt_n256.json`; runs `r4-dyn-tt-c0…c2` |
| 5 | Dynamic at ss and ff | — | not run (time budget) | — |
| — | Full ramp, resistor corners, comparator offset MC with the clkgen, layout, PEX | — | not run | — |

### R2-4 options (tt, 10 test inputs at up to ±0.88 V, both slices at the same time, stagger 0 unless stated)

All values are simulated. "Worst-case" is the comparator input error 25 ns into each tick for decisions 5…13, taken along the common decision path. It bounds the conversion error over all inputs, because decisions 5…13 have only about 0.31 LSB of redundancy. The code difference includes the static VREF offset of the slow error amplifier (gain). Only rows with the same gmin can be compared (see open issue 3).

| Option | gmin | IDDA (mA) | Test-input error (LSB) | Code diff (LSB) | Worst-case (LSB) |
| --- | --- | --- | --- | --- | --- |
| buf32 (msf 32, mib 160), revision-3 error amplifier (tail 10 µA) | 1e-10 | 0.848 | 0.256 | 1 | 2.82 |
| buf64 (msf 64, mib 320), revision-3 error amplifier | 1e-10 | 1.671 | 0.040 | 1 | 1.31 |
| buf32, ncg 4 (four gate capacitors) | 1e-10 | 0.848 | 0.071 | 1 | 1.04 |
| buf32, stagger N = 2 (option 1) | 1e-10 | 0.847 | 2.26 | 2 | 4.21 |
| buf32, error-amplifier tail mt 1 / lt 8 µm (≈ 0.6 µA) | 1e-10 | 0.839 | 0.143 | 3 | 0.447 |
| buf32, tail lt 8 µm, ncg 2 | 1e-10 | 0.840 | 0.256 | 3 | 0.445 |
| buf64, tail lt 8 µm | 1e-10 | 1.663 | 0.105 | 3 | 0.423 |
| **chosen**: buf32, tail mt 1 / lt 8 µm, ncg 1, 6 decoupling cells (`r1_refbuf4` defaults) | 1e-9 | 0.839 | 0.333 | 2 | 0.79 |
| buf32, tail lt 32 µm, ncg 2 | 1e-9 | 0.839 | 0.533 | 2 | 0.276 |

Mechanism (from the waveforms): each CDAC switching event takes charge from VREF. The error amplifier integrates the dip onto the follower gate capacitor Cg. The gate then overshoots and decays with the loop time constant into the next decisions. The kick scales with gm_ea · Q / (gm_f · Cg). A slower error amplifier makes the kick smaller but gives a static offset. Stagger puts the switching of the other slice into the binary decisions of this slice, so it makes the error larger.

Choice (recorded, recommended option of the brief): buf32 with the slow tail, 0.84 mA. It is the lowest current, and its worst-case error is the smallest at 0.84 mA in the gmin-1e-10 set. The lt-32 µm row is better at gmin 1e-9 (0.28 LSB) but was found after the netlist freeze; it is the first candidate for revision 5. Both miss 0.25 LSB.

### Area and power (revision 4)

| Part | Area (mm², estimated) | Current (simulated, tt) |
| --- | --- | --- |
| CDAC, both slices (unchanged from revision 3) | 0.0185 | — |
| Comparators `r1_cmp4` × 2 + bias + clkgen | 0.003 | included in IDD |
| Switches, drivers, SAR logic (behavioural; area from revision 3) | 0.012 | included in IDD |
| Reference buffer `r1_refbuf4` (6 × 70 × 70 µm² Cd, 50 × 50 µm² Cg, devices) | 0.034 | IDDA 0.83–0.84 mA (3.3 V) |
| Recommended input filter Cf 10 pF (`r1_reffilt4`, MIM 82 × 82 µm; not in the chosen netlist) | 0.0067 | — |
| **Total** | **≈ 0.068** (0.075 with the filter) | IDD 2.29 mA at 1.2 V (full core, both slices, mux run `r4-isa-tt-cq2`); IDDA 0.83 mA |

Comparator supply alone (3 comparators + bias, continuous clock, `cmp4_a.json`): tt 2.60 mA, ss 1.36 mA, ff 4.63 mA. The area numbers are estimates from device sizes; nothing is laid out.

### Open issues (revision 4)

1. R2-4 is not met. The chosen buffer gives a worst-case comparator input error of 0.79 LSB (tt, simulated). The cause is the error-amplifier kick: the amplifier integrates each CDAC charge dip onto the follower gate. Options not run: per-slice decoupling (two buffers or two Cd banks) and a separate LSB-array reference (`vrefl` port exists). A third option is a reference that does not need a fast loop: a larger Cd with a slow loop and a calibrated gain.
2. The slow error amplifier (tail ≈ 0.6 µA) gives a static VREF offset of about +1.4 mV against the ideal operating point. This is a gain error (about 2–3 LSB at full scale). Gain calibration must remove it. Start-up and drift time of the slow loop are not simulated.
3. The result depends on gmin. With the same buffer, gmin 1e-10 and 1e-9 give 0.45 and 0.79 LSB worst-case error. Only same-gmin pairs are compared. The cause (numerical or a high-impedance node) is not known.
4. Decision 0 at ss / 125 °C / CM 0.6 V does not resolve for small negative inputs (errors up to 70 LSB). An input CM of 0.45 V fixes it (simulated, ss). This changes the AFE → ADC and isense → ADC contract (INTERFACES.md: output CM 0.6 V). The coordinator must decide. The MSB pre-switch is rejected. A comparator with a PMOS input pair is a third option (not designed).
5. Stagger (R2-4 option 1) makes the error larger: the other slice switches during this slice's binary decisions. Stagger is not used (N = 0).
6. The dynamic test uses fin = 19/256 × fs = 101.17 kHz, not 100.6 kHz (100.6 kHz is not coherent with N = 256).
7. Contract to r1_ctrl: clk30 rising edge resets the comparator (one-shot inside the ADC); per-slice strobes 0.6 ns before the next edge; the track edge comes from a flip-flop (clock-to-q 0.3 ns in the decks; an edge on the clock grid stops ngspice). Conversion = 14 ticks ≤ 17 (INTERFACES.md).
8. The chosen `r1_refbuf4` (and `r1_refbuf3` of revision 3) has a resistive input divider (≈ 344 kΩ, 3.0 µA from 1.045 V). The r1_bgr output is unbuffered (90–200 kΩ). Connected, vref falls to 0.65–0.80 V. All R2-4 decks used an ideal vbg source, so this was not seen. Recommended fix: `r1_refbuf4h` (no divider, vref = vbg ≈ 1.045–1.050 V, full scale +4.5 %, D16 to be confirmed) with the 10 pF input filter (≈ 0.0067 mm² MIM; pole 80 kHz with 190 kΩ, 160 kHz with 90 kΩ; settling time constant ≈ 2 µs at start-up). The R2-4 settling of `r1_refbuf4h` with the bandgap model is the same as the chosen cell (worst-case 0.742 LSB, status table).
9. Reference noise at ss is marginal (109–117 µV against 110 µV). About 76 µV comes from the buffer itself (error-amplifier input pair, 1/f below about 100 kHz). Larger error-amplifier input devices are the next step (not simulated). Noise below the frame rate is common to all decisions of a conversion and to both slices; for the encoder angle (SIN/COS ratio, same VREF, same sampling edge) it cancels to first order (not simulated). The 110 µV target over 10 Hz–10 MHz is therefore a bound.
10. Not designed or not simulated: layout, PEX, resistor corners (`res_typ` only), the full ramp, MC of the comparator offset with the clkgen.

### Failures and mistakes (revision 4)

| # | What happened | Class | Effect and fix |
| --- | --- | --- | --- |
| 1 | The comparator post-processor read the tick parity inverted (big and small inputs swapped); every variant showed 0/8 correct | functional-bug (post-processing) | Found from the waveforms; parity fixed in `post_cmp4.py`; sweep re-posted |
| 2 | The first R2-4 metric read the residue inside the reference dip and took the bits from the step signs: 10–20 LSB "errors" with codes within 1 LSB | verification-gap | Late residue (ts + 14 T + 5 ns) and bits from the SAR register (`post_ref4.py`) |
| 3 | The first mid-evaluation error scaled the whole differential voltage by the decision-1 step: 2.8 LSB artefact | numerical (post-processing) | Exact form V_b − (V_i − (v1 − 1) · S_k) |
| 4 | The revision-4 operating point did not converge at the default gmin (5 runs). MC decks and one ideal run also failed at 1e-10 | numerical | gmin 1e-10, then 1e-9 for all later runs (debug runs `r4-dbg-op-*`, `r4-dbg-opmc-*`). The R2-4 result depends on gmin (open issue 3) |
| 5 | The runner resubmitted a deterministic abort 7 times and skipped frames (`r4-ref-tt-n2-ideal1004-r1…r7`) | tooling | `run_points4.py` stops on an abort in the first frame of a segment; those runs are not used |
| 6 | Full-core mux deck stopped at the sampling edge (edge on the clock grid), then at a PWL corner on the clock edge | numerical | `_cq` timing (track edge 0.3 ns after the clock edge, as a flip-flop does) and PWL corners off the grid (`r4-isa-tt-cq2`) |
| 7 | `run_ngspice.py` returns 0 when ngspice fails; the queue recorded the failed mux run as rc 0 | tooling | `run_queue_r4b.sh` checks `status` in `run.json` |
| 8 | Queue scripts were edited while queues ran; one running shell read the changed file and reported a syntax error after its last job | process-hygiene | No job was lost; edit copies, not running scripts |
| 9 | Stagger (option 1) was expected to help and made the error larger | estimation | Recorded as a result; the mechanism is in "R2-4 options" |
| 10 | The MSB pre-switch fixed decision 0 but broke large inputs (up to 108 LSB) | functional-bug (design option) | Option rejected; CM 0.45 V recommended instead |
| 11 | Decision 0 at ss / CM 0.6 V was assumed to be covered by the redundancy (revision 3) | spec-ambiguity | The 64-input sweep shows that it is not (70 LSB); fix needs a CM contract change |
| 12 | The plan (3 dynamic chunks, 10 MC samples, mux at ss/ff, all R2-4 options) did not fit 4 h on 3 CPUs | planning | Items recorded as not run; MC with fewer samples (see status) |
| 13 | The CM 0.6 V comparator test at ss was cancelled to free a CPU | planning | Run `r4-sweep-ss125-cm060` labelled cancelled; the 64-input sweep answers the question |
| 14 | `.meas` of i(vdd) fails in code-only decks (the vector is not saved); the log shows an error line but the run completes | tooling | Harmless; current is taken from the full-save runs |
| 15 | The buffer input divider (from revision 2/3) loads the unbuffered bandgap; every R2-4 deck used an ideal vbg source, so the 35 % vref drop was found only by the coordinator's noise request | coordination | `r1_refbuf4h` defined and simulated for DC and noise (open issue 8); R2-4 transient with `r1_refbuf4h` run (`r4-ref-tt-n0-bufh-g9-*`) |
| 16 | The MC window for the decision-0 toggle was placed at the revision-3 level (−4.20 mV). In revision 4 the toggle is above −2.6 mV, so the window held no toggle and the top-2 fit was singular (W0 = −75) | verification-gap | Window 0 still counts for DNL; W1-only fit for seeds 11/12; new window `mcwin0.json` around −1.0 mV for seed 13 (W0-only fit) |

## Revision 3 (2026-10-20, schematic level)

Revision 3 is a new netlist and new decks next to revisions 1 and 2, which are unchanged. All numbers in this
section are **simulated** at schematic level with ngspice 46 unless they are marked *derived* (behavioural model
fed with simulated data) or *estimated*. Nothing is laid out or measured. It implements D16 (full scale ±0.9 V,
VREF unchanged) and D17 (14 decisions, two slices converting in parallel with their own comparator and register,
36-tick frame at 30 MHz: {SIN, COS} slot then {ISA, ISB} slot, host-loaded weights `w[13:0]`).

### What changed

| Item | Revision 2 | Revision 3 |
| --- | --- | --- |
| Decisions | 13 (12 + 1 redundant) | 14 (12 + 2 redundant, D17). The LSB array gets a half unit C0 (`cap_cmim` 2.67 × 2.67 µm, ≈ 0.505 Cu). Raw step ≈ 0.31 LSB. Nominal weights (LSB): 2032.4 1016.3 507.9 253.9 127.0 78.8 39.4 19.7 9.85 4.93 2.46 1.23 0.62 0.31 |
| Frame | one pair per 30-tick frame, slices one after the other | 36-tick frame = two 18-tick slots. Both slices sample on one edge and convert in parallel. Decisions at two per tick (16.67 ns): comparator evaluates 13.5 ns, strobe 13.0 ns after the start of evaluation, 3.2 ns reset. Conversion 7.0 ticks (latch at 233 ns), track window 327 ns (slice B 325.5 ns) in every slot |
| Comparator | `r1_cmp2`, 16 µm × 4 µm integration capacitors, ideal 14 µA bias | `r1_cmp3`: 32 µm × 4 µm integration capacitors, reset NMOS 8 µm, bias `r1_cmp3_bias` = diode PMOS + `rppd` 1 × 160 µm to ground (I ∝ VDD − Vsg, so the integration time stays 9.4–10.2 ns over tt / ss-125 °C / ff-−40 °C) |
| Reference buffer | `r1_refbuf` msf 16, mib 80, 44 pF | `r1_refbuf3` (same circuit, new defaults msf 32, mib 160, 44 pF; see the status table for the measured options) |
| Input sources in the decks | B sources | linear E sources around a common-mode V source (R2-7) |
| Timing edges | — | track start 2 ns rise, 6 ns after a clk30 edge, slice B 1.5 ns after slice A (an edge on the clock grid stopped ngspice, see "Failures and mistakes") |

**Frame arithmetic (spec-ambiguity, recorded).** INTERFACES.md asks for conversion ≤ 17 ticks and a track window
≥ 250 ns for both slices in a 36-tick frame. Each slice converts twice per frame, so 2 × (conversion + track) ≤ 36
ticks and the track window forces conversion ≤ 10.5 ticks. With one decision per tick (14 ticks) this is
impossible. Revision 3 takes two decisions per tick (both clk30 edges; strobes from `r1_ctrl` as before, plus a
local ≈ 3 ns delay cell in the ADC for the evaluate/reset split, not designed). The binding number for `r1_ctrl`
is therefore "conversion ≤ 10.5 ticks"; the revision-3 value is 7.0 ticks.

### Files (revision 3)

| Path | Content |
| --- | --- |
| `schematic/gen_r1_adc_r3.py` | Generator (imports the unchanged switch and driver cells of `gen_r1_adc_r2.py`). Writes the two libraries below. |
| `schematic/r1_adc_r3.spice`, `schematic/r1_adc_r3_mm.spice` | `r1_cdac3_side(_mc)`, `r1_cmp3_s1`, `r1_cmp3`, `r1_cmp3_bias`, `r1_cmp3_ibias`, `r1_th3(_fast)`, `r1_sar3_logic`, `r1_adc3_core`, `r1_adc3_core_fast`, `r1_refbuf3` |
| `sim/r3/gen_timing_r3.py`, `sim/r3/r1_adc_timing_r3*.inc` | Ideal D17 frame sources (VDD 1.2 / 1.08 / 1.32 V; `_mux` = SIN/COS in even slots, ISA/ISB in odd slots) |
| `sim/r3/tb_adc3_points.cir`, `sim/r3/run_points3.py` | Both slices, one held input per slot and slice (static windows, reference runs); runner with abort/resume and `<id>_segments.json` |
| `sim/r3/tb_adc3_dyn.cir`, `sim/r3/tb_adc3_isa.cir` | Sine/cosine dynamic deck; mux sequence with the full core |
| `sim/r3/gen_cmp3_decks.py`, `tb_cmp3_tran*.cir`, `tb_cmp3_noise*.cir`, `gen_cmp3_hyst.py`, `tb_cmp3_hyst*.cir` | Comparator sweeps (sets a, b, c), noise (method A of revision 2) and the memory (hysteresis) test |
| `sim/r3/gen_tb_cdac3_mc.py`, `tb_cdac3_mc.cir`, `post_cdac3_mc.py` | CDAC MIM-mismatch MC, 50 samples, AC-solved weights |
| `sim/r3/cal3.py`, `sim/r3/study_cal3_model.py` | Weight calibration methods G (global ramp, revision 2) and W (windowed, revision 3); MC study |
| `sim/r3/post_*.py`, `p3common.py`, `run_queue_r3.sh` | Post-processors and the run queue |
| `sim/r3/points/*.json` | Input levels per slot: smoke, reference (`ref10`), code windows (`calwin`, `cornwin`), locate ramps (`locate`), toggle windows (`togwin`) |
| `sim/results/r3/` | Result JSON (all < 1 MB). Raw files: `<G1_RESULTS_ROOT>/r1_adc/<run-id>/`; run records `sim/runs/r3-*/run.json` |

### Built against (revision 3)

| Item | Value | How established |
| --- | --- | --- |
| PDK | IHP SG13G2 open PDK commit `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` | `flow/run.sh` commit check; `pdk_commit` in every `sim/runs/r3-*/run.json` |
| Container image | `sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2` | `container_image` in `run.json` |
| ngspice | ngspice-46 (creation date 27 Jul 2026), KLU, XSPICE, PSP 103.6 OSDI | `flow/run.sh ngspice -v` on 2026-10-20; `ngspice_version` in every revision-3 `run.json` |
| Netlist identity | sha256 of `r1_adc_r3.spice` at run start | `netlist_sha256` in `run.json` |
| Models | `cornerMOSlv/hv.lib` `mos_tt` / `mos_ss` / `mos_ff`, `cornerCAP.lib` `cap_typ` / `cap_typ_mismatch`, `cornerRES.lib` `res_typ` | deck headers in `sim/runs/r3-*/deck.cir` |
| Options (conversion decks) | `reltol=1e-4 vntol=1e-6 abstol=1e-12 method=trap klu rshunt=1e12`, tmax 0.2 ns (revision-2 finding), `interp` for code-only decks | `substitutions` in `run.json` |
| xschem, KLayout, LibreLane, CACE | not used | — |

### Status (revision 3)

tt = `mos_tt`, `cap_typ`, 27 °C, VDD 1.2 V; ss = `mos_ss`, 125 °C, 1.08 V; ff = `mos_ff`, −40 °C, 1.32 V. Conversion
decks use the fast core (ideal 400 Ω drivers, off-switch in1) unless the full core is named. Resistor corners
(`res_bcs`/`res_wcs`) were not run for the comparator bias.

| Item | Requirement | Result | Status | Evidence |
| --- | --- | --- | --- | --- |
| D16 full scale | ±0.9 V with VREF 1.0 V | LSB 446.4 µV, full scale ±0.914 V (tt, static windows); AC model 0.877 V with 100 fF top-plate parasitic | passed (tt) | `sim/results/r3/win_tt.json`, `sim/results/r3/cdac3_mc50_tt_cp100_globalfit.json` |
| R2-4 reference settling | code error ≤ 0.25 LSB at ±0.88 V, `r1_refbuf3` in the loop, both slices | Best option buf64 (msf 64, mib 320, 6 decoupling cells, 44 pF): code difference to an ideal 1.004 V source ±1 LSB over 10 slots, residue error 0.38 LSB. buf32: ±3 LSB; buf16: ±4 LSB; buf32 with 18 cells (132 pF): ±3 LSB; buf64 with 12 cells (88 pF): ±1 LSB, 0.46 LSB. The dominant disturbance is the LSB-array switch at decision 5 (≈ 0.7 pC per side, both slices at the same time) | **failed** | `sim/results/r3/ref3_tt_buf{16,32,32n18,64,64n12}.json`; runs `r3-ref-tt-*-d` |
| R2-3 comparator noise | ≤ 60 µV rms at ss / 125 °C | `r1_cmp3` (c32c): tt 57.5 µV, ff/−40 °C 45.3 µV, ss/125 °C 75.7 µV. Best variant of the sweep at ss: ≈ 64 µV (larger capacitors and input pair), which does not fit the 13 ns strobe | **failed** at ss; passed tt, ff | `sim/results/r3/cmp3_noise_cm01_all{,_b,_c}.json` |
| R2-3 decision time inside the strobe (13.0 ns) | all corners | 30 mV then −0.2 mV, alternating, 6 decisions: CM 0.1 V: 9.44 / 10.17 / 9.52 ns (tt / ss / ff); CM 0.35 V: 9.74 / 10.81 / 9.70 ns; CM 0.6 V: 12.42 ns / not resolved / 10.46 ns. CM 0.6 V only occurs at decision 0, which has 30 LSB (13 mV) redundancy. The ss static window at code 2048 is monotonic without missing codes | passed at CM ≤ 0.35 V; **failed** at ss for CM 0.6 V (decision 0, covered by redundancy, not proven for all inputs) | `sim/results/r3/cmp3_hyst_{tt27,ss125,ffm40}_d.json`, `sim/results/r3/win_ss125.json` |
| R2-3 decision memory | no wrong small decision after a large one | c32c: 6/6 correct at all corners and CM ≤ 0.35 V (the first choice r80b failed, see below) | passed | `sim/results/r3/cmp3_hyst_*_d.json` |
| R2-11 calibration: widths of codes 1024 / 2048 / 3072 within 0.5 LSB | MC ≥ 30 | Method W on 50 MC weight sets (derived: circuit-MC weights + behavioural model, noise 67 µV, kT/C 101 µV, 1 LSB INL bow): max DNL median 0.31, worst 0.44 LSB, 50/50 ≤ 0.5 LSB; major codes ≤ 0.31 LSB; INL max median 1.28 LSB (bow stays); 50/50 without missing codes. Method G (revision 2) under the same bow: major DNL median 1.25, 0/50 pass | passed (derived) | `sim/results/r3/cal3_mc50_tt_cp100.json` |
| R2-11 circuit-level demo | weights fitted on circuit data, tt | Toggles located (coarse 0.4 mV ramp): decision 0 at −4.20 mV, decision 1 at ±455.3 mV, same for both slices. Windows ±4 LSB, 4 points per LSB, around each toggle. Reduced fit (W0, W1, gain; lower weights kept at design values): W0 16259 (design 16259), W1 8129 (design 8131) in 1/8 LSB, both slices. Codes 2047/2048/3071 with fitted weights: |DNL| ≤ 0.25 LSB (resolution 0.25 LSB), monotonic, no missing codes in all windows, both slices. Nominal circuit only (no mismatch), so this checks the procedure, not the MC spread | passed (reduced: 3 windows, top-2 weights, no mismatch) | `sim/results/r3/cal3_circuit_tt.json`; runs `r3-loc-tt-c*`, `r3-tog-tt-c*`, `r3-cal-tt-c*` |
| R2-7 input sources | E sources, tmax 0.2 ns, reltol kept | All revision-3 conversion decks use linear E sources around a CM source; options unchanged | passed | `sim/r3/tb_adc3_points.cir`, `tb_adc3_dyn.cir`, `tb_adc3_isa.cir` |
| D17 track window | ≥ 250 ns, both slices | 325.1–325.2 ns slice A, 323.6–323.7 ns slice B, every slot (full core) | passed | `sim/results/r3/isa3_tt.json`; run `r3-isa-tt-a` |
| D17 conversion time | ≤ 17 ticks (binding: ≤ 10.5 ticks, see frame arithmetic) | 7.0 ticks (latch 233 ns after the edge) | passed | `sim/results/r3/isa3_tt.json` |
| D17 mux sequence | {SIN, COS} then {ISA, ISB}, correct codes | 5 slots, encoder ±0.4 / ±0.72 V and current ±0.85 V (CM 0.57 V): all codes within −2.1…+3.1 LSB of the ideal code from LSB 446.4 µV (gain and offset, removed by the bench calibration); iref 5.45 µA, IDD 449 µA | passed | `sim/results/r3/isa3_tt.json` |
| Static windows, tt | monotonic, no missing codes, design weights | ±4 LSB at codes 1024 / 2048 / 3072, 4 points per LSB: major |DNL| ≤ 0.25 LSB, monotonic, no missing codes, both slices | passed | `sim/results/r3/win_tt.json`; runs `r3-cal-tt-c*` |
| Static windows, ss/125 °C/1.08 V | same | ±4 LSB, 2 points per LSB: monotonic, no missing codes, |DNL| ≤ 0.5 LSB (resolution 0.5 LSB), both slices; windows shift by ≈ 4 LSB | passed | `sim/results/r3/win_ss125.json`; runs `r3-win-ss125-c*` |
| Static windows, ff/−40 °C/1.32 V | same | same as ss | passed | `sim/results/r3/win_ffm40.json`; runs `r3-win-ffm40-c*` |
| Full static ramp (all 4096 codes) | — | — | not run | — |
| Dynamic, tt | one run | N 32, 3 cycles, fin 156.25 kHz, 0.85 V, design weights, no device noise: SNDR 70.90 dB, ENOB 11.49, SFDR 75.27 dB, THD −74.23 dB, codes 152…3943; slices A and B identical (same phase grid) | passed (one run, N 32) | `sim/results/r3/dyn3_tt_n32.json`; run `r3-dyn-tt-n32` |
| Dynamic, ss and ff; N 1024 | — | — | not run | — |
| Reference buffer at ss / ff | — | — | not run | — |
| Resistor corners of the comparator bias | — | — | not run | — |
| Mux sequence at ss / ff | — | — | not run | — |
| Layout, DRC, LVS, PEX | — | — | not run | — |

### Weight calibration: bench procedure for `r1_ctrl` (R2-11)

Method W (`sim/r3/cal3.py`). Per slice, input from the bench DAC through the normal input path, ideal VREF not
needed (the gain is set by ΣW = 4095):

1. Coarse ramp over ±0.995 full scale, 1 conversion per LSB. Record the raw 14 bits. Find the input levels where
   decisions 0…4 change, and 6 levels each where decisions 5…8 change (≈ 81 levels).
2. Fine ramp of ±12 LSB around each level, 8 conversions per LSB (≈ 19 600 conversions per slice, ≈ 12 ms at
   1.67 MS/s per slice).
3. Least squares of the ramp position against [one offset per window, b0…b13]. The per-window offsets absorb
   the slow INL bow of the sampling network.
4. Scale the 14 weights to ΣW = 4095 LSB, quantise to 1/8 LSB (14 bit), load them in `w[13:0]`.
5. Do steps 1–4 for slice A and slice B. Each slice needs its own 14 weights (2 × 14 registers): this is a
   contract change for `r1_ctrl` and INTERFACES.md (open issue).

Model result (derived, 50 MC samples): see the status table. Circuit demo (tt, reduced): toggles located with a coarse ramp (runs `r3-loc-tt-c*`), three fine windows on the decision 0 and 1 toggles (runs `r3-tog-tt-c*`), top-2 fit, evaluation on the code windows `r3-cal-tt-c*`. The fitted W0/W1 agree with the design weights within 2/8 LSB and the major codes stay within 0.25 LSB. The full 81-window procedure on the circuit is **not run**.

### Area and power (revision 3)

| Part | Area (mm², estimated) | Current |
| --- | --- | --- |
| CDAC, two slices × two sides, MIM | ≈ 0.0185 | — |
| Comparators (2) and bias | ≈ 0.0025 | in the VDD current below |
| Switches, bootstrapped switches, drivers, SAR registers | ≈ 0.012 | in the VDD current below (SAR logic behavioural, not counted) |
| `r1_refbuf3`, buf64 option (6 × 70 × 70 µm decoupling, 50 × 50 µm gate capacitor, follower) | ≈ 0.037 | VDDA 1.65 mA at 3.3 V (simulated); buf32 option 0.84 mA |
| **Total** | **≈ 0.070** | VDD 0.446–0.459 mA at 1.2 V (simulated, fast core, both slices, tt; full core 0.449 mA in the mux deck) + SAR logic (not simulated) |

Areas are estimated from device sizes, without layout. Currents are simulated at tt only.

### Open issues (revision 3)

1. **R2-4 fails.** The best buffer option (buf64, 1.65 mA) gives ±1 LSB code error, not 0.25 LSB. A larger
   buffer does not converge fast enough. A fix needs an architecture change: a separate reference for the LSB
   array, a per-slice decoupling capacitor that is charged in track, or a time offset between the two slices
   at decision 5.
2. **R2-3 fails at ss/125 °C** (75.7 µV against 60 µV). A lower-noise comparator needs more time than the
   13 ns strobe of the two-decisions-per-tick frame. Options: a pre-amplifier, or accept the noise with the
   2 redundant decisions and a calibration that averages (record as a spec decision).
3. Decision 0 at ss with CM 0.6 V does not resolve a −0.2 mV input inside the strobe. The 30 LSB redundancy
   covers it if larger inputs resolve; this is not proven for all inputs.
4. The local ≈ 3 ns delay cell for the evaluate/reset split is not designed.
5. INTERFACES.md: conversion must be ≤ 10.5 ticks (not 17), two decisions per tick, and 2 × 14 weights (one set
   per slice). `r1_ctrl` must agree.
6. Resistor corners (`res_bcs`/`res_wcs`) of the `rppd` comparator bias are not run.
7. R2-8 (logic supply noise on the comparator and the SAR logic) still applies; the SAR logic is behavioural.
8. Not run: full static ramp, dynamic at N 1024 and at ss/ff, reference buffer and mux sequence at ss/ff,
   layout, DRC, LVS, PEX.

### Failures and mistakes (revision 3 session)

| # | What happened | Class | Effect and fix |
| --- | --- | --- | --- |
| 1 | INTERFACES.md asks for ≤ 17-tick conversion and ≥ 250 ns track in a 36-tick frame with two conversions per slice. This needs ≤ 10.5 ticks, which one decision per tick cannot meet. | spec-ambiguity | Two decisions per tick chosen and recorded; contract change open. |
| 2 | The track-start edge sat on a clk30 edge. ngspice stopped with "timestep too small" at 867.667 ns (node `topbp`). A slower rise and a slice-B offset did not help. | numerical | Runs `r3-smoke-tt-a…c`, `r3-smoke-tt-full-c`, `r3-ref-tt-ideal-a` aborted. Track start moved 6 ns off the clock grid. |
| 3 | Multi-line `@REFLINES@`/PWL substitutions also replaced the tokens in deck comment lines and broke the netlist. | process-hygiene | Runs `r3-ref-tt-*-b*` invalid. Tokens removed from comments. |
| 4 | The runner skipped a slot and resubmitted (`-r1`, `-r2`) on a netlist error instead of stopping. | tooling | Wasted CPU time; recorded, runner not changed. |
| 5 | First comparator choice r80b (wide capacitors, 2 µm reset NMOS) had decision memory: wrong decisions on inputs up to 18 mV. The constant-input transient bench did not show it. | verification-gap | Runs `r3-smoke-tt-d`, `r3-smoke-tt-full-d`, `r3-ref-tt-*-c` superseded. Memory test added; c32c with 8 µm reset NMOS chosen. |
| 6 | The first memory-test generator filtered out the clock sources; the second put 12 comparators on one bias node. | functional-bug | Runs `r3-cmp-hyst-*-a`, `-b` invalid; set d uses one bias per comparator. |
| 7 | I assumed the comparator noise falls with the integration capacitance. It saturates at ≈ 64 µV at ss. | estimation | R2-3 fails; time spent on the sweep. |
| 8 | Reference-error metric: first a wrong normalisation, then the ideal 1.0 V run mixed in the 0.4 % static VREF error of the buffer (7.9 LSB at full scale). | numerical | Ideal run repeated at 1.004 V. The residue metric is not reliable where decision paths differ; the code difference is the reported number. |
| 9 | The behavioural calibration with windows only at decisions 0…4 gave a singular fit. | planning | K = 6 windows for decisions 5…8 and h = 12 added. |
| 10 | The circuit calibration windows were centred on the codes, not on the decision toggles (which sit 9 LSB away). The top-2 fit gave nonsense (W0 = 3853). | planning | Result discarded; locate runs `r3-loc-tt-c*` and toggle windows `r3-tog-tt-c*` added. |
| 11 | Corner windows used the tt LSB. At ss/ff the codes 1023/3072 sat at the window edges. | planning | Those codes are not evaluated at ss; recorded. |
| 12 | Run-cost estimate from the smoke runs (≈ 3.5 min per slot) was too high by 4–10 ×. | estimation | Fewer corner and dynamic runs were planned than the CPUs allowed. |

## Revision 2 (2026-10-20, schematic level)

Revision 2 is a new netlist next to revision 1. Revision 1 (sections "What it is" to "Open issues" below) is
unchanged. All numbers in this section are **simulated** at schematic level unless they are marked *derived*.
Nothing is laid out or measured.

### What changed

| Item | Revision 1 | Revision 2 |
| --- | --- | --- |
| Full scale, reference | ±1.163 V from VREF 1.2 V | ±0.919 V (simulated) from VREF 1.0 V (D11 asks ±1.0 V, see issue R2-1) |
| Decisions, raw output | 12, binary | 13 (12 + 1 redundant), 13 raw bits `rawA/rawB`; code = sat12((Σ b_j·W_j + 4) >> 3), W = 14-bit weights in 1/8 LSB (D12) |
| CDAC (per side) | 6+6 bridge, 95 units | sub-binary split array, 22.04 fF unit kept: top 16, 8, 4, 2, 1 Cu; bridge 1.249 Cu (4.23 × 4.23 µm); LSB array 64, 32, 16, 8, 4, 2, 1 Cu; 159.25 units. Each top decision and the bridge have +31 LSB redundancy |
| Comparator | PMOS pair 16/0.2 µm, switch tail | `r1_cmp2`: PMOS pair 48/0.3 µm (12 fingers), current-source tail (≈ 280 µA in evaluation, bias `r1_cmp2_bias` 14 µA), 2 × 16/4 µm MOS integration capacitors |
| SAR logic | P/N flags | P/N flags; a metastable decision (no output at the strobe) switches the N side (N = V AND NOT P) |
| Reference | ideal source | `r1_refbuf`: 1.0 V from the 1.045 V bandgap node (ideal source in the decks), 3.3 V thick-oxide error amplifier and NMOS follower, 44 pF MIM decoupling |
| Timing | 12 + 12 cycles, track 6 cycles | A converts in cycles 0–12 (13 cycles, ≤ 15 per INTERFACES.md), B in 13–25; A tracks 17 T (567 ns), B tracks 4 T (132 ns) |

### Files (revision 2)

| Path | Content |
| --- | --- |
| `schematic/gen_r1_adc_r2.py` | Generator; all revision-2 sizes. Writes the two libraries below. |
| `schematic/r1_adc_r2.spice`, `schematic/r1_adc_r2_mm.spice` | `r1_cdac2_side(_mc)`, `r1_cmp2_s1`, `r1_cmp2`, `r1_cmp2_bias`, `r1_th2(_fast)`, `r1_sar2_logic`, `r1_adc2_core`, `r1_adc2_core_fast`, `r1_adc2_core_fast_a`, `r1_refbuf`; `_mm` adds `mm_ok={mmos}` to every MOS. |
| `sim/r2/gen_timing_r2.py`, `sim/r2/r1_adc_timing_r2*.inc` | Ideal timing sources (VDD 1.2 / 1.08 / 1.32 V; `_mux` without track sources). |
| `sim/r2/tb_adc2_static.cir`, `tb_adc2_dyn.cir`, `tb_adc2_quick.cir`, `tb_adc2_isa.cir`, `tb_adc2_ref.cir` | Conversion decks: ramp, sine, held frames, mux sequence with the current inputs, reference buffer in the loop. |
| `sim/r2/tb_cmp2_tran.cir`, `tb_cmp2_noise.cir`, `tb_cmp2_offset_mc.cir` (+ generators) | Comparator decision time, noise PSD, offset MC. |
| `sim/r2/tb_cdac2_mc.cir`, `gen_tb_cdac2_mc.py` | CDAC MIM-mismatch MC (AC-solved weights, 50 samples). |
| `sim/r2/tb_refbuf_pulse.cir`, `refbuf_load.inc` | Reference buffer with the CDAC charge as a current-pulse train. |
| `sim/r2/sar2_model.py` | Python model: conversion with weights, ramp weight extraction (least squares), 14-bit quantisation, correction, DNL/INL. |
| `sim/r2/post_adc2.py`, `post_cdac2_mc.py`, `post_cmp2_tran.py`, `post_cmp2_noise.py`, `post_cmp2_mc.py`, `post_refbuf.py`, `post_ref_adc.py`, `array_sweep.py` | Post-processors. |
| `sim/r2/run_static2.py` | Runs a ramp, window or sine deck and restarts after a numerical abort; writes `sim/results/r2/<id>_segments.json`. |
| `sim/r2/dbg_*.cir` | Debug decks of the simulator-accuracy finding (below). |
| `sim/results/r2/` | Results JSON. Raw files: `<G1_RESULTS_ROOT>/r1_adc/<run-id>/`. |

### Built against (revision 2)

| Item | Value | How established |
| --- | --- | --- |
| PDK | IHP SG13G2 open PDK commit `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` | `flow/run.sh` check; `pdk_commit` in every `sim/runs/r2-*/run.json` |
| Container image | `sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2` | `container_image` in `run.json` |
| ngspice | ngspice-46 (creation date 27 Jul 2026), KLU, XSPICE `digital.cm`, PSP 103.6 OSDI | `flow/run.sh ngspice -v` in the same container on 2026-10-20 (the run logs are cut and hold no banner) |
| Models | `cornerMOSlv.lib` and `cornerMOShv.lib` (`mos_tt` / `mos_ss` / `mos_ff` / `mos_tt_mismatch`), `cornerCAP.lib` (`cap_typ` / `cap_typ_mismatch`), `cornerRES.lib` `res_typ` | deck headers in `sim/runs/r2-*/deck.cir` |
| Simulator options (conversion decks) | `reltol=1e-4 vntol=1e-6 abstol=1e-12 method=trap klu rshunt=1e12`, tmax 0.2 ns | `substitutions` in `run.json` |
| xschem, KLayout, LibreLane, CACE | not used | — |

How to run (block directory, CPU set of track T2):

```
G1_RESULTS_ROOT=<bulk results root>; export G1_RESULTS_ROOT
python3 schematic/gen_r1_adc_r2.py
python3 sim/r2/run_static2.py --id <id> --cpu 103 --corner mos_tt --temp 27 --vdd 1.2 \
  --timing r1_adc_timing_r2.inc --vstart -0.955 --vstep 3.178e-3 --frames 301
sh sim/r2/post_r2_all.sh
```

### Simulator accuracy (finding, applies to every conversion deck)

With `reltol=1e-3` and `tmax 5 ns`, ngspice gave wrong comparator decisions for residues up to ≈ 6 mV
(13 LSB). With `reltol=1e-4` and `tmax 5 ns` the error was ≈ 0.3–0.5 mV. The same input gave different codes in
two frames. Runs `r2-dbg-probe-c2048`, `r2-dbg-cmptol-*`, `r2-dbg-cmphyst-*`, `r2-dbg-probe1024-*` show this.
The stand-alone comparator with tight options has no memory at ±100 µV (`r2-dbg-cmphyst-tight`).
All revision-2 conversion results below use `reltol=1e-4 vntol=1e-6 abstol=1e-12 method=trap klu rshunt=1e12`
and `tmax 0.2 ns`. These give the same decisions as `reltol=1e-5` (`r2-dbg-probe1024-r5`).
Earlier conversion runs are marked *invalid* or *superseded* in their `run.json` and are not used.

### Status (revision 2)

tt = `mos_tt`, `cap_typ`, 27 °C, VDD 1.2 V, VREF 1.0 V (ideal) unless stated. Conversion decks use the fast core
(ideal 400 Ω bottom-plate drivers, `r1_th2_fast`) except the ISA deck, which uses the full core.

| Goal | Check | Status | Number (simulated unless marked) | Evidence |
| --- | --- | --- | --- | --- |
| 1 | Full scale ±1.0 V from VREF 1.0 V (D11) | **failed** | ±0.919 V differential, LSB 448.6 µV, mid-scale offset −0.11 mV (tt ramp, ramp-calibrated weights). Cause: comparator input (≈ 84 fF) and top-plate parasitics attenuate the CDAC (see issue R2-1) | `sim/results/r2/ramp_tt.json`; runs `r2-ramp-tt-a-f1*`, `r2-ramp-tt-a-f2*` |
| 1 | kT/C with the new array | passed (*derived*) | top node ≈ 0.71 pF + 0.1 pF: 101 µV rms = 0.23 LSB | `sim/results/r2/cdac2_mc50_tt_c_cp100.json` (`ktc_noise_uV`) |
| 2 | Weight-correction model, 14-bit weights, bench ramp extraction (16 conversions per LSB, noise 58 + 101 µV), 50 MC samples: no missing codes in ≥ 48/50 | passed | 50/50 without missing codes (uncorrected: 12/50 with missing codes); INL max 0.69 LSB | `sim/results/r2/cdac2_mc50_tt_c_cp100.json`; run `r2-cdac-mc50-tt-c-cp100` |
| 2 | Same, DNL ≤ 0.5 LSB | **failed** | max \|DNL\| median 0.53 LSB, max 0.69 LSB; 12/50 samples ≤ 0.5 LSB | same |
| 2 | Unit size that meets DNL ≤ 0.5 LSB | none found (*derived*) | ×2 unit: 19/50, ×4 unit: 27/50 ≤ 0.5 LSB. The limit is re-quantisation of the 0.62 LSB raw step, not matching. 14 decisions (one more LSB decision) with the 22 fF unit: median 0.375, 49/50 ≤ 0.5 LSB | `sim/results/r2/array_sweep_derived.txt` |
| 2 | Ramp-calibrated weights from the circuit (tt ramp, 13 weights free) | passed | W = 16253 8131 4066 2033 1017 633 317 159 79 40 20 10 5 (600 ramp points, 13 weights free) (design: 16257 8129 4064 2032 1016 633 316 158 79 40 20 10 5) | `sim/results/r2/ramp_tt.json` |
| 3 | Reference buffer alone, CDAC charge as current pulses (0.42 pC per 33 ns, both slices, reset events) | passed with remark | VREF 1.0040 V; 422 µA from VDDA 3.3 V; max droop 19.4 mV (at the slice-B reset event); full-scale code error *estimate* ≤ 0.74 LSB (A) / 1.05 LSB (B) at decisions 5–12 | `sim/results/r2/refbuf_pulse_tt_b.json`; run `r2-refbuf-pulse-tt-b` |
| 3 | ADC with `r1_refbuf` in the loop against ideal VREF, 8 frames, both slices | **failed** (0.25 LSB) | max code difference 1 LSB at ±0.87/0.88 V; 0 LSB near mid-scale; VREF 0.991–1.007 V during conversion | `sim/results/r2/ref_adc_tt.json`; runs `r2-ref-adc-tt-buf-a`, `r2-ref-adc-tt-ideal-a` |
| 3 | MIM area of the reference | reported (*estimated*) | decoupling 6 × 70 × 70 µm² (44 pF) + gate capacitor 50 × 50 µm² (3.8 pF) = 31 900 µm² MIM | `schematic/gen_r1_adc_r2.py` |
| 4 | Comparator noise ≤ 60 µV rms, tt, CM 0.1 V | passed | 58.1 µV (method A: `.noise` input PSD at the integration operating point × sinc² window, T_int = t_dec − 1 ns = 7.1 ns) | `sim/results/r2/cmp2_noise_tt27_cm01_b16.json`; runs `r2-cmp-noise-tt-cm01-d`, `r2-cmp-tran-tt27-d` |
| 4 | Same at ss / 125 °C / 1.08 V | **failed** | 81.7 µV (T_int 5.4 ns: faster integration at ss/125 °C) | `sim/results/r2/cmp2_noise_ss125_cm01_b16.json` |
| 4 | Noise method B (transient noise, S-curve) | not run | abandoned for cost on an earlier comparator variant (`r2-cmp-trnoise-tt-cm01`) | — |
| 4 | Comparator offset, 30 MC copies (`mos_tt_mismatch`) | reported | σ 3.5 mV at CM 0.6 V, 3.2 mV at CM 0.1 V (censored fit, 4 copies outside ±5 mV); change from CM 0.6 to 0.1 V: σ 0.35 mV, max 0.70 mV (inside the +31 LSB redundancy of decisions 0–4, where the common mode moves) | `sim/results/r2/cmp2_offset_mc30_cm0{6,1}_b16.json` |
| 4 | Comparator decision time | passed | t_dec 8.1–9.3 ns (tt), 6.4–10.4 ns (ss/125/1.08), 10.4–10.8 ns (ff/−40/1.32) against the 15 ns strobe | `sim/results/r2/cmp2_tran_*.json` |
| 5 | ISA / ISB conversion, full core, frames enc / cur / enc / cur | passed | ISA +0.85 V at CM 0.57 V → 3941, ISB −0.85 V → 155 (ideal from the tt LSB: 3943 / 153); encoder frames before and after unchanged (2938 / 1156 and 1156 / 2939) | `sim/results/r2/isa_tt.json`; run `r2-isa-tt-a` |
| 5 | Mux timing against INTERFACES.md ("{SIN, COS} pair then {ISA, ISB} pair" per 1 µs frame, 250 ns track) | **failed** | this design converts one pair per frame (A track 567 ns, B track 132 ns); two pairs per frame need 52 cycles at 13 cycles per conversion (issue R2-6) | `sim/r2/tb_adc2_isa.cir`, `sim/r2/r1_adc_timing_r2.inc` |
| 6 | Static ramp, tt, both halves, 7 LSB per frame, ramp-calibrated weights | passed | best-fit residual −1.11 … +1.27 (ramp-calibrated weights; design weights −1.32 … +1.37) LSB (INL estimate, includes ±0.5 LSB quantisation); monotonic at the sample points: yes (600 points, both weight sets); saturation codes 0 / 4095 reached at both ends | `sim/results/r2/ramp_tt.json` |
| 6 | Windows ±8 codes, 2 frames per LSB: tt at 1024 / 2048 / 3072; ss / 125 °C; ff / −40 °C; tt at VDD 1.08 / 1.32 V | passed (design weights); see R2-11 for ramp-calibrated weights | design weights: DNL −0.50 … +0.55 LSB at 0.5 LSB resolution in all 7 windows, no missing codes, monotonic. Ramp-calibrated weights: code 2048 is 2.8 LSB wide at tt (DNL +1.80), +1.33 at ss/ff, one non-monotonic step at ss / 125 °C and at both VDD windows | `sim/results/r2/win_*.json`; runs `r2-win-*-a-*` |
| 6 | Dynamic, slice A, tt, fin 97.66 kHz (M 25, N 256), 0.88 V amplitude | passed (no device noise) | ramp-calibrated weights: SNDR 70.54 dB, SFDR 78.22 dB, THD −76.21 dB, ENOB 11.43 at −0.37 dBFS; design weights: SNDR 69.00 dB, SFDR 71.79 dB, ENOB 11.17 | `sim/results/r2/dyn_tt_a_n256.json`; runs `r2-dyn-tt-a-n256*` |
| 6 | ENOB with kT/C and comparator noise | *derived* | ≈ 11.18 (noise 0.41 LSB from the simulated SNDR, + 0.23 LSB kT/C + 0.13 LSB comparator, in rms) | from the line above + 101 µV + 58 µV |
| 6 | Dynamic, both slices (sine on A, cosine on B), fin 101.56 kHz (M 13, N 128) | passed (no device noise) | ramp-calibrated weights: A (sine) SNDR 70.46 dB, SFDR 77.91 dB, ENOB 11.41; B (cosine, 132 ns track) SNDR 70.64 dB, SFDR 80.36 dB, ENOB 11.44. Design weights: ENOB 11.27 / 11.32 | `sim/results/r2/dyn_tt_ab_n128.json`; runs `r2-dyn-tt-ab-n128*` |
| 6 | Dynamic at 100.6 kHz with N 1024 | not run | time budget at tmax 0.2 ns (≈ 2 h per run); N 256 at 97.66 kHz run instead | — |
| 6 | Full ramp or dynamic at ss / ff / VDD corners | not run | windows only | — |
| — | Simulator accuracy (see above) | found and corrected | reltol 1e-3 / tmax 5 ns: decision errors ≤ 6 mV; reltol 1e-4 / tmax 5 ns: ≤ 0.5 mV; final: tmax 0.2 ns | runs `r2-dbg-*` |
| — | xschem, layout, DRC, LVS, PEX | not run | — | — |

### Area and power (revision 2)

| Part | Basis | Value | Class |
| --- | --- | --- | --- |
| CDAC MIM | 4 sides × 159.25 Cu × ≈ 29 µm² per unit cell | ≈ 0.0185 mm² | estimated |
| Reference buffer | decoupling 6 × 70 × 70 µm² = 29 400 µm², gate capacitor 2 500 µm², amplifier and divider ≈ 4 000 µm² | ≈ 0.036 mm² | estimated |
| Comparators (2) and bias | | ≈ 0.002 mm² | estimated |
| Switches, drivers, boost capacitors, SAR logic | revision-1 basis, 13 decisions | ≈ 0.0095 mm² | estimated |
| **Total** | | **≈ 0.066 mm²** (S1 budget 0.06 mm²) | estimated |
| VDD 1.2 V (comparators with bias, bootstrap, drivers; SAR logic not included) | `r2-quick-tt-acc`, frames 1–4 | 153 µA (183 µW) | simulated |
| VREF charge (ideal source) | same run | 3.7 µA (3.7 µW) | simulated |
| Reference buffer from VDDA 3.3 V | `r2-refbuf-pulse-tt-b` | 422 µA (1.39 mW) | simulated |
| SAR logic | revision-1 estimate | 20–50 µW | estimated |

### Open issues (revision 2)

R2-1. **Full scale ±0.92 V, not ±1.0 V (D11).** The comparator input capacitance (≈ 84 fF) and the top-plate
   parasitics attenuate the CDAC by ≈ 8 %. Options: (a) VREF 1.09 V from a buffer with gain (the 3.3 V buffer
   supply allows it; the present follower can only give ≤ 1.045 V); (b) accept ±0.92 V and set the AFE gain for
   80 % of it; (c) a smaller comparator pair (noise rises). Recommendation: (a). Specification decision (D11).
R2-2. **DNL floor ≈ 0.53 LSB median with 13 decisions.** The redundant decision makes the raw step 0.62 LSB.
   Re-quantisation to 12 bits then gives \|DNL\| up to ≈ 0.6–0.7 LSB, also with exact weights. Larger units do not
   remove it (*derived*). Missing codes are removed (50/50). Recommendation: 14 decisions (one more LSB decision,
   one more cycle: 14 ≤ 15 ticks) gives median 0.375 and 49/50 ≤ 0.5 LSB (*derived*). This changes D12 and
   INTERFACES.md (14 raw bits, `w[13:0]`).
R2-3. **Comparator noise at ss / 125 °C** is 81.7 µV (target 60 µV). The integration is faster there. Options: a
   larger integration capacitor at the cost of decision time (ss/125 °C t_dec 6.4 ns, so there is margin to the
   15 ns strobe), or a corner-dependent tail current. Not run.
R2-4. **Reference buffer settling.** With `r1_refbuf` in the loop the code error is 1 LSB at ±0.88 V (target
   0.25 LSB). The slice-B decisions see the slice-A reset event (20.7 LSB at decision 0, inside the +31 LSB
   redundancy). Options: more decoupling (area), a faster follower (current), or a reset of the slice-B
   bottom plates outside its conversion. A slow +0.5 mV overshoot tail remains. The 1 mA S1 estimate is now
   422 µA simulated.
R2-5. **Weights 12 vs 13.** INTERFACES.md asks for 13 raw bits and `w[12:0]`; D12 names 12 weight registers.
   The last decision (weight 0.62 LSB, W = 5) can be a fixed constant, so 12 registers are sufficient for 13
   decisions. With R2-2 (14 decisions) the count becomes 13 or 14. Owner: `r1_ctrl` and D12.
R2-6. **Mux timing against INTERFACES.md.** The contract asks for the {SIN, COS} pair and the {ISA, ISB} pair in
   every 1 µs frame, with a 250 ns track window. This design samples one pair per frame edge (A tracks 567 ns,
   B 132 ns). Two pairs per frame need 4 conversions × 13 cycles = 52 cycles with one SAR logic. The `r1_ctrl`
   RTL converts ISA and ISB at separate strobes; with this ADC they need separate frames. Options: alternate
   frames (500 kSPS per channel), a 60 MHz SAR clock, or two SAR logic blocks. The slice-B track window (132 ns)
   is also shorter than the 250 ns AFE contract. Coordinator decision.
R2-7. **ngspice accuracy and aborts.** Conversion decks need tmax 0.2 ns (finding above). Long decks still stop
   with "Timestep too small", often at 123.6 µs and at sampling edges of the B-source inputs (`bsn#branch`).
   `sim/r2/run_static2.py` restarts after each abort; a frame that aborts at its own sampling edge is skipped.
   Next step: replace the B-source inputs by E sources.
R2-8. **VDD windows and the logic supply.** The XSPICE `dac_bridge` drives the switch controls with a fixed
   1.2 V, so the VDD 1.08 / 1.32 V windows change only the analog supply of the comparator, switches and
   timing levels, not the logic high level.
R2-9. **Not run:** noise method B (transient noise), N 1024 dynamic at 100.6 kHz, full ramp and dynamic at
   corners, the reference buffer at corners, xschem sheets, layout, DRC, LVS, PEX. The comparator bias
   current (14 µA) and the bandgap node are ideal sources.
R2-10. **Area** ≈ 0.066 mm² (*estimated*) against the 0.06 mm² S1 budget; the reference decoupling (29 400 µm²)
   is the largest part.
R2-11. **Ramp calibration and mid-scale DNL.** Weights extracted by least squares from the full tt ramp (7 LSB per
   frame) improve SFDR (78.2 against 71.8 dB) but make code 2048 2.8 LSB wide. The design weights give DNL within
   ±0.55 LSB in the same windows. The global fit absorbs the ±1.2 LSB INL bow into the MSB weight. The bench
   method in D12 must therefore use a finer ramp (the model uses 16 conversions per LSB) or a fit that keeps the
   major transitions. Not run at circuit level (cost: ≈ 9 h per full ramp at 16 points per LSB).


## What it is (revision 1)

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

## Files (revision 1)

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

## Built against (revision 1)

| Item | Value | How established |
| --- | --- | --- |
| PDK | IHP SG13G2 open PDK commit `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` | `flow/run.sh` checks `/foss/pdks/ihp-sg13g2/COMMIT` before every run |
| Container image | `sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2` (`tapeoutbench-eda:latest`) | `flow/run.sh` identity check |
| ngspice | ngspice-46, KLU, XSPICE `digital.cm`, PSP 103.6 OSDI | banner in every `sim/runs/*/ngspice.log`; `.spiceinit` in the block root |
| Models | `cornerMOSlv.lib` `mos_tt` / `mos_ss` / `mos_ff` / `mos_tt_mismatch`; `cornerCAP.lib` `cap_typ` / `cap_typ_mismatch` | deck headers in `sim/runs/*/deck.cir` |
| xschem, KLayout, LibreLane, CACE | not used in this step | — |
| Reference design | IHP-AnalogAcademy commit `133ecf65…` (Apache-2.0) | `third_party/README.md` |

## Status (revision 1)

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

## Numbers (revision 1)

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

## Open issues (revision 1)

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

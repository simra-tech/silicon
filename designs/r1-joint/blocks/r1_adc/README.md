# R1_ADC — 12-bit SAR ADC with two simultaneous track-and-holds (schematic level, revisions 1 and 2)

State on 2026-10-20: **schematic written and simulated at schematic level only.** No layout, no PEX, nothing
measured. Every number in this file is **simulated** with ngspice 46 and the PDK models named below, unless it is
marked *estimated* or *derived*. The reference is an **ideal source** in revision 1 and in most revision-2 decks;
revision 2 adds the buffer `r1_refbuf` and simulates it in two decks. The SAR logic and the timing generator are
**behavioural** (XSPICE digital cells and ideal pulse sources).

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

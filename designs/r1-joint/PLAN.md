# R1 plan — specification phase

Written 2026-10-20. The specification is the source of truth for what the chip does; each block's
README is the source of truth for what was run. A step with no evidence linked next to it did not
happen.

## 1. Phases

| Phase | Output | Gate |
| --- | --- | --- |
| P0 specification | top-level specification, pin map, parameter classification, block budgets (area, power, pins), verification gates | owner review |
| P1 architecture studies | encoder chain accuracy budget; BiSS-C/SSI protocol and register map; area and floorplan feasibility; safety architecture | numbers in the specification, each marked simulated / estimated / assumed |
| P2 block design | schematics and RTL, block simulations at corners, MC where mismatch matters | block freeze: DRC/LVS clean or cut |
| P3 integration | floorplan, assembly, chip-level DRC/LVS/PEX, STA, full-chip co-simulation | top freeze: zero-marker decks |
| P4 sign-off | release package, bond plan, status tables | GDS frozen; human signs |

## 2. Cut list

If area, pins or schedule do not close, blocks are removed in this order and the README says so:

1. ABZ incremental output (3 pins) — fold into SPI-only reporting.
2. Second encoder track (nonius absolute) — single-track incremental with index.
3. PWM/commutation generator — gate outputs become controller-driven pass-through with safety gating.
4. Second current channel — one channel, single-phase monitoring.
5. T2F temperature output pin — report over the bus only.

What is never cut: the sine/cosine ADC path, the position computation, one serial interface, the
safety channel with the latched fault output, the bandgap.

## 2a. Area and pin closure (from S3, 2026-10-20; all numbers estimated, nothing run)

Measured on the G1 chip of record: interior inside the IO rows 772 × 772 µm = 0.596 mm²; G1 placed
0.458 mm² of macros there (77 %). Derived conversion for the digital macro: about 11 µm² per gate
equivalent at G1's 81–86 % utilisation.

The R1 block list as first written needs about 1.03 mm² (two SAR ADCs 0.20, digital 0.27, G1-size
BGR 0.15, two G1-size sense amplifiers 0.18, comparators 0.10, AFE 0.08, rest 0.06). The pin list
counts 26. Decisions taken to close:

| # | Decision | Effect |
| --- | --- | --- |
| D1 | Single-track encoder input (on-axis heads, one cycle per revolution, or any single sin/cos track); nonius second track dropped (cut 2) | −4 pins, −0.02 mm² |
| D2 | No ABZ output (cut 1); position over BiSS-C/SSI/SPI only | −3 pins, −0.01 mm² |
| D3 | One SAR ADC with two track-and-holds for simultaneous sine/cosine sampling; the current channels are multiplexed into the same ADC between encoder conversions; the safety comparators stay analog and do not depend on the ADC | −0.10 mm²; defines the current-sense ADC path |
| D4 | PWM pattern generator reduced to a safety-gated pass-through with dead-time insertion for three external low-side FETs (cut 3 in part); the controller generates PWM | −0.02 mm² |
| D5 | Compact new bandgap and compact current-sense cells; the G1 BGR586 (mismatch-averaged, 0.15 mm²) and G1 sense cell (0.09 mm²) are too large for R1 | −0.24 mm² |
| D6 | Iterative CORDIC and a 32-register file; pipelined CORDIC rejected | digital ≈ 0.18 mm² |
| D7 | `MA` shares the pad with `SCLK` and `SLO` with `SDO`; `CS` low selects SPI; no SPI access during a BiSS/SSI frame | −2 pins |
| D8 | `TEMP_OUT` pin dropped (cut 5); temperature over the bus; the freed pad is `EN`/`STO_IN`, a hardware enable the first list lacked | safety input added |
| D9 | Baseline die 1.414 mm (G1 ring reused). If block freeze areas exceed 0.45 mm², the fallback is a 1.5 mm die (interior ≈ 0.86 mm², area ≈ 2.25 mm², above the 2 mm² budget: owner decision at the floorplan gate) | — |

Lean total after D1–D8: ≈ 0.45–0.50 mm², marginal on the baseline die.

**D10 (decided 2026-10-21: 1.6 mm die; see the closing paragraph).** T5 synthesis puts the digital macro at ≈ 0.34 mm² placed (30.4 kGE; `r1_pos` 36 %, registers 19 %, `r1_gate` 17 %, `r1_safe` 10 %, BiSS 10 %, SPI 5 %), against the 0.18 mm² estimate, which predates the on-chip PWM generator (open item 6). Choices: (a) trim the RTL (shared multiplier in `r1_pos`, fewer writable registers, narrower PWM counters) to ≈ 0.28 mm² and still take the 1.5 mm die (D9); (b) the 1.5 mm die with the RTL as is; (c) cut the PWM generator back to pass-through (cut 3) and the I²t model to the host. Decision after T1–T4 report their analog areas.

**D10 closure (2026-10-21, S6).** The S6 floorplan study (`specification/studies/S6_FLOORPLAN.md`) puts the required area at 0.741 mm² against a 0.566 mm² window at 1.414 mm (−31 %); with every cut including the functional ones it is still −10 %. At 1.6 mm the required 0.787 mm² fits the 0.880 mm² window (analog macros under the core ring, as on G1 r4) with 10.6 % margin, given five non-functional cuts: digital at 75 % (C1), register trims to ≤ 240 000 µm² placed (C2), stacked MIM-on-MOS ADC decoupling (C5), AFE MIM over resistors (C6), analog under the ring (C7). Decision: the die is 1.6 mm (ring pitch 140 µm, same 24 pads in the same order); escalate to 1.7 mm if the laid-out analog sum exceeds 0.30 mm² or the digital macro does not close at 75 %. Hard constraint for `r1_ctrl` 0.4: DIE_AREA 520 × 664 µm, ≤ 240 000 µm² placed, 42 MHz at three corners. The functional cuts C3, C4, C8 are rejected.

Area picture after all six P2 reports (2026-10-20; block areas estimated from device counts and the G1 packing ratio,
digital from synthesis × the G1 macro-to-cell ratio):

| Macro | mm² | Source |
| --- | --- | --- |
| Digital (`r1_ctrl`) | 0.34 (0.28 after the RTL trims listed in its README) | T5 |
| AFE | 0.084 | T3 |
| ADC + reference buffer | 0.04 + 0.02 | T2, S1 |
| OSC | 0.018 | T1 |
| isense × 2 | 0.06 | T4 |
| safe (4 comparators + DACs) | 0.025 (revision 3: 0.05–0.06, S6) | T4 |
| BGR (compact), T2F, 3 gates, level shifters | 0.055 | S3 |
| Total | ≈ 0.64 (≈ 0.58 with the digital trims) | |
| Usable at 77 % packing: 1.414 mm die (interior 0.596) | 0.46 | T6, S3 |
| 1.5 mm die (interior ≈ 0.736) | 0.57 | estimated |
| 1.6 mm die (interior ≈ 0.918) | 0.71 | estimated |

**D10 (provisional, 2026-10-20): 1.6 mm die (2.56 mm²).** The lean design does not fit 1.414 mm even with every
cut, and 1.5 mm is marginal only with the digital trims. 1.6 mm keeps every block and leaves ≈ 10 % margin. Owner
confirmation needed (area cost above the 2 mm² budget). Ring and bond plan are re-run by T6 once confirmed.

Decisions from the P2 block reports (2026-10-20, all numbers simulated at schematic level):

| # | Decision | Source |
| --- | --- | --- |
| D11 | ADC full scale is ±1.0 V differential (2.0 Vpp) from a 1.0 V reference, because VREF = 1.2 V is impossible at VDD = 1.08 V. The AFE output target becomes 1.6 Vpp (80 % of FS): stage-2 gain 10/7 → 8/7. | T2, T3 |
| D12 | CDAC mismatch is corrected in the digital domain: one redundant bit in the SAR sequence and host-loaded per-bit weights (12 × 14 bit registers) applied as output = Σ b_i·w_i in `r1_ctrl`; units stay 22 fF. Weights are found on the bench with a ramp. Larger units (200–350 fF) are the fallback. | T2 |
| D13 | `OSC_TRIM` reset value 22 (30.0 MHz at tt). The digital macro closes STA at 42 MHz (fastest untrimmed at code 22 is 38.9 MHz); codes that would exceed 42 MHz at ff are flagged by `OSC_COUNT`, not prevented in hardware. | T1, T5 |
| D15 | Block interfaces are fixed in `blocks/INTERFACES.md` 0.1 (AFE↔ADC, isense↔ADC/safe, safe↔ctrl calibration, ADC↔ctrl weights, osc, bgr, t2f, gate). | all |
| D16 | ADC full scale is ±0.9 V differential (revision 2 reaches ±0.919 V with the unity-gain reference buffer; a buffer with gain is not worth its risk). AFE output target 1.44 Vpp (80 % of FS); isense ±0.85 V is 94 % of FS, accepted. Supersedes the ±1.0 V of D11. | T2b |
| D17 | SAR sequence has 14 decisions (two redundant bits); 14 host-loaded weights. Both CDAC slices convert in parallel with their own comparator and their own sequencer; frame = 36 ticks at 30 MHz: {SIN, COS} then {ISA, ISB}; encoder pair rate ≈ 833 k/s, count-safe ≈ 208 kHz (the 250 kHz target is missed by 17 %, accepted and recorded in the specification). Supersedes the 13-decision, one-pair-per-15-ticks contract. | T2b, T5b |
| D14 | ADC comparator noise target ≤ 60 µV rms and an on-chip reference buffer able to settle 0.42 pC per 33 ns bit cycle are `r1_adc` revision-2 requirements; the AFE track-and-hold model (2.8 pF per side, 250 ns track, 0.6 V CM) is confirmed as the interface. | T2, T3 | Power ≈ 17–21 mW, about
4.5 mA on the single `VDDA` pad (G1 path 11–21 Ω, ≈ 95 mV drop): a second analog supply pad is not
available, so the analog current budget is a design constraint, not a result.
- **D18 (2026-10-20, ADC schedule, replaces the D17 frame arithmetic).** D17 asked for both pairs in a 36-tick frame with conversion ≤ 17 ticks and a 250 ns track window per slice; with each slice converting twice per frame this forces conversion ≤ 10.5 ticks, which r1_adc revision 3 could only meet with two decisions per tick (13 ns strobe: comparator noise fails at ss/125 °C, an undesigned 3 ns delay cell). New schedule: the encoder pair {SIN, COS} is converted every frame of 22 ticks (14 decisions at one per tick + 8 ticks ≥ 250 ns track; 0.733 µs; naive count-safe limit 341 kHz). The current pair {ISA, ISB} replaces one encoder frame per PWM period at the centre-of-on-time strobe from r1_gate (the only instant the current sense needs). The tracking loop must bridge the 1.47 µs encoder gap once per PWM period (ctrl 0.3 item 7, 250 kHz proof). Weights: 14 per slice, 28 registers (R3 open issue 4). Conversion ≤ 17 ticks is restored as the ctrl binding number.

## 3. Studies started 2026-10-20

| Study | Question | Owner | Result |
| --- | --- | --- | --- |
| S1 encoder chain | input standard, ADC resolution and rate, CORDIC widths, calibration, accuracy budget | agent | done 2026-10-20: 40 mVpp–1.4 Vpp differential, CM 0.5–2.8 V, PGA ×1–×32; full accuracy to 100 kHz, count-safe to 250 kHz; 12-bit SAR ENOB ≥ 11.5, simultaneous sampling skew < 0.5 ns; register calibration (offset, gain, phase, H3) brings ≈ ±10° el to < ±0.2° el; iterative CORDIC + tracking loop at ≥ 25 MHz. `specification/studies/S1_ENCODER_CHAIN_20261020.md` |
| S2 bus | BiSS-C/SSI frame, CRC, timing, register map scope | agent | done 2026-10-20: D2 register channel is mandatory (IDs read through CDM/CDS); RS-422 transceiver on the board; SSI trivial on the same pins; AS5047P-compatible SPI read frame proposed; Manufacturer ID registration handled outside the repository. `specification/studies/S2_BUS_20261020.md` |
| S5 oscillator | 25–32 MHz clock options, jitter budget, BiSS timeout | agent | done 2026-10-20: option (a) re-tuned G1 RC at 30 MHz, 5-bit trim, MA-referenced trim count; jitter ≥ 8× inside budget for all options; IHP PLL lacks lock/corner data. `specification/studies/S5_OSCILLATOR_20261020.md` |
| S4 PDK data | MIM/MOS/resistor mismatch models, DRC MIM limits, IO Liberty data | agent | done 2026-10-20: MIM mismatch 1 %·µm (spec blank); MOS and resistor 1σ values listed; no ADC/comparator IP in the PDK; no IO toggle-frequency limit. `specification/studies/S4_PDK_DATA_20261020.md` |
| S3 area and pins | macro budgets from G1 data and literature, floorplan, pin map closure | agent | done 2026-10-20: plan as written ≈ 1.03 mm² of macros against ≈ 0.45 mm² usable on the 1.414 mm die; 26 pins listed against 24; lean variant ≈ 0.56–0.60 mm², marginal. See §2a and `specification/studies/S3_AREA_PINS_20261020.md` |

## 4. Design-trace record

Every run of this design is kept for later reuse (training and evaluation tasks derived from real
design sessions). Rules, binding for every agent on R1:

1. Simulation decks, logs, raw waveforms and reports go under the block's `sim/` or `reports/`
   directory, or under the bulk results root (`G1_RESULTS_ROOT`) with a symlink in the tree. Nothing
   that is evidence lives only under `/tmp`.
2. Each run directory carries a `README.md` or `run.json` with the command, tool versions, PDK
   commit, inputs, the question asked, the result and the disposition (passed / failed / not run).
3. Failed and abandoned runs are kept, not deleted; they are labelled as such. A failure trace is as
   useful as a pass.
4. Session and subagent transcripts are copied to durable storage by a scheduled job; agents do not
   need to do this, but must not place artefacts in locations the job does not cover.
5. Large files (GDS, VCD, waveform dumps above a few MB) go to the bulk root, never into git.

## 5. Progress log

| Date | What happened |
| --- | --- |
| 2026-10-21 | S6 floorplan and area closure (`specification/studies/S6_FLOORPLAN.md`; rectangles only, run `s6-floorplan/run-20261021-b`; block areas estimated except `r1_ctrl` hardened and T2F/LS placed). Analog sum 0.31–0.35 mm²; allowances (keep-out, 30 µm guard strip, VDDA trunk, decoupling) 0.16 mm². 1.414 mm does not fit: 0.205 mm² outside the die with cuts C1, C2, C5, C6, C7; −10 % even with every cut. 1.6 mm fits with 10.6 % margin only with C1 (digital 75 %), C2 (≤ 240 000 µm² placed), C5 (ADC reference decoupling on MOS, −0.02), C6 (AFE MIM over resistors, −0.03) and C7 (analog macros under the core ring as on G1 r4, measured); no functional cut. Recommendation for D10: 1.6 mm; `r1_ctrl` 0.4 hard constraint `DIE_AREA 0 0 520 664`, ≤ 75 % final utilisation; escalate to 1.7 mm if laid-out analog > 0.30 mm². Optional west pin-map swap recommended. Layout, ring rebuild, IR drop: not run. |
| 2026-10-21 | Round 3 closed: afe rev D (9eba0f8ff), adc rev 3 + D18 (116fc93fa), ctrl 0.3 (8b2a26cfe, LibreLane sign-off clean), bgr r1 (6d534b2d7). Running: T2d adc rev 4 under D18 (103-105), S6 floorplan study for D10 (100-102), T3d afe rev E ffx fix (106-108, Sonnet), T7b bgr stability and noise (116-119, Sonnet). ctrl 0.4 (density, floorplan constraint) waits for S6. |
| 2026-10-20 | T2c `r1_adc` revision 3 (schematic, simulated; `blocks/r1_adc/README.md` § Revision 3): D16/D17 applied, 14 decisions, two slices in parallel, two decisions per tick (conversion 7.0 ticks, track 323.6–325.2 ns, mux sequence correct with the full core); FS ±0.914 V; R2-7 E sources done. R2-4 failed (best buffer buf64, 1.65 mA: ±1 LSB, not 0.25). R2-3 failed at ss (75.7 µV vs 60; tt 57.5, ff 45.3); decision time 9.4–10.8 ns at CM ≤ 0.35 V, decision 0 at ss/CM 0.6 V not resolved (redundancy). R2-11 windowed calibration passed (derived, 50/50 MC ≤ 0.5 LSB; circuit demo at tt passed). Static windows tt/ss/ff monotonic, no missing codes; dynamic tt N 32 SNDR 70.9 dB. Contract issues: conversion ≤ 10.5 ticks, 2 × 14 weights. Not run: full ramp, dynamic ss/ff, layout. Area ≈ 0.070 mm² (estimated). |
| 2026-10-20 | T5 `r1_ctrl` revision 0.3 (register map 0.3; simulated, synthesized, hardened; run of record `r1ctrl_20261020_v03`, hardening `r1ctrl_ll_20261020_t6`, D18 RTL). Comparator calibration per the `r1_safe` contract: two-sided search (preset + probe, 14 PWM periods), `CMP_CAL_IDEAL` in half codes (the 6-bit integer form was one code off on 103/274 samples); model vs `cal_model.py` 274/274 identical, RTL vs model 274/274. D18 applied: two 14-bit ADC slice ports, frame generator (22-tick encoder frame, current frame at the strobe restarts the grid), 2 × 14 weights at 0x50–0x5D / 0x60–0x6D, `r1_pos` 2 CORDIC iterations per tick (19 ticks per pair; the 28-tick `r1_pos` dropped half the pairs at 22 ticks). `CAL_CRC` covers 43 words (position, comparator words, all 28 weights). Count safety, 22-tick frame with the 44-tick PWM gap: no count loss at 208 and 250 kHz up to 4.0·10⁹ Hz/s; acceleration limit from the loop gains 2.50·10⁹ Hz/s = 1.57·10¹⁰ rad/s² (45° el), snap-free on the RTL 1.6·10⁹ Hz/s = 1.0·10¹⁰ rad/s²; 100 kHz tracked error 0.016° el. 36-tick (D17) runs superseded (`v03e`). Regression: 315 chip-level checks, 16 position cases, 274 calibration cases passed. The latch register file failed sign-off STA at the slow corner (−2.10 ns); the flip-flop file passes 42 MHz at all corners, DRC/LVS clean (t5, RTL before D18); the D18 RTL of record hardens cleanly too (t6: 42 MHz at all corners, DRC/LVS/antenna 0, die 0.477 mm² at 55 % start utilisation). Cell area 245 386 µm² (1.36 × the 0.18 mm² target; D18 +31.6 k). Open: `r1_adc` rev 4 to confirm conversion ≤ 17 ticks, bit order and 1/4-LSB weights; area; BP_ID/MFR_ID [verify]. `blocks/r1_ctrl/README.md` |
| 2026-10-20 | T3 `r1_afe` revision D (schematic, simulated; runs `r1afe-*-20261020d`, screens `dev-revd-*`): D16 applied (stage-2 Rin 19.44 kΩ, 1.43–1.46 Vpp); output CM 0.594–0.597 V (cause of the rev-C error: OTA2 mirror lengths, fixed with l = 2 µm references); stage-1 CM PM 62.4° at ×32 and 66.2° at ×8 with f_c 1.020 MHz (cross-coupled Miller caps); ×32 noise 31.0 µV at ss (11 % margin, 2× NMOS input pair); DM1 64.4°, DM2 67.7°, CM2 61.3°; THD 0.025 %; MC pole match 0.961 %; PSRR 54.3 dB. Failed: T/H total error 0.38 LSB (non-linear residual 0.005 LSB passed); coordinator decision asked: INTERFACES.md AFE → ADC to "non-linear residual ≤ 0.25 LSB, linear part by gain calibration", or an output buffer (> 1 mA). Failed cross corner ffx (ff, 3.0 V, 125 °C): DM1 52.8°, CM1 54.3°, CM2 59.6° (candidate fix for DM1 recorded). Regression list added. ≈ 0.099 mm² (estimated), 1.71–2.00 mA. `blocks/r1_afe/README.md` |
| 2026-10-20 | Round 2 closed for adc (rev 2, b5f0b5831), afe (rev C, b21d2a03d), safe (rev 3), ctrl (0.2); T7 bgr still running. Contract mismatch safe/ctrl calibration search recorded in INTERFACES.md. Round 3 started 20:10 CEST: T2c adc rev 3 (R2-3/R2-4/R2-11, E sources, D17 frame timing), T3c afe rev D (D16 applied, output CM, CM PM, settling decision), T5b ctrl 0.3 (CAL_IDEAL and two-sided search, LibreLane to sign-off, CAL_CRC scope, 208 kHz). |
| 2026-10-20 | T3 `r1_afe` revision C (schematic, simulated; runs `r1afe-*-20261020c2`): loop-gain analysis (Tian, validated) shows revision B had stage-1 DM PM 15–17° and CM PM 13°; the oscillating rev-B variant gives a negative CM margin, and a new CM-step transient detects it. Revision C: OTA1 Miller cap partly switched by gain code, zero resistors, CM-sense feed-forward caps, OTA2 partial CMFB sink; stage-2 gain 8/7 (D11). Passed: DM1 PM 68.0°, DM2 65.6°, CM2 63.2°, f_c ≥ 1.023 MHz, MC pole match ≤ 0.96 %, THD ≤ 0.032 %, ×32 noise 34.8 µV (ss), temperature, CM-step test. Failed: CM1 PM 54.3° (target 60°), T/H total error ≤ 1.29 LSB (non-linear residual ≤ 0.082 LSB, passed), output CM 0.577–0.648 V. D16 (1.44 Vpp) not applied: 8/7 kept, ADC sees 89 % FS. ≈ 0.091 mm², 1.53–1.86 mA. `blocks/r1_afe/README.md` |
| 2026-10-20 | T2 `r1_adc` revision 2 (schematic, simulated; `blocks/r1_adc/README.md` § Revision 2): 13 decisions with 14-bit weight correction (D12), sub-binary 22 fF CDAC, current-tail comparator, `r1_refbuf` (1.0 V, 422 µA from 3.3 V, 44 pF MIM). Full scale ±0.919 V (D11 asks ±1.0 V: failed); CDAC MC 50/50 without missing codes, DNL ≤ 0.5 LSB failed (median 0.53, re-quantisation floor; 14 decisions recommended, derived 49/50); comparator noise 58 µV tt / 82 µV ss-125 °C, offset σ 3.5 mV; ISA/ISB codes correct, but one pair per frame against the two pairs per frame in INTERFACES.md (coordinator decision); tt ramp monotonic, INL ±1.3 LSB; windows at tt/ss/ff/VDD no missing codes; ENOB 11.4 (A and B, no device noise). Finding: ngspice needs tmax 0.2 ns for correct comparator decisions; earlier conversion runs marked invalid. Area ≈ 0.066 mm² (estimated). |
| 2026-10-20 | T5 `r1_ctrl` RTL revision 0.2 (register map 0.2), all numbers simulated or synthesized. Cell area 180 173 µm² (0.1: 220 968), 0.1 % above the 0.18 mm² target. Added: ADC weight correction (D12, bit-exact; mismatch example 0 missing codes, DNL 0.69 LSB calibrated), comparator offset calibration in `az_win`, OSC_TRIM reset 22 and clock-fault window (D13), BiSS D2 control-channel conformance (9 of 10 items; BP_ID code open), half-tick LAT (161 cells, latch spread halved). Run of record `r1ctrl_20261020_v02b`: 260 chip-level checks and 9 position cases passed. First LibreLane trial (42 MHz, 70 %): die 0.281 mm²; setup failed only on one latch path (fixed in v02b); stopped by the 2 h limit in detailed routing (17 violations left); sign-off STA/DRC/LVS not run. `blocks/r1_ctrl/README.md` |
| 2026-10-20 | T4 `r1_safe` revision 3 (schematic, simulated): 6-bit calibration code per comparator summed into the threshold DAC (252-unit string, 2 × 256:1 muxes per comparator, step LSB/8, range ±4 LSB), `rppd` degeneration and a larger mirror. Raw mismatch σ 6.2 mV (was 32 mV); modelled calibration 51/51 within 0.25 LSB (worst 0.125 LSB); full-path MC r1_isense → r1_safe with in-sample search, 30/30 (worst 0.208 LSB OC); joint path tt/ss_cold/ff_hot passed (centre ≤ 0.052 LSB, simultaneous switching ≤ 0.006 LSB, delay ≤ 156 ns). Open: string-tap kick up to 71 mV on a full step (no false flag at 0.42 LSB margin), ss 125 °C residual 0.225 LSB, adders/search in r1_ctrl, area 19 682 µm² device. `r1_isense` follow-ups passed: MC at ss/ff (worst 48 µV), AZ loop PM ≥ 92.8°, hold droop ≤ 0.95 µV per 50 µs at 150 °C (bound). `blocks/r1_safe/README.md`, `blocks/r1_isense/README.md` |
| 2026-10-20 | T4 `r1_isense` and `r1_safe` (analog) at schematic level, all numbers simulated. r1_isense: G = 14 resistive difference amplifier with whole-channel auto-zero; settling to 0.5 % ≤ 206 ns (ss), bandwidth 9.1–15.2 MHz, 50-sample MC residual offset σ 16.2 µV (worst 35.5 µV), 1.05 mW and 8304 µm² device area per channel; all gates passed. r1_safe revision 2 (degenerated differential-difference comparators, shared 6-bit string): threshold vs code and delay (≤ 178 ns at 10 % overdrive) pass at tt/ss/ff without mismatch; revision 1 failed (input pairs saturate); DC mismatch MC fails (σ 32 mV Vod ≈ 1 LSB): calibration or comparator auto-zero needed. Layout not run. `blocks/r1_isense/README.md`, `blocks/r1_safe/README.md` |
| 2026-10-20 | T2 `r1_adc` schematic step 1: 12-bit SAR, two top-plate CDAC track-and-holds on one `trk` edge, 4-input mux on 2 slices, 6+6 bridge MIM CDAC (22 fF unit), monotonic switching, bootstrapped switches, double-tail comparator, XSPICE SAR logic, ideal VREF. Simulated (tt): static DNL within ±0.25 LSB (resolution), INL ≤ 0.49 LSB, no missing codes (lower half); 100.6 kHz at 2 MSPS ENOB 11.76 / 11.72 without device noise (≈ 11.35–11.55 with kT/C and estimated comparator noise); skew A–B 0 ps nominal, σ 7.6 ps under MOS mismatch. CDAC MIM MC **fails** DNL ≤ 0.5 LSB (median max |DNL| 0.94 LSB, 12/50 with missing codes): MSB-weight calibration or redundancy needed. Reference: up to 0.42 pC per bit cycle and VREF 1.2 V not possible at VDD 1.08 V (spec decision). Corners: ss/125 and ff/−40 windows only. `blocks/r1_adc/README.md` |
| 2026-10-20 | r1_afe (T3) schematic revision B simulated: two-stage PGA (rail-to-rail stage 1, level shift to 0.6 V), f3 ≥ 1.057 MHz at all corners and steps, MC pole matching ≤ 0.90 %, THD ≤ −65 dB, ×1 noise 0.35 LSB; ×32 noise at ss (35.3 µV vs 35) and the r1_adc-matched T/H residual (0.506 LSB) fail marginally; ≈ 0.084 mm², 1.5–1.8 mA (estimated/simulated). `blocks/r1_afe/README.md` |
| 2026-10-20 | `r1_osc` (T1) schematic revision r1 sized and simulated at schematic level (`blocks/r1_osc/README.md`): 5-bit trim monotonic, step ≤ 1.81 %, ss/1.08 V/125 °C reaches 32.61 MHz at code 0, loop delay ≤ 2.3 ns, 231 µA tt (all simulated). 30 MHz tt is at code 22, not mid code 16 (binary trim limit), so `OSC_TRIM` resets to 22. Jitter (white noise, code 22): 14.9 ps per period, 103 ps over 30 cycles. Layout and PEX not run. |
| 2026-10-20 | T6 `r1_padring` ring reference built from the G1 r4 ring cells for the 24-pin R1 map (1414 µm, empty core, core window 692.6 × 689.1 µm = 0.477 mm²). Run `ring-20261020-a`, GDS `3a477ab4…`. Main, maximal, precheck DRC and density (with fill) pass, 0 markers; antenna fails (12 markers on the 4 `IOPadIn` gates: empty core has no `vdd` gate load, control on G1 r4 without decaps reproduces it); projected LVS fails in the G1 form (substrate not tied to `VSS` without core p-taps) and passes in the ring-only form (261/261 devices); canonical LVS fails as on G1. Bond plan: 0 wire crossings, bond map verified. Bonding-service acceptance, PEX and the IHP intake pre-check: not run. `blocks/r1_padring/README.md`, `padframe/README.md` |
| 2026-10-20 | Incident: a T7 sub-agent ran `rm -rf` with a wrong relative path and deleted the working copy of `designs/g1-guardian`. Tracked files restored with `git checkout` (tree identical to HEAD, verified); 699 bulk-offload symlinks re-created from the offload directory; retained-outside-tree artifacts unaffected; untracked local caches (progress logs, waveform text dumps) in that directory are lost. Rule added to `blocks/README.md`. |
| 2026-10-20 | T5 `r1_ctrl` RTL draft 0.1 (pos, bus, gate logic, safe FSM, registers) and `R1_REGISTER_MAP.md` 0.1. Run `r1ctrl_20261020_r3`: V3 RTL vs float reference ≤ 0.021° el, after bench calibration 0.051° el (0.17° el with constant); 217 chip-level protocol/gate/safety checks passed at 21/30/42 MHz. Yosys cell area 0.221 mm² = 1.23 × the 0.18 mm² budget, macro estimate 0.34 mm² (1.88 ×): floorplan decision needed. LibreLane/STA not run. `blocks/r1_ctrl/README.md` |
| 2026-10-20 | T2b `r1_adc` revision 2: weight correction gives 50/50 samples without missing codes (DNL median 0.53, max 0.69 LSB); FS ±0.919 V, noise 58 µV tt / 82 µV ss-hot, reference buffer settles to 1 LSB, mux contract infeasible at 30 ticks; simulator tolerance finding (reltol 1e-3 + tmax 5 ns gave wrong comparator decisions up to 6 mV; reruns with tmax 0.2 ns). D16/D17 taken. ADC revision 3 items: noise at ss/125, buffer settling to 0.25 LSB. |
| 2026-10-20 | S4 (PDK data) and S5 (oscillator) done; specification open items 1 and 2 closed; three technical open items remain (reference buffer vs pin, 5 V heads, current-sample timing). |
| 2026-10-20 | Top-level specification draft 0.1 written (`specification/R1_TOP_LEVEL_SPECIFICATION.md`): blocks, 24-pin map, parameter classification, verification gates V1–V8, six open items. |
| 2026-10-20 | S1 done: ADC and accuracy numbers into the specification; CORDIC clock ≥ 25 MHz means a new or multiplied oscillator (open). |
| 2026-10-20 | S2 done: BiSS-C D2 control channel kept (read-only IDs). |
| 2026-10-20 | S3 done: as-written plan does not fit; decisions D1–D9 taken (§2a). |
| 2026-10-20 | Design chosen; skeleton and plan written; studies S1–S3 started. Name set to R1 (first draft said G2). Design-trace record rules added; durable copy of transcripts scheduled. |
| 2026-10-21 | T7 `r1_bgr` stability and noise (bgr-stb/noise-20261021-b, netlist unchanged): loop gain by Tian injection at 5 cuts × 12 corners (tt/ss/ff and the 9 TC-failure combinations) passed 60/60 (core loop PM ≈ 132°, GM ≥ 20 dB; smallest GM 12.9 dB, a DC positive-feedback loop); 3.3→3.0 V supply step dips `vref` 1.0 % for 0.2 µs, settles to 10 µV in 1.6 µs, no overshoot; `vref` noise 57 / 74 µV rms (10 Hz–100 kHz, tt / ss-125), 158 / 189 µV to 10 MHz, 1/f corner ≈ 6–7 kHz: 0.25 LSB (110 µV) needs a buffer-input pole ≤ 0.28 MHz (estimate), so a `vref` RC filter (≈ 5 pF) is open. |

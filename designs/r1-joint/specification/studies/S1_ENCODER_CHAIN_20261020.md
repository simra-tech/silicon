# S1 — encoder chain: input, accuracy budget, ADC, CORDIC (2026-10-20)

Study by an agent (Opus 5.5), text only; nothing simulated. Labels: L literature, D datasheet/PDK file, E estimated,
A assumed, [verify] not confirmed from the source.

## Input standard and frequency

| Source | Output | |
| --- | --- | --- |
| 1 Vpp industrial standard (Heidenhain) | 0.6–1.2 Vpp differential, CM 2.5 ± 0.5 V, amplitude ratio 0.8–1.25, phase 90° ± 10° el | L [verify] |
| TDK TAS2141 TMR | 1.5 Vpp differential at 5 V supply | D |
| iC-TW8 input | 20 mV–1.4 Vpp, ≤ 125 kHz | L |
| AMR/Hall heads without amplifier | ≈ 20–100 mVpp | A |

Recommendation: differential input 40 mVpp–1.4 Vpp with a ×1–×32 PGA (E); input common mode 0.5–2.8 V so the 3.3 V pad
ESD diodes stay off; resistive-input PGA on 3.3 V thick oxide, output referenced to a 0.6 V common mode in the 1.2 V
domain for the SAR. A 5 V head at 2.5 V CM + 0.6 V peak reaches 3.6 V: out of specification, board rule.

Signal frequency f = rpm/60 × cycles per revolution: on-axis magnet 10 000 rpm → 167 Hz; 32-pole ring 6 000 rpm →
3.2 kHz; 64-pole 10 000 rpm → 10.7 kHz; optical 2048 lines 6 000 rpm → 205 kHz; 5000 lines → 500 kHz (E).
Target: full accuracy to 100 kHz, count-safe to 250 kHz (≥ 4 samples per period at 1 MSPS). 500 kHz would need 2–4 MSPS
on 2–4 channels and does not fit the area (E).

## Accuracy budget (Heydemann 1981 ellipse model)

Resolution and accuracy differ: 14 bit/period = 0.022° el per LSB; absolute ±0.02° mechanical on a 32-pole track is
±0.64° el, only ≈ 9-bit accuracy (E).

| Error source | Angle error | Uncalibrated at 1 Vpp limits (E) | After register calibration (E) |
| --- | --- | --- | --- |
| Offsets | peak √(O_s²+O_c²)/A, 1st harmonic | 6.5 % → ±3.7° el | 0.1 % → ±0.06° el |
| Gain ratio 1+g | (g/2)·sin 2φ | g = 0.25 → ±7.2° el | 0.2 % → ±0.06° el |
| Quadrature error α | ≈ α/2 DC + (α/2)·cos 2φ | 10° → 10° p-p | 0.1° → 0.1° p-p |
| Harmonic k, h_k | ≈ h_k at (k±1)φ | h3 = 1 % (A) → ±0.57° el | with H3 term → ±0.1° el |
| Noise σ_n | σ_φ = σ_n/A rad rms | — | — |
| sin/cos sampling skew Δt | 2π·f·Δt | — | 1.4 ns → 0.05° el at 100 kHz |
| ADC INL | ≈ INL/A | — | 2 LSB of 12 b → 0.07° el |

Heydemann correction: x = u₁ − p; y = [(u₂ − q)/r − x·sin α]/cos α (two multiplies per sample). Calibration reduces
electronic error from ≈ ±10° el to < ±0.2° el (E); without it the ±0.64° el target fails. Magnetic heads have h3 ≈ 0.5–2 %
(A [verify]): add a 3rd-harmonic correction (amplitude, phase). No NVM: optional background tracker of offset/gain from
per-period min/max (iC-TW8 has similar automatic correction, L), bounded and flagged so it cannot hide a failing head.

ENOB (signal at 80 % of full scale, σ_φ ≈ 0.72/2^N rad): 14 bit/period every sample → ENOB 11.9; 16 bit/period every
sample → 13.9; 16 bit/period with 16× averaging (62.5 kS/s output) → 11.9 (E).
Result: 12-bit 1 MSPS SAR with ENOB ≥ 11.5; simultaneous sin/cos sampling with skew < 0.5 ns; anti-alias poles matched
to 1 % with f_c ≥ 1 MHz (≈ 0.06° el at 100 kHz); 16-bit resolution from averaging or a tracking filter. Latency: 2 µs at
100 kHz is a 72° el lag, so latch position at the bus request or extrapolate with velocity (E).

## ADC choice

| Criterion | SAR 12 b 1 MSPS × 2 | 2nd-order ΣΔ (OSR 64, ≈ 13 MHz) | Analog tracking (iC-NQ style) |
| --- | --- | --- | --- |
| Matching-critical part | CDAC (MIM) | none | sine-weighted resistor DAC |
| Latency | 1 µs | several µs (decimator) | low, zero lag at constant speed |
| Raw samples for calibration | yes | yes | no |
| Digital cost | small | 2 decimators, several kGE each | loop counter |
| Area, two channels (E) | 0.08–0.12 mm² | 0.1–0.2 mm² | ≈ 0.1 mm² |

Recommendation: SAR, followed by a digital type-II tracking loop for filtering and velocity. Anchors: 12 b 45 MS/s 130 nm
0.059 mm² (Liu/Huang/Chiu ISSCC 2010, L [verify]); 12 b 1 MS/s 180 nm 26 µW 0.049 mm² (L); 12 b 2 MS/s 180 nm 0.36 mm² (L).
Per ADC 0.04–0.06 mm², 0.1–0.3 mW; reference buffer ≈ 0.02 mm² and 0.5–1 mA unless an external decap pin is used (E).

CDAC with MIM 1.5 fF/µm² ±10 % (D, `cornerCAP.lib`): kT/C needs ≥ 0.3 pF per side at 2.4 Vpp differential FS; INL ≤ 2 LSB
at 3σ needs σ_u/C_u ≤ 1.5 %, DNL ≤ 0.5 LSB needs ≤ 0.26 % (E); MIM matching coefficient for SG13G2 unknown (extract or
MC). A full binary 12-bit array (10 fF units) is 41 pF per side ≈ 0.055 mm² per ADC: too large. Use a split (bridge) 6+6
array or monotonic top-plate switching: ≈ 1.3 pF per side, ≈ 0.005 mm² per side with overhead (E); bridge-cap gain error
folds into the gain-ratio calibration. Starting point: IHP-AnalogAcademy `module_3_8_bit_SAR_ADC` (comparator, SAR logic,
array, layout parts), extended to 12 bits with redundancy, bootstrapped switch, comparator noise σ < 0.3 LSB.

## CORDIC, alternatives, nonius

CORDIC vectoring, 16-bit angle: 18 iterations; 20-bit x/y datapath; 18-bit angle accumulator with 18 × 18-bit arctan ROM;
magnitude output (×1.647) feeds signal-loss and amplitude flags (E).

| Variant | Gates (E) | Area at ≈ 10 µm²/GE | Latency |
| --- | --- | --- | --- |
| Iterative, 1 iteration/clock at 25 MHz | 1.5–2.5 kGE | 0.02–0.03 mm² | ≈ 0.8 µs |
| Fully pipelined | 25–35 kGE | 0.3 mm² (does not fit) | 18 clocks |
| LUT + linear interpolation (octant fold, 256 entries) | ROM-dominated | 0.03–0.05 mm² | 2–3 clocks |
| Tracking loop only | ≈ 1 kGE | 0.01 mm² | zero lag at constant speed |

Recommendation: iterative CORDIC + tracking loop; with calibration multipliers and registers the position block is
≈ 8–12 kGE, 0.08–0.12 mm² (E). Nonius (N and N−1 periods): θ_c = (φ_M − φ_N) mod 2π; k = round((N·θ_c − φ_M)/2π);
θ = (2πk + φ_M)/N; unambiguous if |e_M| + |e_N| < 180°/N el (N = 32: < 5.6° el, use ±1.4° el per track for 2× margin).
Dual-track needs four analog channels (8 pins differential): if ever added, run nonius at power-up/standstill through an
input mux, then count master periods, recheck at low speed. (R1 PLAN.md D1 drops the second track.)

## Proposed register set (host-loaded, ≈ 200 bits ≈ 0.015 mm² of flops, E)

OFFSET_SIN, OFFSET_COS 12 b signed · GAIN_RATIO 12 b (1.0 ± 25 %) · PHASE 10 b signed ±16° (sin α, 1/cos α from a small
LUT) · H3_AMP, H3_PHASE 8 + 8 b · ZERO_OFFSET 16–21 b · DIRECTION 1 b · RESOLUTION 4 b (10–16 bit/period) · PGA_GAIN 3 b ·
FILTER_CFG (averaging, tracking bandwidth) · AUTOCAL_EN 1 b · STATUS sticky W1C 8 b (amplitude low/high, overspeed
> 90° el per sample, ADC overrange, calibration invalid, calibration CRC, clock fault) · AMPLITUDE 12 b RO · CAL_CRC 8 b
checked by hardware.

## Risks and open questions

1. Pin count (resolved by PLAN.md D1/D2/D7/D8). 2. Area: 2 SAR + ref buffer + PGA + position block ≈ 0.25–0.3 mm² of
0.47 (E); current channels share the SAR (PLAN.md D3). 3. MIM matching coefficient and minimum unit cap unknown.
4. Input CM above 2.8 V from 5 V heads: pad diode conduction (G1 lesson: pad-diode stall). 5. ADC supply domain (1.2 V vs
3.3 V) sets FS, kT/C, bootstrap, level shifters. 6. Reference buffer vs external decap pin. 7. Latency vs BiSS sample
point. 8. Harmonic content of target heads. 9. CORDIC needs ≥ 25 MHz: the G1 oscillator (≈ 9.4 MHz) may not suffice;
jitter adds 2π·f·σ_j. 10. Auto-calibration vs safety: bound and flag. 11. iC-Haus datasheets need a login; values came
from press articles or memory.

Sources: Heydemann 1981 https://doi.org/10.1364/AO.20.003382 · iC-TW8 https://www.eenewseurope.com/en/precision-interpolation-circuit-for-16-bits-with-automatic-correction/ ,
https://www.ichaus.de/product/ic-tw8/ · iC-MU https://www.ichaus.de/product/ic-mu/ · iC-NQC https://www.ichaus.de/product/ic-nqc/ ·
Heidenhain interfaces https://www.heidenhain.us/wp-content/uploads/2022/07/PR_Interfaces_ID1078628_en.pdf · TAS2141
https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/TDK-TAS2141-AAAB_C180181.pdf · vernier
https://air.unipr.it/retrieve/6500fd5f-f7d5-4cc8-ad77-37cce2780c83/Absolute_Two-tracked_Optical_Rotary_Encoders_Based_on_Vernier_Method.pdf ·
12 b 1 MS/s SAR https://www.researchgate.net/publication/301306878 · 0.13 µm SAR https://link.springer.com/10.1007/s10470-014-0318-9 ·
IHP-AnalogAcademy https://github.com/IHP-GmbH/IHP-AnalogAcademy/tree/main/modules/module_3_8_bit_SAR_ADC · PDK `cornerCAP.lib`, `sg13g2_stdcell.lef`.

## Addendum (second pass of the same study)

- Root-sum-square after calibration ≈ 0.24° el (offset 0.06, gain 0.06, phase 0.1, H3 0.1, electronics 0.15), inside
  the ±0.64° el target; the remaining ≈ 0.4° el is left for ring pitch error and eccentricity, which the chip cannot
  remove (assumed allocation).
- Two differential 12-bit SARs in the 1.2 V domain (2.4 Vpp differential full scale), top-plate sampling, monotonic
  switching, split 6+6 bridge array (≈ 128 units, ≈ 1.3 pF per side, ≈ 900 µm²); ADC pair with reference buffer ≈ 0.12 mm²
  (≈ 25 % of the core, E). The reference buffer (0.5–1 mA) dominates ADC power.
- Count-safe needs f_s ≥ 4·f_sig (< 90° el per sample). A host-loaded 64-entry error LUT (≈ 768 bits ≈ 0.05 mm²) is a cut
  candidate, not baseline. Registers ≈ 250 bits.
- With PLAN.md D3 (one SAR, two track-and-holds, current channels multiplexed) the sampling simultaneity is kept by the
  track-and-holds and the conversion rate must be ≥ 2 MSPS to keep 1 M sample pairs per second; the two-SAR variant is the
  alternate if the floorplan closes with it.

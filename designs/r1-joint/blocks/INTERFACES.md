# R1 block interface contracts (0.1, 2026-10-20)

Binding for revision-2 work. A change needs a dated row here and in both block READMEs.

| Interface | Contract |
| --- | --- |
| AFE → ADC | Two differential outputs, 1.44 Vpp full input (80 % of the ADC ±0.9 V FS, D16; was 1.6 Vpp / ±1.0 V), common mode 0.6 V from the ADC `vcm2` port; load per side: top-plate CDAC 2.8 pF, 250 ns track window, top plate near 0 V at track start; settling ≤ 0.25 LSB at 12 bits within the track window. |
| isense → ADC mux | Differential ±0.85 V at ≈ 0.57 V CM (gain 14, 40.38 mV pedestal); sampled at the centre strobe `is_smp_a/b` from `r1_ctrl`; same CDAC load as above. |
| isense → safe | The isense differential output drives the four window comparators directly (OC_A, NEG_A, OC_B, NEG_B). |
| safe → ctrl | Four asynchronous flags `oc_a, neg_a, oc_b, neg_b` (active high, 1.2 V domain after level shift); threshold codes `thr_oc[5:0]`, `thr_neg[5:0]` per channel; per-comparator offset-calibration codes `cal_oc_a[5:0]` etc. summed into the threshold DAC; `az_win` strobe from ctrl marks the isense auto-zero window; ctrl runs the calibration search in the zero-current time *after* `az_win` (change 2026-10-20 from T4b: during the window the isense output is not valid), one comparator per PWM period, successive approximation over the 6-bit code (step LSB/8 of the threshold DAC, range about ±4 LSB). The four code adders and the search live in ctrl; the analog block exposes `cal_*[5:0]` inputs only. |
| ADC → ctrl | Per conversion: 14 raw decision bits (12 + 2 redundant, D17) and `valid`, both slices in parallel (own comparator and sequencer); ctrl computes code = Σ b_i·w_i with host-loaded weights `w[13:0]` (14 bit each); conversion ≤ 17 ticks; frame = 36 ticks at 30 MHz: {SIN, COS} pair then {ISA, ISB} pair, strobes from ctrl (change 2026-10-20; was 13 bits, 15 ticks, 1 µs frame). ctrl ports added in revision 0.2: `cal_*` codes, `adcw` weights, `sc_pend`, sub-tick LAT. |
| ADC reference | ≈ 0.92 V at the CDAC from a unity-gain on-chip buffer fed by the bandgap (D16); revision 2 buffer 422 µA from 3.3 V with 31 900 µm² MIM settles to 1 LSB at ±0.88 V; revision 3 target 0.25 LSB. |
| osc → ctrl | `clk30` (23–39 MHz untrimmed at code 22, up to 54.9 MHz if the host writes code 0 at ff); `osc_trim[4:0]` reset 22 (D13); `osc_en`. STA closes at 42 MHz; a count outside the expected window sets the clock-fault bit. |
| bgr → all | `vref` 1.045 V (G1 lineage), `iptat`; threshold DAC reference for safe; T2F bias. |
| t2f → ctrl | Frequency output counted by ctrl over a fixed window into `TEMP_COUNT`. |
| ctrl → gate | `pwm_a/b/c` (dead time inserted in ctrl), `gate_en` (low on fault or EN/STO_IN low); gate pads `sg13g2_IOPadOut30mA` through the 1.2 → 3.3 V level shifters. |
| pads | 3.3 V IO; MA/SCLK and SLO/SDO shared per specification §3. |

## Open contract mismatches (2026-10-20, found at the round-2 review)

| Interface | Mismatch | Resolution |
| --- | --- | --- |
| safe → ctrl, calibration search | `r1_safe` revision 3 (README and `sim/cal_model.py`) defines the result as k_cal = 32 + round((k_rel + k_trip)/2 − k_ideal) with k_ideal = 36.31 (OC) / 27.69 (NEG) at cell code 14 (NEG 49, i.e. `thr_neg` = 14), a two-sided search so the hysteresis cancels. `r1_ctrl` revision 0.2 (`rtl/r1_cmpcal.v`) does a one-sided successive approximation and stores the raw toggle code. Applied as is, the OC threshold shifts by about 4.3 steps (0.54 LSB) plus half the hysteresis, so the 0.25 LSB criterion fails. | ctrl revision 0.3: store cal = 32 + toggle − CAL_IDEAL (new register, 6 bits per comparator type, reset 36 / 28) and either run the search in both directions (14 windows, average) or subtract a host-written half-hysteresis constant. `r1_safe` to state the hysteresis in calibration steps at corners. `THR_ZERO` = 14 for all four comparators is consistent with both sides. |

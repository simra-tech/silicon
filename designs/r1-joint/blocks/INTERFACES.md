# R1 block interface contracts (0.1, 2026-10-20)

Binding for revision-2 work. A change needs a dated row here and in both block READMEs.

| Interface | Contract |
| --- | --- |
| AFE → ADC | Two differential outputs, 1.6 Vpp full input (80 % of the ADC ±1.0 V FS, D11), common mode 0.6 V from the ADC `vcm2` port; load per side: top-plate CDAC 2.8 pF, 250 ns track window, top plate near 0 V at track start; settling ≤ 0.25 LSB at 12 bits within the track window. |
| isense → ADC mux | Differential ±0.85 V at ≈ 0.57 V CM (gain 14, 40.38 mV pedestal); sampled at the centre strobe `is_smp_a/b` from `r1_ctrl`; same CDAC load as above. |
| isense → safe | The isense differential output drives the four window comparators directly (OC_A, NEG_A, OC_B, NEG_B). |
| safe → ctrl | Four asynchronous flags `oc_a, neg_a, oc_b, neg_b` (active high, 1.2 V domain after level shift); threshold codes `thr_oc[5:0]`, `thr_neg[5:0]` per channel; per-comparator offset-calibration codes `cal_oc_a[5:0]` etc. summed into the threshold DAC; `az_win` strobe from ctrl marks the isense auto-zero window during which ctrl searches each calibration code for the comparator toggle at zero input. |
| ADC → ctrl | Per conversion: 13 raw decision bits (12 + 1 redundant, D12) and `valid`; ctrl computes code = Σ b_i·w_i with host-loaded weights `w[12:0]` (14 bit each); conversion ≤ 15 ticks at 30 MHz; mux sequence per 1 µs frame: {SIN, COS} pair then {ISA, ISB} pair, strobes from ctrl. |
| ADC reference | 1.0 V from an on-chip buffer fed by the bandgap (VREF 1.045 V divided); buffer must settle 0.42 pC per 33 ns bit cycle; MIM decoupling on chip. |
| osc → ctrl | `clk30` (23–39 MHz untrimmed at code 22, up to 54.9 MHz if the host writes code 0 at ff); `osc_trim[4:0]` reset 22 (D13); `osc_en`. STA closes at 42 MHz; a count outside the expected window sets the clock-fault bit. |
| bgr → all | `vref` 1.045 V (G1 lineage), `iptat`; threshold DAC reference for safe; T2F bias. |
| t2f → ctrl | Frequency output counted by ctrl over a fixed window into `TEMP_COUNT`. |
| ctrl → gate | `pwm_a/b/c` (dead time inserted in ctrl), `gate_en` (low on fault or EN/STO_IN low); gate pads `sg13g2_IOPadOut30mA` through the 1.2 → 3.3 V level shifters. |
| pads | 3.3 V IO; MA/SCLK and SLO/SDO shared per specification §3. |

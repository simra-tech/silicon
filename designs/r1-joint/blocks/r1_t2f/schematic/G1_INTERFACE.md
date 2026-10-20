# G1_T2F control interface

Bits the sensor needs from the register file (`G1_CTRL`). All three are static
levels, not pulses. They leave the 1.2 V register file and enter the 3.3 V analog
domain through the wrapper's level shifters (plan D8); the sensor itself has no
1.2 V control inputs.

| Register bit | Analog pin | Domain at the pin | Reset value | Meaning |
| --- | --- | --- | --- | --- |
| `T2F_EN` | `g1_t2f.en` | 3.3 V logic | 1 | 1: oscillator runs, `TEMP_OUT` toggles. 0: both timing capacitors held discharged, RS latch held in `q=0`, `fout` low; bias legs stay on (about 36 µA from `IOVDD`). |
| `T2F_MODE` | `g1_t2f.mode` | 3.3 V logic | 0 | 0 (PTAT): comparator threshold = V<sub>REF</sub>, f = I<sub>PTAT</sub> / (2 C V<sub>REF</sub>), proportional to absolute temperature. 1 (REF): threshold = 2 I<sub>PTAT</sub> R<sub>REF</sub>, f = 1 / (4 R<sub>REF</sub> C), temperature independent to first order. The ratio f<sub>PTAT</sub>/f<sub>REF</sub> = 2 ΔV<sub>BE</sub> R<sub>REF</sub> / (R<sub>1</sub> V<sub>REF</sub>) removes C, the threshold and the comparator delay to first order (see the README, "Ratio readout"). |
| `BGR_R4` | `g1_bgr.r4` | 3.3 V logic | 0 | 0: HBT area ratio 1:8. 1 (RATIO test): a second unit HBT is connected in parallel with Q1, ratio becomes 2:8 = 1:4; ΔV<sub>BE</sub> = V<sub>T</sub> ln 4, I<sub>PTAT</sub> falls to about 0.66×, V<sub>REF</sub> falls by about 0.12 V (see the bandgap README). Diagnostic only: verifies the bias-independence of the HBT ideality factor (f<sub>PTAT</sub>(1:8) · V<sub>REF</sub>(1:8) / (f<sub>PTAT</sub>(1:4) · V<sub>REF</sub>(1:4)) should equal ln 8 / ln 4 = 1.5). |

Suggested packing: one register byte `TEMP_CTRL` = `{5'b0, BGR_R4, T2F_MODE, T2F_EN}`.

Measurement modes seen from the pad:

| `BGR_R4` | `T2F_MODE` | Name | What `TEMP_OUT` carries |
| --- | --- | --- | --- |
| 0 | 0 | PTAT | f ∝ T, about 1.6 MHz at 27 °C (simulated, nominal); calibrated reading |
| 0 | 1 | REF | f ≈ constant, about 1.6 MHz; divide the PTAT reading by this one for the ratio readout |
| 1 | 0 | RATIO | f ∝ T with ΔV<sub>BE</sub> = V<sub>T</sub> ln 4; consistency check of the HBT ideality factor |
| 1 | 1 | — | REF threshold with the 1:4 core; not used |

Notes for the digital owner:

- `TEMP_OUT` is a free-running 1.2 V CMOS square wave from `g1_t2f.fout` to the
  `sg13g2_IOPadOut16mA` cell; no divider is needed (1 to 3 MHz over the range).
  There is no on-chip counter; the frequency is counted off-chip. If a gate-time
  counter is added later it belongs in `G1_CTRL` and should count both modes with
  the same gate.
- `fout` is undefined for about 1 µs after `T2F_EN` rises (first ramp).
- `T2F_EN` low does not power the block down; the analog current stays.
- The bandgap has no enable and no control bit besides `BGR_R4`.

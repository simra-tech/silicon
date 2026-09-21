# G1 measurement plan

All items **not run**. Ten packaged parts are planned.

## Fixture

A small board with a QFN24 socket, an external logic-level N-FET and a
low-side shunt in the load return, Kelvin traces from the shunt to `SENSE_P`
and `SENSE_N`, header access to every pin, and a paddle connection brought out
to a jumper. Board material rated for the full temperature range below.

## Sequence per part

1. Zero-power checks: pin-to-pin leakage, supply current at 1.2 V and 3.3 V.
   Power-up order on the fixture is always `VDD` before or together with
   `IOVDD`; record `GATE` during the ramp (expected low with `EN` low).
   `VDDA` (pin 7) and `IOVDD` are fed from one 3.3 V rail through separate
   jumpers so the analog supply current can be measured on its own.
2. Reference and sensor: `VREF` and `TEMP_OUT` at room temperature; serial
   register readback.
3. Breaker: electronic load steps at 1.5×, 2×, 4× nominal with programmable
   durations; record trip/no-trip, time from step to gate low, retry behaviour.
   Then replay a recorded compute-load current profile through the load and
   confirm no trip; inject a step latch-up signature on top and confirm trip.
4. Device corner: `npn13G2` Gummel and output curves on `HBT_E/B/C`, keeping
   V<sub>CE</sub> at or below 1.6 V (the model card's `vce_max`) except in a
   deliberate, last, breakdown sweep on one part;
   `D_STD` and `D_ELT` off-current at `G_SHARED` = 0 V with the drain at 0.1 V
   (primary) and at the device's rail (1.2 V thin-oxide, 3.3 V thick-oxide).
   During irradiation the shared gate is biased at 1.2 V: this is worst case for
   the thin-oxide device and under-biases the thick-oxide device, and is chosen
   so the thin-oxide gate is never over-stressed. Record the bias in the log.
5. Temperature: repeat 2 to 4 at −40, 25, 85, 125, 150 and 175 °C on a
   hotplate or chamber, and at 77 K in liquid nitrogen. Short soaks above
   150 °C.
6. Dose: two parts kept as controls; pairs irradiated to four dose levels at
   a Co-60 or X-ray source; repeat 2 and 4 after each step and after room-
   temperature and 100 °C annealing steps.

## What each measurement decides

| Measurement | Decides |
| --- | --- |
| Trip time versus step amplitude | whether the sense-amp bandwidth and comparator meet the sub-10 µs target |
| Load-profile replay | whether the I²t profile discriminates load steps from latch-up |
| `TEMP_OUT` versus temperature | sensor slope, linearity, and whether the HBT law holds at 77 K |
| `D_STD/D_ELT` ratio versus dose | whether the leakage-ratio canary has usable range and is monotonic |
| Pad leakage reference on an unused analog pin path | the pre-irradiation off-current of the thick-oxide canary is tens of fA at room temperature (simulated), far below the analog pad's ESD leakage; the bench must measure and subtract the pad contribution, otherwise `D_ELT` reads the pad, not the device |
| `HBT_B` current at low V<sub>BE</sub> versus dose | second dose observable; model input |
| `VREF` versus dose and temperature | reference drift |
| SEU counter | only with beam time; otherwise records zero and is reported as not exercised |

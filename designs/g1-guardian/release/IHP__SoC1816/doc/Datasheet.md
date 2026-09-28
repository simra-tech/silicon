# SoC1816 (G1 guardian): datasheet summary

Status: design data only. **Nothing has been fabricated or measured**; values below are
specified or simulated as labelled. Full specification: `doc/Specification.md` (a copy of
`designs/g1-guardian/specification/G1_TOP_LEVEL_SPECIFICATION.md` from
https://github.com/simra-tech/silicon; its relative links point into that repository).

| Item | Value | Basis |
| --- | --- | --- |
| Process | IHP SG13G2 open PDK, commit `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` | design record |
| Die | 1414 x 1414 um (1.999396 mm2), seal ring included; bbox (0,0)-(1414,1414) um | KLayout on the release GDS |
| Supplies | VDD 1.2 V core; IOVDD 3.3 V IO; VDDA 3.3 V analog (tied to IOVDD on the board) | specified |
| Package | QFN24, 4 x 4 mm, 0.5 mm pitch; pad to the lead directly opposite | specified; availability on the IHP run not confirmed |
| Pads | 24 `sg13g2_io` cells, 70 x 70 um TopMetal2 bond pads, 65.8 x 65.8 um passivation openings | KLayout on the GDS |

## Pin map (die pad / QFN24 lead / pin / function)

| Pad | Lead | Pin | Function |
| ---: | ---: | --- | --- |
| 1 | 1 | VDD | 1.2 V core supply |
| 2 | 2 | VSS | core ground, substrate |
| 3 | 3 | IOVDD | 3.3 V IO supply |
| 4 | 4 | IOVSS | IO ground |
| 5 | 5 | VSS | second ground pad |
| 6 | 6 | IOVSS | second IO ground pad |
| 7 | 7 | VDDA | 3.3 V analog supply |
| 8 | 8 | SENSE_P | shunt Kelvin, positive |
| 9 | 9 | SENSE_N | shunt Kelvin, negative |
| 10 | 10 | GATE | external N-FET gate (30 mA output pad) |
| 11 | 11 | FAULT_N | low while tripped |
| 12 | 12 | EN | enable / reset of the trip latch |
| 13 | 18 | TRIP_SET | not connected in the core on this revision |
| 14 | 17 | SCLK | serial clock |
| 15 | 16 | SDI | serial data in |
| 16 | 15 | SDO | serial data out |
| 17 | 14 | TEMP_OUT | temperature as frequency |
| 18 | 13 | VREF | bandgap output, for test |
| 19 | 24 | G_SHARED | canary pair gate |
| 20 | 23 | D_STD | standard NMOS drain |
| 21 | 22 | D_ELT | HV NMOS drain (legacy pin name) |
| 22 | 21 | HBT_E | test HBT emitter |
| 23 | 20 | HBT_B | test HBT base |
| 24 | 19 | HBT_C | test HBT collector |

## Selected simulated results (chip-level layout netlist, r4)

- Hard fault 1.8x: GATE below 1 V 1.5432 / 1.7263 / 1.4334 us after the fault at tt 27 C / ss 125 C / ff -40 C (simulated).
- Hard threshold: 0.97x of the code no trip, 1.03x trips, at every corner, temperature and supply tried (simulated).
- Bandgap VREF 1.04546 V at 27 C, nominal TC 8.53 ppm/C (simulated, block level).
- Temperature sensor about 1.51 MHz at 25 C, 4.909 kHz/C (simulated, block level).

## Board rules (required, from the specification section 6)

VDD must be in regulation before IOVDD/VDDA rise and stay until they are down; an independent
load-bus inhibit during every power-up; VDD and 3.3 V supervisors; FET hold-off against drain
dV/dt; EN low at power-up. See `doc/Specification.md` section 6.

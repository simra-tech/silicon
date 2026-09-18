# G1 blocks

One directory per block will be created as work starts. Until then this table
is the index. Lineage names the internal reference design a block starts from,
where one exists; every block is re-verified here regardless.

| Block | Starts from | First deliverable | Status |
| --- | --- | --- | --- |
| `G1_SENSE` | two-stage OTA reference | schematic, offset Monte Carlo, bandwidth | not started |
| `G1_TRIP` | StrongARM comparator reference | schematic, delay and hysteresis sims; timer RTL | not started |
| `G1_BGR` | new | schematic, V<sub>REF</sub>(T) sim over −196 °C to 175 °C | not started |
| `G1_T2F` | temperature-to-frequency reference | HBT ΔV<sub>BE</sub> core, frequency versus T sim | not started |
| `G1_DOSE` | new | ELT NMOS layout, DRC, extraction rule, I<sub>off</sub> sim | not started |
| `G1_SEU` | new | RTL for plain and TMR register, LibreLane run | not started |
| `G1_CTRL` | new | register map, serial interface RTL, state machines | not started |
| `G1_PADRING` | LibreLane SG13G2 chip flow | ring with 24 cells, DRC | not started |
| `G1_TOP` | — | AMS co-simulation of breaker path with a load model | not started |

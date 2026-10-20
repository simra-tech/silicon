# R1 — open joint front-end (SiGe BiCMOS, in specification)

A mixed-signal chip for one robot joint: it reads an incremental or dual-track sine/cosine
encoder head, measures phase currents on low-side shunts, measures winding temperature, runs an
independent hardware safety channel, drives external low-side FETs through three gate outputs and
reports position, current and status over BiSS-C, SSI or SPI. Target process is the IHP SG13G2
open PDK, die area budget 2 mm², QFN24 through the PDK's `sg13g2_io` ring, as for
[G1](../g1-guardian/).

**State (2026-10-20): in specification.** No block has been simulated, laid out or checked for this
design. Every status below is *not run*.

## Why this chip

Every joint of a cobot, quadruped or humanoid needs the same five things: a position reading from
the encoder head, phase currents for torque control, winding temperature, a safety path that can cut
torque independently of the controller, and a field bus. Open-hardware joint controllers build this
from catalogue parts on a board; no open ASIC exists. R1 is that ASIC, scaled to what fits in
2 mm² and 24 pins.

## Blocks (planned)

| Block | Function | Origin |
| --- | --- | --- |
| `r1_afe` | Differential sine/cosine input, programmable gain, anti-alias filter | new |
| `r1_adc` | Two 12–14-bit SAR ADCs, simultaneous sampling of sine and cosine | new |
| `r1_pos` | CORDIC arctangent, offset/gain/phase calibration, dual-track (nonius) absolute combination, ABZ output | new (digital) |
| `r1_bus` | BiSS-C slave, SSI slave, SPI register access, CRC | new (digital) |
| `r1_isense` | Two low-side shunt sense amplifiers with auto-zero; third phase computed | G1 `g1_sense` lineage |
| `r1_safe` | Window comparators, I²t winding model, watchdog, latched fault / STO output | G1 `g1_trip` lineage |
| `r1_pwm` | Commutation / PWM pattern generator for three external low-side FETs | new (digital) |
| `r1_gate` | Three gate outputs | G1 `g1_gate` lineage |
| `r1_bgr` | SiGe bandgap reference | G1 `g1_bgr` |
| `r1_t2f` | Temperature to frequency | G1 `g1_t2f` |
| `r1_osc` | On-chip oscillator | G1 `g1_osc` |
| `r1_padring` | 24-pad `sg13g2_io` ring | G1 `g1_padring` |

The cut list, in the order blocks are dropped if area or schedule demands it, is in
[`PLAN.md`](PLAN.md).

## Status

| Check | Status |
| --- | --- |
| Specification | in progress |
| Block simulation | not run |
| Layout, DRC, LVS, PEX | not run |
| Digital flow, STA, GLS | not run |
| Full-chip simulation | not run |
| Measurement | not run |

## Built against

| Item | Version | How established |
| --- | --- | --- |
| PDK | to be pinned (G1 used `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`) | not yet run |
| ngspice, KLayout, xschem, LibreLane | to be pinned from the `flow/` container image | not yet run |

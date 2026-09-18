# G1 — radiation-aware node guardian (SiGe BiCMOS test chip)

A small mixed-signal die that protects a commercial compute load from single-event
latch-up, and reports the temperature, accumulated dose and upset rate it sees.
Four functions on one 1 × 1 mm die, packaged in QFN24, measured on a board:

1. a current-limiting **breaker**: shunt sense amplifier, trip comparator, I²t
   timer and gate drive for an external switch, with a trip profile that lets a
   fast load step through and cuts a latch-up signature;
2. a **temperature sensor** with a one-wire frequency output, built on the
   HBT ΔV<sub>BE</sub> law so it stays valid far outside the commercial range;
3. a **dose canary**: a standard NMOS beside an enclosed-layout NMOS at equal
   bias, whose off-current ratio tracks total ionizing dose;
4. an **upset canary**: a scrubbed shift register whose upset count is reported.

A SiGe bandgap supplies the reference, and a three-wire serial interface exposes
telemetry and trip settings. A bare HBT and the canary transistors are also
brought out to pins for direct device characterisation.

Target process is the IHP SG13G2 open PDK (0.13 µm SiGe BiCMOS). The die uses
the PDK's `sg13g2_io` cells as its pad ring, six per side, and is wire-bonded
into a QFN24 package.

**State: in specification. No block has a schematic, simulation or layout in
this directory yet. Nothing has been fabricated or taped out. Every check in
the tables below is *not run*.**

## What the chip is meant to do

| Block | Function | Devices | Domain | Est. area |
| --- | --- | --- | --- | ---: |
| `G1_SENSE` | Kelvin shunt sense amplifier, low-side, gain 20 | `npn13G2` input pair, thick-oxide MOS | 3.3 V | 0.004 mm² |
| `G1_TRIP` | Fast comparator plus I²t integrator/timer with programmable thresholds | CMOS comparator, digital timer | 1.2 V | 0.005 mm² |
| `G1_GATE` | Gate driver for an external low-side logic-level N-FET, latched or retriggering | `sg13g2_IOPadOut30mA` | 3.3 V | pad |
| `G1_BGR` | Bandgap reference and PTAT current | `npn13G2`, thick-oxide MOS, `rppd` | 3.3 V | 0.010 mm² |
| `G1_T2F` | Temperature-to-frequency sensor, HBT ΔV<sub>BE</sub> core, ring-oscillator readout | `npn13G2`, LV CMOS | 1.2 V | 0.006 mm² |
| `G1_DOSE` | Standard-NMOS / enclosed-layout-NMOS pair with on-chip leakage readout, both drains also pinned out | `sg13_lv_nmos`, drawn ELT | 1.2 V | < 0.001 mm² |
| `G1_SEU` | 1024-bit shift register, plain and triple-modular-redundant, scrubbed and counted | LV CMOS standard cells | 1.2 V | 0.030 mm² |
| `G1_CTRL` | Register file, serial interface, scrub and trip state machines | LV CMOS standard cells | 1.2 V | 0.020 mm² |
| `G1_DUT` | One bare `npn13G2` with E, B, C on pins | `npn13G2` | — | < 0.001 mm² |
| `G1_PADRING` | 24 `sg13g2_io` cells, 4 corners, fillers | `sg13g2_io` | 3.3 V / 1.2 V | 0.38 mm² |

Core area is well under the roughly 0.35 mm² available inside the ring; see
[`padframe/`](padframe/README.md) for the geometry. Full specification, pin map
and parameter classification: [`specification/G1_TOP_LEVEL_SPECIFICATION.md`](specification/G1_TOP_LEVEL_SPECIFICATION.md).

## Built against

| Thing | Version | How it will be established |
| --- | --- | --- |
| PDK | IHP SG13G2, commit `144f811cdffda49b71d28f64e8a92b697b61cf06` (target; to be confirmed from the `COMMIT` file of the install used for the first simulation) | `COMMIT` file at the PDK install root |
| ngspice | not yet run | simulator banner in each run log |
| KLayout | not yet run | `klayout -v` |
| xschem | not yet run | `v {xschem version=...}` header of each `.sch` |
| LibreLane | not yet run | flow log header |

## What was actually measured

Nothing. No simulation has been run for this design. The first results to be
recorded here are, in order: HBT ΔV<sub>BE</sub> versus temperature from the PDK
model, sense-amplifier offset Monte Carlo, comparator delay, and the trip-profile
behaviour against a synthetic load-step waveform.

## Assumptions carried into the design

| Assumption | Status |
| --- | --- |
| Drawn, non-PCell transistor geometry (the enclosed-layout NMOS in `G1_DOSE`) is acceptable on the target shuttle provided it is DRC-clean and its extraction is documented | **assumed accepted; foundry confirmation pending** |
| Wire-bonding of 80 × 180 µm `sg13g2_io` bondpads at 80 µm pitch into QFN24, with the die paddle bonded out as a substrate connection | **assumed; bonding-service confirmation pending** |
| Package survives −196 °C to +175 °C for characterisation soaks | assumed from generic epoxy-lid QFN limits; not verified |
| Low-side shunt sensing with common mode within −0.1 V to +0.3 V of ground | design choice |
| Trip response target under 10 µs from overcurrent to gate low | design target, not yet simulated |

## What remains unverified

Everything. Specifically: no schematic, no DRC, no LVS, no PEX, no post-layout
simulation, no antenna or density check, no precheck-deck run, no IO ring
assembly, no measurement. Each of those is listed as *not run* in the
specification's verification table and will be flipped one at a time with the
evidence attached.

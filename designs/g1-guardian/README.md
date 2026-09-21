# G1 — radiation-aware node guardian (SiGe BiCMOS test chip)

A mixed-signal test chip intended to protect a compute load from single-event
latch-up and characterize temperature, dose-sensitive leakage and upset events.
Four functions on one 1.35 × 1.35 mm die, planned for QFN24 board measurements:

1. a current-limiting **breaker**: shunt sense amplifier, trip comparator, I²t
   timer and gate drive for an external switch, with a trip profile that lets a
   fast load step through and cuts a latch-up signature;
2. a **temperature sensor** with a one-wire frequency output, built on the
   HBT ΔV<sub>BE</sub> law; operation beyond the model range remains unverified;
3. a **dose canary**: two NMOS transistors of different oxide thickness at equal
   bias, for investigation of off-current versus total ionizing dose; no dose
   calibration has been measured. The experimental enclosed-layout alternative
   is not in the assembled chip;
4. an **upset canary**: scrubbed shift registers, plain and triple-modular-redundant, whose upset counts are reported.

A SiGe bandgap supplies the reference, and a three-wire serial interface exposes
telemetry and trip settings. A bare HBT and the canary transistors are also
brought out to pins for direct device characterisation.

Target process is the IHP SG13G2 open PDK (0.13 µm SiGe BiCMOS). The die uses
the PDK's `sg13g2_io` cells as its pad ring, six per side, and is wire-bonded
into a QFN24 package after bonding-service acceptance.

The implementation uses standard SG13G2 devices and requires no optional TSV,
localized backside etching, MEMRES/RRAM, photonics or copper-backend module.
The 3.3 V thick-oxide MOSFETs, SiGe HBTs, MIM capacitors and poly resistors are
part of the base open PDK. The legacy `D_ELT` pin connects to a standard HV
NMOS in the assembled netlist, not an enclosed-layout transistor.

Current snapshot: [assembled GDS](blocks/g1_padring/layout/g1_chip_top.gds),
[netlist](blocks/g1_padring/netlist/g1_chip_top.cdl), and
[design review PDF](review/G1_DESIGN_REVIEW.pdf). The PDF is a dated review
snapshot; subsequent status updates are recorded below and in block evidence.

**State: the 1.35 × 1.35 mm chip is assembled. The assembly passes KLayout
hard-rule DRC, precheck, density, supply-connectivity/isolation checks, timing,
and core-only LVS (52 circuit pairs matched). Full-chip LVS through the IO ring
and KLayout antenna remain failed; see the evidence and scope in
[`blocks/g1_padring/INTEGRATION.md`](blocks/g1_padring/INTEGRATION.md).
Original breaker runs used a faulty clock bridge and are not timing acceptance
evidence. Corrected schematic cases completed; integrated block-PEX OP and
1 µs/4 µs startup diagnostics passed. A 10 µs request timed out at a last
reported 7.551 µs, before configuration and fault injection. Integrated PEX
fault-event and power-up verification remain not run to completion. See
[restart evidence](blocks/g1_top/sim/DIAGNOSTICS_20260921.md).
125 °C historical attempts failed numerically; the simulation matrix is incomplete.
Nothing has been fabricated, taped out or measured. This is not a signed-off
submission.**

## What the chip is meant to do

| Block | Function | Devices | Domain | Est. area |
| --- | --- | --- | --- | ---: |
| `G1_SENSE` | Kelvin shunt sense amplifier, low-side, gain 20; difference amplifier around three PMOS-input OTAs (`blocks/g1_sense/layout/`: 252 × 189 µm, DRC and LVS clean, PEX done; post-layout gain 19.99, bandwidth 4.2 MHz) | thick-oxide PMOS input, thick-oxide MOS, `rppd`, `cmim` | 3.3 V | 0.048 mm² |
| `G1_TRIP` | Two clocked comparators with V<sub>REF</sub>-referenced 8-bit resistor-string DACs, soft and hard thresholds (`blocks/g1_trip/layout/`: 229 × 207 µm, DRC and LVS clean including a one-to-one compare of all 530 string resistors, PEX done; post-layout delay ≤ 1.8 ns at 1 mV overdrive worst corner, DAC INL ≤ 0.002 LSB) | 1.2 V StrongARM comparators, `rppd` strings, thick-oxide switch trees | 1.2 V / 3.3 V | 0.047 mm² |
| `G1_GATE` | Latch and driver core for the external low-side N-FET, latched or retriggering, fast path from the hard comparator (`blocks/g1_gate/layout/`: 131 × 51 µm, DRC and LVS clean, PEX done) plus the 30 mA output pad in the ring | thick-oxide MOS, `sg13g2_IOPadOut30mA` | 3.3 V | 0.007 mm² + pad |
| `G1_BGR` | Bandgap reference and PTAT current (`blocks/g1_bgr/layout/`: 84 × 124 µm, DRC, antenna and LVS clean, PEX capacitances extracted; post-layout V<sub>REF</sub> within 0.15 % of schematic) | `npn13G2`, thick-oxide MOS, `rppd`, `rhigh` | 3.3 V | 0.010 mm² |
| `G1_T2F` | Temperature-to-frequency sensor: PTAT current from the bandgap core into a `cmim` relaxation oscillator with a V<sub>REF</sub> threshold, PTAT and reference modes (`blocks/g1_t2f/layout/`: revision 2 with collector cascodes, 92 × 103 µm, DRC, antenna and LVS clean, PEX done; every HBT within the 1.6 V V<sub>CE</sub> limit; simulated two-point residual −0.85 to +0.17 °C over −40 to 150 °C, supply sensitivity −2.5 °C/V) | `npn13G2`, thick-oxide MOS, `rppd`, `cmim`, LV CMOS output | 3.3 V core, 1.2 V output | 0.009 mm² |
| `G1_DOSE` | Thin-oxide / thick-oxide NMOS canary pair with shared gate, drains pinned out; drawn enclosed-layout NMOS as an approval-gated alternative | `sg13_lv_nmos`, `sg13_hv_nmos`, drawn ELT | 1.2 / 3.3 V | < 0.001 mm² |
| `G1_SEU` | Plain and triple-modular-redundant shift registers, scrubbed and counted; depth parameterised, 256 + 3 × 128 bits in the assembled digital macro | LV CMOS standard cells | 1.2 V | inside the digital macro |
| `G1_CTRL` | Register file, serial interface, trip timers, scrub state machine; hardened together with `G1_SEU` as one digital macro (`blocks/g1_ctrl/layout/`, run 7: DRC, LVS, antenna, XOR and timing clean; TMR copies placed ≥ 27 µm apart; gate-level simulation passes) | LV CMOS standard cells | 1.2 V | 0.13 mm² (macro, 360 × 360 µm, 46 pins) |
| `G1_OSC` | Relaxation oscillator clocking the timers and scrubber, 4-bit trim (`blocks/g1_osc/layout/`: 166 × 138 µm, DRC and LVS clean, PEX done; 9 MHz at mid code post-layout, nominal trim brackets 10 MHz; full PVT coverage not run) | MOS, `rppd`, `cmim` | 1.2 V | 0.023 mm² |
| `G1_DUT` | One bare `npn13G2` with E, B, C on pins (`blocks/g1_dut/`: DRC and LVS clean) | `npn13G2` | — | < 0.001 mm² |
| `G1_PADRING` | 24 `sg13g2_io` cells, 24 bondpads, 4 corners, fillers, sealring | `sg13g2_io`, PDK PCells | 3.3 V / 1.2 V | about 1.4 mm² |

The core window inside the ring is about 620 × 620 µm (0.38 mm²) on the 1.35 × 1.35 mm die; the digital macro (360 × 360 µm) and the sense amplifier (252 × 189 µm) are the largest tenants; see
[`padframe/`](padframe/README.md) for the geometry. Full specification, pin map
and parameter classification: [`specification/G1_TOP_LEVEL_SPECIFICATION.md`](specification/G1_TOP_LEVEL_SPECIFICATION.md).
Schedule, freeze lines, decisions and pin fallbacks: [`PLAN.md`](PLAN.md).

## Built against

| Thing | Version | How it will be established |
| --- | --- | --- |
| PDK | IHP SG13G2, commit `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` | `COMMIT` file at the PDK install root, recorded in the first simulation logs under `blocks/g1_dut/sim/logs/` |
| ngspice | 46 | simulator banner in `blocks/g1_dut/sim/logs/` |
| KLayout | 0.30.9 | DRC/LVS run logs under `blocks/*/reports/` |
| xschem | 3.4.8RC | `v {xschem version=...}` header of each `.sch` |
| LibreLane | 3.1.0.dev2 | `blocks/g1_padring/reports/` flow log header |

## What was actually measured

Physical measurement: **not run**. Block simulation and post-layout results
are recorded in the block READMEs. The chip-level breaker simulation uses real
RTL, transistor-level analog blocks, an ideal clock and fitted output-pad
drivers; its model substitutions and incomplete cases are explicit in
[`blocks/g1_top/README.md`](blocks/g1_top/README.md).

The original chip-level simulation clock bridge can double-count RTL edges.
A focused regression reproduces the issue and verifies the corrected receiver
([bridge evidence](blocks/g1_top/sim/bridge_probe/README.md)). Historical trip
latencies are retained for diagnosis but are not accepted sign-off evidence.

## Assumptions carried into the design

| Assumption | Status |
| --- | --- |
| Drawn, non-PCell transistor geometry (the enclosed-layout NMOS in `G1_DOSE`) is acceptable on the target shuttle provided it is DRC-clean and its extraction is documented | **not applicable to assembled standard-PCell pair; experimental ELT fails `Gat.f`, acceptance not established** |
| Wire-bonding of 70 × 70 µm external bondpads at 112 µm pitch into QFN24, with the die paddle bonded out as a substrate connection | **assumed; bonding-service confirmation pending** |
| Package survives −196 °C to +175 °C for characterisation soaks | not verified; package and fixture qualification required |
| Low-side shunt sensing with common mode within −0.1 V to +0.3 V of ground | design choice |
| `VDDA` (pin 7) and `IOVDD` come from one 3.3 V board rail | required: the analog pad's ESD diodes reference `IOVDD`; `VDDA` above `IOVDD` by a diode drop would forward-bias them (`PLAN.md` D14) |
| Trip response target under 10 µs from overcurrent to gate low | selected corrected schematic cases completed; integrated PEX fault-event verification not run to completion |
| Board powers `VDD` before or with `IOVDD` | required: with only `IOVDD` present the 30 mA output pad drives `GATE` high (IO-cell property, simulated) |

## What remains unverified

- Full-chip LVS through the IO ring and KLayout antenna: **failed**, with
  reference-cell evidence in the pad-ring reports; no waiver is claimed.
- Chip-level 125 °C breaker transients: **failed** (solver timestep collapse).
- Remaining chip-level simulation cases, process corners, mismatch and supply
  extremes: **not run to completion** or **not run**, as listed in G1_TOP.
- Full-chip PEX, package/bond-wire parasitics and physical measurements:
  **not run**.
- Bonding-service acceptance and final submission review: **not run**.

The core-only LVS excludes IO cells, bondpads and ring rails. Geometric
connectivity checks do not replace transistor-level verification of those cells.

# G1 bring-up board checklist (chip of record r3, register map 1.2)

What the bring-up PCB and bench must provide, derived from
[`G1_TOP_LEVEL_SPECIFICATION.md`](../../specification/G1_TOP_LEVEL_SPECIFICATION.md) §3, §4, §6 (P1–P9),
the bench plan [`../README.md`](../README.md) (B1–B8), the bond plan
[`../../padframe/BONDPLAN_20260925.md`](../../padframe/BONDPLAN_20260925.md), the register map
[`G1_REGISTER_MAP.md`](../../specification/G1_REGISTER_MAP.md) and the block records cited inline.

**Status: no board exists and nothing here has been measured.** Every number is either from the
specification or **simulated** (it says which). Values marked *proposed* are board-design choices
made for this checklist. No run supports them, and each one must be recorded in the run sheet.
Tick a box only against a record: schematic review, continuity log or scope capture.

## 1. QFN24 lead map (board schematics use the lead number)

QFN24, 4 × 4 mm, 0.5 mm pitch, exposed paddle = `VSS`. Pin 1 is at the top left of the top view,
and leads are numbered counter-clockwise. Die pads 1–12 land on leads 1–12. Die pads 13–18 land on
leads **18–13** and die pads 19–24 on leads **24–19**, reversed within each side (bond plan,
0 crossings). The die-pad numbers in the GDS and the block documents are unchanged.

| QFN24 lead | Die pad | Net | IO cell | Board connection |
| ---: | ---: | --- | --- | --- |
| 1 | 1 | `VDD` | `sg13g2_IOPadVdd` | 1.2 V core rail (1.08–1.32 V), local decoupling |
| 2 | 2 | `VSS` | `sg13g2_IOPadVss` | ground plane, tied to paddle |
| 3 | 3 | `IOVDD` | `sg13g2_IOPadIOVdd` | 3.3 V rail via its own current-sense link |
| 4 | 4 | `IOVSS` | `sg13g2_IOPadIOVss` | ground plane, tied to paddle |
| 5 | 5 | `VSS` | `sg13g2_IOPadVss` | ground plane, tied to paddle |
| 6 | 6 | `IOVSS` | `sg13g2_IOPadIOVss` | ground plane, tied to paddle |
| 7 | 7 | `VDDA` | `sg13g2_IOPadAnalog` (bare terminal) | **same 3.3 V rail as `IOVDD`**, through its own sense link (P3/B5) |
| 8 | 8 | `SENSE_P` | `sg13g2_IOPadAnalog` | shunt Kelvin +, high side of the low-side shunt |
| 9 | 9 | `SENSE_N` | `sg13g2_IOPadAnalog` | shunt Kelvin −, at the shunt's ground-side sense terminal |
| 10 | 10 | `GATE` | `sg13g2_IOPadOut30mA` | external N-FET gate (via series R) |
| 11 | 11 | `FAULT_N` | `sg13g2_IOPadOut4mA` | host input / LED; push-pull, low while tripped |
| 12 | 12 | `EN` | `sg13g2_IOPadIn` | CMOS/Schmitt buffer from host, 100 kΩ pull-down |
| 13 | 18 | `VREF` | `sg13g2_IOPadAnalog` | bandgap test pin: capacitor option + test point (§5) |
| 14 | 17 | `TEMP_OUT` | `sg13g2_IOPadOut16mA` | frequency counter / host timer input |
| 15 | 16 | `SDO` | `sg13g2_IOPadOut4mA` | host MISO |
| 16 | 15 | `SDI` | `sg13g2_IOPadIn` | host MOSI, 100 kΩ pull-down |
| 17 | 14 | `SCLK` | `sg13g2_IOPadIn` | host SCLK, 100 kΩ pull-down |
| 18 | 13 | `TRIP_SET` | `sg13g2_IOPadAnalog` | **no function on r3** (pad net has no core load); test point only, do not drive |
| 19 | 24 | `HBT_C` | `sg13g2_IOPadAnalog` | HBT coupon collector → SMU (triax/guarded) |
| 20 | 23 | `HBT_B` | `sg13g2_IOPadAnalog` | HBT coupon base → SMU |
| 21 | 22 | `HBT_E` | `sg13g2_IOPadAnalog` | HBT coupon emitter → SMU |
| 22 | 21 | `D_ELT` | `sg13g2_IOPadAnalog` | DOSE pair, HV NMOS drain (legacy name) → SMU |
| 23 | 20 | `D_STD` | `sg13g2_IOPadAnalog` | DOSE pair, LV NMOS drain → SMU |
| 24 | 19 | `G_SHARED` | `sg13g2_IOPadAnalog` | DOSE pair shared gate: **thin oxide, ≤ 1.32 V, ESD-sensitive** |

- [ ] Footprint and schematic symbol checked against this table and
  `padframe/bondmap_20260926_r4.csv` (`qfn24_lead` column). **Not** checked against the superseded
  r3 CSV or against die-pad numbers.
- [ ] Paddle soldered or socket-contacted to the `VSS` plane. Leads 2, 5 (`VSS`) and 4, 6 (`IOVSS`) are
  tied to the paddle ground at the package (B7). On the die `VSS` and `IOVSS` meet only through
  substrate resistance, so the board provides the connection.

## 2. Supplies and sequencing (P1, P2, P3, B1, B2, B5, B7)

- [ ] **`VDD` (1.2 V) comes up before or together with `IOVDD`/`VDDA` (3.3 V).** At shutdown `VDD`
  stays until 3.3 V is down. Implement with sequenced bench supplies, or a supervisor that holds the
  3.3 V rail off until 1.2 V is valid. *Why:* the `sg13g2_io` output pads take their gate drive from
  core-powered level-up cells. With 3.3 V alone `GATE` reached 3.288 V (simulated). IO-first on the r3
  chip netlists gave `GATE` 3.300 V for 4.34 µs with EN low, and the 1 A load conducted (case `gA`,
  simulated).
- [ ] **`VDDA` (lead 7) on the same 3.3 V source as `IOVDD`** (lead 3), with separate current-sense links
  (≤ 0.5 Ω each, decoupled on the chip side) or sensing on the common source. There is no separate
  `VDDA` supply. `VDDA` must never exceed `IOVDD` by a diode drop, because the analog-pad ESD diodes
  reference `IOVDD`.
- [ ] Fast 3.3 V ramp, target < 100 µs (P2).
- [ ] **`VDD` undervoltage supervisor that asserts the load-bus inhibit** (P8/B7). A `VDD` brownout with
  `IOVDD` present reproduces the IO-first unsafe state.
- [ ] **Current-limited bench supplies.** *Proposed* initial limits: 1.2 V at 20 mA and 3.3 V at 20 mA.
  Expected quiescent VDDA is about 1.46 mA and IOVDD 0.1 mA with `TEMP_OUT` toggling (simulated).
  `GATE` edges draw 3.5–6.2 mA peaks from `IOVDD` (simulated), and local decoupling supplies these.
  The `VDD` current of the digital macro was **not simulated**, so record it before tightening the limit.
- [ ] Decoupling at leads 1, 3 and 7 (*proposed*: 100 nF X7R at the lead + 1 µF nearby, placed on the chip
  side of each sense link).
- [ ] Rails, `GATE` and `EN` brought to test points so every power cycle can be captured (B1).

## 3. Load path, inhibit and FET (P2, P7, B2, feasibility envelope)

- [ ] **Independent load-bus inhibit**, not driven by G1. Examples: a second series switch or a relay
  from the bench interlock. It is asserted **before any rail rises**, through calibration and across
  every `EN` edge. Losing control power must leave it asserted (default-off). The host drives it through
  the `inhibit` callback in `g1_host.py`. `EN` is **not** a configuration-preserving inhibit, because
  `EN` low resets all registers.
- [ ] The inhibit is qualified **without the DUT** before any energized test: open/close state,
  cut-off delay, overshoot at the Kelvin pins and delivered energy (bench plan, "Before enabling a
  load").
- [ ] **External `GATE` pull-down** at the FET, *proposed* 10 kΩ (the simulated value). Core-first with
  10 kΩ gave `GATE` ≤ 9 mV with EN low (simulated). It does **not** hold `GATE` low with IO first, where
  the 30 mA driver wins, and a pull-down strong enough to do so is not qualified. It complements the
  inhibit and does not replace it.
- [ ] **Real-FET fixture matching the simulations:** the gate network is 10 Ω series with about 5 nF
  of effective gate load. That is the fixture of every chip-level trip run (`GATE` < 1 V 1.43–1.73 µs
  after the fault, r3 full-chip deck, simulated). TI CSD16340Q3 is the **simulation characterization
  candidate** (`blocks/g1_gate/sim/REAL_FET_20260921.md`, assumed 5 V/12 V R-L loads), **not a
  selected BOM part**. Whatever FET is fitted, record part/lot, its gate charge at V<sub>GS</sub> = 3.3 V
  and R<sub>DS(on)</sub> at V<sub>GS</sub> = 3.0 V (minimum `IOVDD`). A FET that needs more than about
  3 V to enhance is outside the drive.
- [ ] Load for first silicon: current-limited, **non-inductive, nominal 5 V resistive**, 1 A nominal.
  The fault step is 1.8 A (45 mV at 25 mΩ). The ceiling is 2 A/50 mV *including transient overshoot at
  the sense pins* ([feasibility envelope](../../specification/FEASIBILITY_DEMO_ENVELOPE_20260922.md)).
  Inductive or autonomous loads: **not run**, out of scope.
- [ ] Clamp and return path for the load drawn explicitly on the schematic.

## 4. Shunt and sense pins (P9, B8, spec §4)

- [ ] **Four-wire (Kelvin) shunt, 25 mΩ nominal**: 1 A → 25 mV nominal, 50 mV full scale (2 A).
  *Proposed*: ≥ 0.5 W (1.8 A² × 25 mΩ = 81 mW during the fault step), low TC. Measure and record R and
  TC. The shunt is **low side**, and the sense common mode is −0.1…+0.3 V (spec §4).
- [ ] `SENSE_P`/`SENSE_N` routed as a tightly coupled pair from the shunt's **sense** terminals, not
  from the current path or the ground plane. No RC filter on the sense pair, because the simulations
  have none and a filter adds trip delay (not simulated).
- [ ] **Absolute maximum while powered: ≤ 100 mV differential at the sense pins.** Above about 115 mV
  `ISENSE` saturates and the comparator input exceeds the 1.2 V thin-oxide rating (simulated). The
  fault source compliance and overshoot must keep the pins ≤ 50 mV for the demo (§3).
- [ ] **Never leave `SENSE_P` open while powered.** An open `SENSE_P` drives the comparator input to
  1.644 V continuously and trips permanently (simulated). No jumper in the `SENSE_P` lead.
- [ ] **Open-`SENSE_N` blindness check** in the procedure, because an open `SENSE_N` leaves `ISENSE` at
  0.05–0.29 V and the breaker is **blind with no indication** (simulated, `ELECTRICAL_SYSTEM.md` M3).
  Before arming and after every EN cycle, run `G1.kelvin_check()` with load current flowing
  (`STATUS2.CMP_SOFT` = 1 at `DAC_SOFT` 5). *Optional (proposed):* a removable 0 Ω link in `SENSE_N`
  for a deliberate, supervised open-lead characterization. That behaviour is unqualified.
- [ ] Calibration input: a traceable low-noise source (25.00 mV nominal) connectable at the Kelvin
  pins with the load bus inhibited, plus a 6½-digit DMM across `SENSE_P`–`SENSE_N`.

## 5. `VREF` pin (lead 13) capacitor (P4, P5, B3, B4)

BGR586 output resistance is 19.3–25.8 kΩ (22.3 kΩ tt/27 °C, simulated). The pin sits behind the
613 Ω route estimate.

| Option | Settling to 1 % from ramp start (simulated) | Required `EN` delay after rails | Noise / probing |
| --- | --- | --- | --- |
| 0 nF (pin open) | about 7–8 µs, with a 1.3–1.7 % overshoot during the ramp (stock pad did not converge at tt/27 °C; pad-less and ff/−40 °C values) | ≥ 50 µs (*proposed*, library default) | probe capacitance and noise act directly on the bandgap output; every probe reading loads it |
| **10 nF (1 Ω ESR simulated)** | 1.26 ms tt/27 °C, 1.20 ms ff/−40 °C, 1.32 ms ss/125 °C (pad-less); 0.1 %: 1.67–1.93 ms | **≥ 2 ms** (P4) | τ ≈ 0.2–0.27 ms low-pass. The on-chip `VREF` node carries 32–46 mV p-p clock spikes (extracted interconnect, simulated), which the pad with 10 nF does not show |
| 100 nF | 11.8–13.2 ms (0.1 %: 16.4–19.3 ms) | ≥ 20 ms (*proposed*: 0.2 ms/nF) | lowest noise, longest start |

- [ ] Footprint for the capacitor, populated with **10 nF** for first silicon (*proposed*). The value
  and ESR go in the run sheet. The `EN` delay scales with it (`G1.enable(vref_cap_nF=...)`).
- [ ] Step recovery is single-pole with no ringing at 0/10/100 nF (simulated, three corners), so the
  choice is a settling-versus-noise trade, not a stability one.
- [ ] Measure `VREF` with a ≥ 10 GΩ input (DMM high-Z mode) or a characterized buffer. A 10 MΩ meter
  lowers it by about 2.3 mV (computed from the simulated R<sub>out</sub>, not a pad-inclusive
  simulation).

## 6. Digital control pins (P6, P8, B3, B6; map §1, §3)

- [ ] **`EN` driven low at power-up** from a low-impedance **CMOS or Schmitt buffer** with a fast,
  clean edge. Never use an RC timer, because the pad has no hysteresis and chatters through its
  threshold. Never tie `EN` high. `EN` is the only reset: there is no POR (`por_n` tied high) and no pad
  pull.
- [ ] **100 kΩ pull-downs at the package on `EN`, `SCLK`, `SDI`** (P8). The input pads have no pull and
  no hysteresis, and noise on floating `SCLK`/`SDI` can complete write frames (for example `MODE`).
- [ ] Deliberate resets: **`EN` low ≥ 2 µs**. On r3 the core resets after 8 consecutive low samples
  (about 1 µs). An `EN` low of 8 to ~11 cycles can leave a trip latched, and a shorter glitch still
  turns `GATE` off and clears the G1_GATE latch through the analog `en_core` path.
- [ ] `EN` routed away from `GATE` and `FAULT_N`.
- [ ] Host SPI in **mode 0**, SCLK idle low, no chip select (G1 has none; leave the adapter CS
  unconnected). *Proposed* 1 MHz SCLK: f<sub>SCLK</sub> ≤ f<sub>OSC</sub> (≥ 7.6 MHz simulated
  minimum), and every SCLK-low phase inside a frame stays < 64 osc cycles (< 5.3 µs). Check with a scope
  that the adapter sends 16/24 contiguous clocks per frame.
- [ ] `SDO` and `FAULT_N` are 4 mA push-pull 3.3 V outputs. Do not wire-OR them, and use 3.3 V logic
  levels on the host side.
- [ ] `TEMP_OUT` (16 mA push-pull) to an SMA/test point for a reciprocal counter. Keep the load
  ≤ 20 pF, as in the simulation (IOVDD +96–128 µA with it toggling). *Proposed:* 33 Ω series
  resistor at the pin.
- [ ] `TRIP_SET` (lead 18): no connection to anything that drives it. It has no function on the chip of
  record.

## 7. Analog device pins and ESD (B8, spec §3)

- [ ] **`G_SHARED` (lead 24, die pad 19) ≤ 1.32 V**, except in a declared stress experiment. It is a
  thin-oxide gate with no secondary protection, so treat it as ESD-sensitive. *Proposed:* a shorting
  jumper from `G_SHARED`, `D_STD`, `D_ELT` and `HBT_*` to ground, fitted during handling and insertion
  and removed only with the SMUs connected.
- [ ] Every device pin stays **≥ −0.3 V while powered**. The analog pads carry ESD diodes to
  `IOVDD`/`IOVSS`. Biasing a device pin above an unpowered `IOVDD` back-feeds the rail through the
  diode, so keep 3.3 V up (or the pins at 0 V) while SMUs are connected.
- [ ] HBT coupon (leads 19–21): SMUs with explicit compliance and **V<sub>CE</sub> ≤ 1.6 V**.
- [ ] DOSE pair (leads 22–24): source and body are on `VSS`. *Proposed* drain limit ≤ 1.2 V for both
  drains in the common sweep (LV device rating), and a declared, separate limit for the HV drain.
- [ ] Guarded/triax routing for leads 19–24 where low currents are measured. The pad ESD-diode leakage
  sets the current floor, and the plan keeps device currents in the nA–µA range.
- [ ] Standard ESD handling (wrist strap, dissipative mat) for every insertion.

## 8. Socket, temperature and records

- [ ] QFN24 4 × 4 mm 0.5 mm socket (open-top/clamshell) **that contacts the exposed paddle**, since the
  paddle is `VSS` and the substrate, and is rated for the intended temperature range. A soldered
  adapter is the alternative. Record the socket part and its rating.
- [ ] The characterisation target is −40…125 °C. The package, socket and board are **not qualified**.
  77 K and 150/175 °C are separate experiments, each with its own fixture qualification (bench plan).
- [ ] A calibrated reference thermometer next to the package for `TEMP_OUT` work, plus logged case and
  shunt temperatures.
- [ ] Separate current monitors for `VDD`, `VDDA`, `IOVDD`, and the load current.
- [ ] Board revision, BOM (shunt R/TC, FET lot, gate R, pull-down values, `VREF` C/ESR) and the
  continuity record are pinned in each run sheet (bench plan, "Fixture and records").

## Status

| Item | Status |
| --- | --- |
| Board schematic / layout | not run (no board exists) |
| Lead map vs bond map CSV | not run for a board. The CSV passed its geometric check against the r3 GDS (`blocks/g1_padring/reports/signoff-1414r3-20260926/bondmap/verify_bondmap_r4.json`) |
| Inhibit qualification without DUT | not run |
| Any measurement | not run |

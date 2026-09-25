# G1 red-team review: electrical system, supply domains, pads, reset and bias sharing (2026-09-25)

Reviewer role: independent senior analog/mixed-signal red team. Scope: the chip of record
`g1_chip_top_1414.gds` (`629d303a…`). The connectivity reference is the canonical netlist
`blocks/g1_padring/netlist/g1_chip_top_1414.cdl` (SHA-256 prefix `af5a4dbd0b17013b`, checked). Line numbers
below refer to that file. Nothing here has been measured. Every number is simulated or derived, and the
text says which.

Inputs read: `AGENTS.md`, `README.md`, `specification/G1_TOP_LEVEL_SPECIFICATION.md`,
`specification/G1_REGISTER_MAP.md`, `measurement/README.md`, block READMEs, `blocks/g1_top/README.md`,
`blocks/g1_top/sim/campaigns/RESULTS_20260925.md`, `blocks/g1_trip/sim/postlayout/README.md`,
`blocks/g1_ctrl/rtl/g1_digital_top.v`, `g1_trip_timer.v`, and the CDL.

## Summary

| Rank | Count | Items |
| --- | ---: | --- |
| Blocker | 0 | No finding needs a mask change before the chip can be a useful test vehicle |
| Must-fix | 5 | M1–M5: power-up and enable contract, loss of protection when the clock stops, blind breaker when the Kelvin lead opens, floating serial and enable inputs, unfiltered `EN` |
| Should-fix | 8 | S1–S8 |
| Note | 7 | N1–N7 |

"Must-fix" means one of two things. Either the board, firmware or measurement contract has to change
before any energized load test, or a specification statement is wrong. None of the must-fix items is
covered by the existing simulations, because those use an ideal `EN` copy, an ideal clock, an ideal ground
and connected Kelvin leads.

## Checks run for this review

| Check | Status | Evidence |
| --- | --- | --- |
| CDL connectivity walk: every top-level instance, every net that crosses a domain, every pad terminal, single-ended nets | passed (done) | §A |
| Core-first power-up with the real PDK `sg13g2_IOPadIn` (EN), `g1_gate` schematic and `sg13g2_IOPadOut30mA`, VDD up, IOVDD = VDDA ramped, EN pin at 0 V | 5 runs completed, 1 **failed** numerically (stock pad, ff/−40 °C, `darea` stall at 8.07 µs) | M1, §B.1 |
| G1_SENSE (c1414 `sch` view) DC with an open SENSE_N or SENSE_P lead, 0–250 mV shunt | passed (ran) | M3, S1, §B.2 |
| TRIP NF4 extraction, strobe-train bench, hard path with soft code 255 (soft comparator deciding low) | 2 runs completed | S3, §B.3 |
| T2F effect on VREF and thresholds, from the existing chip-level waveforms (`q` with and without `--t2f tl`, tt/27 °C) | post-processed, no new simulation | N1 |
| VDD/VSS bounce at the comparator strobe, full-chip PEX, IR drop | **not run** | S2 |
| ESD (HBM/CDM) of pads and domain crossings | **not run** | S5, N6 |
| Latch-up assessment beyond the DRC `LU.*` rules | **not run** | N5 |
| Hard threshold versus VDD, temperature and SEU pattern at chip level | **not run** | S2, S3 |

Tools: ngspice-46 in the pinned container (`flow/run.sh`, `G1_CPUSET=38-39`, image identity and PDK commit
`84374023ee8b4b126bebbba67fcbada0a9c0ff0b` checked by the runner). The decks were built in a scratch
directory and are not committed. Their essential lines are in §B.

---

## Must-fix

### M1. Core-first power-up: the EN input reads "enabled" until IOVDD reaches about 1.1 V, and the GATE latch comes up in a random state

The facts from the CDL:

- `EN` enters through `Xpad12_en … sg13g2_IOPadIn` (CDL 17911). Its `LevelDown` (CDL 18292) takes the pad
  through an IOVDD-powered inverter pair (`net7`, `net4`). It then drives `net2` with two HV NMOS: `MN2` to
  VSS and `MN0` from VDD. With IOVDD = 0 both gates are at 0 V, so `net2` floats. The core output `en_i` is
  an LV inverter of `net2` on VDD.
- A subthreshold estimate puts `net2` at about 20 mV (`MN2` at V<sub>GS</sub> = 0 against `MN0` at
  V<sub>GS</sub> = −V<sub>net2</sub>). **`en_i` then sits at VDD, which means "enabled".** ngspice's DC
  operating point puts `net2` at 0.64 V instead, because gmin sets it there. That is a solver artefact.
- `por_n` is tied high by `Xi_core_u_digital_1 net VDD VSS / sg13g2_tiehi` (CDL 17889). The async reset is
  `arst_n = por_n & en` (`X_3266_`, CDL 8696). In the VDD-only window of the mandated P1 order, the digital
  core is therefore **not in reset**. All its outputs (`osc_en`, `trip_d`, `clr_d`, `fast_en`, DAC codes,
  `bgr_r4`, `t2f_*`) are arbitrary.
- `g1_gate` (CDL 2667) takes `en_i` through `g1_lvlup`. `gate_h = NOR(en_hn, q)`. The NOR latch `q`/`qb` has
  no defined power-up state.

Simulated with the real input pad, the gate core and the output pad. VDD = 1.2 V throughout, VDDA = IOVDD
ramped 0 → 3.3 V, EN pin held at 0 V, digital inputs of `g1_gate` at 0, 10 kΩ + 5 nF on `GATE`:

| Run | `en_i` goes low at IOVDD = | latch `q` at IOVDD 1.05 V | `gate_core` > 0.6 V with IOVDD > 0.8 V | `GATE` max |
| --- | --- | --- | --- | --- |
| tt/27 °C, 20 µs ramp, `net2` from OP (0.64 V) | at start | 0 | no | 0.0000 V |
| tt/27 °C, 20 µs, `net2` = 0 V | 1.16 V | 1 (tripped) | no | 0.0083 V |
| tt/27 °C, 200 µs, `net2` = 0 V | 1.09 V | 1 | no | 0.0032 V |
| ss/125 °C, 20 µs, `net2` = 0 V, pads without `dantenna` | 1.11 V | 1 | no | 0.0001 V |
| ff/−40 °C, 20 µs, `net2` = 0 V, pads without `dantenna` | 1.17 V | 1 | no | 0.018 V |
| **ff/−40 °C, 20 µs, `net2` = 0 V, stock pads** | not reached | **0** | **yes: 1.20 V from IOVDD ≈ 1.1 V** | **0.172 V and rising when the solver stalled** (`darea`, `xpe.xi0.xi0.xd1`, 8.07 µs); **failed** numerically |

Reading. In the physically expected state (`net2` low), `EN` is seen as high until IOVDD ≈ 1.09–1.17 V. The
safety of the GATE pin then depends on how the `g1_gate` NOR latch happens to resolve. Five runs resolved to
`q` = 1 (tripped), which is protective by accident. One run resolved to `q` = 0 and commanded the gate on
(`gate_core` = 1.2 V). The only change between that run and a protective one was the removal of pad-diode
model elements, which shows how uncontrolled the resolution is. In every run `gate_core` also glitches to
0.70–0.84 V below IOVDD ≈ 0.75 V (`g1_lvldn` with VDDA absent). At that point the pad cannot yet drive.

The peak `GATE` voltage is bounded by IOVDD at the moment `en_i` resolves, about 1.1–1.2 V. That window
scales with the ramp time: a 10 ms regulator soft-start holds it for hundreds of µs. The value sits in the
threshold range of logic-level FETs. The documented core-first pass (`g1_top` gB, `GATE` ≤ 0.073 V) used an
ideal `EN` copy (`blocks/g1_top/README.md`: "EN via the d_source"), so this mechanism was outside it.

Required:
1. Make the P2 independent load-bus inhibit mandatory for **every** power-up order, not only IO-first. Today
   spec §6 P2 and measurement B2 present it as a pull-down "or" an inhibit.
2. Qualify the spec §6 P1 / B1 evidence as "ideal EN".
3. Board: ramp IOVDD/VDDA quickly (target < 100 µs).
4. Next revision: a 3.3 V-domain POR that forces `en_h` low, or a pad `LevelDown` whose default is safe.

### M2. A stopped clock removes all protection, FAST_EN included; spec §6 says otherwise

- `cmp_clk` is `cmp_clk_q`, a flop of the digital core (`g1_digital_top.v` lines 63–68). The hard comparator
  strobes on its inverse (`XCLKI`, CDL 2887). The fast path `fast = hard_cmp & fast_en` (`g1_gate`, CDL 2667)
  therefore depends on the digital clock. When `osc_clk` stops, both comparators freeze in their last
  decision and neither path can trip. `GATE` stays on while `EN` is high.
- Spec §6 reads: "The <10 µs target cannot apply … to a stopped clock with FAST_EN disabled". That implies
  FAST_EN covers a stopped clock. **It does not.**
- A stopped clock needs only one flop: `OSC_CTRL.OSC_EN` is `X_5608_` (`dfrbpq`, CDL 11038) → `X_2650_` inverter
  (CDL 8080) → `osc_en`. It can be cleared by a single serial write (see M4), and it is not TMR, so one
  upset can clear it too. Recovery needs an `EN` cycle.

Required:
- Correct spec §6 and register map `OSC_CTRL`: a stopped clock disables both paths.
- Firmware: poll `OSC_CNT` as a clock watchdog, with the load-bus inhibit as the action.
- Measurement plan: an explicit stopped-clock test with the inhibit armed.
- Record the configuration SEU hazard in the radiation test plan.

### M3. An open SENSE_N lead makes the breaker blind; an open SENSE_P lead trips it permanently

Simulated (G1_SENSE c1414 `sch` view, BGR replaced by 1.04546 V and 4.13 µA, tt/27 °C; §B.2), `ISENSE`
against shunt voltage:

| Shunt voltage | both leads | SENSE_N open (1 GΩ) | SENSE_P open (1 GΩ) |
| --- | --- | --- | --- |
| 0 | 1.008 V | 0.048 V | 3.288 V |
| 25 mV | 1.507 V | 0.072 V | 3.288 V |
| 50 mV | 2.007 V | 0.096 V | 3.288 V |
| 100 mV | 3.006 V | 0.143 V | 3.288 V |
| 250 mV | 3.288 V | 0.286 V | 3.288 V |

With SENSE_N open, `icmp` = 0.024–0.143 V against a lowest DAC threshold (code 0) of 0.503 V. The breaker
does not trip even at 10× nominal, and nothing reports it. The Kelvin pads are `padbare` (CDL 17907–17908),
with no on-chip bias that would pull a lost lead to a safe state.

Required:
- Add a Kelvin-integrity check to the measurement procedure and firmware: with a known load current
  flowing, set `DAC_SOFT` to a low code and require `STATUS2.CMP_SOFT` = 1. An open SENSE_N gives 0.
- Check again after every `EN` cycle.
- State in spec §6 that open-lead behaviour is asymmetric: SENSE_P open fails safe, SENSE_N open fails
  unsafe.

### M4. SCLK, SDI and EN float without external pulls; noise on SCLK/SDI can execute register writes

- `sg13g2_IOPadIn` (CDL 18224, 18292) has no pull resistor and no hysteresis (plain inverter `LevelDown`).
- The serial interface has no chip select and frames by clock count (register map §1.2).
- On a floating `SCLK`/`SDI`, noise edges can complete 16-clock write frames. Examples:
  - `OSC_CTRL` with bit 4 = 0 stops the clock, which is M2.
  - `MODE` with bits 0–1 = 0 disables both paths.
  - `DAC_HARD` = 0xFF sets the highest threshold.
- A floating `EN` gives a random enable.
- The register map §3 promises: "With no host at all the chip runs as a breaker on the reset values". That
  is not safe without external pulls. Measurement B3 says only "Do not tie EN high".

Required:
- Board: pull-downs on `EN`, `SCLK` and `SDI` (for example 100 kΩ), placed at the package.
- Spec and register map: make the pulls a board requirement.
- Firmware: read back the configuration periodically, including `OSC_CTRL` and `MODE`.

### M5. EN is an unfiltered asynchronous kill-and-clear; a short low glitch re-energises a latched fault with 1 ms of masking

- `en_i` goes straight into `g1_gate` (`XN2 en_hn clr_h rst_n`, level-sensitive reset of the latch) and into
  the async reset of the digital core (CDL 8696).
- A low glitch longer than the gate delays, a few ns, has two effects. It clears a latched trip. It also
  resets every register: `FAST_EN` → 0, `INRUSH` → 1 ms, DAC codes → defaults.
- When `EN` returns high, `GATE` turns on at once and both trip paths are masked for 1 ms.
- The input has no hysteresis. Measurement B3 suggests driving `EN` "from a timer": a slow RC edge chatters
  through the threshold.
- `EN` (pin 12) is adjacent to `FAULT_N` (pin 11), which switches at every trip, and two pins from `GATE`
  (pin 10).

Required:
- Drive `EN` from a low-impedance CMOS or Schmitt buffer with fast edges, never from a bare RC.
- Keep `EN` away from `FAULT_N`/`GATE` routing.
- Add a firmware check that detects an unexpected reset: `TRIP_CNT` or a written signature register back
  at its default.

---

## Should-fix

### S1. The LV comparator gate at `icmp` sees up to 1.64 V

`ISENSE` saturates at 3.288 V for shunt voltages above about 115 mV. `icmp` = `ISENSE`/2 is then 1.644 V
(§B.2). It is already 1.503 V at the `e20` fixture (100 mV). That voltage sits on the thin-oxide input
devices of `g1_cmp` (`MM1`, `MMD1/2`, CDL 3964) and `g1_cmp_regenpair4` (CDL 4004) at VDD = 1.2 V, above the
1.2 V (1.32 V max) LV rating. In a real fault it lasts only until the trip. With SENSE_P open (M3) it is
**continuous** while powered, even with `EN` low. No simulation checked SOA.

Action:
- Record the limit in the spec (shunt range, open-lead case).
- Measurement plan: do not leave SENSE_P open while powered.
- Next revision: clamp or rescale the divider.

### S2. Comparator decisions coincide with the switching edge of every flop; supply bounce was never simulated

- `cmp_clk_q` toggles on the same `osc_clk` rising edge as all 1200 flops (CDL count of
  `dfrbp`/`dfrbpq`/`sdfrbp` cells in `g1_digital`).
- The default SEU pattern is the checkerboard (`SEU_CTRL` 0x01), which toggles every one of the 640 SEU bits
  on every cycle.
- VDD enters through one pad (pin 1, CDL 17900), decoupled by about 5 500 `decap_8` and 390 `decap_4` cells.
- The `g1_top` decks draw 3.5–5.6 µA from VDD (RTL co-simulation, ideal supplies). The StrongARM
  precharge-to-evaluation kick, already −40…−56 LSB on the hard path, scales with VDD, and VDD droops at
  exactly the decision instant.
- The hard-threshold offset against VDD, and the offset against SEU pattern or `SCRUB_EN`, are **not run**.
  The supply matrix only used the 1.8× fault, well above threshold.

Action:
- Bench: bracket both thresholds with the SEU pattern set to checkerboard and to static (`PATTERN` = 1), and
  at VDD 1.08/1.32 V.
- Treat full-chip PEX with a power grid as required before claiming any threshold accuracy.

### S3. The hard-path early trip does not depend on the soft comparator's decision; calibrate in the operating configuration

To test whether the soft comparator's reset kick depends on its own decision, soft code 255 was used. With
it the soft comparator decides low (0/3 strobes high). Hard code 254 still tripped on 3/3 strobes at 4 and
at 16 LSB underdrive (NF4 extraction, tt/1.2 V/27 °C; §B.3). Moving the soft DAC therefore does not remove
the offset.

The spec §6 contract (bracket the effective threshold, ≥ 56 codes of search) stands. Calibrate with the
soft code, `SENSE_OFS`, T2F state and SEU pattern that will be used in operation, and repeat at each
declared VDD and temperature.

### S4. TRIP_SET and `trip_set_sel` are unconnected, yet documented as functional

- `Xpad13_trip_set … i_core_trip_set` (CDL 17912) has no consumer.
- `i_core_trip_set_sel` exists only on the digital port (CDL 17888).
- The trip README and the `g1_top` README say "not built".
- Spec §3 (pin 13 "external hard-threshold override, optional"), spec §2 (`G1_TRIP` interfaces) and register
  map §2 and `MODE` bit 3 still describe the function.

Correct the documents: `TRIP_SET` is a no-connect analog pad, and `MODE.TRIP_SET_SEL` has no effect.

### S5. Device pins: thin gate on a bare pad, substrate injection, over-voltage

- `G_SHARED` (CDL 17918, `padbare`, `padres` = `_nc4`) connects directly to the gate of the LV NMOS `MLV`
  (CDL 4036). The 587 Ω secondary protection is not in the path. The primary diodes clamp at IOVDD + V<sub>D</sub>,
  about 4 V, far above the rating of the LV oxide.
- The dose README already names 3.3 V exposure as an over-stress. The ESD side is **not assessed**:
  the thin oxide sits behind primary protection only.
- `HBT_C`, `D_STD` and `D_ELT` driven below VSS forward-bias collector–substrate or drain–substrate
  junctions. That injects minority carriers into the substrate shared with the BGR and SENSE.

Action:
- Measurement plan: ESD handling class for pin 19, `G_SHARED` ≤ 1.32 V except in a declared stress
  experiment, and all device pins ≥ −0.3 V with the chip powered.

### S6. A VDD brownout during operation reproduces the IO-first unsafe state

P1 constrains order and shutdown only. With IOVDD/VDDA present and VDD sagging, the output pads lose their
core-driven gate signals, the same mechanism as IO-first (3.28–3.30 V on `GATE`, RESULTS §5). Board: a VDD
supervisor must assert the load-bus inhibit on VDD undervoltage. Add this as P6/B6.

### S7. Board-level coupling into VREF and VDDA

- `TEMP_OUT` (pin 17) is adjacent to `VREF` (pin 18). It is a 16 mA pad that toggles by default at about
  1.5 MHz, because `TEMP_CTRL` resets to 0x01.
- Its current returns on IOVDD, which the board ties to VDDA (P3).
- During startup, before VREF settles, the T2F runs faster, because its threshold is VREF.
- With the P5 "0 nF" option, VREF is a 22 kΩ node on the pin.

Action:
- Keep ≥ 10 nF on `VREF`.
- Calibrate with T2F in its operating state, or with `T2F_EN` = 0 and then check with T2F on.
- Decouple VDDA at pin 7 separately from IOVDD.

### S8. Grounds: one VSS net for analog, digital and substrate; VSS and IOVSS joined only through the substrate on the die; the separate current-sense links

- In the CDL, `VSS` is the single ground of BGR, SENSE, TRIP, GATE, T2F, OSC, the digital macro, and the
  DOSE/DUT substrate (CDL 17887–17899).
- `IOVSS` reaches `VSS` only through the `ptap1` substrate resistors of each IO cell (derivative cells,
  CDL 18143–18357). No metal connects them.
- All chip decks use one ideal ground.
- Measurement B5 asks for separate current-sense links on VDDA and IOVDD. A sense resistor in the IOVDD
  path lets VDDA rise above IOVDD during IO current spikes: 30 mA `GATE` edges, 16 mA `TEMP_OUT`. That
  forward-biases the VDDA pad's DCP diode and the `Clamp_P20N0D` drain–bulk junction (CDL 18214), a dynamic
  P3 violation.

Board:
- Tie VSS, IOVSS and the paddle at the package.
- Links ≤ 0.5 Ω with decoupling on the chip side of each link, or place the sense on the common 3.3 V
  source instead.

---

## Notes

**N1. BGR/T2F sharing of `pbias`/`pcasc`/`VREF`.** The T2F loads `pbias` and `pcasc` with gates only:
`MMPO`, `MMPR`×2, `MMPB`, `MMPF`, `MMCO`, `MMCR`×2, `MMCB`, all 10/4 µm HV devices (CDL 2796). It loads
`VREF` only through the bases of `QQA1`/`QQA2` via `MMX1`. There is no DC path. From the existing chip
waveforms (`q`, tt/27 °C, 10 nF pin, BGR `sch`), T2F on against off gives:

| Node | Change |
| --- | --- |
| `VREF` | 1.04546 → 1.04499 V (−0.47 mV); pp 0.31 → 0.78 mV |
| `vth_hard` | −0.47 mV |
| `icmp` | −0.25 mV |

That is below 0.2 LSB of threshold shift. `T2F_EN` does not disconnect the T2F from the rails. A T2F defect
such as a gate short would bias the BGR and, through `IPTAT`, all three SENSE OTAs. There is no isolation.
Accepted for a test chip.

**N2. VREF loading.** The consumers are:

- the SENSE `XREF` buffer (gate);
- the T2F bases (tens of nA, N1);
- `pad18` through `padres`: 587 Ω, `dantenna` to VSS, `dpantenna` to IOVDD (CDL 17917, 18357).

The DAC reference is `vref_buf` (CDL 17899). The pedestal and the DAC taps both derive from it, so the
shunt-referred threshold is proportional to `vref_buf`. A slow `VREF` during startup and probe loading
(1 MΩ ⇒ about 2 %) shift every threshold proportionally. During startup the shift is in the early-trip
direction, which is safe. No consumer can pull `VREF` significantly.

**N3. CLEAR or retrigger into a persistent fast-path fault.** While `clr_d` (2 × `osc_clk`, about 212 ns)
and `set` are both high, `q` = `qb` = 0 and `gate_h` = 1. `GATE` is then driven on for the clear pulse,
current-limited (30 mA × 212 ns / 5 nF ≈ 1.3 V). Document it. `EN` low does not have this issue.

**N4. FAULT_N semantics.** `FAULT_N` = ¬`q`. It reads "no fault" while `EN` is low, and it floats while VDD
is absent. A host cannot tell "disabled" from "healthy" by this pin.

**N5. Latch-up.** The protection is p+ VSS guard rings per macro plus the DRC `LU.a`/`LU.b` rules (passed in
main and maximal DRC). There is no n-well/p+ double guard between the 3.3 V macros and the 1.2 V logic. The
G1 die's own SEL susceptibility is not assessed. That matters if the parts go into a heavy-ion beam.

**N6. Domain-crossing inventory (CDL).**

VDD → VDDA:

| Cell | Count | CDL | Supplies |
| --- | ---: | --- | --- |
| `g1_ls_up` (`t2f_en`, `t2f_mode`, `bgr_r4`) | 3 | 17893–17895, 4052 | VDD / VDDA / VSS, correct |
| `g1_lvlup` in `g1_gate` | 4 | 2697 | correct |
| `g1_tlvlup` in the DACs | 16 | 3991 | correct |

VDDA → VDD:

| Cell | Count | CDL |
| --- | ---: | --- |
| `g1_lvldn` | 3 | 2715 |
| T2F internal level-down on `vdd12` | 1 | 2796 |

The pads' own `LevelUp`/`LevelDown` cells cross between VDD and IOVDD.

The analog crossings are `icmp` (a resistor divider into the LV gate, S1) and the DAC taps (≤ `vref_buf`).

No path back-drives VDDA into VDD in the custom cells: the LV PMOS in the level-down cells are pulled only
by HV NMOS. In the VDD-only window (M1) the `LevelDown` core inverters of `EN`, `SCLK` and `SDI` have a
floating input, so a crowbar current flows. It is not quantified.

**N7. Digital outputs at reset.** Every output that drives analog comes from an async-reset flop. `osc_en`
= 1 under reset (`X_5608_` resets to 0, then inverts), so the clock runs for the synchronous release.
`cmp_clk` = 0: the soft comparator precharges and the hard comparator holds, which is harmless because
`fast_en` = 0. `t2f_en` = 1 and `bgr_r4` = 0. The only window in which these are X is the VDD-only window of
M1.

---

## §A. CDL facts used

| Item | CDL line |
| --- | --- |
| top ports, 22 pins | 13039 |
| block instances | 17887–17899 |
| pad instances | 17900–17923 |
| `IOPadAnalog`: `pad`, `padres` pins; P20N0D, N20N0D clamps; DCN/DCP diodes; SecondaryProtection | 18214 |
| `IOPadIn` / `LevelDown` | 18224 / 18292 |
| SecondaryProtection: 586.9 Ω `rppd`, `dantenna` to VSS, `dpantenna` to `plus` = IOVDD | 18357 |
| VDD pad clamp to IOVSS | 18277 |

Single-ended nets in the top cell: `i_core_trip_set`, `i_core_trip_set_sel`, `i_core_clk_div_out`,
`i_core_gate_en`, `i_core_trip`, `i_core_fault_n_dig`, `i_core_trip_cause_*`, `i_core_unused_vbe`,
`i_core_dvbe`, `i_core_unused_vped`, and `_nc1`…`_nc9` (unused `padres`). No block **input** is left
floating. The only input without a consumer is the `TRIP_SET` pad itself (S4).

## §B. Deck essentials (scratch; not committed)

**B.1, power-up.**

- Model libraries: PDK corner libraries (`cornerMOSlv/hv`, `cornerRES`, `cornerCAP`, `cornerDIO`) and
  `sg13g2_io.spi`. For the "without `dantenna`" runs, the `g1nd_*` copy that `run_top.py --pads nodcn` emits.
- Netlist: `blocks/g1_gate/sim/netlist/g1_gate.spice`, the same schematic as CDL 2667.
- Supplies: `Vdd` 1.2 V DC and `Vdda` = IOVDD PWL 0 → 3.3 V, each through 0.5 Ω and 1 nF.
- Instances: `XPE en_pad en_core vdd 0 vdda 0 sg13g2_IOPadIn` with `en_pad` = 0 V;
  `XG 0 0 0 0 en_core gate_core fault_core tripped vdd vdda 0 g1_gate`;
  `XPG gate gate_core vdd 0 vdda 0 sg13g2_IOPadOut30mA`.
- Load: 10 Ω + 5 nF, and 10 kΩ from `GATE` to ground.
- Integration: gear.
- Initial condition: `.ic v(xpe.xi0.net2)=0` where stated.

**B.2, Kelvin leads.**

- Netlist: `blocks/g1_trip/sim/qualification/joint586-…-r1/sense.spice` (the c1414 `sch` view).
- Sources: VDDA 3.3 V, `vref` 1.04546 V, `Iptat` 4.13 µA into `iptat`.
- Shunt: at `{VSH}` through 1 Ω leads, with 1 GΩ for the open lead.
- Load: 50 kΩ / 50 kΩ divider standing in for `g1_cond`.
- Analysis: DC operating point.

**B.3, kick.**

```
flow/run.sh bash postlayout/run_kick_train.sh postlayout/g1_trip_nf4_pex.spice nf4 mos_tt 1.2 27 hard <out> {4|16} 0.8u 254 255
```

Decisions were read 50 ns after each hard strobe for k = 1…3, following the `kick_threshold.py` convention.

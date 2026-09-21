# G1_TOP — chip-level simulation of the breaker path

State: **chip-level mixed-signal simulation of the breaker path built and run (2026-09-19), schematic
netlists of the analog blocks**: external shunt and load → `SENSE_P`/`SENSE_N` analog pads (PDK
`sg13g2_IOPadAnalog` models) → G1_BGR → G1_SENSE → G1_TRIP → G1_GATE at transistor level → external
FET gate (5 nF + 10 Ω) → load switch, closed loop, with the real digital RTL (`g1_digital`,
`blocks/g1_ctrl/rtl` + `blocks/g1_seu/rtl`) co-simulated inside ngspice through the XSPICE `d_cosim`
code model and Icarus Verilog. The soft path is therefore the **real RTL** at chip level, not a
behavioural stand-in. No layout exists for this block; the post-layout repeat with the kpex block
netlists and the temperature cases are listed as *not run* where no log exists. Every number below is
simulated. Two things the deck does **not** contain at transistor level are stated up front, because
the request asked for them: the `GATE`/`FAULT_N` output pads and the `EN`/`SCLK`/`SDI` input pads are
behavioural stand-ins fitted to (or bypassing) the PDK pad models, and the clock delivered to the
RTL is an ideal source at G1_OSC's block-simulated frequency; the reasons are numerical and are
documented with evidence in "Numerical notes". Both pads and the transistor-level oscillator are
simulated in their own chip-context runs (cases `g*` and `osc`).

**Recovery finding (2026-09-20): earlier chip-level timing results are not
accepted verification evidence.** The clock's 0.55–0.65 V ADC band can deliver
two RTL rising edges during one analog edge. The isolated regression in
[sim/bridge_probe/README.md](sim/bridge_probe/README.md) reproduces this and
verifies a separate 0.6 V single-threshold clock receiver. Corrected runs use
`_clockfix` tags; original logs are retained. All historical trip/no-trip
observations below require revalidation. The affected in-flight runs were
stopped before restarting with the corrected receiver.

## What it is

`sim/run_top.py` generates and runs one ngspice deck per case (copies in `sim/decks/`, logs in
`sim/logs/`, decimated waveforms in `sim/results/waves/`, one summary block per run appended to
`sim/results_top.txt`; `sim/summarize.py` turns the logs into `sim/results/summary.md`).

```
board:  I_load(t) = profile(t) x sw(V_FET_gate)      sw = 0.5 (1 + tanh((V - 1.5 V)/0.15 V))   (load switch on the external FET gate)
        R_shunt 25 mOhm (1 A nominal = 25 mV = DAC code 128), R_gnd 10 mOhm (low-side return), 1 Ohm Kelvin traces,
        FET gate 10 Ohm + 5 nF, FAULT_N 20 pF, 10 nF on the VREF pin, EN / SCLK / SDI 3.3 V PWL sources with 2 ns edges,
        one 3.3 V rail -> VDDA (pin 7) and IOVDD (pin 3) each through 0.5 Ohm + 1 nF, 1.2 V VDD through 0.5 Ohm + 1 nF
pads:   sg13g2_IOPadAnalog x3: SENSE_P, SENSE_N on the bare pad terminal, VREF on the padres terminal (padframe/README.md)
chain:  g1_bgr (r4 = 0) -> VREF, IPTAT -> g1_sense -> ISENSE -> g1_trip (DAC codes from the RTL, strobe cmp_clk from the RTL)
        -> cmp_soft, cmp_hard -> RTL g1_digital (256/128 SEU) -> trip_d, clr_d, fast_en -> g1_gate -> gate_core, fault_core, tripped
digital: g1_dig_cosim.v (sim/rtl) wraps g1_digital; ports matched by position to an XSPICE d_cosim instance (Icarus shim ivlng);
        adc_bridge 0.6/0.6 V on osc_clk; 0.55/0.65 V on cmp_soft, cmp_hard, tripped; dac_bridge 0/1.2 V, 0.3 ns edges on every RTL output;
        EN, SCLK, SDI reach the RTL as an XSPICE d_source stimulus with the same edge times as the pad PWLs
clock:  ideal 1.2 V square wave at the G1_OSC block-simulated frequency (9.919 MHz schematic, 8.994 MHz post-layout),
        enabled at 0.1 us by the RTL's osc_en; case osc runs the transistor-level g1_osc on the chip VDD with the RTL
outputs: GATE pad = 47 Ohm driver to IOVDD/0 switched by gate_core (fitted to the g1_gate block results with the
        sg13g2_IOPadOut30mA model: 5 nF + 10 Ohm fall 90-10 % 606 ns, arming 677 ns); FAULT_N = 500 Ohm driver
```

Timeline of every functional case (operating point at t = 0, supplies on): oscillator enable 0.1 µs,
`EN` high at 3.07 µs, one serial write frame `INRUSH` = 0x00 at 18.2–21.3 µs (SPI mode 0, 4.96 MHz,
`f_SCLK` = `f_OSC`/2), register update seen at 21.4 µs (`STATUS.INRUSH_ACTIVE` falls), load event at
30 µs. `INRUSH` = 0 is the one register the host writes: with the reset value 0x14 both trip paths are
masked for 1.0 ms after `EN`, which would make every fast case a 1 ms run. Every other register keeps
its reset value (`DAC_SOFT` 0x99 = 30.0 mV, `DAC_HARD` 0xFE = 49.8 mV, `SOFT_TIME` 0x0027 ≈ 1 ms,
`HARD_N` 4, `MODE` 0x03) unless the case says otherwise (`c_fast`: `MODE` = 0x23; `a_s`, `b_s`,
`d_s`: `SOFT_TIME_L` = 0x01). Case-specific waveforms are in `sim/run_top.py` (`make_cases`).

## Simulated

Toolchain: `flow/run.sh` container (`PLAN.md` §2), ngspice 46 with the PDK OSDI models loaded by
`sim/.spiceinit`, Icarus Verilog 14.0 (`iverilog -g2005`, `vvp` library `/foss/tools/iverilog/lib` on
`LD_LIBRARY_PATH` for the `ivlng` shim), PDK commit `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` (every
log header records the PDK commit, the ngspice and iverilog version lines and the sha256 of every
netlist and RTL file used). Run from the repository root:

```
G1_WORKDIR=designs/g1-guardian/blocks/g1_top/sim flow/run.sh python3 run_top.py --list
G1_WORKDIR=designs/g1-guardian/blocks/g1_top/sim flow/run.sh python3 run_top.py q c c_fast e f a_s b_s d_s
G1_WORKDIR=designs/g1-guardian/blocks/g1_top/sim flow/run.sh python3 run_top.py --front beh a b d
G1_WORKDIR=designs/g1-guardian/blocks/g1_top/sim flow/run.sh python3 run_top.py --temp 125 c e
G1_WORKDIR=designs/g1-guardian/blocks/g1_top/sim flow/run.sh python3 run_top.py --netlist pex c e q
G1_WORKDIR=designs/g1-guardian/blocks/g1_top/sim flow/run.sh python3 run_top.py osc gA gB gA_pd gB_pd
python3 designs/g1-guardian/blocks/g1_top/sim/summarize.py
```

Block netlists (`--netlist sch`, the frozen schematic netlists; `--netlist pex`, the kpex 2.5D
capacitance netlists of the laid-out macros):

| Block | schematic | post-layout |
| --- | --- | --- |
| G1_BGR | `../g1_bgr/xschem/g1_bgr.spice` | `../g1_bgr/sim/postlayout/g1_bgr_pex.spice` |
| G1_SENSE | `../g1_sense/sim/netlist/g1_sense.spice` | `../g1_sense/sim/postlayout/g1_sense_pex.spice` |
| G1_TRIP | `../g1_trip/sim/netlist/g1_trip.spice` | `../g1_trip/sim/postlayout/g1_trip_pex.spice` |
| G1_OSC (case `osc`) | `../g1_osc/sim/netlist/g1_osc.spice` (revision 5) | `../g1_osc/sim/postlayout/g1_osc_pex.spice` |
| G1_GATE | `../g1_gate/sim/netlist/g1_gate.spice` | `../g1_gate/sim/postlayout/g1_gate_pex.spice` |
| digital | `../g1_ctrl/rtl/*.v`, `../g1_seu/rtl/*.v` (register map 1.1 RTL, the source of the hardened macro run7) | — (RTL, not the gate-level netlist) |
| pads | `$PDK_ROOT/$PDK/libs.ref/sg13g2_io/spice/sg13g2_io.spi` | — |

Model lines (all decks): `cornerMOSlv.lib`/`cornerMOShv.lib` `mos_tt`, `cornerRES.lib` `res_typ`,
`cornerCAP.lib` `cap_typ`, `cornerHBT.lib` `hbt_typ`, `cornerDIO.lib` `dio_tt`; `--corner ss|ff` selects
`mos_ss res_wcs cap_wcs hbt_wcs` / `mos_ff res_bcs cap_bcs hbt_bcs` (not run). Solver, transistor-level
front end: `method=trap reltol=0.001 abstol=1e-10 vntol=1e-6 chgtol=1e-14 rshunt=1e12 itl4=100`,
maximum step 5 ns; behavioural front end and power-up cases: `method=gear reltol=0.002 abstol=1e-8
vntol=1e-4 chgtol=1e-12 rshunt=1e12` (see "Numerical notes" for why).

Measurements per run (all in the log, `QUIET`/`CLOCK`/`SUPPLY_uA`/`TRIP`/`CHARGE`/`REARM`/`POWERUP`
lines): quiet values after the register write (VREF, ISENSE, comparator input `icmp`, the two DAC
outputs, load current, GATE, the DAC codes read back from the analog code lines, `INRUSH_ACTIVE`),
oscillator and strobe frequency, supply currents averaged over the armed quiet window (rail totals and
per block through 0 V sources on every block supply pin), and after the load event: `tripped` (G1_GATE
latch), `trip_d` (RTL latch), first crossing of `GATE` below 1 V and below 0.33 V, minimum and final
`GATE`, peak and final load current, cause code read from the RTL (`trip_cause`), `SOFT_PEAK`
register, charge passed after the event.

### Results — waveform library (schematic netlists, tt, 27 °C)

Historical tt, 27 °C schematic runs (times relative to the load event; simulated, **pending revalidation of the clock**):

| Case | Functional result | GATE < 0.33 V | Evidence in `sim/logs/` |
| --- | --- | --- | --- |
| q, nominal load | observed no trip; revalidation required | not applicable | `q_sch_tl_tt_27C.log` |
| a_s, short 1.5× pulse | observed no trip; revalidation required | not applicable | `a_s_sch_tl_tt_27C.log` |
| b_s, held 1.5× load, shortened timer | observed soft trip; revalidation required | 26.86 µs | `b_s_sch_tl_tt_27C.log` |
| c, 3× step | observed hard trip; revalidation required | 1.96 µs | `c_sch_tl_tt_27C.log` |
| c_fast, 3× step with FAST_EN | observed hard trip; revalidation required | 0.95 µs | `c_fast_sch_tl_tt_27C.log` |
| e20, 4× step with 20 ns rise | observed hard trip; revalidation required | 1.55 µs | `e20_sch_tl_tt_27C.log` |
| f, trip then EN toggle | observed re-arm to 1 A; revalidation required | 1.96 µs before re-arm | `f_sch_tl_tt_27C.log` |

The complete parsed measurements, including incomplete and failed attempts, are
in [sim/results/summary.md](sim/results/summary.md). The e20 waveform does not
validate the original e case's 100 ns rise.

### Quiet operating point and supply currents (armed, nominal 1 A load, before the event)

Case q reports simulated VREF 1.03785 V, ISENSE 1.4967 V and VDDA current
1055.33 µA (BGR 22.04 µA, SENSE 1033.29 µA). RTL and ideal-clock supply
currents are not physical estimates. See the generated summary for all values.

### Clock case `osc` (transistor-level G1_OSC clocking the RTL on the chip VDD)

**not run to completion**: no completed `osc` log exists. Block oscillator results do not establish this chip-context check.

### Power-up (case g)

**not run**: no completed `gA`, `gB`, `gA_pd` or `gB_pd` log exists in this suite. The separate G1_GATE pad/power-up evidence remains block-level evidence.

### Temperature and post-layout

The c and e schematic runs at 125 °C **failed** with timestep collapse near
30.020 µs and 30.066 µs respectively (`sim/logs/*125C.log`). Partial measurements
from these runs are not functional verdicts. Post-layout chip-path checks are
**not run to completion**; a c-case run was started during recovery on 2026-09-20.

## Behavioural front end (`--front beh`)

Used for the three long-window cases (a), (b), (d) at the default `SOFT_TIME` (≈ 1 ms) and as the
cross-check column of the table above. G1_BGR, G1_SENSE and G1_TRIP are replaced by their block-level
transfer functions: VREF 1.0399 V fixed; ISENSE = 0.9992 V + 19.99 × (SENSE_P − SENSE_N) through a single
pole at 4.19 MHz (`../g1_sense/sim/results_sense.txt`); conditioning divider ISENSE/2 with 25 kΩ into
1 pF; DAC taps VREF × (255 + code)/530 from the RTL codes; two ideal clocked comparators (2 mV wide
tanh decision, sampled by XSPICE `d_dff` on the rising / falling `cmp_clk` edge like the StrongARM
pair). G1_GATE and the pads are the same as in the transistor-level deck. What this front end cannot
show: comparator kickback, offset, sense-amplifier settling, supply coupling, DAC settling — those are
the transistor-level runs' job; what it shows is the RTL's window/decay logic against the load profile
at chip level with the real GATE path.

## Numerical notes (what was tried, with the evidence under `build/g1_top/dbg/` while it exists)

These decide what the deck contains and are the reason for every deviation from "everything at
transistor level":

1. **`d_cosim` is available in this ngspice build** (`digital.cm` carries `d_cosim`, the Icarus shim
   `ivlng.so`/`ivlng.vpi` and the Verilator helper `vlnggen` are installed). The Icarus route works once
   the top module carries a `` `timescale `` directive (without it the shim delivers no events: a 4-bit
   counter test stayed at zero) and `libvvp.so` is on `LD_LIBRARY_PATH`. The RTL's clock, comparator
   and latch inputs go through `adc_bridge`; the RTL outputs through `dac_bridge`. Verilator was not used.
2. **The analog operating point is computed with the digital outputs at zero**: XSPICE does not run
   the co-simulator during the OP, so the RTL's reset values (DAC codes, `osc_en`, trim) arrive 0.3 ns
   into the transient and the DAC strings settle in the first microsecond (visible as `vth` = 0.499 V
   at t = 0 in the waveform files). Nothing is measured before 21 µs.
3. **PDK IO-pad models and the StrongARM comparators need incompatible integration settings.** The
   `sg13g2_IOPadOut30mA`/`IOPadIn` models stop the solver ("timestep too small", always on an
   internal node of one of their `dantenna`/`dpantenna` diodes, whose model cards carry
   rs = 0.2–1.7 MΩ per unit and tt = 700 ns) whenever an XSPICE event lands on one of their switching
   edges, unless the integration is gear with `chgtol` = 1e-12 (`w3`, `x1..x4`, `beh_d1n` tests).
   With that setting the StrongARM comparators of G1_TRIP decide **wrongly at 250 mV overdrive** (the
   `kb*`/`kbe*` tests: with gear, `reltol` ≥ 0.002 and `chgtol` = 1e-12 the hard comparator resolved in
   the wrong direction in about one strobe of three; the block decks use `tran 0.2n`, trap, default
   tolerances and are right). Attempts to have both: bridge hysteresis, bridge delays, `itl4`, `gmin`,
   `rshunt`, tolerances, 10 ns pad edges, threshold-aligned PWL corners, a breakpoint train through
   the strobes — all fail on one side or the other (`z*`, `w*`, `x*`, `kbe_*` logs). The decision was
   to keep the analog chain exact and take the pads out of the transistor-level decks: the `EN`/`SCLK`/
   `SDI` pads become ideal 3.3 → 1.2 V level copies, the `GATE`/`FAULT_N` pads become drivers fitted to
   the g1_gate block results with the real pad models (`../g1_gate/sim/results_gate.txt`), and the
   transistor-level runs use trap with `chgtol` = 1e-14. The pad models themselves are exercised
   in the power-up cases and in the behavioural runs (gear, `chgtol` 1e-12), where no comparator exists.
4. **The transistor-level oscillator cannot drive the RTL in the full deck.** With g1_osc on the chip
   VDD and the RTL clocked from its output, the solver aborts within a few µs after `EN` or at the
   oscillator start, blamed on the bandgap's `XQD1` HBT (VBIC) or a pad diode, in every one of
   fourteen variants (tolerances, integration method, bandgap post-layout netlist, VREF isolation,
   local decoupling, separate supplies: `z0..z17`); the same deck runs with an ideal clock of the same
   frequency (`y1`), or without G1_TRIP (`y2`), or without the co-simulation (`y4`). The RTL clock is
   therefore an ideal source at the block-simulated frequency; case `osc` runs the transistor-level
   oscillator with the RTL, G1_BGR and G1_SENSE (no G1_TRIP, no pads).
5. **Oscillator frequency is time-step dependent** (schematic g1_osc alone, gear): maximum step 20 ns
   → +9.6 %, 5 ns → +3–4 %, 1 ns → +1 %, 0.2 ns → 9.94 MHz (block value 9.92). With the XSPICE bridge
   attached the 5 ns figure is +5–9 %. Hence the 5 ns maximum step everywhere and the ideal clock at
   the block value for the trip runs; the `osc` case reports its own measured frequency.
6. **XSPICE forces `trtol` = 1** ("Reducing trtol to 1 for xspice 'A' devices"); an explicit `trtol` in
   `.option` does not override it. With `trtol` = 7 and `reltol` = 0.005 even the block-level
   comparator deck decides wrongly at a 5 ns maximum step.
7. **Bridge unknown states double-count as clock edges**: The recovery regression also confirmed this on `osc_clk`; its receiver now uses one 0.6 V threshold. Historical clock and trip-timer results require reruns. Original finding: an `adc_bridge` whose input passes through the
   0.55–0.65 V band at an analog time point emits `U`, which the RTL sees as `x` (0→x→1 = two
   `posedge`s); a serial frame then loses its framing. The RTL's `EN`/`SCLK`/`SDI` are therefore a
   digital `d_source` stimulus; the analog copies of the same edges still drive G1_GATE.
8. ngspice control language: a `>` inside a `let` expression is an output redirection (files named
   `0.6)` appeared); `gt`/`lt` are used instead. Only the last `.save` line of a deck counts.
9. **Speed**: the transistor-level deck (≈ 1500 MOS, 1150 resistors, 19 000 nodes with the trip
   block's DAC trees) runs 36 µs in 23–27 min on the emulated container at load; 1 ms would take
   about 12 h per case, which is why the ≈ 1 ms `SOFT_TIME` cases use the behavioural front end and the
   transistor-level soft-path cases use `SOFT_TIME` = 0x0001 (256 osc_clk) with the load timing scaled
   by the same factor.

## Scope statement

| Part | Level | Netlist / model |
| --- | --- | --- |
| G1_BGR, G1_SENSE, G1_TRIP (both comparators, both DACs, level shifters, conditioning divider), G1_GATE (latch, level shifters) | transistor level | schematic netlists (`--netlist sch`); post-layout kpex CC netlists where the table says `pex` |
| `SENSE_P`, `SENSE_N`, `VREF` pads | transistor level | PDK `sg13g2_IOPadAnalog` (ESD clamps and diodes) |
| digital core (register file, serial interface, trip timer, SEU monitor) | RTL, co-simulated | `g1_digital` RTL of the hardened macro; not the gate-level netlist, no SDF |
| `GATE`, `FAULT_N` output pads | behavioural, fitted | 47 Ω / 500 Ω drivers switched by `gate_core`/`fault_core`; timing from the g1_gate block runs with the PDK models |
| `EN`, `SCLK`, `SDI` input pads | behavioural | ideal 3.3 → 1.2 V level copies (pad delay ≈ 1 ns not modelled) |
| RTL clock | ideal source | at the g1_osc block frequency (schematic 9.919 MHz, post-layout 8.994 MHz); g1_osc itself transistor-level in case `osc` only |
| load, shunt, FET gate, board decoupling | behavioural | current-source profile × tanh switch on the FET gate; RC elements |
| long-window cases (a), (b), (d) | behavioural front end | block transfer functions, ideal clocked comparators, real RTL, real G1_GATE, PDK output pads |
| power-up cases (g) | pads at transistor level, front end behavioural | PDK pad models for `EN`, `GATE`, `FAULT_N`, `SCLK`, `SDI`; supply ramps |

Not simulated: the full-chip extracted netlist (no chip-level PEX), the chip-level routing parasitics
between macros (300 fF on ISENSE and 20–100 fF on the digital nets are estimates), the digital
macro's supply current (LibreLane estimate 0.97 mW at 10 MHz, `../g1_ctrl/README.md`), package and
bond-wire parasitics, the board beyond the elements listed, process corners and mismatch at chip
level, the `TRIP_SET` pad path (not built), `SDO` and `TEMP_OUT` pads.

## Checks

| Check | Status | Evidence |
| --- | --- | --- |
| Nominal schematic cases q, a_s, b_s, c, c_fast, e20, f | failed clock validation; reruns not run to completion | waveform table and `sim/logs/` |
| Schematic c/e at 125 °C | failed, solver timestep collapse | `sim/logs/*125C.log` |
| d_s and original e at 27 °C | not run to completion | logs have no completion footer |
| Default-window behavioural a/b/d | not run to completion; started during recovery | `sim/logs/` |
| Post-layout c | not run to completion; started during recovery | `sim/logs/` |
| Post-layout q/e, osc, power-up suite, process corners | not run | no completed logs |
| Full-chip PEX and physical measurements | not run | no extracted chip or measured sample |
| Layout DRC/LVS of this simulation-only block | not applicable | chip layout evidence is in G1_PADRING |

## Unverified

- Full-chip extracted netlist (no chip-level PEX exists yet) and the inter-macro wiring; package,
  bond wire and board parasitics beyond the lumped elements above.
- The PDK output/input pad SPICE models together with the transistor-level comparators in one
  transient (numerical incompatibility, note 3); the fitted drivers reproduce the block-level pad
  timing into 5 nF + 10 Ω only.
- The transistor-level oscillator clocking the RTL inside the full chain (note 4); its frequency
  and current in the chip supply context come from case `osc`.
- Process corners (`--corner ss|ff` exists, not run), mismatch, supply ±10 % at chip level.
- The default 1 ms `SOFT_TIME` window at transistor level (behavioural front end only, note 9).
- Comparator decisions at small overdrive at chip level (the trip cases use ≥ 1.4 × nominal; the
  block MC gives the offset).
- Digital core at gate level with timing (the RTL is co-simulated; the macro's gate-level regression is
  in `../g1_ctrl/sim`).
- Power-up with the analog blocks' real behaviour under supply ramps (the power-up cases use the
  behavioural front end; g1_bgr and g1_sense start-up are block-level results).

# Chip-level timing of the g1_digital macro

For the ring / integration owner (`../../g1_padring`). Companion file:
`g1_digital_top.sdc` (constraints to source from the chip SDC). Evidence:
`../reports/top_sta_dryrun1350/`. Macro of record: run7 (`../README.md`).

## 1. The hold violation of the D14 dry run, explained

`reports/dryrun-1350/stapostpnr_summary.rpt` of the padring reports hold
−0.094 ns (fast), −0.015 ns (typ), +0.126 ns (slow) on reg-to-reg paths inside
`g1_digital` (`i_core.u_digital/_6673_ → _6674_`, the SCLK-domain serial shift
register), while the macro's own signoff (`../reports/librelane_run7/`) has
+0.106 / +0.185 / +0.326 ns on the very same paths. The difference is
**exactly 0.200 ns in every corner**, and the two path reports are identical
line by line except one:

| | macro signoff (`run7`, `flow/g1_digital.sdc`) | chip dry run (`g1_chip_top.sdc`) |
| --- | --- | --- |
| launch clk→Q of `_6673_` (fast) | 0.128526 ns | 0.128529 ns |
| library hold time of `_6674_` | −0.026901 ns | −0.026901 ns |
| **clock uncertainty applied to hold** | **0.05 ns** (`set_clock_uncertainty -hold 0.05`) | **0.25 ns** (`set_clock_uncertainty $CLOCK_UNCERTAINTY_CONSTRAINT`, PDK default 0.25, no `-setup`/`-hold`, so it applies to both) |
| slack | +0.106 ns | −0.094 ns |

So: not a library problem and not a corner mismatch. Two facts about the chip
flow explain why the macro's internals are re-judged at all:

1. **`STA_MACRO_PRIORITIZE_NL` defaults to `true`** in LibreLane 3.1.0.dev2
   (`steps/openroad.py`, `MultiCornerSTA`): when a macro has `nl` and `spef`
   views, the chip STA reads the macro's gate-level netlist and SPEF and times
   every internal path with the *chip* SDC; the liberty views are read too
   (`STA-1140 … library g1_digital already exists` in `flow.log`) but are not
   what times the instance. Hence "hold inside g1_digital".
2. The chip template SDC (from the IIC-JKU AMS template) constrains **one**
   clock, `SCLK` at `pad14_sclk/p2c`, with the LibreLane/PDK defaults: 0.25 ns
   uncertainty on setup and hold, 5 % derating, 20 % IO delays. The macro was
   hardened with 0.5 ns setup / 0.05 ns hold uncertainty (`flow/g1_digital.sdc`;
   run3, with 0.5 ns applied to hold on the 1024/256 SEU configuration, failed
   its hold repair with "max buffer count reached" on 2418 endpoints, and a
   same-edge hold check with a propagated clock has no jitter term to model, so
   0.05 ns was chosen and documented in `../README.md`). The template's 5 % derate has no visible effect on
   this path: every cell delay in the two reports is identical to 3 fs.

A second finding from the same reports: **`osc_clk` has no clock at chip
level**. `g1_osc` is a black box without a timing model, so nothing defines a
clock on its output, and the 1148 `osc_clk` registers of the macro (register
file, trip timer, SEU chains) were simply unconstrained in the dry-run STA. The
52 SCLK-domain flops were the only ones checked; that is where the −0.094 ns
came from.

## 2. The fix: chip-level constraints, not new liberty views

**Recommendation: keep the netlist-based timing (flow default) and source
`g1_digital_top.sdc` from `flow/g1_chip_top.sdc`, after the template's own
`create_clock` / `set_clock_uncertainty` / `set_propagated_clock` lines.** It
adds what the macro signoff assumed:

| Constraint | What it does |
| --- | --- |
| `create_clock -name osc_clk -period 100 [get_pins i_core.u_digital/clkbuf_0_osc_clk/A]` + `set_clock_transition 0.3` + `set_propagated_clock` | defines the oscillator clock. It has to sit on the macro's root clock-buffer input: a clock created on `i_core.u_osc/osc_clk` or on the hierarchical pin `i_core.u_digital/osc_clk` is accepted by OpenSTA but propagates to **0** registers, because the only leaf driver of that net is the black box's output pin, which has no liberty and no direction (measured on the dry-run database: 0 / 0 / 1148 registers for the three choices). `clkbuf_0_osc_clk` is the only leaf pin the port drives in the run7 netlist. The oscillator-to-macro wire is thereby excluded from the clock latency; it is common to every osc_clk path and changes no check. |
| `set_clock_groups -asynchronous -group osc_clk -group SCLK` | the two domains are asynchronous; all crossings are synchronisers (register map 1.3) |
| `set_clock_uncertainty -setup 0.5` / `-hold 0.05` on both clocks | the macro's signoff values; later statements override the template's 0.25 ns for the same clock |
| `set_false_path -from [get_ports EN]`; `set_false_path -through i_core.u_digital/{cmp_soft,cmp_hard,tripped,en,por_n}` | asynchronous inputs (synchronised inside); `EN` is also the reset and must not get an SCLK-relative check into the osc_clk domain |
| `set_input_delay -min 2.0 -clock SCLK [get_ports SDI]` | the host drives SDI on the falling SCLK edge (register map 1.1); the template's 20 ns max delay stays |

The outputs of the macro end at analog macros without timing models (quasi-
static levels; timed in the macro signoff with a 20 ns output delay) and need
nothing at chip level once `osc_clk` exists.

**Verified** by re-running the dry run's own signoff STA step
(`OpenROAD.STAPostPnR`, same ODB / netlists / SPEF / `config.json` of
`flow/runs/dryrun-1350/54-openroad-stapostpnr`, via `python3 -m
librelane.steps run`) with the ring owner's SDC as is, and with
`g1_digital_top.sdc` appended (`../reports/top_sta_dryrun1350/summary.txt`,
worst hold paths per corner in `hold_worst_{baseline,test}_<corner>.rpt`, the
SDC used in `g1_chip_top_plus_g1_digital_top.sdc`):

| Corner | baseline: hold worst / violations / `osc_clk` paths | with `g1_digital_top.sdc`: hold worst SCLK / osc_clk / violations | setup worst SCLK / osc_clk |
| --- | --- | --- | --- |
| fast 1.32 V −40 °C | **−0.094 ns / 48 / 0** | **+0.106 / +0.125 ns / 0** | 28.3 / 96.6 ns |
| typ 1.20 V 25 °C | −0.015 ns / 5 / 0 | +0.185 / +0.205 ns / 0 | 27.7 / 95.0 ns |
| slow 1.08 V 125 °C | +0.126 ns / 0 / 0 | +0.326 / +0.348 ns / 0 | 26.4 / 92.3 ns |

The baseline reproduces the dry-run numbers to six decimals; with the
snippet the SCLK-domain hold equals the macro signoff (+0.106 ns) and the
osc_clk domain is checked for the first time at chip level (6003 paths
reported, 1148 registers; hold +0.125 ns, setup 96.6 ns at fast). The remaining
"max slew" entries of the chip STA (12, all corners) are the `pad`/`padbare`
pins of the analog `sg13g2_IOPadAnalog` cells (200 ns "transition" from the pad
library on unconstrained analog pins) and are not related to the macro; the 78
"max fanout" entries are the macro's CTS leaf buffers (16–18 sinks against the
default limit of 10), reported and explained in `../README.md`.

## 3. The alternative, and why not

Timing the macro as a **black box from its liberty views**
(`STA_MACRO_PRIORITIZE_NL: false`) also removes the finding: the internal paths
then live only in the macro signoff, and the chip STA checks the pad ↔ macro
interface. The views are in place for it: `lib/g1_digital__nom_{typ_1p20V_25C,
fast_1p32V_m40C,slow_1p08V_125C}.lib`, written by OpenSTA `write_timing_model`
in LibreLane's `STAPostPnR` of run7 with the macro's extracted parasitics, one
per corner (`nom_voltage`/`nom_temperature` 1.20/25, 1.32/−40, 1.08/125),
`osc_clk` and `sclk` declared as clock pins, `sdi` setup/hold against `sclk`,
`sdo` as an `sclk` falling-edge arc, every other output as an `osc_clk`
rising-edge arc; the five asynchronous inputs (`cmp_soft`, `cmp_hard`,
`tripped`, `en`, `por_n`) carry no arcs because they are false paths — they are
characterised models, not stubs. The netlist route is preferred because it
re-checks the whole macro with the real pad-to-macro wires and costs nothing
once the SDC is consistent, whereas the black box checks nothing inside the
macro and rests entirely on the macro's own signoff. If the ring owner prefers
the lib route, `osc_clk` must still be created (on `i_core.u_digital/osc_clk`,
a liberty clock pin in that case) and the macro-internal uncertainty question
disappears; the lib route has not been run here.

**Not** recommended: re-hardening the macro with 0.25 ns hold uncertainty.
Every direct flop-to-flop stage of the SEU chains and of the serial shift
register (about 640 of them) would need 0.2 ns more hold margin; run7 already
spends 264 hold buffers to bring every path to ≥ +0.1 ns under the 0.05 ns
assumption. Not run; the cost is estimated, not measured, at several hundred
more buffer cells in a macro at 81.4 % utilisation — for a check that models
jitter between two edges of the same propagated clock, which does not exist.

## 4. What else the ring owner should know

- The template's `set_clock_uncertainty` (both setup and hold) and
  `set_timing_derate` stay in force for the pad ↔ macro paths; only the two
  clocks' uncertainties are overridden. Setup slack on SCLK drops from 28.5 to
  28.3 ns because the setup uncertainty goes 0.25 → 0.5 ns (the macro's
  assumption for oscillator jitter, harmless at a 100 ns period).
- The instance names in the snippet (`i_core.u_digital`, `pad14_sclk`, clock
  name `SCLK`) follow `rtl/g1_core_dryrun.sv` / `flow/config.yaml` of the
  padring; the clock-buffer name `clkbuf_0_osc_clk` is fixed for the run7
  netlist (`g1_digital.nl.v`) and must be re-checked if the macro is re-run.
- `PINS.md` lists every macro pin with direction, domain, layer, edge and
  coordinates; `g1_digital.sdc` in this directory is the SDC the flow wrote
  back for the macro alone (not for chip use).

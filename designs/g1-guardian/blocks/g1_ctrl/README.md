# G1_CTRL

State (2026-09-26): **the chip of record r3 (`g1_chip_top_1414_r3.gds`, `7d07a784…`) carries
the RTL-only ECO (register map 1.2)**: `rtl_eco_20260925/` and `../g1_seu/rtl_eco_20260925/`,
re-hardened pin-compatible (gate netlist `4b83f181`; `ECO_20260925.md`,
`../g1_padring/reports/signoff-1414r3-20260926/README.md`, `PLAN.md` D16). It fixes red-team
findings M1, M2, M3, S2 and S5; S1 (serial framing) is not addressed.

Historical below: the rest of this README describes `rtl/` (register map 1.1) and the run7 macro
(`layout/`, `reports/librelane_run7/`), the source of the r1/r2 digital (`6181b988`, re-routed
from run7). No silicon.

`G1_CTRL` is the digital core of G1: three-wire serial interface, register
file, trip timer, and the top level that also instantiates `G1_SEU`. The
hardened macro is `g1_digital` (a one-to-one wrapper of `g1_digital_top`).
Contract: `../../specification/G1_REGISTER_MAP.md` (serial protocol, register
map, analog interface names, trip behaviour); the analog side of the same
contract is `../g1_trip/INTERFACE.md` and `../g1_t2f/INTERFACE.md`. The three
control bits that enter the 3.3 V domain use the `g1_ls_up` level shifter in
`ls/` (`ls/README.md`).

## Source

| Repository | Commit | Licence | What was used |
| --- | --- | --- | --- |
| https://github.com/ChipDesign-BV/spi-slave-ihp | `7eb03a4bdd7b9409f290261f301f80747fe8d437` | Apache-2.0 | `spi_slave.v`: command-byte convention (bit 7 = R/nW, bits 6:0 address), SPI mode-0 edge usage, two-flop synchroniser discipline, structure of the testbench tasks; `flow/config.yaml` and `flow/constraint.sdc` as the template for `flow/`. The original RTL and its LICENSE are kept unchanged in `third_party/spi-slave-ihp/`. |
| https://github.com/IHP-GmbH/ihp-sg13g2-librelane-template | `0418301723d86133de686ef743cfd668bb3d11d4` | Apache-2.0 | LibreLane option names for the IHP PDK (PDN, corners, `substituting_steps`); nothing copied. |

The serial slave was rewritten rather than reused as-is: the original
oversamples `SCK` in the system clock and needs a chip select; G1 has three
wires and an uncalibrated 10 MHz ±20 % clock, so `g1_serial` clocks the shift
logic on `SCLK`, hands off to `osc_clk` with toggle synchronisers, uses a
24-clock read frame (turnaround byte) and an idle-timeout frame reset
(register map, section 1).

## RTL

Verilog-2005 (`.v`; both iverilog 14 and yosys 0.67 read it without flags).

| Module | File | Function |
| --- | --- | --- |
| `g1_digital` | `rtl/g1_digital.v` | macro wrapper, parameters `SEU_PLAIN_LEN` = 256, `SEU_TMR_LEN` = 128 |
| `g1_digital_top` | `rtl/g1_digital_top.v` | reset synchroniser (`por_n & en`, async assert, sync release), `cmp_clk` = `osc_clk`/2 divider, instances, `gate_en = en & ~trip` |
| `g1_serial` | `rtl/g1_serial.v` | SCLK-domain shift/bit counter, negedge SDO, idle-timeout frame reset, toggle synchronisers, `rd_hold` |
| `g1_regfile` | `rtl/g1_regfile.v` | register file (map 1.1: `SENSE_OFS`, `OSC_CTRL`, `TEMP_CTRL`, `DAC_*_EFF`, `MODE.FAST_EN`, `STATUS2.TRIPPED_A`), self-clearing command bits, `OSC_CNT` prescaler, L/H hold, read mux |
| `g1_trip_timer` | `rtl/g1_trip_timer.v` | comparator and `tripped` synchronisers, soft up/down accumulator with decay and digital hysteresis, hard N-consecutive-decision filter sampled once per `cmp_clk`, signed sense offset with saturation on both DAC codes, inrush mask, latch/retrigger with hold, retry give-up, `trip_d`/`clr_d` to G1_GATE, adoption of analog fast-path trips, trip count, soft peak |
| `g1_sync2` | `rtl/g1_sync2.v` | two-flop synchroniser |
| `g1_seu`, `g1_seu_chain`, `g1_tmr_reg` | `../g1_seu/rtl/` | SEU monitor, see `../g1_seu/README.md` |

Ports of `g1_digital` (44 signal pins plus `VDD`/`VSS`; register map section 2): `osc_clk por_n
en sclk sdi sdo cmp_clk cmp_soft cmp_hard dac_soft[7:0] dac_hard[7:0]
trip_set_sel trip_d clr_d fast_en tripped trip gate_en fault_n trip_cause[1:0]
osc_en osc_trim[3:0] t2f_en t2f_mode bgr_r4 clk_div_out`. Changes against the
run4 macro (map 1.0): `cmp_clk`, `trip_d`, `clr_d`, `fast_en`, `tripped`,
`osc_en`, `osc_trim`, `t2f_en`, `t2f_mode`, `bgr_r4` are new; nothing was
removed. Reset codes are now `DAC_SOFT` 0x99 / `DAC_HARD` 0xFE, `HARD_N`
counts comparator decisions (200 ns) — register map section 7.

Clock domains: `osc_clk` (everything except the serial shift logic) and
`sclk` (bit counter, input shift register, holding registers, toggles,
falling-edge output register). All crossings are toggle or level
synchronisers; the scheme, its latency and the resulting speed rule
(`f_SCLK` ≤ `f_OSC`) are in register map section 1.3. Reset: `EN` low or
`por_n` low resets everything (there is no reset pin); register defaults make
the chip a latched breaker with no serial traffic (register map section 3).

## Simulated

Icarus Verilog 14.0, `iverilog -g2005 -Wall -Wno-timescale`, inside the pinned
container (image and PDK commit in `../../PLAN.md` section 2). Run from the
repository root:

```
flow/run.sh bash designs/g1-guardian/blocks/g1_ctrl/sim/run_sim.sh
```

`sim/tb_g1_digital.v` drives `g1_digital_top` (256/128 SEU) through the pads
only, at `osc_clk` = 10 MHz and `SCLK` = 5 MHz (10 MHz in T03). The analog
side is modelled as the interface files describe it: the comparators latch
`over_soft` / `over_hard` on the rising / falling `cmp_clk` edge (valid 1 ns
after the edge, held), and the G1_GATE latch is a reset-dominant SR latch,
`set = trip_d | (cmp_hard & fast_en)`, `reset = !en | clr_d`, feeding
`tripped`. Log: `sim/tb_g1_digital.log` — **15 tests, 204 checks, all
passed** (2026-09-19, register map 1.1).

| Test | What it checks | Result |
| --- | --- | --- |
| T01 | reset value of every register in the map (incl. 0x27–0x2B), unmapped addresses read 0, output ports at reset (`osc_en` 1, `osc_trim` 8, `t2f_en` 1, `fast_en` 0), `cmp_clk` is `osc_clk`/2 | passed |
| T02 | write and read back of every RW register, bit masking of narrow registers (`MODE` 6 bits, `OSC_CTRL` 5, `TEMP_CTRL` 3), ports follow (`dac_*`, `trip_set_sel`, `fast_en`, `osc_en`, `osc_trim`, `t2f_*`, `bgr_r4`), RO/WO/unmapped writes ignored | passed |
| T03 | serial at `f_SCLK` = `f_OSC` = 10 MHz; frame aborted after 5 clocks, idle > 128 cycles, next frames correct (idle-timeout resync) | passed |
| T04 | `EN` low: `gate_en` = 0, `trip` = `trip_d` = 0, `osc_en` stays 1, configuration back to reset values after the `EN` cycle | passed |
| T05 | inrush mask after `EN` (hard overcurrent ignored, `INRUSH_ACTIVE` read), hard trip after ~1 ms: latency 9–12 cycles for `HARD_N` = 4, cause = hard, `fault_n`/`gate_en` low, `trip_d` sets the G1_GATE latch, `STATUS2.TRIPPED_A`, latched, `TRIP_CNT` = 1, `CLEAR` clears both latches | passed |
| T06 | `HARD_N` = 10: 9 decisions no trip; 6 + gap + 6 no trip (clear-on-low); 10 decisions trip | passed |
| T07 | `SOFT_TIME` = 512 cycles: 300 high then low no trip, `dac_soft` lowered by 1 LSB while armed and restored, `SOFT_PEAK`; continuous trip at 512–520 cycles; intermittent 400 + 100 low + 250 trips (symmetric decay); decay 1/16 trips sooner | passed |
| T08 | both paths disabled: no trip, G1_GATE latch stays clear (`fast_en` = 0); `FORCE_TRIP`: cause = forced, latch set, `CLEAR` re-trips while forced (latch set again after the clear pulse), clears after release | passed |
| T09 | retrigger: hold 8192 ± 7 cycles (`HOLD_TIME` = 1), re-enable clears the G1_GATE latch, inrush restart (505–535 cycles), give-up after `RETRY_MAX` = 2, `GAVE_UP`/`RETRY_CNT`/`TRIP_CNT` read, cool-down resets `RETRY_CNT` | passed |
| T10 | SEU `INJ_PLAIN` → `SEU_PLAIN` = 1, `SEU_RUN` = 1; `INJ_TMR` → `SEU_CORR` = 1, `SEU_UNC` = 0; `CLR_CNT` | passed |
| T11 | SEU all-ones pattern: chains all ones, no false counts, hierarchical flips in the plain register and TMR copy a → counts 1/1/0 | passed |
| T12 | `OSC_CNT` rate at `/256` and `/1024`, L read latches H across a 0x00FF → 0x0100 boundary, `CLR_OSC_CNT` | passed |
| T13 | `SENSE_OFS` +10 / −20 / −128 / +127 on both codes, saturation at 0 and 255, `DAC_*_EFF` readback, stacking with the 2-LSB hysteresis (0x60 − 2 − 5 = 0x59 armed, 0x5B disarmed) | passed |
| T14 | analog fast path (`FAST_EN`, digital hard path off): one `cmp_hard` decision sets the G1_GATE latch, the core adopts it within 6 cycles with cause hard, `TRIPPED_A`, `TRIP_CNT` = 1; `CLEAR` pulses `clr_d`, both latches clear, no re-trip from the stale synchronised state; retrigger re-enable clears the analog latch; `EN` low clears it | passed |
| T15 | every `clr_d` pulse in the run is 200 ns wide (14 pulses, ≥ 100 ns required by G1_GATE) | passed |

While extending T13 a testbench framing fault was found and fixed: a frame
started exactly 80 `osc_clk` after the previous one, inside the 64–80-cycle
idle-reset window of register map section 1.2, lost its first edge (the RTL
behaved as specified; the rule stands).

The unit testbench for the SEU monitor is described in `../g1_seu/README.md`.
Waveforms (`*.vcd`) are written to `build/g1_digital/` and not committed.

### Gate level

The hardened netlist (`nl/g1_digital.nl.v` of the LibreLane run, gitignored)
is simulated with the PDK's `sg13g2_stdcell.v` functional models (with
`sg13g2_udp.v`, `-DFUNCTIONAL -DUNIT_DELAY=#1`, no SDF) by the same testbench
with `-DGLS` (T11 and T12 poke RTL internals and are skipped). Run from the
repository root after the LibreLane run:

```
flow/run.sh bash designs/g1-guardian/blocks/g1_ctrl/sim/run_gls.sh [netlist] [tag]
```

One log per run, `sim/tb_g1_digital_gls_<tag>.log` (the header records the
netlist sha256 and PDK commit); the same 13 tests (T01–T10, T13–T15: serial
read/write of every register, idle-timeout resync, `EN` reset, hard and soft
trips, retrigger, SEU injection, sense offset, G1_GATE fast path) and 193 checks
ran on each placed-and-routed netlist:

| Netlist | sha256 | Result | Log |
| --- | --- | --- | --- |
| run5 | `1543a722…` | 13 tests, 193 checks, all passed | `sim/tb_g1_digital_gls_run5.log` |
| run6 | `197e5ee3…` | 13 tests, 193 checks, all passed | `sim/tb_g1_digital_gls_run6.log` |
| **run7 (macro of record)** | `fce14375…` (`layout/g1_digital.nl.v`) | **13 tests, 193 checks, all passed** | `sim/tb_g1_digital_gls_run7.log` |
| **chip netlist** (the `g1_digital` cell inside `g1_chip_top_1414.gds`: run7 placement, CTS redone, rerouted) | `6181b988…` | **13 tests, 193 checks, 0 errors** (functional models, unit delay) | `sim/tb_g1_digital_gls_chip6181b988.log` |
| chip netlist, typ SDF annotated (Icarus ignores the SDF timing checks, so not a setup/hold qualification) | `6181b988…` | 13 tests, 193 checks, 0 errors; fast/slow SDF: not run | `sim/tb_g1_digital_gls_chip6181b988_sdf_typ.log` |

Commands and inputs for the chip-netlist runs: `reports/sta_merged_sdc_20260924/README.md`,
section "Chip digital netlist (6181b988)".

## Synthesised

Yosys 0.67 in the container. The standalone scripts and logs in `reports/`
(`synth_generic.ys`, `synth_sg13g2.ys`, `yosys_*_g1_digital.log`) are from the
map-1.0 RTL (3884 cells, 81 279 µm², 1175 flops) and are kept for the SEU area
sweep in `../g1_seu/README.md`. For the map-1.1 RTL the LibreLane synthesis
report is the reference: `reports/librelane_run5/synth_stat.rpt` —
**4046 cells, 84 796 µm²** of cell area, 1200 × `sg13g2_dfrbpq_1`
(58 787 µm²); the 25 flops and 3.5 k µm² added by map 1.1 are the `cmp_clk`
divider, `SENSE_OFS`, `OSC_CTRL`, `TEMP_CTRL`, `FAST_EN`, the `tripped`
synchroniser, the `clr_d` pulse and mask counters and the two saturating adders.

## Laid out (LibreLane)

LibreLane 3.1.0.dev2, Classic flow, OpenROAD 26Q3-850, yosys 0.67, PDK commit
`84374023ee8b4b126bebbba67fcbada0a9c0ff0b`, `sg13g2_stdcell` at 1.2 V.
Base config `flow/config.yaml`, constraints `flow/g1_digital.sdc` (two
asynchronous clocks at 100 ns, setup uncertainty 0.5 ns, hold 0.05 ns, false
paths from the asynchronous inputs incl. `tripped`, 1.5 ns max transition).
The macro of record is built from `flow/config_tmr_spread.yaml` (= `config.yaml`
plus the TMR seeds and the step reorder described below). Run from the
repository root:

```
G1_WORKDIR=designs/g1-guardian/blocks/g1_ctrl/flow flow/run.sh \
  librelane config_tmr_spread.yaml --pdk ihp-sg13g2 --pdk-root /foss/pdks --manual-pdk \
  --run-tag run7 --save-views-to /work/build/g1_digital/final_run7
```

Die 360 × 360 µm (macro budget from the chip floorplan), core 344 × 344 µm,
no PDN core ring (stripe pins on TopMetal1/TopMetal2). Run history:

| Run | Configuration | Outcome |
| --- | --- | --- |
| run1 | relative sizing | failed at configuration: `KLayout.Density` is not a step of this flow, cannot be substituted |
| run2 | relative sizing | failed at synthesis check: 43 `keep_hierarchy` submodule instances reported as unmapped cells → attribute replaced by `(* keep *)` on the flops |
| run3 | relative sizing (die 560 × 579 µm, 1024/256 SEU) | failed at post-CTS hold repair: 2418 endpoints, "max buffer count reached", caused by `set_clock_uncertainty 0.5` applied to hold → uncertainty split setup/hold |
| run4_512 | 512/128 SEU, 360 × 360 µm, `PL_TARGET_DENSITY_PCT` 85 | failed: detailed placement after post-CTS buffering (`DPL-0036`), i.e. does not fit |
| run4 | map 1.0, 256/128 SEU, 360 × 360 µm, density 75, heuristic diode insertion | completed; DRC 0, LVS clean, XOR 0, antenna 0, STA clean; **36 max-slew pins at 1.53 vs 1.5 ns at the slow corner** (`reports/librelane_run4/`) |
| **run5** | map 1.1 RTL, same die, heuristic diode insertion off (antenna repair only where the check fails), design repair with 30 % slew/cap margin, second repair pass after global routing | **completed, 79/79 steps, 8 min 31 s; every check clean, 0 max-slew violations** (`reports/librelane_run5/`) |
| run6 | run5 + TMR copy separation into three vertical thirds (`flow/config_tmr.yaml`, `flow/tmr_columns.py`) | completed, 79/79 steps, 24 min; DRC 0, LVS clean, XOR 0, antenna 0 (61 diodes inserted), setup/hold clean, **81 max-slew violations at the slow corner (1.52–1.93 ns vs 1.5 ns) on 18 TMR vote nets**, wirelength 446 mm (2.6 × run5); separation achieved for 194 of 199 stages, 5 copy-c flops displaced by the legaliser back next to copy b (`reports/librelane_run6/`). Not the macro of record. |
| **run7** | run5 + density-neutral TMR copy spread (`flow/config_tmr_spread.yaml`, `flow/tmr_spread.py`) and the manual placement moved ahead of the post-placement design repair | **completed, 79/79 steps, 9 min 0 s; every check clean (0 max-slew), all 199 TMR stages ≥ 27 µm apart; macro of record** (`reports/librelane_run7/`, views in `layout/`) |

### Max-slew fix (run4 → run5)

The 36 violating pins of run4 were all inputs of cells on nets that had
received heuristic antenna diodes (`ANTENNA__*` instances on the same nets in
`reports/librelane_run4/sta_checks_slow.rpt`): 1496 `sg13g2_antennanp` cells
were inserted after the design-repair step, and their input capacitance pushed
already-marginal nets from ≤ 1.2 ns to 1.53 ns at 1.08 V / 125 °C. The fix is
in the flow, not the constraint: `RUN_HEURISTIC_DIODE_INSERTION: false`
(OpenROAD's `repair_antennas` still runs in the global- and detailed-routing
iterations and inserts diodes only where the antenna check fails — it inserted
**none**, the antenna check is 0/0), `DESIGN_REPAIR_MAX_SLEW_PCT` /
`_CAP_PCT` 30 (repair to 70 % of the limit before routing) and
`RUN_POST_GRT_DESIGN_REPAIR: true` (a second `repair_design` on the
global-routed parasitics, 10 % margin). Result: 0 max-slew, 0 max-cap
violations in all three corners; the 1.5 ns limit is unchanged.

### Results of run5, run6 and run7 (`reports/librelane_run<n>/metrics.json`)

Same RTL, same synthesis result (`synth_stat.rpt` identical: 4046 cells,
84 796 µm²), same die 360 × 360 µm / core 344 × 344 µm (129 600 / 116 920 µm²);
the runs differ only in the placement of the 597 TMR copy flops.

| Quantity | run5 | run6 | **run7 (of record)** |
| --- | --- | --- | --- |
| standard cells (incl. timing-repair / hold buffers) | 4841 (630 / 263) | 4891 (622 / 255) | 4842 (631 / 264) |
| antenna diode cells | 0 | 61 | 2 |
| standard-cell area / utilisation | 95 091 µm² / 81.3 % | 95 296 µm² / 81.5 % | 95 149 µm² / 81.4 % |
| routed wirelength / vias | 171 001 µm / 32 675 | 446 174 µm / 48 756 | 220 970 µm / 36 313 |
| routing DRC (detailed router) | 0 after 6 iterations | 0 after 12 iterations | 0 |
| STA setup, worst slack (typ / fast / slow), 100 ns period | 28.84 / 29.06 / 28.48 ns | 28.85 / 29.06 / 28.48 ns | 28.84 / 29.06 / 28.48 ns |
| STA hold, worst slack (typ / fast / slow) | 0.178 / 0.102 / 0.315 ns | 0.185 / 0.106 / 0.327 ns | 0.185 / 0.106 / 0.326 ns |
| max slew violations (1.5 ns limit; typ / fast / slow) | 0 / 0 / 0 | 0 / 0 / **81** | **0 / 0 / 0** |
| max cap violations | 0 | 0 | 0 |
| max fanout (report only, no checker; limit 10 set by LibreLane) | 79 clock-tree leaf buffers with 16–17 sinks | 81 | 78 (same kind) |
| KLayout DRC (`ihp-sg13g2.drc`, deep, no density) | 0 | 0 | 0 |
| magic DRC | 0 | 0 | 0 |
| netgen LVS (layout vs synthesised netlist) | match uniquely, 4845 devices / 4851 nets | match uniquely, 4895 / 4840 | **match uniquely, 4846 / 4850** |
| KLayout vs magic stream-out XOR | 0 | 0 | 0 |
| antenna (OpenROAD, after detailed routing) | 0 nets / 0 pins | 0 / 0 | 0 / 0 |
| power grid violations / worst IR drop (typ) | 0 / 0.32 mV | 0 / 0.23 mV | 0 / 0.42 mV |
| power, typ, vectorless, `osc_clk` 10 MHz | 0.96 mW | 1.01 mW | 0.97 mW |
| TMR copies: smallest distance between two copies of one stage, over 199 stages (`tmr_separation.txt`) | 3.8 µm (adjacent rows) | 4.0 µm (5 stages < 40 µm, otherwise ≥ 114 µm) | **27.4 µm min, 42.6 µm median** |
| run time | 8 min 31 s | 24 min 25 s | 9 min 0 s |

The max-fanout entries are the CTS leaf buffers (`clkbuf_leaf_*`) driving
16–17 flops each against LibreLane's default `MAX_FANOUT_CONSTRAINT` of 10;
the flow has no checker for it, the clock-tree slews are within the 1.5 ns
limit in all corners, and the numbers are recorded here so the report is
complete.

Outputs (gitignored): `build/g1_digital/final_run<n>/` (GDS, LEF, DEF,
netlists, SDF, SPEF, lib); flow logs `build/g1_digital/librelane/run<n>.log` and
`flow/runs/run<n>/`. Signoff reports are copied by `flow/collect_reports.sh
run<n>` into `reports/librelane_run<n>/`; `tmr_separation.txt` there is the
output of `flow/tmr_check.py` on the final netlist and DEF.

### TMR copy separation (run6, run7)

Purpose: a single particle must not be able to upset two of the three copies
of one TMR stage. Charge sharing in a 130 nm bulk process reaches a few µm, so
the criterion used here is **every stage's three copies ≥ 20 µm apart**, in
both axes where possible (a track along a row or a column must not cross two
copies). In run5 the placer put the three copies of every stage next to each
other (3.8 µm, adjacent rows; `reports/librelane_run5/tmr_separation.txt`), so
the TMR register of run5 would have counted multi-cell upsets as
"uncorrectable". LibreLane 3.1.0.dev2 has no placement-region variable
(checked in the installed package: only `IO_EXCLUDE_PIN_REGION` exists), so
the copies are separated with `MANUAL_GLOBAL_PLACEMENTS` seeds, which
`Odb.ManualGlobalPlacement` applies after global placement and before
legalisation. Copy membership of a flop is read from the net on its Q pin
(`u_core.u_seu.q{a,b,c}[i]` for the 128 chain stages,
`u_core.u_seu.u_<reg>.q{a,b,c}[i]` for the 71 redundant control-register
bits; 597 flops). Instance names are yosys's `_NNNN_`, reproducible for
identical RTL and synthesis settings; regenerate the seeds whenever the RTL or
anything before global placement changes. `flow/tmr_check.py` measures the
result on the final netlist and DEF.

**run6 — three vertical thirds** (`flow/tmr_columns.py`,
`flow/tmr_placements.yaml`, `flow/config_tmr.yaml`): copy a seeded into the
west third of the core, b into the centre, c into the east (199 flops each).
Result (`reports/librelane_run6/tmr_separation.txt`): 194 of 199 stages have
their copies ≥ 114 µm apart, but the legaliser moved five copy-c chain flops
(stages 3–6 and 14) 100–150 µm out of the crowded south-east corner back into
the centre band, 4–33 µm from copy b (one control-register copy-b flop sits
1.3 µm outside its band). Cause: at global placement the SEU register sat in
the west half of the core; moving two thirds of its flops east left the west
at 40–50 % and the east at 100–120 % local density, and `detailed_placement`
(max displacement 168.6 µm) had to push cells out. The second cost was timing:
in the Classic flow `OpenROAD.RepairDesignPostGPL` runs *before*
`Odb.ManualGlobalPlacement`, so the design repair saw the copies still
clustered; after the move every majority-vote net spanned the three bands
(~230 µm, one driver, three flop D pins) and was never buffered. The post-GRT
repair did not catch them either (1001 `EST-0026` "missing route to pin"
warnings, estimates fell back to placement-based values). Signoff STA then
reported **81 max-slew violations at the slow corner** (1.52–1.93 ns against
the 1.5 ns limit, all on 18 vote nets: 18 vote-gate outputs, 54 flop D pins
and 9 antenna-diode inputs), wirelength 2.6 × run5, 61 antenna diodes. DRC, LVS, antenna, setup and
hold were clean and its netlist passed gate-level simulation, but the
max-slew criterion that made run5 replace run4 is failed, so run6 is not the
macro of record.

**run7 — density-neutral spread** (`flow/tmr_spread.py`,
`flow/config_tmr_spread.yaml`): every stage's three flops keep their
global-placement centroid; copy a is seeded 40 µm west and 4 rows (15.12 µm)
south of it, copy b at the centroid, copy c 40 µm east and 4 rows north, so
the copies of one stage are ≥ 42.8 µm apart along a diagonal, the density map
is unchanged to first order, and a vote net spans ~85 µm instead of ~230 µm.
The seeds are generated from the run6 global-placement DEF (global placement
is bit-identical between runs of the same netlist and configuration: checked
for run5 vs run6; any run's `28-openroad-globalplacement/` output serves):

```
python3 flow/tmr_spread.py flow/runs/run6/28-openroad-globalplacement/g1_digital.nl.v \
  flow/runs/run6/28-openroad-globalplacement/g1_digital.def seeds.yaml   # then pasted into config_tmr_spread.yaml
python3 flow/tmr_check.py build/g1_digital/final_run7/nl/g1_digital.nl.v build/g1_digital/final_run7/def/g1_digital.def
``` In addition `meta.substituting_steps` removes
`Odb.ManualGlobalPlacement` from its stock position and re-inserts it *before*
`OpenROAD.RepairDesignPostGPL` (`-OpenROAD.RepairDesignPostGPL:
Odb.ManualGlobalPlacement`), so the design repair buffers the vote nets at
their final length. Result (`reports/librelane_run7/tmr_separation.txt`):
**all 199 stages ≥ 27.4 µm (median 42.6 µm, none below 20 µm)**, the design
repair found the same 7 slew violations as in run5 (no new ones from the
spread), 0 max-slew violations in signoff, wirelength 1.29 × run5, 2 antenna
diodes, 4842 standard cells (run5: 4841). Run7 is the macro of record.

### Macro of record (run7)

Views copied from `build/g1_digital/final_run7/` into `layout/`
(`layout/SHA256SUMS` lists every file):

| File | Content | sha256 |
| --- | --- | --- |
| `layout/g1_digital.lef` | abstract, 360 × 360 µm, 46 pins (44 signal + `VDD`, `VSS`) | `7519083e…` |
| `layout/g1_digital.gds` | layout, 4.5 MB | `065b4504…` |
| `layout/g1_digital.nl.v` | gate-level netlist (the one simulated above) | `fce14375…` |
| `layout/g1_digital.pnl.v` | powered netlist for the chip-level LVS | `d303399d…` |
| `layout/g1_digital.vh` | black box for the chip-level RTL | `ea0d48a7…` |
| `layout/g1_digital.nom.spef` | parasitics, nominal RC corner | `42dbd018…` |
| `layout/lib/g1_digital__nom_{typ_1p20V_25C,fast_1p32V_m40C,slow_1p08V_125C}.lib` | timing models, three corners | see `SHA256SUMS` |
| `layout/g1_digital.sdc` | the constraints as written back by the flow | `7de6a086…` |
| `layout/PINS.md` | every pin with direction, domain, layer, edge, coordinates and destination block (generated by `flow/pins_md.py` from the LEF) | — |
| `layout/g1_digital_top.sdc`, `layout/TOP_SDC.md` | chip-level constraints for the macro (clock on `osc_clk`, asynchronous groups, the signoff uncertainties, false paths, SDI min delay) and why they are needed: with LibreLane's default netlist-based macro timing the chip SDC re-times every internal path (section "Chip-level timing" below) | — |

Pin placement was left to the placer (17 pins on the north edge on Metal2, 24
on the east and 3 on the west edge on Metal3; the run4 macro used by the
padring dry run was also spread over three edges). If the chip floorplan
needs a particular assignment, add `FP_PIN_ORDER_CFG` to `flow/config.yaml`
and repeat run, gate-level simulation and report collection. The GDS carries
the macro's `prBoundary` (189/4, 0–360 × 0–360 µm, plus one per standard
cell); the level-shifter GDS carries its own (`ls/README.md`).

### Chip-level timing (padring dry run D14)

The chip dry run of record (`../g1_padring/reports/dryrun-1350/`) reported
hold −0.094 ns (fast) / −0.015 ns (typ) *inside* `g1_digital` while the macro
signoff has +0.106 / +0.185 ns on the same paths. Cause, established by
re-running the dry run's own STA step with and without the fix
(`reports/top_sta_dryrun1350/`, details in `layout/TOP_SDC.md`): LibreLane
times macros from their netlist and SPEF by default
(`STA_MACRO_PRIORITIZE_NL`), so the chip SDC re-judges every internal path,
and the chip template applies the PDK default 0.25 ns clock uncertainty to
hold where the macro was hardened with 0.05 ns — a difference of exactly
0.200 ns in every corner, nothing else differs. The chip SDC also defined no
`osc_clk`, leaving 1148 of the macro's 1200 flops unconstrained at chip level.
The fix is `layout/g1_digital_top.sdc` (historical: the constraints were merged inline into
`../g1_padring/flow/g1_chip_top.sdc` on 2026-09-24, `reports/sta_merged_sdc_20260924/`): with it
the same STA gives hold +0.106 / +0.185 / +0.326 ns on SCLK and
+0.125 / +0.205 / +0.348 ns on osc_clk, 0 violations, setup ≥ 26.4 ns, in
all three corners. The liberty views in `layout/lib/` are characterised
(`write_timing_model`, three corners) and remain available for a black-box
timing of the macro (`STA_MACRO_PRIORITIZE_NL: false`), which was not run.

STA on the chip's own digital netlist (`6181b988…` with its SPEF `e6c89575…`, merged chip SDC,
nominal RC, OpenSTA 3.1.0; `reports/sta_merged_sdc_20260924/README.md` "Chip digital netlist
(6181b988)"), simulated/static analysis:

| Check (chip netlist 6181b988) | Status |
| --- | --- |
| Setup / hold, merged SDC, fast / typ / slow | passed: worst setup 28.011 / 27.282 / 25.756 ns, worst hold +0.104 / +0.183 / +0.323 ns, 0 violations; 52 SCLK + 1148 osc_clk registers clocked |
| Template SDC only (control) | failed, as expected: hold −0.131 ns (fast), 50 endpoints |
| Max fanout / max cap | passed (0 / 0); the redone CTS removed the run7 view's 78 fanout flags |
| Max slew | failed: 12 per corner on analog-pad pins (placeholder liberty tables; dispositioned, not waived) |
| Full parasitic annotation | failed: 105 unannotated drivers (60 CTS dummy loads, 17 ports, 28 pad pins; dispositioned, not waived) |
| Min/max RC corners; timing of the final filled GDS | not run |

## Checks

Status of the macro of record (run7) unless a run is named; run5 and run6
figures are in the comparison table above.

| Check | Status |
| --- | --- |
| RTL simulation, 15 system tests through the serial interface (map 1.1) | passed (`sim/tb_g1_digital.log`) |
| RTL simulation, SEU unit tests | passed (`../g1_seu/sim/tb_g1_seu.log`) |
| Gate-level simulation of the hardened netlist, 13 tests / 193 checks (T11/T12 skipped) | passed on the run5, run6 and run7 netlists (`sim/tb_g1_digital_gls_run{5,6,7}.log`) |
| Lint (verilator 5.050 in LibreLane) | passed (0 warnings, run5–run7) |
| Synthesis, yosys liberty-mapped; LibreLane synthesis checks (unmapped cells, assign statements) | passed (0 errors; identical result in run5–run7) |
| Placement and routing in 360 × 360 µm | passed (run7: 4842 standard cells, 95 149 µm², 81.4 % utilisation, 0 routing DRC) |
| STA, setup, 3 corners (typ 1.20 V 25 °C, fast 1.32 V −40 °C, slow 1.08 V 125 °C), parasitics | passed: worst setup slack 28.48 ns at slow (period 100 ns), 0 violations (`reports/librelane_run7/sta_summary.rpt`) |
| STA, hold, 3 corners | passed: worst hold slack +0.106 ns at fast, 0 violations |
| Max slew / max cap | **passed: 0 / 0 violations in all three corners** (run4: 36 max-slew, run6: 81 max-slew — both described above) |
| Max fanout | not checked by the flow (no checker); 78 CTS leaf buffers above the default limit of 10, reported above |
| Antenna (OpenROAD check after detailed routing) | passed: 0 violating nets, 0 violating pins (2 diode cells inserted by `repair_antennas`) |
| DRC, KLayout `ihp-sg13g2.drc` (block, deep, no density) | passed: 0 errors (run7; also run5, run6) |
| DRC, magic | passed: 0 errors (run7; also run5, run6) |
| LVS, netgen | passed: circuits match uniquely, 0 differences (run7: 4846 devices, 4850 nets; also run5, run6) |
| XOR (KLayout vs magic stream-out) | passed: 0 differences (run7; also run5, run6) |
| TMR copies physically separated (every stage's three copies ≥ 20 µm apart) | **passed in run7: 199/199 stages, minimum 27.4 µm, median 42.6 µm** (`reports/librelane_run7/tmr_separation.txt`); failed in run5 (3.8 µm, copies adjacent) and incomplete in run6 (194/199 stages, 5 stages 4–33 µm) |
| Density | not applicable at macro level (checked at chip level after fill) |
| Corners / MC / temperature (analog-style) | not applicable (digital standard cells; timing corners above) |
| PEX + post-layout | covered by the LibreLane parasitic extraction and STA above |
| Level shifters 1.2 V → 3.3 V (`t2f_en`, `t2f_mode`, `bgr_r4`): schematic, corners, layout, DRC, LVS | passed (3 instances of `g1_ls_up`; `ls/README.md`); PEX not run |
| Pin list for the ring / integration owner | done: `layout/PINS.md` (46 pins of the run7 macro) |
| `prBoundary` (189/4) in the GDS of record | passed: one macro-level rectangle 0–360 × 0–360 µm (`g1_digital.gds`; checked with KLayout) |
| Chip-level STA of the macro inside the padring dry run (netlist + SPEF, chip SDC) | **failed with the ring template SDC alone: hold −0.094 ns fast / −0.015 ns typ, 48 / 5 endpoints, osc_clk domain unconstrained; passed with `layout/g1_digital_top.sdc` appended: 0 violations in all corners, both domains constrained** (`reports/top_sta_dryrun1350/summary.txt`). Historical: the snippet was merged inline into `../g1_padring/flow/g1_chip_top.sdc` on 2026-09-24; chip-context STA with the merged SDC passed on run7 and on the chip netlist 6181b988 (`reports/sta_merged_sdc_20260924/README.md`) |
| Gate-level simulation of the chip netlist 6181b988, 13 tests / 193 checks | passed: functional (unit delay) and typ-SDF annotated (timing checks not executed by Icarus); fast/slow SDF not run (`sim/tb_g1_digital_gls_chip6181b988*.log`) |
| STA of the chip netlist 6181b988, merged SDC, 3 corners | passed setup/hold, 0 violations; max slew and full annotation failed (dispositioned, see "Chip-level timing") |
| Integration into the chip-level floorplan | done by the ring owner in the D14 dry run (`../g1_padring/reports/dryrun-1350/`): run7 macro at (367, 372), three `g1_ls_up` at (546/566/586, 860), routing 0 DRC, KLayout DRC 0 markers, PDN connected; open items there were the chip SDC above (merged 2026-09-24), density fill and the analog-pad antenna artefacts, none of them in this block |

## Unverified

`SCLK` timing at the pad with the real IO cell delays; the trip timer under
an oscillator at the ±20 % limits (functionally clock-rate independent,
simulated only at 10 MHz); reset behaviour with a real `por_n` source; the
comparator models in the testbench are behavioural (decision latency and
kickback are the G1_TRIP block's evidence); the `tripped` adoption mask (5
cycles) against the real G1_GATE `clr_d` → `tripped` path delay (nanoseconds
by the G1_GATE simulation, so the margin is > 400 ns); gate-level simulation
is functional only (no SDF back-annotation); the 20 µm separation criterion
for the TMR copies is a design margin, not a measured upset cross-section (the
SEU monitor has not been irradiated); the macro pins were not placed against
the chip floorplan (the D14 dry run routed to them as they are); the
chip-level STA with the merged SDC was run by hand with OpenSTA
(`reports/sta_merged_sdc_20260924/`), not by the padring flow itself; anything on silicon.

# G1_SEU

State: **RTL complete, simulated, synthesised; hardened as part of the
`g1_digital` macro (run7, the macro of record), with the three TMR copies of
every stage placed ≥ 27 µm apart; gate-level simulation of the hardened
netlist passed** (see `../g1_ctrl/README.md` for the LibreLane runs). No
silicon, no irradiation.

Single-event-upset monitor: a plain shift register and a triple-modular-
redundant (TMR) shift register clocked by `osc_clk`, continuously scrubbed
against a known pattern, with saturating upset counters read over the serial
interface. Register map and behaviour: `../../specification/G1_REGISTER_MAP.md`
sections 4.4 and 6.

## Source

No existing design was ported; the TMR vote-and-rewrite structure is the
standard one. All RTL in `rtl/` is original (Apache-2.0).

| File | Lines | Content |
| --- | ---: | --- |
| `rtl/g1_seu.v` | 137 | monitor: pattern generator, fill counter, plain and TMR chains, comparison, counters |
| `rtl/g1_seu_chain.v` | 24 | one free-running shift-register copy (`keep` attribute on the flops) |
| `rtl/g1_tmr_reg.v` | 40 | generic triple-redundant register with majority vote (`g1_tmr_copy` × 3) |

## Architecture

- **Plain register**: `SEU_PLAIN_LEN` stages, one `sg13g2_dfrbpq_1` per stage.
- **TMR register**: `SEU_TMR_LEN` stages × 3 copies (`u_tmr_a/b/c`, separate
  instances). At every clock each stage's three outputs are majority-voted and
  the vote is written into all three flops of the next stage; a single upset
  is corrected at the next clock and counted once (`SEU_CORR`); two upset
  copies in one stage propagate to the output and count as uncorrectable
  (`SEU_UNC`).
- **Pattern**: checkerboard (dynamic test, every flop toggles each clock),
  all-0 or all-1 (static-data test, flops clocked but never change). Because
  the patterns have period ≤ 2 and the lengths are even, the expected output
  bit is the bit currently being fed in; no delayed reference is needed.
- **Redundant control**: pattern phase, fill counter and all counters are
  `g1_tmr_reg` instances (three copies, voted, rewritten each clock).
- **Self-test**: `INJ_PLAIN` / `INJ_TMR` invert one input bit for one clock.
- **No clock enable on the chains.** sg13g2 has no enable flop and no
  reset-less flop (checked in `sg13g2_stdcell_typ_1p20V_25C.lib`: the smallest
  flop is `sg13g2_dfrbpq_1`, 48.99 µm²; `sg13g2_dfrbp_1` is 52.62 µm²). An
  earlier version with a per-bit enable (static hold and divided shifting)
  cost one `sg13g2_mux2_1` (18.1 µm²) per stage, 33 k µm² at 1024 + 3 × 256
  stages, and was removed for the area budget below. Static-data testing is
  done with the constant patterns instead.
- **Synthesis attribute**: the copy flops carry `(* keep *)`. Without it yosys
  `opt_merge` collapses identical copies after flattening (measured: 2408 →
  1703 flops); with it all copies survive `synth -flatten`, `opt -full` and
  liberty mapping (`../g1_ctrl/reports/yosys_sg13g2_g1_digital.log`).

## Built configuration and area

The macro budget from the chip floorplan is at most 360 × 360 µm at a
utilisation the router accepts (60–70 %), i.e. about 80–85 k µm² of cells for
the whole digital core. Liberty-mapped yosys synthesis of `g1_digital` (yosys
0.67, `sg13g2_stdcell_typ_1p20V_25C.lib`, scripts in `reports/`):

| plain / TMR stages | flops | cells | cell area (µm²) | utilisation in 344 × 344 µm core | log |
| ---: | ---: | ---: | ---: | ---: | --- |
| 1024 / 256 (specification) | 2327 | 5863 | 144 660 | 122 % — does not fit | `reports/sweep_1024_256.log` |
| 512 / 256 | 1815 | 5295 | 118 987 | 101 % — does not fit | `reports/sweep_512_256.log` |
| 512 / 128 | 1431 | — | 94 008 | 79 % — LibreLane detailed placement failed after post-CTS buffering (`../g1_ctrl/README.md`) | `reports/sweep_512_128.log` |
| **256 / 128 (built)** | 1175 | 3884 | 81 279 | 69 % | `../g1_ctrl/reports/yosys_sg13g2_g1_digital.log` |

The 1024-bit registers of the specification were cut in the order asked for
by the chip floorplan (plain first, then TMR): the built G1 has a **256-bit
plain register and a 128-bit × 3 TMR register**. The RTL keeps the lengths as
parameters (`SEU_PLAIN_LEN`, `SEU_TMR_LEN` on `g1_digital`); the 1024/256
configuration is what the unit testbench simulates, so it stays verified. The
SEU block alone at 1024/256 is 4119 cells, 116 153 µm² of cells
(`reports/yosys_sg13g2_g1_seu_1024_256.log`), 2005 of them flops.

Consequence, stated plainly: with 256 + 3 × 128 = 640 monitored flops the
block yields useful statistics only under a heavy-ion beam. In low Earth orbit
or under protons it will record near zero and is to be reported as **not
exercised**, not as "no upsets".

## Simulated

Icarus Verilog 14.0 (`iverilog -g2005 -Wall -Wno-timescale`), inside the
pinned container. Run from the repository root:

```
flow/run.sh bash designs/g1-guardian/blocks/g1_ctrl/sim/run_sim.sh
```

Unit testbench `sim/tb_g1_seu.v` on the **1024 / 256** configuration, log
`sim/tb_g1_seu.log` (11 tests, 43 checks, all passed):

| Test | What it checks | Result |
| --- | --- | --- |
| S01 | fill of 1024 shifts, then active; checkerboard in the chain, copies agree, no false counts over 3000 clocks | passed |
| S02 | one bit flipped in the plain register (hierarchical assignment to the flop) counts exactly once, `SEU_RUN` = 1 | passed |
| S03 | one bit flipped in TMR copy b: disagreement visible for one clock, corrected at the next shift, `SEU_CORR` = 1, `SEU_UNC` = 0 | passed |
| S04 | same stage flipped in copies a and c: `SEU_CORR` +1 and `SEU_UNC` +1 | passed |
| S05 | five adjacent plain flips: count 5, longest run 5 | passed |
| S06 | register-driven `INJ_PLAIN` / `INJ_TMR` pulses: one count each | passed |
| S07 | pattern change restarts the fill; all-ones and all-zeros patterns; no false counts at the change | passed |
| S08 | constant pattern: a flop holds its value over 50 clocks while clocked; flips are still counted | passed |
| S09 | 300 flips at the output stage count 300; `SEU_RUN` saturates at 255 | passed |
| S10 | `SEU_UNC` saturates at 255 | passed |
| S11 | `SCRUB_EN` = 0: registers keep shifting, nothing counts; re-enable refills, then active | passed |

S07 found a real RTL fault before the fix: in the clock of a pattern change,
the comparison used the new pattern bit against the old register contents and
produced two false counts; `cmp_en` is now gated with `~restart`.

The **256 / 128** configuration as built is exercised through the serial
interface in `../g1_ctrl/sim/tb_g1_digital.v` tests T10 (injection bits,
`CLR_CNT`) and T11 (all-ones pattern, hierarchical flips in the plain register
and one TMR copy, counters), log `../g1_ctrl/sim/tb_g1_digital.log`.

## Laid out

As part of the `g1_digital` macro (LibreLane Classic), documented in
`../g1_ctrl/README.md` ("TMR copy separation"). The copies are identified in
the flat netlist by the nets on their Q pins (`u_core.u_seu.q{a,b,c}[i]`,
`u_core.u_seu.u_<reg>.q{a,b,c}[i]`); LibreLane has no placement regions, so
the separation is done with per-flop global-placement seeds:

| Run | Method | Smallest distance between two copies of one stage (199 stages: 128 chain + 71 control bits) | Signoff |
| --- | --- | --- | --- |
| run5 | none | 3.8 µm (the placer stacks the three copies in adjacent rows) | clean |
| run6 | each copy in its own vertical third of the core | 4.0 µm: 194 stages ≥ 114 µm, 5 stages 4–33 µm (legaliser displaced five copy-c flops) | 81 max-slew violations on the ~230 µm vote nets |
| **run7** | each stage's copies spread ±40 µm / ±4 rows around their own centroid (`../g1_ctrl/flow/tmr_spread.py`) | **27.4 µm minimum, 42.6 µm median, no stage below 20 µm** | clean |

Evidence: `../g1_ctrl/reports/librelane_run{5,6,7}/tmr_separation.txt`
(output of `../g1_ctrl/flow/tmr_check.py` on the final netlist and DEF). The
criterion, ≥ 20 µm in every stage, is an order of magnitude above the
charge-collection radius of a single ion in a 130 nm bulk process; it is a
design margin, not a measured cross-section. Voters, the pattern generator and
the clock tree are not triplicated in place and are not covered by it.

## Checks

| Check | Status |
| --- | --- |
| RTL simulation, unit (1024/256), 11 tests | passed (`sim/tb_g1_seu.log`) |
| RTL simulation, in system (256/128), T10–T11 | passed (`../g1_ctrl/sim/tb_g1_digital.log`) |
| Lint (verilator, in LibreLane) | passed, 0 warnings after the `shreg` fix |
| Synthesis, yosys 0.67 liberty-mapped | passed (redundant flops preserved: 1175 = 256 + 384 chain flops + 3 × 71 redundant control bits + 322 control flops) |
| Area within macro budget (256/128) | passed, 81.3 k µm² of cells |
| Area within macro budget (512/128) | **failed** (LibreLane detailed placement, `../g1_ctrl/README.md`) |
| Area within macro budget (1024/256 specification) | **failed**, 144.7 k µm² of cells |
| Gate-level simulation of the hardened netlist (T10 injection self-test in system; T11 pokes RTL internals and is skipped at gate level) | passed on the run5, run6 and run7 netlists (`../g1_ctrl/sim/tb_g1_digital_gls_run{5,6,7}.log`) |
| TMR copies of every stage ≥ 20 µm apart in the placed macro | **passed (run7: 199/199 stages, min 27.4 µm)**; failed in run5 (3.8 µm), incomplete in run6 (194/199) |
| DRC / LVS (macro) | see `../g1_ctrl/README.md` |
| Corners / MC / temperature (analog-style) | not applicable (standard-cell digital; timing corners in the LibreLane STA) |
| PEX + post-layout | see LibreLane parasitic STA in `../g1_ctrl/README.md` |
| Irradiation | not run |

## Unverified

SEU cross-section of `sg13g2_dfrbpq_1`; whether a real upset in a voter or in
the pattern generator is masked as designed; whether 27 µm is enough
separation against grazing-angle heavy ions (no irradiation, no TCAD);
behaviour under the ±20 % oscillator (functionally clock-rate independent, not
simulated at other rates); gate-level simulation is functional only (no SDF).

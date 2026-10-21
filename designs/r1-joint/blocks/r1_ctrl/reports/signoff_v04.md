# r1_ctrl revision 0.4 sign-off verification (track T5, 2026-10-21)

Question: do the five open checks of revision 0.4 pass? They are true setup slack, max-fanout, gate-level
simulation, formal equivalence and clock-domain crossings.

Subject: RTL tree of revision 0.4 (sha256 `6ca24fce...6eb0`) and the hardening run `r1ctrl_ll_20261021_t7`.
No RTL, register-map or constraint file was changed. Nothing is committed.

Note. The working tree of `rtl/`, `tb/tb_top.v`, `flow/r1_ctrl.sdc` and `README.md` changed during this work
(by other work on a later revision, for example `rtl/r1_tapidx.v`; not by me). My results apply to the t7 files:
the RTL copy in the t7 run (sha256 above), the t7 netlist, SDF and SPEF, and the `tb/tb_top.v` that `versions.txt` of each
gate-level run records by sha256. They do not apply to the current tree.

Status at the time of writing. The typ-corner SDF run of `biss` at 23.810 ns (run `r1ctrl_gl_20261021_i`) was still running
with 42 of 48 checks passed and 0 failed. Its final result is in `<G1_RESULTS_ROOT>/r1_ctrl/r1ctrl_gl_20261021_i/typ/top_biss_23.810.log` and `.rc`.

Built against: container `tapeoutbench-eda:latest` (sha256 `ddeb69576f28`, checked by `flow/run.sh`), PDK commit
`84374023ee8b4b126bebbba67fcbada0a9c0ff0b`, OpenSTA 3.1.0 (`sta`), Icarus Verilog 14.0 (devel, s20260301), Yosys 0.67, eqy.
All runs used `flow/run.sh` with `G1_CPUSET=112-115`, `G1_WORKDIR=designs/r1-joint/blocks/r1_ctrl`,
`G1_RESULTS_ROOT=<G1_RESULTS_ROOT>`. Scripts are in `sim/signoff/`. Small result files are in `sim/signoff/results/`.
Bulk logs are in `<G1_RESULTS_ROOT>/r1_ctrl/<run-id>/`.

## Summary

| # | Check | Result | Run id |
| --- | --- | --- | --- |
| 1 | True setup slack | **passed**: worst slow setup slack +1.776 ns; no path below +0.3 ns. The "0.000" of the t7 report is latch time borrowing, not clipping | `r1ctrl_20261021_t7sta` |
| 2 | Max-fanout | 6 nets, **not closed**, no RTL change needed: limit is 8 (library), not 16; 4 clock-tree nets and 2 data nets | `r1ctrl_20261021_t7sta` |
| 3 | Gate-level simulation | **partly passed**. Slow SDF: 21 of 22 `gate` checks (1 failed: EN to GATE_C within 1 ns, STA delay 1.47 ns, spec 1 µs); ssi, spi, safe, cal, and `biss` at 23.810 ns (47 passed, 0 failed, 1 skipped) passed. Typ SDF: ssi, spi, gate, safe, cal passed; `biss` at 23.810 ns: **not completed** (stopped at the time limit): 42 passed, 0 failed so far, 0 skipped. SDF `biss` at 33.333 / 47.619 ns not run (time); zero-delay `biss` at both passed | `r1ctrl_gl_20261021_b`, `_f`, `_g` |
| 4 | Formal equivalence | **inconclusive, not passed**: see section 4 | `r1ctrl_equiv_20261021_b` |
| 5 | CDC | **no tool run** (RTL inspection only). 10 crossings have a 2-flip-flop synchroniser. 6 crossings or reset paths have none (A to F). Four rely on host timing rules. One timing limit (D, SSI) and one glitch-prone reset (F) are open findings | - |

## 1. True setup slack

Method. The t7 sign-off report lists setup slack 0.000 ns at the three corners. I ran OpenSTA again on the t7
post-layout netlist (`final/nl`), the SDC (`final/sdc`) and the SPEF (`final/spef/nom`) with the PDK liberty files
for each corner (`sim/signoff/sta_true.tcl`, `sta_borrow.tcl`). The result is identical to the t7 sign-off
summary (setup 0.0000, hold 0.0209 / 0.0748 / 0.1834), so the re-run is the same data.

Finding. The 0.000 is not a clipped number. The worst endpoints are the 120 level-sensitive latch D pins
(68 negative-level, 52 positive-level). OpenSTA reports slack 0.000 on a latch D pin whenever the data
arrives after the latch opens: the path "borrows" time and the margin moves to the next stage. The real margins are
below. Latch borrow at the slowest corner is at most 1.02 ns of 11.47 ns allowed (120 latches).

Worst setup slack per corner at 42 MHz, `set_clock_uncertainty -setup 0.5` included. Slack in ns, signed.

| Corner | Worst flip-flop D / output / input endpoint | Worst recovery check | Worst latch borrow (used / allowed) |
| --- | --- | --- | --- |
| nom_typ_1p20V_25C | **+9.725**: `_26009_` (`meas_angle[2]`, `u_pos`) to `_25968_` (`u_pos.cx[15]`) | +9.570: `_26406_` (`rs1`) to `_26647_` (`u_biss.n1`) | 0.836 / 11.63 |
| nom_fast_1p32V_m40C | **+11.247**: `_26647_` (`u_biss.n1`) to `_26649_` (`u_biss.n2`); first input path +13.867 (`adc_valid_b` to `_26636_`, `u_gate.conv`) | +10.235: same pair as typ | 0.723 / 11.75 |
| nom_slow_1p08V_125C | **+1.776**: `_26009_` (`meas_angle[2]`) to `_25968_` (`u_pos.cx[15]`); next +1.977 (`u_pos.cx[14]`), +2.024 (`u_pos.cx[11]`) | +8.543: `_26406_` to `_26647_` | 1.020 / 11.47 |

Slow corner path. It starts at the angle register `meas_angle[2]`, goes through the CORDIC / position datapath
(about 50 cells, 21.4 ns of logic) and ends at the CORDIC x accumulator `u_pos.cx[15]`. Arrival 22.963 ns,
required 24.739 ns. The worst slow slack is above +0.3 ns, so no path is named for the +0.3 ns rule. Output ports
(`fault_n`, `thr_oc_a[4]`) have +13.2 ns or more. MA-domain flip-flop paths have +47 ns or more and `slo_sdo` has +25.5 ns.

Worst hold slack (ns, signed).

| Corner | Slack | Path |
| --- | --- | --- |
| nom_typ_1p20V_25C | +0.0748 | `_27233_` (`u_pos.zero_ofs[5]`, clocked by gated clock `u_regs.u_16.gclk`) to `_26416_` (`pos_out[7]`, clock `clk_regs`) |
| nom_fast_1p32V_m40C | **+0.0209** | same pair. Data 0.844 ns, required 0.823 ns. The launch clock arrives 0.60 ns, the capture clock 0.78 ns (0.18 ns skew in favour of the capture flop) |
| nom_slow_1p08V_125C | +0.1834 | `adc_valid_b` (input, min delay 0.5 ns) through hold buffer `hold1798` to `_25897_` (`u_gate.u_wb.acc[0]`); register to register worst +0.1880 (same pair as fast) |

The hold uncertainty in the SDC is 0.05 ns. No on-chip variation derate is applied. The fast margin is 21 ps.

## 2. Max-fanout violations

Six nets violate at every corner (same list in `final/metrics`, `checks.rpt`). I read the limit and the loads
with `sim/signoff/sta_fanout.tcl`.

Limit. The effective limit is **8**, not 16. The SDC has `set_max_fanout 16` for the design. The liberty files set
`default_max_fanout : 8` and OpenSTA applies 8. The earlier statement "limit 16" in the README is wrong. At a limit of 16 the count would be 0 (the largest fanout is 16).

| # | Net (driver pin) | Fanout | Limit | Class | Loads |
| --- | --- | --- | --- | --- | --- |
| 1 | `clknet_0_clk_regs` (`clkbuf_0_clk_regs/X`) | 16 | 8 | clock (CTS root of the `clk_regs` tree) | 16 `buf_2` |
| 2 | `clknet_0_ma_sclk` (`clkbuf_0_ma_sclk/X`) | 16 | 8 | clock (CTS root of the MA / SCLK tree) | 16 `buf_2` |
| 3 | `clknet_0_u_gate.g_sh` (`clkbuf_0_u_gate.g_sh/X`) | 16 | 8 | clock (CTS root of the gated shadow clock) | 16 `buf_2` |
| 4 | `clknet_0_clk` (`clkbuf_0_clk/X`) | 11 | 8 | clock (CTS root of `clk`) | 8 `buf_2`, 3 antenna diodes |
| 5 | `net1342` (`fanout1342/X`, a resizer buffer on `reg_wdata[11]`) | 14 | 8 | data (SPI write-data bit 11) | 3 flip-flop D, 2 `a22oi`, 2 `inv`, 1 buffer, 6 antenna diodes |
| 6 | `net436` (`fanout436/X` on decode net `_11472_`) | 13 | 8 | data (register read-mux select) | 7 `a22oi`, 1 buffer, 5 antenna diodes |

None of the six is a reset or a clock-enable net. Four are clock-tree nets. Two are data nets.

Estimate (not run). Nets 5 and 6 would be at 8 loads without the antenna diodes that the antenna repair added to them
after the fanout buffering. One extra `buf_1` on each net (7 + 7 loads) closes them. Cost about 20 µm². Slack
effect is negligible (slow setup +1.78 ns, borrow margin above 10 ns). Nets 1 to 4 are CTS tree branches: a buffer
tree does not close them without changing the clock tree. Two options exist. Waive them (maximum slew on the clock
nets is 0.47 ns against 1.5 ns, no slew or capacitance violation). Or change the CTS branching and the diode placement. This needs a new hardening run, which is not part of this check.

## 3. Gate-level simulation

Flow. The SDF flow works in this container with Icarus Verilog 14.0, after three fixes (failures 3 to 5 below).

- Netlist: t7 post-layout `final/nl/r1_ctrl_top.nl.v` (flattened, no power pins), with the PDK cell models
  `sg13g2_stdcell.v` and `sg13g2_udp.v`.
- SDF: `final/sdf/nom_slow_1p08V_125C` (maximum of each min:typ:max triple) and `final/sdf/nom_typ_1p20V_25C` (typical),
  annotated with `$sdf_annotate`. Cell IOPATH delays are applied. INTERCONNECT entries (wire delays, 0 to a few tens of ps)
  are dropped because the reader crashes on them. `TIMINGCHECK` entries are ignored by Icarus: **setup and hold are not
  checked by this simulation** (STA does that). Evidence that delays are active: the spi run ends 36 ns later than at
  zero delay (880 270 500 ps against 880 234 500 ps) and the `gate` check below fails at slow only.
- Testbench: `tb/tb_top.v` is not edited. `sim/signoff/mk_gl_tb.sh` makes a gate-level copy. It adds the SDF call and
  replaces the hierarchical probes that do not exist in the flattened netlist. Differences from the RTL run:
  1. `biss item8: 14 x CDM = 0 returns the control channel to idle`: **skipped** (the state register is recoded). It is
     counted as skipped, not as passed.
  2. `spi: status byte in every frame`: compares 6 of 8 status bits (`clk_fault` and `overspeed` do not exist as nets).
  3. `safe: power-on reset latches POR and CAL`: checks `FAULT_N` low and `cause[11]` (CAL) only. `cause[12]` (POR) is not a net.
  4. `safe` I2t cooling wait: a fixed wait of 2400 ticks replaces polling `e_a` (not a net). The check afterwards is unchanged.
- Tests as in `sim/run_all.sh`: `biss` and `ssi` at 23.810, 33.333, 47.619 ns; `spi`, `gate`, `safe`, `cal` at 33.333 ns; `cal` at 23.810 ns.
  The 42 MHz period (23.810 ns) is the sign-off clock.
- Wall time with SDF is about 7 times the zero-delay time. One `biss` run at 23.810 ns takes more than 1 h.

Results (pass / fail / skipped; expected checks in brackets). Logs: `sim/signoff/results/<run-id>/`.

| Group | Clock ns | Slow SDF (max) | Typ SDF | Zero delay |
| --- | --- | --- | --- | --- |
| `biss` (48) | 23.810 | 47 passed, 0 failed, 1 skipped | **not completed** (stopped at the time limit): 42 passed, 0 failed so far, 0 skipped | 47 / 0 / 1 passed (run `_b`) |
| `biss` (48) | 33.333 | not run (time) | not run (time) | 47 / 0 / 1 passed (run `_h`) |
| `biss` (48) | 47.619 | not run (time) | not run (time) | 47 / 0 / 1 passed (run `_h`) |
| `ssi` (9) | 23.810 / 33.333 / 47.619 | 9 / 9 / 9 passed | 9 / 9 / 9 passed | passed (run `_b`) |
| `spi` (26) | 33.333 | 26 passed | 26 passed | passed |
| `gate` (22) | 33.333 | **21 passed, 1 failed** | 22 passed | 22 passed |
| `safe` (32) | 33.333 | 32 passed | 32 passed | 32 passed |
| `cal` (2 x 32) | 33.333 / 23.810 | 32 / 32 passed | 32 / 32 passed | passed |

The one failure. `gate: EN low forces GATE_C low within 1 ns (combinational)` fails at slow (t = 2335.166 ns). The
check is an assertion of the zero-delay RTL. STA gives the real delay from `en_pad` to `gate_a/b/c`: typ 0.90 ns, fast 0.58 ns,
slow **1.47 ns** (input buffer, two `and2`, output buffer; `sim/signoff/results/r1ctrl_20261021_t7sta/en_to_gate.txt`).
The specification row for the fault path is 1 µs, so the design meets it. The check as written still fails at slow; I did
not change it. The README note "the real delay is a pad/STA item" now has the number.

Zero-delay runs (`_b`): the first runs did not apply the SDF (failure 3). They are zero-delay gate-level runs, labelled so.
They pass all groups except the two `biss` clocks that I stopped and reran as run `_h`.

Not run: SDF `biss` at 33.333 and 47.619 ns (time), SDF at the fast corner, post-layout simulation with wire (INTERCONNECT)
delays, setup/hold violation checks in the simulator, gate-level simulation of `r1_pos` accuracy cases (the 16 position
cases and the 274 calibration cases run on RTL only).


## 4. Formal equivalence, RTL against post-synthesis netlist

Result: **inconclusive. Equivalence is not established.** It is not "not run: tool absent": Yosys 0.67 with the
`equiv_*` passes and eqy are present in the container.

What was run.
1. eqy, strategy `sby` (`r1ctrl_eqy_20261021_a`): failed. The first partitions returned "equivalence unknown" and the
   SMT engine gave no status. Failed run, kept.
2. eqy, strategy `sat` (`_b`): stopped by eqy ("partition contains memory"). Added `memory_map`.
3. eqy, strategy `sat` (`_c`): 305 of 1843 names matched. The gate netlist uses scalar names (`u_pos.cx[15]`), the RTL
   uses buses. The first partition did not prove (1 min each, 331 partitions). Stopped by me.
4. eqy with `splitnets` on the RTL (`_d`): 1836 names matched. At about 1 min per partition the run needed more than 5 h. Stopped by me.
5. Direct Yosys `equiv_make`, `equiv_simple`, `equiv_induct` (`r1ctrl_equiv_20261021_b`, script `sim/signoff/equiv.ys.in`).
   RTL: `prep`, flatten, `memory_map`, `techmap`. Netlist: step `06-yosys-synthesis` with the liberty cell functions. Both
   after `async2sync`.

Result of step 5. `equiv_make` matched 1835 signal pairs by name. The netlist has 3730 flip-flops and 120 latches,
so about half of the state elements have no name partner. `equiv_simple` proved 797 of 1882 compare points. 1085
stayed unproven, spread over all modules (`u_regs` 223, `u_pos` 215, `u_gate` 188, `u_biss` 126, `u_safe` 114,
`u_cal` 62, `u_spi` 43, and 16 outputs). `equiv_induct` did not converge (5.5 M clauses, step 1 failed) and I stopped it.
The unproven points include cones that read an unmatched register. Yosys also recoded five state machines
(`om`, `u_biss.cst`, `u_biss.mst`, `u_safe.i2t_ph`, `u_spi.ph`; `yosys-synthesis.log` lines 4122-4130), so those
registers have no partner by construction. The unproven count is therefore not evidence of a difference. It is also not evidence of equivalence.

What would close it (not run): match the state registers with a name map (or disable FSM recoding in a
second synthesis run for comparison), prove the combinational cones with `equiv_simple`, then run `equiv_induct` with the
matched registers as invariants. This needs a few hours of work.

Supporting evidence (not a proof): the zero-delay gate-level simulation of section 3 passes all comparable checks
on the t7 post-layout netlist.

## 5. Clock-domain crossings

No CDC tool was run. The list below comes from reading the RTL (`rtl/*.v`) and the SDC. The SDC puts `clk` and `ma`
(MA / SCLK pad) in asynchronous clock groups, so STA does not check any crossing between them. Domains:

| Domain | Source | Flip-flops |
| --- | --- | --- |
| `clk` | `r1_osc`, 42 MHz at sign-off (gated copies `u_regs.*.gclk`, `u_gate.g_sh`, `clk_regs`) | all core logic, same domain, STA checked |
| `ma` | MA / SCLK pad, 10 MHz limit | BiSS: `fall_seen`, `rdy_n1` (falling edge), `mst`, `bidx`, `crc`, `slo_q`, `rdy_p2`, `prev_b`, `ma_tog`, `lat_tog`; SPI: `fresh`, `rx`, `rcnt`, `oidx` (falling edge); top: `pc`, `p16_tog` |
| async inputs | `por_n`, `cs_n`, `en_pad`, `cmp[3:0]`, `t2f_clk` | - |
| clk-synchronous inputs | `adc_valid_a/b`, `adc_raw_a/b` (SDC input delay 7 ns / 0.5 ns) | constrained, no synchroniser, assumed same clock as `r1_adc` |

Crossings with a synchroniser (`r1_sync2`: two flip-flops, asynchronous reset, depth 2).

| # | Signal | From to | Synchroniser | Depth |
| --- | --- | --- | --- | --- |
| 1 | `ma` level | `ma` to `clk` | `u_sma` in `r1_biss` | 2 |
| 2 | `ma_tog` | `ma` to `clk` | `u_smt` in `r1_biss` | 2 |
| 3 | `lat_tog` | `ma` to `clk` | `u_slt` in `r1_biss`; and `n1` (falling `clk`) to `n2` to `n3` (half-tick timing) | 2; 3 (first stage resolves in half a period) |
| 4 | `p16_tog` | `ma` to `clk` | `u_sp16` in `r1_ctrl_top` | 2 |
| 5 | `cs_n` | pad to `clk` | `u_scs` in `r1_biss` and `u_scs` in `r1_spi` | 2 each |
| 6 | `rdy_tog` | `clk` to `ma` | `rdy_n1` (falling edge of `ma`) to `rdy_p2` (rising edge) | 2 (first stage has half a period) |
| 7 | `por_n` | pad to `clk` | `rs0`, `rs1` in `r1_ctrl_top` (assert asynchronous, release synchronous) | 2 |
| 8 | `en_pad` | pad to `clk` | `u_sen` in `r1_safe` | 2 |
| 9 | `cmp[3:0]` | analog to `clk` | `u_scmp` in `r1_safe` (4 bits, one flag each) | 2 |
| 10 | `t2f_clk` | analog to `clk` | `u_st2f` in `r1_safe` | 2 |

Crossings **without** a synchroniser. These are findings, not proven faults.

| # | Crossing | What the RTL does | Risk |
| --- | --- | --- | --- |
| A | SPI `rx[23:0]`, `rcnt[5:0]` (`ma`) to `clk` (`reg_addr`, `reg_wdata`, decode) | The `clk` side reads the 30 flip-flops directly after `cs_s` (2 flip-flops) goes high and the decode phase. They are stable only while CS_N is high | Needs CS_N high time of at least 8 `clk` ticks (190 ns at 42 MHz, 270 ns at 30 MHz). The host must keep it. No hardware check |
| B | `tx_word[23:0]` (`clk`) to the `sdo` mux (`oidx`, `ma`) | Written by `clk` after CS_N rises. Read by SCLK after CS_N falls | Stable by protocol only |
| C | BiSS `fd[35:0]`, `cds_frame`, `nbits`, `off`, `st_n`, `ssi_mode`, `gray` (`clk`) to the `ma` shift logic | BiSS: `fd` is written in the same tick as `rdy_tog`, and `ma` reads it only after `rdy_p2` shows the toggle. Safe. Configuration bits change only when the host writes them. No interlock | Host rule: no register write during a frame |
| D | SSI: `fd` is updated every tick while `ma_s` is high and `frame_act` is low | `ma_s` falls up to 2 ticks after the MA fall. `ma` reads `fd[MSB]` at the first MA rising edge | `fd` is stable at that edge only if half an MA period is longer than about 3 `clk` ticks. At 42 MHz this is 71 ns (MA below about 7 MHz). At 21 MHz it is 143 ns (MA below about 3.5 MHz). The testbench SSI frames use a 1 µs MA period. Estimate from the RTL, not simulated |
| E | `rst_n` release (`clk` flip-flop `rs1`) to the asynchronous reset of `ma` flip-flops (`pc`, `p16_tog`, `ma_tog`, `lat_tog`, `rx`, `rcnt`) | Release is not aligned to `ma`. STA does not check the recovery in the async group | Needs MA quiet at power-up |
| F | `ma_rst_n = rst_n & cs_n & armed & ~to_rst[1]` and `cs_n` on the asynchronous set / reset of `fresh`, `oidx` | A combinational AND of `clk` flip-flops and a pad drives the reset of the `ma` flip-flops. It can glitch when `armed` falls and `to_rst[1]` falls in the same tick. CS_N rise releases `fresh` and `oidx` asynchronously to SCLK | Reset released for a few ps. Low probability. Add a registered reset in a later revision |

Not a crossing, by design. `en_pad` also gates `gate_a/b/c` with a combinational AND. A low `en_pad` forces the gates low
at once (this is the safe direction and is tested). `adc_*` inputs: the same clock as `r1_adc` is assumed (see
`r1_adc` README). If `r1_adc` runs from a different buffer of the `r1_osc` output, a skew budget applies.

## Failures and mistakes

| # | What happened | Class | Effect / fix |
| --- | --- | --- | --- |
| 1 | The t7 report and README called the setup WS 0.000 "clipped" and "true slack unknown" | verification-gap | The 0.000 is latch time borrowing. A custom STA run gave the real slack in 10 minutes |
| 2 | README states the max-fanout limit is 16. The effective limit is 8 (liberty default). The SDC value 16 is not the binding one | spec-ambiguity | Corrected in this report and in the README row |
| 3 | First gate-level runs (`_b`) did not annotate the SDF. Icarus omits specify blocks unless `-gspecify -ginterconnect` is given, and the `GLNOTE` print said "annotated" anyway | tooling | The `_b` runs are labelled zero-delay. The note text is kept as a known false message |
| 4 | SDF path was longer than the 128-byte string register in the testbench copy | tooling | Register widened to 2048 bits |
| 5 | The Icarus SDF reader crashed on INTERCONNECT entries and could not find escaped instance names (246 clock buffers). It also rejected the header and the min:typ:max triples | tooling | `sim/signoff/prep_sdf.py` renames 246 instances, drops 39 838 INTERCONNECT entries, collapses triples. Cell delays are unchanged. Wire delays (a few ps) are not applied. Runs `_c`, `_d`, `_e` failed and are kept |
| 6 | A status bit-width error in the testbench copy put `osc_done` on the wrong bit. I stopped run `_a` by `podman stop` of my own container | regression | Fixed, rerun as `_b` |
| 7 | I killed the biss 33.333 / 47.619 jobs of run `_b` to save time. They ran much faster than my estimate (zero delay: 16 min for biss at 23.81 ns) | estimation | Reran later at zero delay |
| 8 | I estimated the SDF run time from the zero-delay speed. SDF runs are 7 times slower. Biss at 23.81 ns took 6264 s (1.7 h) at slow | estimation | Scope reduced: SDF `biss` only at 23.81 ns (see section 3) |
| 9 | The eqy flow was tried before checking name matching. Four eqy runs gave no result | planning | Direct `equiv_*` flow used. Still inconclusive |
| 10 | Internal probes of the testbench (`dut.status`, `u_safe.cause[12]`, `e_a`, `u_biss.cst`) do not exist in the flattened netlist | verification-gap | One check skipped (GLSKIP), one reduced, one wait replaced. Listed in section 3 |
| 11 | Editing `run_gl.sh` while runs started from it were active | process-hygiene | No effect seen. Do not edit running scripts |

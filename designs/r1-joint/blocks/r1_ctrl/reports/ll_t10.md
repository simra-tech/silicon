# r1_ctrl 0.6 hardening, runs t9f (reused), t10, t11, t12 (2026-10-26)

Box 532 x 679 um (INTERFACES.md, "ctrl macro box and pin template"), east tap/cmp pin pitch 1.68 um, pin order of `flow/librelane/pins_v06.md`, RTL 0.5
(concatenated `rtl/*.v` sha256 `10ba8006ee6215f70278f603a5db080cba43e576b765381c5436b2a454a2352d`, unchanged). All numbers are LibreLane, OpenSTA or Icarus results; nothing is measured.
`<G1_RESULTS_ROOT>` is the bulk results root; run directories are `<G1_RESULTS_ROOT>/r1_ctrl/<run-id>/`. Tools: LibreLane 3.1.0.dev2 (Classic), container
tapeoutbench-eda:latest sha256:ddeb69576f28, PDK commit `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`, OpenSTA (`sta`) and Icarus Verilog 14.0 from the same container.
Command: `flow/run.sh sh flow/librelane/run_harden.sh <run-id> 10800` (`G1_CPUSET=112-115`, `G1_WORKDIR=designs/r1-joint/blocks/r1_ctrl`).

## Runs

| Run id | Config difference | Result |
| --- | --- | --- |
| `r1ctrl_ll_20261021_t9f` | reused from the earlier session: 532 x 679, stride-2 east pins, `MAX_FANOUT_CONSTRAINT` 8, SDC limit 8, CTS balance levels and 60 um buffer distance (via `R1_CFG_APPEND`) | flow complete, exit 0, 2 h 11 min; DRC, LVS, antenna, routing 0; **1 max-fanout violation** (net `_00002_`, see below) |
| `r1ctrl_ll_20261026_t10` | `config.yaml` of 0.6 (same values, in the file instead of the append), `MAX_FANOUT_CONSTRAINT` 7 | exit 0; netlist and LEF **bit-identical** to t9f (GDS differs in the stream date only; SDF differs in its DATE line only). `MAX_FANOUT_CONSTRAINT` does not change this flow; same 1 violation |
| `r1ctrl_ll_20261026_t11` | adds `r1_ctrl_pnr.sdc` (`set_max_fanout 7`) as `PNR_SDC_FILE`; sign-off SDC keeps 8 | exit 0; fanout 0 at limit 8; **4 max-slew violations at slow** (1.52 ns against 1.50 ns, one net, -0.02 ns); utilisation 75.46 % |
| `r1ctrl_ll_20261026_t12` | t11 and `DESIGN_REPAIR_MAX_SLEW_PCT` 40 (was 30) | exit 0, 1 h 31 min; **all checks clean** (below). Run of record |

Reuse record: t9f inputs (RTL copy, SDC, pin table `pins_v06_532x679_s2.cfg`, DIE_AREA, CORE_AREA, CTS keys) equal the 0.6 inputs; its DEF matches the pin table (127 of 127, 0 mismatches). t9f is kept as evidence for the fanout finding and the t10 reproducibility result; the sign-off of record is t12. Runs t9, t9a to t9e were not reused (other box or pitch or not finished; t9e has no `run.json`: stopped when the earlier session ended).

## Fanout finding (t9f = t10)

The violator is `_00002_` (driver `_14543_/Y`): 8 logic loads (seven `sg13g2_mux2_1` select pins and one `sg13g2_dfrbpq_1` D pin) plus the antenna diode `ANTENNA_3` that the antenna repair adds after the fanout repair. 9 loads against the limit of 8, at all three corners. The clock-tree roots are clean (CTS balance levels and 60 um buffer distance). Fix (t11): the place-and-route SDC carries `set_max_fanout 7`; the sign-off SDC keeps 8. This is a repair margin, not a waiver. In t11 the final netlist has two nets with 8 loads (`net1843`, `net1900`, a diode among them) and in t12 one (`net1845`): the sign-off count at limit 8 is 0 in both, at limit 7 it is 2 and 1.

## Result of record: t12

| Item | Value |
| --- | --- |
| Box, core | DIE_AREA 0 0 532 679 (361 228 um^2); core 333 666 um^2 after row snapping |
| Placed standard cells | 251 815 um^2 (18 162 cells), **75.47 %** of the core (target was 75 %; the box was not exceeded). Timing-repair buffers 16 956 um^2, clock buffers 5 933 um^2, fill 81 851 um^2 |
| Max-fanout (limit 8, sign-off SDC), typ / fast / slow | 0 / 0 / 0 (own OpenSTA run and flow metric) |
| Max-slew / max-cap, typ / fast / slow | 0 / 0 / 0 each |
| Detailed routing DRC | 0 (iteration list ends 2, 1, 0) |
| Magic DRC / KLayout DRC | 0 / 0 |
| LVS (netgen) | 0 differences, 0 errors |
| Antenna | 0 violating nets, 0 pins (8 diodes on nets, 10 antenna cells) |
| Pins | 127 of 127 at the table coordinates, 0 mismatches (`check_pins_v06.py`) |

True setup slack (OpenSTA, post-layout netlist and SPEF of t12, sign-off SDC, `sim/signoff/sta_all.sh`). The flow summary shows 0.000 because the worst path group is latch time borrowing; the table gives the slack of each endpoint class.

| Corner | Worst flip-flop D | Worst output port | Worst hold | Worst latch D |
| --- | --- | --- | --- | --- |
| typ 1.20 V 25 C | +9.562 ns (`_27127_` to `_27435_`) | +15.140 ns (`fault_n`) | +0.0927 ns (`_28021_` to `_27132_`) | borrow only (0.000 slack), next +9.353 ns |
| fast 1.32 V -40 C | +10.230 ns (`_27127_` to `_27435_`) | +16.241 ns (`fault_n`) | +0.0556 ns (`_28021_` to `_27132_`) | borrow only, next +10.095 ns |
| slow 1.08 V 125 C | **+3.680 ns** (`_26759_` to `_26684_`) | +13.212 ns (`fault_n`) | +0.1101 ns (`adc_valid_a` to `_26537_`) | borrow only, next +8.164 ns |

Evidence: `<G1_RESULTS_ROOT>/r1_ctrl/r1ctrl_20261026_t12sta/` (`sta_true_*.rpt`, `fanout_*.rpt`). Void first attempt: `r1ctrl_20261026_t10sta_void_t7netlist` (the corner script read the t7 netlist because `LLRUN` was not passed into the container; see README failures).
For t11: `r1ctrl_20261026_t11sta` (SDC limit 7, not the sign-off view) and `r1ctrl_20261026_t11sta_so` (sign-off SDC, shows the slow-corner slew pins `_18167_/B_N`, `_20725_/A`, `_20728_/A`, `_18166_/Y`).

## Gate-level simulation with SDF (slow corner, MAXIMUM, post-layout netlist)

Run `r1ctrl_gl_20261026_t12c` (record), `flow/run.sh env LLRUN=r1ctrl_ll_20261026_t12 GL_JOBS= sh sim/signoff/run_gl.sh r1ctrl_gl_20261026_t12c slow 4`. SDF `nom_slow_1p08V_125C`, mode MAXIMUM, Icarus Verilog 14.0 with `-gspecify -ginterconnect`; testbench `tb/tb_top.v` through `mk_gl_tb.sh` and `mk_gl_tb_v05.py` (ADC inputs delayed by the SDC minimum input delay 0.5 ns). Per group:

| Group | Clock periods (ns) | Checks | Failed | Skipped |
| --- | --- | --- | --- | --- |
| `tap` (0.5) | 33.333 | 5 | 0 | 0 |
| `ana` (0.5) | 33.333 | 9 | 0 | 0 |
| `ssi` | 23.810, 33.333, 47.619 | 3 x 9 | 0 | 0 |
| `spi` | 33.333 | 27 | 0 | 0 |
| `gate` | 33.333 | 22 | 0 | 0 |
| `safe` | 33.333 | 32 | 0 | 0 |
| `biss` | 23.810, 33.333, 47.619 | 3 x 47 | 0 | 1 each (control-channel state register recoded by synthesis) |
| `disc`, `cdc`, `cal` | - | - | - | **not run** (probes `adc_arm`, `u_gate.nra/nrb`, `frame_pos` force, `thr_*`/`cal_*` are not nets of the flattened netlist) |

Total 263 checks, 0 failed. Earlier runs on the record: `r1ctrl_gl_20261026_t9f` (t9f = t10 netlist, no input delay in the testbench): same groups, 0 failed. `r1ctrl_gl_20261026_t12` (no input delay): **failed** 1 `gate`, 1 `safe` and 2 `biss` checks per clock (6 for `biss`, 8 in total). Cause found with an edge monitor (`mon_gate.log` in the run directory): `is_smp` stayed high after the first frame because `adc_valid_*` changed at the clock edge while the capturing flop's clock arrives 1.57 ns later at slow (hold check of the stimulus; the SDC assumes at least 0.5 ns, STA hold +0.110 ns with it). This is a testbench stimulus error, not a design error; see the README failure 8 and open issue 7. `r1ctrl_gl_20261026_t12b`: compile error (tooling), kept.
Typ and fast corner SDF runs: **not run** (the request was slow).

## Deliverables

`<G1_RESULTS_ROOT>/r1_ctrl/r1ctrl_06_release/` with `SHA256SUMS`: `r1_ctrl_top.gds`, `.lef`, `.def`, `.nl.v` (gate-level netlist), three SDF files (typ, fast, slow), the place-and-route and sign-off SDC, the pin table (`pins_v06.md`, `.json`, `.cfg`). The release of t10 (`r1ctrl_06_release_t10`) is kept as the superseded interim.

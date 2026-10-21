# LibreLane runs `r1ctrl_ll_20261021_t9` family (r1_ctrl 0.6): not closed

Command (repository root; `designs/r1-joint/blocks/r1_ctrl` as `G1_WORKDIR`, CPU set 112-115, results root `<G1_RESULTS_ROOT>`):

```
flow/run.sh sh flow/librelane/run_harden.sh <run-id> 10800
```

LibreLane 3.1.0.dev2, Classic flow, PDK commit `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`, container tapeoutbench-eda:latest sha256:ddeb69576f28.
RTL: concatenated `rtl/*.v` sha256 `10ba8006ee6215f70278f603a5db080cba43e576b765381c5436b2a454a2352d` (RTL 0.5, equal to the simulation run `r1ctrl_20261021_v05c`).
Config: `flow/librelane/config.yaml` of revision 0.6 (`MAX_FANOUT_CONSTRAINT: 8`, SDC `set_max_fanout 8`, `IO_PIN_ORDER_CFG` = the template of the run).

| Run | Box (um) | East pin pitch (um) | CTS | Result |
| --- | --- | --- | --- | --- |
| t9 | 520 x 664 | 0.84 | cluster 30 / 120, `buf_2` | **failed**: timeout 10 800 s (exit 124) in detailed routing; 69 violations constant for 4 iterations |
| t9a, t9b | 520 x 664 | 0.84 | cluster 60 / 200, 45 / 160 | stopped by PID after CTS (buffer count 530 / 529, no change); first launch of these ids was void (variables not passed into the container) |
| t9c | 520 x 664 | 0.84 | `CTS_BALANCE_LEVELS`, distance 60 | stopped by PID after CTS; typ fanout violators 4 -> 1 |
| t9d | 532 x 679 | 0.84 | as t9c | stopped by PID at 68 violations (constant) |
| t9e | 520 x 664 | 1.68 | as t9c | running at the time of writing (213 violations) |
| t9f | 532 x 679 | 1.68 | as t9c | running at the time of writing (133 violations) |

Metrics at step 41 (after global-route repair; typ corner values of step 44, estimated parasitics):

| Run | Core (um^2) | Placed (um^2) | Utilisation | Clock buffers (um^2) | Repair buffers (um^2) | Typ hold WS (ns) | Typ fanout violators | Slew / cap violators (typ) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| t9 | 318 286 | 247 076 | 0.7763 | 4 799 | 13 552 | +0.001 | 4 | 0 / 0 |
| t9c | 318 286 | 246 573 | 0.7747 | 5 089 | 12 824 | +0.030 | 1 | 0 / 0 |
| t9d | 333 666 | 247 473 | 0.7417 | 5 334 | 13 418 | +0.107 | 0 | 0 / 0 |
| t9e | 318 286 | 246 513 | 0.7745 | 5 126 | 12 712 | +0.025 | 1 | 0 / 0 |
| t9f | 333 666 | 247 056 | 0.7404 | 5 380 | 12 973 | +0.119 | 0 | 0 / 0 |

Synthesis cell area (LibreLane, ABC with fanout 8): 228 322 um^2 (Yosys flat 228 526). Sign-off STA, DRC, LVS, antenna, final fanout, slew and cap: **not run** (no finished layout).
The fast and slow corner values of step 44 (setup -14 / -45 ns, 485 fanout violators) are the same in every run and in t7 at the same step; they are not results.

Gate-level, zero delay, post-synthesis netlist of t9 (`<G1_RESULTS_ROOT>/r1_ctrl/r1ctrl_gl_20261021_syn_zd/`, 33.333 ns): `tap` 5/5, `ana` 9/9, `spi` 27/27, `gate` 22/22, `safe` 32/32, `ssi` 9/9 passed.
This is not the requested SDF run at slow on the post-layout netlist: **not run**.

To finish when t9e or t9f converges: `python3 flow/librelane/ll_report.py <run dir> <run id> reports/ll_<id>.md`; `check_pins_v06.py <final def> flow/librelane/pins_v06_s2.json`;
`LLRUN=<id> sim/signoff/sta_all.sh`, `sta_fanout.sh` (with `FANOUT_TCL=sim/signoff/sta_fanout06.tcl`), `run_gl.sh <id> slow` with `mk_gl_tb_v05.py` in the chain.

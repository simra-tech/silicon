# g1_digital pin-compatible re-hardening: feasibility dry run (2026-09-25)

Question: can `g1_digital` be re-hardened from RTL so that the new macro drops into the
1414 µm chip (`g1_padring/layout/g1_chip_top_1414_r2.gds`, `9049e87b…`) in place of cell
`__rz_port_text_000_retained_g1_digital`, with the top-level routing untouched?
This is a dry run. No tracked file was changed and nothing was adopted. All numbers are
**simulated** (STA) or come from rule-deck checks. No silicon.

**Recommendation: GO for the real run**, with two chip-level items to close first (GatPoly
density margin, chip LVS references; see "Obstacles"). The macro flow is reproducible from
tracked files. It gives identical pins, the chip-compatible clock tree and clean macro
sign-off on both the current RTL and the ECO RTL snapshot. The swap script reproduces the
chip exactly when it is given the chip's own macro.

## Built against

| Item | Value | How established |
|---|---|---|
| PDK | IHP-Open-PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` | `flow/run.sh` COMMIT check |
| Container | `tapeoutbench-eda:latest` = `sha256:ddeb6957…` | `flow/run.sh` identity check |
| LibreLane | 3.1.0.dev2 | `librelane --version` |
| OpenROAD | 26Q1-1024-gdcf36133a (`/foss/tools/openroad-librelane`) | the build run7 and the chip macro used (SPEF headers). `run_trial.sh` sets `_LLN_OVERRIDE_OPENROAD`, because the PATH build 26Q3-850 fails `set_layer_rc` (`review/audits/DIGITAL_CTS_FANOUT_20260923.md`) |
| KLayout / OpenSTA | 0.30.9 / 3.1.0 | container |
| CPUs | 88-95: two flows ran in parallel, 4 CPUs each, `DRT_THREADS=4` | `taskset` via `G1_CPUSET` |

## What was added (all new, under `flow/eco/`)

| File | Purpose |
|---|---|
| `make_config.py` | Derives the config from `../config_tmr_spread.yaml` (run7). Changes: RTL dir; `FP_DEF_TEMPLATE` = `g1_digital_pins_run7.def` in strict mode (pins are copied, not re-placed); `CTS_SINK_CLUSTERING_SIZE: 8`; step `G1.SplitClockRoot` after `OpenROAD.CTS`; `RT_MAX_LAYER: Metal5`; TMR seeds (`run7`, `none` or a `tmr_spread.py` output) |
| `make_pin_template.py`, `g1_digital_pins_run7.def` | Pin-only DEF: the 44 signal pins of run7 final DEF (`a92abf31…`). Its PINS section is identical to the chip macro's DB `digital-final-dbrename` (`fc52dc71…`) |
| `librelane_plugin_g1eco/` | LibreLane plugin with step `G1.SplitClockRoot`. It is the chip macro's out-of-flow root split (`run_digital_cts_fanout.py --cluster 8 --split-root`), now in-flow: 2 × `sg13g2_buf_16`, 8 root branches each, the chip's final instance names, DPL legalisation |
| `run_trial.sh`, `sta_trial.sh`, `summarize_trial.py`, `clock_fanout.py` | Runs the flow in the container. Merged-SDC STA via the unchanged `reports/sta_merged_sdc_20260924/run_sta.sh`. Metrics and step times. Clock-buffer fanout (limit 8 = liberty `default_max_fanout`) |
| `extract_macro_pins.py`, `compare_macro_pins.py` | Pin shapes (x/2), labels (x/25) and TopMetal1/2 drawing of a macro cell in a GDS. Compare: pins identical, and the candidate's TopMetal inside the reference's |
| `swap_macro.py` | KLayout swap (see "Swap") |
| `config_standin.yaml`, `config_eco_pass{1,2}.yaml`, `seeds_eco_trial.yaml` | Generated configs and seeds of this trial (pass 1 was run before `RT_MAX_LAYER` was added; see note 3) |

Commands, from the repository root. `BULK` is the bulk root. Results are in
`${BULK}/digital-eco-feasibility-20260925/`.

```
E=designs/g1-guardian/blocks/g1_ctrl/flow/eco
python3 $E/make_config.py --rtl ../../rtl_eco_20260925 --seeds none --out $E/config_eco_pass1.yaml
BULK=$BULK G1_CPUSET=92-95 G1_CPUS=4 $E/run_trial.sh config_eco_pass1.yaml eco_pass1 -T OpenROAD.GlobalPlacement
python3 designs/g1-guardian/blocks/g1_ctrl/flow/tmr_spread.py <run>/28-openroad-globalplacement/g1_digital.{nl.v,def} $E/seeds_eco_trial.yaml
python3 $E/make_config.py --rtl ../../rtl_eco_20260925 --seeds seeds_eco_trial.yaml --out $E/config_eco_pass2.yaml
BULK=$BULK G1_CPUSET=92-95 G1_CPUS=4 $E/run_trial.sh config_eco_pass2.yaml eco_m5 -c DRT_THREADS=4 --save-views-to $BULK/digital-eco-feasibility-20260925/final_eco_m5
BULK=$BULK $E/sta_trial.sh $BULK/digital-eco-feasibility-20260925/final_eco_m5 eco_m5 95
flow/run.sh python3 $E/swap_macro.py --chip designs/g1-guardian/blocks/g1_padring/layout/g1_chip_top_1414_r2.gds \
  --cell __rz_port_text_000_retained_g1_digital --macro <final>/gds/g1_digital.gds --netlist <final>/nl/g1_digital.nl.v \
  --def <final>/def/g1_digital.def --out <chip.gds> --report <report.json>
```

RTL: `rtl/` (the run7 RTL; seeds of run7 reused) was the stand-in. `rtl_eco_20260925/` appeared during
the task, so it was run too. The snapshot hashes (`g1_digital_top.v` `c52918f7…`, `g1_regfile.v`
`605d7385…`, `g1_trip_timer.v` `5cab0bc3…`, the rest identical to `rtl/`) were recorded at launch
and were unchanged at the end. The ECO keeps the port list (`g1_digital.v` identical).

## (1)-(2) Pin interface of the chip macro and where it came from

The chip cell has 64 pin shapes: 17 Metal2 (north edge), 27 Metal3 (east/west), and
TopMetal1/TopMetal2 VDD/VSS stripe pins. There are 41 labels. Bounding box 360 × 360 µm,
instance at (367, 364) µm, R0. The pins are identical to `layout/g1_digital.gds` (run7) and to
the chip macro GDS `1a662082`. The chip has 7 labels fewer: `clk_div_out fault_n gate_en trip
trip_cause[1:0] trip_set_sel`. The chip leaves these pins unconnected, and the port-text
normalisation removed their labels. **There is no pin-order file.** run7 had no
`FP_PIN_ORDER_CFG`, and its pins came from OpenROAD's automatic `place_pins`, which depends on
the placement. A re-run with new RTL would therefore move them. The run7 DEF PINS section,
used as `FP_DEF_TEMPLATE`, is the reconstructed constraint.

## (3) Flow results (macro level, LibreLane in-flow checks)

| Run | RTL | Variant | Wall | Setup WS typ/fast/slow (ns) | Hold WS typ/fast/slow (ns) | Slew/cap/fanout viol. | Clock-buffer max fanout | Route DRC / antenna | Magic / KLayout DRC | LVS (netgen) | XOR |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `standin` | run7 | template + cluster 8, no split, TM routing allowed | 20 min | 28.81 / 29.04 / 28.43 | 0.194 / 0.111 / 0.341 | 0 / 0 / 1 | **16 (root) - failed** | 0 / 0 | 0 / 0 | clean | 0 |
| `eco_pass2` | ECO | same | 20 min | 28.83 / 29.05 / 28.46 | 0.185 / 0.106 / 0.325 | 0 / 0 / 1 | **16 (root) - failed** | 0 / 0 | 0 / 0 | clean | 0 |
| `standin_m5` | run7 | + split, `RT_MAX_LAYER` Metal5 | 29 min¹ | 28.78 / 29.02 / 28.38 | 0.189 / 0.108 / 0.334 | 0 / 0 / 0 | **8 - passed** | 0 / 0 | 0 / 0 | clean | 0 |
| **`eco_m5`** | **ECO** | **same (candidate)** | **19 min** | **28.83 / 29.05 / 28.47** | **0.185 / 0.106 / 0.326** | **0 / 0 / 0** | **8 - passed** | **0 / 0** | **0 / 0** | **clean** | **0** |

¹ It shared the CPUs with the chip DRC. Detailed routing took 886 s instead of 539 s.

`eco_m5` in detail: 7894 instances, cell utilisation 85.6 % (run7 81.4 %), wirelength 240 mm.
The synthesised cell area is 86 402 µm² (run7 84 796 µm²). There are 1167 `osc_clk` registers
(+19) and 52 `sclk` registers. 209 clock-buffer nets all have ≤ 8 loads. TMR separation
(`flow/tmr_check.py`): all 199 stages have their copies ≥ 20 µm apart (minimum 23.0 µm, median
42.2 µm; run7 27.4 / 42.6 µm). Step wall times: synthesis 6 s, floorplan to global placement
13 s, placement repair 12 s, CTS + split 14 s, post-CTS repair 9 s, **routing 572 s**, fill/RCX/STA/IR 19 s,
**stream-out + Magic/KLayout DRC 467 s**, LVS 6 s. ECO pass 1 (to global placement) took 30 s.

Merged-SDC STA (`run_sta.sh` unchanged, nominal SPEF), `eco_m5`: macro setup/hold
28.83 / 0.185, 29.05 / 0.106, 28.47 / 0.326 ns (typ/fast/slow). chip_merged setup/hold
27.26 / 0.185, 27.99 / 0.106, 25.72 / 0.326 ns. 0 setup and 0 hold violations. There are no
macro-internal DRV violators. The chip cases carry the same 12 analog-pad slew flags as the chip
of record (`runs_chip6181b988`), which are unrelated to the macro.

## (4) Pin comparison and swap

`compare_macro_pins.py` against the chip cell, for all four runs: bounding box equal, **all 64 pin
shapes identical** (0 only-in-chip, 0 only-in-new). Labels differ only by the 7 unconnected-pin
labels listed above.
TopMetal: in `standin`/`eco_pass2` the router put 18 signal wires on TopMetal1, and 2 of them
cross the chip's own full-height TopMetal1 stripes. Those stripes run over the macro at macro
x = 64.4-70.4, 140-146, 215.6-221.6 and 291.2-297.2 µm, so this would be a short. The chip's
TopMetal1/TopMetal2 fill also sits between the macro's TopMetal shapes (28.7k / 31.4k µm²
inside the macro outline). `RT_MAX_LAYER: Metal5` fixes this. In `*_m5` the TopMetal1/2
drawing is the PDN only, a strict subset of the chip macro's: **swap-compatible**.

`swap_macro.py` does the following:
- empties the target cell and deletes its private sub-cells, but keeps the cell, its name and
  its instance;
- copies the new macro in;
- repeats the chip's port-text normalisation: it removes the 7 unconnected-pin labels and, as
  the chip did for its 29 `sg13g2_inv_{2,4,8}` CTS dummy loads, the output labels of floating
  dummy loads, using per-instance clones;
- checks the result. It XORs the pin layers (top level of the cell), checks that the new
  TopMetal lies inside the old, and XORs the whole rest of the chip on all layers with the
  target cell excluded.

| Check | Control: chip's own macro `1a662082` swapped in | `eco_m5` swapped in |
|---|---|---|
| Pin-layer XOR, 7 layers | 0 | 0 |
| TopMetal outside old | 0 / 0 | 0 / 0 |
| Rest of chip, all layers | unchanged | unchanged |
| Whole-cell XOR, all layers | **0**. Deep Metal1 labels 31 928 = 31 928; 29 clones, as in the chip | differs inside (expected). 0 clones: its 22 dummy loads are `buf_8`/`inv_1`, which the chip did not need to clone |
| Output | `control_swap_self.gds` | `swap_eco_m5.gds` `4ad1041c…` |

Chip checks on `swap_eco_m5.gds`, stock decks, same options as the r2 sign-off:

| Check | Result |
|---|---|
| Main DRC | **passed**: 0 markers, 341 s |
| Antenna | **passed**: 0, 142 s |
| Density | **failed**: `GFil.g` GatPoly global density 14.998 % against a 15.00 % minimum, 30 µm² short |
| Maximal DRC | **passed**: 0 errors, 774 s with 4 threads. A first attempt with 8 threads crashed (KLayout SIGSEGV after 263 s); its log is kept in `chipdrc/drc_maximal_attempt1_sigsegv_8threads/` |
| Precheck | not run |
| LVS (projected and canonical) | **not run**: the references contain the old `g1_digital` and must be regenerated |

## Can the swap leave top-level routing untouched?

Yes. Inside the macro outline, the chip has only its Metal2/Metal3 pin stubs (0.105-0.2 µm into
the edge, on the pin shapes), its TopMetal1 stripes, the TopMetal fill, and FEOL/Metal1 fill in
the 8 µm ring outside the core rows. It has nothing else on Metal1-Metal5. The macro LEF
obstructions are Metal1-Metal5 plus GatPoly (plus TopMetal1 signal rectangles in run7), and
in the `eco_m5` LEF they are Metal1-Metal5 plus GatPoly only (no TopMetal1 rectangles under the Metal5 cap). A
macro with different internal routing drops in as long as the pins are identical and the
TopMetal content lies inside the old one. Both hold for `eco_m5`, and the main DRC and antenna
checks of the swapped chip pass. The chip assembly is native GDS, so the LEF is not used by any
top-level router.

## Obstacles

1. **GatPoly density margin (blocking).** The chip of record is at 15.02 %. The ECO macro has
   460 µm² less GatPoly (21 877 against 22 337 µm²), because more logic leaves fewer decap cells.
   Fixes: re-run the chip's native poly fill (`review/audits/add_native_poly_fill.py`), which
   changes top-level fill but not routing; or recover GatPoly inside the macro, e.g. with a
   lower `PL_TARGET_DENSITY_PCT` or decap-first filling. Either needs a density re-run.
2. **Chip LVS references.** The canonical CDL `g1_digital` subckt comes from pnl via
   `flow/lvs/assemble_chip_cdl.py` (`verilog_to_subckt`), and the projected flat reference must
   be rebuilt too. The port-text normalisation of floating CTS dummy loads is empirical (the chip
   cloned `inv_2/4/8` only). Chip LVS decides which labels must go. `normalize_rz_port_text.py`
   is tied to its input hashes, so `swap_macro.py` re-implements that step.
3. The TMR seeds depend on the synthesised instance names. Every RTL change needs pass 1 (to
   global placement), then `tmr_spread.py`, then pass 2. Here pass 1 ran before
   `RT_MAX_LAYER: Metal5` was added. The seeds are still valid: separation was achieved (23 µm
   minimum). The real run should regenerate them with the final config.
4. The custom CTS and post-CTS scripts behind the chip macro (`review/audits/run_digital_cts_fanout.py`,
   `run_digital_postcts.py`, rename scripts) are tracked, but they are pinned to run7 hashes, so
   they cannot be re-used. They are replaced in-flow by `CTS_SINK_CLUSTERING_SIZE` 8 plus
   `G1.SplitClockRoot`. The chip's clock-instance renames (`_cell` suffix) are built in.
   Hold fixing needed nothing special: the standard LibreLane post-CTS/post-GRT repair gave
   ≥ 0.106 ns hold slack.
5. Not run here: GLS and equivalence of the ECO netlist, and PEX/IR of the swapped chip.

## Estimated time for the real run (ECO RTL frozen)

Macro: pass 1 1 min, seeds 1 min, pass 2 ~20 min (4 CPUs), STA 6 min, pins and swap 3 min.
Chip DRC suite in parallel ~15 min. Compute: about **45 min wall**. The GatPoly fix, the
regeneration of the CDL and projected references, chip LVS, and GLS on the new netlist add
about **3-4 h** of engineering. Total: about half a day.

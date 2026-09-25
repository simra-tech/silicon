# g1_digital run7: STA with the merged chip SDC (2026-09-24)

All numbers are **simulated** (static timing analysis). No silicon.

## Scope: what this closure covers

The physical chip of record is **not** the LibreLane `g1_chip_top` assembly: it is the
native, hand-assembled 1414 × 1414 µm GDS (`../../../g1_padring/layout/g1_chip_top_1414.gds`)
which keeps the **same run7 `g1_digital` macro unchanged**. So the timing closure
we can claim is:

1. macro-level STA of the run7 netlist and nominal SPEF (the macro signoff, repeated here), and
2. the macro expanded inside the routed chip-level signal netlist with its extracted
   pad-to-macro wiring (`final_signal.nl.v` 337db3b1… + `final_signal.nom.spef` ceb5651e…,
   57 routed nets, the documented estimate in
   `../../../../review/audits/FINAL_ROUTED_TIMING_20260923.md`), timed with the chip SDC.

That routed signal netlist and SPEF come from the routed signal DB. They are **not**
an extraction of the final filled 1414 µm GDS with moved bond pads, fill, supply routing or
native terminal metal. Full-chip timing of the final GDS is **not run**.

## What was run

`sta.tcl` (this directory), one run per case and corner, through `run_sta.sh`:

```
# repository root; results root must exist
designs/g1-guardian/blocks/g1_ctrl/reports/sta_merged_sdc_20260924/run_sta.sh <case> <fast|typ|slow> <cpu> <results_root>
#   = G1_CPUSET=<cpu> G1_CPUS=1 G1_CONTAINER_ENGINE=podman G1_RESULTS_ROOT=<root> flow/run.sh \
#       env CASE=<case> CORNER=<corner> OUT=<root>/<case>-<corner> TEMPLATE_SDC=... sta -no_splash -exit .../sta.tcl
```

| Case | Top | Netlist / parasitics | SDC |
| --- | --- | --- | --- |
| `macro` | `g1_digital` | `layout/g1_digital.nl.v` (fce14375…) + `layout/g1_digital.nom.spef` (42dbd018…) | `flow/g1_digital.sdc` (macro signoff) |
| `chip_template` | `g1_chip_top` | routed top netlist + SPEF above; macro netlist and SPEF read under `i_core.u_digital` (`read_spef -name CURRENT -path`, `-keep_capacitive_coupling`); TRIP/OSC declaration stubs from the 2026-09-23 evidence | `g1_chip_top_template_only.sdc` = the ring template without the macro section (byte-identical to the template part of the committed file at HEAD) |
| `chip_merged` | `g1_chip_top` | same | `../../../g1_padring/flow/g1_chip_top.sdc` as changed today (template + g1_digital constraints inline) |

Libraries: PDK `sg13g2_stdcell_{fast_1p32V_m40C,typ_1p20V_25C,slow_1p08V_125C}.lib`;
chip cases add `ip/sg13g2_io_padbare/lib/sg13g2_io_{fast_1p32V_3p6V_m40C,typ_1p2V_3p3V_25C,slow_1p08V_3p0V_125C}.lib`.
Only the nominal RC SPEF exists for the macro and the routed top, so every corner
uses nominal parasitics. Chip env values (period 100 ns, IO delay 20 %,
uncertainty 0.25 ns, transition 0.15 ns, derate 5 %, 6 pF load) are those of the
assembly flow, as in `FINAL_ROUTED_TIMING_20260923.md`.

## Built against

| Item | Version | Established by |
| --- | --- | --- |
| PDK | IHP SG13G2 `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` | `/foss/pdks/ihp-sg13g2/COMMIT`, checked by `flow/run.sh` |
| OpenSTA | 3.1.0 (`/foss/tools/bin/sta`, sha256 49ddbd40…) | `sta -version` in the container |
| OpenROAD | 26Q3-850-gc74892e7b (not used for these runs) | `openroad -version` |
| Container | `tapeoutbench-eda:latest` = sha256:ddeb6957… | `flow/run.sh` identity check |

Inputs and outputs are hashed in `SHA256SUMS`; per-run reports are in `runs/<case>-<corner>/`
(`summary.tsv`, worst setup/hold path, violator lists, annotation, `check_setup`).

## Results

Worst slack in ns; violations = endpoints with negative slack.

| Case | Corner | Worst setup | Worst hold | Hold viol. | Setup viol. | Registers SCLK / osc_clk | Unconstrained endpoints | Unannotated drivers (partial) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| macro | fast | 29.056 | +0.106 | 0 | 0 | 52 / 1148 | 3 | 56 (0) |
| macro | typ | 28.843 | +0.185 | 0 | 0 | 52 / 1148 | 3 | 56 (0) |
| macro | slow | 28.484 | +0.326 | 0 | 0 | 52 / 1148 | 3 | 56 (0) |
| chip_template | fast | 28.256 | **−0.137** | **50** | 0 | 52 / not defined | **1163** | 101 (0) |
| chip_template | typ | 27.528 | **−0.070** | **6** | 0 | 52 / not defined | **1163** | 101 (0) |
| chip_template | slow | 26.001 | +0.065 | 0 | 0 | 52 / not defined | **1163** | 101 (0) |
| chip_merged | fast | 28.006 | +0.106 | 0 | 0 | 52 / 1148 | 19 | 101 (0) |
| chip_merged | typ | 27.277 | +0.185 | 0 | 0 | 52 / 1148 | 19 | 101 (0) |
| chip_merged | slow | 25.751 | +0.326 | 0 | 0 | 52 / 1148 | 19 | 101 (0) |

Per path group (chip_merged): hold SCLK +0.106 / +0.185 / +0.326, osc_clk +0.126 / +0.205 / +0.348,
asynchronous (recovery/removal) +0.491 / +0.819 / +1.373; setup SCLK 28.006 / 27.277 / 25.751,
osc_clk 96.56 / 95.04 / 92.34 (fast / typ / slow).

- The macro case reproduces the run7 flow signoff (`../librelane_run7/`, `56-openroad-stapostpnr`: setup 29.06 / 28.84 / 28.48, hold 0.106 / 0.185 / 0.326, 56 unannotated) exactly.
- The chip_merged case reproduces the 2026-09-23 all-net result of `FINAL_ROUTED_TIMING_20260923.md` exactly (same slacks to 1 ps, 101 unannotated, 0 partial). The inlined constraints therefore behave like the previously sourced `g1_digital_top.sdc`.
- Template alone fails hold in fast and typ. The worst path is SDI → `i_core.u_digital/_6671_` (min input delay 0 ns in the template), then 49 / 5 internal SCLK-domain paths judged with 0.25 ns hold uncertainty instead of 0.05 ns. The osc_clk domain has no clock, so its 1148 registers are unconstrained. The numbers differ from the 2026-09-19 dry-run figure (−0.094 ns, 48 endpoints) because this is the later routed netlist; the cause is the same.
- **Unconstrained endpoints, chip_merged (19):** the 3 first synchroniser flops `_6644_/_6645_/_6646_` fed by the asynchronous `cmp_soft`, `cmp_hard` and `tripped` (false paths by design; metastability MTBF not analysed); 16 top-level ports reported by `check_setup`: EN, SCLK, SDI (pad ports), the 10 analog signal pins, and the outputs GATE, FAULT_N and TEMP_OUT, which the macro does not drive (GATE and FAULT_N come from g1_gate, TEMP_OUT from g1_t2f; neither block has a timing model). SDO is constrained. The macro standalone has the same 3 flops.
- **Unannotated drivers (the "101 unannotated paths"):** 56 are unused CTS dummy-load outputs `i_core.u_digital/clkload*/X` (also present standalone, where they are the macro's 56); 17 are chip ports; 28 are pad-cell pins (`pad`/`padres`/`padbare` of the analog and output pads). None of these is a digital register-to-register path. The 0 partially annotated drivers show that every routed net was loaded completely. This is a disposition, not a waiver.
- **"36 slow-pad flags":** these are 12 max-slew flags per corner × 3 corners. The analog-pad pins (`pad07_vdda/pad`, `/padbare` and `pad08`…`pad24` analog `pad`) report 200 ns against the 3.5 ns limit because the `sg13g2_IOPadAnalog` liberty has constant placeholder tables (200 ns transition, 1000 ns delay; local results artefact `analog-pad-slew-attribution-20260923-r2.json`). They are not digital nets. Same count in every corner here.
- **Max fanout, 78 flags in every case:** CTS clock buffers `clkbuf_leaf_*_osc_clk` / `clkbuf_0_osc_clk` drive 11–18 loads against the stdcell liberty `default_max_fanout : 8`, which is tighter than the SDC's 16 / 10. There are no max-slew or max-cap violations inside the macro. This is the known CTS fanout item (`../../README.md`, `DIGITAL_CTS_FANOUT_20260923.md`). It is **retained, not waived**.

## Status

| Check | Status |
| --- | --- |
| Macro setup / hold, 3 corners, nominal SPEF | passed |
| Chip context, template SDC only | failed (hold −0.137 fast / −0.070 typ, 50 / 6 endpoints, osc_clk unconstrained). This is the reason for the change. |
| Chip context, merged SDC, setup / hold, 3 corners | passed |
| Clock coverage (52 SCLK + 1148 osc_clk registers = all 1200) | passed |
| Full parasitic annotation | failed: 101 unannotated drivers (dispositioned above, not waived) |
| Max slew | failed: 12 per corner, analog-pad placeholder liberty (dispositioned above, not waived) |
| Max fanout | failed: 78 CTS buffers vs liberty default 8 (retained) |
| Corner-specific RC (min/max SPEF) | not run (only nominal extraction exists) |
| Timing of the final 1414 µm GDS (fill, moved pads, supply metal) | not run |
| Asynchronous inputs: MTBF, analog-to-digital timing | not run |
| SDF-annotated timing gate-level simulation | not run in this report (the handoff lists timing GLS as not qualified) |

## SDC change (`blocks/g1_padring/flow/g1_chip_top.sdc`)

The committed file **sourced** `g1_digital_top.sdc` through a relative path, and only when
the instance and the file both existed. If either was missing, the constraints were
silently skipped. The constraints are now **inline**, with a warning when the macro is
absent. `g1_digital_top.sdc` and `TOP_SDC.md` remain the block owner's reference. What each line does:

| # | Constraint | Why |
| --- | --- | --- |
| 1 | `create_clock osc_clk 100 ns` on `i_core.u_digital/clkbuf_0_osc_clk/A`, 0.3 ns transition, propagated | Without it the 1148 osc_clk registers are unclocked. The pin is the macro's root clock buffer: g1_osc has no liberty, so a clock placed on its output reaches no register. |
| 2 | `set_clock_groups -asynchronous` osc_clk vs SCLK | Every crossing is synchronised in the macro, so no cross-domain checks. |
| 3 | uncertainty setup 0.5 / hold 0.05 ns on both clocks | Macro signoff values. This replaces the template's 0.25 ns on hold, which is the source of the −0.2 ns shift. |
| 4 | `set_false_path -from EN`; `-through` macro pins `cmp_soft cmp_hard tripped en por_n` | Asynchronous inputs that are synchronised inside. EN is also the reset and must not create SCLK checks into osc_clk. |
| 5 | `set_input_delay -min 2.0` on SDI vs SCLK | The host drives SDI ≥ 2 ns after the falling SCLK edge. The template's 0 ns creates the SDI hold failure. |
| 6 | no constraint on macro→analog outputs | These are quasi-static, end at blocks without timing models, and were timed at macro signoff (20 ns output delay). |

The SDC names (`i_core.u_digital`, `pad14_sclk/p2c`, `clkbuf_0_osc_clk`) are those of the
LibreLane-lineage netlist; the run7 macro inside the 1414 µm GDS has the same internal names.

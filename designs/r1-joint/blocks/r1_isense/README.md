# r1_isense — two low-side shunt sense channels (3.3 V / 1.2 V, auto-zero)

State (2026-10-21, revision 2 + layout b): **laid out, DRC / antenna / LVS clean, extracted, simulated post-layout.**
The schematic (revision 2) is unchanged. Layout b: the residual offset after the auto-zero passes (+26 … +36 µV against 100 µV,
tt / ss / ff and the r1_bias current range). The loop crossover margins and the settling pass. The stb loop-validity flag fails
(regression from layout a; open issue 1). Area 0.047 mm² (target 0.025 mm² failed; S7 floorplan box met).
All numbers are **simulated** (ngspice-46, pinned PDK). Nothing is measured.

## Layout (revision b, 2026-10-21, track T4) — current state

Layout of record: `layout/r1_isense.gds` (sha256 `221ad69af11d…`). Box, pins and pin sides are unchanged: 158.4 × 296.8 µm,
19 Metal3 pins, inputs east, outputs west. Layout a is kept as `layout/r1_isense_layout_a.gds` (sha256 `054373fc7286…`).
The netlist of record is unchanged: revision 2, `schematic/r1_isense.spice`, sha256 `af013b95f5fd…`.
Runs: checks `layout-20261021-b`, extraction `pex-20261021-b`, post-layout campaign suffix `20261021-b`.
All numbers are **simulated** (ngspice-46, extracted RC). Nothing is measured.

Result: **the residual offset after the auto-zero passes** at tt, ss/125 °C and ff/−40 °C (+28.7, +25.8, +35.2 µV;
limit 100 µV). It also passes over the r1_bias current range. **Regression:** the loop-validity flag of the stb suite fails in most
loop results. The DC loop phase is −180° (right-half-plane pole of the broken loop). The crossover margins pass (PM ≥ 70.9°, GM ≥ 18.1 dB).
The cause is the wiring resistance of `vss` (see "Loop validity flag"). This is open for revision c.

### 1. Cause of the layout-a offset (quantified)

Method: remove groups of coupling capacitors from the layout-a extraction (`pex-20261021-a`), then run the same DC
deck at tt. Script `<G1_RESULTS_ROOT>/r1_isense/t4b-work/zeroc.py`. Results are in `sim/results/dev-b-attr-*/`.
Clock nets: `az`, `azb`, `azh`, `azhb`, `az_lv`, `azh_lv` and the level-shifter nodes `xls1_*`, `xls2_*`.

| Variant of the layout-a extraction | Residual offset, tt |
| --- | --- |
| as extracted | −216.4 µV |
| clock → `h1`/`h2` removed (18 caps, 2.9 fF) | +101.0 µV |
| clock → `xh1`/`xh2` removed | −218.9 µV |
| clock → amplifier nodes removed (`x1a/b`, `sa/b`, `f1/2`, `outp/n`, `rfoa/b`, … 142 caps) | −311.0 µV |
| clock → `h1`/`h2`, `xh1`/`xh2` and amplifier nodes removed | +5.7 µV |
| clock → `h1`/`h2`, `xh1`/`xh2` removed (35 caps, 4.7 fF) | **+7.0 µV** |
| every non-supply net → `h1`/`h2`, `xh1`/`xh2` removed (155 caps) | −2.3 µV |

The hold nodes are the whole cause. The driven pairs only act through their coupling into the hold nodes.
Hand estimate from the clock steps at the end of the auto-zero: dV(h1 − h2) = Σ dC × dV_clock / C_hold = −2.80 fC / 1.01 pF = −2.77 mV.
Referred to the input with gm_aux / gm1 ≈ 1/12, this gives −231 µV (estimated; simulated −216 µV).

### 2. Fix: grounded shield around the hold nets

1. The generator routes `h1`, `h2`, `xh1` and `xh2` first. It then wraps them in a `vss` shield
   (`Router.route_shielded` in `layout/maze_router.py`).
2. The shield takes every free grid node within one step of the route, on the route layer and on the layers above and below (Metal2–Metal4).
3. The shield is drawn as solid metal with Via2/Via3 stacks. It has 3125 nodes in 5 components, each tied to `vss` by the router.
4. Nodes next to or above another net's pin stay free, so the pins remain reachable.
5. The switch placement is unchanged: `xsh1` and `xsh2` are adjacent in NMOS row 3, in the same orientation. The MIM hold caps have their `vss` Metal5 bottom plate under the `h` top plate.
6. Mirrored hand-placed clock routes were not drawn. With the shield, the coupling of a hold route to a clock line is near zero wherever the clock line runs. The grid router is not symmetric. Recorded as a deviation from the task wording.

Coupling of each clock net to the hold pairs (kpex 2.5D CC; dC = C to the p side − C to the n side, in fF; full table for
all pairs: `reports/layout-20261021-b/coupling_ab.md`, script `layout/tools/coupling_table.py`):

| Clock net (step at AZ end) | Pair | dC layout a | dC layout b |
| --- | --- | --- | --- |
| `azh` (−3.3 V) | `h1/h2` | +0.567 | +0.102 |
| `azh` (−3.3 V) | `xh1/xh2` | −0.491 | −0.023 |
| `azhb` (+3.3 V) | `h1/h2` | −0.351 | +0.070 |
| `azb` (+3.3 V) | `h1/h2` | +0.239 | +0.075 |
| `xls2_inb` (+1.2 V) | `xh1/xh2` | +0.517 | −0.013 |
| `xls2_a` (+3.3 V) | `h1/h2` | −0.115 | +0.002 |
| `azh_lv` (−1.2 V) | `h1/h2` | −0.110 | −0.002 |
| `xls2_b` (−3.3 V) | `h1/h2` | +0.076 | +0.001 |
| `xls2_inb` (+1.2 V) | `h1/h2` | −0.042 | −0.000 |
| sum of abs(dC), clock → `h1/h2` | | 1.514 | 0.258 |
| estimated input-referred kick | | −231 µV | +12 µV |

Per-pair target ≤ 0.2 fF: **passed for the hold pairs** (worst 0.102 fF, `azh` → `h1/h2`). **Failed for the driven pairs**,
for example `xls1_inb` → `outp/outn` 5.19 fF (a: 4.98), `azhb` → `f1/f2` 1.64 fF (a: 0.06), `azb` → `sa/sb` 1.70 fF (a: 1.50).
The attribution above shows no residual-offset effect from these pairs, so they were not changed further. See open issue 2.

### Status (revision b)

| Check | Result | Evidence |
| --- | --- | --- |
| DRC, PDK deck, main + maximal, deep, density off | **passed**, 0 | `reports/layout-20261021-b/drc.log`, `run.json` |
| Density | **not run** (block level; top-level fill) | — |
| Antenna | **passed**, 0 | `reports/layout-20261021-b/antenna.log` |
| LVS against `layout/r1_isense_lvs.cdl` | **passed**: `r1_isense_ch` 143/143 nets, 177/177 devices; `r1_isense` 19/19 | `reports/layout-20261021-b/lvs_summary.txt` |
| Pin check (19 pins, sides) | **passed** | `reports/layout-20261021-b/pin_check.txt` |
| Box ≤ 158.4 × 296.8 µm (S7) | **passed** (equal) | `layout/r1_isense_layout.json` |
| PEX (kpex 2.5D CC + RNetExtractor + MIM) | **passed** (no open or negative element) | `<G1_RESULTS_ROOT>/r1_isense/pex-20261021-b/run.json` |
| Residual offset after AZ, ideal PTAT bias: tt / ss 125 °C / ff −40 °C | **passed**: +28.7 / +25.8 / +35.2 µV (≤ 100) | `sim/results/isense-post-dc-20261021-b/`, `isense-post-dc-ssff-20261021-b/` |
| Residual offset, `ibias` 3.5 / 5.07 / 7.7 µA × tt / ss / ff (9 points) | **passed**: +25.8 … +35.9 µV | `sim/results/isense-post-dc-ib{3.5u,5.07u,7.7u}-20261021-b/` |
| Gain, same 12 points | 14.050 … 14.065 (report; a 14.051) | same |
| Output CM, same 12 points | **passed**: 0.5913 … 0.5970 V (0.60 ± 0.03) | same |
| Pedestal error | +508 … +668 µV (report; a +829 µV at tt); split at tt: devices + C −68 µV, devices + R +589 µV | same, `isense-post-dc_c-`, `isense-post-dc_r-20261021-b/` |
| CM rejection, Kelvin CM −0.1 → +0.1 V, tt | input-referred offset +63.4 → −6.0 µV: 69.4 µV per 0.2 V (≈ 69 dB) (report; layout a by the same method: −183.0 → −249.9 µV, 67.0 µV) | `sim/results/isense-post-dc-cmm100-20261021-b/`, `-cmp100-` |
| Loops, normal state, tt and ffx, 3 shunt levels: crossover margins | PM 71.6–88.8°, GM ≥ 18.1 dB | `sim/results/isense-post-stb-20261021-b/` |
| Loops, normal state: validity flag | **failed** in 6 of 8 loop results: `cm_out` at all levels (tt, ffx), `dm_out`/`dm_in` at 0 mV (tt, ffx) and −20 mV (tt); DC phase −178.9 … −180° (layout a: `dm_in` tt 0 mV only) | same |
| Loops, AZ closed (az = azh = 1), tt and ffx | AZ servo `dm_aux` **passed** (80.7° / 44.6 dB tt, 83.8° / 39.3 dB ffx); `cm_out` crossover PM 75.9° / 77.8°, validity flag **failed** | `sim/results/isense-post-stbaz-20261021-b/` |
| Loops, intermediate state az = 1, azh = 0, tt and ffx | `cm_out` crossover PM 70.9° (ffx), validity flag **failed** (tt, ffx); other loops below 0 dB (not applicable) | `sim/results/isense-post-stbazi-20261021-b/` |
| Input-gate cross-check (`dm_in`) | **failed** flag (tt 0 and −20 mV, ffx 0 mV); the voltage-only ratio at the same probe equals the Tian result at every point → not a probe artefact, see below | `<G1_RESULTS_ROOT>/r1_isense/isense-post-stbdiag-20261021-b/` (`*_t4`, `*_t24`: columns 5–8) |
| Shunt step 0 → 100 mV, 10 ns edge, tt and ss | **passed**: 99.9 / 277.7 ns to 0.5 % (≤ 300; a 94.1 / 248.5), no overshoot | `sim/results/isense-post-stbstep-20261021-b/` |
| Offset and gain with the `r1_bias` netlist (bandgap + distribution) | **not run**; the 3.5–7.7 µA range of `ib_is_a/b` (INTERFACES.md) is used as a fixed-current sweep instead (recommended option, cheaper deck) | — |
| CM step (`stbcm`), sf / fs / ssx corners, MC on the extraction, EM / IR at the top level | **not run** | — |

### Loop validity flag and the input-gate cross-check (explanation)

1. **Not the probe.** The new deck `tb_isense_stbdiag.cir` (from `make_post.py`) also writes the voltage-only ratio
   Tv = −v(network side) / v(gate side) of the same probe. At a MOS gate the load side draws no current, so Tv is the loop gain at low frequency without the
   current-injection run. Tv equals the Tian result at every point, in layout a (−178.8° at tt / 0 mV, `dev-b-dmin-a`) and in
   layout b. The open issue 3 hypothesis of layout a (incomplete break) is therefore wrong.
2. **A real low-frequency property of the extracted circuit.** With the main loop broken, the rest of the circuit has a pole
   in the right half plane: T ≈ −K / (1 − s/p) with p of a few kHz. The DC phase is −180°, the magnitude is the same as a normal
   pole, and the high-frequency part is the same as the normal loop. With one open-loop RHP pole the Nyquist plot encircles
   −1 once counter-clockwise, so the closed loop is stable. The DC runs (16 µs transients) and the step runs (no overshoot) agree.
   The analyzer flag is correct in that the single-break margin is not a complete stability proof in this case.
3. **Source: wiring resistance of `vss`.** At tt in layout b, the effect is absent in the devices + C view (71.2 dB, −2.8°). It is present in the devices + R view.
   It is absent when only the `vss` wiring R is shorted (`dev-b-stbdiag-svss`: 71.0 dB, −2.8°), and present when only the output wiring R is shorted.
   The output-stage source current and the CMFB currents flow through `vss` wiring shared with the stage-1 sinks, the bias row and the
   slow-CMFB mirror (`xmgd` row 1, `xmgm` row 2). This closes a local loop around stages 1 and 2 that no single break opens.
   Probe `dev-b-supprobe-04`: per 1 V of output DM, 11 µV at the `xmgd` source and 125 µV at the `xmgm` source.
4. Layout a had a weaker form (`dm_in` at 0 mV only). The shield changed the `vss` network, because the shield components are `vss`
   pins and `vss` routes may run through them.
5. Five layout variants were tried (table below). None meets both goals. A shield that is a current-free tree (`dev-b06`) removes all
   flags at tt but raises the offset to +164 µV. **Recommended option, taken:** keep the variant that meets the stated goal (offset) and record the
   flags as open issue 1.

| Variant (dev run) | Change from b | Offset tt / ss | Normal-state flags at tt |
| --- | --- | --- | --- |
| b (`pex-20261021-b`; `pex-dev-b01` + the M2 stitch fix) | — | +28.7 / +25.8 µV | `dm` 0 and −20 mV, `cm` all |
| `pex-dev-b02` | output-stage sources on their own route to the trunk at row 3 (`vss_o`) | +76.6 / +68.0 µV | `dm` −20 mV |
| `pex-dev-b04` | + private NMOS tie strips (one via stack each) | +161.9 / +143.5 µV | `dm` −20 mV |
| `pex-dev-b05` | + `vss_o` joins south of the reference | +182.2 / +161.4 µV | `dm` −20 mV |
| `pex-dev-b06` | shield as a separate tree `vss_sh`, one trunk tap | +163.7 / +146.0 µV | none (all passed) |

The options stay in the generator, disabled: `OWN_RETURN`, `PRIVATE_STRIPS`, `SHIELD_NET`. Dev summaries: `sim/results/dev-b-*`. Raw data and check
reports: `<G1_RESULTS_ROOT>/r1_isense/pex-dev-b0*`, `reports-dev/layout-dev-b0*`.

### Open issues (revision b)

1. **Loop-validity flags (regression from a).** The fix needs a `vss` topology in which no varying current flows in wiring shared by the
   stage-1 sinks, the bias mirrors and the slow-CMFB mirror, while the static drops stay equal between AZ and normal mode.
   A candidate is a solid Metal1/Metal2 `vss` strap grid under the NMOS rows plus the `vss_sh` shield tree. Re-run the offset and the loops together on every
   variant. Revision c.
2. The driven pairs keep clock-coupling differences up to 5.2 fF. They have no effect on the residual offset (attribution), but they
   can add kick-back and a settling difference after the AZ. The ss step settling went from 248.5 to 277.7 ns (limit 300).
3. The pedestal error is +575 µV at tt, dominated by the wiring R (split +589 µV). It is a fixed term and is calibrated. Report only.
4. The offset and gain rows use a fixed-current sweep, not the `r1_bias` netlist with the bandgap. **Not run** with the real bias network.
5. kpex 2.5D runs about 22 min per extraction (layout a: about 6 min) because of the solid shield.
6. Open issues 2 and 4–9 of layout a (area 0.047 mm², `vssa`, top-level `vss` reference, MIM over resistors, router copy) still apply.

### Failures and mistakes (revision b)

| # | What happened | Class | Evidence |
| --- | --- | --- | --- |
| 1 | The record extraction `pex-20261021-b` was started before the loop check on the dev extraction. The layout then changed, so the run was stopped before kpex finished and renamed `pex-20261021-b-abandoned` (note `ABANDONED.txt`). The later record run reused the id. | process-hygiene | `<G1_RESULTS_ROOT>/r1_isense/pex-20261021-b-abandoned/` |
| 2 | The shield fix turned the single `dm_in` flag of layout a into flags in `dm_out` and `cm_out` in all states. Only the DC offset was checked on the first dev extraction. | regression | `sim/results/dev-b-stbdiag-01`, `isense-post-stb-20261021-b` |
| 3 | The layout-a explanation of the `dm_in` flag (incomplete break at the probe) was not tested; the voltage-only ratio shows it is a real circuit property. | verification-gap | `sim/results/dev-b-dmin-a`, `dev-b-dmin-a-hxall` |
| 4 | Three supply-topology changes (b02, b04, b05) were each based on one probe reading. None removed the flags, and each raised the offset. | estimation | table above |
| 5 | The current-free shield tree (b06) removed the flags but raised the offset to +164 µV: the two goals conflict through the `vss` R. Not resolved in the time budget. | estimation | `sim/results/dev-b-stb-06`, `dev-b-post-dc-06` |
| 6 | M2.b notch (0.04 µm, same net) between a router wire and a gate-rail stitch box (layout-dev-b03). The generator now starts the stitch under the node pad. | functional-bug | `<G1_RESULTS_ROOT>/r1_isense/reports-dev/layout-dev-b03/` |
| 7 | The GDS sha256 changes on every run (header time stamp). Reproduction is checked by a geometry comparison (KLayout `LayoutDiff`) of the regenerated file against the layout of record: identical. The generator sha256 in the check `run.json` (`54c40125…`) is older than the file; later edits only add the disabled options. | tooling | `<G1_RESULTS_ROOT>/r1_isense/t4b-work/gdsdiff.py` |
| 8 | The coupling attribution is not additive (clock → `xh` alone: −2.5 µV; together with clock → `h`: about −94 µV). Single-group removal underestimates the coupled paths. | numerical | `sim/results/dev-b-attr-*` |
| 9 | The per-pair target ≤ 0.2 fF was read as applying to every pair. It is met only where it affects the offset (hold pairs); the driven pairs fail it. | spec-ambiguity | `reports/layout-20261021-b/coupling_ab.md` |
| 10 | The layout-a CM-rejection row ("64.5 µV output change, ≈ 93 dB") does not match its own summaries: the analyzer offsets are input-referred, giving 67.0 µV per 0.2 V input-referred (≈ 69 dB). Revision b reports the input-referred value. | verification-gap | `sim/results/isense-post-dc-cmm100-20261021-a/`, `-cmp100-` |
| 11 | `cpuset` is null in the check and PEX `run.json` (as in layout a); the CPU set was 109–111. | tooling | `reports/layout-20261021-b/run.json` |

### Built against (revision b)

As layout a: IHP-Open-PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`, KLayout 0.30.9, kpex 0.3.12, ngspice-46, container
`tapeoutbench-eda` `sha256:ddeb6957…` (all checked by `flow/run.sh` and written in each `run.json`), CPU set 109–111.

### Reproduce (revision b)

From the repository root, POSIX sh, with `G1_CPUSET=109-111; export G1_CPUSET` and `G1_RESULTS_ROOT` set and exported:

1. `G1_WORKDIR=designs/r1-joint/blocks/r1_isense/layout; export G1_WORKDIR; flow/run.sh klayout -b -r r1_isense_layout.py`
2. `flow/run.sh sh run_checks.sh layout-20261021-b all`
3. `unset G1_WORKDIR; sh designs/r1-joint/blocks/r1_isense/layout/pex/run_pex.sh pex-20261021-b`
4. `sh designs/r1-joint/blocks/r1_isense/layout/pex/run_post.sh pex-20261021-b 20261021-b` (now includes the ss/ff DC, the
   `ibias` sweep, the intermediate AZ state and the input-gate cross-check)
5. `python3 designs/r1-joint/blocks/r1_isense/layout/tools/coupling_table.py a=<kpex netlist a> b=<kpex netlist b>`

---

## Layout (revision a, 2026-10-21, track T4 layout) — superseded by revision b

Layout of record: `layout/r1_isense.gds` (sha256 `054373fc7286…`), both channels, generated by
`layout/r1_isense_layout.py` from the revision-2 netlist of record (`schematic/r1_isense.spice`, sha256 `af013b95f5fd…`,
unchanged). Checks run `layout-20261021-a`, extraction `pex-20261021-a`, post-layout campaign suffix `20261021-a`.
All post-layout numbers are **simulated** (ngspice-46, extracted RC). Nothing is measured.

### What the layout is

1. Two channels as identical placed copies of one cell `r1_isense_ch` (147.2 × 143.2 µm): channel A at the south,
   channel B at the north, a 1.6 µm gap between them.
2. Gain network: 82 `rppd` units (w 2 µm, l 30.8 µm) in one array of 41 columns × 2 rows, with 2 dummy columns on
   each side. RIA / RIB sit in the centre column. The 14 + 14 RF units interleave in the columns −7 … +7
   (pattern `ABBAABBAABBAAB`); the 26 + 26 RP units in the columns ±8 … ±20. Both patterns have equal first and
   second moments per side. The RF chains are explicit snakes; the last RF unit is strapped to RIN on Metal1.
3. Shunt inputs: the RIA / RIB heads face the 5.6 µm gap between the two rows. A Metal3 band (1.6 µm wide) runs from
   each head to the east edge. Wiring from pin to RIN: 10.8 Ω (it was 131 Ω with router wires, `pex-dev-01`).
4. Input pairs `xm1` / `xm2` and the aux pairs `xa1` / `xa2`: each device in two halves, placed ABBA over two rows
   (common centroid), with poly dummies at both ends of each device.
5. MIM over the resistor array (C6 practice): `xci` (1.9 pF), the hold caps `xch1` / `xch2`, the CM caps and the Miller
   caps, all inside the main array outline. TopMetal1 only on the MIM plates; no TopMetal2.
6. Thick-oxide devices in TGO rows with the HV well rules; the 1.2 V level shifter and the `vdd` output loads in a
   separate LV block. p+ guard ring (`vss`) around the block. Routing Metal1–Metal4 (grid router, 0.8 µm pitch).
7. Kelvin trees (layout only; the netlist does not change):
   - outputs: the output-stage current flows in `outp` / `outn` (drains of `xmo` and `xml`, caps). The feedback switch
     `xsf`, the CM-sense `rhigh` and the edge pin join that tree at one node of the `xmo` drain rail.
   - the `vss` end of the RPA arm has its own route to the `vss` trunk.
   - the hold nodes `h1`/`h2`/`xh1`/`xh2` and the summing nodes `sa`/`sb` are routed first; other routes pay a cost
     next to, over and under them.
8. Pins (Metal3, at the boundary; floorplan S7):
   - east: `isa_p`, `isa_n`, `isb_p`, `isb_n` (1.6 µm wide bands);
   - west: `outa_p`, `outa_n`, `outb_p`, `outb_n`;
   - south: `vss`, `vdda`, `vdd` (Metal4 trunks to Metal3 stubs), `vcm`, `vref`, `ibias_a`, `az_a`, `azh_a`;
   - north: `az_b`, `azh_b`, `ibias_b`.

### Area

| Item | Value | Basis |
| --- | --- | --- |
| Bounding box, both channels | **158.4 × 296.8 µm = 0.0470 mm²** | `layout/r1_isense_layout.json`, `reports/layout-20261021-a/pin_check.txt` |
| Task target | ≤ 0.025 mm²: **failed** (+88 %) | the device area alone is 0.021 mm² (`schematic/area.py`), so 0.025 mm² leaves 19 % for wiring, wells and spacing |
| Floorplan S7 box (PLAN.md D10 amendment) | ≤ 158.4 × 296.8 µm: **met** (equal) | coordinator message during this track |
| Channel cell | 147.2 × 143.2 µm = 0.0211 mm² | layout |

### Status (layout, runs `layout-20261021-a`, `pex-20261021-a`, `*-20261021-a`)

| Check | Result | Evidence |
| --- | --- | --- |
| DRC, PDK deck, main + maximal tables, deep, density off | **passed**, 0 markers | `reports/layout-20261021-a/run.json`, `drc.log` |
| Density | **not run** (waived at block level; top-level fill) | — |
| Antenna, PDK deck | **passed**, 0 markers | `reports/layout-20261021-a/antenna.log` |
| LVS, PDK deck, deep, `--no_series_res`, against `layout/r1_isense_lvs.cdl` (revision 2 with the unit split) | **passed**: `r1_isense_ch` 143/143 nets, 177/177 devices; `r1_isense` 19/19 nets | `reports/layout-20261021-a/lvs_summary.txt` |
| Pin check (Metal3 pins at the boundary = CDL ports, sides) | **passed**, 19 pins | `reports/layout-20261021-a/pin_check.txt` |
| PEX: kpex 2.5D CC + wiring R + MIM from the netlist | **passed** (no open or negative element) | `<G1_RESULTS_ROOT>/r1_isense/pex-20261021-a/run.json` |
| Post-layout DC, tt: residual offset after AZ | **failed**: −216.4 µV (criterion ≤ 100 µV; schematic 0.0) | `sim/results/isense-post-dc-20261021-a/` |
| Post-layout DC, tt: gain, output CM | gain 14.051 (report); output CM 0.591 V: **passed** (0.60 ± 0.03 V) | same |
| Post-layout DC split views (devices + C, devices + R) | run (diagnosis) | `sim/results/isense-post-dc_c-20261021-a/`, `isense-post-dc_r-20261021-a/` |
| Post-layout CM rejection, Kelvin CM ±0.1 V, tt | 64.5 µV output change per 0.2 V (≈ 93 dB input-referred; schematic −2.3 µV, ≈ 122 dB); report | `sim/results/isense-post-dc-cmm100-20261021-a/`, `-cmp100-` |
| Post-layout CM loop, normal and AZ closed, tt and ffx | **passed**: worst PM 67.4° (normal, tt), GM ≥ 30 dB or no 180° crossing | `sim/results/isense-post-stb-20261021-a/`, `isense-post-stbaz-20261021-a/` |
| Post-layout DM loop and AZ servo, tt and ffx | **passed**: DM 71.3° / 17.3 dB, AZ servo 81.0° / 38.9 dB | same |
| Post-layout input-gate cross-check `dm_in` | **failed** (analyzer flag) at tt, shunt 0 mV only: DC phase −178.8°, the break is not complete in the extracted network (see open issue 3); PM 71.3° / GM 17.4 dB equal to `dm_out` | `sim/results/isense-post-stb-20261021-a/` |
| Post-layout shunt step 0 → 100 mV, tt and ss | **passed**: 94 / 249 ns to 0.5 % (≤ 300 ns), no overshoot | `sim/results/isense-post-stbstep-20261021-a/` |
| EM / IR drop at the top level | **not run** | — |
| Mismatch MC on the extracted netlist | **not run** | — |
| Post-layout at ss, ff, sf, fs, ssx (other than the rows above) | **not run** | — |

### Pre- versus post-layout (simulated; post = full extracted RC of the channel, both channels use the same extraction)

| Quantity | Schematic (rev 2) | Post-layout | Unit | Criterion |
| --- | --- | --- | --- | --- |
| DC tt gain (RC) | 14.01 | 14.05 |  | report (14) |
| DC tt gain (devices + C / devices + R) | not run | 14.0217 / 14.0373 |  | split |
| DC tt pedestal_error_uV (RC) | -54.49 | 828.7 | uV | report |
| DC tt pedestal_error_uV (devices + C / devices + R) | not run | 158.8734 / 613.4958 | uV | split |
| DC tt offset_pedestal_off_uV (RC) | 0 | -216.4 | uV | abs <= 100 |
| DC tt offset_pedestal_off_uV (devices + C / devices + R) | not run | -222.6529 / 9.0805 | uV | split |
| DC tt vcm_out_V (RC) | 0.6005 | 0.5906 | V | 0.60 +/- 0.03 |
| DC tt vcm_out_V (devices + C / devices + R) | not run | 0.5999 / 0.5912 | V | split |
| Kelvin CM -0.1 -> +0.1 V: output change (CM gain) | -2.3 | 64.5 | uV per 0.2 V | report |
| normal tt cm_out PM / GM | 71.8 deg / 30.8 dB | 67.4 deg / no 180 deg crossing |  | PM >= 60, GM >= 10 |
| normal tt dm_out PM / GM | 74.4 deg / 18.6 dB | 71.3 deg / 17.3 dB |  | PM >= 60, GM >= 10 |
| normal tt dm_in PM / GM | 74.4 deg / 18.6 dB | 71.3 deg / 17.4 dB |  | PM >= 60, GM >= 10 |
| normal ffx cm_out PM / GM | 73.6 deg / 30.7 dB | 72.3 deg / no 180 deg crossing |  | PM >= 60, GM >= 10 |
| normal ffx dm_out PM / GM | 77.4 deg / 20.3 dB | 76.7 deg / 19.9 dB |  | PM >= 60, GM >= 10 |
| normal ffx dm_in PM / GM | 77.4 deg / 20.3 dB | 76.7 deg / 19.9 dB |  | PM >= 60, GM >= 10 |
| AZ closed tt cm_out PM / GM | 77.0 deg / 31.5 dB | 75.0 deg / no 180 deg crossing |  | PM >= 60, GM >= 10 |
| AZ closed tt dm_aux PM / GM | 81.5 deg / 44.6 dB | 81.0 deg / 44.1 dB |  | PM >= 60, GM >= 10 |
| AZ closed ffx cm_out PM / GM | 77.6 deg / 30.7 dB | 77.0 deg / 58.7 dB |  | PM >= 60, GM >= 10 |
| AZ closed ffx dm_aux PM / GM | 84.6 deg / 39.2 dB | 84.0 deg / 38.9 dB |  | PM >= 60, GM >= 10 |
| step 0 -> 100 mV tt settle 0.5 % (from edge start) | 92.62 | 94.08 | ns | <= 300 |
| step tt overshoot count | 0 | 0 |  | report |
| step 0 -> 100 mV ss settle 0.5 % (from edge start) | 208.2 | 248.5 | ns | <= 300 |
| step ss overshoot count | 0 | 0 |  | report |

CM rejection from the extracted resistor network: the units are identical by construction, so the systematic ratio
error of the unit arrays is 0. The wiring in series with the arms is what remains. From `pex_paths.json`: RIN side
10.8 Ω on each input; the RF and RP arms differ by less than 20 Ω out of 56 kΩ and 104 kΩ. The Kelvin common-mode
row above is the simulated result with these values.

### Open issues (layout)

1. **AZ residual offset after the layout is −216 µV at tt (criterion 100 µV).** The split runs give the cause: the
   devices + C view alone gives −223 µV, the devices + R view +9 µV. The capacitive asymmetry of the
   switched nets (AZ clocks, level-shifter nodes) against `x1a/x1b`, `f1/f2`, `outp/outn` and the hold nodes kicks the
   hold caps when AZ opens. Guarding the AZ clock nets made it worse (−295 µV, `pex-dev-07`). A fix needs
   mirrored, hand-placed routes for these pairs (the router is not symmetric). Not done in this track.
2. The pedestal error grew from −54 µV to +829 µV (same cause). The pedestal is a fixed, calibrated term; report only.
3. **`dm_in` cross-check at tt, shunt 0 mV:** the gate probe sees a DC loop phase of −178.8° and a lower DC gain than
   `dm_out`. The extracted wiring R and the coupling C of `sa`/`sb` sit on the driver side of the probe, so the break is
   not complete. `dm_out` (the loop of record) passes with the same PM. Not resolved; a probe at the device gate pins
   of the extracted netlist is the next step.
4. Output CM 0.591 V (schematic 0.6005 V); the supply wiring (`vss`, `vdda`) gives most of the drop
   (split runs `dev-bisect-01-sup`, `isense-post-dc_r-20261021-a`). Inside 0.60 ± 0.03 V.
5. The netlist has one ground `vss`. The task lists `vssa` as a pin; no `vssa` exists in revision 2. The layout has
   `vss` only (spec-ambiguity, below).
6. The vss reference of the extraction is the trunk label in the channel. At the top level the channel current flows
   to the south pin along the trunk (about 2 mV over 70 µm at 0.57 mA, estimated). The RPA arm has a Kelvin tap; its
   top-level reference must be the ground of `vref` (open for the top-level assembly).
7. MIM over the resistors couples the plates to the `rppd` bodies (included in the extraction; the caps of `outp`,
   `vcm` and the hold nodes sit over RF / RP units).
8. Area: 0.047 mm² against the 0.025 target. Reduction options (not tried): narrower RP units (w 1 µm), MIM over the
   MOS rows, a second Metal routing grid at 0.6 µm pitch.
9. The grid router is a copy of the r1_afe router with an added guarded mode (`route_guarded`); the router is not
   shared code.

### Failures and mistakes (layout)

Development runs: raw and reports of `layout-dev-*` and `pex-dev-*` under `<G1_RESULTS_ROOT>/r1_isense/`; summaries of
`dev-post-dc-*` and `dev-bisect-01-*` in `sim/results/`.

| # | What happened | Class | Evidence |
| --- | --- | --- | --- |
| 1 | The HV PCells clamp L > 10 µm ("using maximum length 10u"): the 20 µm devices came out short. Fixed with a stretched PCell (`LongMos`). | tooling | `layout/r1_isense_layout.py` `LongMos` |
| 2 | The first segment placement put two segments on top of each other (assert); the start x of the tail segments was not computed from the real widths. | estimation | generator assert, `layout-dev` |
| 3 | First DRC: 32 markers in the LV block (Cnt.d 6, M1.b 13, pSD.d1 1, Sal.d 4, Cnt.g 8): the LV block overlapped the RDG implants and the short-gate contacts collided with the source rails. | planning | `<G1_RESULTS_ROOT>/r1_isense/reports-dev/layout-dev-01/` |
| 4 | The first extraction gave gain 13.77 (schematic 14.008) and offset −652 µV: the router wires from the shunt pins to RIN had 131 Ω (3.3 % of RIN). The input path was not designed as a precision path. Fixed with the Metal3 input bands. | verification-gap | `pex-dev-01`, `dev-post-dc-01*` |
| 5 | After the input fix the offset was −1494 µV. A split by shorting groups of wiring R (`dev-bisect-01-*`) showed the output-stage current in the `outp/outn` wiring as the cause (−600 µV → −30 µV with that wiring shorted). Fixed with Kelvin output trees (−599 → +9 µV in the R view). | functional-bug | `dev-post-dc-02*`, `dev-bisect-01-*`, `dev-post-dc-07*` |
| 6 | A Kelvin tap of the RPA `vss` end was added first on a wrong hypothesis (no change, −599 µV). Kept: it is correct practice. | estimation | `dev-post-dc-06*` |
| 7 | The Kelvin router net `vss_k` was written as a label; LVS named the net `vss,vss_k` and the post-layout decks failed. Fixed with a label alias. | tooling | `pex-dev-04` |
| 8 | A hard keep-out around the hold nets made 11–16 nets unroutable; replaced by a path cost. Guarding the AZ clock nets made the offset worse (−216 → −295 µV) and was reverted. | estimation | `layout-dev-06`, `-07`, `-12`, `pex-dev-07` |
| 9 | Three via cuts at 0.5 µm pitch in the tie stacks were 0.11 µm from a router via (V2.b / V3.b, 2 + 2 markers). Fixed with two cuts. | functional-bug | `<G1_RESULTS_ROOT>/r1_isense/reports-dev/layout-dev-04/` |
| 10 | A combined background command started the extraction twice; stopped after seconds, before any output, and restarted as one script. | process-hygiene | `<G1_RESULTS_ROOT>/r1_isense/final/final.sh` |
| 11 | The task lists a `vssa` pin; the revision-2 netlist has none. Taken as `vss` only. | spec-ambiguity | `schematic/r1_isense.spice` ports |
| 12 | The floorplan constraint S7 arrived during the track (pin sides). Controls, bias and references moved to the south (A, shared) and north (B) edges; "controls" was taken to include `ibias`, `vref` and `vcm`. | spec-ambiguity / coordination | coordinator message, `reports/layout-20261021-a/pin_check.txt` |
| 13 | The post-layout input-gate cross-check `dm_in` was not validated on the extracted netlist before the campaign; it fails its validity flag at one point (open issue 3). | verification-gap | `sim/results/isense-post-stb-20261021-a/` |
| 14 | The `run.json` field `cpuset` of the check and PEX runs is null: `G1_CPUSET` is not passed into the container. The CPU set was 109–111 (command line). | tooling | `reports/layout-20261021-a/run.json` |

### Built against (layout)

| Item | Version | How established |
| --- | --- | --- |
| PDK | IHP-Open-PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` | checked by `flow/run.sh`; `run.json` field `tools.pdk_commit` |
| KLayout | 0.30.9 | `klayout -v` in `run.json` |
| kpex | 0.3.12 | `kpex --version` in the PEX `run.json` |
| ngspice | ngspice-46 | `run.json` of each post-layout run |
| Container | `tapeoutbench-eda`, id `sha256:ddeb6957…` | `flow/run.sh` |
| CPU set | 109–111 | command line |

### Files (layout)

| Path | Content |
| --- | --- |
| `layout/r1_isense.gds` | layout of record (1.6 MB) |
| `layout/r1_isense_layout.py` | generator (KLayout Python): `flow/run.sh klayout -b -r r1_isense_layout.py` in `layout/` |
| `layout/r1_isense_netlist.py`, `layout/r1_isense_lvs.cdl` | unit split of the netlist of record for LVS (generated) |
| `layout/maze_router.py` | grid router (copy of the r1_afe router, with `route_guarded`) |
| `layout/run_checks.sh`, `layout/check_pins.py`, `layout/tools/` | DRC, antenna, LVS, pin check, `run.json` |
| `layout/pex/run_pex.sh` | extraction: `pex_prepare.py`, kpex, `pex_build.py`, `pex_paths.py`, `make_post.py`, `tools/write_pex_runjson.py` |
| `layout/pex/run_post.sh`, `layout/pex/report_post.py` | post-layout campaign and the pre/post table (`sim/results/summary-post-20261021-a.json`) |
| `reports/layout-20261021-a/` | check logs and `run.json` |

Reproduce from the repository root (POSIX sh): set `G1_CPUSET` and `G1_RESULTS_ROOT`, then
`G1_WORKDIR=designs/r1-joint/blocks/r1_isense/layout; export G1_WORKDIR; flow/run.sh klayout -b -r r1_isense_layout.py`,
`flow/run.sh sh run_checks.sh layout-20261021-a all`, and (with `G1_WORKDIR` unset)
`sh designs/r1-joint/blocks/r1_isense/layout/pex/run_pex.sh pex-20261021-a` and
`sh designs/r1-joint/blocks/r1_isense/layout/pex/run_post.sh pex-20261021-a 20261021-a`.

---

## Revision 2 (2026-10-21, track T4) — schematic of record

Netlist of record: `schematic/r1_isense.spice` (revision 2, sha256 `af013b95f5fd…`, generated by `schematic/gen_isense.py`
with its default options). Revision 1 is kept as `schematic/r1_isense_rev1.spice` (sha256 `5db34e0a8f7c…`, the netlist of
every revision-1 run below). All numbers are **simulated** (ngspice-46, IHP SG13G2 `84374023`), schematic level, ideal
reference sources. Nothing is measured. The revision-1 record follows this section unchanged.

Goal (task T4 revision 2): the CM/CMFB loop at PM ≥ 60° and GM ≥ 10 dB in the normal state, with the auto-zero closed
(az = azh = 1) and in the intermediate state az = 1, azh = 0, at tt, ss/125 °C/3.0 V, ff/−40 °C/3.6 V, sf, fs, ssx and ffx,
with every revision-1 pass kept. **Result: met** (tables below). The DM path, the resistor network, the auto-zero switches
and caps and the bias are unchanged.

### What changed (revision 1 → 2)

| # | Instance (channel subcircuit `r1_isense_ch`) | Revision 1 | Revision 2 | Why |
| --- | --- | --- | --- | --- |
| 1 | CMFB share of the folding sinks `XMC1S/XMC2S`; fixed sinks `XMS1/XMS2` | 2 units (10 µA, 2/3 of the CMFB diode); 7 units (35 µA) | **1 unit (5 µA, 1/3); 8 units (40 µA)** | halves the fast CM-loop gain; total sink current unchanged (45 µA) |
| 2 | CMFB pair `XMF1/XMF2` source degeneration `XRDG1/2` (new) | none | **`rppd` w 1 µm, l 50 µm (≈ 13 kΩ) per side** | lowers the fast CM-loop gain; with item 1 the CM crossover falls from 6.5–20.5 MHz to below the stage-2 phase roll-off |
| 3 | Slow CMFB path (new; **topology change in the CMFB**) | — | OTA `XMTG` (w 0.5/l 2 µm, ≈ 0.6 µA), pair `XMG1/XMG2` (w 1/l 24 µm), mirror `XMGD/XMGM` (w 8/l 32 µm), integrating cap `XCI` 36 × 36 µm MIM (≈ 1.9 pF) from `vint` to `vcm`; `vint` replaces `vcm` at the gate of `XMF2` | restores the DC accuracy of the output CM that items 1–2 remove (see "Why a topology change"); the cap to `vcm` lets a `vcm` step reach the fast path at once |
| 4 | Reference of the fixed sinks: cascode `XMBFC` (new, w 10/l 2 µm, gate `vbnc`) in the `XMBF` diode branch | `XMBF` diode at V_GS | **wide-swing reference: `XMBF` at the fold-node voltage** | systematic output-CM error (channel-length modulation, sinks at 0.29–0.48 V vs reference at 0.67–0.82 V): output CM 0.559–0.588 V → 0.601–0.602 V |
| 5 | CMFB diodes `XMFD/XMFE`: cascodes `XMFDC/XMFEC` (new, w 30/l 2 µm, gate `vbnc`) | diode at V_GS | **diode drain at the fold-node voltage** | same as item 4, for the CMFB mirror |
| 6 | Hold path: `XRH1/XRH2` (new, `rhigh` w 1/l 37.5 µm, 50 kΩ) between `x1a/x1b` and the hold switches | switch on `x1a/x1b` | **50 kΩ in series** | with AZ closed, the 1 pF hold caps loaded the stage-1 output node and cost 10–14° of CM phase margin; the resistor isolates them above the AZ servo band (AZ servo PM 92.6–96.5° → 77.4–85.1°, still ≥ 60°) |

Unchanged: input pair, aux pair, folded cascode, stage 2, Miller `CC` 0.22 pF and `RZ`, CM-sense `rhigh` 2 × 200 kΩ and
bypass caps, resistor network, AZ switches and hold caps, level shifters, bias.

### Why a topology change (development record, runs `dev-r2-01` … `dev-r2-29`)

The task prefers compensation and bias values. Value-only candidates were screened first (`sim/dev_r2.py`; loop gain in
the three states at tt/ff/ssx/ffx, worst CM PM in brackets):

| Candidate | CM PM normal / AZ closed | Finding | Run |
| --- | --- | --- | --- |
| revision 1 (baseline, 7 corners) | 35.5° / 21.4° (az = 1, azh = 0: 32.6°) | failed | `dev-r2-01` |
| cross-coupled Miller caps (CM-only Miller, as r1_afe rev D), 17/12 µm and 14/7 µm | 71.7° / 60.4°; 55.1° / 59.1° | **DM GM 6.0 dB and 9.5 dB** (the cross cap is positive feedback for DM): failed | `dev-r2-02`, `-10` |
| lag network at the sink gates | 23.5° / 15.7° | worse (the rhigh lag resistors and the sink gate cap add a pole near the crossover) | `dev-r2-05` |
| more CM-sense bypass, larger `RZ` | +4° / +1° | not enough | `dev-r2-07`, `-08` |
| source degeneration 13–26 kΩ (+ items 4, 5, 6) | 60.6–70.2° / 63.3–65.5° | margins met, but the **output CM under mismatch** σ rises from 16.6 mV to 62 mV (41 mV with a 2 × 2 reference): the DC CM gain falls by the same factor as the HF gain | `dev-r2-06`, `-09`, `-13`, `-14` |
| two-path CMFB, slow path as current steering (`TP=1`) | 38–67° | slow path out of range (output CM 0.66–0.84 V) or too fast | `dev-r2-15`, `-16`, `-23` |
| two-path CMFB, slow path trims the fast-pair reference (`TP=2`) | 61.5–83.6° | adopted; iterations: degenerated slow pair (resistor mismatch, CM σ 27.8 mV, `dev-r2-17`) → long-channel pair (σ 3.4–4.6 mV, `-18`…`-22`); cap to `vss` made a `vcm` step slow (> 1.1 µs, `-22`) → cap to `vcm` (`-24`); CM-input sensitivity of the fast pair at ss (tail headroom, 73 % step) → smaller CMFB share (`-25`, `-26`); slow tail of the CM step → slower slow path (`-27`); slow-path range at ss 125 °C (2/30 MC samples, `vint` at 0.30 V) → mirror w 2 → 8 µm (`-29`) | `dev-r2-17` … `-29` |

The decision: a two-path CMFB (fast degenerated path for the crossover, slow integrating path for the DC level) is the
smallest change found that meets the margins **and** keeps the output-CM accuracy under mismatch (better than revision 1).
Recorded here as the recommended option; no question was asked.

### Margins per loop, state and corner (worst over the shunt levels 0 / +100 / −20 mV; PM ° / GM dB)

Criterion PM ≥ 60°, GM ≥ 10 dB. Revision-1 values for ssx, ffx and the az = 1 / azh = 0 state are from `dev-r2-01`
(revision-1 netlist, never run before). Load: joint-path fixture of r1_safe (2 pF per output, OC and NEG comparators).

| Corner | CM normal rev 1 → 2 | CM AZ closed rev 1 → 2 | CM az = 1, azh = 0 rev 1 → 2 | DM normal rev 2 (rev 1) | AZ servo rev 2 (rev 1) |
| --- | --- | --- | --- | --- | --- |
| tt | 41.5 / 11.3 → **71.8 / 30.8** | 29.7 / 13.3 → **77.0 / 31.5** | 40.2 / 10.7 → **71.3 / 30.1** | 74.4 / 18.6 (74.8 / 18.7) | 81.5 / 44.6 (95.1 / 31.7) |
| ss 125 °C 3.0 V | 49.5 / 13.8 → **76.6 / 34.4** | 41.5 / 19.9 → **83.6 / 33.0** | 43.4 / 11.7 → **74.3 / 31.7** | 79.0 / 21.5 (79.0 / 21.4) | 78.0 / 45.7 (92.6 / 33.6) |
| ff −40 °C 3.6 V | 35.5 / 9.7 → **68.0 / 28.5** | 21.4 / 8.6 → **72.0 / 29.9** | 35.4 / 9.5 → **67.8 / 28.2** | 71.9 / 17.2 (72.2 / 17.3) | 85.1 / 42.0 (96.5 / 30.2) |
| sf | 41.3 / 11.2 → **71.7 / 30.7** | 29.7 / 13.6 → **76.8 / 31.4** | 39.8 / 10.6 → **71.1 / 30.0** | 74.2 / 18.5 (74.7 / 18.6) | 81.3 / 44.4 (95.1 / 31.6) |
| fs | 41.7 / 11.4 → **72.0 / 30.9** | 29.7 / 13.1 → **77.1 / 31.5** | 40.5 / 10.8 → **71.5 / 30.2** | 74.6 / 18.7 (75.0 / 18.8) | 81.7 / 44.8 (95.0 / 31.8) |
| ssx (ss, −40 °C, 3.6 / 1.32 V) | 45.2 / 11.9 → **73.0 / 31.5** | 32.1 / 12.9 → **77.5 / 32.0** | 44.9 / 11.7 → **73.0 / 31.2** | 74.5 / 18.6 (74.8 / 18.7) | 77.4 / 49.2 (95.6 / 32.4) |
| ffx (ff, 125 °C, 3.0 / 1.08 V) | 39.2 / 11.5 → **73.6 / 30.7** | 28.7 / 13.8 → **77.6 / 30.7** | 32.6 / 9.2 → **70.0 / 28.0** | 77.4 / 20.3 (77.4 / 20.2) | 84.6 / 39.2 (93.4 / 31.0) |

Smallest CM margin: 67.8° (az = 1, azh = 0, ff), +7.8° above the limit. Smallest CM GM 28.0 dB.
CM step (VCM +20 mV): overshoot 25–44 % with 2–3 overshoots (revision 1) → 0.0–2.7 %, at most 1 overshoot beyond 2 %,
settled to 2 % in 108–205 ns.

### Status (revision 2, campaign suffix `20261021r2`)

Evidence: `sim/results/<run-id>/run.json` (command, PDK commit, ngspice version, netlist sha256 `af013b95f5fd…`, included
netlists) and `summary.json`; reduced table `sim/results/summary-20261021r2.json` (from `sim/report_r2.py`); raw decks, logs
and waveforms in `<G1_RESULTS_ROOT>/r1_isense/<run-id>/` and `<G1_RESULTS_ROOT>/r1_safe/<run-id>/`.

| Check | Criterion | Status | Evidence |
| --- | --- | --- | --- |
| CM / CMFB loop, normal state, 7 corners, 3 shunt levels | PM ≥ 60°, GM ≥ 10 dB | **passed**: 68.0–76.6°, GM ≥ 28.5 dB (rev 1 failed: 35.5–49.5°) | `sim/results/isense-stb-20261021r2/` |
| CM / CMFB loop, AZ closed (az = azh = 1), 7 corners | same | **passed**: 72.0–83.6°, GM ≥ 29.9 dB (rev 1 failed: 21.4–41.5°) | `sim/results/isense-stbaz-20261021r2/` |
| CM / CMFB loop, az = 1, azh = 0 (new state), 7 corners | same | **passed**: 67.8–74.3°, GM ≥ 28.0 dB (rev 1, `dev-r2-01`: failed, 32.6–44.9°) | `sim/results/isense-stbazi-20261021r2/` |
| Main DM loop, normal state, 7 corners | same | **passed**: 71.9–79.0°, GM ≥ 17.2 dB (unchanged within 0.5°) | `isense-stb-20261021r2` |
| DM cross-check, break at the input gates | equal to the output break | **passed**: within 0.03° | `isense-stb-20261021r2` |
| AZ servo, AZ closed, 7 corners | PM ≥ 60°, GM ≥ 10 dB | **passed**: 77.4–85.1°, GM ≥ 39.2 dB (rev 1 92.6–96.5°: the hold-path resistors cost 8–18°) | `isense-stbaz-20261021r2` |
| AZ loop return ratio (1 GH / 1 F method), 5 corners | PM ≥ 45° | **passed**: 77.2° worst, GM ≥ 39.4 dB, unity 0.71–1.10 MHz, DC ≥ 47.9 dB | `sim/results/isense-azloop-20261021r2/` |
| CM step, VCM +20 mV, 7 corners | ≤ 1 overshoot beyond 2 %, settled to 2 % within 300 ns | **passed**: 0.0–2.7 %, ≤ 1, 108–205 ns (rev 1 re-analysed: failed, 2–3 overshoots) | `sim/results/isense-stbcm-20261021r2/` |
| Output CM, 5 corners (DC and step decks) | 0.600 V ± 30 mV | **passed**: 0.6003–0.6007 V (rev 1: 0.559–0.588 V; ss_cold −41 mV was outside) | `isense-dc-20261021r2`, `isense-step-20261021r2` |
| Output CM under mismatch (new row), MC tt 50, ss 125 °C 30, ff −40 °C 30 | ± 30 mV every sample | **passed**: σ 3.2 / 4.1 / 3.5 mV, range 0.587–0.608 V, 110/110 (rev 1 from its raw waveforms: σ 16–17 mV, 0.532–0.624 V, not all within) | `isense-mc-20261021r2`, `isense-mc-ssff-20261021r2` |
| Load sensitivity (ADC load 100 Ω + 2.8 pF + 0.2 pF), tt / ss | PM ≥ 60° | **passed**: DM 72.0 / 77.3°, CM 70.6 / 75.8° | `isense-stb-load28-20261021r2` |
| Comparators at the calibration point (code 14 / 49), tt / ss | PM ≥ 60° | **passed**: DM 74.6 / 79.1°, CM 71.9 / 76.6° | `isense-stb-c14-20261021r2` |
| Joint path with r1_safe (path fixture, both channels), tt / ss_cold / ff_hot | centres within 0.05 LSB and delays within 20 ns of revision 1 | **passed**: max \|Δ centre\| 0.011 LSB, max \|Δ delay\| 1.8 ns; OC trip 139.8 / 157.8 / 130.4 ns (< 300 ns); max \|centre error\| 0.051 LSB; 0 cross-channel glitches | `../r1_safe/sim/results/safe-joint-20261021r2/` vs `safe-joint-20261020-r3b` |
| Regression list (below), 21 revision-1 rows | as revision 1 | **passed**: every row re-run, no row fails | `sim/results/summary-20261021r2.json` |
| MC of the CM-to-differential error after AZ; AZ with noise folding; mismatch spread of the loop gain; channel b and the second comparator pair in the `stb` fixture | — | **not run** | — |
| Slow CMFB path: start-up time and recovery after a large CM disturbance (power-up, overload) | — | **not run** (estimate: slow-path time constant a few µs) | — |
| Real VREF/VCM/IBIAS sources, level-shifter timing, pads | — | **not run** | — |
| Layout, DRC, LVS, PEX | — | **not run** | — |

### Regression list (every revision-1 pass; re-run on the frozen revision-2 netlist)

Rule (as r1_afe): a revision is not done until every row is re-run and still passes. Run ids end in `-20261021r2`.

| # | Revision-1 row | Criterion | Revision 1 | Revision 2 | Status |
| --- | --- | --- | --- | --- | --- |
| 1 | Settling to ±0.5 % after the 100/120 mV edges, 5 corners (`isense-step`) | ≤ 300 ns | 206.4 ns | 208.4 ns | passed |
| 2 | Settling 0 → −20 mV small step | recorded | 285.7 ns | 293.8 ns | recorded (6.2 ns from 300 ns, see open issue 3) |
| 3 | Overload ±200 mV for 300 ns, recovery | recorded | 132–184 ns | ≤ 203.6 ns | recorded |
| 4 | Output nodes ≤ VDD incl. overload | ≤ 1.32 V | 1.310 V | 1.309 V | passed |
| 5 | Closed-loop bandwidth, peaking, 5 corners (`isense-noise`) | ≥ 1 MHz | 9.10 MHz min, 0 dB | 9.12 MHz min, 0 dB | passed |
| 6 | Residual offset after AZ, MC tt 50 (`isense-mc`) | ≤ 100 µV | σ 16.2, worst 35.5 µV | σ 13.2, worst 36.6 µV, 50/50 | passed |
| 7 | Residual offset after AZ, MC ss 125 °C 30 / ff −40 °C 30 (`isense-mc-ssff`) | ≤ 100 µV | worst 42.7 / 48.2 µV | worst 27.9 / 29.1 µV, 60/60 | passed |
| 8 | Gain, 5 corners (`isense-dc`) | 14 ± 0.1 % | 13.9999–14.0076 | 14.0011–14.0084 | passed |
| 9 | INL −20…100 mV | report | ≤ 0.023 % | ≤ 0.025 % | passed |
| 10 | Pedestal | report | 40.307–40.342 mV | 40.307–40.342 mV | recorded |
| 11 | Pedestal at Kelvin CM −0.1 / +0.1 V (tt) | shift ≤ 2 µV vs CM 0 | 1.1 / 1.4 µV | 1.1 / 1.2 µV | passed |
| 12 | Noise at 1 MHz / 10 kHz–5 MHz (worst corner) | recorded | 37.3 nV/√Hz / 80.3 µV | 37.3 nV/√Hz / 80.3 µV | recorded |
| 13 | Supply / CM rejection at 1 MHz | recorded | −71.6 / −69.4 dB | −71.6 / −69.4 dB | recorded |
| 14 | AZ loop return ratio, 5 corners (`isense-azloop`) | PM ≥ 45° | 92.8° | 77.2° | passed |
| 15 | Hold droop, mismatch bound, 125 °C / 150 °C (`isense-droop`, `-150C`) | ≤ 50 µV | 0.146 / 0.952 µV | 0.146 / 0.952 µV | passed |
| 16 | Main DM loop, normal, 5 + 2 corners (`isense-stb`) | PM ≥ 60°, GM ≥ 10 dB | 72.2° / 17.3 dB | 71.9° / 17.2 dB | passed |
| 17 | DM cross-check at the input gates | equal | within 0.05° | within 0.03° | passed |
| 18 | AZ servo, AZ closed (`isense-stbaz`) | PM ≥ 60° | 92.6° | 77.4° | passed |
| 19 | Load sensitivity and comparator-state runs (`isense-stb-load28`, `isense-stb-c14`) | recorded / PM ≥ 60° | DM 72.5°, CM 37.2° | DM 72.0°, CM 70.6° | passed |
| 20 | Shunt step 0 → 100 mV, 10 ns edge, joint load (`isense-stbstep`) | ≤ 300 ns, ≤ 1 overshoot | 102 / 205 ns, 0 | 93 / 208 ns, 0 | passed |
| 21 | Joint path with r1_safe: centres, simultaneous vs staggered, delays, kickback (`safe-joint`) | ≤ 0.5 LSB, < 300 ns, 0 glitches | 0.052 LSB, 156 ns | 0.051 LSB, 158 ns, Δ ≤ 0.011 LSB / 1.8 ns | passed |

Rows that lost margin: AZ servo PM (−15°, still 17° above its limit) and the 0 → −20 mV small-step settling (+8 ns).

### Area and current (revision 2)

| Item | Revision 1 | Revision 2 | Basis |
| --- | --- | --- | --- |
| Device area per channel | 8304 µm² | **10 476 µm²** (+2172, +26 %): MIM 3064 (+1296, `XCI`), thick MOS 1857 (+701: slow-path pair and mirror, cascodes), `rppd` 5158 (+100, degeneration), `rhigh` 375 (+75, hold resistors) | `python3 schematic/area.py schematic/r1_isense.spice r1_isense_ch` (estimated, not a layout) |
| Both channels | 16 608 µm² | 20 952 µm²; with the layout factor 3–4: 0.063–0.084 mm² (0.031–0.042 mm² per channel; target ≈ 0.04 mm²) | estimated |
| IDDA / IDD per channel, tt | 170.1 / 406.9 µA | 170.9 / 403.6 µA (slow path + 0.6 µA) | simulated, `isense-step-20261021r2` |
| IDDA / IDD per channel, ss 125 °C / ff_hot | 212.9 / 501.8; 225.2 / 568.6 µA | 213.8 / 495.9; 226.2 / 567.3 µA | simulated |

### Open issues (revision 2)

1. **Slow CMFB path dynamics not verified at large signal.** The slow path settles in microseconds (tail ≈ 0.6 µA, `XCI` 1.9 pF).
   Its start-up after power-up and its recovery after a large CM disturbance (overload, AZ edges at extreme duty) are
   **not run**. The DM output does not depend on it at first order, but the ADC sees the CM error until it settles.
2. **Slow-path range.** At ss 125 °C the trim node `vint` spanned 0.30–0.95 V over 30 MC samples with the slow-path mirror
   at w 2 µm (candidate `r2a`, 2 samples clipped, `dev-r2-mcvint-01`). With w 8 µm all 110 samples pass, but the `vint`
   range per corner was not reduced from the waveforms. A wider sample count or a range check per corner is open.
3. **Small-step settling 0 → −20 mV at ss 125 °C is 293.8 ns** (revision 1 285.7 ns). It is a recorded row, not a
   criterion, but it is 6 ns from 300 ns. If it becomes a criterion, it needs a DM change (not in this revision).
4. **AZ servo PM fell 92.6° → 77.4°** because of the 50 kΩ hold resistors. A smaller resistor trades AZ-closed CM margin
   (the AZ-closed CM loop has 12° of margin to spare) against AZ servo margin.
5. Area +26 %; the 1.9 pF integrating cap is the largest part. A MOS cap or a smaller cap with a lower slow-path gm is a
   layout-phase option (not screened).
6. Revision-1 open issues 1 (noise), 3 (AZ timing), 4 (Kelvin CM), 5 (ideal sources), 7 (r1_safe drive) are unchanged.
   Open issue 2 (output CM 0.56–0.59 V) and 6 (CMFB margin) are **closed** by revision 2. The INTERFACES.md row
   "isense → ADC mux, ≈ 0.57 V CM" can change to 0.60 V (coordinator action; this track did not edit INTERFACES.md).

### Failures and mistakes (revision 2)

| # | What happened | Class | Evidence |
| --- | --- | --- | --- |
| 1 | The first candidate after the margin fix was source degeneration only. It met the margins (tt CM PM 68.4°), and only the MC of the output CM (a check revision 1 never had) showed σ 62.0 mV (41.0 mV with less degeneration). The cost of a lower DC CM gain under mismatch was not estimated before the screen. | estimation | `dev-r2-13`, `dev-r2-14` |
| 2 | The lag network at the sink gates made the margin worse (tt CM PM 41.5° → 28.7° normal, 22.4° AZ closed): the rhigh resistances with the sink gate capacitance placed a pole near the crossover. | estimation | `dev-r2-05` |
| 3 | Two-path variant 1 (current steering): `XMI` too weak, slow OTA at its rail (MC output CM 0.68–0.82 V, tt CM PM 54.0°); then too fast (tt CM PM 41.2°). A degenerated slow pair added resistor-mismatch offset (MC output-CM σ 27.8 mV). | estimation | `dev-r2-15`, `-16`, `-17` |
| 4 | Two-path variant 2 with the integrating cap to `vss`: a `vcm` step reached the output only through the slow path (not settled to 2 % within the 1.1 µs window). The `vcm`-step path was not considered when the trim point was chosen. | planning | `dev-r2-22` |
| 5 | The degenerated fast pair left too little tail headroom at ss 125 °C; the fast path took only 73 % of a CM step (settling 285–846 ns). Then the slow path was too fast and its tail failed the 2 % band (182–490 ns) until its gm was lowered. Found in the CM-step transient, not in the loop gain. | verification-gap | `dev-r2-24`, `-25`, `-26`, `dev-r2-cmdbg-01` |
| 6 | **Regression found after freezing.** Candidate `r2a` (slow-path mirror w 2 µm) failed the new MC output-CM row at ss 125 °C (2/30 samples, slow path at the end of its range, `vint` 0.30 V). The screens had run the MC at tt only. The full candidate-`r2a` campaign is kept with the suffix `20261021r2a` (labelled superseded in each `run.json`); revision 2 of record widens the mirror to w 8 µm and the campaign was re-run. | verification-gap | `sim/results/*-20261021r2a/`, `summary-20261021r2a.json`, `dev-r2-mcvint-01`, `dev-r2-29` |
| 7 | The first restart of the campaign was stopped after one minute to correct a stale comment in the generator (the netlist hash would have changed after the evidence); the partial step run is kept as `<G1_RESULTS_ROOT>/r1_isense/isense-step-20261021r2-aborted/`. Orphaned ngspice jobs needed a second, explicit `kill` by PID. | process-hygiene | campaign log `campaign-20261021r2-aborted.log` |
| 8 | `gen_tb_isense_stb.py` edited the CMFB gate with the literal `XMF1 vcmfb vcms ctail`; the degeneration variant renamed the source node and the generator aborted after the screen directory existed. The empty directory was removed inside the results root (path printed after, not before, the removal). | tooling | `dev-r2-04` |
| 9 | `dev_r2.py` read the wrong level of `run.json` (all margins printed as "-"), and the MC corner list used "," inside a ","-separated state list. Fixed, re-reported without re-running. | tooling | `dev-r2-01`, `dev-r2-15` |
| 10 | `run_deck.py` used `subprocess.run(capture_output=…)`, which Python 3.6 does not have; the ngspice version in 107 `run.json` files was back-filled from one `flow/run.sh ngspice -v` call after the runs (same image). Fixed for later runs. | tooling | `run.json` field `ngspice_version` |
| 11 | The task lists "output CM 0.6 V ± 30 mV" among the revision-1 passes. Revision 1 was 0.559 V at ss_cold and ssx (outside) and had no such row. Taken as a revision-2 criterion; revision 2 meets it. | spec-ambiguity | `isense-dc-20261020-r1` |
| 12 | "Settled within 300 ns" has no tolerance. Taken as ±2 % of the CM step (the tolerance of the revision-1 analyzer); a pass/fail criterion was added to `analyze_stbcm.py`. | spec-ambiguity | `sim/analyze_stbcm.py` |
| 13 | ssx/ffx are defined in r1_afe for one supply. Here both supplies go to the same extreme (ssx 3.6 / 1.32 V, −40 °C; ffx 3.0 / 1.08 V, 125 °C). | spec-ambiguity | `sim/run_deck.py` CORNERS |
| 14 | The regenerated decks `tb_isense_stb*.cir` and `tb_isense_azloop.cir` now hold the revision-2 deck-local copy; the revision-1 deck copies exist only in the raw run directories. | process-hygiene | `<G1_RESULTS_ROOT>/r1_isense/isense-stb-20261021-r1/` |
| 15 | The screens shared CPUs 109–111 with one replay run for about 4 minutes (4 jobs on 3 CPUs); wall time only. | planning | `dev-r2-mcvint-01` |
| 16 | `run_deck.py` wrote the `--pre` deck path as given (absolute results-root path) into `run.json` field `prerun`; 31 `run.json` files carried a machine path. Fixed in `run_deck.py` (`rel()`), the files were rewritten to the `<G1_RESULTS_ROOT>` placeholder. Found by the final path scrub. | process-hygiene | `run.json` field `prerun.*.deck` |

### Built against (revision 2)

| Item | Version | How established |
| --- | --- | --- |
| PDK | IHP-Open-PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` | checked by `flow/run.sh` before every run |
| ngspice | ngspice-46 (OSDI PSP 103) | `flow/run.sh ngspice -v`, recorded in each `run.json` (`ngspice_version`) |
| Container | `tapeoutbench-eda:latest`, id `sha256:ddeb6957…` | checked by `flow/run.sh` |
| CPU set | 109–111 (`G1_CPUSET`) | `run.json` field `cpuset` |

### Files (revision 2)

| Path | Content |
| --- | --- |
| `schematic/r1_isense.spice` | revision-2 netlist of record (generated) |
| `schematic/r1_isense_rev1.spice` | revision-1 netlist (all revision-1 runs) |
| `schematic/r1_isense.spice.tmpl`, `schematic/gen_isense.py` | template with the revision-2 options; defaults = revision 2; `gen_isense.py BFC=0 FDC=0 RDG=0 RH=0 TP=0 MS=7 MCS=2` reproduces revision 1 (comment lines differ) |
| `sim/run_deck.py` | **shared runner** of r1_isense and r1_safe (the two hand-edited copies merged; `../r1_safe/sim/run_deck.py` is a shim); new: corners `ssx`/`ffx`, absolute deck paths, `--netlist`, ngspice version and results-root include hashes in `run.json` |
| `sim/gen_tb_isense_stb.py` | new deck `tb_isense_stbazi.cir` (az = 1, azh = 0); `R1_NET`/`R1_OUTDIR` for variants |
| `sim/analyze_stb.py`, `sim/analyze_stbcm.py`, `sim/analyze_mc.py` | intermediate state; CM-step pass/fail; MC output CM |
| `sim/dev_r2.py` | development screens (variant netlist → three states, CM step, MC) |
| `sim/campaign_20261021r2.sh`, `sim/report_r2.py` | regression campaign; reduction to `sim/results/summary-20261021r2.json` |

Reproduce from the repository root: `G1_RESULTS_ROOT=<bulk results root>; export G1_RESULTS_ROOT`, then
`sh designs/r1-joint/blocks/r1_isense/sim/campaign_20261021r2.sh` and `python3 designs/r1-joint/blocks/r1_isense/sim/report_r2.py`.

---

## Revision 1 record (superseded by revision 2)

The sections below describe revision 1 (`schematic/r1_isense_rev1.spice`) and are kept unchanged. Where they give the
output CM as about 0.57 V, the CMFB share as 2/3 of the sinks, or CM margins below 60°, revision 2 (above) replaces them.

State (2026-10-21; follow-ups 2026-10-20 and the `stb` suite of 2026-10-21): **schematic level, simulated.** No layout, no extraction. All numbers below are
**simulated** (ngspice-46, pinned PDK), at schematic level, with ideal reference sources (marked in each
deck). Nothing is measured.

## What it is

Each channel is a resistive difference amplifier around a fully differential two-stage OTA, with an
input-referred pedestal and an auto-zero (AZ) loop.

```
OUTP - OUTN = G * ((ISP - ISN) - VPED)        G = RF/RIN = 14,  VPED = VREF/26 = 40.38 mV at VREF = 1.05 V
-20 mV .. +100 mV  ->  -0.845 V .. +0.836 V differential, output common mode about 0.57 V (VCM input 0.6 V)
```

- Input: differential Kelvin pins ISx_P/ISx_N through RIN = 4 kΩ (`rppd` unit w = 2 µm, l = 30.8 µm). RF = 14 units,
  pedestal arms RP = 26 units. All three are made of one unit, so G and VPED/VREF are unit ratios.
- Stage 1 (VDDA 3.3 V): thick-oxide PMOS input pair (w 40 / l 1 µm, 20 µA each, bulk = tail) that works with an input
  common mode near 0 V; folded cascode; CMFB on 2/3 of the variable part of the folding sinks.
- Stage 2 (VDD 1.2 V core): thick-oxide NMOS common source, thin-oxide PMOS current-source load, Miller CC 0.22 pF
  with a nulling resistor. **OUTP/OUTN cannot rise above VDD (≤ 1.32 V).** The outputs are therefore safe for the
  thin-oxide ADC multiplexer and comparator inputs, also in overload (G1 lesson: G1 spec §4 "Absolute maximum shunt
  voltage", where a 3.3 V output drove a thin-oxide comparator input to 1.644 V).
- Auto-zero of the whole channel. AZ runs only while the shunt carries no current (low-side FET off, outside dead
  time). During AZ (`az`): the output ends of both RF arms move from the outputs to VCM, and both pedestal arms open.
  During `azh` (inside `az`): two 1 pF hold caps follow the stage-1 outputs, and an auxiliary PMOS pair
  (gm ≈ gm1/12) nulls the stage-1 output. The stored correction cancels the OTA offset **and** the resistor-network
  error at Vod = 0 (0.6 V output common mode through mismatched RF/RIN ratios, about 150 µV σ). An OTA-only AZ left
  ±200 µV (development run `dev-mc-01`, failed).
- AZ phases `az_lv`, `azh_lv` are 1.2 V logic from r1_ctrl, level-shifted in the block. Sequence: `azh` falls at
  least one clock cycle (33 ns) before `az`. The output is invalid during AZ and for the recovery time after it.
  r1_safe must blank over that window.

Interface assumptions (to confirm with r1_adc and r1_bgr):

| Item | Assumption in this step |
| --- | --- |
| ADC input | differential, 1.2 V domain, 2.4 Vpp FS; this block uses ±0.845 V (70 % of FS) so that both outputs stay in 0.15–1.02 V at VDD = 1.08 V |
| ADC load | 2 pF per output (T/H sampling cap through the multiplexer) |
| VCM | 0.6 V from the r1_adc reference (ideal source here); it sinks or sources ≈ 10 µA per RF arm during AZ |
| VREF | 1.05 V, **buffered** (ideal source here); load 2 × 4 µA per channel (pedestal arms) |
| IBIAS | 5 µA PTAT (5 µA × T/300 K) per channel from the r1_bgr PTAT branch (ideal source here) |
| AZ window | ≥ 2.05 µs AZ per PWM period while the low-side FET is off, ≥ 100 ns before the sample strobe |

Why G = 14 and not 20 ("100 mV → about 2.0 Vpp"): at VDD = 1.08 V the thin-oxide load needs ≈ 60 mV of headroom,
and the output common mode is 0.57 V. A gain of 14 keeps the full −20…+100 mV range linear at ss/125 °C/1.08 V.
At G = 14 with a 40 mV pedestal, the 120 mV range maps to 1.68 Vpp (0.5 bit of ADC range unused).

## Status

| Check | Status | Evidence |
| --- | --- | --- |
| Settling to ±0.5 % within 300 ns after 0→100 mV, −20→100 mV, 100→0 and 100→−20 mV edges, 2 pF load, tt/ss/ff/ss_cold/ff_hot | **passed**: worst 206 ns (ss 125 °C, 1.08/3.0 V) | `sim/results/isense-step-20261020-r1/` |
| Closed-loop bandwidth ≥ 1 MHz, 5 corners | **passed**: 9.1–15.2 MHz, no peaking | `sim/results/isense-noise-20261020-r1/` |
| Residual offset after AZ ≤ 100 µV, 50-sample mismatch MC (`mm_ok=1`), tt 27 °C | **passed**: 50/50, σ 16.2 µV, worst 35.5 µV (raw before AZ σ 2.57 mV) | `sim/results/isense-mc-20261020-r1/` |
| Gain, pedestal, INL over −20…+100 mV after AZ, 5 corners | **passed** (report): G 13.9999–14.0076, INL ≤ 0.023 % of span, pedestal 40.307–40.342 mV | `sim/results/isense-dc-20261020-r1/` |
| Same at Kelvin common mode −0.1 V and +0.1 V (tt) | **passed** (report): pedestal moves ≤ 1.2 µV | `isense-dc-cmm100-…`, `isense-dc-cmp100-…` |
| Negative excursion: −20 mV linear; −200 mV and +200 mV for 300 ns, recovery to ±0.5 % | **passed** (report): in range linear; recovery 132–184 ns | `isense-step-20261020-r1` |
| Output nodes ≤ VDD in all runs, including overload | **passed**: max 1.310 V at VDD 1.32 V (ff_hot) | `isense-step-20261020-r1` |
| Noise (continuous time, AZ held), 5 corners | run (report): 25–37 nV/√Hz white, 1/f corner ≈ 70 kHz, 53–80 µV rms in 10 kHz–5 MHz | `isense-noise-20261020-r1` |
| Residual offset after AZ ≤ 100 µV, mismatch MC at ss 125 °C (30 samples, seed 4) and ff −40 °C (30 samples, seed 5) | **passed**: ss 30/30, σ 15.6 µV, worst 42.7 µV (raw σ 3.14 mV); ff 30/30, σ 23.3 µV, worst 48.2 µV (raw σ 2.46 mV) | `sim/results/isense-mc-ssff-20261020-r1/` |
| MC of the CM-to-differential error after AZ | **not run** | — |
| AZ hold droop over one 50 µs PWM period at zero current (gmin 1e-15), tt / ss 125 °C / ff_hot 125 °C, and ss / ff at 150 °C | **passed** (limit 50 µV input-referred): output drift ≤ 0.004 µV input-referred; hold-node droop ≤ 1.75 µV (125 °C), ≤ 11.4 µV (150 °C), common to both caps; mismatch bound (one cap droops, the other not, /12 aux gm ratio) ≤ 0.15 µV (125 °C), ≤ 0.95 µV (150 °C) | `sim/results/isense-droop-20261020-r1/`, `sim/results/isense-droop-150C-20261020-r1/` |
| AZ with noise folding (sampled noise) | **not run** (estimate: hold-cap kT/C 64 µV per node → ≈ 7 µV input-referred) | — |
| Auto-zero loop gain (return ratio during AZ hold, loop broken at the aux-pair gates), 5 corners | **passed** (limit 45°): differential phase margin 92.8–96.5°, unity gain 0.74–1.14 MHz, DC loop gain 47.9–56.9 dB, gain margin 29.6–33.4 dB; common mode: loop gain ≤ −47 dB at all frequencies (the aux pair rejects CM; no CM AZ loop) | `sim/results/isense-azloop-20261020-r1/` |
| Loop gain (Tian double injection, as r1_afe) of the main differential loop, normal state (az = azh = 0), break at the OTA outputs, shunt 0 / +100 / −20 mV, tt, ss 125 °C 3.0 V, ff −40 °C 3.6 V, sf, fs; load = joint path fixture of r1_safe (2 pF per output, OC and NEG comparators of the channel) | **passed** (PM ≥ 60°, GM ≥ 10 dB): worst PM / GM per corner tt 74.8° / 18.7 dB, ss 79.0° / 21.4 dB, ff 72.2° / 17.3 dB, sf 74.7° / 18.6 dB, fs 75.0° / 18.8 dB (worst at 0 mV); unity gain 2.2–9.6 MHz | `sim/results/isense-stb-20261021-r1/` |
| Same loop, cross-check with the break at the input-pair gates | **passed**: PM and GM equal the output break within 0.05° / 0.2 dB, all 5 corners | same |
| Common-mode / CMFB loop, normal state (output break, symmetric injection: CMFB path plus the CM path through the input pair and the network), same corners, levels and load | **failed** (PM ≥ 60° not met in any corner; GM ≥ 10 dB not met at ff): worst PM / GM tt 41.5° / 11.3 dB, ss 49.5° / 13.8 dB, ff 35.5° / 9.7 dB, sf 41.3° / 11.2 dB, fs 41.7° / 11.4 dB (worst at 0 mV; at +100 / −20 mV tt 51.6° / 52.3°, ss 66.3° / 66.9°); unity gain 6.5–20.5 MHz | same |
| CMFB path alone (break at the sense node, other loops closed) | informational (not a valid Nyquist break when the input-pair CM loop is also > 1): equals the CM loop above within 0.1° | same |
| Input-pair CM path (symmetric injection at the input gates) | **not applicable**: loop gain ≤ −49 dB at all frequencies (the CM loop is the CMFB) | same |
| CM-step cross-check (VCM reference +20 mV after AZ, output common-mode overshoot) | informational, agrees with the loop-gain ranking: overshoot tt 36 %, ss 25 %, ff 44 %, sf 37 %, fs 36 % (2nd-order equivalent PM 34–44°) | `sim/results/isense-stbcm-20261021-r1/` |
| Loop gain with the auto-zero closed (az = azh = 1): AZ servo (break at the aux-pair gates), 5 corners | **passed**: PM 92.6–96.5° (tt 95.1, ss 92.6, ff 96.5, sf 95.1, fs 95.0), GM 30.2–33.5 dB, unity gain 0.83–0.94 MHz (the AZ loop result of 2026-10-20 reproduced with the new method within 0.4° at tt, ss, ff) | `sim/results/isense-stbaz-20261021-r1/` |
| Loop gain with the auto-zero closed: CM / CMFB loop (outputs free, RF arms at VCM) | **failed**: PM 21.4–41.5° (tt 29.7, ss 41.5, ff 21.4, sf 29.7, fs 29.7), GM 8.6–19.9 dB (ff 8.6 dB fails GM); unity gain 10.7–15.1 MHz | same |
| Loop gain with the auto-zero closed: differential output break; CM path of the aux pair | **not applicable**: loop gain ≤ −142 dB (no external differential loop while the RF arms are at VCM); aux-pair CM ≤ −44 dB | same |
| Load sensitivity: ADC load 100 Ω + 2.8 pF + 0.2 pF wiring per output (INTERFACES.md CDAC), normal state, tt and ss | run: DM loop PM 72.5° / 77.3°, CM loop 37.2° / 45.8° (tt / ss; 4° lower than with 2 pF) | `sim/results/isense-stb-load28-20261021-r1/` |
| Comparator-state sensitivity: both comparators at the calibration point (code 14 / 49), tt and ss | run: PM within 0.3° of the code-44 runs | `sim/results/isense-stb-c14-20261021-r1/` |
| Loop gain in the intermediate state az = 1, azh = 0 (hold open, outputs free); mismatch spread of the loop gain; channel b and the second comparator pair in the fixture | **not run** (the CMFB loop of the AZ-closed state is the same loop without the AZ servo) | — |
| Step 0 → 100 mV shunt, 10 ns edge, after AZ, joint load fixture, tt and ss 125 °C | **passed**: settling to ±0.5 % in 102 ns (tt) and 205 ns (ss) from the edge start, no overshoot (peak 0.000 %), 0 overshoots (limit 1) | `sim/results/isense-stbstep-20261021-r1/` |
| Supply rejection (report) | run: VDDA→Vod −72…−85 dB, VDD→Vod ≤ −83 dB at 1 MHz (nominal, no mismatch) | `isense-noise-20261020-r1` |
| Real VREF/VCM/IBIAS sources, level-shifter timing, pads (`dantenna`) | **not run** (ideal sources; pad diodes left out at block level per the ngspice pad-diode note) | — |
| Layout, DRC, LVS, PEX | **not run** | — |

## Numbers (simulated, schematic level)

| Quantity | tt 27 °C | ss 125 °C | ff −40 °C | ss −40 °C | ff 125 °C |
| --- | --- | --- | --- | --- | --- |
| Supplies VDDA / VDD (V) | 3.3 / 1.2 | 3.0 / 1.08 | 3.6 / 1.32 | 3.0 / 1.08 | 3.6 / 1.32 |
| Settling 0→100 mV, ±0.5 % (ns) | 98 | 203 | 65 | 105 | 119 |
| Settling, worst 100/120 mV edge (ns) | 99 | 206 | 66 | 106 | 123 |
| Settling 0→−20 mV (small step, ns) | 121 | 286 | 75 | 126 | 162 |
| −3 dB bandwidth (MHz) | 12.0 | 9.1 | 15.2 | 10.4 | 12.6 |
| Gain (LSQ fit) | 14.008 | 14.007 | 14.005 | 14.007 | 14.000 |
| Pedestal error vs VREF/26 (µV) | −54 | −74 | −44 | −43 | −78 |
| INL (% of the −20…100 mV output span) | 0.004 | 0.021 | 0.002 | 0.002 | 0.023 |
| Output common mode (V) | 0.570 | 0.582 | 0.565 | 0.559 | 0.588 |
| Input noise at 1 MHz (nV/√Hz) | 30 | 37 | 25 | 27 | 36 |
| Input noise 10 kHz–5 MHz (µV rms) | 65 | 80 | 53 | 57 | 76 |
| IDDA (3.3 V) / IDD (1.2 V) per channel (µA) | 170 / 407 | 213 / 502 | 143 / 340 | 131 / 292 | 225 / 569 |

Mismatch MC (50 samples, tt): raw offset before AZ σ 2.57 mV (−5.66…+8.51 mV); residual after AZ mean −0.4 µV,
σ 16.2 µV, range −34.0…+35.5 µV; pedestal 40.32 mV σ 0.10 mV; gain 14.012 σ 0.028.
At ss 125 °C (30 samples): raw σ 3.14 mV (worst 7.56 mV), residual σ 15.6 µV (worst 42.7 µV), pedestal σ 0.11 mV,
gain σ 0.032. At ff −40 °C (30 samples): raw σ 2.46 mV (worst 4.96 mV), residual σ 23.3 µV (worst 48.2 µV),
pedestal σ 0.10 mV, gain σ 0.030.

Auto-zero loop (return ratio during AZ hold): differential DC loop gain 56.4 dB (tt), 54.6 (ss), 55.5 (ff), 56.9
(ss_cold), 47.9 (ff_hot); unity gain 0.87 / 0.96 / 0.89 / 0.74 / 1.14 MHz; phase margin 95.3 / 92.8 / 96.5 / 95.4 / 94.1°.
The closed AZ loop time constant is about 1/(2π · 0.74 MHz) ≈ 0.22 µs, so the 2.0 µs `azh` phase is ≥ 9 time constants.

The pedestal error (−43…−78 µV systematic, 0.10 mV σ under mismatch) is not an offset of the amplifier: AZ
removes everything except the pedestal itself, and the ADC reads the pedestal at zero current. A host or r1_ctrl
zero-current reading per part therefore removes it. Its drift between AZ cycles is the resistor-ratio drift only.

Power per channel (tt): 0.56 mW from VDDA + 0.49 mW from VDD ≈ 1.05 mW (G1 sense: 3.6 mW).

## Area (device area, from `schematic/area.py`)

| Item | µm² per channel |
| --- | --- |
| `rppd` (2 + 28 + 52 units of 62 µm²) | 5058 |
| MIM (2 × 1 pF hold, 2 × 0.22 pF CC, 2 × 64 µm² CM bypass) | 1768 |
| thick-oxide MOS | 1156 |
| `rhigh` CM sense | 300 |
| thin-oxide MOS | 21 |
| **Total** | **8304 (0.0083 mm²)** |

With an analog layout factor of 3–4, the estimate is 0.025–0.033 mm² per channel (target ≈ 0.04 mm²; G1 cell
0.092 mm²). The estimate is not a layout.

## Open issues

1. **Noise.** 30 nV/√Hz white (tt) gives about 1.5 ADC LSB rms (input-referred LSB 42 µV) over 5 MHz. Options:
   more input-pair current, longer folding sinks, digital averaging of two samples. No noise target is specified;
   r1_adc and the system budget must set one.
2. **Output common mode** is 0.56–0.59 V, not 0.60 V (CMFB pair offset). This costs 10–40 mV of bottom headroom.
3. **AZ dependency on the gate timing.** AZ is valid only while the shunt current is zero. r1_gate/r1_ctrl must give
   an AZ window inside the high-side on-time, outside dead time, and r1_safe must blank the comparators over AZ +
   ≈ 100–200 ns. At duty cycles with no such window (low-side on ≈ 100 %), the hold caps must keep the correction.
   Droop (simulated, model leakage only): worst-case mismatch bound ≤ 0.95 µV input-referred per 50 µs at 150 °C,
   so about 100 periods (5 ms) without AZ stay within a 100 µV budget at 150 °C (estimate from the bound).
   r1_safe revision 3 also uses the zero-current window after AZ for its calibration search (r1_safe README).
4. **Kelvin common-mode change between AZ and sampling** converts through RF/RIN mismatch (estimate: σ ≈ 3.7 µV per mV
   of CM change). Board rule proposal: tie chip VSS close to the shunt ground side.
5. **Ideal sources.** VREF must be buffered (pedestal arms are 104 kΩ). VCM must sink/source the RF-arm current during
   AZ. IBIAS is assumed PTAT.
6. **CMFB loop margin (failed, 2026-10-21).** A CMFB share of 8/3 of the folding current oscillated at 46 MHz
   (development run `dev-step-11`); the share of 2/3 is stable in all corners, but the loop-gain run shows a phase
   margin of 35–50° in normal mode and 21–42° with the auto-zero closed (criterion 60°, GM 10 dB), with a crossover
   (6.5–20 MHz) above the differential crossover. A CM-step transient confirms the ringing (overshoot 25–44 %). The
   netlist of record is unchanged. Candidates (not simulated): smaller CMFB pair or tail current (lower CM gain), more
   CM-sense bypass, or a CM-only Miller part as in r1_afe revision D. The differential loop and the AZ servo pass.
7. **r1_safe drive.** The sense outputs drive the four r1_safe comparator gates directly (thick PMOS, no DC load).
   The joint deck `r1_safe/sim/tb_safe_joint3.cir` checks thresholds and delay through the real sense output.

## Built against

| Item | Version | How established |
| --- | --- | --- |
| PDK | IHP-Open-PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` | checked by `flow/run.sh` before every run |
| ngspice | ngspice-46 (OSDI PSP 103, `r3_cmc`) | `flow/run.sh ngspice -v` banner, 2026-10-20; `sim/.spiceinit` loads the OSDI models |
| Container | `tapeoutbench-eda:latest`, id `sha256:ddeb6957…` | checked by `flow/run.sh` |
| xschem / KLayout / LibreLane / CACE | not used in this step | — |

## Files and reproduction

- `schematic/r1_isense.spice.tmpl` + `schematic/gen_isense.py` → `schematic/r1_isense.spice` (generated; sha256
  prefix `5db34e0a8f7c` for all evidence runs). `schematic/area.py` gives the device area.
- Decks: `sim/tb_isense_step.cir`, `sim/tb_isense_dc.cir`, `sim/tb_isense_mc.cir`, `sim/tb_isense_noise.cir`,
  `sim/tb_isense_droop.cir`, `sim/tb_isense_azloop.cir` (from `sim/gen_tb_isense_azloop.py`: a deck-local copy of
  `r1_isense_ch` with the AZ loop broken at the aux-pair gates);
  analyzers `sim/analyze_*.py`; runner `sim/run_deck.py` (corner substitution, `flow/run.sh`, `run.json`).
- Campaign: `sh designs/r1-joint/blocks/r1_isense/sim/campaign_20261020.sh` from the repository root
  (CPU set 109–111); follow-ups (ss/ff MC, AZ loop gain, droop): `sim/campaign_20261020_fu.sh`. A `TEMP` override
  (150 °C droop run) is recorded in `run.json` under `overrides`. Raw waveforms: `<G1_RESULTS_ROOT>/r1_isense/<run-id>/`.
- `sim/results/<run-id>/run.json` and `summary.json` per run. Runs named `dev-*` are development runs on earlier
  netlist states (their `run.json` holds the netlist hash). They are kept as a record, not as evidence; `dev-mc-01`
  to `dev-mc-03` (OTA-only AZ, failed) and `dev-step-06`/`dev-step-11` (CM loop unstable) are the failed designs.

## `stb` suite (2026-10-21, T4 follow-up c)

Decks are generated by `sim/gen_tb_isense_stb.py` from the netlist of record (deck-local copy `r1_isense_ch_stb` with
probe sources; the record is included unchanged): `tb_isense_stbpre.cir` (auto-zero on the channel alone, prints the
hold-cap voltages `HOLDVALS`), `tb_isense_stb.cir` (normal state; the hold caps are tied at DC to the post-AZ voltages by
1 GH, open for AC), `tb_isense_stbaz.cir` (AZ closed), `tb_isense_stbc14.cir` (comparators at the calibration point),
`tb_isense_stbstep.cir`, `tb_isense_stbcm.cir`. Analyzers `sim/analyze_stb.py`, `analyze_stbstep.py`, `analyze_stbcm.py`.
Runner: `sim/run_deck.py` with the new `--pre` option (pre-run deck, fills `@@VH1@@`/`@@VH2@@`), the corners `sf`, `fs`, and
`included_netlists` (sha256 of every `.include`d netlist) in `run.json`. Campaign: `sim/campaign_20261021_stb.sh`
(CPU set 109–110; the CM-step run was started by hand, command in its `run.json`). Netlists of record in every `stb`
`run.json`: r1_isense sha256 `5db34e0a8f7c…` and r1_safe `812f886dce2b…` (both match the records). Raw files:
`<G1_RESULTS_ROOT>/r1_isense/<run-id>/`. `dev-stb-01` is the first development run (kept, not evidence).
Criterion: PM ≥ 60° and GM ≥ 10 dB per loop, corner and shunt level (worst reported). Corners: tt 27 °C 3.3 V / 1.2 V,
ss 125 °C 3.0 V / 1.08 V, ff −40 °C 3.6 V / 1.32 V, sf and fs 27 °C at the tt supplies.

### Failures and mistakes (stb suite)

| # | What happened | Class | Evidence |
| --- | --- | --- | --- |
| 1 | The earlier statement "CMFB share 2/3 is stable in all corners" rested on transients only. The loop-gain run shows 35–50° (normal) and 21–42° (AZ closed). The 60° criterion fails for the CM loop; the netlist of record stays unchanged. | verification-gap | `isense-stb-20261021-r1`, `isense-stbaz-20261021-r1`, `isense-stbcm-20261021-r1` |
| 2 | The brief listed a CMFB, a main loop and an AZ loop, and the AZ loop was measured before (45° limit) with a 1 GH / 1 F break. Re-measured here with the Tian method at the stricter 60° limit; both agree within 0.4°. | planning | `isense-azloop-20261020-r1`, `isense-stbaz-20261021-r1` |
| 3 | First idea for the normal-state operating point was to tie each hold node to its stage-1 output by 1 GH. That closes the AZ servo at DC and removes the pedestal (output ≈ 0 V instead of −0.565 V). Found before the first run; replaced by a pre-run that supplies the post-AZ hold voltages. | numerical | `sim/tb_isense_stbpre.cir` |
| 4 | The generator's own assertion for the CM-step deck contradicted the deck text and aborted after the run directory was created; the rerun stopped with "run id exists" until the empty directory was removed. | tooling | development only |
| 5 | `r1_isense` and `r1_safe` each carry a private copy of `run_deck.py` (they differ in the `NET` handling only). The `stb` additions were applied to both by hand. Drift risk; a shared runner is the cleaner fix. | process-hygiene | `sim/run_deck.py` in both blocks |
| 6 | Not covered: the intermediate state az = 1, azh = 0, a mismatch spread of the loop gain, channel b. | verification-gap | status table |

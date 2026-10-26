# r1_adc post-layout simulation harness (T2, 2026-10-26)

All numbers are **simulated** (ngspice 46, PDK `84374023`, container `sha256:ddeb6957…`). Raw files:
`<G1_RESULTS_ROOT>/r1_adc/<run id>/`. Run records: `sim/post/runs/<run id>/run.json`. Result JSON: `sim/post/results/`.

## Files

| File | Content |
| --- | --- |
| `make_sim_netlist.py` | Builds the layout-mapped ngspice netlist from the contract `layout/r1_adc_netlist.py`: `r1_adc_lay` (ports = `TOP_PORTS`, same order; `[k]` → `_k`) and `r1_adc_lay_pr` (+ `vref vrefl` probe ports). It adds the comparator loads Cbp / Cbn (3 fF, not drawn) back. It merges identical parallel devices into m = count (`--no-merge` writes every drawn device). Parasitic hook: `--pex-slice`, `--pex-slice-b`, `--pex-top`, `--pex-flat` (mapping by net name; see the docstring) |
| `r1_adc_lay0.spice` | Layout-mapped netlist, no parasitics, merged (current contract: NDUMMY 82, `layout/r1_adc_decap.json`) |
| `r1_adc_lay0u.spice` | The same netlist without the merge |
| `merge_parallel.py` | Merges identical parallel instances of an extracted netlist. `r1_adc_post_rc_m.spice` and `r1_adc_post_c_m.spice` are merged copies of `pex/r1_adc_post_rc.spice` and `pex/r1_adc_post_c.spice` (layout lead; `pex/` is not edited) |
| `gen_post_decks.py` | Writes the wrapper `r1_adc5_post.spice`, the deck variants `tb_post_points.cir` and `tb_post_isa.cir` (from the r5 decks), and `points/win3.json` |
| `run_post.py`, `run_qpost.sh`, `jobs_*.txt` | Runner (r5 rules: one job, no resume, no resubmission, exit 1 on any failure) and job queues |
| `post_post.py` | Post-processing: `win` (n windows), `ref` (the unchanged `sim/r5/post_ref5.py`, segment files from `sim/post/results`), optional slice-port vectors and base reference values for RC netlists; `isa` / `first` (`sim/r5/post_t2.py` + comparison with the pre-layout run), `pre` (writes `pre_values.json`) |
| `make_sp_netlist.py`, `r1_adc_post_rc_m_sp_tt.spice`, `r1_adc_post_rc_m_sp_ss125.spice` | R2-4 base netlists for the RC netlist (H12): inside `r1_adc_lay_pr` the slice vref / vrefl pins are driven by ideal DC sources at the buffer-OP slice-port values (`post-op-tt-rc3`, `post-op-ss125-rc3`); everything else as extracted |
| `sep_ref.py` | Diagnostic: reference droop at the follower source and at the slice port in an R2-4 buffer run |
| `net_reff.py` | Diagnostic: effective resistance from the main node to the port nodes of a net |
| `make_synth_pex.py`, `scratch/` | Synthetic parasitic files (test input only). `scratch/` is regenerable and is not evidence: do not commit it |

## Wrapper interface

`r1_adc5_core_lay` has the pins of `r1_adc5_core` in the same order, plus `vbg nb vdda`. A deck therefore changes only
the cell name and appends `vbg nbr vdda`. Inside the wrapper:

1. `XL` is `r1_adc_lay_pr` (any netlist that defines it: layout-mapped or extracted). `XSAR` is `r1_sar5_logic` from the netlist of record, connected through the `sar_*` nets.
2. `clk` = `clk30`, `vref_in` = `vbg`, `ibias` = `nb`, `vss` = `gnd`.
3. `vrefa` = `vref` and `vrefla` = `vrefl` of the laid-out buffer. `vrefb` and `vreflb` are E-source copies (no load). A deck must not drive `vrefb` or `vreflb`.
4. The 35 unconnected checklist pins and `vcm`, `vcm2` connect to gnd through 1 kΩ (a stand-in for their drivers).

Reference modes of `run_post.py` (`--core lay`):

- `lay`: bandgap model (Vbgi + TRNOISE, NT 47.3 ns, Rbg 190 kΩ into `vref_in`) and Ibref 5 µA into `ibias`. The 10 pF filter and the buffer are in the layout netlist.
- `lay-ideal`: ideal sources on `vrefa` and `vrefla`, with the buffer still connected. The bandgap DC is 50 mV below the forced value, so the error amplifier rails. This mode gives the R2-4 base runs and the static windows.

Cores: `rec` = `r1_adc5_core` (netlist of record, full core), `recfast` = `r1_adc5_core_fast`.

## Decisions (recommended option, recorded)

1. The R2-4 base run forces the ideal reference at the `vref` / `vrefl` port node. For the extracted netlists, this is the main node at the follower source (`xref_xmsf_s0` / `xref_xmsfl_s0`). The base run therefore contains the wiring resistance of the reference too. The metric thus measures the buffer settling and the wiring drop between the follower and the port only. The IR drop from the port to the drivers appears in the codes and in the gain, not in the R2-4 number.
2. The VIDEAL of the base run is the buffer DC value of an op-only run of the same netlist (`--vref op:<run>`; revision-5 failure 25).
3. `noopiter` is on for the layout cores. The 4-segment rppd starts the first Newton step outside the r3 vmax limit and KLU then reports a singular matrix. The netlist of record also needs gmin stepping. The OP is identical to the printed digits (scratch `post-dbg-sing`).
4. `--solver sparse` is used for the extracted netlists. KLU fails the OP on the RC netlist (layout lead, 2026-10-26).
5. Parallel identical devices are merged (exact when the units share nodes; pex_build ties the units of a bit to one collector and one top-plate node). Without the merge, the 830 unit MIMs (each a PDK 55 mΩ + C subcircuit) make ngspice 14 to more than 28 times slower.
6. Pre-layout comparison values for the full core were run here (`rec`), because the r5 R2-4 and first-conversion runs used the fast core (ideal drivers).

## Results (tt = 27 °C, 1.2 V, VDDA 3.3 V unless stated)

Column header key:

- Pre: netlist of record, full core.
- Layout-mapped: lay0, no parasitics.
- Post: layout A extracted, C only (`r1_adc_post_c_m.spice`) or RC (`r1_adc_post_rc_m.spice`), merged, Sparse solver.

| Check | Pre (netlist of record, full core) | Layout-mapped (lay0, no parasitics) | Post, C only (layout A) | Post, RC (layout A) | Status |
| --- | --- | --- | --- | --- | --- |
| (a) Static windows at tt, ±6 LSB at 1023/1024, 2047/2048, 3071/3072, VREF 1.045 V, design weights | max \|DNL\| 0.54 / 0.54 LSB (resolution), monotonic, no missing code (`post-win-tt-rec`, 3148 s, `results/win3_tt_rec.json`) | Same codes and DNL (`post-win-tt-lay0m`, 3434 s, `results/win3_tt_lay0m.json`) | not run | `post-win-tt-rc-103` (layout lead run, CPU 103, 9876 s; `results/win3_tt_rc.json`): monotonic; windows moved by the gain error (about 1.14): a 872-887, 2030-2045, 3190-3203; b 869-884, 2030-2045, 3194-3208. Max \|DNL\| 0.54 / 0.54 LSB on the codes with hits. Codes with no hit: a 886, 2044; b 883, each at the last frame of its window. At gain 1.14 the grid is 0.58 output LSB per point, so a code with no hit shows DNL < −0.42 LSB; it does not prove a missing code. A finer window is not run | pre passed; layout-mapped passed; RC failed by the window criterion (codes with no hit), cause not resolved |
| (b) R2-4 at tt (limit 0.25 LSB) | 0.179 LSB, after gain fit 0.153 (`post-ref-tt-rec` / `-ideal`); fast core 0.209 (r5) | 0.178 LSB (`post-ref-tt-lay0m` / `-ideal`) | not run | 5.03 LSB (a 4.91), after gain fit 1.09, code difference ≤ 1 LSB, final residue error 1.35 LSB (`post-ref-tt-rc3` 1335 s + base `post-ref-tt-rc4-sp` 1190 s, `results/ref_tt_rc4.json`) | pre passed; layout-mapped passed; RC failed |
| (b) R2-4 at ss / 125 °C / 1.08 V | 0.168 LSB, after gain fit 0.149 (`post-ref-ss125-rec` / `-ideal`); fast core 0.163 (r5) | 0.169 LSB (`post-ref-ss125-lay0` / `-ideal`, merged, `results/ref_ss125_lay0m.json`) | not run | 4.70 LSB (a 4.54), after gain fit 1.52, code difference ≤ 7 LSB (`post-ref-ss125-rc3` 1084 s + base `post-ref-ss125-rc4-sp` 1094 s, `results/ref_ss125_rc4.json`) | pre passed; layout-mapped passed; RC failed |
| (c) Mux sequence at tt, 33 ns pulse | `t2-isa-tt`: max error 3.66 LSB, gain 0.9982, residual after gain fit 0.45 | All 8 codes identical to `t2-isa-tt` (`post-isa-tt-lay0` 519 s, `post-isa-tt-lay0m` 198 s) | `post-isa-tt-cm2` (layout lead): gain 1.089, residual 6.97 LSB; codes 2994/1088, 4075/24, 1090/2991, 3757/324 | `post-isa-tt-rc2` (507 s): gain 1.114, max error 213 LSB, residual 34 LSB; frame 1 clipped (4095/0); without frame 1: gain 1.127, offset −10.7 LSB, residual 4.62 LSB; codes 3024/1049, 4095/0, 1055/3023, 3812/258 | pre and layout-mapped passed; C only and RC failed (gain error from the top-plate parasitic, about 73 fF per side, layout lead analysis) |
| (d) First conversion with the 33 ns pulse | tt: 2047/2048, 2048/2047 (`post-fc-tt-rec`, 115 s); ss −0.90 V: 74/74, 116/116 (`post-fc-ss-rec`) | tt ±1 LSB; ss 0 / 0 LSB, codes 74 / 116 (`post-fc-*-lay0*`) | `post-fc-tt-cm-nom` (layout lead): 2040 / 2040 | `post-fc-tt-rcm2` (layout lead, 305 s): 2037 / 2036, 2037 / 2037, frame 0 − frame 1 ≤ 1 LSB | passed (frame 0 = frame 1 within 1 LSB); ss on C only and RC not run |
| (e) IDD / IDDA at tt (from (c)) | 0.903 / 1.034 mA | 0.904 / 1.034 mA | 0.894 / 1.036 mA | 0.636 / 1.023 mA (supply R; C only does not drop) | recorded; no limit in this harness |

Not run, recorded: static windows on the C-only netlist; R2-4 on the C-only netlist; the lay0 unmerged R2-4 tt pair (`post-ref-tt-lay0`, superseded by the merge, H4); the synthetic-parasitic speed tests (replaced by the real netlists). Invalid, not used: `results/*_INVALID_*.json` (H8, H11, H12).

R2-4 RC reading: the comparator-input error is 4-5 LSB at decision 6 and decays slowly (about 3.8 LSB at decision 13, 1.3 LSB at the final residue at tt). The slice-port reference has not recovered from the MSB charge draw. In `post-ref-tt-rc3` the peak droop during evaluation at the follower source is 2.79 mV (layout-mapped 1.19 mV, pre 1.20 mV); the wiring from the source to the slice port adds only 0.20 mV dynamic and 5.61 mV static (a gain term). The vrefl port droops 3.47 mV (layout-mapped 0.73 mV). The error is the buffer response with the extracted load and supply resistance, not the reference wiring (`sep_ref.py`, diagnostic).

## Run time (simulated time per wall minute, one CPU, machine load about 80)

| Netlist | Deck | Rate |
| --- | --- | --- |
| Netlist of record, full core | mux 3.31 µs | 0.86 µs/min (`t2-isa-tt`) |
| Netlist of record, full core | windows 56 µs | 1.07 µs/min (`post-win-tt-rec`, 52 min) |
| lay0 unmerged | mux | 0.38 µs/min |
| lay0 unmerged | first conversion | 0.07 µs/min (`post-fc-tt-lay0`, 27 min for 1.86 µs) |
| lay0 merged | first conversion | 1.02 µs/min (109 s) |
| lay0 merged | windows | 0.98 µs/min (57 min) |
| lay0 merged | mux | 1.00 µs/min (198 s) |
| Layout A RC, merged, sparse (1729 R, 1817 C, about 2000 nodes) | mux | 0.39 µs/min (507 s) |
| Layout A RC, merged, sparse | R2-4 points 7.7 µs, tt | 0.35-0.39 µs/min (`post-ref-tt-rc3` 1335 s, `post-ref-tt-rc4-sp` 1190 s) |
| Layout A RC, merged, sparse | R2-4 points, ss125 | 0.41-0.43 µs/min (1084-1134 s) |
| Layout A RC, merged, sparse | OP only | 6-8 s |
| Layout A RC, merged, sparse | windows 56 µs | 0.34 µs/min (`post-win-tt-rc-103`, 9876 s = 2.7 h, CPU 103) |

Rule for planning: an RC run costs about 2.5 times the netlist-of-record run. Examples: windows 56 µs ≈ 2.4 h; one R2-4 run 7.7 µs ≈ 20 min; one mux run ≈ 8.5 min. Without the merge, multiply by 15 or more.

## Contract items for the layout

1. `vref` and `vrefl` must be named nets at the follower sources (`xref_xmsf_s0`, `xref_xmsfl_s0`): the R2-4 base runs and the probes use them. pex_build does this.
2. `topap`, `topan`, `topbp`, `topbn` must stay labelled; the R2-4 metric reads them.
3. The units of a CDAC bit must share one node per plate in the extracted netlist, or the merge is not exact and the run time grows by 15 times or more.
4. Effective resistance (`net_reff.py`; the lead's corrected values include the `__iK` nodes): slice gnd 249 Ω, vdd 116 Ω, vref 85 Ω, vrefl 99 Ω; top vss 253 Ω, vdd 200 Ω, vdda 130 Ω. The layout lead records these as an open issue for layout B (0.40 µm router wires on the supplies).

## Failures and mistakes (this harness)

| # | What happened | Class | Effect and fix |
| --- | --- | --- | --- |
| H1 | The first layout-mapped OP (`post-op-tt-lay0`) was labelled failed: a singular-matrix warning before the gmin stepping, caused by the 4-segment rppd | numerical | `noopiter` for the layout cores; rerun `post-op-tt-lay0-b`. KLU rejects `.nodeset` (diagnostic scratch run `post-dbg-sing`, no run.json, not evidence) |
| H2 | I changed a comment line of `make_sim_netlist.py` output while runs used `r1_adc_lay0.spice`; its hash changed | process-hygiene | Restored byte-identical before a new run started. Later edits write new files |
| H3 | The synthetic-parasitic hook lumped the capacitors of internal RC nodes to ground and counted the nodes per occurrence | functional-bug | Two-pass node collection (`Scope.add_all`) |
| H4 | I did not check the run speed of the unmerged layout netlist before queuing the 56 µs window. `post-win-tt-lay0` would have taken about 12 h; stopped by SIGKILL on its PID after 31 min (labelled failed). `post-ref-tt-lay0-ideal` was stopped as well, and its buffer run `post-ref-tt-lay0` is not used | estimation / verification-gap | Short speed checks first; merge of parallel devices; reruns `*-lay0m` |
| H5 | The first speed hypothesis (error amplifier at high open-loop gain against the forced reference) was wrong. `--ideal-bgr off50m` did not change the speed (`post-fc-tt-lay0-b`) | estimation | The cause was the unit MIM count. Diagnostic scratch run `post-dbg-speed` (no run.json, not evidence): merged 42 s, unmerged not finished in 1275 s. The evidence is the merged reruns `*-lay0m` against the netlist of record. `off50m` stays as the default (no effect on the core) |
| H6 | Scratch speed decks ended at 0.75 µs, on a clk30 falling edge, and aborted at the last time point (revision-5 lesson: no breakpoint on the clock grid) | numerical | Used only as a relative speed comparison up to the abort |
| H7 | The layout contract changed during the runs (NDUMMY 88 → 82, `r1_adc_decap.json`, MIM area +2 µm²). Runs before 17:15 CET carry `r1_adc_lay0.spice` sha256 `25d481a1…` (contract `93b0b61e…`) | coordination | No electrical effect without parasitics (gnd-gnd dummies); recorded per run |
| H8 | `merge_parallel.py` wrote `m=1` on every instance, also on `Xslice_a` / `Xslice_b`. In ngspice 46 this overrides the merged m inside the slice: all CDAC MIMs became m=1 (gain 1.40, codes at the rails). Found by the layout lead | functional-bug | Unmerged lines are written unchanged. `post-isa-tt-rc-s`, `post-op-tt-rc-s`, `post-ref-tt-rc-s`, `post-isa-tt-cm` are marked invalid |
| H9 | The first RC jobs ran with KLU (OP failure: `post-isa-tt-rc`, `post-ref-tt-rc`, `post-ref-tt-rc-ideal` failed; `post-op-tt-rc` not used) | tooling | `--solver sparse` (layout lead) |
| H10 | Queue waiters. I believed a chained waiter (`nohup sh -c` from the tool shell) had ended with the tool call, and I started a second waiter. The first waiter was alive. Two copies of `jobs_q104d` ran: two runs of `post-ref-ss125-rc` / `-ideal` ran in parallel, and the copy that started later refused the existing run ids. I stopped both runs by SIGKILL on their PIDs (old base method, see H11). They are labelled failed and are not used | tooling / process-hygiene | One waiter per queue, started with `setsid`; check `ps` before a new waiter. The run-id refusal prevented overwrites |
| H11 | R2-4 base run on the RC netlist with the buffer biased (`post-ref-tt-rc2-ideal`, `--ref lay-ideal`): the 0.8 mA of the sink XMIB flows from the forced node through the reference wiring. The slices see a different static reference than in the buffer run. Result 5.77 LSB, code difference about 100 LSB: a base-run artefact | verification-gap (metric) | `ref_tt_rc.json` is not a result. Not used |
| H12 | Fix attempt for H11 (rc3: `--base-ibias 0`, VIDEAL = buffer-OP slice-port vref) was wrong: with no tail current the error amplifier output goes high (ng 2.04 V), the followers turn fully on (IDDA 3.1 mA) and their current flows through the wiring into the forced node. OP diagnosis `post-op-tt-rc3-gnd`, `-ideal-gnd`, `-gnd2`, `-ideal-gnd2`: base slice-port vref 1.0558 V against 1.0426 V, slice vss 0.2-0.3 mV against 8-15 mV. R2-4 35-37 LSB, flat over decisions 5-13 (`ref_tt_rc3.json`); a modelled static correction gave 10-12 LSB (`ref_tt_rc3c.json`). Neither is a result. I did not check the base-run OP against the buffer OP before the transient | verification-gap (metric) | rc4: `make_sp_netlist.py` cuts the slice vref / vrefl pins from the wiring inside `r1_adc_lay_pr` and drives them with ideal DC sources at the buffer-OP port values; the buffer and all supplies stay as extracted; base run with `--ref lay`. Base OP `post-op-tt-rc4-sp` is identical to the buffer OP. Rule: compare the base OP with the buffer OP before every R2-4 base transient |

# Final-GDS chip STA re-run with a working 5 % derate, 2026-10-06

Re-run of the chip-level static timing of `../sta_final_gds_20260928/` after correcting the derate
expression in the SDC of record. Every number is **simulated** (OpenSTA 3.1.0). Nothing was measured.

## The defect and the fix

`blocks/g1_padring/flow/g1_chip_top.sdc` computed the derate as `expr 1-[expr $::env(TIME_DERATING_CONSTRAINT) / 100]`.
With the integer `5` that is integer division in Tcl (`5 / 100 = 0`), so the SDC executed
`set_timing_derate -early 1` and `-late 1`: derate 0 %, while the log line still said "5%".
**Every chip-level STA record before this one was at derate 0 %**: `sta_merged_sdc_20260924`,
`sta_final_gds_20260928`, and the LibreLane runs run4..run7 (config `TIME_DERATING_CONSTRAINT 5`, same template).
The fix is `/ 100.0`, giving `-early 0.95` and `-late 1.05`. It is applied in the SDC of record and in the two stored
copies of the same template lines (`sta_merged_sdc_20260924/g1_chip_top_template_only.sdc`,
`top_sta_dryrun1350/g1_chip_top_plus_g1_digital_top.sdc`); nothing else in them changed. The stored logs and
reports of the earlier runs are unchanged, and they remain the record of what was run at derate 0 %. The
`sta_merged_sdc_20260924/SHA256SUMS` line for the SDC (`bb006e96…`) refers to the pre-fix file (commit `458c702cd`).

| SDC | sha256 |
| --- | --- |
| before (derate 0 %, record of 28 Sep) | `bb006e9680938e9a6ed5fe09426a4ab30c0a71cc35fea8084426236d845b7710` |
| after (derate 5 %, this record) | `cd9537ee7cc818411f230ead101d8b13ac37c1f7e529e200a95c84b3f3934b86` |

## Built against

| Item | Version / hash | How established |
| --- | --- | --- |
| GDS of record | `g1_chip_top_1414_r4.gds` `225d0b53…` | `sha256sum` |
| Inputs | identical to `sta_final_gds_20260928`: STA netlist `47b39ca6…`, stubs `ddb9f6fc…`, macro netlist `4b83f181…`, macro SPEF `0b626c7f…`, top SPEF `4b2f878d…` (p2p) / `3b1ec0bf…` (ub) | `sha256sum` of the copies used (`bulk_inputs.sha256`) |
| SDC | `g1_chip_top.sdc` `cd9537ee7cc818411f230ead101d8b13ac37c1f7e529e200a95c84b3f3934b86` | `sha256sum` |
| PDK | IHP SG13G2 `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` | `flow/run.sh` commit check |
| OpenSTA | 3.1.0 | `sta -version` in the container (same image) |
| Container | `tapeoutbench-eda:latest` `sha256:ddeb6957…` | `flow/run.sh` image identity check |
| Scripts | `sta_final.tcl`, `run_sta_final.sh`, `summarize.py` of `sta_final_gds_20260928`, unchanged | git |
| CPUs | 90-91 (`taskset` through `flow/run.sh`, `G1_CPUSET`) | allocation |

## Command

From the repository root. `BULK` is this re-run's results root, filled beforehand with copies of `inputs/`,
`rc_r4/` and `eco_views/` from the `postsub-20260928/timing` root of the 28 Sep run.

```sh
BULK=${BULK} designs/g1-guardian/blocks/g1_ctrl/reports/sta_final_gds_derate5_20261006/run_all_derate5.sh   # 18 runs, 2 at a time
python3 designs/g1-guardian/blocks/g1_ctrl/reports/sta_final_gds_20260928/summarize.py ${BULK}/final ${BULK}/summary
```

The 18 runs are the 6 chip cases of the 28 Sep record x 3 corners (`chip_p2p`, `chip_ub`, `chip_p2p_oscedge`,
`chip_p2p_sclkport`, `chip_p2p_board10pF`, `chip_p2p_board15pF`). All completed (`STA_FINAL_COMPLETE`, rc 0; `runs/*/sta.log`
shows the derate line). The `macro` case was **not re-run**: it uses the macro sign-off SDC `g1_digital.sdc`, which
does not contain this expression. The bulk run directories are in `${BULK}`; the small logs and tables are in
`runs/` and `results/` here (`SHA256SUMS`).

## Results

Worst slack in ns, derate 0 % (28 Sep record) against derate 5 % (this record). Same cases, parasitics and corners.

| Case | Corner | Setup, 0 % | Setup, **5 %** | Hold, 0 % | Hold, **5 %** | Violations setup / hold |
| --- | --- | --- | --- | --- | --- | --- |
| chip_p2p (record case) | fast | 27.874 | **27.793** | +0.114 | **+0.098** | 0 / 0 |
| chip_p2p | typ | 27.053 | **26.930** | +0.195 | **+0.176** | 0 / 0 |
| chip_p2p | slow | 25.381 | **25.176** | +0.337 | **+0.308** | 0 / 0 |
| chip_ub | fast / typ / slow | 27.874 / 27.052 / 25.381 | 27.793 / 26.930 / 25.175 | +0.114 / +0.195 / +0.337 | +0.098 / +0.176 / +0.308 | 0 / 0 |
| chip_p2p_oscedge | fast / typ / slow | 27.874 / 27.053 / 25.381 | 27.793 / 26.930 / 25.176 | +0.114 / +0.195 / +0.337 | +0.097 / +0.176 / +0.308 | 0 / 0 |
| chip_p2p_sclkport | fast / typ / slow | 27.680 / 26.780 / 24.950 | 27.589 / 26.644 / 24.723 | +0.114 / +0.195 / +0.337 | +0.098 / +0.176 / +0.308 | 0 / 0 |
| chip_p2p_board10pF | fast / typ / slow | 24.855 / 22.721 / 18.725 | 24.623 / 22.382 / 18.186 | +0.114 / +0.195 / +0.337 | +0.098 / +0.176 / +0.308 | 0 / 0 |
| chip_p2p_board15pF | fast / typ / slow | 23.350 / 20.561 / 15.402 | 23.042 / 20.114 / 14.697 | +0.114 / +0.195 / +0.337 | +0.098 / +0.176 / +0.308 | 0 / 0 |

Per-group worst slack, `chip_p2p` at 5 % (setup SCLK / osc_clk / async; hold SCLK / osc_clk / async):

| Corner | Setup | Hold |
| --- | --- | --- |
| fast | 27.793 / 96.867 / 97.552 | 0.102 / 0.098 / 0.235 |
| typ | 26.930 / 95.462 / 96.462 | 0.176 / 0.179 / 0.393 |
| slow | 25.175 / 93.024 / 94.692 | 0.308 / 0.326 / 0.670 |

- The worst setup is still the SDO output path (SCLK fall, `output34`, `pad16_sdo`); the 5 % derate costs 0.08-0.20 ns of it.
- The worst hold is still inside the macro (osc_clk removal check, `i_core.u_digital`), and it moves by 16 / 19 / 29 ps
  (fast / typ / slow). The fast-corner cost of 16 ps agrees with the macro-level derate run in
  `review/redteam-20260927/digital/FINDINGS.md` (114 ps at 0 %, 98 ps at +-5 %).
- Max-capacitance and max-fanout flags, the max-slew flags of the 10 analog pads (placeholder liberty), the 10 / 15 pF board-load
  flags, the unannotated-driver counts (53 + 9) and the register counts (52 + 1170) are the same as at 0 %.
- The simulated osc_clk root transition (1.560 ns at slow, above the macro's 1.5 ns design limit) is an ngspice result and
  does not depend on the STA derate.

## Status

| Check | Status |
| --- | --- |
| Setup / hold, final-GDS routes, SDC of record with working 5 % derate (0.95 / 1.05), 3 corners | **passed** (0 / 0 violations), simulated |
| Variants `chip_ub`, `chip_p2p_oscedge`, `chip_p2p_sclkport`, `chip_p2p_board10pF`, `chip_p2p_board15pF` at 5 % | passed (setup / hold), simulated; 15 pF is outside the 4 mA pad liberty (max_capacitance 12 pF) |
| `macro` case at 5 % | not applicable (macro SDC has no derate expression; the 28 Sep macro numbers stand) |
| Min / max RC corners, crosstalk, analog-driven nets | **not run**, as in the 28 Sep record |
| Derate other than 5 % (for example +-10 %) at chip level | **not run** |

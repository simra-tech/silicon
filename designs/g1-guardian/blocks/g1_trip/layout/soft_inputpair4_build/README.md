# Soft input pair NF4: candidate build and check helpers

These are the helper scripts that built and checked the folded soft-comparator
input pair (NF4: `MM1`/`MM2` W12/L0.34 → W24/L0.68, four 6 µm fingers) and the
isolated 1414 µm parent `candidate.gds` `60730627…`. The chip of record
`g1_padring/layout/g1_chip_top_1414.gds` (`629d303a…`) is that parent with its
top cell renamed. The saved results are in
[`../../reports/soft-inputpair4-folded-physical-20260924-r1/`](../../reports/soft-inputpair4-folded-physical-20260924-r1/README.md).

Copied 2026-09-24 from the helper bundle (`${TOOLS}` in `evidence.json`). The
recorded SHA-256 of each original was checked against `external_tools` in
`../../reports/soft-inputpair4-folded-physical-20260924-r1/evidence.json`
(`soft_inputpair4_folded_native_r1.py` is not listed there; its hash was taken from the bundle).

**Byte-identical copies** (copy hash = recorded hash):

| File | SHA-256 | Role |
| --- | --- | --- |
| `prepare_soft_inputpair4_folded_native_r1.py` | `6dd9903f6409e245a49e6c536f7a503614bbc6339a57b4c6192331deea04869e` | standalone folded comparator GDS/CDL and readback |
| `prepare_soft_inputpair4_parent_r3.py` | `208f6c18ebf46cf8d6b072510348fafa871cf48b30d7370d8fedeecfb25e130f` | isolated parent delta (soft cell + q-feed) and `candidate.cdl` |
| `run_soft_inputpair4_parent_drc_r1.py` | `5b2c9aaa7786d92387c1b5b872a5225d38e2aa9f1aba3e5875aef555c0a216e4` | bounded main/no-density DRC |
| `run_soft_inputpair4_parent_maximal_r2.py` | `160dad80f7991f451cb068581f78d33eccfa4ae196a1fd2bcd537f439b5f108d` | maximal-only DRC |
| `run_soft_inputpair4_parent_lvs_r1.py` | `e9bff1b004d2bbd96edffced99aec79aa5047ba01b6da725e2a233e97afb272d` | projected-reference strict stock LVS |

**Sanitised copies** (differ from the recorded file only in the lines listed):

| File | Recorded SHA-256 (original) | Copy SHA-256 | Changed lines | Change |
| --- | --- | --- | --- | --- |
| `soft_inputpair4_parent_reference_r1.py` | `6813a1bb86b050ea22ed563d2459e71a120f5d12aec210bef20c546f4a7dd6ab` | `0325ddab769227d748131ead96241decb487f5758466a4fb230c77d42acb785f` | 2, 4 | `import os`; `SOURCE` host path → `$G1_RESULTS_ROOT/osc-r095-physical-20260924-r1/fullchip_r095_candidate.cdl` |
| `run_soft_parent_density_antenna_r1.py` | `909eea85c84baf6606608beaa6fbba56b6f97d7279e586eb47747220c2925b11` | `454bc142942bea7caf6a4f25f7e908f42f72b9444ba4de7cd3150b27db570daf` | 16 | `CANDIDATE` host path → `$G1_RESULTS_ROOT/soft-inputpair4-parent-20260924-r3` |
| `inspect_soft_inputpair4_parent_r1.py` | `2849882180fd25b99909691d8a0f3cf8d6a188a5d0b0159dae80bf20a1268189` | `ebab8fe30c4d814e794cea451f93a745827d49946c30d53bad5a6dee7ed7d811` | 2, 4, 5, 7 | `import os`; `ROOT` `parents[3]` → `parents[6]` (new depth); `PARENT`, `STANDALONE` host paths → `$G1_RESULTS_ROOT/osc-r095-fullchip-integration-20260924-r1/osc_r095_fullchip.gds`, `$G1_RESULTS_ROOT/soft-inputpair4-folded-native-20260924-r1/standalone.gds` |
| `soft_inputpair4_folded_native_r1.py` | `6899361f0e39ed8db3978cd8f461a8156ed53b5dff5c67b203c6822f7e67feca` (bundle; not in `evidence.json`) | `3df73a33410dc8dd62b316d61890df70cb8433fbd5560add9115607f9397e789` | 13 | `ROOT` `parents[3]` → `parents[6]` |
| `flatten_soft_inputpair4_reference_r1.rb` | `18f9be251f46d25d9c332c6857636f9209d2679fd6866ac0b35a3724aa7670c5` | `9f93aa77679a9fa660334c3e3686f31c6a2557861a596c576e5c59b4b5880f28` | 4 | base lookup `'../../..'` → `'../../../../../..'` (repository root from this directory; resolved path checked to exist) |

Set `G1_RESULTS_ROOT` to the bulk results root (`${BULK}` in `evidence.json`)
before running. Every input the scripts read is still checked against its
recorded SHA-256, so a wrong root fails an assertion rather than running on
other data. Scripts that hash themselves (`source_sha256`, bound inputs) will
now report the copy hash, not the recorded one.

## Limits

- Repository modules they import exist in the tracked tree:
  `review/audits/io_tap_closure/physical_source/integration_purefill/`
  (`current_rz_bindings.py`, `current_rz_stock_preconditions.py`, `run_osc_r095_fullchip_stock_lvs.py`,
  `flatten_rz_reference.rb`), `review/audits/run_core_maximal_only.py` and `../gen_trip_layout.py`.
- The DRC/LVS runners assert CPU affinity (`{2}`, density/antenna `{14}`) and the container PDK path
  `/foss/pdks/ihp-sg13g2` at commit `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`.
- The bulk inputs (parent GDS, standalone GDS, CDLs) are not in Git.
- Reproduction from this directory: **not run**. Only static checks were run: file hashes,
  import names and the `.rb` path resolution.

## Recorded command lines

Taken from the report README and `evidence.json` (locations normalised there: `${BULK}` is the
results root, `${PDK}` the pinned PDK, `${TOOLS}` the helper bundle, which is this directory for the files above).

```sh
# preparation (output directory must not exist)
python3 ${TOOLS}/prepare_soft_inputpair4_folded_native_r1.py --output ${BULK}/soft-inputpair4-folded-native-20260924-r1
python3 ${TOOLS}/prepare_soft_inputpair4_parent_r3.py --output ${BULK}/soft-inputpair4-parent-20260924-r3

# main/no-density DRC (record: failed, rc 124 at 1151.67 s after table main completed with 0 markers)
python3 ${PDK}/libs.tech/klayout/tech/drc/run_drc.py --path=${BULK}/soft-inputpair4-parent-20260924-r3/candidate.gds \
  --topcell=placed_core_NOT_CONNECTED_FULLCHIP --run_mode=deep --no_density \
  --run_dir=${BULK}/soft-inputpair4-parent-20260924-r3/drc-main

# maximal-only DRC (record: passed, 0 markers)
timeout --kill-after=5 1130 python3 ${TOOLS}/run_soft_inputpair4_parent_maximal_r2.py \
  --candidate-dir ${BULK}/soft-inputpair4-parent-20260924-r3 --execute

# projected-reference strict stock LVS (record: passed; comparison-only reference, not canonical LVS)
python3 ${PDK}/libs.tech/klayout/tech/lvs/run_lvs.py --layout ${BULK}/soft-inputpair4-parent-20260924-r3/candidate.gds \
  --netlist ${BULK}/soft-inputpair4-parent-20260924-r3/flat-r1/physical_AP_three_dummy_flat_reference.cdl \
  --topcell placed_core_NOT_CONNECTED_FULLCHIP --run_mode deep --top_lvl_pins --spice_comments \
  --run_dir ${BULK}/soft-inputpair4-parent-20260924-r3/lvs-r1

# density and antenna (record: passed, 0 markers each; wrapper run_soft_parent_density_antenna_r1.py --mode density|antenna)
python3 ${PDK}/libs.tech/klayout/tech/drc/run_drc.py --path=${BULK}/soft-inputpair4-parent-20260924-r3/candidate.gds \
  --topcell=placed_core_NOT_CONNECTED_FULLCHIP --run_mode=deep --density_thr=1 --density_only \
  --run_dir=${BULK}/soft-inputpair4-parent-20260924-r3/density_cpu14_r1/reports
python3 ${PDK}/libs.tech/klayout/tech/drc/run_drc.py --path=${BULK}/soft-inputpair4-parent-20260924-r3/candidate.gds \
  --topcell=placed_core_NOT_CONNECTED_FULLCHIP --run_mode=deep --density_thr=1 --antenna_only \
  --run_dir=${BULK}/soft-inputpair4-parent-20260924-r3/antenna_cpu14_r1/reports --antenna
```

The command lines for `run_soft_inputpair4_parent_drc_r1.py` and
`run_soft_inputpair4_parent_lvs_r1.py` themselves (`--candidate-dir`, `--run-dir`)
are not recorded in `evidence.json`. Only the stock argv they launched is recorded.
The flatten step's invocation is not recorded either.

The sign-off of the renamed chip file (`629d303a…`) was rerun separately and does
not depend on these helpers: `../../../g1_padring/reports/signoff-1414-20260924/README.md`.

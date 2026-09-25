# r3 macro of record: tracked build inputs and rebuild command

These are the exact inputs that built the `g1_digital` macro in the chip of record
`blocks/g1_padring/layout/g1_chip_top_1414_r3.gds` (`7d07a784…`). The original run is
`${BULK}/digital-eco-r3cand2-20260926` (2026-09-25/26); `${BULK}` is the bulk results root.

| File | What it is |
|---|---|
| `config_r3_as_run.yaml`, `config_r3_pass1_as_run.yaml` | The configs of the original main run and first pass, verbatim except `/opt/…` → `${BULK}`. They read the RTL from the run's `rtl_snapshot/`, so they are a record, not runnable from the tree |
| `config_r3.yaml` | **Runnable**: `config_r3_as_run.yaml` with only the paths changed. The RTL comes from the tracked `blocks/g1_ctrl/rtl_eco_20260925/` and `blocks/g1_seu/rtl_eco_20260925/`, byte-identical to the snapshot. SDC and pin template paths are adjusted for this directory |
| `seeds_r3.yaml` | The TMR placement seeds from the first pass (`tmr_spread.py`). They are embedded in both configs, identical to this file |
| `g1_digital_pins_run7.def` | `FP_DEF_TEMPLATE`: the 44 signal pins of run7, identical to the chip macro's pins |
| `rtl_sha256.txt` | SHA-256 of the 9 RTL files and the SDC the run read |

The plugin step `G1.SplitClockRoot` comes from `../librelane_plugin_g1eco/`. `../run_trial.sh` puts it
on `PYTHONPATH` and selects OpenROAD 26Q1 (`openroad-librelane`).

## Rebuild

Run from the repository root, inside the pinned container, with `BULK` set. This takes about 18 min on 8 CPUs.

```sh
sha256sum -c <(sed 's|  g1_ctrl/|  designs/g1-guardian/blocks/g1_ctrl/rtl_eco_20260925/|; s|  g1_seu/|  designs/g1-guardian/blocks/g1_seu/rtl_eco_20260925/|' \
  designs/g1-guardian/blocks/g1_ctrl/flow/eco/r3/rtl_sha256.txt)
ECO_ROOT=$BULK/<new root> BULK=$BULK G1_CPUSET=88-95 G1_CPUS=8 \
  designs/g1-guardian/blocks/g1_ctrl/flow/eco/run_trial.sh r3/config_r3.yaml main \
  -c DRT_THREADS=8 --save-views-to $BULK/<new root>/final
```

To reproduce the chip GDS, continue with `swap_macro.py` into r2 (retained at
`${BULK}/g1-freeze-retention-20260925/g1_chip_top_1414_r2.gds`), then `add_gatpoly_fill.py`, with the
arguments in `../RUNBOOK.md` §3.

## Verified (2026-09-26)

The rebuild ran from these tracked files in `${BULK}/digital-eco-r3-rebuild-20260926` (1087 s, rc 0).

| Output | Result against the original run |
|---|---|
| `nl`, `pnl`, `def`, `lef` | byte-identical (`4b83f181…`, `476885d7…`, `dabad146…`, `e32287e5…`) |
| Macro GDS | identical record for record except the BGNLIB/BGNSTR timestamps (534 377 records) |
| SPEF, 3 SDFs | identical except the `DATE` header line |
| Swap into r2 + GatPoly fill of the rebuilt macro | chip GDS **byte-identical to the chip of record**, `7d07a7841a531f51e08b0c90e76fe603889cd2ef29905e309e63f09742e688f2` (swapped intermediate `861e880d…` also identical) |

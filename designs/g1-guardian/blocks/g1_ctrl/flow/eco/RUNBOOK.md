# g1_digital ECO: re-harden, swap into the 1414 µm chip, re-sign-off

This runbook lists the commands in order, from the repository root. The dry run and its
results are in [`../../ECO_FLOW_FEASIBILITY_20260925.md`](../../ECO_FLOW_FEASIBILITY_20260925.md).

**Status (2026-09-25):** waiting for the corrected ECO RTL. The rehearsal run on the revoked
freeze is in `$BULK/digital-eco-20260925/` (`REHEARSAL_SUPERSEDED_RTL.txt`). Its netlist and
DEF are byte-identical to the dry run `eco_m5`; nothing there is a candidate. The real run
uses a new root.

Conventions:
- `BULK` is the bulk results root. `R=$BULK/digital-eco-<date>-r<n>` is this run's root: a new
  directory, never the rehearsal's.
- `E=designs/g1-guardian/blocks/g1_ctrl/flow/eco` and `P=designs/g1-guardian/blocks/g1_padring`.
- `D=/foss/pdks/ihp-sg13g2/libs.tech/klayout/tech` is the path inside the container.
- `run() { G1_RESULTS_ROOT=$BULK G1_CPUSET=<cpus> G1_CPUS=<n> G1_CONTAINER_ENGINE=podman flow/run.sh "$@"; }`

Macro CPUs are 88-95. Chip DRC runs on 64-79 in parallel. The r2 files and records are
read only; every output is a new file.

## 0. Inputs

Check the ECO RTL hashes against the coordinator's list, then record every input:

```
sha256sum designs/g1-guardian/blocks/g1_ctrl/rtl_eco_20260925/*.v \
          designs/g1-guardian/blocks/g1_seu/rtl_eco_20260925/*.v \
          designs/g1-guardian/blocks/g1_ctrl/flow/g1_digital.sdc > $R/inputs_sha256.txt
```

## 1. Macro

```
# 1a  first pass, synthesis to global placement (about 1 min)
python3 $E/make_config.py --rtl ../../rtl_eco_20260925 --seu-rtl ../../../g1_seu/rtl_eco_20260925 \
    --seeds none --out $E/config_final_pass1.yaml
ECO_ROOT=$R BULK=$BULK G1_CPUSET=90-93 G1_CPUS=4 $E/run_trial.sh config_final_pass1.yaml final_pass1 -T OpenROAD.GlobalPlacement

# 1b  TMR seeds from pass 1, then the final config
python3 designs/g1-guardian/blocks/g1_ctrl/flow/tmr_spread.py \
    $R/runs/final_pass1/28-openroad-globalplacement/g1_digital.nl.v \
    $R/runs/final_pass1/28-openroad-globalplacement/g1_digital.def $E/seeds_final.yaml
python3 $E/make_config.py --rtl ../../rtl_eco_20260925 --seu-rtl ../../../g1_seu/rtl_eco_20260925 \
    --seeds seeds_final.yaml --out $E/config_final.yaml

# 1c  main flow (about 20-30 min). It runs the macro DRC (Magic, KLayout), netgen LVS,
#     antenna, XOR and 3-corner STA
ECO_ROOT=$R BULK=$BULK G1_CPUSET=88-93 G1_CPUS=6 $E/run_trial.sh config_final.yaml final \
    -c DRT_THREADS=6 --save-views-to $R/final
python3 $E/summarize_trial.py $R/runs/final $R/summary_final.json
python3 $E/clock_fanout.py $R/final/nl/g1_digital.nl.v                         # max <= 8
run python3 designs/g1-guardian/blocks/g1_ctrl/flow/tmr_check.py $R/final/nl/g1_digital.nl.v \
    $R/final/def/g1_digital.def > $R/tmr_separation.txt                        # all >= 20 um

# 1d  merged-SDC STA, macro and chip netlist, 3 corners
STA_SUB=digital-eco-20260925/sta BULK=$BULK $E/sta_trial.sh $R/final final 95    # -> $R/sta/final/<case>-<corner>

# 1e  pins against the chip macro (pins identical, TopMetal inside the old macro's)
run python3 $E/extract_macro_pins.py $P/layout/g1_chip_top_1414_r2.gds \
    __rz_port_text_000_retained_g1_digital $R/pins_chip_r2.json
run python3 $E/extract_macro_pins.py $R/final/gds/g1_digital.gds g1_digital $R/pins_final.json
python3 $E/compare_macro_pins.py $R/pins_chip_r2.json $R/pins_final.json $R/pincmp_final.json   # exit 0
```

## 2. GLS handoff

Write the netlist, SDF and SDC paths and their hashes into `$E/HANDOFF.md` for the ECO
agent. Gate-level simulation is theirs:
`flow/run.sh bash designs/g1-guardian/blocks/g1_ctrl/sim/run_gls.sh $R/final/nl/g1_digital.nl.v eco`.

## 3. Swap into r2, then fill

```
mkdir -p $R/chip
run python3 $E/swap_macro.py --chip $P/layout/g1_chip_top_1414_r2.gds \
    --cell __rz_port_text_000_retained_g1_digital --macro $R/final/gds/g1_digital.gds \
    --netlist $R/final/nl/g1_digital.nl.v --def $R/final/def/g1_digital.def \
    --out $R/chip/swapped.gds --report $R/chip/swap.json                       # "swapped": true

# GatPoly fill regeneration: 5/22 is added in the chip top cell, outside the macro outline.
# Exclusions are the stock GFil.d/e sets at 1.1 um (Activ, GatPoly, Cont, pSD, nSD:block,
# SalBlock, NWell, nBuLay) plus 26/0, with 0.3 um to Activ fill. The minimum width is 0.7 um (GFil.b).
# Tried on the trial swap: 100 rectangles (700 um2), global GatPoly 14.998 % -> 15.034 %.
# Main, maximal, density and precheck DRC were all 0.
run python3 $E/add_gatpoly_fill.py --in $R/chip/swapped.gds --out $R/chip/g1_chip_top_1414_r3_candidate.gds \
    --target-um2 700 --exclude-box 367,364,727,724 \
    --obstacles 1/0,5/0,6/0,14/0,7/21,28/0,31/0,32/0,26/0,1/22:300 --min-width-nm 700 \
    --report $R/chip/fill.json                                                 # >= 15.02 %

# XOR proof: outside the macro only 5/22 changed; inside, the macro layers and the
# 7 removed labels
run python3 $E/chip_xor.py $P/layout/g1_chip_top_1414_r2.gds $R/chip/g1_chip_top_1414_r3_candidate.gds \
    367,364,727,724 $R/chip/chip_xor.json
```

## 4. Chip CDL references

```
mkdir -p $R/cdl
python3 $E/regen_chip_cdl.py --canonical $P/netlist/g1_chip_top_1414_r2.cdl --pnl $R/final/pnl/g1_digital.pnl.v \
    --out $R/cdl/g1_chip_top_1414_r3.cdl --projection-out $R/cdl/comparison_only.cdl --report $R/cdl/regen.json \
    --header "g1_chip_top_1414_r3 canonical: r2 CDL with g1_digital from the ECO powered netlist"
run klayout -b -r $E/flatten_reference.rb -rd source=$R/cdl/comparison_only.cdl \
    -rd output=$R/cdl/g1_chip_top_1414_r3_projected_ref.cdl -rd top=g1_chip_top
```

`regen_chip_cdl.py` resolves `assign osc_en = <tie net>;`. That assign is new in the ECO
netlist (osc_en is tied high), and without it projected LVS fails on one tie-cell PMOS.
The control run passed: regenerated from the chip pnl `4fd0b616`, the `g1_digital` block
is byte-identical to r2, and the flat reference matches `g1_chip_top_1414_projected_ref.cdl`
(76 059 devices, 22 pins).

## 5. Chip sign-off suite

Same options as the r2 sign-off. Run in parallel, 5400 s bound each.

```
G=$R/chip/g1_chip_top_1414_r3_candidate.gds; S=$R/signoff
python3 $D/drc/run_drc.py --path=$G --topcell=g1_chip_top --run_mode=deep --no_density --disable_extra_rules --density_thr=4 --run_dir=$S/drc_main        # 64-67
python3 $P/flow/signoff/1414/run_maximal.py $G g1_chip_top $S/drc_maximal 4                                                                              # 68-71 (8 threads crashed once)
python3 $D/drc/run_drc.py --path=$G --topcell=g1_chip_top --run_mode=deep --density_thr=2 --density_only --run_dir=$S/density                            # 72-73
python3 $D/drc/run_drc.py --path=$G --topcell=g1_chip_top --run_mode=deep --density_thr=2 --antenna_only --run_dir=$S/antenna --antenna                  # 74-75
python3 $D/drc/run_drc.py --path=$G --topcell=g1_chip_top --run_mode=deep --precheck_drc --disable_extra_rules --density_thr=2 --run_dir=$S/precheck     # 76-77
python3 $D/lvs/run_lvs.py --layout $G --netlist $R/cdl/g1_chip_top_1414_r3_projected_ref.cdl --topcell g1_chip_top --run_mode deep --top_lvl_pins --spice_comments --run_dir $S/lvs_projected   # 78
python3 $D/lvs/run_lvs.py --layout $G --netlist $R/cdl/g1_chip_top_1414_r3.cdl --topcell g1_chip_top --run_mode deep --top_lvl_pins --spice_comments --run_dir $S/lvs_canonical              # 79
klayout -b -r $P/flow/signoff/1414/lvs_pair_counts.py -rd db=$S/lvs_<kind>/<name>.lvsdb > $S/lvs_<kind>/pair_counts.json
klayout -b -r $E/lvs_mismatches.py -rd db=$S/lvs_<kind>/<name>.lvsdb                # names any non-Match pair
```

Acceptance:
- DRC: main, maximal, density, antenna and precheck all at 0 markers.
- Projected LVS: Match.
- Canonical LVS: the same 14 IO sub-circuits NoMatch as r2, and top Skipped.
  Any other difference is a failure.

## 6. Bond map, then the records

- **Bond map.** Write a new bond map with the rows of `padframe/bondmap_20260925_r3.csv`,
  `candidate_gds_sha256` set to the r3 candidate's hash and `status=candidate`. Check it with
  `klayout -b -r $P/flow/signoff/1414r2/verify_bondmap.py -rd g=$G -rd csvf=<csv> -rd out=<json>`.
  Adoption as chip of record is the owner's decision.
- **Records.** Put `$P/reports/signoff-1414r3-20260926/README.md` in the r2 format:
  - Built against, and the files of record with their hashes;
  - what changed from r2 (the swap, the fill and the CDL), with the XOR proof;
  - the check table, the command list and the bond map;
  - "Not run": full-chip PEX, IR/EM, timing of the final GDS, and GLS if it is still open.

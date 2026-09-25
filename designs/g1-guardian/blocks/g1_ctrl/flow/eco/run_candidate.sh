#!/usr/bin/env bash
# RUNBOOK steps 0-6 in one script (macro -> swap -> fill -> CDL -> chip sign-off -> bond map).
# Usage (repository root): BULK=<bulk root> run_candidate.sh <R = new result root under BULK> [stage]
#   stage: all (default) | macro | chip | signoff | post
# Each stage stops on the first failed acceptance check. Nothing in the repository is written
# except the generated flow/eco/config_<tag>*.yaml and seeds_<tag>.yaml.
set -euo pipefail
R=$1; STAGE=${2:-all}
TAG=$(basename "$R")
E=designs/g1-guardian/blocks/g1_ctrl/flow/eco
P=designs/g1-guardian/blocks/g1_padring
D=/foss/pdks/ihp-sg13g2/libs.tech/klayout/tech
REL=../../../../../../..$R/rtl_snapshot
run() { local cpus=$1; shift; G1_RESULTS_ROOT=$BULK G1_CPUSET=$cpus G1_CPUS=1 G1_CONTAINER_ENGINE=podman flow/run.sh "$@" 2> >(grep -v 'level=warning' >&2); }
mkdir -p "$R/logs"

macro() {
  mkdir -p "$R/rtl_snapshot/g1_ctrl" "$R/rtl_snapshot/g1_seu"
  cp -p designs/g1-guardian/blocks/g1_ctrl/rtl_eco_20260925/*.v "$R/rtl_snapshot/g1_ctrl/"
  cp -p designs/g1-guardian/blocks/g1_seu/rtl_eco_20260925/*.v "$R/rtl_snapshot/g1_seu/"
  (cd "$R/rtl_snapshot" && sha256sum */*.v) > "$R/inputs_sha256.txt"
  sha256sum designs/g1-guardian/blocks/g1_ctrl/flow/g1_digital.sdc >> "$R/inputs_sha256.txt"
  (cd $E && python3 make_config.py --rtl $REL/g1_ctrl --seu-rtl $REL/g1_seu --seeds none --out config_${TAG}_pass1.yaml)
  date +%s > "$R/logs/pass1.start"
  ECO_ROOT=$R G1_CPUSET=90-93 G1_CPUS=4 $E/run_trial.sh config_${TAG}_pass1.yaml pass1 -T OpenROAD.GlobalPlacement > "$R/logs/pass1.log" 2>&1
  date +%s > "$R/logs/pass1.end"
  local GP=$R/runs/pass1/28-openroad-globalplacement
  python3 designs/g1-guardian/blocks/g1_ctrl/flow/tmr_spread.py $GP/g1_digital.nl.v $GP/g1_digital.def $E/seeds_${TAG}.yaml
  (cd $E && python3 make_config.py --rtl $REL/g1_ctrl --seu-rtl $REL/g1_seu --seeds seeds_${TAG}.yaml --out config_${TAG}.yaml)
  cp $E/seeds_${TAG}.yaml $E/config_${TAG}.yaml $E/config_${TAG}_pass1.yaml "$R/"
  date +%s > "$R/logs/main.start"
  ECO_ROOT=$R G1_CPUSET=88-95 G1_CPUS=8 $E/run_trial.sh config_${TAG}.yaml main -c DRT_THREADS=8 --save-views-to $R/final > "$R/logs/main.log" 2>&1
  date +%s > "$R/logs/main.end"
  python3 $E/summarize_trial.py $R/runs/main $R/summary_main.json | grep -v class > $R/summary_main.txt
  python3 - "$R/summary_main.json" <<'PY'
import json, sys
m = json.load(open(sys.argv[1]))['metrics']
zero = ['timing__setup_vio__count', 'timing__hold_vio__count', 'design__max_slew_violation__count',
        'design__max_cap_violation__count', 'design__max_fanout_violation__count', 'route__drc_errors',
        'antenna__violating__nets', 'magic__drc_error__count', 'klayout__drc_error__count',
        'design__lvs_error__count', 'design__xor_difference__count', 'design__disconnected_pin__count']
bad = {k: m.get(k) for k in zero if m.get(k) != 0}
assert not bad, bad
print('macro metrics: all zero-checks passed')
PY
  python3 $E/clock_fanout.py $R/final/nl/g1_digital.nl.v
  run 88-89 python3 designs/g1-guardian/blocks/g1_ctrl/flow/tmr_check.py $R/final/nl/g1_digital.nl.v $R/final/def/g1_digital.def > $R/tmr_separation.txt
  head -3 $R/tmr_separation.txt
  ! grep -q "closer than 20 um: [1-9]" $R/tmr_separation.txt
  run 88 python3 $E/extract_macro_pins.py $P/layout/g1_chip_top_1414_r2.gds __rz_port_text_000_retained_g1_digital $R/pins_chip_r2.json
  run 88 python3 $E/extract_macro_pins.py $R/final/gds/g1_digital.gds g1_digital $R/pins_final.json
  python3 $E/compare_macro_pins.py $R/pins_chip_r2.json $R/pins_final.json $R/pincmp_final.json > /dev/null
  STA_SUB=$(basename "$R")/sta $E/sta_trial.sh $R/final main 95 > $R/logs/sta.log 2>&1
  ! grep -q FAILED-run $R/logs/sta.log
  grep -A1 "^##" $R/logs/sta.log | grep -o "worst_setup_ns\s[-0-9.]*\|worst_hold_ns\s[-0-9.]*" | paste - - > $R/sta_worst.txt
  ! awk '{ if ($2 < 0 || $4 < 0) exit 0; else exit 1 }' $R/sta_worst.txt
  (cd $R/final && sha256sum nl/g1_digital.nl.v pnl/g1_digital.pnl.v sdf/*/*.sdf sdc/g1_digital.sdc spef/nom/g1_digital.nom.spef gds/g1_digital.gds def/g1_digital.def lef/g1_digital.lef) > $R/final_views.sha256
}

chip() {
  mkdir -p $R/chip $R/cdl
  run 88-89 python3 $E/swap_macro.py --chip $P/layout/g1_chip_top_1414_r2.gds --cell __rz_port_text_000_retained_g1_digital \
      --macro $R/final/gds/g1_digital.gds --netlist $R/final/nl/g1_digital.nl.v --def $R/final/def/g1_digital.def \
      --out $R/chip/swapped.gds --report $R/chip/swap.json > $R/logs/swap.log
  python3 -c "import json,sys; d=json.load(open('$R/chip/swap.json')); assert d['swapped'], 'swap checks failed'"
  run 88 python3 $E/add_gatpoly_fill.py --in $R/chip/swapped.gds --out $R/chip/g1_chip_top_1414_r3_candidate.gds \
      --target-um2 700 --exclude-box 367,364,727,724 --obstacles 1/0,5/0,6/0,14/0,7/21,28/0,31/0,32/0,26/0,1/22:300 \
      --min-width-nm 700 --report $R/chip/fill.json > $R/logs/fill.log
  python3 -c "import json; d=json.load(open('$R/chip/fill.json')); assert d['global_ratio_after_pct'] >= 15.02, d['global_ratio_after_pct']"
  python3 $E/regen_chip_cdl.py --canonical $P/netlist/g1_chip_top_1414_r2.cdl --pnl $R/final/pnl/g1_digital.pnl.v \
      --out $R/cdl/g1_chip_top_1414_r3.cdl --projection-out $R/cdl/comparison_only.cdl --report $R/cdl/regen.json \
      --header "g1_chip_top_1414_r3 CANDIDATE ($TAG, not promoted): r2 canonical CDL with g1_digital regenerated from the ECO powered netlist" > /dev/null
  run 89 klayout -b -r $E/flatten_reference.rb -rd source=$R/cdl/comparison_only.cdl \
      -rd output=$R/cdl/g1_chip_top_1414_r3_projected_ref.cdl -rd top=g1_chip_top > $R/logs/flatten.log
}

signoff() {
  local G=$R/chip/g1_chip_top_1414_r3_candidate.gds S=$R/signoff
  mkdir -p $S; sha256sum $G > $S/input_gds.sha256
  export G1_RESULTS_ROOT=$BULK
  flow/launch_pinned.sh 64-67 . 5400 $S/drc_main/run.log python3 $D/drc/run_drc.py --path=$G --topcell=g1_chip_top --run_mode=deep --no_density --disable_extra_rules --density_thr=4 --run_dir=$S/drc_main
  flow/launch_pinned.sh 68-71 . 5400 $S/drc_maximal/run.log python3 $P/flow/signoff/1414/run_maximal.py $G g1_chip_top $S/drc_maximal 4
  flow/launch_pinned.sh 72-73 . 5400 $S/density/run.log python3 $D/drc/run_drc.py --path=$G --topcell=g1_chip_top --run_mode=deep --density_thr=2 --density_only --run_dir=$S/density
  flow/launch_pinned.sh 74-75 . 5400 $S/antenna/run.log python3 $D/drc/run_drc.py --path=$G --topcell=g1_chip_top --run_mode=deep --density_thr=2 --antenna_only --run_dir=$S/antenna --antenna
  flow/launch_pinned.sh 76-77 . 5400 $S/precheck/run.log python3 $D/drc/run_drc.py --path=$G --topcell=g1_chip_top --run_mode=deep --precheck_drc --disable_extra_rules --density_thr=2 --run_dir=$S/precheck
  flow/launch_pinned.sh 78 . 5400 $S/lvs_projected/run.log python3 $D/lvs/run_lvs.py --layout $G --netlist $R/cdl/g1_chip_top_1414_r3_projected_ref.cdl --topcell g1_chip_top --run_mode deep --top_lvl_pins --spice_comments --run_dir $S/lvs_projected
  flow/launch_pinned.sh 79 . 5400 $S/lvs_canonical/run.log python3 $D/lvs/run_lvs.py --layout $G --netlist $R/cdl/g1_chip_top_1414_r3.cdl --topcell g1_chip_top --run_mode deep --top_lvl_pins --spice_comments --run_dir $S/lvs_canonical
  flow/launch_pinned.sh 88 . 5400 $R/chip/chip_xor.log python3 $E/chip_xor.py $P/layout/g1_chip_top_1414_r2.gds $G 367,364,727,724 $R/chip/chip_xor.json
  for c in drc_main drc_maximal density antenna precheck lvs_projected lvs_canonical; do
    while [ ! -f $S/$c/run.log.rc ]; do sleep 20; done
  done
  while [ ! -f $R/chip/chip_xor.log.rc ]; do sleep 20; done
}

post() {
  local G=$R/chip/g1_chip_top_1414_r3_candidate.gds S=$R/signoff
  for k in projected canonical; do
    run 89 klayout -b -r $P/flow/signoff/1414/lvs_pair_counts.py -rd db=$(ls $S/lvs_$k/*.lvsdb) | grep -v Resource > $S/lvs_$k/pair_counts.json
  done
  mkdir -p $R/bondmap
  python3 - "$(sha256sum $G | cut -c1-64)" "$R/bondmap/bondmap_r3cand.csv" <<'PY'
import csv, sys
rows = list(csv.DictReader(open('designs/g1-guardian/padframe/bondmap_20260925_r3.csv')))
w = csv.DictWriter(open(sys.argv[2], 'w', newline=''), fieldnames=list(rows[0].keys())); w.writeheader()
for r in rows:
    r['candidate_gds_sha256'] = sys.argv[1]; r['status'] = 'candidate_not_promoted'; w.writerow(r)
PY
  run 89 klayout -b -r $P/flow/signoff/1414r2/verify_bondmap.py -rd g=$G -rd csvf=$R/bondmap/bondmap_r3cand.csv -rd out=$R/bondmap/verify_bondmap_r3cand.json > /dev/null
  sha256sum $G > $S/input_gds.sha256.after
}

case $STAGE in
  all) macro; chip; signoff; post ;;
  macro) macro ;; chip) chip ;; signoff) signoff ;; post) post ;;
esac
echo "STAGE $STAGE DONE"

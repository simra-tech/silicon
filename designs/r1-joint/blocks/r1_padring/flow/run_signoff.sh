#!/usr/bin/env bash
# Physical checks of the R1 ring, same commands and options as G1 run_candidate.sh 'signoff' (r4 sign-off).
#   G1_CPUSET=... G1_CPUS=4 G1_WORKDIR=designs/r1-joint/blocks/r1_padring G1_RESULTS_ROOT=<results root> \
#   flow/run_signoff.sh <run-dir-under-results-root> <ring.gds> <topcell> <projected_ref.cdl> <canonical.cdl>
# Each check runs in the pinned container through flow/run.sh; independent checks continue after a failure.
set -u
RUN=$1; GDS=$2; TOP=$3; PROJ=$4; CAN=$5
REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../.." && pwd)
D=/foss/pdks/ihp-sg13g2/libs.tech/klayout/tech
W=/work/designs/r1-joint/blocks/r1_padring
S=$RUN/signoff; mkdir -p $S
sha256sum $GDS > $S/input_gds.sha256
run() { name=$1; shift; mkdir -p $S/$name; ( "$REPO/flow/run.sh" "$@" > $S/$name/run.log 2>&1; echo $? > $S/$name/run.log.rc ); }
run drc_main        python3 $D/drc/run_drc.py --path=$GDS --topcell=$TOP --run_mode=deep --no_density --disable_extra_rules --density_thr=4 --run_dir=$S/drc_main
run drc_maximal     python3 $W/flow/run_maximal.py $GDS $TOP $S/drc_maximal 4
run density         python3 $D/drc/run_drc.py --path=$GDS --topcell=$TOP --run_mode=deep --density_thr=4 --density_only --run_dir=$S/density
run antenna         python3 $D/drc/run_drc.py --path=$GDS --topcell=$TOP --run_mode=deep --density_thr=4 --antenna_only --run_dir=$S/antenna --antenna
run precheck        python3 $D/drc/run_drc.py --path=$GDS --topcell=$TOP --run_mode=deep --precheck_drc --disable_extra_rules --density_thr=4 --run_dir=$S/precheck
run lvs_projected   python3 $D/lvs/run_lvs.py --layout $GDS --netlist $PROJ --topcell $TOP --run_mode deep --top_lvl_pins --spice_comments --run_dir $S/lvs_projected
run lvs_canonical   python3 $D/lvs/run_lvs.py --layout $GDS --netlist $CAN  --topcell $TOP --run_mode deep --top_lvl_pins --spice_comments --run_dir $S/lvs_canonical
for k in projected canonical; do
  db=$(ls $S/lvs_$k/*.lvsdb 2>/dev/null | head -1)
  [ -n "$db" ] && "$REPO/flow/run.sh" klayout -b -r $W/flow/lvs_pair_counts.py -rd db=$db 2>/dev/null | grep -v '^time=\|^Resource' > $S/lvs_$k/pair_counts.json
done
sha256sum $GDS > $S/input_gds.sha256.after
echo done > $S/DONE

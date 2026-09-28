#!/usr/bin/env bash
cd ${REPO}
X=${BULK}/r4-20260927/signoff_report_extra
G=designs/g1-guardian/blocks/g1_padring/layout/g1_chip_top_1414_r4.gds
P=designs/g1-guardian/blocks/g1_padring
run() { local log=$1; shift; G1_RESULTS_ROOT=${BULK}/r4-20260927 G1_CPUSET=45-47 G1_CPUS=1 G1_CONTAINER_ENGINE=podman /usr/bin/time -f 'wall_s %e' flow/run.sh "$@" > $X/$log 2>&1; echo $? > $X/$log.rc; }
run verify_bondmap_r4_hashonly.log klayout -b -r $P/flow/signoff/1414r2/verify_bondmap.py -rd g=$G -rd csvf=$X/bondmap_r4chip_hashonly.csv -rd out=$X/verify_bondmap_r4_hashonly.json
run verify_bondmap_r3csv_on_r4.log klayout -b -r $P/flow/signoff/1414r2/verify_bondmap.py -rd g=$G -rd csvf=designs/g1-guardian/padframe/bondmap_20260926_r4.csv -rd out=$X/verify_bondmap_r3csv_on_r4.json
run gds_inventory_r4.log klayout -b -r designs/g1-guardian/review/tapein/gds_inventory.py -rd gds=$G -rd lyp=/foss/pdks/ihp-sg13g2/libs.tech/klayout/tech/sg13g2.lyp -rd out=$X/gds_inventory_g1_chip_top_1414_r4.json
run stock_compare_r4.log klayout -b -r $P/flow/signoff/1414r2/stock_compare.py -rd g=$G -rd out=$X/stock_compare_r4.json

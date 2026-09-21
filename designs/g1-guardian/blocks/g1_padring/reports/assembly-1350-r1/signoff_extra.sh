#!/usr/bin/env bash
# Extra sign-off on the assembly GDS: DRC with recommended rules, DRC precheck, density with per-window detail.
set -u
GDS=$1; OUT=$2; mkdir -p $OUT
D=/foss/pdks/ihp-sg13g2/libs.tech/klayout/tech/drc
echo "== DRC recommended (no_recommended=false)"; klayout -b -zz -r $D/ihp-sg13g2.drc -rd input=$GDS -rd topcell=g1_chip_top -rd report=$OUT/drc_recommended.lyrdb -rd run_mode=deep -rd threads=8 > $OUT/drc_recommended.log 2>&1; grep -c "<item>" $OUT/drc_recommended.lyrdb
echo "== DRC precheck (precheck_drc=true, no_recommended=true)"; klayout -b -zz -r $D/ihp-sg13g2.drc -rd input=$GDS -rd topcell=g1_chip_top -rd report=$OUT/drc_precheck.lyrdb -rd run_mode=deep -rd no_recommended=true -rd precheck_drc=true -rd threads=8 > $OUT/drc_precheck.log 2>&1; grep -c "<item>" $OUT/drc_precheck.lyrdb
echo "== density (default) with per-window detail"; klayout -b -zz -r $D/rule_decks/density.drc -rd input=$GDS -rd topcell=g1_chip_top -rd report=$OUT/density.lyrdb -rd threads=8 > $OUT/density.log 2>&1; grep -c "<item>" $OUT/density.lyrdb
echo "== density precheck"; klayout -b -zz -r $D/rule_decks/density.drc -rd input=$GDS -rd topcell=g1_chip_top -rd report=$OUT/density_precheck.lyrdb -rd precheck_drc=true -rd threads=8 > $OUT/density_precheck.log 2>&1; grep -c "<item>" $OUT/density_precheck.lyrdb
grep -h "Using prBoundary\|Using EdgeSeal\|No prBoundary" $OUT/density.log

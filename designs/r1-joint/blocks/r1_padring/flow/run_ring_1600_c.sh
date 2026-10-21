#!/bin/sh
# Revision c (run ring-20261021-c): rebuild the 1600 um ring, write the 1600 um references with the real IO filler
# population, run all checks.  POSIX shell; every tool through flow/run.sh.
#   G1_CPUSET=116-119; G1_CPUS=4; G1_RESULTS_ROOT=<results root>; export G1_CPUSET G1_CPUS G1_RESULTS_ROOT
#   designs/r1-joint/blocks/r1_padring/flow/run_ring_1600_c.sh            (from the repository root)
set -eu
G1_WORKDIR=designs/r1-joint/blocks/r1_padring; export G1_WORKDIR
B=$G1_WORKDIR; W=/work/$B; ID=ring-20261021-c
R=$G1_RESULTS_ROOT/r1_padring/$ID; A=$G1_RESULTS_ROOT/r1_padring/ring-20261020-a; C=reports/$ID
mkdir -p "$R" "$B/$C"
# 1 build, fill, timestamp-free rewrite (generator unchanged from revision b; output must be 40514b4f...)
flow/run.sh klayout -b -r flow/build_ring_1600.py -rd src=$A/r1_padring_nofill.gds -rd io_gds=/foss/pdks/ihp-sg13g2/libs.ref/sg13g2_io/gds/sg13g2_io.gds -rd out=$R/r1_padring_1600_nofill.gds -rd report=$R/build_ring_1600.json
flow/run.sh bash -c "KLAYOUT_PATH=\$PDK_ROOT/\$PDK/libs.tech/klayout klayout -n sg13g2 -zz -r \$PDK_ROOT/\$PDK/libs.tech/klayout/tech/scripts/filler.py -rd output_file=$R/r1_padring_1600_filled_raw.gds $R/r1_padring_1600_nofill.gds" > $R/fill.log 2>&1
flow/run.sh klayout -b -r flow/rewrite_gds.py -rd i=$R/r1_padring_1600_filled_raw.gds -rd o=$R/r1_padring_1600.gds
sed "s#$G1_RESULTS_ROOT#<G1_RESULTS_ROOT>#g" $R/build_ring_1600.json > $B/$C/build_ring_1600.json
# 2 references with the filler population of the build report (the fix of revision c)
( cd $B && python3 flow/make_cdl.py ../../../g1-guardian/blocks/g1_padring/netlist/g1_chip_top_1414_r4.cdl netlist/r1_padring_1600.cdl netlist/r1_padring_1600_projection_src.cdl netlist/r1_padring_1600_ringonly_projection_src.cdl --fillers=$C/build_ring_1600.json )
flow/run.sh klayout -b -r flow/flatten_reference.rb -rd source=$W/netlist/r1_padring_1600_projection_src.cdl -rd output=$W/netlist/r1_padring_1600_projected_ref.cdl -rd top=r1_padring
flow/run.sh klayout -b -r flow/flatten_reference.rb -rd source=$W/netlist/r1_padring_1600_ringonly_projection_src.cdl -rd output=$W/netlist/r1_padring_1600_ringonly_projected_ref.cdl -rd top=r1_padring
# 3 checks: ring-only LVS in parallel with run_signoff.sh (DRC main/maximal/precheck/density/antenna, LVS G1 form, canonical)
mkdir -p $R/signoff/lvs_projected_ringonly
( flow/run.sh python3 /foss/pdks/ihp-sg13g2/libs.tech/klayout/tech/lvs/run_lvs.py --layout $R/r1_padring_1600.gds --netlist $W/netlist/r1_padring_1600_ringonly_projected_ref.cdl --topcell r1_padring --run_mode deep --top_lvl_pins --spice_comments --run_dir $R/signoff/lvs_projected_ringonly > $R/signoff/lvs_projected_ringonly/run.log 2>&1; echo $? > $R/signoff/lvs_projected_ringonly/run.log.rc ) &
$B/flow/run_signoff.sh $R $R/r1_padring_1600.gds r1_padring $W/netlist/r1_padring_1600_projected_ref.cdl $W/netlist/r1_padring_1600.cdl
wait
# 4 geometry, abutment, bond map, PNG
flow/run.sh klayout -b -r flow/measure_ring_1600.py -rd g=$R/r1_padring_1600.gds -rd out=$C/measure_ring_1600.json -rd ref=$A/r1_padring_a.gds
flow/run.sh klayout -b -r flow/compare_order.py -rd a=$A/r1_padring_a.gds -rd b=$R/r1_padring_1600.gds -rd out=$C/compare_order.json
flow/run.sh klayout -b -r flow/check_abutment.py -rd gds=$R/r1_padring_1600_nofill.gds -rd out=$C/abutment_1600_nofill.json
G1_WORKDIR=. flow/run.sh klayout -b -r $B/flow/verify_bondmap.py -rd g=$R/r1_padring_1600.gds -rd csvf=designs/r1-joint/padframe/bondmap_r1_1600_ring.csv -rd out=$B/$C/verify_bondmap_r1_1600.json
flow/run.sh klayout -b -r flow/screenshot_ring.py -rd g=$R/r1_padring_1600.gds -rd png=$C/r1_padring_1600.png -rd w=700

#!/bin/sh
# Revision d (run ring-20261021-d): build the 1700 um ring, write the references with the real IO filler population, run the checks.
# Command record. POSIX shell; every tool through flow/run.sh; ONE KLayout job at a time (CPUs shared with other tracks).
# The steps were run one by one (build, fill, rewrite, references) and the checks by a detached driver in the results root.
#   G1_CPUSET=116-119; G1_CPUS=4; G1_RESULTS_ROOT=<results root>; export G1_CPUSET G1_CPUS G1_RESULTS_ROOT
#   designs/r1-joint/blocks/r1_padring/flow/run_ring_1700_d.sh          (from the repository root)
set -eu
G1_WORKDIR=designs/r1-joint/blocks/r1_padring; export G1_WORKDIR
B=$G1_WORKDIR; W=/work/$B; ID=ring-20261021-d
R=$G1_RESULTS_ROOT/r1_padring/$ID; A=$G1_RESULTS_ROOT/r1_padring/ring-20261020-a; C=$B/reports/$ID
D=/foss/pdks/ihp-sg13g2/libs.tech/klayout/tech
mkdir -p "$R" "$C"
# 1 build, fill, timestamp-free rewrite
flow/run.sh klayout -b -r $W/flow/build_ring_1700.py -rd src=$A/r1_padring_nofill.gds -rd io_gds=/foss/pdks/ihp-sg13g2/libs.ref/sg13g2_io/gds/sg13g2_io.gds -rd out=$R/r1_padring_1700_nofill.gds -rd report=$R/build_ring_1700.json
flow/run.sh bash -c "KLAYOUT_PATH=\$PDK_ROOT/\$PDK/libs.tech/klayout klayout -n sg13g2 -zz -r \$PDK_ROOT/\$PDK/libs.tech/klayout/tech/scripts/filler.py -rd output_file=$R/r1_padring_1700_filled_raw.gds $R/r1_padring_1700_nofill.gds" > $R/fill.log 2>&1
flow/run.sh klayout -b -r $W/flow/rewrite_gds.py -rd i=$R/r1_padring_1700_filled_raw.gds -rd o=$R/r1_padring_1700.gds
sed "s#$G1_RESULTS_ROOT#<G1_RESULTS_ROOT>#g" $R/build_ring_1700.json > $C/build_ring_1700.json
# 2 references with the filler population of the build report
( cd $B && python3 flow/make_cdl.py ../../../g1-guardian/blocks/g1_padring/netlist/g1_chip_top_1414_r4.cdl netlist/r1_padring_1700.cdl netlist/r1_padring_1700_projection_src.cdl netlist/r1_padring_1700_ringonly_projection_src.cdl --fillers=reports/$ID/build_ring_1700.json )
flow/run.sh klayout -b -r $W/flow/flatten_reference.rb -rd source=$W/netlist/r1_padring_1700_projection_src.cdl -rd output=$W/netlist/r1_padring_1700_projected_ref.cdl -rd top=r1_padring
flow/run.sh klayout -b -r $W/flow/flatten_reference.rb -rd source=$W/netlist/r1_padring_1700_ringonly_projection_src.cdl -rd output=$W/netlist/r1_padring_1700_ringonly_projected_ref.cdl -rd top=r1_padring
python3 $B/flow/make_lef.py $B/layout/r1_padring_1700_ref.lef 1700
# 3 geometry, bond map, PNG (one job after the other)
GDS=$R/r1_padring_1700.gds; SHA=$(sha256sum $GDS | cut -d' ' -f1)
flow/run.sh klayout -b -r $W/flow/measure_ring_1700.py -rd g=$GDS -rd out=$W/reports/$ID/measure_ring_1700.json -rd ref=$A/r1_padring_a.gds
flow/run.sh klayout -b -r $W/flow/compare_order.py -rd a=$A/r1_padring_a.gds -rd b=$GDS -rd out=$W/reports/$ID/compare_order.json
flow/run.sh klayout -b -r $W/flow/check_abutment.py -rd gds=$R/r1_padring_1700_nofill.gds -rd out=$W/reports/$ID/abutment_1700_nofill.json
G1_WORKDIR=. flow/run.sh klayout -b -r designs/r1-joint/padframe/bondplan_r1.py -rd gds=$GDS -rd src_csv=designs/r1-joint/padframe/bondmap_src_r1_1700.csv -rd out_csv=designs/r1-joint/padframe/bondmap_r1_1700_ring.csv -rd out_svg=designs/r1-joint/padframe/bondplan_r1_1700.svg -rd out_json=designs/r1-joint/padframe/bondplan_r1_1700.json -rd gds_sha=$SHA -rd die_um=1700
G1_WORKDIR=. flow/run.sh klayout -b -r $B/flow/verify_bondmap.py -rd g=$GDS -rd csvf=designs/r1-joint/padframe/bondmap_r1_1700_ring.csv -rd out=$B/reports/$ID/verify_bondmap_r1_1700.json
flow/run.sh klayout -b -r $W/flow/screenshot_ring.py -rd g=$GDS -rd png=$W/reports/$ID/r1_padring_1700.png -rd w=700
# 4 DRC and LVS, one after the other (each prints its own run directory under $R/signoff)
S=$R/signoff; mkdir -p $S; sha256sum $GDS > $S/input_gds.sha256; TOP=r1_padring
flow/run.sh python3 $D/drc/run_drc.py --path=$GDS --topcell=$TOP --run_mode=deep --no_density --disable_extra_rules --density_thr=4 --run_dir=$S/drc_main
flow/run.sh python3 $W/flow/run_maximal.py $GDS $TOP $S/drc_maximal 4
flow/run.sh python3 $D/drc/run_drc.py --path=$GDS --topcell=$TOP --run_mode=deep --precheck_drc --disable_extra_rules --density_thr=4 --run_dir=$S/precheck
flow/run.sh python3 $D/drc/run_drc.py --path=$GDS --topcell=$TOP --run_mode=deep --density_thr=4 --density_only --run_dir=$S/density
flow/run.sh python3 $D/drc/run_drc.py --path=$GDS --topcell=$TOP --run_mode=deep --density_thr=4 --antenna_only --run_dir=$S/antenna --antenna || true   # exit 1 expected: empty core
flow/run.sh python3 $D/lvs/run_lvs.py --layout $GDS --netlist $W/netlist/r1_padring_1700_ringonly_projected_ref.cdl --topcell $TOP --run_mode deep --top_lvl_pins --spice_comments --run_dir $S/lvs_projected_ringonly
flow/run.sh python3 $D/lvs/run_lvs.py --layout $GDS --netlist $W/netlist/r1_padring_1700_projected_ref.cdl --topcell $TOP --run_mode deep --top_lvl_pins --spice_comments --run_dir $S/lvs_projected || true
# the canonical LVS (netlist/r1_padring_1700.cdl) was not run in revision d
sha256sum $GDS > $S/input_gds.sha256.after

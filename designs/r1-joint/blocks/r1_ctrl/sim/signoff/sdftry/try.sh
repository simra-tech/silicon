export LD_LIBRARY_PATH=/foss/tools/iverilog/lib
V=/foss/pdks/ihp-sg13g2/libs.ref/sg13g2_stdcell/verilog
T7=$G1_RESULTS_ROOT/r1_ctrl/r1ctrl_ll_20261021_t7/flow/runs/r1ctrl_ll_20261021_t7/final
O=$G1_RESULTS_ROOT/r1_ctrl/r1ctrl_sdftry_20261021; mkdir -p $O; cd $O
python3 /work/designs/r1-joint/blocks/r1_ctrl/sim/signoff/prep_sdf.py $T7/nl/r1_ctrl_top.nl.v $T7/sdf/nom_slow_1p08V_125C/r1_ctrl_top__nom_slow_1p08V_125C.sdf $O/nl2.v $O/d2.sdf max
iverilog -g2005 -gspecify -ginterconnect -Wno-timescale -o tb_sdf2.vvp $V/sg13g2_udp.v $V/sg13g2_stdcell.v $O/nl2.v /work/designs/r1-joint/blocks/r1_ctrl/sim/signoff/sdftry/tb_sdf.v > c2.log 2>&1
vvp -n tb_sdf2.vvp +sdf=$O/d2.sdf 2>&1 | grep -v "TIMINGCHECK not supported" | head -12 | cut -c1-200
vvp -n tb_sdf2.vvp +sdf=$O/d2.sdf 2>&1 | grep -c "TIMINGCHECK not supported"

# Revision 0.9 (T5j, PLAN.md D30 item 4): hold check of a hardening run with the ADC minimum input delay set to ADCMIN ns.
# Same OpenSTA setup as sta_true.tcl (one liberty corner, final netlist, nominal SPEF, sign-off SDC flow/r1_ctrl.sdc);
# after the SDC, set_input_delay -min on the ADC inputs is replaced by ADCMIN. env: RUN, LIBNAME, CORNER, ADCMIN
set run $::env(RUN)
read_liberty /foss/pdks/ihp-sg13g2/libs.ref/sg13g2_stdcell/lib/sg13g2_stdcell_$::env(LIBNAME).lib
read_verilog $run/final/nl/r1_ctrl_top.nl.v
link_design r1_ctrl_top
read_sdc flow/r1_ctrl.sdc
read_spef $run/final/spef/nom/r1_ctrl_top.nom.spef
set adc [get_ports {adc_valid_a adc_valid_b adc_raw_a[*] adc_raw_b[*]}]
set_input_delay -clock clk -min $::env(ADCMIN) $adc
puts "=== $::env(CORNER) ADC -min input delay $::env(ADCMIN) ns"
report_worst_slack -min -digits 4
report_worst_slack -max -digits 4
puts "--- worst hold from the ADC inputs"
report_checks -path_delay min -from $adc -group_path_count 1 -digits 4
puts "--- worst hold, all paths"
report_checks -path_delay min -group_path_count 1 -digits 4

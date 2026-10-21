# EN (en_pad) to gate outputs: combinational input-to-output delay, three corners. env: RUN, LIBNAME
set run $::env(RUN)
read_liberty /foss/pdks/ihp-sg13g2/libs.ref/sg13g2_stdcell/lib/sg13g2_stdcell_$::env(LIBNAME).lib
read_verilog $run/final/nl/r1_ctrl_top.nl.v
link_design r1_ctrl_top
create_clock -name clk -period 23.81 [get_ports clk]
set_propagated_clock [all_clocks]
read_spef $run/final/spef/nom/r1_ctrl_top.nom.spef
set_input_delay 0 -clock clk [get_ports en_pad]
set_output_delay 0 -clock clk [get_ports {gate_a gate_b gate_c}]
set_load 0.05 [all_outputs]
foreach g {gate_a gate_b gate_c} {
  puts "=== $::env(LIBNAME) en_pad -> $g (max delay, unconstrained path report)"
  report_checks -path_delay max -from [get_ports en_pad] -to [get_ports $g] -digits 4 -fields {fanout cap slew}
}

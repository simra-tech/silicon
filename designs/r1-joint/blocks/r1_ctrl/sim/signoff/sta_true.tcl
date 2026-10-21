# True-slack STA of the t7 post-layout netlist + SPEF (OpenSTA), one corner per call.
# env: CORNER (nom_typ_1p20V_25C ...), LIBNAME (stdcell lib file stem), RUN (t7 run dir), OUTDIR
set corner $::env(CORNER)
set run $::env(RUN)
read_liberty /foss/pdks/ihp-sg13g2/libs.ref/sg13g2_stdcell/lib/sg13g2_stdcell_$::env(LIBNAME).lib
read_verilog $run/final/nl/r1_ctrl_top.nl.v
link_design r1_ctrl_top
read_sdc $run/final/sdc/r1_ctrl_top.sdc
read_spef $run/final/spef/nom/r1_ctrl_top.nom.spef
puts "=== $corner worst slack (all groups)"
report_worst_slack -max -digits 4
report_worst_slack -min -digits 4
report_tns -digits 4
set ff [all_registers -edge_triggered -data_pins]
set la [all_registers -level_sensitive -data_pins]
puts "=== $corner setup to edge-triggered flop D (3 worst unique endpoints)"
report_checks -path_delay max -to $ff -group_path_count 3 -unique_paths_to_endpoint -sort_by_slack -digits 4 -fields {fanout}
puts "=== $corner setup to output ports"
report_checks -path_delay max -to [all_outputs] -group_path_count 3 -unique_paths_to_endpoint -sort_by_slack -digits 4
puts "=== $corner setup to level-sensitive latch D (time borrowing; 3 worst by borrow)"
report_checks -path_delay max -to $la -group_path_count 3 -unique_paths_to_endpoint -sort_by_slack -digits 4
puts "=== $corner clock-gating and recovery/removal groups"
foreach g {"gated clock" asynchronous ma} {
  puts "--- path group $g"
  report_checks -path_delay max -path_group $g -group_path_count 2 -unique_paths_to_endpoint -sort_by_slack -digits 4
}
puts "=== $corner hold (3 worst)"
report_checks -path_delay min -group_path_count 3 -unique_paths_to_endpoint -sort_by_slack -digits 4 -format full_clock_expanded
puts "=== $corner max fanout violators"
report_check_types -max_fanout -violators -digits 3
puts "max fanout violation count [sta::max_fanout_violation_count]"

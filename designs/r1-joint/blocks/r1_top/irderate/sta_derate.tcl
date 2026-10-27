# SPDX-License-Identifier: Apache-2.0
# r1_top try g, ctrl IR-drop derate (track T11b), step 2: OpenSTA on the r1_ctrl 0.8 release netlist with a
# voltage-scaled cell delay. Same inputs as the 0.8 sign-off (sim/signoff/sta_true.tcl of r1_ctrl): liberty corner
# LIBNAME, release netlist, release sign-off SDC, nominal SPEF of run r1ctrl_ll_20261027_t22.
# env: LIBNAME, NETLIST, SDC, SPEF, CASES = "name:early:late name:early:late ..." (set_timing_derate factors,
# applied to cell delays and cell timing checks, clock and data paths).
read_liberty /foss/pdks/ihp-sg13g2/libs.ref/sg13g2_stdcell/lib/sg13g2_stdcell_$::env(LIBNAME).lib
read_verilog $::env(NETLIST)
link_design r1_ctrl_top
read_sdc $::env(SDC)
read_spef $::env(SPEF)
set ff [all_registers -edge_triggered -data_pins]
set la [all_registers -level_sensitive -data_pins]
foreach c $::env(CASES) {
  lassign [split $c :] name early late
  catch {unset_timing_derate}
  set_timing_derate -early -cell_delay $early
  set_timing_derate -late -cell_delay $late
  set_timing_derate -early -cell_check $early
  set_timing_derate -late -cell_check $late
  puts "=== CASE $name early $early late $late"
  report_worst_slack -max -digits 4
  report_worst_slack -min -digits 4
  report_tns -digits 4
  puts "--- setup to flop D"
  report_checks -path_delay max -to $ff -group_path_count 1 -sort_by_slack -digits 4
  puts "--- setup to outputs"
  report_checks -path_delay max -to [all_outputs] -group_path_count 1 -sort_by_slack -digits 4
  puts "--- setup to latch D"
  report_checks -path_delay max -to $la -group_path_count 1 -sort_by_slack -digits 4
  puts "--- hold"
  report_checks -path_delay min -group_path_count 1 -sort_by_slack -digits 4
  puts "=== END $name"
}

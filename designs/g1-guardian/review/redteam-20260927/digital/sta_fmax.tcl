# Red-team 2026-09-27: reg-to-reg setup slack per clock at a 100 ns constraint, r3 g1_digital (nl 4b83f181,
# SPEF 0b626c7f) -> minimum clock period the core logic tolerates. Env: CORNER, MACRO_NL, MACRO_SPEF, OUT.
set corner $::env(CORNER); set out $::env(OUT)
set pdk /foss/pdks/ihp-sg13g2
array set sc {fast fast_1p32V_m40C typ typ_1p20V_25C slow slow_1p08V_125C}
set sta_report_default_digits 3
read_liberty $pdk/libs.ref/sg13g2_stdcell/lib/sg13g2_stdcell_$sc($corner).lib
read_verilog $::env(MACRO_NL)
link_design g1_digital
read_sdc /work/designs/g1-guardian/blocks/g1_ctrl/flow/g1_digital.sdc
read_spef $::env(MACRO_SPEF)
set fp [open $out/fmax_$corner.tsv w]
foreach c {osc_clk sclk} {
  set p [find_timing_paths -path_delay max -from [all_registers -clock $c -clock_pins] -to [all_registers -clock $c -data_pins] -group_path_count 1]
  if {[llength $p]} { puts $fp "$c\treg2reg_setup_slack_ns_at_100ns\t[get_property [lindex $p 0] slack]" } else { puts $fp "$c\tno_path" }
}
# asynchronous group (recovery) and outputs
set p [find_timing_paths -path_delay max -to [get_ports {trip_d clr_d fast_en cmp_clk dac_hard[*] dac_soft[*]}] -group_path_count 1]
puts $fp "osc_outputs_setup_slack_ns_at_100ns_with_20ns_output_delay\t[get_property [lindex $p 0] slack]"
close $fp
report_checks -path_delay max -from [all_registers -clock osc_clk -clock_pins] -to [all_registers -clock osc_clk -data_pins] -format full > $out/fmax_path_$corner.rpt
puts "FMAX_DONE $corner"

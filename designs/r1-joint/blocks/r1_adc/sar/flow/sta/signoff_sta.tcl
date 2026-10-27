# r1_adc_sar sign-off STA (T2j) on the final netlist and SPEF with flow/r1_adc_sar.sdc, one corner per call:
#   env SAR_NL=<nl.v> SAR_SPEF=<spef> SAR_LIB=<liberty> SAR_TAG=<corner> SAR_SDC=<sdc> sta -no_splash -exit signoff_sta.tcl
# Same data as LibreLane OpenROAD.STAPostPNR (nom RC extraction) with the sign-off SDC of record.
read_liberty $::env(SAR_LIB)
read_verilog $::env(SAR_NL)
link_design r1_adc_sar
read_spef $::env(SAR_SPEF)
read_sdc $::env(SAR_SDC)
puts "CORNER $::env(SAR_TAG)"
report_worst_slack -max -digits 4
report_worst_slack -min -digits 4
report_tns -max -digits 4
report_tns -min -digits 4
foreach g {clk mclk} {
  foreach t {max min} {
    set pe [find_timing_paths -path_group $g -path_delay $t -group_path_count 1]
    if {[llength $pe]} { puts "GROUP $g $t [sta::format_time [[lindex $pe 0] slack] 4] [get_full_name [[lindex $pe 0] pin]]" }
  }
}
puts "GATING_BEGIN"
report_checks -path_delay max -path_group [list {gated clock}] -group_path_count 1 -digits 4
report_checks -path_delay min -path_group [list {gated clock}] -group_path_count 1 -digits 4
puts "GATING_END"
report_check_types -max_slew -max_capacitance -max_fanout -violators
report_checks -path_delay max -group_path_count 3 -digits 3 -fields {slew cap}
report_checks -path_delay min -group_path_count 3 -digits 3 -fields {slew cap}
report_checks -unconstrained -path_delay max -to [get_ports {cpa[*] cna[*] cpb[*] cnb[*]}] -digits 3

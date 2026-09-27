# Red-team 2026-09-27: macro hold/setup/recovery-removal with an OCV derate on the r3 g1_digital
# (nl 4b83f181, SPEF 0b626c7f), and a slack histogram. Env: CORNER, DERATE (e.g. 0.10), MACRO_NL, MACRO_SPEF, OUT.
set corner $::env(CORNER); set d $::env(DERATE); set out $::env(OUT)
set pdk /foss/pdks/ihp-sg13g2
array set sc {fast fast_1p32V_m40C typ typ_1p20V_25C slow slow_1p08V_125C}
set sta_report_default_digits 4
read_liberty $pdk/libs.ref/sg13g2_stdcell/lib/sg13g2_stdcell_$sc($corner).lib
read_verilog $::env(MACRO_NL)
link_design g1_digital
read_sdc /work/designs/g1-guardian/blocks/g1_ctrl/flow/g1_digital.sdc
read_spef $::env(MACRO_SPEF)
if {$d > 0} {
  set_timing_derate -early [expr {1.0 - $d}]
  set_timing_derate -late  [expr {1.0 + $d}]
}
set fp [open $out/summary_$corner\_d$d.tsv w]
puts $fp "corner\t$corner\nderate\t$d"
puts $fp "worst_setup_ns\t[worst_slack -max]"
puts $fp "worst_hold_ns\t[worst_slack -min]"
puts $fp "tns_hold_ns\t[total_negative_slack -min]"
# hold slack histogram over all endpoints (min paths)
set b50 0; set b100 0; set b150 0; set n 0
foreach p [find_timing_paths -path_delay min -group_path_count 100000 -endpoint_path_count 1 -slack_max 0.3] {
  set s [get_property $p slack]; incr n
  if {$s < 0.05} {incr b50}; if {$s < 0.10} {incr b100}; if {$s < 0.15} {incr b150}
}
puts $fp "hold_endpoints_slack_lt_0p30\t$n\nhold_lt_0p05\t$b50\nhold_lt_0p10\t$b100\nhold_lt_0p15\t$b150"
close $fp
report_checks -path_delay min -group_path_count 5 -format end > $out/hold_top_$corner\_d$d.rpt
report_checks -path_delay min -group_path_count 1 -path_group sclk -format full_clock_expanded > $out/hold_sclk_$corner\_d$d.rpt
puts "DERATE_DONE $corner $d"

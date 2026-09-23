set_thread_count 1
if {[catch {source {/usr/local/lib/python3.12/dist-packages/librelane/scripts/openroad/cts.tcl}} detail options]} {puts [dict get $options -errorinfo]; exit 1}
report_check_types -max_slew -max_capacitance -max_fanout -violators > {${RESULTS_ROOT}/digital-cts-baseline-20260923-r3/macro_violators.rpt}
set_max_fanout 8 [current_design]
report_check_types -max_fanout -violators > {${RESULTS_ROOT}/digital-cts-baseline-20260923-r3/integrated_fanout.rpt}
set fp [open {${RESULTS_ROOT}/digital-cts-baseline-20260923-r3/counts.tsv} w]
foreach name {sclk osc_clk} {puts $fp "$name\t[llength [all_registers -clock $name]]"}
close $fp
puts CTS_FANOUT_EXPERIMENT_COMPLETE

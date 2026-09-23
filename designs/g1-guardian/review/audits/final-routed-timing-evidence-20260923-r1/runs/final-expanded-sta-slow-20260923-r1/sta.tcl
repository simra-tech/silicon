set sta_report_default_digits 9
define_corners CURRENT
read_liberty -corner CURRENT {/foss/pdks/ihp-sg13g2/libs.ref/sg13g2_stdcell/lib/sg13g2_stdcell_slow_1p08V_125C.lib}
read_liberty -corner CURRENT {@REPO@/designs/g1-guardian/blocks/g1_padring/ip/sg13g2_io_padbare/lib/sg13g2_io_slow_1p08V_3p0V_125C.lib}
read_verilog {@RESULTS@/final-expanded-sta-slow-20260923-r1/g1_trip_declaration.v}
read_verilog {@RESULTS@/final-expanded-sta-slow-20260923-r1/g1_osc_declaration.v}
read_verilog {@REPO@/designs/g1-guardian/blocks/g1_ctrl/layout/g1_digital.nl.v}
read_verilog {@RESULTS@/final-routed-rcx-20260923-r1/final_signal.nl.v}
link_design g1_chip_top
set ::env(DESIGN_NAME) g1_chip_top
set ::env(CLOCK_PORT) SCLK
set ::env(CLOCK_NET) pad14_sclk/p2c
set ::env(CLOCK_PERIOD) 100
set ::env(IO_DELAY_CONSTRAINT) 20
set ::env(MAX_FANOUT_CONSTRAINT) 10
set ::env(OUTPUT_CAP_LOAD) 6.0
set ::env(CLOCK_UNCERTAINTY_CONSTRAINT) 0.25
set ::env(CLOCK_TRANSITION_CONSTRAINT) 0.15
set ::env(TIME_DERATING_CONSTRAINT) 5
read_sdc {@REPO@/designs/g1-guardian/blocks/g1_padring/flow/g1_chip_top.sdc}
read_spef -corner CURRENT {@RESULTS@/final-routed-rcx-20260923-r1/final_signal.nom.spef}
read_spef -corner CURRENT -path i_core.u_digital {@REPO@/designs/g1-guardian/blocks/g1_ctrl/layout/g1_digital.nom.spef}
set fp [open {@RESULTS@/final-expanded-sta-slow-20260923-r1/counts.tsv} w]
foreach name {SCLK osc_clk} {
  if {[llength [get_clocks -quiet $name]] != 1} {error "Clock missing or duplicated: $name"}
  puts $fp "$name	[llength [all_registers -clock $name]]"
}
close $fp
report_checks -path_delay min -fields {slew cap input net fanout} -format full_clock_expanded -group_path_count 20 > {@RESULTS@/final-expanded-sta-slow-20260923-r1/hold.rpt}
report_checks -path_delay max -fields {slew cap input net fanout} -format full_clock_expanded -group_path_count 20 > {@RESULTS@/final-expanded-sta-slow-20260923-r1/setup.rpt}
report_check_types -max_slew -max_capacitance -max_fanout -violators > {@RESULTS@/final-expanded-sta-slow-20260923-r1/violators.rpt}
report_parasitic_annotation -report_unannotated > {@RESULTS@/final-expanded-sta-slow-20260923-r1/annotation.rpt}
check_setup -verbose -unconstrained_endpoints -multiple_clock -no_clock -no_input_delay -loops -generated_clocks > {@RESULTS@/final-expanded-sta-slow-20260923-r1/coverage.rpt}
set fp [open {@RESULTS@/final-expanded-sta-slow-20260923-r1/slack.tsv} w]
puts $fp "hold	[worst_slack -min]"
puts $fp "setup	[worst_slack -max]"
close $fp
puts "FINAL_EXPANDED_STA_COMPLETE"

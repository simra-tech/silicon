# OpenSTA on the g1_digital run7 macro, standalone and expanded in the routed chip netlist.
# Environment: CASE = macro | chip_template | chip_merged ; CORNER = fast | typ | slow ; OUT = output dir.
# Paths are container paths (repository at /work). See README.md.
set case   $::env(CASE)
set corner $::env(CORNER)
set out    $::env(OUT)
set R /work/designs/g1-guardian
set pdk /foss/pdks/ihp-sg13g2
array set sc {fast fast_1p32V_m40C typ typ_1p20V_25C slow slow_1p08V_125C}
array set io {fast fast_1p32V_3p6V_m40C typ typ_1p2V_3p3V_25C slow slow_1p08V_3p0V_125C}
set sta_report_default_digits 4
define_corners CURRENT
read_liberty -corner CURRENT $pdk/libs.ref/sg13g2_stdcell/lib/sg13g2_stdcell_$sc($corner).lib
set macro_nl   $R/blocks/g1_ctrl/layout/g1_digital.nl.v
set macro_spef $R/blocks/g1_ctrl/layout/g1_digital.nom.spef
set ev $R/review/audits/final-routed-timing-evidence-20260923-r1/runs
if { $case eq "macro" } {
    read_verilog $macro_nl
    link_design g1_digital
    read_sdc $R/blocks/g1_ctrl/flow/g1_digital.sdc
    read_spef -corner CURRENT $macro_spef
    set clks {osc_clk sclk}
} else {
    read_liberty -corner CURRENT $R/blocks/g1_padring/ip/sg13g2_io_padbare/lib/sg13g2_io_$io($corner).lib
    read_verilog $ev/final-sta-allnets-fast-20260923-r1/g1_trip_declaration.v
    read_verilog $ev/final-sta-allnets-fast-20260923-r1/g1_osc_declaration.v
    read_verilog $macro_nl
    read_verilog $ev/final-routed-rcx-20260923-r1/final_signal.nl.v
    link_design g1_chip_top
    # values of the chip flow configuration (assembly-1350 _env.tcl), as in FINAL_ROUTED_TIMING_20260923
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
    if { $case eq "chip_template" } {
        read_sdc $::env(TEMPLATE_SDC)
    } else {
        read_sdc $R/blocks/g1_padring/flow/g1_chip_top.sdc
    }
    read_spef -keep_capacitive_coupling -corner CURRENT $ev/final-routed-rcx-20260923-r1/final_signal.nom.spef
    read_spef -keep_capacitive_coupling -name CURRENT -path i_core.u_digital $macro_spef
    set clks {SCLK osc_clk}
}
set fp [open $out/summary.tsv w]
puts $fp "case\t$case\ncorner\t$corner"
foreach c $clks {
    if {[llength [get_clocks -quiet $c]]} {
        puts $fp "registers_$c\t[llength [all_registers -clock $c]]"
    } else { puts $fp "registers_$c\tclock_not_defined" }
}
puts $fp "worst_setup_ns\t[worst_slack -max]"
puts $fp "worst_hold_ns\t[worst_slack -min]"
puts $fp "tns_setup_ns\t[total_negative_slack -max]"
puts $fp "tns_hold_ns\t[total_negative_slack -min]"
close $fp
report_checks -path_delay max -group_path_count 1 -format full_clock_expanded -fields {slew cap fanout} > $out/setup_worst.rpt
report_checks -path_delay min -group_path_count 1 -format full_clock_expanded -fields {slew cap fanout} > $out/hold_worst.rpt
report_checks -path_delay min -slack_max 0 -group_path_count 100000 -endpoint_path_count 1 -format end > $out/hold_violators.rpt
report_checks -path_delay max -slack_max 0 -group_path_count 100000 -endpoint_path_count 1 -format end > $out/setup_violators.rpt
report_check_types -max_slew -max_capacitance -max_fanout -violators > $out/drv_violators.rpt
report_parasitic_annotation -report_unannotated > $out/annotation.rpt
check_setup -verbose -unconstrained_endpoints -multiple_clock -no_clock -no_input_delay -loops -generated_clocks > $out/coverage.rpt
puts "STA_MERGED_COMPLETE $case $corner"

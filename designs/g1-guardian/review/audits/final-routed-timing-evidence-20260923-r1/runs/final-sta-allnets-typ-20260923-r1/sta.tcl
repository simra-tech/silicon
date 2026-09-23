set sta_report_default_digits 9
define_corners CURRENT
read_liberty -corner CURRENT {/foss/pdks/ihp-sg13g2/libs.ref/sg13g2_stdcell/lib/sg13g2_stdcell_typ_1p20V_25C.lib}
read_liberty -corner CURRENT {@REPO@/designs/g1-guardian/blocks/g1_padring/ip/sg13g2_io_padbare/lib/sg13g2_io_typ_1p2V_3p3V_25C.lib}
read_verilog {@RESULTS@/final-sta-allnets-typ-20260923-r1/g1_trip_declaration.v}
read_verilog {@RESULTS@/final-sta-allnets-typ-20260923-r1/g1_osc_declaration.v}
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
read_spef -keep_capacitive_coupling -corner CURRENT {@RESULTS@/final-routed-rcx-20260923-r1/final_signal.nom.spef}
read_spef -keep_capacitive_coupling -name CURRENT -path i_core.u_digital {@REPO@/designs/g1-guardian/blocks/g1_ctrl/layout/g1_digital.nom.spef}
set fp [open {@RESULTS@/final-sta-allnets-typ-20260923-r1/counts.tsv} w]
foreach name {SCLK osc_clk} {
  if {[llength [get_clocks -quiet $name]] != 1} {error "Clock missing or duplicated: $name"}
  puts $fp "$name	[llength [all_registers -clock $name]]"
}
close $fp
report_checks -path_delay min -fields {slew cap input net fanout} -format full_clock_expanded -group_path_count 20 > {@RESULTS@/final-sta-allnets-typ-20260923-r1/hold.rpt}
report_checks -path_delay max -fields {slew cap input net fanout} -format full_clock_expanded -group_path_count 20 > {@RESULTS@/final-sta-allnets-typ-20260923-r1/setup.rpt}
report_check_types -max_slew -max_capacitance -max_fanout -violators > {@RESULTS@/final-sta-allnets-typ-20260923-r1/violators.rpt}
report_parasitic_annotation -report_unannotated > {@RESULTS@/final-sta-allnets-typ-20260923-r1/annotation.rpt}
report_net {i_core.sclk_i} > {@RESULTS@/final-sta-allnets-typ-20260923-r1/sclk_net.rpt}
report_net {i_core.sdo_o} > {@RESULTS@/final-sta-allnets-typ-20260923-r1/sdo_net.rpt}
check_setup -verbose -unconstrained_endpoints -multiple_clock -no_clock -no_input_delay -loops -generated_clocks > {@RESULTS@/final-sta-allnets-typ-20260923-r1/coverage.rpt}
set fp [open {@RESULTS@/final-sta-allnets-typ-20260923-r1/slack.tsv} w]
puts $fp "hold	[worst_slack -min]"
puts $fp "setup	[worst_slack -max]"
close $fp
report_net {d_elt_bare} > {@RESULTS@/final-sta-allnets-typ-20260923-r1/net_00.rpt}
report_net {d_std_bare} > {@RESULTS@/final-sta-allnets-typ-20260923-r1/net_01.rpt}
report_net {en_i} > {@RESULTS@/final-sta-allnets-typ-20260923-r1/net_02.rpt}
report_net {fault_n_o} > {@RESULTS@/final-sta-allnets-typ-20260923-r1/net_03.rpt}
report_net {g_shared_bare} > {@RESULTS@/final-sta-allnets-typ-20260923-r1/net_04.rpt}
report_net {gate_o} > {@RESULTS@/final-sta-allnets-typ-20260923-r1/net_05.rpt}
report_net {hbt_b_bare} > {@RESULTS@/final-sta-allnets-typ-20260923-r1/net_06.rpt}
report_net {hbt_c_bare} > {@RESULTS@/final-sta-allnets-typ-20260923-r1/net_07.rpt}
report_net {hbt_e_bare} > {@RESULTS@/final-sta-allnets-typ-20260923-r1/net_08.rpt}
report_net {i_core.bgr_r4_12} > {@RESULTS@/final-sta-allnets-typ-20260923-r1/net_09.rpt}
report_net {i_core.bgr_r4_33} > {@RESULTS@/final-sta-allnets-typ-20260923-r1/net_10.rpt}
report_net {i_core.clr_d} > {@RESULTS@/final-sta-allnets-typ-20260923-r1/net_11.rpt}
report_net {i_core.cmp_clk} > {@RESULTS@/final-sta-allnets-typ-20260923-r1/net_12.rpt}
report_net {i_core.cmp_hard} > {@RESULTS@/final-sta-allnets-typ-20260923-r1/net_13.rpt}
report_net {i_core.cmp_soft} > {@RESULTS@/final-sta-allnets-typ-20260923-r1/net_14.rpt}
report_net {i_core.dac_hard\[0\]} > {@RESULTS@/final-sta-allnets-typ-20260923-r1/net_15.rpt}
report_net {i_core.dac_hard\[1\]} > {@RESULTS@/final-sta-allnets-typ-20260923-r1/net_16.rpt}
report_net {i_core.dac_hard\[2\]} > {@RESULTS@/final-sta-allnets-typ-20260923-r1/net_17.rpt}
report_net {i_core.dac_hard\[3\]} > {@RESULTS@/final-sta-allnets-typ-20260923-r1/net_18.rpt}
report_net {i_core.dac_hard\[4\]} > {@RESULTS@/final-sta-allnets-typ-20260923-r1/net_19.rpt}
report_net {i_core.dac_hard\[5\]} > {@RESULTS@/final-sta-allnets-typ-20260923-r1/net_20.rpt}
report_net {i_core.dac_hard\[6\]} > {@RESULTS@/final-sta-allnets-typ-20260923-r1/net_21.rpt}
report_net {i_core.dac_hard\[7\]} > {@RESULTS@/final-sta-allnets-typ-20260923-r1/net_22.rpt}
report_net {i_core.dac_soft\[0\]} > {@RESULTS@/final-sta-allnets-typ-20260923-r1/net_23.rpt}
report_net {i_core.dac_soft\[1\]} > {@RESULTS@/final-sta-allnets-typ-20260923-r1/net_24.rpt}
report_net {i_core.dac_soft\[2\]} > {@RESULTS@/final-sta-allnets-typ-20260923-r1/net_25.rpt}
report_net {i_core.dac_soft\[3\]} > {@RESULTS@/final-sta-allnets-typ-20260923-r1/net_26.rpt}
report_net {i_core.dac_soft\[4\]} > {@RESULTS@/final-sta-allnets-typ-20260923-r1/net_27.rpt}
report_net {i_core.dac_soft\[5\]} > {@RESULTS@/final-sta-allnets-typ-20260923-r1/net_28.rpt}
report_net {i_core.dac_soft\[6\]} > {@RESULTS@/final-sta-allnets-typ-20260923-r1/net_29.rpt}
report_net {i_core.dac_soft\[7\]} > {@RESULTS@/final-sta-allnets-typ-20260923-r1/net_30.rpt}
report_net {i_core.fast_en} > {@RESULTS@/final-sta-allnets-typ-20260923-r1/net_31.rpt}
report_net {i_core.iptat} > {@RESULTS@/final-sta-allnets-typ-20260923-r1/net_32.rpt}
report_net {i_core.isense} > {@RESULTS@/final-sta-allnets-typ-20260923-r1/net_33.rpt}
report_net {i_core.osc_clk} > {@RESULTS@/final-sta-allnets-typ-20260923-r1/net_34.rpt}
report_net {i_core.osc_en} > {@RESULTS@/final-sta-allnets-typ-20260923-r1/net_35.rpt}
report_net {i_core.osc_trim\[0\]} > {@RESULTS@/final-sta-allnets-typ-20260923-r1/net_36.rpt}
report_net {i_core.osc_trim\[1\]} > {@RESULTS@/final-sta-allnets-typ-20260923-r1/net_37.rpt}
report_net {i_core.osc_trim\[2\]} > {@RESULTS@/final-sta-allnets-typ-20260923-r1/net_38.rpt}
report_net {i_core.osc_trim\[3\]} > {@RESULTS@/final-sta-allnets-typ-20260923-r1/net_39.rpt}
report_net {i_core.pbias} > {@RESULTS@/final-sta-allnets-typ-20260923-r1/net_40.rpt}
report_net {i_core.pcasc} > {@RESULTS@/final-sta-allnets-typ-20260923-r1/net_41.rpt}
report_net {i_core.sclk_i} > {@RESULTS@/final-sta-allnets-typ-20260923-r1/net_42.rpt}
report_net {i_core.sdi_i} > {@RESULTS@/final-sta-allnets-typ-20260923-r1/net_43.rpt}
report_net {i_core.sdo_o} > {@RESULTS@/final-sta-allnets-typ-20260923-r1/net_44.rpt}
report_net {i_core.sense_n} > {@RESULTS@/final-sta-allnets-typ-20260923-r1/net_45.rpt}
report_net {i_core.sense_p} > {@RESULTS@/final-sta-allnets-typ-20260923-r1/net_46.rpt}
report_net {i_core.t2f_en_12} > {@RESULTS@/final-sta-allnets-typ-20260923-r1/net_47.rpt}
report_net {i_core.t2f_en_33} > {@RESULTS@/final-sta-allnets-typ-20260923-r1/net_48.rpt}
report_net {i_core.t2f_mode_12} > {@RESULTS@/final-sta-allnets-typ-20260923-r1/net_49.rpt}
report_net {i_core.t2f_mode_33} > {@RESULTS@/final-sta-allnets-typ-20260923-r1/net_50.rpt}
report_net {i_core.temp_out_o} > {@RESULTS@/final-sta-allnets-typ-20260923-r1/net_51.rpt}
report_net {i_core.trip_d} > {@RESULTS@/final-sta-allnets-typ-20260923-r1/net_52.rpt}
report_net {i_core.tripped} > {@RESULTS@/final-sta-allnets-typ-20260923-r1/net_53.rpt}
report_net {i_core.vref} > {@RESULTS@/final-sta-allnets-typ-20260923-r1/net_54.rpt}
report_net {i_core.vref_buf} > {@RESULTS@/final-sta-allnets-typ-20260923-r1/net_55.rpt}
report_net {net} > {@RESULTS@/final-sta-allnets-typ-20260923-r1/net_56.rpt}
puts "FINAL_EXPANDED_STA_COMPLETE"

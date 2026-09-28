# OpenSTA 3.1.0: timing of the final GDS (r4, 1414 um). The ECO g1_digital macro (gate netlist +
# its own nominal SPEF) inside the chip's top-level netlist derived from the canonical CDL, with the
# top-level route RC of the r4 top-interconnect view as SPEF, the stock sg13g2_io liberty for the
# pads and liberty stubs (estimated input C, no arcs) for the analog blocks. SDC of record unchanged.
# Environment: CASE = chip | macro ; CORNER = fast | typ | slow ; OUT ; INPUTS (dir with
# g1_chip_top_sta.v and g1_analog_stubs.lib) ; TOP_SPEF ; MACRO_NL ; MACRO_SPEF ;
# optional CLOCK_NET (default pad14_sclk/p2c); OSC_TRANS "rise fall" (ns, transition assigned at the
# osc_clk root pin clkbuf_0_osc_clk/A, from osc_clk_stage.py); OSC_LAT "rise fall" (ns, osc_clk source
# latency: oscillator output inverters + top route + macro port wire); BOARD_LOAD_PF (external load on
# the output pad ports instead of the SDC's OUTPUT_CAP_LOAD).
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
puts "macro_nl $::env(MACRO_NL)\nmacro_spef $::env(MACRO_SPEF)"
if { $case eq "macro" } {
    read_verilog $::env(MACRO_NL)
    link_design g1_digital
    read_sdc $R/blocks/g1_ctrl/flow/g1_digital.sdc
    read_spef -corner CURRENT $::env(MACRO_SPEF)
    set clks {osc_clk sclk}
} else {
    read_liberty -corner CURRENT $pdk/libs.ref/sg13g2_io/lib/sg13g2_io_$io($corner).lib
    read_liberty -corner CURRENT $::env(INPUTS)/g1_analog_stubs.lib
    read_verilog $::env(MACRO_NL)
    read_verilog $::env(INPUTS)/g1_chip_top_sta.v
    link_design g1_chip_top
    set ::env(DESIGN_NAME) g1_chip_top
    set ::env(CLOCK_PORT) SCLK
    set ::env(CLOCK_NET) [expr {[info exists ::env(CLOCK_NET)] && $::env(CLOCK_NET) ne "" ? $::env(CLOCK_NET) : "pad14_sclk/p2c"}]
    set ::env(CLOCK_PERIOD) 100
    set ::env(IO_DELAY_CONSTRAINT) 20
    set ::env(MAX_FANOUT_CONSTRAINT) 10
    set ::env(OUTPUT_CAP_LOAD) 6.0
    set ::env(CLOCK_UNCERTAINTY_CONSTRAINT) 0.25
    set ::env(CLOCK_TRANSITION_CONSTRAINT) 0.15
    set ::env(TIME_DERATING_CONSTRAINT) 5
    read_sdc $R/blocks/g1_padring/flow/g1_chip_top.sdc
    if { [info exists ::env(OSC_TRANS)] && $::env(OSC_TRANS) ne "" } {
        lassign [split $::env(OSC_TRANS) ,] tr tf
        set_assigned_transition -rise $tr [get_pins i_core.u_digital/clkbuf_0_osc_clk/A]
        set_assigned_transition -fall $tf [get_pins i_core.u_digital/clkbuf_0_osc_clk/A]
        puts "osc_clk root transition assigned rise $tr fall $tf"
    }
    if { [info exists ::env(OSC_LAT)] && $::env(OSC_LAT) ne "" } {
        lassign [split $::env(OSC_LAT) ,] lr lf
        set_clock_latency -source -rise $lr [get_clocks osc_clk]
        set_clock_latency -source -fall $lf [get_clocks osc_clk]
        puts "osc_clk source latency rise $lr fall $lf"
    }
    if { [info exists ::env(BOARD_LOAD_PF)] && $::env(BOARD_LOAD_PF) ne "" } {
        set_load $::env(BOARD_LOAD_PF) [get_ports {GATE FAULT_N SDO TEMP_OUT}]
        puts "board load $::env(BOARD_LOAD_PF) pF on the output pad ports"
    }
    read_spef -corner CURRENT $::env(TOP_SPEF)
    read_spef -keep_capacitive_coupling -name CURRENT -path i_core.u_digital $::env(MACRO_SPEF)
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
report_checks -path_delay max -group_path_count 1 -format full_clock_expanded -fields {slew cap fanout net} > $out/setup_worst.rpt
report_checks -path_delay min -group_path_count 1 -format full_clock_expanded -fields {slew cap fanout net} > $out/hold_worst.rpt
report_checks -path_delay min_max -group_path_count 1 -format end > $out/groups_end.rpt
report_checks -path_delay min -slack_max 0 -group_path_count 100000 -endpoint_path_count 1 -format end > $out/hold_violators.rpt
report_checks -path_delay max -slack_max 0 -group_path_count 100000 -endpoint_path_count 1 -format end > $out/setup_violators.rpt
report_check_types -max_slew -max_capacitance -max_fanout -violators > $out/drv_violators.rpt
report_parasitic_annotation -report_unannotated > $out/annotation.rpt
check_setup -verbose -unconstrained_endpoints -multiple_clock -no_clock -no_input_delay -loops -generated_clocks > $out/coverage.rpt
report_clock_latency -include_internal_latency > $out/clock_latency.rpt
report_clock_skew -setup -include_internal_latency > $out/clock_skew.rpt
if { $case ne "macro" } {
    # boundary pins: every pin on a top-level net (pads, macro pins, stubs)
    set fp [open $out/boundary_pins.tsv w]
    puts $fp "net\tpin\tdirection\tslew_max_rise_ns\tslew_max_fall_ns\tnet_pin_cap_pf\tnet_wire_cap_pf"
    foreach n [get_nets *] {
        set net [get_full_name $n]
        set wc ""; set pc ""
        catch { set wc [sta::format_capacitance [$n wire_capacitance CURRENT max] 5] }
        catch { set pc [sta::format_capacitance [$n pin_capacitance CURRENT max] 5] }
        foreach p [get_pins -quiet -of_objects $n] {
            set sr ""; set sf ""
            catch { set sr [get_property $p slew_max_rise] }
            catch { set sf [get_property $p slew_max_fall] }
            puts $fp "$net\t[get_full_name $p]\t[get_property $p direction]\t$sr\t$sf\t$pc\t$wc"
        }
    }
    close $fp
    foreach p {pad14_sclk/p2c pad15_sdi/p2c pad12_en/p2c pad16_sdo/c2p pad16_sdo/pad pad11_fault_n/c2p pad10_gate/c2p pad17_temp_out/c2p
               i_core.u_digital/sclk i_core.u_digital/sdi i_core.u_digital/en i_core.u_digital/sdo i_core.u_digital/osc_clk
               i_core.u_digital/clkbuf_0_osc_clk/A i_core.u_digital/cmp_clk i_core.u_trip/clk} {
        sta::redirect_file_append_begin $out/slews_key_pins.rpt
        report_slews [get_pins $p]
        sta::redirect_file_end
    }
    foreach n [get_nets *] {
        report_net [get_full_name $n] >> $out/nets_all.rpt
    }
    report_checks -path_delay max -through [get_pins i_core.u_digital/sdo] -format full_clock_expanded -fields {slew cap fanout net} > $out/sdo_path_max.rpt
    report_checks -path_delay min -through [get_pins i_core.u_digital/sdi] -format full_clock_expanded -fields {slew cap fanout net} > $out/sdi_path_min.rpt
    report_checks -path_delay max -through [get_pins i_core.u_digital/sdi] -format full_clock_expanded -fields {slew cap fanout net} > $out/sdi_path_max.rpt
}
if { $case ne "macro" && [info exists ::env(PIN_SLEWS)] && $::env(PIN_SLEWS) ne "" } {
    # slew at every leaf pin (driver and loads) of every top-level net, limits from the liberty
    set fp [open $out/top_net_pins.tsv w]
    puts $fp "net\tpin\tdirection\tcell\tslew_rise_ns\tslew_fall_ns\tlib_max_transition_ns\tnet_total_cap_pf"
    foreach n [get_nets *] {
        set name [get_full_name $n]
        sta::redirect_string_begin; report_net -digits 5 $name; set txt [sta::redirect_string_end]
        set tc0 ""; set tc1 ""; regexp {Total capacitance: ([-\d.e]+)(?:-([-\d.e]+))?} $txt -> tc0 tc1
        set tc [expr {$tc1 ne "" ? $tc1 : $tc0}]
        foreach {- pn dir cell} [regexp -all -inline -line {^ (\S+) (input|output|bidirect) \((\S+)\)} $txt] {
            sta::redirect_string_begin; report_slews -digits 4 [get_pins $pn]; set sl [sta::redirect_string_end]
            set sr ""; set sf ""; regexp {\^ [\d.]+:([\d.]+) v [\d.]+:([\d.]+)} $sl -> sr sf
            set mt ""; catch { set mt [get_property [get_lib_pins [get_property [get_pins $pn] lib_pin_name] ] max_transition] }
            puts $fp "$name\t$pn\t$dir\t$cell\t$sr\t$sf\t$mt\t$tc"
        }
    }
    close $fp
}
puts "STA_FINAL_COMPLETE $case $corner"

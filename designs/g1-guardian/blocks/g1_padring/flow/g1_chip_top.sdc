# SPDX-FileCopyrightText: 2025 LibreLane Contributors, 2026 Simon Dorrer and Harald Pretl
# SPDX-License-Identifier: Apache-2.0 WITH SHL-2.1
# Adapted for G1 from iic-jku/ihp-sg13g2-ams-chip-template flow/librelane/chip_top.sdc:
# clock defined at the SCLK pad's core-side pin, IO delays on the digital pads;
# the digital macro's chip-level constraints are sourced at the end.

current_design $::env(DESIGN_NAME)
set_units -time ns

set clock_port __VIRTUAL_CLK__
if { [info exists ::env(CLOCK_PORT)] } {
    set port_count [llength $::env(CLOCK_PORT)]
    if { $port_count == "0" } {
        puts "\[WARNING] No CLOCK_PORT found. A dummy clock will be used."
    } elseif { $port_count != "1" } {
        puts "\[WARNING] Multi-clock files are not currently supported by the base SDC file. Only the first clock will be constrained."
    }
    if { $port_count > "0" } {
        set ::clock_port [lindex $::env(CLOCK_PORT) 0]
    }
}

if { $::env(CLOCK_PORT) == $::env(CLOCK_NET) } {
    set port_args [get_ports $clock_port]
} else {
    set port_args [get_pins [lindex $::env(CLOCK_NET) 0]]
}

puts "\[INFO] Using clock $clock_port…"
create_clock {*}$port_args -name $clock_port -period $::env(CLOCK_PERIOD)

set input_delay_value [expr $::env(CLOCK_PERIOD) * $::env(IO_DELAY_CONSTRAINT) / 100]
set output_delay_value [expr $::env(CLOCK_PERIOD) * $::env(IO_DELAY_CONSTRAINT) / 100]
puts "\[INFO] Setting output delay to: $output_delay_value"
puts "\[INFO] Setting input delay to: $input_delay_value"

set_max_fanout $::env(MAX_FANOUT_CONSTRAINT) [current_design]
if { [info exists ::env(MAX_TRANSITION_CONSTRAINT)] } {
    set_max_transition $::env(MAX_TRANSITION_CONSTRAINT) [current_design]
}
if { [info exists ::env(MAX_CAPACITANCE_CONSTRAINT)] } {
    set_max_capacitance $::env(MAX_CAPACITANCE_CONSTRAINT) [current_design]
}

set clocks [get_clocks $clock_port]

# Digital input pads (the clock pad SCLK is excluded)
set core_input_ports [get_ports { EN SDI }]
set_input_delay -min 0 -clock $clocks $core_input_ports
set_input_delay -max $input_delay_value -clock $clocks $core_input_ports

# Digital output pads
set core_output_ports [get_ports { GATE FAULT_N SDO TEMP_OUT }]
set_output_delay $output_delay_value -clock $clocks $core_output_ports

set cap_load [expr $::env(OUTPUT_CAP_LOAD) / 1000.0]
puts "\[INFO] Setting load to: $cap_load"
set_load $cap_load $core_output_ports

puts "\[INFO] Setting clock uncertainty to: $::env(CLOCK_UNCERTAINTY_CONSTRAINT)"
set_clock_uncertainty $::env(CLOCK_UNCERTAINTY_CONSTRAINT) $clocks

puts "\[INFO] Setting clock transition to: $::env(CLOCK_TRANSITION_CONSTRAINT)"
set_clock_transition $::env(CLOCK_TRANSITION_CONSTRAINT) $clocks

puts "\[INFO] Setting timing derate to: $::env(TIME_DERATING_CONSTRAINT)%"
set_timing_derate -early [expr 1-[expr $::env(TIME_DERATING_CONSTRAINT) / 100]]
set_timing_derate -late [expr 1+[expr $::env(TIME_DERATING_CONSTRAINT) / 100]]

if { [info exists ::env(OPENLANE_SDC_IDEAL_CLOCKS)] && $::env(OPENLANE_SDC_IDEAL_CLOCKS) } {
    unset_propagated_clock [all_clocks]
} else {
    set_propagated_clock [all_clocks]
}

# ---------------------------------------------------------------------------
# Digital macro g1_digital (run7) at chip level. Merged inline from
# ../../g1_ctrl/layout/g1_digital_top.sdc (rationale: ../../g1_ctrl/layout/TOP_SDC.md;
# evidence: ../../g1_ctrl/reports/sta_merged_sdc_20260924/README.md) so that this
# file is complete on its own. Keep the two in step if either changes.
# Applied only when the macro instance exists (ring-only builds have none).
# ---------------------------------------------------------------------------
set g1d i_core.u_digital
if { [llength [get_cells -quiet $g1d]] > 0 } {
    puts "\[INFO] Applying g1_digital chip-level constraints to $g1d"

    # (1) Oscillator clock: ~10 MHz nominal, +-20 % untrimmed, constrained at
    #     100 ns like the macro signoff. Defined on the macro's root clock-buffer
    #     input: g1_osc is a black box without timing model, so a clock created
    #     on its output or on the macro's hierarchical osc_clk pin reaches no
    #     register (0 vs 1148 registers, TOP_SDC.md). 0.3 ns transition and
    #     propagated latency as in the macro SDC.
    if { [llength [get_clocks -quiet osc_clk]] == 0 } {
        create_clock -name osc_clk -period 100.0 [get_pins $g1d/clkbuf_0_osc_clk/A]
    }
    set_clock_transition 0.3 [get_clocks osc_clk]
    set_propagated_clock [get_clocks osc_clk]

    # (2) osc_clk and SCLK are asynchronous; every crossing goes through a
    #     synchroniser inside the macro (register map section 1.3).
    set_clock_groups -asynchronous -name g1_digital_async \
        -group [get_clocks osc_clk] -group $clocks

    # (3) Macro signoff uncertainties: 0.5 ns setup (oscillator jitter),
    #     0.05 ns hold. Overrides the 0.25 ns set above for both checks, which on
    #     hold is 0.2 ns more than the macro was hardened with (-0.094 ns fast).
    foreach c [list [get_clocks osc_clk] $clocks] {
        set_clock_uncertainty -setup 0.5  $c
        set_clock_uncertainty -hold  0.05 $c
    }

    # (4) Asynchronous macro inputs, synchronised inside; no timing requirement.
    #     EN is also the chip reset: its pad input delay must not create
    #     SCLK-relative checks into the osc_clk domain.
    set_false_path -from [get_ports EN]
    foreach p {cmp_soft cmp_hard tripped en por_n} {
        set_false_path -through [get_pins $g1d/$p]
    }

    # (5) SDI is driven by the host on the falling SCLK edge, >= 2 ns after it:
    #     minimum input delay 2 ns (the template above uses 0).
    set_input_delay -min 2.0 -clock $clocks [get_ports SDI]

    # (6) Other macro outputs (DAC codes, strobe, latch controls, oscillator
    #     enable/trim, level-shifter inputs) end at analog macros without timing
    #     models and are quasi-static; they are timed only inside the macro
    #     signoff (20 ns output delay against osc_clk). Nothing to add here.
} else {
    puts "\[WARNING] $g1d not found: g1_digital constraints not applied (ring-only build?)"
}

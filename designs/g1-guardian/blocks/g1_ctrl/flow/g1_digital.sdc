# G1 digital macro timing constraints.
# Two asynchronous clocks: osc_clk (internal ring oscillator, ~10 MHz nominal,
# constrained at 100 ns) and sclk (serial clock, <= f_OSC, constrained at 100 ns).
# All crossings go through the synchronisers in g1_serial (register map, 1.3).
# Adapted from ChipDesign-BV/spi-slave-ihp flow/constraint.sdc (Apache-2.0).
current_design g1_digital
set_units -time ns

create_clock -name osc_clk -period 100.0 [get_ports osc_clk]
create_clock -name sclk    -period 100.0 [get_ports sclk]
set_clock_groups -asynchronous -group {osc_clk} -group {sclk}

# uncertainty: 0.5 ns for setup (ring-oscillator jitter), 0.05 ns for hold;
# a single 0.5 ns value applied to hold made every reg-to-reg path fail
set_clock_uncertainty -setup 0.5  [all_clocks]
set_clock_uncertainty -hold  0.05 [all_clocks]
set_clock_transition  0.3 [all_clocks]

# Serial data: sampled on the rising edge of sclk, driven on the falling edge
# the host drives SDI on its falling SCLK edge: at least 2 ns after the edge
set_input_delay  -clock sclk -max 20.0 [get_ports sdi]
set_input_delay  -clock sclk -min  2.0 [get_ports sdi]
set_output_delay -clock sclk -max 20.0 [get_ports sdo]
set_output_delay -clock sclk -min  0.0 [get_ports sdo]

# Asynchronous inputs (synchronised inside): no timing requirement
set_false_path -from [get_ports {cmp_soft cmp_hard tripped en por_n}]

# Quasi-static outputs to the analog blocks and pads (cmp_clk = osc_clk/2 is a
# flop output; the comparators only need its edges, not a phase relation)
set osc_outputs [get_ports {dac_soft[*] dac_hard[*] trip_set_sel trip gate_en fault_n trip_cause[*] clk_div_out \
                            cmp_clk trip_d clr_d fast_en osc_en osc_trim[*] t2f_en t2f_mode bgr_r4}]
set_output_delay -clock osc_clk -max 20.0 $osc_outputs
set_output_delay -clock osc_clk -min  0.0 $osc_outputs

set_load 0.05 [all_outputs]
set_max_fanout 16 [current_design]
set_max_transition 1.5 [current_design]
set_propagated_clock [all_clocks]

# Place-and-route copy of r1_ctrl.sdc (revision 0.6, run t11): the repair limit is 7 so that the antenna diode added after
# the fanout repair cannot push a net to 9 loads. Sign-off uses r1_ctrl.sdc (limit 8). Only this line differs.
# r1_ctrl macro timing constraints (revision 0.5; port names of the D18 ADC interface, tap_p / tap_n,
# pga_c, t2f_en, t2f_mode, bias_en). flow/check_sdc_ports.py lists the ports of the RTL and checks that every
# port bit is constrained and that no pattern below is stale. Applies to LibreLane PnR and
# signoff STA. Structure follows the G1 g1_digital.sdc (same repository).
#   clk     : r1_osc, STA closes at 42 MHz (23.81 ns), the fastest untrimmed
#             clock at OSC_TRIM reset code 22 is 38.9 MHz (PLAN.md D13).
#   ma_sclk : MA (BiSS, <= 10 MHz) and SCLK (SPI) on one pad; constrained at
#             10 MHz. Both edges are used (BiSS: rising drives SLO, falling
#             samples the ready toggle; SPI: rising samples SDI, falling drives SDO).
# clk and ma_sclk are asynchronous; all crossings go through the synchronisers
# and handshakes described in r1_biss.v, r1_spi.v and r1_ctrl_top.v.
# The register-file and PWM-shadow latch words are clocked by gated copies of
# clk (r1_cgate); STA propagates clk through the gates and checks them.
current_design r1_ctrl_top
set_units -time ns

create_clock -name clk -period 23.81 [get_ports clk]
create_clock -name ma  -period 100.0 [get_ports ma_sclk]
set_clock_groups -asynchronous -group {clk} -group {ma}

# r1_osc period jitter is about 15 ps (r1_osc README); 0.5 ns setup margin as in G1
set_clock_uncertainty -setup 0.5  [all_clocks]
set_clock_uncertainty -hold  0.05 [all_clocks]
set_clock_transition  0.3 [all_clocks]

# ADC: SAR logic and decisions are synchronous to clk (r1_adc); 30 % of the period
# Revision 0.4: the 0.2 port names (adc_valid, adc_raw, adc_mux) no longer exist since D18, so up to
# the 0.3 hardening (t6) these constraints matched nothing and the ADC ports were unconstrained.
set_input_delay  -clock clk -max 7.0 [get_ports {adc_valid_a adc_valid_b adc_raw_a[*] adc_raw_b[*]}]
set_input_delay  -clock clk -min 0.5 [get_ports {adc_valid_a adc_valid_b adc_raw_a[*] adc_raw_b[*]}]
# SPI data in, sampled on the rising SCLK edge
set_input_delay  -clock ma -max 20.0 [get_ports sdi]
set_input_delay  -clock ma -min  2.0 [get_ports sdi]
# SLO/SDO is driven on MA/SCLK edges (and muxed by CS_N)
set_output_delay -clock ma -max 20.0 [get_ports slo_sdo]
set_output_delay -clock ma -min  0.0 [get_ports slo_sdo]

# Asynchronous inputs (synchronised inside, or asynchronous by design: EN gates
# the outputs combinationally, CS_N is an asynchronous set/reset of SPI/BiSS state)
set_false_path -from [get_ports {por_n cs_n en_pad cmp[*] t2f_clk}]

# Outputs to the analog blocks and pads, registered in clk (gates: AND with EN)
set clk_outputs [get_ports {gate_a gate_b gate_c fault_n adc_hold is_smp adc_start adc_sel \
                            az_win tap_p[*] tap_n[*] osc_trim[*] pga_c[*] t2f_en t2f_mode bias_en}]
set_output_delay -clock clk -max 5.0 $clk_outputs
set_output_delay -clock clk -min 0.0 $clk_outputs

set_load 0.05 [all_outputs]
# revision 0.6: 8 = liberty default_max_fanout (0.3 to 0.5 carried 16, which the library limit overrides)
set_max_fanout 7 [current_design]
set_max_transition 1.5 [current_design]
set_propagated_clock [all_clocks]

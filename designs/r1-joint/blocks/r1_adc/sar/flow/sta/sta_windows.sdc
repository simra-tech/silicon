# r1_adc_sar window analysis constraints (T2j; used only by sta_windows.tcl, not by PnR or sign-off).
# Every launch source has its own clock tag so that report_arrival separates the paths:
#   clk  : the oscillator clock (sequencer and flag flops)
#   mclk : the comparator one-shot (waveform arbitrary; edge times are subtracted in sta_windows.py)
#   vctl : virtual clock of the r1_ctrl requests (input delay 0: the arrival is the path delay)
#   vcmp : virtual clock of the comparator decisions
current_design r1_adc_sar
set_units -time ns
create_clock -name clk  -period 23.81 [get_ports clk]
create_clock -name mclk -period 23.81 -waveform {1.0 12.0} [get_ports mclk]
create_clock -name vctl -period 23.81
create_clock -name vcmp -period 23.81
set_clock_transition 0.3 [get_clocks clk]
set_clock_transition 0.1 [get_clocks mclk]
set_input_delay -clock vctl 0 [get_ports {adc_hold is_smp adc_start adc_sel cur_trk}]
set_input_delay -clock vcmp 0 [get_ports {oap oan oanp oann obp obn obnp obnn}]
set_driving_cell -lib_cell sg13g2_buf_2 -pin X [get_ports {adc_hold is_smp adc_start adc_sel cur_trk}]
set_input_transition 0.3 [get_ports {oap oan oanp oann obp obn obnp obnn}]
set_load 0.05 [get_ports {adc_valid_a adc_valid_b adc_raw_a[*] adc_raw_b[*]}]
set_load 0.04 [get_ports {cpa[*] cna[*] cpb[*] cnb[*] trka0 trka1 trkb0 trkb1}]
set_load 0.10 [get_ports {clka clkab clkna clknab clkb clkbb clknb clknbb}]
set_propagated_clock [get_clocks {clk mclk}]

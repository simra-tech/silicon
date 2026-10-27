# r1_adc_sar timing constraints (T2j, D21). Used by LibreLane PnR and sign-off STA (typ / fast / slow).
# Clocks
#   clk  : the oscillator clock (the same net as r1_ctrl clk); STA closes at 42 MHz (23.81 ns) as r1_ctrl.
#   mclk : the comparator one-shot r1_cmp4_clkgen (inside r1_adc): falls about 0.05 ns after each clk rising edge
#          (comparator reset), rises after the one-shot width (evaluate). Width 0.91 / 1.38 / 2.27 ns at
#          ff / tt / ss (r1_adc README, revision 4). One SDC serves all corners, so the waveform uses the
#          smallest width (0.91 ns): rise 0.91 ns, fall 23.81 + 0.03 ns. Both clocks are synchronous.
# The CDAC-switch and comparator-clock windows per corner are reported by sta_windows.tcl, not by these
# constraints alone (sar/README.md "Timing").
current_design r1_adc_sar
set_units -time ns

create_clock -name clk  -period 23.81 [get_ports clk]
# mclk rise per corner for the sign-off STA of record (flow/sta/run_sta.sh sets SAR_MCLK_RISE = mclk fall delay
# 0.04 ns + one-shot width: fast 0.95, typ 1.42, slow 2.31 ns); LibreLane uses the default 0.91 ns (all corners)
if {[info exists ::env(SAR_MCLK_RISE)]} { set mr $::env(SAR_MCLK_RISE) } else { set mr 0.91 }
create_clock -name mclk -period 23.81 -waveform [list $mr 23.84] [get_ports mclk]

set_clock_uncertainty -setup 0.5  [all_clocks]
set_clock_uncertainty -hold  0.05 [all_clocks]
# mclk is made from each clk edge on the chip (one-shot, no PLL): the clk -> mclk relation has no cycle jitter;
# its spread is the one-shot width per corner (SAR_MCLK_RISE). 0.1 ns between the two clocks.
set_clock_uncertainty -setup 0.1 -from [get_clocks clk] -to [get_clocks mclk]
set_clock_uncertainty -setup 0.1 -from [get_clocks mclk] -to [get_clocks clk]
set_clock_transition  0.3 [get_clocks clk]
set_clock_transition  0.1 [get_clocks mclk]

# r1_ctrl frame protocol (r1_gate flip-flops): the ctrl SDC guarantees arrival <= 23.81 - 5.0 ns and no
# change before the edge (output delay -min 0)
set ctrl_in [get_ports {adc_hold is_smp adc_start adc_sel cur_trk}]
set_input_delay -clock clk -max 18.81 $ctrl_in
set_input_delay -clock clk -min 0.0   $ctrl_in

# comparator decisions: the comparator evaluates from the rise of its clock (mclk rise, then the gate) and its
# decision must reach the latch >= 3.0 ns before the next clk edge: input delay against the mclk rise
# 23.81 - 0.91 - 3.0 = 19.9 ns. (Against clk, STA pairs the clk launch with the latch closing 0.03 ns later and
# reports a false -21 ns.)
# Hold at the latch close: the latch gate is the comparator clock net itself (one driver for the latch GATE and
# the output pin), and the comparator output answers its clock 0.18-0.23 ns later (decks). An input delay
# against the mclk fall cannot express "after the output pin falls", so the hold check is excluded here and
# done in sta_windows.py (timing requirement 2: pin fall + 0.18 ns - gate fall - latch hold > 0).
set cmp_in [get_ports {oap oanp obp obnp}]
set_input_delay -clock mclk -max [expr {23.81 - $mr - 3.0}] $cmp_in
set_false_path -hold -from $cmp_in
# dummy loads and the unused frame type
set_false_path -from [get_ports {oan oann obn obnn adc_sel}]
# power-on reset: asynchronous assert, released through the 2-flop synchroniser
set_false_path -from [get_ports por_n]

# outputs to r1_ctrl: r1_ctrl assumes the ADC outputs change >= 0.5 ns after the clock edge and settle
# <= 7.0 ns after it (r1_ctrl.sdc: input delay -min 0.5 / -max 7.0)
set ctrl_out [get_ports {adc_valid_a adc_valid_b adc_raw_a[*] adc_raw_b[*]}]
set_output_delay -clock clk -max 16.81 $ctrl_out
set_output_delay -clock clk -min -0.5  $ctrl_out
# adc_raw_* are the decision flag flops: they change at the conversion edges E1..E14 and at the clear edge E16.
# r1_ctrl captures them at E15 only (the edge where it sees adc_valid_*), so the next change after the capture is
# one period later: the hold check moves back by one cycle. adc_valid_* keeps the 0.5 ns hold requirement.
set_multicycle_path -hold 1 -to [get_ports {adc_raw_a[*] adc_raw_b[*]}]

# CDAC driver lines: switch within the one-shot reset after the edge (bound for the optimiser: <= 2.0 ns,
# the slow-corner one-shot width 2.27 ns less 0.2 ns;
# the per-corner check against the one-shot width is in sta_windows.tcl)
set cdac_out [get_ports {cpa[*] cna[*] cpb[*] cnb[*]}]
# sign-off: required time = requirement 1 at the slow corner, 2.07 ns (23.81 - 0.5 uncertainty - 21.24); the
# fast and typ limits (0.71 / 1.18 ns) are checked in sta_windows.py
set_output_delay -clock clk -max 21.24 $cdac_out
set_output_delay -clock clk -min 0.0   $cdac_out
# lines 11..0: busy only enables them (it rises before their flags and falls at E14 after the last decision);
# the busy -> line path only has to clear the lines before the track phase (release at E15 or later):
# excluded here, its delay is reported by sta_windows.py (cdac_clear_ns, limit one tick)
set_false_path -through [get_nets busy] -to [get_ports {cpa[0] cpa[1] cpa[2] cpa[3] cpa[4] cpa[5] cpa[6] cpa[7] cpa[8] cpa[9] cpa[10] cpa[11] cna[0] cna[1] cna[2] cna[3] cna[4] cna[5] cna[6] cna[7] cna[8] cna[9] cna[10] cna[11] cpb[0] cpb[1] cpb[2] cpb[3] cpb[4] cpb[5] cpb[6] cpb[7] cpb[8] cpb[9] cpb[10] cpb[11] cnb[0] cnb[1] cnb[2] cnb[3] cnb[4] cnb[5] cnb[6] cnb[7] cnb[8] cnb[9] cnb[10] cnb[11]}]
# track switches: from the sequencer flops they change only at E14 (track starts; the track phase is 8 ticks,
# 267 ns, against >= 250 ns: requirement 7), so the bound is 10 ns. The sample instant follows the ctrl request
# (combinational, excluded below, measured in sta_windows.py).
set trk_out [get_ports {trka0 trka1 trkb0 trkb1}]
set_output_delay -clock clk -max 13.81 $trk_out
set_output_delay -clock clk -min 0.0   $trk_out
# comparator clocks: gated mclk; delay and skew reported by sta_windows.tcl
set cmpclk_out [get_ports {clka clkab clkna clknab clkb clkbb clknb clknbb}]
# No output delay: an output delay against mclk pairs the clk launch at 0 with the mclk rise at 0.91 ns and
# gives a meaningless -22 ns slack. The mclk -> pin delays, the true / complement skew and the clk -> busy ->
# win closing time against the mclk rise are measured in sta_windows.tcl.
# (no limit is given for mclk -> comparator clock pins, README requirement 5; PnR uses a 1.5 ns bound)

# loads: r1_ctrl input over the top-level route (as r1_ctrl.sdc); CDAC driver gates and about 100 um of route;
# comparator clock inputs (r1_cmp4: tail 16 um PMOS + 2 x 20 um reset NMOS) and route
# combinational paths from the ctrl requests: adc_hold / is_smp -> trk (the sample instant follows the ctrl
# edge; its delay and the slice A / B skew are reported by sta_windows.tcl) and adc_start -> win -> comparator
# clocks (the window opens during the frame-start tick, decision 0 is taken at the next edge). Both paths
# are combinational from an input with an 18.81 ns input delay to outputs that have their own budget, so a
# period check is meaningless; they are excluded here and measured in sta_windows.tcl.
set_false_path -from $ctrl_in -to $trk_out
set_false_path -from $ctrl_in -to $cmpclk_out
# the same requests at the comparator clock gates (adc_start opens the window during the frame-start tick;
# adc_hold / is_smp through the 2-cell delay): clock-gating checks against mclk are not meaningful
set_false_path -from $ctrl_in -to [get_clocks mclk]
set_load 0.05 $ctrl_out
set_load 0.04 $cdac_out
set_load 0.04 $trk_out
set_load 0.10 $cmpclk_out
set_driving_cell -lib_cell sg13g2_buf_2 -pin X [get_ports {adc_hold is_smp adc_start adc_sel cur_trk}]
set_input_transition 0.3 [get_ports {oap oan oanp oann obp obn obnp obnn}]
set_max_fanout 8 [current_design]
set_max_transition 1.5 [current_design]
set_propagated_clock [all_clocks]

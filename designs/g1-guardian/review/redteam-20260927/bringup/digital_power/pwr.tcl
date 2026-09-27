# Red-team bring-up 2026-09-27: VDD current estimate of g1_digital (nl 4b83f181, SPEF 0b626c7f), typ lib.
set pdk /foss/pdks/ihp-sg13g2
set N $::env(BULK)/digital-eco-r3cand2-20260926/final
read_liberty $pdk/libs.ref/sg13g2_stdcell/lib/sg13g2_stdcell_typ_1p20V_25C.lib
read_verilog $N/nl/g1_digital.nl.v
link_design g1_digital
create_clock -name osc_clk -period 105.98 [get_ports osc_clk]
set_clock_transition 0.3 [all_clocks]
read_spef $N/spef/nom/g1_digital.nom.spef
foreach a {0.0 0.1 0.5 1.0} {
  set_power_activity -global -activity $a
  set_power_activity -input -activity 0.0
  puts "=== global data activity $a (transitions per osc_clk period), clock 9.436 MHz, sclk idle"
  report_power
}

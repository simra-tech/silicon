# Fanout nets and latch borrow, slow corner of the t7 run (OpenSTA).
set run $::env(RUN)
read_liberty /foss/pdks/ihp-sg13g2/libs.ref/sg13g2_stdcell/lib/sg13g2_stdcell_slow_1p08V_125C.lib
read_verilog $run/final/nl/r1_ctrl_top.nl.v
link_design r1_ctrl_top
read_sdc $run/final/sdc/r1_ctrl_top.sdc
read_spef $run/final/spef/nom/r1_ctrl_top.nom.spef
foreach p {clkbuf_0_clk_regs clkbuf_0_ma_sclk clkbuf_0_u_gate.g_sh fanout1342 fanout436 clkbuf_0_clk} {
  set inst [get_cells $p]
  set ipin [get_pins $p/A]
  set opin [get_pins $p/X]
  set onet [get_nets -of_objects $opin]
  set inet [get_nets -of_objects $ipin]
  puts "NET $p cell=[get_property $inst ref_name] in_net=[get_full_name $inet] out_net=[get_full_name $onet]"
  foreach l [get_pins -of_objects $onet -filter "direction==input"] {
    puts "   load [get_full_name $l] ([get_property [get_cells -of_objects $l] ref_name])"
  }
  puts "   input-net driver(s):"
  foreach d [get_pins -of_objects $inet -filter "direction==output"] { puts "   drv [get_full_name $d]" }
}
puts "=== max latch borrow"
report_checks -path_delay max -to [all_registers -level_sensitive -data_pins] -group_path_count 3000 -unique_paths_to_endpoint -sort_by_slack -digits 4 -format full

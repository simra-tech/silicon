# r1_adc_sar window analysis (T2j). Inside the container, from the sar directory:
#   env SAR_NL=<final nl.v> SAR_SPEF=<spef> SAR_LIB=<liberty> SAR_TAG=<corner> sta -no_splash -exit flow/sta/sta_windows.tcl
# Prints "ARR <pin>" followed by report_arrival for every output and latch gate pin; flow/sta/sta_windows.py
# turns the logs of the three corners into the window table.
read_liberty $::env(SAR_LIB)
read_verilog $::env(SAR_NL)
link_design r1_adc_sar
read_spef $::env(SAR_SPEF)
read_sdc [file dirname [info script]]/sta_windows.sdc
puts "CORNER $::env(SAR_TAG)"
set pins {}
foreach p [get_ports -filter "direction == output"] { lappend pins [get_full_name $p] }
foreach p [get_pins u_lat_*/GATE] { lappend pins [get_full_name $p] }
foreach n $pins {
  puts "ARR $n"
  if {[string first / $n] >= 0} { report_arrival [get_pins $n] } else { report_arrival [get_ports $n] }
}
# CDAC lines 11..0: from the flag flip-flops only (busy only enables them, sar/rtl/r1_adc_sar.v)
set busyc [get_full_name [get_cells -of_objects [get_pins -of_objects [get_nets busy] -filter "direction == output"]]]
set regs {}
foreach c [all_registers -edge_triggered] { if {[get_full_name $c] ne $busyc} { lappend regs $c } }
puts "BUSY_CELL $busyc"
foreach b {cpa cna cpb cnb} {
  for {set k 0} {$k < 12} {incr k} {
    foreach t {max min} {
      puts "CDAC $b\[$k\] $t"
      report_checks -from $regs -to [get_ports "$b\[$k\]"] -unconstrained -path_delay $t -digits 4
    }
  }
}
puts "END"

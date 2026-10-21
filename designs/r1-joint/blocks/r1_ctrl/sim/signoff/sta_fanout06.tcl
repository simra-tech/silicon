# Max-fanout violators of a hardening run with net names and loads (OpenSTA), one corner per call.
# env: RUN (hardening run dir), LIBNAME (liberty stem, for example slow_1p08V_125C)
set run $::env(RUN)
read_liberty /foss/pdks/ihp-sg13g2/libs.ref/sg13g2_stdcell/lib/sg13g2_stdcell_$::env(LIBNAME).lib
read_verilog $run/final/nl/r1_ctrl_top.nl.v
link_design r1_ctrl_top
read_sdc $run/final/sdc/r1_ctrl_top.sdc
read_spef $run/final/spef/nom/r1_ctrl_top.nom.spef
report_check_types -max_fanout -violators -verbose
foreach t [list max_slew max_capacitance] { puts "=== $t violators"; report_check_types -$t -violators }
puts "=== loads of the violating nets"
set tmp [file join $::env(TMPDIR_FO) fo_violators.txt]
report_check_types -max_fanout -violators -verbose > $tmp
set fh [open $tmp]; set txt [read $fh]; close $fh
foreach line [split $txt "\n"] {
  if {[regexp {^Pin (\S+/\S+)} $line -> pn]} {
    set pin [get_pins $pn]; set net [get_nets -of_objects $pin]
    puts "NET [get_full_name $net] driver $pn"
    foreach l [get_pins -of_objects $net -filter "direction==input"] {
      puts "   load [get_full_name $l] ([get_property [get_cells -of_objects $l] ref_name])"
    }
  }
}

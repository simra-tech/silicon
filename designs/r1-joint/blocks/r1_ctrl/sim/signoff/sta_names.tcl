set run $::env(RUN)
read_liberty /foss/pdks/ihp-sg13g2/libs.ref/sg13g2_stdcell/lib/sg13g2_stdcell_slow_1p08V_125C.lib
read_verilog $run/final/nl/r1_ctrl_top.nl.v
link_design r1_ctrl_top
read_sdc $run/final/sdc/r1_ctrl_top.sdc
read_spef $run/final/spef/nom/r1_ctrl_top.nom.spef
foreach c {_26009_ _25968_ _26406_ _26647_ _26649_ _27147_ _26508_ _27233_ _26416_ _25897_ _26636_} {
  foreach pn {Q Q_N D} {
    set p [get_pins -quiet $c/$pn]
    if {$p ne ""} { puts "PIN $c/$pn net [get_full_name [get_nets -of_objects $p]]" }
  }
}


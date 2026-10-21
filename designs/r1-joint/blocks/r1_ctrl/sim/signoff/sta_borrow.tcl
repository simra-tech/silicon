# Time borrowing at all level-sensitive latch D pins (t7 post-layout netlist + SPEF), one corner per call. env: RUN, LIBNAME
set run $::env(RUN)
read_liberty /foss/pdks/ihp-sg13g2/libs.ref/sg13g2_stdcell/lib/sg13g2_stdcell_$::env(LIBNAME).lib
read_verilog $run/final/nl/r1_ctrl_top.nl.v
link_design r1_ctrl_top
read_sdc $run/final/sdc/r1_ctrl_top.sdc
read_spef $run/final/spef/nom/r1_ctrl_top.nom.spef
report_checks -path_delay max -to [all_registers -level_sensitive -data_pins] -group_path_count 3000 -unique_paths_to_endpoint -sort_by_slack -digits 4 -format full

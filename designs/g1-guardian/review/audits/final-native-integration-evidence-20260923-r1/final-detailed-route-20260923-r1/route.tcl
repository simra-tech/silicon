set_thread_count 1
read_liberty {/foss/pdks/ihp-sg13g2/libs.ref/sg13g2_stdcell/lib/sg13g2_stdcell_typ_1p20V_25C.lib}
read_liberty {/work/designs/g1-guardian/blocks/g1_padring/ip/sg13g2_io_padbare/lib/sg13g2_io_typ_1p2V_3p3V_25C.lib}
read_liberty {/work/designs/g1-guardian/blocks/g1_ctrl/layout/lib/g1_digital__nom_typ_1p20V_25C.lib}
read_db {@RESULTS@/final-global-route-20260923-r1/global.odb}
set ::env(DESIGN_NAME) g1_chip_top
set ::env(CLOCK_PORT) SCLK
set ::env(CLOCK_NET) pad14_sclk/p2c
set ::env(CLOCK_PERIOD) 100
set ::env(IO_DELAY_CONSTRAINT) 20
set ::env(MAX_FANOUT_CONSTRAINT) 10
set ::env(OUTPUT_CAP_LOAD) 6.0
set ::env(CLOCK_UNCERTAINTY_CONSTRAINT) 0.25
set ::env(CLOCK_TRANSITION_CONSTRAINT) 0.15
set ::env(TIME_DERATING_CONSTRAINT) 5
read_sdc {/work/designs/g1-guardian/blocks/g1_padring/flow/g1_chip_top.sdc}
read_guides {@RESULTS@/final-global-route-20260923-r1/global.guide}
detailed_route -droute_end_iter 64 -or_seed 42 -verbose 1 -output_drc {@RESULTS@/final-detailed-route-20260923-r1/detailed.drc}
write_db {@RESULTS@/final-detailed-route-20260923-r1/detailed.odb}
write_def {@RESULTS@/final-detailed-route-20260923-r1/detailed.def}
set fp [open {@RESULTS@/final-detailed-route-20260923-r1/after.tsv} w]
set b [ord::get_db_block]
set die [$b getDieArea]
puts $fp "DIE	[$die xMin]	[$die yMin]	[$die xMax]	[$die yMax]"
foreach i [$b getInsts] {
  set m [$i getMaster]; set bb [$i getBBox]
  puts $fp "INST	[$i getName]	[$m getName]	[$i getOrient]	[$bb xMin]	[$bb yMin]	[$bb xMax]	[$bb yMax]"
  foreach t [$m getMTerms] {puts $fp "MTERM	[$m getName]	[$t getName]"}
}
foreach n [$b getNets] {
  puts $fp "NET	[$n getName]"
  foreach t [$n getITerms] {
    puts $fp "CONN	[$n getName]	[[$t getInst] getName]	[[$t getMTerm] getName]"
  }
  foreach t [$n getBTerms] {puts $fp "CONN	[$n getName]	PIN	[$t getName]"}
}
close $fp

set_thread_count 1
read_db {@RESULTS@/final-detailed-route-20260923-r1/detailed.odb}
set fp [open {@RESULTS@/final-routed-rcx-20260923-r1/before.tsv} w]
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
define_process_corner -ext_model_index 0 CURRENT_CORNER
extract_parasitics -ext_model_file {/foss/pdks/ihp-sg13g2/libs.tech/librelane/openrcx/IHP_rcx_patterns.rules} -lef_res
write_spef {@RESULTS@/final-routed-rcx-20260923-r1/final_signal.nom.spef}
write_verilog {@RESULTS@/final-routed-rcx-20260923-r1/final_signal.nl.v}
set fp [open {@RESULTS@/final-routed-rcx-20260923-r1/after.tsv} w]
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
puts "FINAL_ROUTED_RCX_COMPLETE"

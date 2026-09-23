set_thread_count 1
read_db {<results>/bondpad-outward-odb-20260923-r1/unrouted_fullchip.odb}
set fp [open {<results>/bondpad-outward-odb-20260923-r1/roundtrip.tsv} w]
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

set_thread_count 1
read_lef {/foss/pdks/ihp-sg13g2/libs.ref/sg13g2_stdcell/lef/sg13g2_tech.lef}
read_lef {/foss/pdks/ihp-sg13g2/libs.ref/sg13g2_stdcell/lef/sg13g2_stdcell.lef}
read_lef {<repository>/designs/g1-guardian/blocks/g1_padring/ip/sg13g2_io_padbare/lef/sg13g2_io.lef}
read_lef {<repository>/designs/g1-guardian/blocks/g1_padring/ip/bondpad_70x70_tm1/lef/bondpad_70x70_tm1.lef}
read_lef {<results>/bgr-closed-lef-egress-20260922-r3/g1_bgr.lef}
read_lef {<results>/sense-closed-lef-egress-20260922-r2/g1_sense.lef}
read_lef {<repository>/designs/g1-guardian/blocks/g1_ctrl/layout/g1_digital.lef}
read_lef {<repository>/designs/g1-guardian/blocks/g1_trip/layout/g1_trip.lef}
read_lef {<repository>/designs/g1-guardian/blocks/g1_gate/layout/g1_gate.lef}
read_lef {<repository>/designs/g1-guardian/blocks/g1_osc/layout/g1_osc.lef}
read_lef {<repository>/designs/g1-guardian/blocks/g1_t2f/layout/g1_t2f.lef}
read_lef {<repository>/designs/g1-guardian/blocks/g1_dut/layout/g1_dut_macro.lef}
read_lef {<repository>/designs/g1-guardian/blocks/g1_dose/layout/g1_dose_macro.lef}
read_lef {<repository>/designs/g1-guardian/blocks/g1_ctrl/ls/layout/g1_ls_up.lef}
read_def {<results>/bondpad-outward-20260923-r2/placement_projection/g1_chip_top_unrouted.def}
set fp [open {<results>/bondpad-outward-odb-20260923-r1/import.tsv} w]
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
write_db {<results>/bondpad-outward-odb-20260923-r1/unrouted_fullchip.odb}

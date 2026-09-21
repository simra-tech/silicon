read_lef /foss/pdks/ihp-sg13g2/libs.ref/sg13g2_stdcell/lef/sg13g2_tech.lef
read_lef /work/designs/g1-guardian/blocks/g1_dut/layout/g1_dut_macro.lef
foreach lib [[ord::get_db] getLibs] {
  foreach m [$lib getMasters] {
    puts "MASTER [$m getName] [$m getType] [expr [$m getWidth]/1000.0] x [expr [$m getHeight]/1000.0] um"
    foreach t [$m getMTerms] { puts "  PIN [$t getName] [$t getIoType] [$t getSigType]" }
    foreach o [$m getObstructions] { puts "  OBS [[$o getTechLayer] getName] [$o xMin] [$o yMin] [$o xMax] [$o yMax]" }
  }
}
exit

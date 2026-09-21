# LEF load check: OpenROAD (26Q3) reads the PDK tech LEF and layout/g1_t2f.lef and lists the macro. Run from the repo root:
#   flow/run.sh openroad -exit /work/designs/g1-guardian/blocks/g1_t2f/reports/lef/lef_check.tcl > .../reports/lef/lef_check.log
read_lef /foss/pdks/ihp-sg13g2/libs.ref/sg13g2_stdcell/lef/sg13g2_tech.lef
read_lef /work/designs/g1-guardian/blocks/g1_t2f/layout/g1_t2f.lef
set db [ord::get_db]
set lib [lindex [$db getLibs] end]
foreach m [$lib getMasters] {
  puts "MASTER [$m getName] type [$m getType] size [expr [$m getWidth]/1000.0] x [expr [$m getHeight]/1000.0] um"
  foreach t [$m getMTerms] {
    set boxes {}
    foreach p [$t getMPins] { foreach b [$p getGeometry] { lappend boxes "[[$b getTechLayer] getName] ([expr [$b xMin]/1000.0] [expr [$b yMin]/1000.0] [expr [$b xMax]/1000.0] [expr [$b yMax]/1000.0])" } }
    puts "  PIN [$t getName] [$t getSigType] [$t getIoType] $boxes"
  }
  puts "  OBS count [llength [$m getObstructions]]"
}

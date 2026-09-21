# LEF load check: OpenROAD reads the PDK tech LEF and layout/g1_trip.lef and lists the macro. Run from the repo root:
#   flow/run.sh openroad -exit /work/designs/g1-guardian/blocks/g1_trip/reports/lef/lef_check.tcl > .../reports/lef/lef_check.log
read_lef /foss/pdks/ihp-sg13g2/libs.ref/sg13g2_stdcell/lef/sg13g2_tech.lef
read_lef /work/designs/g1-guardian/blocks/g1_trip/layout/g1_trip.lef
set db [ord::get_db]
set lib [lindex [$db getLibs] end]
foreach m [$lib getMasters] {
  puts "MASTER [$m getName] type [$m getType] size [expr [$m getWidth]/1000.0] x [expr [$m getHeight]/1000.0] um"
  foreach t [$m getMTerms] {
    set boxes {}
    foreach p [$t getMPins] { foreach bx [$p getGeometry] { lappend boxes "[[$bx getTechLayer] getName] ([expr [$bx xMin]/1000.0] [expr [$bx yMin]/1000.0] [expr [$bx xMax]/1000.0] [expr [$bx yMax]/1000.0])" } }
    puts "  PIN [$t getName] [$t getSigType] [$t getIoType] $boxes"
  }
  puts "  OBS count [llength [$m getObstructions]]"
  # obstructions per layer, and whether any Metal4/Metal5/TopMetal1 obstruction reaches the
  # VDD/VSS Metal3 bars (north/south 2.5 um of the macro): the chip PDN lands straps there
  set H [$m getHeight]
  foreach o [$m getObstructions] {
    set ln [[$o getTechLayer] getName]
    set over ""
    if {[lsearch {Metal4 Metal5 TopMetal1} $ln] >= 0 && ([$o yMin] < 2500 || [$o yMax] > $H - 2500)} { set over " OVER-BAR" }
    puts "  OBS $ln ([expr [$o xMin]/1000.0] [expr [$o yMin]/1000.0] [expr [$o xMax]/1000.0] [expr [$o yMax]/1000.0])$over"
  }
}

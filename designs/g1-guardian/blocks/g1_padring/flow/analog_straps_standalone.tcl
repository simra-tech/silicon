# Wrapper to run analog_straps.tcl outside a LibreLane step (flow/run_dryrun.sh):
# reads the GeneratePDN ODB in place, applies the straps, writes ODB and DEF back.
set step $::env(STEP_DIR)
read_lef /foss/pdks/ihp-sg13g2/libs.ref/sg13g2_stdcell/lef/sg13g2_tech.lef
read_db $step/g1_chip_top.prestraps.odb
set ::g1_standalone 1
source [file dirname [info script]]/analog_straps.tcl
write_db  $step/g1_chip_top.odb
write_def $step/g1_chip_top.def

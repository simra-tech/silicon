set_thread_count 1
if {[catch {source {/usr/local/lib/python3.12/dist-packages/librelane/scripts/openroad/cts.tcl}} detail options]} {puts [dict get $options -errorinfo]; exit 1}

set root_inst [$::block findInst clkbuf_0_osc_clk]
if {$root_inst == "NULL"} {error "Root missing"}
set root_net [[$root_inst findITerm X] getNet]
set sinks [list]
foreach term [$root_net getITerms] {
    set name [[$term getInst] getName]
    set pin [[$term getMTerm] getName]
    if {$name eq "clkbuf_0_osc_clk" && $pin eq "X"} {continue}
    if {![string match clkbuf_* $name] || $pin ne "A"} {error "Unexpected root sink $name/$pin"}
    lappend sinks $name
}
set sinks [lsort $sinks]
if {[llength $sinks] != 16} {error "Expected exactly 16 original root sinks"}
set master [$::db findMaster sg13g2_buf_16]
if {$master == "NULL"} {error "Missing source buffer master"}
lassign [$root_inst getLocation] x y
for {set group 0} {$group < 2} {incr group} {
    set name clkbuf_fanout_split${group}_osc_clk
    if {[$::block findInst $name] != "NULL" || [$::block findNet $name] != "NULL"} {error "Nonfresh split names"}
    set inserted [odb::dbInst_create $::block $master $name]
    set net [odb::dbNet_create $::block $name]
    $net setSigType CLOCK
    $inserted setLocation $x $y
    $inserted setPlacementStatus PLACED
    [$inserted findITerm A] connect $root_net
    [$inserted findITerm X] connect $net
    foreach sink [lrange $sinks [expr {$group*8}] [expr {$group*8+7}]] {
        set term [[$::block findInst $sink] findITerm A]
        $term disconnect
        $term connect $net
        puts "CTS_SPLIT $name $sink/A"
    }
}
source $::env(SCRIPTS_DIR)/openroad/common/dpl.tcl
estimate_parasitics -placement
write_views

report_check_types -max_slew -max_capacitance -max_fanout -violators > {${RESULTS_ROOT}/digital-cts-split-20260923-r1/macro_violators.rpt}
set_max_fanout 8 [current_design]
report_check_types -max_fanout -violators > {${RESULTS_ROOT}/digital-cts-split-20260923-r1/integrated_fanout.rpt}
set fp [open {${RESULTS_ROOT}/digital-cts-split-20260923-r1/counts.tsv} w]
foreach name {sclk osc_clk} {puts $fp "$name\t[llength [all_registers -clock $name]]"}
close $fp
puts CTS_FANOUT_EXPERIMENT_COMPLETE

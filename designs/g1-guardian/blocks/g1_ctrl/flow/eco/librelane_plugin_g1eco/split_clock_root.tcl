# G1.SplitClockRoot: see __init__.py. Environment as OpenROAD.CTS.
source $::env(SCRIPTS_DIR)/openroad/common/io.tcl
source $::env(SCRIPTS_DIR)/openroad/common/resizer.tcl
read_current_odb
source $::env(SCRIPTS_DIR)/openroad/common/set_rc.tcl
set limit 8
set master [$::db findMaster sg13g2_buf_16]
if {$master == "NULL"} {error "sg13g2_buf_16 missing"}
set inserted 0
foreach root_inst [$::block getInsts] {
    set rname [$root_inst getName]
    if {![regexp {^clkbuf_0_(.+)$} $rname -> clk]} {continue}
    set root_net [[$root_inst findITerm X] getNet]
    set sinks [list]
    foreach term [$root_net getITerms] {
        set name [[$term getInst] getName]
        if {$name eq $rname} {continue}
        if {![string match clkbuf_* $name] || [[$term getMTerm] getName] ne "A"} {
            error "unexpected sink $name on $rname"
        }
        lappend sinks $name
    }
    set n [llength $sinks]
    puts "G1_SPLIT root $rname fanout $n"
    if {$n <= $limit} {continue}
    set sinks [lsort $sinks]
    lassign [$root_inst getLocation] x y
    set groups [expr {($n + $limit - 1) / $limit}]
    for {set g 0} {$g < $groups} {incr g} {
        set net_name clkbuf_fanout_split${g}_$clk
        set inst_name ${net_name}_cell
        if {[$::block findInst $inst_name] != "NULL" || [$::block findNet $net_name] != "NULL"} {error "name clash $inst_name"}
        set buf [odb::dbInst_create $::block $master $inst_name]
        set net [odb::dbNet_create $::block $net_name]
        $net setSigType CLOCK
        $buf setLocation $x $y
        $buf setPlacementStatus PLACED
        [$buf findITerm A] connect $root_net
        [$buf findITerm X] connect $net
        foreach s [lrange $sinks [expr {$g * $limit}] [expr {$g * $limit + $limit - 1}]] {
            set t [[$::block findInst $s] findITerm A]
            $t disconnect
            $t connect $net
        }
        incr inserted
        puts "G1_SPLIT inserted $inst_name"
    }
}
puts "G1_SPLIT buffers inserted: $inserted"
source $::env(SCRIPTS_DIR)/openroad/common/dpl.tcl
estimate_parasitics -placement
write_views

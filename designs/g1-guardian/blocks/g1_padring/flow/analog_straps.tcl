# SPDX-License-Identifier: Apache-2.0
# G1 integration: VDDA supply grid and feed, and the connection of the analog
# macros' supply pins to the chip PDN. Runs between OpenROAD.GeneratePDN and
# the next step (flow/run_dryrun.sh; analog_straps_standalone.tcl sources this
# file with ::g1_standalone set and does the ODB/DEF I/O itself).
#
# 1. VDDA grid (VDDA is not a pdngen net: a secondary VDD_NETS entry breaks the
#    VDD/VSS pad connections, INTEGRATION.md): vertical TopMetal1 and horizontal
#    TopMetal2 stripes between the VDD/VSS pairs, cut around the macros'
#    TopMetal obstructions, via6_7 at the crossings.
# 2. VDDA feed from pad07_vdda (D14): the pad's core-side 'padbare' terminal is a
#    Metal3 strip 24.8 x 0.29 um at the IO row's inner edge (the bare conductor
#    itself is the pad's Metal2 plate under it). Metal3/Metal4/Metal5 patches
#    4.4 um wide over the strip's height, Via3/Via4 arrays between them, and a
#    Metal4+Metal5 strap from the patch to the first vertical VDDA TopMetal1
#    stripe with a TopVia1 array there. The strap's y range is chosen inside
#    the terminal's height where no other net has Metal4/Metal5 special wires
#    (pdngen's VDD stripe-to-rail via stacks at x = 982.7 cross the corridor).
#    Nothing is drawn on TopMetal1/TopMetal2 near the pad: the pad's own vss
#    (TopMetal1, Metal5, Metal4) and vdd (Metal3) rails start 2 um inside the
#    cell, the first VSS TopMetal2 stripe runs under the terminal at y 386.5
#    and pdngen's ring-to-pad connection sits at y 395..408. (The first
#    version, an 8 um TopMetal2 strap with patches 1 um inside the pad,
#    shorted VDDA to VSS and VDD on exactly those shapes; found by the
#    core-only KLayout LVS, reports/assembly-1350-r1/.)
# 3. Macro supply pins (Metal3 bars, Metal3 stubs, Metal1 rails): for a bar
#    crossed by a same-net TopMetal1 stripe, a via stack TopMetal1 -> Metal5 ->
#    Metal4 -> Metal3 (pdngen's own via definitions via5_6/via4_5/via3_4
#    *_2200_440_*) with 2.2 um Metal4/Metal5 patches over the bar height. A pin
#    without a crossing stripe gets a horizontal jog on its own layer (Metal3)
#    or on Metal2 (Metal1 rails: via1_2 at the rail) to a same-net stripe and a
#    via stack there. Every stack and jog is checked against the block
#    instances' obstructions and pins on the layers it uses (the pin's own
#    rectangle excepted); a blocked candidate stripe is skipped and logged.
#    Exemption: g1_ls_up's LEF obstructs Metal1/Metal2 over the whole cell,
#    its GDS has no Metal2 above y = 8.2 um or below y = 1.35 um (checked,
#    INTEGRATION.md), so Metal2 jogs through the shifter row are allowed.
#    (Version 1 jogged the shifters' vdd to the stripe at x = 529.1, which
#    runs over g1_osc, and stacked through the oscillator's internal metal.)
# 4. check_power_grid on every PDN net.
#
# Why not pdngen for the macros: its macro grids over pg pins never produced the
# Metal3 vias and broke the connectivity check of the whole net (INTEGRATION.md).

if { ![info exists ::g1_standalone] } {
    source $::env(SCRIPTS_DIR)/openroad/common/io.tcl
    read_current_odb
}
set block [ord::get_db_block]
set tech  [ord::get_db_tech]
set dbu   [$tech getDbUnitsPerMicron]

set insts [list i_core.u_bgr i_core.u_sense i_core.u_t2f i_core.u_trip i_core.u_gate i_core.u_osc i_core.u_ls_r4 i_core.u_ls_mode i_core.u_ls_en i_core.u_dose i_core.u_dut]
set vdda_pad_inst pad07_vdda
# Helper TopMetal1 stripe segments {net x y1 y2} (um), each tied to the net's
# horizontal TopMetal2 stripe it crosses with a via6_7. pdngen removed its VDD
# TopMetal1 stripe at x = 604.72 above y = 847 (g1_t2f's TopMetal1 plate), so
# the shifter row (y 860..872) and the g1_t2f vdd12 pin (y 977.6) have no VDD
# stripe that can be reached without crossing g1_osc or g1_bgr:
#  * x 604.72, y 831.5..872.5: channel between the shifters (x <= 595.2) and
#    g1_bgr (x >= 645), tied to the VDD TopMetal2 stripe at y 833.86;
#  * x 630.0, y 907..988: over g1_t2f east of its TopMetal1 plate (obstruction
#    ends at x 610.5), crossing the vdd12 pin (x 592.6..638), tied at y 909.46.
set helper_stripes [list [list VDD 604.72 831.5 872.5] [list VDD 630.0 907.0 988.0]]
# masters whose Metal1/Metal2 LEF obstructions are blankets over a cell that has
# no Metal2 where the supply jogs run (GDS checked, see the header)
set m12_exempt_masters [list g1_ls_up]

proc find_via {block name_prefix} {
    foreach v [$block getVias] {
        if { [string match "${name_prefix}*" [$v getName]] } { return $v }
    }
    return "NULL"
}
set via12 [find_via $block via1_2_2200_440]
set via23 [find_via $block via2_3_2200_440]
set via34 [find_via $block via3_4_2200_440]
set via45 [find_via $block via4_5_2200_440]
set via56 [find_via $block via5_6_2200_440]
set via67 [find_via $block via6_7_2200_2200]
foreach v [list $via12 $via23 $via34 $via45 $via56 $via67] {
    if { $v == "NULL" } { puts "\[ERROR\] analog_straps: pdngen via (2200 x 440 / 2200 x 2200) not found in the block"; exit 1 }
}
set m1 [$tech findLayer Metal1]
set m2 [$tech findLayer Metal2]
set m3 [$tech findLayer Metal3]
set m4 [$tech findLayer Metal4]
set m5 [$tech findLayer Metal5]
set tm1 [$tech findLayer TopMetal1]
set tm2 [$tech findLayer TopMetal2]
set um $dbu

# ---- block instances: obstructions and pin shapes in chip coordinates ----------
# obs: {inst layer x1 y1 x2 y2}   pins: {inst layer net x1 y1 x2 y2}
set blk_obs [list]; set blk_pins [list]; set blk_bbox [dict create]
foreach inst [$block getInsts] {
    set master [$inst getMaster]
    if { ![$master isBlock] } { continue }
    set iname [$inst getName]
    set bb [$inst getBBox]
    dict set blk_bbox $iname [list [$bb xMin] [$bb yMin] [$bb xMax] [$bb yMax] [$master getName]]
    set xf [$inst getTransform]
    foreach obs [$master getObstructions] {
        set ln [[$obs getTechLayer] getName]
        set p1 [odb::new_Point [$obs xMin] [$obs yMin]]; $xf apply $p1
        set p2 [odb::new_Point [$obs xMax] [$obs yMax]]; $xf apply $p2
        lappend blk_obs [list $iname $ln [expr min([$p1 getX], [$p2 getX])] [expr min([$p1 getY], [$p2 getY])] [expr max([$p1 getX], [$p2 getX])] [expr max([$p1 getY], [$p2 getY])]]
    }
    foreach iterm [$inst getITerms] {
        set net [$iterm getNet]
        set nname [expr { $net == "NULL" ? "-" : [$net getName] }]
        foreach geom [$iterm getGeometries] {
            set layer [lindex $geom 0]; set r [lindex $geom 1]
            lappend blk_pins [list $iname [$layer getName] $nname [$r xMin] [$r yMin] [$r xMax] [$r yMax]]
        }
    }
}
proc overlaps {a b} {
    lassign $a ax1 ay1 ax2 ay2; lassign $b bx1 by1 bx2 by2
    expr { $ax1 < $bx2 && $bx1 < $ax2 && $ay1 < $by2 && $by1 < $ay2 }
}
proc inside {a b} {
    lassign $a ax1 ay1 ax2 ay2; lassign $b bx1 by1 bx2 by2
    expr { $ax1 >= $bx1 && $ay1 >= $by1 && $ax2 <= $bx2 && $ay2 <= $by2 }
}
# blocked rect layers net own_inst own_pin_layer own_pin_rect -> "" or a reason
proc blocked {rect layers net own_inst own_layer own_rect} {
    global blk_obs blk_pins blk_bbox m12_exempt_masters
    foreach o $blk_obs {
        lassign $o iname ln x1 y1 x2 y2
        if { [lsearch -exact $layers $ln] < 0 } { continue }
        set master [lindex [dict get $blk_bbox $iname] 4]
        if { ($ln == "Metal1" || $ln == "Metal2") && [lsearch -exact $m12_exempt_masters $master] >= 0 } { continue }
        if { ![overlaps $rect [list $x1 $y1 $x2 $y2]] } { continue }
        if { $iname == $own_inst && $ln == $own_layer } {
            # the part of the rect over the own instance must lie within the pin
            lassign [dict get $blk_bbox $iname] bx1 by1 bx2 by2 -
            lassign $rect rx1 ry1 rx2 ry2
            set ix [list [expr max($rx1,$bx1)] [expr max($ry1,$by1)] [expr min($rx2,$bx2)] [expr min($ry2,$by2)]]
            if { [inside $ix $own_rect] } { continue }
        }
        return "obstruction of $iname on $ln"
    }
    foreach p $blk_pins {
        lassign $p iname ln pnet x1 y1 x2 y2
        if { [lsearch -exact $layers $ln] < 0 || $pnet == $net } { continue }
        if { [overlaps $rect [list $x1 $y1 $x2 $y2]] } { return "pin of $iname ($pnet) on $ln" }
    }
    return ""
}

# ---- 1. VDDA grid -----------------------------------------------------------------
set vdda_net [$block findNet VDDA]
set xs [list]; set ys [list]
if { $vdda_net == "NULL" } {
    puts "\[WARNING\] analog_straps: no VDDA net, VDDA grid and feed skipped"
} else {
    $vdda_net setSpecial
    $vdda_net setSigType POWER
    set vsw "NULL"
    foreach sw [$vdda_net getSWires] { set vsw $sw }
    if { $vsw == "NULL" } { set vsw [odb::dbSWire_create $vdda_net ROUTED] }
    set core [$block getCoreArea]
    set cx1 [$core xMin]; set cy1 [$core yMin]; set cx2 [$core xMax]; set cy2 [$core yMax]
    set pitch [expr int($::env(PDN_VPITCH) * $dbu)]
    set half  [expr $pitch / 2]
    set w     [expr int($::env(PDN_VWIDTH) * $dbu)]
    set voff  [expr int($::env(PDN_VOFFSET) * $dbu) + $half]
    set hoff  [expr int($::env(PDN_HOFFSET) * $dbu) + $half]
    for { set x [expr $cx1 + $voff] } { $x + $w < $cx2 } { incr x $pitch } { lappend xs $x }
    for { set y [expr $cy1 + $hoff] } { $y + $w < $cy2 } { incr y $pitch } { lappend ys $y }
    # stripes overhang the core area by 2.5 um: the VDD/VSS ring starts 4.5 um
    # outside it and TopMetal spacing (TM1.b/TM2.b) is 1.64 um
    set ov [expr int(2.5 * $dbu)]
    # keep-out: the macros' TopMetal1/TopMetal2 obstructions + 2 um (TM1.b/TM2.b 1.64)
    set margin [expr 2 * $dbu]
    set keep1 [list]; set keep2 [list]
    foreach o $blk_obs {
        lassign $o iname ln x1 y1 x2 y2
        set kr [list [expr $x1 - $margin] [expr $y1 - $margin] [expr $x2 + $margin] [expr $y2 + $margin]]
        if { $ln == "TopMetal1" } { lappend keep1 $kr } elseif { $ln == "TopMetal2" } { lappend keep2 $kr }
    }
    proc cut_segments {x1 x2 y1 y2 keeps} {
        # parts of the vertical span y1..y2 (at x1..x2) outside every keep-out
        set segs [list [list $y1 $y2]]
        foreach k $keeps {
            lassign $k kx1 ky1 kx2 ky2
            if { $kx2 <= $x1 || $kx1 >= $x2 } { continue }
            set new [list]
            foreach sg $segs {
                lassign $sg a b
                if { $ky2 <= $a || $ky1 >= $b } { lappend new $sg; continue }
                if { $ky1 > $a } { lappend new [list $a $ky1] }
                if { $ky2 < $b } { lappend new [list $ky2 $b] }
            }
            set segs $new
        }
        return $segs
    }
    set n_tm1 0; set n_tm2 0
    foreach x $xs {
        foreach sg [cut_segments $x [expr $x + $w] [expr $cy1 - $ov] [expr $cy2 + $ov] $keep1] {
            lassign $sg a b
            if { [expr $b - $a] < [expr 5 * $dbu] } { continue }
            set crosses 0
            foreach y $ys { if { $y >= $a && [expr $y + $w] <= $b } { set crosses 1 } }
            if { !$crosses } { continue }
            odb::dbSBox_create $vsw $tm1 $x $a [expr $x + $w] $b STRIPE; incr n_tm1
        }
    }
    foreach y $ys {
        set segs [list [list [expr $cx1 - $ov] [expr $cx2 + $ov]]]
        foreach k $keep2 {
            lassign $k kx1 ky1 kx2 ky2
            if { $ky2 <= $y || $ky1 >= [expr $y + $w] } { continue }
            set new [list]
            foreach sg $segs {
                lassign $sg a b
                if { $kx2 <= $a || $kx1 >= $b } { lappend new $sg; continue }
                if { $kx1 > $a } { lappend new [list $a $kx1] }
                if { $kx2 < $b } { lappend new [list $kx2 $b] }
            }
            set segs $new
        }
        foreach sg $segs {
            lassign $sg a b
            if { [expr $b - $a] < [expr 5 * $dbu] } { continue }
            odb::dbSBox_create $vsw $tm2 $a $y $b [expr $y + $w] STRIPE; incr n_tm2
        }
    }
    foreach x $xs { foreach y $ys {
        set vx [expr $x + $w/2]; set vy [expr $y + $w/2]; set ok 1
        foreach k [concat $keep1 $keep2] { lassign $k kx1 ky1 kx2 ky2; if { $vx > $kx1 && $vx < $kx2 && $vy > $ky1 && $vy < $ky2 } { set ok 0 } }
        if { $ok } { odb::dbSBox_create $vsw $via67 $vx $vy STRIPE }
    } }
    puts "\[INFO\] analog_straps: VDDA stripe segments: $n_tm1 TopMetal1, $n_tm2 TopMetal2 (keep-outs: [llength $keep1] TM1, [llength $keep2] TM2 macro obstructions)"
    puts "\[INFO\] analog_straps: VDDA grid: [llength $xs] TopMetal1 x [llength $ys] TopMetal2 stripes, [expr $w/double($dbu)] um"

    # ---- 2. VDDA feed from pad07_vdda ---------------------------------------------
    set pinst [$block findInst $vdda_pad_inst]
    set pterm [$pinst findITerm padbare]
    set term_rect ""
    foreach geom [$pterm getGeometries] {
        set layer [lindex $geom 0]; set r [lindex $geom 1]
        if { [$layer getName] == "Metal3" } { set term_rect $r }
    }
    if { $term_rect == "" } { puts "\[ERROR\] analog_straps: padbare Metal3 geometry of $vdda_pad_inst not found"; exit 1 }
    set tx1 [$term_rect xMin]; set tx2 [$term_rect xMax]; set ty1 [$term_rect yMin]; set ty2 [$term_rect yMax]
    # east-side pad: the core is at x < tx1, the pad cell (rails from tx1 + 2 um on
    # Metal3..TopMetal1) at x > tx1. Patches 4.4 um wide: 3 um over the core side,
    # 1.4 um into the pad (0.6 um to the rails).
    set px1 [expr $tx1 - int(3.0 * $um)]; set px2 [expr $tx1 + int(1.4 * $um)]
    foreach lay [list $m3 $m4 $m5] { odb::dbSBox_create $vsw $lay $px1 $ty1 $px2 $ty2 STRIPE }
    set n_v34 0
    foreach cx [list [expr $px1 + int(1.1 * $um)] [expr $px2 - int(1.1 * $um)]] {
        for { set vy [expr $ty1 + int(0.5 * $um)] } { $vy <= [expr $ty2 - int(0.5 * $um)] } { incr vy [expr int(0.6 * $um)] } {
            odb::dbSBox_create $vsw $via34 $cx $vy STRIPE
            odb::dbSBox_create $vsw $via45 $cx $vy STRIPE
            incr n_v34
        }
    }
    # nearest vertical VDDA stripe west of the pad
    set sx1 -1
    foreach x $xs { if { [expr $x + $w] < $tx1 && $x > $sx1 } { set sx1 $x } }
    set sx2 [expr $sx1 + $w]; set scx [expr $sx1 + $w/2]
    # strap y range: the longest part of the terminal's height free of other nets'
    # Metal4/Metal5 special wires (0.6 um clearance) between the stripe and the pad
    set clr [expr int(0.6 * $um)]
    set blocked_iv [list]
    foreach net [$block getNets] {
        if { [$net getName] == "VDDA" } { continue }
        foreach sw [$net getSWires] {
            foreach sb [$sw getWires] {
                if { [$sb isVia] } {
                    set via [$sb getBlockVia]
                    if { $via == "NULL" } { set via [$sb getTechVia] }
                    if { $via == "NULL" } { continue }
                    set bl [[$via getBottomLayer] getName]; set tl [[$via getTopLayer] getName]
                    if { $bl != "Metal4" && $bl != "Metal5" && $tl != "Metal4" && $tl != "Metal5" } { continue }
                } else {
                    set lay [[$sb getTechLayer] getName]
                    if { $lay != "Metal4" && $lay != "Metal5" } { continue }
                }
                if { [$sb xMax] < [expr $sx1 - $um] || [$sb xMin] > $px2 } { continue }
                if { [$sb yMax] < $ty1 || [$sb yMin] > $ty2 } { continue }
                lappend blocked_iv [list [expr [$sb yMin] - $clr] [expr [$sb yMax] + $clr]]
            }
        }
    }
    set free [list [list $ty1 $ty2]]
    foreach iv $blocked_iv {
        lassign $iv a b; set new [list]
        foreach f $free {
            lassign $f fa fb
            if { $b <= $fa || $a >= $fb } { lappend new $f; continue }
            if { $a > $fa } { lappend new [list $fa $a] }
            if { $b < $fb } { lappend new [list $b $fb] }
        }
        set free $new
    }
    set best ""
    foreach f $free { lassign $f fa fb; if { $best == "" || [expr $fb - $fa] > [expr [lindex $best 1] - [lindex $best 0]] } { set best $f } }
    lassign $best hy1 hy2
    if { [expr $hy2 - $hy1] < [expr 3 * $um] } { puts "\[ERROR\] analog_straps: no Metal4/Metal5 corridor >= 3 um for the VDDA feed ($free)"; exit 1 }
    if { [expr $hy2 - $hy1] > [expr 8 * $um] } { set mid [expr ($hy1 + $hy2)/2]; set hy1 [expr $mid - 4 * $um]; set hy2 [expr $mid + 4 * $um] }
    odb::dbSBox_create $vsw $m4 $sx1 $hy1 $px2 $hy2 STRIPE
    odb::dbSBox_create $vsw $m5 $sx1 $hy1 $px2 $hy2 STRIPE
    set n_v56 0
    for { set vy [expr $hy1 + int(0.7 * $um)] } { $vy <= [expr $hy2 - int(0.7 * $um)] } { incr vy [expr int(1.4 * $um)] } {
        odb::dbSBox_create $vsw $via56 $scx $vy STRIPE; incr n_v56
    }
    puts "\[INFO\] analog_straps: VDDA feed: padbare strip x [expr $tx1/double($um)]..[expr $tx2/double($um)] y [expr $ty1/double($um)]..[expr $ty2/double($um)]; Metal3/4/5 patches x [expr $px1/double($um)]..[expr $px2/double($um)], $n_v34 via3_4 + $n_v34 via4_5; Metal4+Metal5 strap y [expr $hy1/double($um)]..[expr $hy2/double($um)] to the TopMetal1 stripe at x = [expr $scx/double($um)] ([expr ($px2 - $sx1)/double($um)] um), $n_v56 via5_6 (corridor candidates: $free)"
}

# ---- 2b. helper TopMetal1 stripe segments ---------------------------------------------
foreach h $helper_stripes {
    lassign $h hnet hx hy1 hy2
    set net [$block findNet $hnet]
    if { $net == "NULL" } { puts "\[WARNING\] analog_straps: helper stripe: no net $hnet"; continue }
    set swire "NULL"
    foreach sw [$net getSWires] { set swire $sw }
    if { $swire == "NULL" } { set swire [odb::dbSWire_create $net ROUTED] }
    set hw [expr int($::env(PDN_VWIDTH) * $dbu)]
    set hx1 [expr int($hx * $um) - $hw/2]; set hx2 [expr $hx1 + $hw]
    set hy1u [expr int($hy1 * $um)]; set hy2u [expr int($hy2 * $um)]
    set why [blocked [list [expr $hx1 - 2*$um] [expr $hy1u - 2*$um] [expr $hx2 + 2*$um] [expr $hy2u + 2*$um]] [list TopMetal1] $hnet "" "" [list 0 0 0 0]]
    if { $why != "" } { puts "\[WARNING\] analog_straps: helper stripe $hnet x=$hx skipped ($why)"; continue }
    # the net's TopMetal2 stripes crossed by the segment
    set tied 0
    foreach sb [$swire getWires] {
        if { [$sb isVia] || [[$sb getTechLayer] getName] != "TopMetal2" } { continue }
        if { [expr [$sb yMax] - [$sb yMin]] > [expr 3 * $dbu] } { continue }
        if { [$sb xMin] > $hx1 || [$sb xMax] < $hx2 } { continue }
        set tcy [expr ([$sb yMin] + [$sb yMax]) / 2]
        if { $tcy < [expr $hy1u + $hw/2] || $tcy > [expr $hy2u - $hw/2] } { continue }
        odb::dbSBox_create $swire $via67 [expr int($hx * $um)] $tcy STRIPE
        incr tied
    }
    if { !$tied } { puts "\[WARNING\] analog_straps: helper stripe $hnet x=$hx crosses no TopMetal2 stripe of its net, not created"; continue }
    odb::dbSBox_create $swire $tm1 $hx1 $hy1u $hx2 $hy2u STRIPE
    puts "\[INFO\] analog_straps: helper TopMetal1 stripe $hnet x=$hx y=$hy1..$hy2, $tied via6_7 to the TopMetal2 stripe(s)"
}

# ---- 3. macro supply pins -------------------------------------------------------------
set n_straps 0
foreach inst_name $insts {
    set inst [$block findInst $inst_name]
    if { $inst == "NULL" } { puts "\[WARNING\] analog_straps: no instance $inst_name"; continue }
    foreach iterm [$inst getITerms] {
        set mterm [$iterm getMTerm]
        set sig [$mterm getSigType]
        if { $sig != "POWER" && $sig != "GROUND" } { continue }
        set net [$iterm getNet]
        if { $net == "NULL" } { puts "\[WARNING\] analog_straps: $inst_name/[$mterm getName] has no net"; continue }
        set net_name [$net getName]
        set pin_name "$inst_name/[$mterm getName]"
        set swire "NULL"
        foreach sw [$net getSWires] { set swire $sw }
        if { $swire == "NULL" } { set swire [odb::dbSWire_create $net ROUTED] }
        # TopMetal1 stripes (not ring sides) of this net: {x1 x2 y1 y2}
        set stripes [list]
        foreach sb [$swire getWires] {
            if { [$sb isVia] } { continue }
            if { [[$sb getTechLayer] getName] != "TopMetal1" } { continue }
            if { [expr [$sb xMax] - [$sb xMin]] > [expr 3 * $dbu] } { continue }
            lappend stripes [list [$sb xMin] [$sb xMax] [$sb yMin] [$sb yMax]]
        }
        set pin_ok 0; set pin_unresolved [list]
        foreach geom [$iterm getGeometries] {
            set layer [lindex $geom 0]; set r [lindex $geom 1]
            set lname [$layer getName]
            if { $lname != "Metal3" && $lname != "Metal1" } { continue }
            set bx1 [$r xMin]; set by1 [$r yMin]; set bx2 [$r xMax]; set by2 [$r yMax]
            set bh [expr $by2 - $by1]
            if { $bh > [expr 3 * $dbu] } { continue }   ;# not a bar/rail (e.g. a shifter's big vss plate)
            set cy [expr ($by1 + $by2) / 2]
            set pin_rect [list $bx1 $by1 $bx2 $by2]
            # (a) stripes crossing the bar: via stack at each crossing
            set hit 0
            if { $lname == "Metal3" } {
                foreach st $stripes {
                    lassign $st sx1 sx2 sy1 sy2
                    if { $sx1 < $bx1 || $sx2 > $bx2 } { continue }
                    # the stripe must overlap the bar by >= 1 um (or the whole bar if thinner)
                    set oy1 [expr max($sy1, $by1)]; set oy2 [expr min($sy2, $by2)]
                    if { [expr $oy2 - $oy1] < [expr min($um, $bh)] } { continue }
                    set cx [expr ($sx1 + $sx2) / 2]
                    set vcy [expr ($oy1 + $oy2) / 2]
                    set py1 [expr min($by1, $vcy - int(0.25 * $um))]; set py2 [expr max($by2, $vcy + int(0.25 * $um))]
                    set why [blocked [list $sx1 $py1 $sx2 $py2] [list Metal4 Metal5] $net_name $inst_name $lname $pin_rect]
                    if { $why != "" } { puts "\[WARNING\] analog_straps: $pin_name: stack at x=[expr $cx/double($um)] skipped ($why)"; continue }
                    odb::dbSBox_create $swire $m4 $sx1 $py1 $sx2 $py2 STRIPE
                    odb::dbSBox_create $swire $m5 $sx1 $py1 $sx2 $py2 STRIPE
                    odb::dbSBox_create $swire $via34 $cx $vcy STRIPE
                    odb::dbSBox_create $swire $via45 $cx $vcy STRIPE
                    odb::dbSBox_create $swire $via56 $cx $vcy STRIPE
                    incr n_straps; set hit 1; set pin_ok 1
                    puts "\[INFO\] analog_straps: $pin_name ($net_name): stack on the bar at ([expr $cx/double($um)], [expr $vcy/double($um)])"
                }
            }
            if { $hit } { continue }
            # (b) no crossing stripe: jog to the nearest stripe spanning this y whose
            #     stack and jog are free of other block instances' metal
            set cands [list]
            foreach st $stripes {
                lassign $st sx1 sx2 sy1 sy2
                if { $sy1 > [expr $by1 - 2*$dbu] || $sy2 < [expr $by2 + 2*$dbu] } { continue }
                set cx [expr ($sx1 + $sx2) / 2]
                lappend cands [list [expr min(abs($cx - $bx1), abs($cx - $bx2))] $st]
            }
            set cands [lsort -integer -index 0 $cands]
            set done 0
            foreach cand $cands {
                lassign [lindex $cand 1] sx1 sx2 sy1 sy2
                set cx [expr ($sx1 + $sx2) / 2]
                set w  [expr max($bh, int(0.5 * $dbu))]
                set jy1 [expr $cy - $w/2]; set jy2 [expr $cy + $w/2]
                set jx1 [expr min($bx1, $sx1)]; set jx2 [expr max($bx2, $sx2)]
                set py1 [expr min($jy1, $cy - int(0.25 * $um))]; set py2 [expr max($jy2, $cy + int(0.25 * $um))]
                set stack_rect [list [expr $sx1 - int(0.1 * $um)] $py1 [expr $sx2 + int(0.1 * $um)] $py2]
                set jog_rect [list $jx1 $jy1 $jx2 $jy2]
                if { $lname == "Metal3" } {
                    set why [blocked $stack_rect [list Metal3 Metal4 Metal5] $net_name $inst_name $lname $pin_rect]
                    if { $why == "" } { set why [blocked $jog_rect [list Metal3] $net_name $inst_name $lname $pin_rect] }
                } else {
                    set why [blocked $stack_rect [list Metal2 Metal3 Metal4 Metal5] $net_name $inst_name $lname $pin_rect]
                    if { $why == "" } { set why [blocked $jog_rect [list Metal2] $net_name $inst_name $lname $pin_rect] }
                }
                if { $why != "" } { puts "\[INFO\] analog_straps: $pin_name: stripe at x=[expr $cx/double($um)] skipped ($why)"; continue }
                if { $lname == "Metal3" } {
                    odb::dbSBox_create $swire $m3 $jx1 $jy1 $jx2 $jy2 STRIPE
                } else {
                    # Metal1 rail: via up to Metal2 at the rail, jog on Metal2, then up
                    set px [expr ($bx1 + $bx2) / 2]
                    odb::dbSBox_create $swire $m2 $jx1 $jy1 $jx2 $jy2 STRIPE
                    odb::dbSBox_create $swire $via12 $px $cy STRIPE
                    odb::dbSBox_create $swire $m3 $sx1 $py1 $sx2 $py2 STRIPE
                    odb::dbSBox_create $swire $via23 $cx $cy STRIPE
                }
                odb::dbSBox_create $swire $m4 $sx1 $py1 $sx2 $py2 STRIPE
                odb::dbSBox_create $swire $m5 $sx1 $py1 $sx2 $py2 STRIPE
                odb::dbSBox_create $swire $via34 $cx $cy STRIPE
                odb::dbSBox_create $swire $via45 $cx $cy STRIPE
                odb::dbSBox_create $swire $via56 $cx $cy STRIPE
                incr n_straps; set done 1; set pin_ok 1
                puts "\[INFO\] analog_straps: $pin_name ($net_name): jog on [expr {$lname == "Metal3" ? "Metal3" : "Metal2"}] x [expr $jx1/double($um)]..[expr $jx2/double($um)] at y=[expr $cy/double($um)], stack at x=[expr $cx/double($um)]"
                break
            }
            if { !$done } { lappend pin_unresolved "$lname rect [expr $bx1/double($um)],[expr $by1/double($um)]..[expr $bx2/double($um)],[expr $by2/double($um)] ([llength $cands] candidates)" }
        }
        if { !$pin_ok && [llength $pin_unresolved] } { puts "\[WARNING\] analog_straps: $pin_name ($net_name): not strapped, no free stripe for: [join $pin_unresolved {; }]; left to check_power_grid" }
    }
}
puts "\[INFO\] analog_straps: $n_straps via stacks added"

# ---- 4. connectivity check --------------------------------------------------------
foreach net_name [concat $::env(VDD_NETS) $::env(GND_NETS) VDDA] {
    puts "\[INFO\] analog_straps: check_power_grid -net $net_name"
    if { [catch { check_power_grid -net $net_name -error_file $::env(STEP_DIR)/${net_name}-grid-errors.rpt } err] } {
        puts "\[WARNING\] analog_straps: $err"
    }
}

if { ![info exists ::g1_standalone] } { write_views }

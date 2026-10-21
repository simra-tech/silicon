# Yosys synthesis of r1_ctrl_top for the cell area (revision 0.5 adds a CHECK pass log; revision 0.4: R1_CFG_FLOPS + R1_CFG_GATED, flip-flop
# register file on per-word gated clocks; not a hardening run).
# Library: sg13g2_stdcell typical 1.2 V 25 C from the pinned PDK.
# Revision 0.2: Booth multiplier recoding; latches mapped with the PDK LibreLane
# latch map (sg13g2_dlhrq_1 / sg13g2_dllrq_1), as LibreLane does; ABC delay
# target 23810 ps (42 MHz, D13).
# Run inside the container with G1_WORKDIR=designs/r1-joint/blocks/r1_ctrl:
#   SYN_OUT=<dir> flow/run.sh yosys -c flow/synth.tcl
yosys -import
set lib $::env(PDK_ROOT)/ihp-sg13g2/libs.ref/sg13g2_stdcell/lib/sg13g2_stdcell_typ_1p20V_25C.lib
set lmap $::env(PDK_ROOT)/ihp-sg13g2/libs.tech/librelane/sg13g2_stdcell/latch_map.v
set out $::env(SYN_OUT)
foreach f [lsort [glob rtl/*.v]] { read_verilog -defer -DR1_CFG_FLOPS -DR1_CFG_GATED $f }
hierarchy -check -top r1_ctrl_top
synth -top r1_ctrl_top -flatten -booth
# CHECK pass on the generic netlist (after the mapping the library cells have no port directions and every
# output is reported as undriven: the first 0.5 run put it there and got 86 false problems)
tee -o $out/yosys_check.txt check
techmap -map $lmap
dfflibmap -liberty $lib
abc -liberty $lib -D 23810
opt_clean -purge
hilomap -hicell sg13g2_tiehi L_HI -locell sg13g2_tielo L_LO
tee -o $out/stat_flat.txt stat -liberty $lib
write_verilog -noattr $out/r1_ctrl_top.nl.v
# per-block breakdown (hierarchical run; small leaf modules r1_cword, r1_sync2,
# r1_idrom, r1_sinlut, r1_adcw are listed under their parents by summarize.py)
design -reset
foreach f [lsort [glob rtl/*.v]] { read_verilog -defer -DR1_CFG_FLOPS -DR1_CFG_GATED $f }
hierarchy -check -top r1_ctrl_top
synth -top r1_ctrl_top -booth
techmap -map $lmap
dfflibmap -liberty $lib
abc -liberty $lib -D 23810
opt_clean -purge
tee -o $out/stat_hier.txt stat -liberty $lib

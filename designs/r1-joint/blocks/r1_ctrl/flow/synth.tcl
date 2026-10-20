# Yosys synthesis of r1_ctrl_top for the gate count (not a hardening run).
# Library: sg13g2_stdcell typical 1.2 V 25 C from the pinned PDK.
# Run inside the container with G1_WORKDIR=designs/r1-joint/blocks/r1_ctrl:
#   flow/run.sh yosys -c flow/synth.tcl
yosys -import
set lib $::env(PDK_ROOT)/ihp-sg13g2/libs.ref/sg13g2_stdcell/lib/sg13g2_stdcell_typ_1p20V_25C.lib
set out $::env(SYN_OUT)
foreach f [lsort [glob rtl/*.v]] { read_verilog -defer $f }
hierarchy -check -top r1_ctrl_top
synth -top r1_ctrl_top -flatten
dfflibmap -liberty $lib
abc -liberty $lib -D 33333
opt_clean -purge
hilomap -hicell sg13g2_tiehi L_HI -locell sg13g2_tielo L_LO
tee -o $out/stat_flat.txt stat -liberty $lib
write_verilog -noattr $out/r1_ctrl_top.nl.v
# per-block breakdown (hierarchical run)
design -reset
foreach f [lsort [glob rtl/*.v]] { read_verilog -defer $f }
hierarchy -check -top r1_ctrl_top
synth -top r1_ctrl_top
dfflibmap -liberty $lib
abc -liberty $lib -D 33333
opt_clean -purge
tee -o $out/stat_hier.txt stat -liberty $lib

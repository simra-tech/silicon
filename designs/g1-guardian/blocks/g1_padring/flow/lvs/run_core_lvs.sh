#!/usr/bin/env bash
# Core-only KLayout LVS of the assembled chip (inside the container, repo at /work):
#   run_core_lvs.sh <run dir> <out dir>
# 1. core_cdl.py: chip CDL minus the ring cells -> g1_core subcircuit with the pad nets as ports
# 2. core_only_gds.py: chip GDS minus the ring cells, std-cell variants folded, pad nets labelled on their wires, top renamed g1_core
# 3. PDK run_lvs.py (deep) on the two
set -u
RUN=$1; OUT=$2; mkdir -p $OUT
B=/work/designs/g1-guardian/blocks/g1_padring
python3 $B/flow/lvs/core_cdl.py $B/netlist/g1_chip_top.cdl $OUT/g1_core.cdl | tee $OUT/core_cdl.log
klayout -b -rd gds=$RUN/final/gds/g1_chip_top.gds -rd out=$OUT/g1_core.gds -rd lef=$B/ip/sg13g2_io_padbare/lef/sg13g2_io.lef -rd defp=$RUN/final/def/g1_chip_top.def -r $B/flow/lvs/core_only_gds.py 2>&1 | grep -v "Warning: Ignoring" | tee $OUT/core_only_gds.log
cd $OUT && python3 /foss/pdks/ihp-sg13g2/libs.tech/klayout/tech/lvs/run_lvs.py --layout g1_core.gds --netlist g1_core.cdl --topcell g1_core --run_mode deep --run_dir lvs --top_lvl_pins --spice_comments 2>&1 | tail -25

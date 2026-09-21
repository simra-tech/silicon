#!/usr/bin/env bash
# Reproduce the G1_PADRING build: bondpad from the PDK PCell, then the LibreLane
# Chip flow on designs/g1-guardian/blocks/g1_padring/flow/config.yaml.
# Everything runs inside the pinned container through flow/run.sh.
#   flow/run_ring.sh                 full run, tag "ring-1350" (override with G1_RUN_TAG)
#   flow/run_ring.sh --to OpenROAD.PadRing   ring placement only
# Extra arguments are passed to librelane. Runs land in <block>/flow/runs/<tag>/
# (gitignored); evidence is copied by hand into <block>/reports/.
# KLayout LVS of a finished run (not part of the flow, see README "Checks"):
#   python3 <block>/flow/lvs/pnl2cdl.py <run>/final/pnl/g1_chip_top.pnl.v sch.cdl \
#     $PDK_ROOT/$PDK/libs.ref/sg13g2_stdcell/cdl/sg13g2_stdcell.cdl $PDK_ROOT/$PDK/libs.ref/sg13g2_io/cdl/sg13g2_io.cdl
#   python3 $PDK_ROOT/$PDK/libs.tech/klayout/tech/lvs/run_lvs.py --layout <run>/final/gds/g1_chip_top.gds \
#     --netlist sch.cdl --topcell g1_chip_top --run_mode deep --top_lvl_pins --run_dir <dir>
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BLOCK="designs/g1-guardian/blocks/g1_padring"
TAG="${G1_RUN_TAG:-ring-1350}"

echo "[run_ring] 1/2 bondpad_70x70_tm1 from the PDK bondpad PCell"
G1_WORKDIR="$BLOCK" "$HERE/run.sh" bash -c \
  'KLAYOUT_PATH=$PDK_ROOT/$PDK/libs.tech/klayout klayout -zz -nc -n sg13g2 \
   -r ip/bondpad_70x70_tm1/gen_bondpad.py -rd output=ip/bondpad_70x70_tm1/gds/bondpad_70x70_tm1.gds'

echo "[run_ring] 2/2 LibreLane Chip flow, run tag '$TAG'"
G1_WORKDIR="$BLOCK" "$HERE/run.sh" librelane flow/config.yaml \
  --pdk ihp-sg13g2 --pdk-root /foss/pdks --manual-pdk \
  --run-tag "$TAG" --overwrite "$@"

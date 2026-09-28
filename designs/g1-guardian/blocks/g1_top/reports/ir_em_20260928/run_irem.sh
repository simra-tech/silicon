#!/bin/sh
# Chip-level IR/EM solve of record. Run inside flow/run.sh from the repository root; $1 = ${BULK}/postsub-20260928/irem
# (holds geom/ from flow/pex/supply_geometry.py). Record mesh pitch 1.0 um; 5.0 and 2.5 um for the convergence table.
set -e
B=$1; R=designs/g1-guardian/blocks/g1_top/reports/ir_em_20260928
python3 $R/make_loads.py $B/loads
solve() {  # pitch tech outdir [cases]
  for net in VDD VSS VDDA IOVDD IOVSS GATE SENSE_P SENSE_N VREF; do
    python3 flow/pex/supply_mesh_solve.py --geom $B/geom/$net.json --loads $B/loads/$net.json --tech $2 --pitch $1 --outdir $3 $4
  done
  python3 flow/pex/supply_mesh_solve.py --geom $B/geom/i_core_vref.json --loads $B/loads/i_core_vref.json --tech $2 --pitch $1 \
    --source-group Xi_core_u_bgr --outdir $3 $4
}
solve 1.0 typ $B/solve
solve 1.0 worst $B/solve
solve 5.0 typ $B/pitch_5.0 "--cases trip_worst"
solve 2.5 typ $B/pitch_2.5 "--cases trip_worst"

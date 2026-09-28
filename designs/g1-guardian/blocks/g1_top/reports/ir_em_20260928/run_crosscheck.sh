B=$1
for net in VDD VSS VDDA GATE SENSE_P SENSE_N; do
  python3 flow/pex/supply_mesh_solve.py --geom $B/geom/$net.json --loads $B/xcheck/loads/$net.json --tech typ --pitch 1.0 --outdir $B/xcheck/mesh
  python3 flow/pex/supply_rnet_crosscheck.py --geom $B/geom/$net.json --out $B/xcheck/rnet_sq_$net.json
  python3 flow/pex/supply_rnet_crosscheck.py --geom $B/geom/$net.json --algorithm Tesselation --out $B/xcheck/rnet_tes_$net.json
done
python3 flow/pex/supply_mesh_solve.py --geom $B/geom/i_core_vref.json --loads $B/xcheck/loads/i_core_vref.json --tech typ --pitch 1.0 --source-group Xi_core_u_bgr --outdir $B/xcheck/mesh
python3 flow/pex/supply_rnet_crosscheck.py --geom $B/geom/i_core_vref.json --source-group Xi_core_u_bgr --out $B/xcheck/rnet_sq_i_core_vref.json
python3 flow/pex/supply_rnet_crosscheck.py --geom $B/geom/i_core_vref.json --source-group Xi_core_u_bgr --algorithm Tesselation --out $B/xcheck/rnet_tes_i_core_vref.json

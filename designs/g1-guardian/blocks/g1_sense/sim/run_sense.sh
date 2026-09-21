#!/usr/bin/env bash
# Run tb_sense.cir over corners and temperatures. Usage (repo root):
#   G1_WORKDIR=designs/g1-guardian/blocks/g1_sense/sim flow/run.sh bash run_sense.sh [quick]
# Logs: logs/sense_<mos>_<res>_<vdd>_<temp>_cm<vcm>.log ; summary: results_sense.txt
set -u
mkdir -p logs ../../../../../build/g1_sense
B=../../../../../build/g1_sense
run() { # MOS RES CAP VDDA TEMP VCM
  tag="sense_$1_$2_$4V_$5C_cm$6"
  sed -e "s/@@MOS@@/$1/g" -e "s/@@RES@@/$2/g" -e "s/@@CAP@@/$3/g" -e "s/@@VDDA@@/$4/g" -e "s/@@TEMP@@/$5/g" -e "s/@@VCM@@/$6/g" tb_sense.cir > $B/$tag.cir
  ngspice -b $B/$tag.cir > logs/$tag.log 2>&1
  echo "== $tag"; grep -E "^(OP|DC|AC|PSRR|CM gain|STEP)" logs/$tag.log
}
{
echo "# G1_SENSE results, $(date -u +%Y-%m-%dT%H:%MZ), ngspice $(ngspice -v | grep -o 'ngspice-[0-9]*')"
if [ "${1:-}" = quick ]; then run mos_tt res_typ cap_typ 3.3 27 0; exit; fi
if [ "${1:-}" = one ]; then run $2 $3 $4 $5 $6 $7; exit; fi   # single point, appended by the caller
for T in -40 27 85 125 150 175; do run mos_tt res_typ cap_typ 3.3 $T 0; done
for T in -40 27 175; do run mos_ff res_bcs cap_bcs 3.3 $T 0; run mos_ss res_wcs cap_wcs 3.3 $T 0; done
run mos_tt res_typ cap_typ 3.0 27 0; run mos_tt res_typ cap_typ 3.6 27 0
run mos_tt res_typ cap_typ 3.3 27 -0.1; run mos_tt res_typ cap_typ 3.3 27 0.3
} | tee results_sense.txt
# "one" runs are appended to results_sense.txt by: ... run_sense.sh one MOS RES CAP VDDA TEMP VCM >> results_sense.txt

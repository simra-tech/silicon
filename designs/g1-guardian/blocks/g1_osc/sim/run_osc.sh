#!/usr/bin/env bash
# Run tb_osc.cir over corners, temperatures, supplies and trim codes; tb_osc_startup.cir for start-up.
# Usage (repo root): G1_WORKDIR=designs/g1-guardian/blocks/g1_osc/sim flow/run.sh bash run_osc.sh [quick|trim|corners|startup|all]
# Variants are written to build/g1_osc/, logs to logs/, summary appended to results_osc.txt.
set -u
mkdir -p logs ../../../../../build/g1_osc
B=../../../../../build/g1_osc
run() { # MOS RES CAP VDD TEMP CODE
  local c=$6
  local b0=$((c&1)) b1=$(((c>>1)&1)) b2=$(((c>>2)&1)) b3=$(((c>>3)&1))
  tag="osc_$1_$2_$3_$4V_$5C_code$6"
  sed -e "s/@@MOS@@/$1/" -e "s/@@RES@@/$2/" -e "s/@@CAP@@/$3/" -e "s/@@VDD@@/$4/g" -e "s/@@TEMP@@/$5/" \
      -e "s/@@B0@@/$b0/" -e "s/@@B1@@/$b1/" -e "s/@@B2@@/$b2/" -e "s/@@B3@@/$b3/" tb_osc.cir > $B/$tag.cir
  ngspice -b $B/$tag.cir > logs/$tag.log 2>&1
  echo "== $tag"; grep "^OSC" logs/$tag.log
}
startup() { # MOS RES CAP TEMP
  tag="osc_startup_$1_$2_$3_$4C"
  sed -e "s/@@MOS@@/$1/" -e "s/@@RES@@/$2/" -e "s/@@CAP@@/$3/" -e "s/@@TEMP@@/$4/" tb_osc_startup.cir > $B/$tag.cir
  ngspice -b $B/$tag.cir > logs/$tag.log 2>&1
  echo "== $tag"; grep "^STARTUP" logs/$tag.log
}
what=${1:-quick}
# extremes: the two extreme corners at 27 C, mid code and the trim code nearest to 10 MHz (revision 4 check)
{
echo "# G1_OSC results ($what), $(date -u +%Y-%m-%dT%H:%MZ), $(ngspice -v | grep -o 'ngspice-[0-9]*')"
case $what in
quick) run mos_tt res_typ cap_typ 1.2 27 8 ;;
trim) for c in 0 4 8 12 15; do run mos_tt res_typ cap_typ 1.2 27 $c; done ;;
corners)
  for T in -40 27 85 125 150 175; do run mos_tt res_typ cap_typ 1.2 $T 8; done
  for T in -40 27 175; do
    run mos_ff res_bcs cap_bcs 1.2 $T 8; run mos_ss res_wcs cap_wcs 1.2 $T 8
    run mos_tt res_bcs cap_wcs 1.2 $T 8; run mos_tt res_wcs cap_bcs 1.2 $T 8
  done
  run mos_tt res_typ cap_typ 1.08 27 8; run mos_tt res_typ cap_typ 1.32 27 8
  run mos_ss res_wcs cap_wcs 1.08 175 8; run mos_ff res_bcs cap_bcs 1.32 -40 8 ;;
extremes)
  run mos_tt res_typ cap_typ 1.2 27 8
  run mos_ff res_bcs cap_bcs 1.2 27 8; run mos_ff res_bcs cap_bcs 1.2 27 15; run mos_ff res_bcs cap_bcs 1.2 27 14
  run mos_ss res_wcs cap_wcs 1.2 27 8; run mos_ss res_wcs cap_wcs 1.2 27 4; run mos_ss res_wcs cap_wcs 1.2 27 3; run mos_ss res_wcs cap_wcs 1.2 27 0 ;;
startup) startup mos_tt res_typ cap_typ 27; startup mos_ss res_wcs cap_wcs -40; startup mos_ss res_wcs cap_wcs 175 ;;
all) bash run_osc.sh trim >/dev/null; bash run_osc.sh corners >/dev/null; bash run_osc.sh startup >/dev/null; bash run_osc.sh extremes >/dev/null; exit ;;
esac
} | tee -a results_osc.txt

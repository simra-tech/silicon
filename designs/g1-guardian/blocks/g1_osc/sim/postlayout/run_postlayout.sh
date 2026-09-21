#!/usr/bin/env bash
# Post-layout runs of G1_OSC on the kpex 2.5D CC netlist (g1_osc_pex.spice): same decks as ../run_osc.sh
# (tb_osc_pex.cir = ../tb_osc.cir with the .include swapped), nominal, trim, the two extreme corners
# at 27 C with the trim codes nearest 10 MHz, and start-up.
# Usage (repo root): G1_WORKDIR=designs/g1-guardian/blocks/g1_osc/sim flow/run.sh bash postlayout/run_postlayout.sh
set -u
mkdir -p postlayout/logs ../../../../../build/g1_osc/postlayout
B=../../../../../build/g1_osc/postlayout
run() { # MOS RES CAP VDD TEMP CODE
  local c=$6
  local b0=$((c&1)) b1=$(((c>>1)&1)) b2=$(((c>>2)&1)) b3=$(((c>>3)&1))
  tag="pex_osc_$1_$2_$3_$4V_$5C_code$6"
  sed -e "s/@@MOS@@/$1/" -e "s/@@RES@@/$2/" -e "s/@@CAP@@/$3/" -e "s/@@VDD@@/$4/g" -e "s/@@TEMP@@/$5/" \
      -e "s/@@B0@@/$b0/" -e "s/@@B1@@/$b1/" -e "s/@@B2@@/$b2/" -e "s/@@B3@@/$b3/" postlayout/tb_osc_pex.cir > $B/$tag.cir
  ngspice -b $B/$tag.cir > postlayout/logs/$tag.log 2>&1
  echo "== $tag"; grep "^OSC" postlayout/logs/$tag.log
}
startup() { # MOS RES CAP TEMP
  tag="pex_osc_startup_$1_$2_$3_$4C"
  sed -e "s/@@MOS@@/$1/" -e "s/@@RES@@/$2/" -e "s/@@CAP@@/$3/" -e "s/@@TEMP@@/$4/" postlayout/tb_osc_startup_pex.cir > $B/$tag.cir
  ngspice -b $B/$tag.cir > postlayout/logs/$tag.log 2>&1
  echo "== $tag"; grep "^STARTUP" postlayout/logs/$tag.log
}
{
echo "# G1_OSC post-layout results (kpex 2.5D CC), $(date -u +%Y-%m-%dT%H:%MZ), $(ngspice -v | grep -o 'ngspice-[0-9]*')"
for c in 0 8 15; do run mos_tt res_typ cap_typ 1.2 27 $c; done
run mos_ff res_bcs cap_bcs 1.2 27 8; run mos_ff res_bcs cap_bcs 1.2 27 15; run mos_ff res_bcs cap_bcs 1.2 27 14; run mos_ff res_bcs cap_bcs 1.2 27 12; run mos_ff res_bcs cap_bcs 1.2 27 11
run mos_ss res_wcs cap_wcs 1.2 27 8; run mos_ss res_wcs cap_wcs 1.2 27 3; run mos_ss res_wcs cap_wcs 1.2 27 4; run mos_ss res_wcs cap_wcs 1.2 27 0; run mos_ss res_wcs cap_wcs 1.2 27 1
run mos_tt res_typ cap_typ 1.08 27 8; run mos_tt res_typ cap_typ 1.32 27 8
run mos_tt res_typ cap_typ 1.2 -40 8; run mos_tt res_typ cap_typ 1.2 125 8
startup mos_tt res_typ cap_typ 27
} | tee postlayout/results_postlayout.txt

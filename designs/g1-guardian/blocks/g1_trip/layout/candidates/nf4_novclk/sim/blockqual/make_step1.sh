#!/usr/bin/env bash
# Block qualification 2026-09-27, step 1: writes the post-layout comparator delay, settle and DAC decks for the r4
# (novclk) and r3 (nf4) extractions into $1, with exactly the substitutions of sim/postlayout/run_postlayout.sh
# (cmp(): same sed on tb_trip_cmp_pex.cir, 5 MHz; dac(): tb_trip_dac_pex.cir with its include swapped to the extraction,
# because run_postlayout.sh's dac() always includes g1_trip_pex.spice) and tb_trip_settle.cir with @@NET@@/@@MOS@@/@@VDD@@/@@TEMP@@.
# Decks are run with ngspice -b from blocks/g1_trip/sim (G1_WORKDIR), like run_postlayout.sh.
set -eu
O=$1; mkdir -p "$O"; cd "$(dirname "$0")/../../../../../sim"
for net in r4:postlayout/g1_trip_nf4_novclk_pex.spice r3:postlayout/g1_trip_nf4_pex.spice; do
  tag=${net%%:*}; N=${net#*:}
  for c in "mos_tt 1.2 27" "mos_ss 1.08 -40"; do set -- $c
    T=$(python3 -c "print(1e-6/5)"); TH=$(python3 -c "print(0.5e-6/5)"); T2=$(python3 -c "print(20e-9+1e-6/5)"); TE=$(python3 -c "print(20e-9+1.45e-6/5)")
    sed -e "s/@@MOS@@/$1/" -e "s/@@VDD@@/$2/" -e "s/@@TEMP@@/$3/" -e "s/@@TPER@@/$T/g" -e "s/@@THALF@@/$TH/g" \
        -e "s/@@T2@@/$T2/g" -e "s/@@TEND@@/$TE/g" -e "s#postlayout/g1_trip_pex.spice#$N#" postlayout/tb_trip_cmp_pex.cir > $O/${tag}_cmp_delay_$1_$2V_$3C_5MHz.cir
  done
  for c in "mos_tt 1.2 27" "mos_ss 1.08 -40" "mos_ff 1.32 125"; do set -- $c
    sed -e "s#@@NET@@#$N#" -e "s/@@MOS@@/$1/" -e "s/@@VDD@@/$2/" -e "s/@@TEMP@@/$3/" postlayout/tb_trip_settle.cir > $O/${tag}_settle_$1_$2V_$3C.cir
  done
  sed -e "s/@@MOS@@/mos_tt/" -e "s/@@RES@@/res_typ/" -e "s/@@TEMP@@/27/" -e "s#postlayout/g1_trip_pex.spice#$N#" postlayout/tb_trip_dac_pex.cir > $O/${tag}_dac_mos_tt_res_typ_27C.cir
done
grep -l "include postlayout/g1_trip_nf4" $O/*.cir | wc -l

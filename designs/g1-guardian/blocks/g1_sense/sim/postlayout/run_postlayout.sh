#!/usr/bin/env bash
# Post-layout runs of the G1_SENSE testbench on the kpex netlist. Usage (repo root):
#   G1_WORKDIR=designs/g1-guardian/blocks/g1_sense/sim flow/run.sh bash postlayout/run_postlayout.sh [all|one MOS RES CAP VDDA TEMP VCM]
# The deck is tb_sense.cir with the schematic netlist swapped for postlayout/g1_sense_pex.spice and the
# nodeset/echo names of the OTA-internal nodes rewritten to the flat names (xdut.xota_out1 ...).
# Logs: postlayout/logs/pl_<mos>_<res>_<vdd>_<temp>_cm<vcm>.log ; summary: postlayout/results_postlayout.txt
set -u
mkdir -p postlayout/logs ../../../../../build/g1_sense_pl
B=../../../../../build/g1_sense_pl
sed -e 's#^\.include netlist/g1_sense.spice#.include postlayout/g1_sense_pex.spice#' \
    -e 's/xdut\.xota\./xdut.xota_/g' -e 's/xdut\.xbuf\./xdut.xbuf_/g' -e 's/xdut\.xref\./xdut.xref_/g' \
    -e 's/ sub! / 0 /g' \
    -e '/^meas tran tsettle when vo=vlo1 rise=1/a\
let err = abs(vo - vhi)\
meas tran tband when err=0.01*(vhi-vlo) cross=last\
let tsb = tband-1u\
echo "SETTLE_BAND: t_last_outside_1pct=" $\&tsb' tb_sense.cir > postlayout/tb_sense_pex.cir
# (added measurement: last time the output is outside the +-1 % band of the final value, since the
#  post-layout overshoot exceeds 1 % and the schematic deck's t_to_99pct is a first-crossing time)
# (the load resistors' substrate node sub! is tied to ground here: in the schematic deck it floats
#  with the 95 unit resistors on it, in the PEX netlist the resistor substrates are vss)
run() { # MOS RES CAP VDDA TEMP VCM
  tag="pl_$1_$2_$4V_$5C_cm$6"
  sed -e "s/@@MOS@@/$1/g" -e "s/@@RES@@/$2/g" -e "s/@@CAP@@/$3/g" -e "s/@@VDDA@@/$4/g" -e "s/@@TEMP@@/$5/g" -e "s/@@VCM@@/$6/g" postlayout/tb_sense_pex.cir > $B/$tag.cir
  ngspice -b $B/$tag.cir > postlayout/logs/$tag.log 2>&1
  echo "== $tag"; grep -E "^(OP|DC|AC|PSRR|CM gain|STEP|SETTLE_BAND)" postlayout/logs/$tag.log
}
{
echo "# G1_SENSE post-layout results (kpex 2.5D CC netlist), $(date -u +%Y-%m-%dT%H:%MZ), ngspice $(ngspice -v | grep -o 'ngspice-[0-9]*')"
if [ "${1:-all}" = one ]; then run $2 $3 $4 $5 $6 $7; exit; fi
run mos_tt res_typ cap_typ 3.3 27 0
run mos_tt res_typ cap_typ 3.3 175 0
run mos_tt res_typ cap_typ 3.3 -40 0
run mos_ss res_wcs cap_wcs 3.3 175 0
run mos_ff res_bcs cap_bcs 3.3 27 0
} | tee postlayout/results_postlayout.txt

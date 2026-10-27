#!/bin/sh
# usage (host, r1_ctrl block dir as cwd, G1_RESULTS_ROOT set): release08.sh <ll-run> <gl-run> <sta-run>
# writes <G1_RESULTS_ROOT>/r1_ctrl/r1ctrl_08_release with SHA256SUMS (same file set as r1ctrl_07_release)
set -eu
R=$G1_RESULTS_ROOT/r1_ctrl; LL=$1; GL=$2; STA=$3
F=$R/$LL/flow/runs/$LL/final; O=$R/r1ctrl_08_release
[ -e "$O" ] && { echo "$O exists"; exit 1; }
mkdir -p $O
cp $F/gds/r1_ctrl_top.gds $F/lef/r1_ctrl_top.lef $F/nl/r1_ctrl_top.nl.v $F/def/r1_ctrl_top.def $O/
for c in nom_typ_1p20V_25C nom_fast_1p32V_m40C nom_slow_1p08V_125C; do cp $F/sdf/$c/r1_ctrl_top__$c.sdf $O/; done
cp flow/r1_ctrl.sdc $O/r1_ctrl_signoff.sdc
cp $F/sdc/r1_ctrl_top.sdc $O/r1_ctrl_top_pnr.sdc
cp flow/librelane/pins_v07.cfg flow/librelane/pins_v07.json flow/librelane/pins_v07.md $O/
cp R1_REGISTER_MAP.md $O/R1_REGISTER_MAP_0.8.md
echo "run $LL; RTL concat sha256 $(cat $R/$LL/rtl/*.v | sha256sum | cut -d' ' -f1); RTL revision 0.8, ID 0x5208 (PLAN.md D22)" > $O/SOURCE.txt
echo "sign-off STA: $STA; gate-level simulation: $GL; pins: pins_v07 (128, same slots as 0.7)" >> $O/SOURCE.txt
(cd $O && sha256sum $(ls | grep -v SHA256SUMS) > SHA256SUMS)
cat $O/SHA256SUMS

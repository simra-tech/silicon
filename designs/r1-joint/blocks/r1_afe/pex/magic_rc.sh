#!/bin/sh
# Layout E8 (track T3l): development RC view with magic CC capacitance (kpex --magic, seconds) instead of kpex 2.5D (50-70 min):
# R networks from the kpex-deck LVS databases of an R-view run (run_pexr.sh), capacitance from magic on the same flat
# channel and top layouts, converted to the Cext format that pex_rc_build.py reads. For screening (DM1 phase margin, C
# balance) only; never the record. Calibrated on layout-e7-dev17 (README "Layout E8").
# usage (host, repo root): G1_RESULTS_ROOT=<bulk>; export G1_RESULTS_ROOT; sh designs/r1-joint/blocks/r1_afe/pex/magic_rc.sh <layout run id> <pexr run id>
set -u
LR=$1; PR=$2
cd "$(dirname "$0")/../../../../.."
: "${G1_RESULTS_ROOT:?set G1_RESULTS_ROOT}"; G1_CPUSET=${G1_CPUSET:-108}; G1_WORKDIR=designs/r1-joint/blocks/r1_afe
export G1_RESULTS_ROOT G1_CPUSET G1_WORKDIR
B=$G1_RESULTS_ROOT/r1_afe; D=$B/$PR
for c in ch top; do
  if [ $c = ch ]; then G=$D/r1_afe_ch_flat.gds; CELL=r1_afe_ch; KD=r1_afe_ch_flat__r1_afe_ch; LV=$D/lvs_ch/$KD/r1_afe_ch.lvsdb.gz; OUTN=r1_afe_ch_k25d_pex_netlist.spice
  else G=$D/r1_afe_top_flat.gds; CELL=r1_afe; KD=r1_afe_top_flat__r1_afe; LV=$D/lvs_top/$KD/r1_afe.lvsdb.gz; OUTN=r1_afe_k25d_pex_netlist.spice; fi
  [ -s $D/magic_$c/$KD/magic_CC/$CELL.pex.spice ] || flow/run.sh kpex --pdk ihp-sg13g2 --threads 1 --gds $G --schematic layout/r1_afe_lvs.cdl --cell $CELL --magic --magic_mode CC --out_dir $D/magic_$c > $D/magic_${c}_console.log 2>&1
  mkdir -p $D/mrc_$c
  cp $LV $D/mrc_$c/
  python3 - $D/magic_$c/$KD/magic_CC/$CELL.pex.spice $D/mrc_$c/$OUTN <<'PY'
import re, sys
n = 0
with open(sys.argv[2], 'w') as o:
    o.write('* magic CC capacitance in kpex Cext format (pex/magic_rc.sh)\n')
    for ln in open(sys.argv[1]):
        t = ln.split()
        if len(t) >= 4 and re.match(r'^C\d', t[0]):
            n += 1; o.write('Cext_%d %s %s %s\n' % (n, t[1], t[2], t[3]))
print(sys.argv[2], n, 'caps')
PY
done
flow/run.sh klayout -b -r pex/pex_rc_build.py -rd kchdir=$D/mrc_ch -rd ktopdir=$D/mrc_top -rd ports=$B/$LR/r1_afe_ports.json -rd out=$B/pexmrc-$LR > $D/mrc_build.log 2>&1; echo "mrc build $?" >> $D/pexr.log

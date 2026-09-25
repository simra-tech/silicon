#!/bin/sh
# Netlist every readable sheet with xschem and compare it with its reference netlist.
# Run inside the pinned container from the repository root, with a results directory:
#   G1_RESULTS_ROOT=<dir> flow/run.sh sh designs/g1-guardian/review/schematics-readability-20260925/run_proof.sh <dir>
# Writes <dir>/<group>/<cell>.spice, <cell>.equiv.json and <dir>/summary.txt; touches nothing in the repository.
set -u
OUT=$1
B=/work/designs/g1-guardian/blocks
R=/work/designs/g1-guardian/review/schematics-readability-20260925
PDKRC=/foss/pdks/ihp-sg13g2/libs.tech/xschem/xschemrc
mkdir -p "$OUT"; : > "$OUT/summary.txt"
nl() {  # nl <group> <sheet dir> <rc: pdk|local> <cell>
  mkdir -p "$OUT/$1"
  if [ "$3" = local ]; then rc=xschemrc; else rc=$PDKRC; fi
  (cd "$2" && xschem -n -q -x --rcfile "$rc" -o "$OUT/$1" "$4.sch" > "$OUT/$1/$4.log" 2>&1)
  sed -i -e 's/^\*+ /+ /' -e 's/^\*\*\.subckt/.subckt/' -e 's/^\*\*\.ends/.ends/' -e '/^\.end$/d' "$OUT/$1/$4.spice"
}
chk() {  # chk <group> <cell> <reference netlist> [top]
  python3 $R/check_equivalence.py "$3" "$OUT/$1/$2.spice" "${4:-$2}" --json "$OUT/$1/$2.equiv.json" | sed "s|^|$1 |" >> "$OUT/summary.txt"
}
G=$B/g1_gate/schematic
for c in g1_lv_inv g1_lv_nand2 g1_hv_inv g1_hv_nor2 g1_lvlup g1_lvldn g1_gate; do nl gate $G pdk $c; done
for c in g1_lv_inv g1_lv_nand2 g1_hv_inv g1_hv_nor2 g1_gate; do chk gate $c $B/g1_gate/sim/netlist/g1_gate.spice; done
chk gate g1_lvlup $B/g1_gate/sim/netlist/g1_lvlup.spice; chk gate g1_lvldn $B/g1_gate/sim/netlist/g1_lvldn.spice
nl ls $B/g1_ctrl/ls/xschem pdk g1_ls_up; chk ls g1_ls_up $B/g1_ctrl/ls/sim/netlist/g1_ls_up.spice
G=$B/g1_osc/schematic
for c in g1_osc_inv g1_osc_nor2 g1_osc_nor3 g1_osc_nand2 g1_osc_cmp g1_osc_cbank g1_osc; do nl osc $G pdk $c; done
for c in g1_osc_inv g1_osc_nor2 g1_osc_nor3 g1_osc_nand2 g1_osc_cbank g1_osc; do chk osc $c $B/g1_osc/sim/netlist/g1_osc.spice; done
chk osc g1_osc_cmp $B/g1_osc/sim/netlist/g1_osc_cmp.spice
# the 117 um baseline behind G1_OSC_VARIANT=baseline, generated into the results directory
mkdir -p "$OUT/osc_baseline_sheets"
(cd "$OUT/osc_baseline_sheets" && G1_OSC_VARIANT=baseline python3 $B/g1_osc/schematic/gen_osc.py > /dev/null)
nl osc_baseline "$OUT/osc_baseline_sheets" pdk g1_osc; chk osc_baseline g1_osc $B/g1_osc/sim/netlist/g1_osc.spice
for c in g1_ota g1_sense; do nl sense $B/g1_sense/schematic pdk $c; chk sense $c $B/g1_sense/sim/netlist/$c.spice; done
nl sense_c45 $B/g1_sense/xschem/comp45_r100 pdk g1_sense
chk sense_c45 g1_sense $B/g1_sense/reports/rz100-partial-field-evidence-20260923-r1/sense-comp45-rz100-actual-source-20260923-r1/candidate.spice
G=$B/g1_trip/schematic
for c in g1_trip g1_tg; do nl trip $G pdk $c; done
chk trip g1_trip $B/g1_trip/sim/qualification/joint586-softinputpair4-nf4-roomcal-s73133-20260924-r1/trip.spice
G=$B/g1_trip/schematic/historical_12u034
for c in g1_inv g1_tg g1_thv_inv g1_tlvlup g1_cmp g1_cond g1_dac8 g1_trip; do nl trip_hist $G pdk $c; done
for c in g1_inv g1_trip; do chk trip_hist $c $B/g1_trip/sim/netlist/g1_trip.spice; done
chk trip_hist g1_thv_inv $B/g1_trip/sim/netlist/g1_tlvlup.spice
for c in g1_tlvlup g1_cmp g1_cond g1_dac8; do chk trip_hist $c $B/g1_trip/sim/netlist/$c.spice; done
chk trip g1_tg "$OUT/trip_hist/g1_tg.spice"
for c in g1_t2f g1_ref_sensor; do nl t2f $B/g1_t2f/xschem local $c; done
chk t2f g1_t2f $B/g1_t2f/xschem/g1_t2f.spice
nl bgr586 $B/g1_bgr/xschem/bgr586 pdk g1_bgr
chk bgr586 g1_bgr $B/g1_bgr/sim/qualification/candidates/bgr_loop24_qref4_r253p465_hv06/bgr_loop24_qref4_r253p465_hv06.spice
nl chip $B/g1_top/xschem/chip_interconnect pdk g1_chip_top
python3 $R/compare_chip_subset.py $B/g1_padring/netlist/g1_chip_top_1414_r2.cdl "$OUT/chip/g1_chip_top.spice" --json "$OUT/chip/compare.json" | sed "s|^|chip_r2 |" >> "$OUT/summary.txt"
python3 $R/compare_chip_subset.py $B/g1_padring/netlist/g1_chip_top_1414.cdl "$OUT/chip/g1_chip_top.spice" --json "$OUT/chip/compare_r1.json" | sed "s|^|chip_r1 |" >> "$OUT/summary.txt"
cat "$OUT/summary.txt"

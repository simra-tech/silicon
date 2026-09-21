#!/usr/bin/env bash
# Derive an ngspice netlist from an LVS-extracted netlist:  make_sim_netlist.sh <variant>
#   variant = pair  : reports/lvs_pair/g1_dose_extracted.cir    -> g1_dose_pair_extracted.cir       (ELT + LV)
#   variant = pcell : reports/lvs_pcell/g1_dose_pcell_extracted.cir -> g1_dose_pair_pcell_extracted.cir (HV + LV)
#   variant = nw    : reports/lvs_nw/g1_dose_nw_extracted.cir   -> g1_dose_pair_nw_extracted.cir    (narrow + wide LV)
# Edits: KLayout device names M$<n> -> XM<n> ("$" is a comment character for ngspice; the PDK MOS
# models are subcircuits, so the instance needs the X prefix), and MOS pins re-ordered from KLayout's
# S G D B (custom_writer.lvs, terminal_definitions order) to SPICE D G S B. AD is the drain junction.
set -e
cd "$(dirname "$0")"
v=${1:-pair}
case $v in
  pair)  src=../reports/lvs_pair/g1_dose_extracted.cir ;;
  pcell) src=../reports/lvs_pcell/g1_dose_pcell_extracted.cir ;;
  nw)    src=../reports/lvs_nw/g1_dose_nw_extracted.cir ;;
  *) echo "unknown variant $v"; exit 1 ;;
esac
out=g1_dose_pair_${v}_extracted.cir; [ "$v" = pair ] && out=g1_dose_pair_extracted.cir
{
  echo "* Derived from $src by make_sim_netlist.sh (device names and pin order edited for ngspice, see script)"
  sed -E 's/^M\$([0-9]+) ([A-Za-z0-9_]+) ([A-Za-z0-9_]+) ([A-Za-z0-9_]+) ([A-Za-z0-9_]+) /XM\1 \4 \3 \2 \5 /' "$src"
} > "$out"
grep -n "^XM" "$out"

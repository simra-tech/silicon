#!/usr/bin/env bash
# usage (container, workdir designs/g1-guardian/blocks/g1_gate/sim): run_dvdt.sh <mos> <temp> <tr> <vbus> <Lg> <Rg> <outdir>
set -eu
SUF=""; if [ "${NODCN:-0}" = 1 ]; then SUF=_nodcn; fi
if [ "${SHORT:-0}" = 1 ]; then SUF="${SUF}_gsshort"; fi
MOS=$1; T=$2; TR=$3; VB=$4; LG=$5; RG=$6; OUT=$7
tag="dvdt_${MOS}_${T}C_tr${TR}_v${VB}_L${LG}_R${RG}${SUF}"
sed -e "s/@@MOS@@/$MOS/g" -e "s/@@TEMP@@/$T/" -e "s/@@TR@@/$TR/g" -e "s/@@VBUS@@/$VB/g" -e "s/@@LG@@/$LG/g" -e "s/@@RG@@/$RG/g" -e "s/@@TAG@@/$tag/" \
  "$(dirname "$0")/tb_gate_dvdt.cir.tmpl" > "$OUT/$tag.cir"
if [ "${NODCN:-0}" = 1 ]; then sed -i -e "s#^.include /foss/pdks/ihp-sg13g2/libs.ref/sg13g2_io/spice/sg13g2_io.spi#.include ${G1_RESULTS_ROOT}/redteam-20260927/trip_path/net/sg13g2_io_nodcn.spi#" -e "s/ sg13g2_IOPad/ g1nd_sg13g2_IOPad/" "$OUT/$tag.cir"; fi
# SHORT=1: reference run with the FET gate tied to its source (1 mOhm): displacement (Coss) current only
if [ "${SHORT:-0}" = 1 ]; then sed -i -e "s/^Rpulldown gfet fsrc 10k/Rpulldown gfet fsrc 1m/" "$OUT/$tag.cir"; fi
ngspice -b "$OUT/$tag.cir" > "$OUT/$tag.log" 2>&1 || true
grep -E "^DVDT|Timestep too small|rror" "$OUT/$tag.log" | head -3

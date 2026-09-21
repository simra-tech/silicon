#!/usr/bin/env bash
# Run from this directory inside the pinned container (flow/run.sh).
set -e
cd "$(dirname "$0")/decks"
mkdir -p ../logs
ngspice -v | head -3 > ../logs/ngspice_banner.txt
cat /foss/pdks/ihp-sg13g2/COMMIT > ../logs/pdk_commit.txt
ngspice -b mos_tt_Tm40C_off.cir > ../logs/mos_tt_Tm40C_off.log 2>&1
ngspice -b mos_tt_Tp27C_off.cir > ../logs/mos_tt_Tp27C_off.log 2>&1
ngspice -b mos_tt_Tp85C_off.cir > ../logs/mos_tt_Tp85C_off.log 2>&1
ngspice -b mos_tt_Tp125C_off.cir > ../logs/mos_tt_Tp125C_off.log 2>&1
ngspice -b mos_tt_Tp150C_off.cir > ../logs/mos_tt_Tp150C_off.log 2>&1
ngspice -b mos_tt_Tp175C_off.cir > ../logs/mos_tt_Tp175C_off.log 2>&1
ngspice -b mos_tt_Tm196C_off.cir > ../logs/mos_tt_Tm196C_off.log 2>&1
ngspice -b mos_ss_Tm40C_off.cir > ../logs/mos_ss_Tm40C_off.log 2>&1
ngspice -b mos_ss_Tp27C_off.cir > ../logs/mos_ss_Tp27C_off.log 2>&1
ngspice -b mos_ss_Tp85C_off.cir > ../logs/mos_ss_Tp85C_off.log 2>&1
ngspice -b mos_ss_Tp125C_off.cir > ../logs/mos_ss_Tp125C_off.log 2>&1
ngspice -b mos_ss_Tp150C_off.cir > ../logs/mos_ss_Tp150C_off.log 2>&1
ngspice -b mos_ss_Tp175C_off.cir > ../logs/mos_ss_Tp175C_off.log 2>&1
ngspice -b mos_ss_Tm196C_off.cir > ../logs/mos_ss_Tm196C_off.log 2>&1
ngspice -b mos_ff_Tm40C_off.cir > ../logs/mos_ff_Tm40C_off.log 2>&1
ngspice -b mos_ff_Tp27C_off.cir > ../logs/mos_ff_Tp27C_off.log 2>&1
ngspice -b mos_ff_Tp85C_off.cir > ../logs/mos_ff_Tp85C_off.log 2>&1
ngspice -b mos_ff_Tp125C_off.cir > ../logs/mos_ff_Tp125C_off.log 2>&1
ngspice -b mos_ff_Tp150C_off.cir > ../logs/mos_ff_Tp150C_off.log 2>&1
ngspice -b mos_ff_Tp175C_off.cir > ../logs/mos_ff_Tp175C_off.log 2>&1
ngspice -b mos_ff_Tm196C_off.cir > ../logs/mos_ff_Tm196C_off.log 2>&1

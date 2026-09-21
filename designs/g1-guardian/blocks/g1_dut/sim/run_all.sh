#!/usr/bin/env bash
# Run from this directory inside the pinned container (flow/run.sh).
set -e
cd "$(dirname "$0")/decks"
mkdir -p ../logs
ngspice -v | head -3 > ../logs/ngspice_banner.txt
cat /foss/pdks/ihp-sg13g2/COMMIT > ../logs/pdk_commit.txt
ngspice -b hbt_typ_Tm40C_gummel.cir > ../logs/hbt_typ_Tm40C_gummel.log 2>&1
ngspice -b hbt_typ_Tm40C_output.cir > ../logs/hbt_typ_Tm40C_output.log 2>&1
ngspice -b hbt_typ_Tp27C_gummel.cir > ../logs/hbt_typ_Tp27C_gummel.log 2>&1
ngspice -b hbt_typ_Tp27C_output.cir > ../logs/hbt_typ_Tp27C_output.log 2>&1
ngspice -b hbt_typ_Tp85C_gummel.cir > ../logs/hbt_typ_Tp85C_gummel.log 2>&1
ngspice -b hbt_typ_Tp85C_output.cir > ../logs/hbt_typ_Tp85C_output.log 2>&1
ngspice -b hbt_typ_Tp125C_gummel.cir > ../logs/hbt_typ_Tp125C_gummel.log 2>&1
ngspice -b hbt_typ_Tp125C_output.cir > ../logs/hbt_typ_Tp125C_output.log 2>&1
ngspice -b hbt_typ_Tp150C_gummel.cir > ../logs/hbt_typ_Tp150C_gummel.log 2>&1
ngspice -b hbt_typ_Tp150C_output.cir > ../logs/hbt_typ_Tp150C_output.log 2>&1
ngspice -b hbt_typ_Tp175C_gummel.cir > ../logs/hbt_typ_Tp175C_gummel.log 2>&1
ngspice -b hbt_typ_Tp175C_output.cir > ../logs/hbt_typ_Tp175C_output.log 2>&1
ngspice -b hbt_typ_Tm196C_gummel.cir > ../logs/hbt_typ_Tm196C_gummel.log 2>&1
ngspice -b hbt_typ_Tm196C_output.cir > ../logs/hbt_typ_Tm196C_output.log 2>&1
ngspice -b hbt_bcs_Tm40C_gummel.cir > ../logs/hbt_bcs_Tm40C_gummel.log 2>&1
ngspice -b hbt_bcs_Tm40C_output.cir > ../logs/hbt_bcs_Tm40C_output.log 2>&1
ngspice -b hbt_bcs_Tp27C_gummel.cir > ../logs/hbt_bcs_Tp27C_gummel.log 2>&1
ngspice -b hbt_bcs_Tp27C_output.cir > ../logs/hbt_bcs_Tp27C_output.log 2>&1
ngspice -b hbt_bcs_Tp85C_gummel.cir > ../logs/hbt_bcs_Tp85C_gummel.log 2>&1
ngspice -b hbt_bcs_Tp85C_output.cir > ../logs/hbt_bcs_Tp85C_output.log 2>&1
ngspice -b hbt_bcs_Tp125C_gummel.cir > ../logs/hbt_bcs_Tp125C_gummel.log 2>&1
ngspice -b hbt_bcs_Tp125C_output.cir > ../logs/hbt_bcs_Tp125C_output.log 2>&1
ngspice -b hbt_bcs_Tp150C_gummel.cir > ../logs/hbt_bcs_Tp150C_gummel.log 2>&1
ngspice -b hbt_bcs_Tp150C_output.cir > ../logs/hbt_bcs_Tp150C_output.log 2>&1
ngspice -b hbt_bcs_Tp175C_gummel.cir > ../logs/hbt_bcs_Tp175C_gummel.log 2>&1
ngspice -b hbt_bcs_Tp175C_output.cir > ../logs/hbt_bcs_Tp175C_output.log 2>&1
ngspice -b hbt_bcs_Tm196C_gummel.cir > ../logs/hbt_bcs_Tm196C_gummel.log 2>&1
ngspice -b hbt_bcs_Tm196C_output.cir > ../logs/hbt_bcs_Tm196C_output.log 2>&1
ngspice -b hbt_wcs_Tm40C_gummel.cir > ../logs/hbt_wcs_Tm40C_gummel.log 2>&1
ngspice -b hbt_wcs_Tm40C_output.cir > ../logs/hbt_wcs_Tm40C_output.log 2>&1
ngspice -b hbt_wcs_Tp27C_gummel.cir > ../logs/hbt_wcs_Tp27C_gummel.log 2>&1
ngspice -b hbt_wcs_Tp27C_output.cir > ../logs/hbt_wcs_Tp27C_output.log 2>&1
ngspice -b hbt_wcs_Tp85C_gummel.cir > ../logs/hbt_wcs_Tp85C_gummel.log 2>&1
ngspice -b hbt_wcs_Tp85C_output.cir > ../logs/hbt_wcs_Tp85C_output.log 2>&1
ngspice -b hbt_wcs_Tp125C_gummel.cir > ../logs/hbt_wcs_Tp125C_gummel.log 2>&1
ngspice -b hbt_wcs_Tp125C_output.cir > ../logs/hbt_wcs_Tp125C_output.log 2>&1
ngspice -b hbt_wcs_Tp150C_gummel.cir > ../logs/hbt_wcs_Tp150C_gummel.log 2>&1
ngspice -b hbt_wcs_Tp150C_output.cir > ../logs/hbt_wcs_Tp150C_output.log 2>&1
ngspice -b hbt_wcs_Tp175C_gummel.cir > ../logs/hbt_wcs_Tp175C_gummel.log 2>&1
ngspice -b hbt_wcs_Tp175C_output.cir > ../logs/hbt_wcs_Tp175C_output.log 2>&1
ngspice -b hbt_wcs_Tm196C_gummel.cir > ../logs/hbt_wcs_Tm196C_gummel.log 2>&1
ngspice -b hbt_wcs_Tm196C_output.cir > ../logs/hbt_wcs_Tm196C_output.log 2>&1

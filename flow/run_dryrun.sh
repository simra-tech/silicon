#!/usr/bin/env bash
# G1 integration dry run: LibreLane Chip flow on
# designs/g1-guardian/blocks/g1_padring/flow/config_dryrun.yaml with the analog
# supply straps applied between PDN generation and the following step.
#   flow/run_dryrun.sh [--to <step>]        tag "dryrun-1350" (override with G1_RUN_TAG)
# Sequence (all inside the pinned container through flow/run.sh):
#   1. librelane ... --to OpenROAD.GeneratePDN
#   2. LibreLane's own OpenROAD (/foss/tools/openroad-librelane, the one that
#      wrote the ODB; the container's other openroad writes a newer schema)
#      runs flow/analog_straps.tcl on the GeneratePDN step's ODB (via stacks
#      from the chip stripes onto the analog macros' Metal3 bars, jogs for the
#      shifters and stubs, check_power_grid); the ODB/DEF are rewritten in place
#   3. librelane ... --from Odb.RemovePDNObstructions [--to <step>]
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BLOCK="designs/g1-guardian/blocks/g1_padring"
TAG="${G1_RUN_TAG:-assembly-1350}"
LL="librelane flow/config_dryrun.yaml --pdk ihp-sg13g2 --pdk-root /foss/pdks --manual-pdk --run-tag $TAG"
flow_failed=0

echo "[run_dryrun] 1/3 flow to OpenROAD.GeneratePDN"
G1_WORKDIR="$BLOCK" "$HERE/run.sh" $LL --overwrite --to OpenROAD.GeneratePDN || flow_failed=1
STEP=$(ls -d "$HERE/../$BLOCK/flow/runs/$TAG"/*-openroad-generatepdn | head -1)
[ -f "$STEP/g1_chip_top.odb" ] || { echo "[run_dryrun] GeneratePDN produced no ODB, see $STEP"; exit 1; }
STEP_REL="${STEP#$HERE/../}"

echo "[run_dryrun] 2/3 analog supply straps on $STEP_REL"
G1_WORKDIR="$BLOCK" "$HERE/run.sh" bash -c "
  export SCRIPTS_DIR=/usr/local/lib/python3.12/dist-packages/librelane/scripts
  export STEP_DIR=/work/$STEP_REL VDD_NETS='VDD' GND_NETS='VSS' PDN_VPITCH=75.6 PDN_VWIDTH=2.2 PDN_VOFFSET=13.6 PDN_HOFFSET=13.6
  cd /work/$STEP_REL && cp g1_chip_top.odb g1_chip_top.prestraps.odb &&
  /foss/tools/openroad-librelane/bin/openroad -exit -no_splash -log analog_straps.log /work/$BLOCK/flow/analog_straps_standalone.tcl" 
grep -h "analog_straps\|PSM-0040\|PSM-0069" "$STEP/analog_straps.log" | grep -v "PSM-003[89]"
# The step's recorded metric still holds pdngen's pre-strap count and would stop
# the flow at Checker.PowerGridViolations; replace it with the post-strap count
# (number of nets whose check_power_grid did not report PSM-0040).
python3 "$HERE/update_pdn_metrics.py" "$STEP"

echo "[run_dryrun] 3/3 flow from Odb.RemovePDNObstructions $*"
G1_WORKDIR="$BLOCK" "$HERE/run.sh" $LL --from Odb.RemovePDNObstructions "$@" || flow_failed=1

# ---- evidence: netlists of record ------------------------------------------
# Verilog (powered and plain) netlists from the flow, plus the chip CDL assembled
# from this run's powered netlist, the PDK stdcell/IO CDLs and the macro CDLs of
# record (flow/lvs/assemble_chip_cdl.py) -- the schematic side of the core-only LVS
RUN="$HERE/../$BLOCK/flow/runs/$TAG"
if [ -f "$RUN/final/pnl/g1_chip_top.pnl.v" ]; then
  mkdir -p "$HERE/../$BLOCK/netlist"
  cp "$RUN/final/pnl/g1_chip_top.pnl.v" "$HERE/../$BLOCK/netlist/g1_chip_top.pnl.v"
  cp "$RUN/final/nl/g1_chip_top.nl.v"   "$HERE/../$BLOCK/netlist/g1_chip_top.nl.v"
  echo "[run_dryrun] netlists copied to $BLOCK/netlist/"
  M=/work/designs/g1-guardian/blocks
  G1_WORKDIR="$BLOCK" "$HERE/run.sh" python3 /work/$BLOCK/flow/lvs/assemble_chip_cdl.py \
    /work/$BLOCK/netlist/g1_chip_top.pnl.v /work/$BLOCK/netlist/g1_chip_top.cdl \
    --lib /foss/pdks/ihp-sg13g2/libs.ref/sg13g2_stdcell/cdl/sg13g2_stdcell.cdl \
    --lib /foss/pdks/ihp-sg13g2/libs.ref/sg13g2_io/cdl/sg13g2_io.cdl \
    --macro g1_gate=$M/g1_gate/layout/g1_gate.cdl --macro g1_osc=$M/g1_osc/layout/g1_osc_lvs.cdl \
    --macro g1_sense=$M/g1_sense/layout/g1_sense.cdl --macro g1_t2f=$M/g1_t2f/layout/g1_t2f_lvs.cdl \
    --macro g1_trip=$M/g1_trip/layout/g1_trip_lvs.cdl --macro g1_bgr=$M/g1_bgr/schematic/g1_bgr_lvs.cdl \
    --macro g1_dose_macro=$M/g1_dose/schematic/g1_dose_macro.cdl --macro g1_dut_macro=$M/g1_dut/schematic/g1_dut_macro.cdl \
    --macro g1_ls_up=$M/g1_ctrl/ls/sim/netlist/g1_ls_up.cdl \
    --digital $M/g1_ctrl/layout/g1_digital.pnl.v \
    && echo "[run_dryrun] chip CDL assembled: $BLOCK/netlist/g1_chip_top.cdl" || flow_failed=1
fi
exit "$flow_failed"

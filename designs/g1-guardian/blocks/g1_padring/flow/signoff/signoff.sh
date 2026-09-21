#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# Sign-off of an assembly run beyond the flow's own steps, and evidence
# collection. Runs inside the pinned container (repo at /work):
#   flow/run.sh bash designs/g1-guardian/blocks/g1_padring/flow/signoff/signoff.sh <run tag>
# Writes designs/g1-guardian/blocks/g1_padring/reports/<run tag>/:
#   flow logs and reports (DRC, density, antenna, XOR, routing, connectivity, STA),
#   drc_recommended/ (all rules), drc_precheck/ (precheck_drc=true), density_detail/
#   (per-layer table, precheck), antenna_markers.txt, pdn_net_overlap.log,
#   pdn_macro_overlap.log, supply_isolation.log, core_lvs/ (core-only KLayout LVS),
#   metrics_summary.json, macro_placement.txt, final_gds.sha256
set -u
TAG=${1:-assembly-1350}
B=/work/designs/g1-guardian/blocks/g1_padring
R=$B/flow/runs/$TAG
D=$B/reports/$TAG
GDS=$R/final/gds/g1_chip_top.gds
DEF=$R/final/def/g1_chip_top.def
DRC=/foss/pdks/ihp-sg13g2/libs.tech/klayout/tech/drc
mkdir -p $D $D/drc_recommended $D/drc_precheck $D/density_detail $D/core_lvs
[ -f $GDS ] || { echo "no final GDS in $R"; exit 1; }
export KLAYOUT_PATH=/foss/pdks/ihp-sg13g2/libs.tech/klayout

cp_first() { local f; f=$(ls $1 2>/dev/null | head -1); [ -n "$f" ] && cp "$f" "$2"; }
echo "== flow evidence"
cp_first "$R/*-openroad-generatepdn/openroad-generatepdn.log" $D/openroad-generatepdn.log
cp_first "$R/*-openroad-generatepdn/analog_straps.log" $D/analog_straps.log
cp_first "$R/*-openroad-cutrows/openroad-cutrows.log" $D/openroad-cutrows.log
cp_first "$R/*-openroad-detailedrouting/openroad-detailedrouting.log" $D/openroad-detailedrouting.log
cp_first "$R/*-odb-reportdisconnectedpins/*.log" $D/odb-reportdisconnectedpins.log
cp_first "$R/*-odb-reportdisconnectedpins/full_disconnected_pins_table.txt" $D/full_disconnected_pins_table.txt
cp_first "$R/*-openroad-checkantennas-1/reports/antenna_summary.rpt" $D/antenna_summary.rpt
cp_first "$R/*-klayout-drc/klayout-drc.log" $D/klayout-drc.log
cp_first "$R/*-klayout-drc/reports/drc.klayout.json" $D/drc.klayout.json
cp_first "$R/*-klayout-drc/reports/drc.klayout.lyrdb" $D/drc.klayout.lyrdb
cp_first "$R/*-klayout-density/klayout-density.log" $D/klayout-density.log
cp_first "$R/*-klayout-density/reports/density.klayout.json" $D/density.klayout.json
cp_first "$R/*-klayout-density/reports/density.klayout.lyrdb" $D/density.klayout.lyrdb
cp_first "$R/*-klayout-antenna/reports/antenna.klayout.json" $D/antenna.klayout.json
cp_first "$R/*-klayout-antenna/reports/antenna.klayout.lyrdb" $D/antenna.klayout.lyrdb
cp_first "$R/*-klayout-xor/klayout-xor.log" $D/klayout-xor.log
cp_first "$R/*-openroad-stapostpnr/summary.rpt" $D/stapostpnr_summary.rpt
cp_first "$R/*-magic-drc/reports/drc.magic.rpt" $D/drc.magic.rpt
cp_first "$R/*-netgen-lvs/reports/lvs.netgen.rpt" $D/lvs.netgen.rpt
for c in nom_fast_1p32V_m40C nom_typ_1p20V_25C nom_slow_1p08V_125C; do
  f=$(ls $R/*-openroad-stapostpnr/$c/min.rpt 2>/dev/null | head -1)
  [ -n "$f" ] && { echo "# first 300 lines of min.rpt (worst hold paths first); the full $(grep -c '' $f)-line report stays in flow/runs/$TAG/*-openroad-stapostpnr/$c/min.rpt"; head -300 $f; } > $D/sta_${c}_min.rpt
done
cp $R/flow.log $R/warning.log $D/ 2>/dev/null; cp $R/error.log $D/ 2>/dev/null
cp $B/flow/pdn_cfg_g1.tcl $D/pdn_cfg_g1_used.tcl
cp $B/flow/config_dryrun.yaml $D/config_dryrun_used.yaml
cp $B/flow/macro_gds_assembly/prepare_macros.log $D/ 2>/dev/null
sha256sum $GDS | sed "s#$R/#flow/runs/$TAG/#" > $D/final_gds.sha256
python3 - "$R" "$D" <<'PY'
import json, sys, glob, re
R, D = sys.argv[1], sys.argv[2]
m = glob.glob(R + "/final/metrics.json") or sorted(glob.glob(R + "/*/state_out.json"))[-1:]
d = json.load(open(m[0])); d = d.get("metrics", d)
keys = [k for k in d if any(x in k for x in ["drc", "antenna", "density", "disconnected", "power_grid", "xor", "setup__ws", "hold__ws", "wirelength", "instance__count__macros", "instance__count__stdcell"])]
json.dump({k: d[k] for k in sorted(keys)}, open(D + "/metrics_summary.json", "w"), indent=1)
t = open(glob.glob(R + "/*-openroad-generatepdn/g1_chip_top.def")[0]).read()
rows = [f"{a:18s} {b:14s} x={int(x)/1000:8.3f} y={int(y)/1000:8.3f} {o}" for a, b, x, y, o in re.findall(r"-\s+(i_core\.u_\w+)\s+(g1_\w+)\s*\+\s*FIXED\s*\(\s*(-?\d+)\s+(-?\d+)\s*\)\s*(\w+)", t)]
open(D + "/macro_placement.txt", "w").write("# FIXED macro placements (um)\n" + "\n".join(rows) + "\n")
print({k: d[k] for k in sorted(keys) if "corner" not in k})
PY

echo "== antenna markers (KLayout deck)"
python3 - $D/antenna.klayout.lyrdb <<'PY' > $D/antenna_markers.txt
import re, sys
t = open(sys.argv[1]).read()
rows = {}
for it in re.findall(r"<item>(.*?)</item>", t, re.S):
    c = re.search(r"<category>(.*?)</category>", it).group(1).strip("'")
    cell = re.search(r"<cell>(.*?)</cell>", it); cell = cell.group(1) if cell else "?"
    v = re.findall(r"<value>(.*?)</value>", it, re.S)
    m = re.search(r"polygon: \(([\d.]+),([\d.]+)", v[0])
    key = (cell, m.group(1), m.group(2)) if m else (cell, "?", "?")
    d = rows.setdefault(key, {"cats": set(), "vals": {}}); d["cats"].add(c)
    for x in v[1:]:
        mm = re.match(r"\[#(\w+)\] float: ([\d.]+)", x)
        if mm: d["vals"][mm.group(1)] = float(mm.group(2))
print(f"# {len(re.findall('<item>', t))} markers, {len(rows)} gates")
for k in sorted(rows):
    v = rows[k]["vals"]
    print(k, sorted(rows[k]["cats"]), "diode=%s" % v.get("has_diode"), "tm2_ratio=%.0f" % v.get("tm2_ratio", 0), "sum_m1_tm2=%.0f" % v.get("sum_m1_tm2", 0))
PY
head -1 $D/antenna_markers.txt

echo "== DRC recommended (no_recommended=false)"
klayout -b -zz -r $DRC/ihp-sg13g2.drc -rd input=$GDS -rd topcell=g1_chip_top -rd report=$D/drc_recommended/drc_recommended.lyrdb -rd run_mode=deep -rd threads=8 > $D/drc_recommended/drc_recommended.log 2>&1
echo "markers: $(grep -c '<item>' $D/drc_recommended/drc_recommended.lyrdb)"; grep -o "<category>'[^']*'</category>" $D/drc_recommended/drc_recommended.lyrdb | sort | uniq -c
echo "== DRC precheck (precheck_drc=true, no_recommended=true)"
klayout -b -zz -r $DRC/ihp-sg13g2.drc -rd input=$GDS -rd topcell=g1_chip_top -rd report=$D/drc_precheck/drc_precheck.lyrdb -rd run_mode=deep -rd no_recommended=true -rd precheck_drc=true -rd threads=8 > $D/drc_precheck/drc_precheck.log 2>&1
echo "markers: $(grep -c '<item>' $D/drc_precheck/drc_precheck.lyrdb)"
echo "== density (default and precheck) with the per-layer table"
klayout -b -zz -r $DRC/rule_decks/density.drc -rd input=$GDS -rd topcell=g1_chip_top -rd report=$D/density_detail/density.lyrdb -rd threads=8 > $D/density_detail/density.log 2>&1
klayout -b -zz -r $DRC/rule_decks/density.drc -rd input=$GDS -rd topcell=g1_chip_top -rd report=$D/density_detail/density_precheck.lyrdb -rd precheck_drc=true -rd threads=8 > $D/density_detail/density_precheck.log 2>&1
echo "markers: $(grep -c '<item>' $D/density_detail/density.lyrdb) / precheck $(grep -c '<item>' $D/density_detail/density_precheck.lyrdb)"
grep -h "Using prBoundary\|Using EdgeSeal\|No prBoundary\|Density % =" $D/density_detail/density.log | sed 's/^.*: //'

echo "== supply nets: same-layer overlaps between different nets"
klayout -b -rd gds=$GDS -rd defp=$DEF -r $B/flow/lvs/pdn_net_overlap.py 2>&1 | grep -v "Warning: Ignoring" > $D/pdn_net_overlap.log; tail -1 $D/pdn_net_overlap.log
echo "== supply shapes on macro / IO-cell metal outside their pins"
LEFS=$B/../g1_ctrl/layout/g1_digital.lef,$B/../g1_bgr/layout/g1_bgr.lef,$B/../g1_sense/layout/g1_sense.lef,$B/../g1_trip/layout/g1_trip.lef,$B/../g1_gate/layout/g1_gate.lef,$B/../g1_t2f/layout/g1_t2f.lef,$B/../g1_osc/layout/g1_osc.lef,$B/../g1_ctrl/ls/layout/g1_ls_up.lef,$B/../g1_dose/layout/g1_dose_macro.lef,$B/../g1_dut/layout/g1_dut_macro.lef,$B/ip/sg13g2_io_padbare/lef/sg13g2_io.lef
klayout -b -rd gds=$GDS -rd defp=$DEF -rd lefs=$LEFS -r $B/flow/lvs/pdn_macro_overlap.py 2>&1 | grep -v "Warning: Ignoring" > $D/pdn_macro_overlap.log; tail -1 $D/pdn_macro_overlap.log
echo "== supply isolation (metal-only connectivity of the whole chip)"
klayout -b -rd gds=$GDS -r $B/flow/lvs/supply_isolation.py 2>&1 | grep -v "Warning: Ignoring" > $D/supply_isolation.log; tail -1 $D/supply_isolation.log

echo "== core-only KLayout LVS"
bash $B/flow/lvs/run_core_lvs.sh $R /work/build/scratch/corelvs > $D/core_lvs/run_core_lvs.log 2>&1
cp /work/build/scratch/corelvs/core_cdl.log /work/build/scratch/corelvs/core_only_gds.log $D/core_lvs/ 2>/dev/null
cp /work/build/scratch/corelvs/lvs/g1_core.log $D/core_lvs/ 2>/dev/null; cp /work/build/scratch/corelvs/lvs/lvs_run_*.log $D/core_lvs/ 2>/dev/null
klayout -b -rd db=/work/build/scratch/corelvs/lvs/g1_core.lvsdb -r $B/flow/lvs/xref_summary.py 2>&1 | grep -v "Warning: Ignoring" > $D/core_lvs/xref.txt
grep -h "Netlists\|Congratulations\|Total Run time" $D/core_lvs/g1_core.log; tail -1 $D/core_lvs/xref.txt
echo "== done: $D"

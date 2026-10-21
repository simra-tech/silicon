#!/bin/sh
# DRC (PDK sg13g2 deck, deep, no density: block level), antenna (PDK deck) and LVS (PDK deck, deep,
# --no_series_res) of r1_afe.gds against r1_afe_lvs.cdl (revision E, unit split by r1_afe_netlist.py).
# Usage (repo root, host):
#   G1_CPUSET=106-108; export G1_CPUSET; G1_RESULTS_ROOT=<bulk root>; export G1_RESULTS_ROOT
#   G1_WORKDIR=designs/r1-joint/blocks/r1_afe/layout; export G1_WORKDIR; flow/run.sh sh run_checks.sh <run-id> [drc|ant|lvs|all]
# Outputs: $G1_RESULTS_ROOT/r1_afe/<run-id>/{drc,antenna,lvs}; logs, the LVS summary and run.json in ../reports/<run-id>/
set -eu
RID=$1; WHAT=${2:-all}
OUTD=$G1_RESULTS_ROOT/r1_afe/$RID
REP=../reports/$RID
mkdir -p $OUTD $REP
T=/foss/pdks/ihp-sg13g2/libs.tech/klayout/tech
GDS=$(pwd)/r1_afe.gds
if [ "$WHAT" = all ] || [ "$WHAT" = drc ]; then
  python3 $T/drc/run_drc.py --path=$GDS --topcell=r1_afe --run_mode=deep --no_density --run_dir=$OUTD/drc > $OUTD/drc.log 2>&1 || true
  cp $OUTD/drc.log $REP/drc.log
fi
if [ "$WHAT" = all ] || [ "$WHAT" = ant ]; then
  python3 $T/drc/run_drc.py --path=$GDS --topcell=r1_afe --run_mode=deep --antenna_only --run_dir=$OUTD/antenna > $OUTD/antenna.log 2>&1 || true
  cp $OUTD/antenna.log $REP/antenna.log
fi
if [ "$WHAT" = all ] || [ "$WHAT" = lvs ]; then
  python3 $T/lvs/run_lvs.py --layout=$GDS --netlist=$(pwd)/r1_afe_lvs.cdl --topcell=r1_afe --run_mode=deep \
     --no_series_res --run_dir=$OUTD/lvs > $OUTD/lvs.log 2>&1 || true
  cp $OUTD/lvs.log $REP/lvs.log
  klayout -b -r tools/lvsdb_report.py -rd db=$OUTD/lvs/r1_afe.lvsdb > $REP/lvs_summary.txt 2>&1 || true
fi
# public repository: no machine paths in the copied logs
for f in $REP/*.log $REP/*.txt; do
  [ -f "$f" ] && sed -i -e "s#$G1_RESULTS_ROOT#<G1_RESULTS_ROOT>#g" -e "s#/work/#<repo>/#g" "$f"
done
python3 - "$RID" "$WHAT" "$OUTD" "$REP" <<'PY'
import hashlib, json, os, re, subprocess, sys, time
rid, what, outd, rep = sys.argv[1:5]
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
root = os.environ['G1_RESULTS_ROOT']
def grab(p, pat):
    try:
        return [l.strip() for l in open(p, errors='replace') if re.search(pat, l)]
    except OSError:
        return ['not run']
kv = subprocess.check_output(['klayout', '-v']).decode().strip()
j = dict(run_id=rid, what=what, date_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
         command='G1_CPUSET=106-108; G1_RESULTS_ROOT=<bulk>; G1_WORKDIR=designs/r1-joint/blocks/r1_afe/layout; '
                 'flow/run.sh sh run_checks.sh %s %s' % (rid, what),
         tools=dict(klayout=kv, image_id='sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2',
                    pdk_commit=open('/foss/pdks/ihp-sg13g2/COMMIT').read().strip()),
         inputs={'layout/r1_afe.gds': sha('r1_afe.gds'), 'layout/r1_afe_lvs.cdl': sha('r1_afe_lvs.cdl'),
                 'schematic/r1_afe.spice': sha('../schematic/r1_afe.spice'),
                 'layout/r1_afe_layout.py': sha('r1_afe_layout.py'), 'layout/r1_afe_netlist.py': sha('r1_afe_netlist.py'),
                 'layout/maze_router.py': sha('maze_router.py')},
         drc=grab(os.path.join(rep, 'drc.log'), r'Number of DRC errors|DRC Check'),
         antenna=grab(os.path.join(rep, 'antenna.log'), r'(?i)error|violation|completed'),
         lvs=grab(os.path.join(rep, 'lvs.log'), r'(?i)netlists match|don.t match|LVS'),
         raw='$G1_RESULTS_ROOT/' + os.path.relpath(outd, root) + '/')
json.dump(j, open(os.path.join(rep, 'run.json'), 'w'), indent=1)
print(json.dumps(dict(drc=j['drc'], antenna=j['antenna'][-3:], lvs=j['lvs'][-3:]), indent=1))
PY

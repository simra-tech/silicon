#!/bin/sh
# LVS of r1_adc layout B5 (analog part + r1_adc_sar standard-cell sub-macro) against layout/r1_adc_lvs_b5.cdl.
# Run from the repository root (POSIX sh):
#   G1_CPUSET=103; export G1_CPUSET; G1_RESULTS_ROOT=<G1_RESULTS_ROOT>; export G1_RESULTS_ROOT
#   sh designs/r1-joint/blocks/r1_adc/layout/b5/run_lvs_b5.sh <run-id> <gds> stock|limits
# limits: run-time copy of the PDK LVS directory with two comparer search limits after "align" (max_depth(8),
# max_branch_complexity(100)), the method of blocks/r1_safe/layout/run_checks.sh (SAR INTEGRATION.md 5). No extraction
# or rule line is changed. Outputs: $G1_RESULTS_ROOT/r1_adc/<run-id>/; log copy and summary in reports/<run-id>/.
set -eu
RID=$1; G=$2; MODE=$3
# optional 4th argument (T2o, layout B9): the reference CDL, repository-relative (default the B5 CDL)
CDL=${4:-designs/r1-joint/blocks/r1_adc/layout/r1_adc_lvs_b5.cdl}
B=designs/r1-joint/blocks/r1_adc
X=$G1_RESULTS_ROOT/r1_adc/$RID
REP=$B/reports/$RID
test ! -e "$X" || { echo "run dir exists: $X"; exit 1; }
mkdir -p "$X" "$REP"
PDKD=/foss/pdks/ihp-sg13g2/libs.tech/klayout/tech
if [ "$MODE" = limits ]; then
  mkdir -p "$X/deck/p/libs.tech/klayout/tech"
  flow/run.sh sh -c "cp -r $PDKD/lvs $X/deck/p/libs.tech/klayout/tech/ && cp /foss/pdks/versions.txt $X/deck/"
  sed -i 's/^  align$/  align\n  max_depth(8)\n  max_branch_complexity(100)/' "$X/deck/p/libs.tech/klayout/tech/lvs/sg13g2.lvs"
  grep -n "max_depth\|max_branch" "$X/deck/p/libs.tech/klayout/tech/lvs/sg13g2.lvs" > "$X/deck_diff.txt"
  RUN="$X/deck/p/libs.tech/klayout/tech/lvs/run_lvs.py"
else
  RUN="$PDKD/lvs/run_lvs.py"
fi
date -u +%Y-%m-%dT%H:%M:%SZ > "$X/start.txt"
set +e
flow/run.sh python3 "$RUN" --layout="$G" --netlist="/work/$CDL" --topcell=r1_adc --run_mode=deep \
  --no_series_res --run_dir="$X/out" > "$X/console.log" 2>&1
echo "exit $?" > "$X/exit.txt"
date -u +%Y-%m-%dT%H:%M:%SZ > "$X/end.txt"
G1_WORKDIR=$B/layout; export G1_WORKDIR
flow/run.sh klayout -b -r tools/lvsdb_report.py -rd db=$X/out/r1_adc.lvsdb 2>&1 | grep -v "level=warning\|Resource enforcement" > "$REP/lvs_summary.txt"
set -e
cp "$X/console.log" "$REP/lvs.log"
for f in "$REP/lvs.log" "$REP/lvs_summary.txt"; do
  sed -i -e "s#$G1_RESULTS_ROOT#<G1_RESULTS_ROOT>#g" -e "s#/work/#<repo>/#g" -e "s#$(pwd)/#<repo>/#g" "$f"
done
python3 - "$RID" "$MODE" "$G" "$X" "$REP" "$CDL" <<'PY'
import hashlib, json, os, re, sys
rid, mode, g, x, rep, cdl = sys.argv[1:]
root = os.environ['G1_RESULTS_ROOT']
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
L = open(os.path.join(rep, 'lvs.log'), errors='replace').read()
res = [l.strip() for l in L.splitlines() if re.search(r'(?i)netlists match|don.t match|error', l)][-4:]
j = dict(run_id=rid, mode=mode, command='G1_CPUSET=<cpus>; G1_RESULTS_ROOT=<G1_RESULTS_ROOT>; sh designs/r1-joint/blocks/r1_adc/layout/b5/run_lvs_b5.sh %s <gds> %s%s' % (rid, mode, '' if cdl.endswith('r1_adc_lvs_b5.cdl') else ' ' + cdl),
         inputs={g.replace(root, '<G1_RESULTS_ROOT>'): sha(g), cdl.replace('designs/r1-joint/blocks/r1_adc/', ''): sha(cdl)},
         tools=dict(klayout='0.30.9 (container image sha256:ddeb69576f28...)', pdk_commit='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'),
         start=open(os.path.join(x, 'start.txt')).read().strip(), end=open(os.path.join(x, 'end.txt')).read().strip(),
         exit=open(os.path.join(x, 'exit.txt')).read().strip(), result=res, raw='<G1_RESULTS_ROOT>/r1_adc/%s/' % rid)
json.dump(j, open(os.path.join(rep, 'run.json'), 'w'), indent=1)
print(json.dumps(j['result'], indent=1), j['exit'])
PY

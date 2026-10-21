#!/bin/sh
# PEX of r1_osc (method of r1_bgr: kpex 2.5D CC + KLayout RNetExtractor, see pex_input.py and pex_build.py).
# Run from the repository root after run_checks.sh <layout-tag> (POSIX sh):
#   G1_CPUSET=100-102; export G1_CPUSET; G1_RESULTS_ROOT=<G1_RESULTS_ROOT>; export G1_RESULTS_ROOT
#   sh designs/r1-joint/blocks/r1_osc/layout/run_pex.sh <layout-tag> <pex-tag>
# Reads <G1_RESULTS_ROOT>/r1_osc/layout-gen-<layout-tag>/; writes pex-in-, pex-cc-, pex-rc-<pex-tag>/.
set -eu
LT=$1
PT=$2
R=$G1_RESULTS_ROOT/r1_osc
L=designs/r1-joint/blocks/r1_osc/layout
G=$R/layout-gen-$LT
for k in in cc rc; do test ! -e "$R/pex-$k-$PT" || { echo "run dir exists: $R/pex-$k-$PT"; exit 1; }; done
mkdir -p "$R/pex-in-$PT"
flow/run.sh klayout -b -r $L/pex_input.py -rd gds=$G/r1_osc.gds -rd meta=$G/r1_osc_layout_meta.json \
  -rd out=$R/pex-in-$PT/r1_osc_pexin.gds > "$R/pex-in-$PT/pex_input.log" 2>&1
# kpex clears its --out_dir: its console log goes next to the directory
flow/run.sh kpex --pdk ihp_sg13g2 --gds $R/pex-in-$PT/r1_osc_pexin.gds --cell r1_osc --schematic $G/r1_osc_lvs.cdl \
  --2.5D --mode CC --out_dir $R/pex-cc-$PT > "$R/pex-cc-$PT.console.log" 2>&1
flow/run.sh klayout -b -r $L/pex_build.py -rd kpexdir=$R/pex-cc-$PT/r1_osc_pexin__r1_osc -rd gds=$R/pex-in-$PT/r1_osc_pexin.gds \
  -rd meta=$G/r1_osc_layout_meta.json -rd out=$R/pex-rc-$PT > "$R/pex-rc-$PT.console.log" 2>&1
python3 - "$R" "$LT" "$PT" <<'PY'
import hashlib, json, os, sys, time
R, LT, PT = sys.argv[1:]
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
rc = os.path.join(R, 'pex-rc-' + PT)
logl = open(os.path.join(rc, 'pex_build.log')).read().splitlines()
j = dict(run_id='pex-rc-' + PT, written=time.strftime('%Y-%m-%dT%H:%M:%S'),
         pdk_commit='84374023ee8b4b126bebbba67fcbada0a9c0ff0b',
         container='tapeoutbench-eda:latest sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2',
         cpuset=os.environ.get('G1_CPUSET'), tools=dict(klayout='0.30.9', kpex='0.3.12'),
         command='sh designs/r1-joint/blocks/r1_osc/layout/run_pex.sh %s %s' % (LT, PT),
         inputs=dict(layout_run='<G1_RESULTS_ROOT>/r1_osc/layout-gen-' + LT,
                     gds_sha256=sha(os.path.join(R, 'layout-gen-' + LT, 'r1_osc.gds')),
                     pex_input_gds_sha256=sha(os.path.join(R, 'pex-in-' + PT, 'r1_osc_pexin.gds')),
                     lvs_cdl_sha256=sha(os.path.join(R, 'layout-gen-' + LT, 'r1_osc_lvs.cdl'))),
         question='post-layout RC netlist of r1_osc (devices + MIM re-inserted + kpex 2.5D CC + RNetExtractor wiring R)',
         result=dict(log=logl, pex_netlist='<G1_RESULTS_ROOT>/r1_osc/pex-rc-%s/r1_osc_pex.spice' % PT,
                     pex_netlist_sha256=sha(os.path.join(rc, 'r1_osc_pex.spice')),
                     c_only_netlist_sha256=sha(os.path.join(rc, 'r1_osc_pex_c.spice'))),
         disposition='run')
json.dump(j, open(os.path.join(rc, 'run.json'), 'w'), indent=1)
print('\n'.join(l for l in logl if not l.startswith('per-net')))
cn = json.load(open(os.path.join(rc, 'r1_osc_pex_rnets.json')))['cnet_fF']
print(' '.join('%s=%.1f' % (k, v) for k, v in sorted(cn.items(), key=lambda kv: -kv[1]) if k not in ('vss', 'vdd'))[:900])
PY

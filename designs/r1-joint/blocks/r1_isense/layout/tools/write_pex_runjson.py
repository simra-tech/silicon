#!/usr/bin/env python3
"""run.json for a run_pex.sh run (container Python, repo root as cwd): command, tools, PDK commit, input sha256,
extraction statistics from pex_build.log, outputs. Paths as placeholders.   python3 write_pex_runjson.py <run id>"""
import hashlib, json, os, re, subprocess, sys, time
rid = sys.argv[1]
root = os.environ['G1_RESULTS_ROOT']
P = os.path.join(root, 'r1_isense', rid)
B = 'designs/r1-joint/blocks/r1_isense'
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
ph = lambda p: '<G1_RESULTS_ROOT>/' + os.path.relpath(p, root)
log = open(os.path.join(P, 'rc', 'pex_build.log'), errors='replace').read() if os.path.exists(os.path.join(P, 'rc', 'pex_build.log')) else ''
stats = [l.strip() for l in log.splitlines() if re.match(r'(devices|resistors|capacitors|device lines)', l)]
kv = subprocess.check_output(['klayout', '-v']).decode().strip()
kp = subprocess.run(['kpex', '--version'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout.decode().strip().splitlines()[-1]
j = dict(run_id=rid, date_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
         question='r1_isense channel PEX: kpex 2.5D CC (MIM stripped) + wiring R by square counting (pex_build.py) + MIM '
                  'from the netlist; post-layout netlists RC, devices + C (_c), devices + R (_r)',
         command='G1_CPUSET=109-111; G1_RESULTS_ROOT=<G1_RESULTS_ROOT>; sh %s/layout/pex/run_pex.sh %s' % (B, rid),
         cpuset=os.environ.get('G1_CPUSET'),
         tools=dict(klayout=kv, kpex=kp, image_id='sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2',
                    pdk_commit=open('/foss/pdks/ihp-sg13g2/COMMIT').read().strip()),
         inputs={'layout/r1_isense.gds': sha(B + '/layout/r1_isense.gds'), 'layout/r1_isense_lvs.cdl': sha(B + '/layout/r1_isense_lvs.cdl'),
                 'schematic/r1_isense.spice': sha(B + '/schematic/r1_isense.spice'),
                 'layout/pex/pex_build.py': sha(B + '/layout/pex/pex_build.py'), 'layout/pex/make_post.py': sha(B + '/layout/pex/make_post.py')},
         method='sheet R: Metal1 0.110, Metal2-Metal4 0.088 ohm/sq, 9 ohm per via cut; kpex 2.5D CC; MIM devices from the '
                'netlist by net name; contact resistance inside PCells not extracted',
         stats=stats,
         outputs={k: ph(os.path.join(P, 'rc', k)) for k in ('r1_isense_ch_pex.spice', 'r1_isense_ch_pex_c.spice', 'r1_isense_ch_pex_r.spice',
                                                          'r1_isense_post.spice', 'r1_isense_post_c.spice', 'r1_isense_post_r.spice',
                                                          'pex_paths.json')},
         outputs_sha256={k: sha(os.path.join(P, 'rc', k)) for k in ('r1_isense_ch_pex.spice', 'r1_isense_post.spice')
                         if os.path.exists(os.path.join(P, 'rc', k))},
         disposition='passed' if stats and "'open': 0" in log else 'failed')
json.dump(j, open(os.path.join(P, 'run.json'), 'w'), indent=1)
print('run.json', j['disposition'])

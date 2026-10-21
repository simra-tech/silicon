#!/usr/bin/env python3
"""run.json for a run_checks.sh run (container Python): command, tools, PDK commit, input sha256, DRC markers per
rule (main + maximal, and antenna) from the .lyrdb files, LVS outcome and counts, pin check. Paths as placeholders."""
import glob, hashlib, json, os, re, subprocess, sys, time
import xml.etree.ElementTree as ET
rid, what, outd, rep = sys.argv[1:5]
root = os.environ['G1_RESULTS_ROOT']
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()


def markers(d):
    files = sorted(glob.glob(os.path.join(d, '*.lyrdb')))
    if not files:
        return dict(status='not run')
    cnt = {}
    for p in files:
        for it in ET.parse(p).getroot().iter('item'):
            c = it.find('category').text.strip().strip("'")
            cnt[c] = cnt.get(c, 0) + 1
    return dict(status='passed' if not cnt else 'failed', total=sum(cnt.values()), per_rule=cnt,
                lyrdb=['<G1_RESULTS_ROOT>/' + os.path.relpath(p, root) for p in files])


def grab(p, pat):
    try:
        return [l.strip() for l in open(p, errors='replace') if re.search(pat, l)]
    except OSError:
        return ['not run']


lvs = dict(status='not run')
if os.path.exists(os.path.join(rep, 'lvs.log')):
    log = open(os.path.join(rep, 'lvs.log'), errors='replace').read()
    lvs['status'] = 'passed' if 'PASS (netlists match)' in log else 'failed'
    if os.path.exists(os.path.join(rep, 'lvs_summary.txt')):
        lvs['summary'] = [l.rstrip() for l in open(os.path.join(rep, 'lvs_summary.txt')) if l.startswith(('CIRCUIT', '  nets', '  net non', '  device non'))]
pins = dict(status='not run')
if os.path.exists(os.path.join(rep, 'pin_check.txt')):
    t = open(os.path.join(rep, 'pin_check.txt')).read()
    pins = dict(status='passed' if 'PIN CHECK: pins equal CDL ports' in t else 'failed',
                lines=[l for l in t.splitlines() if l.startswith(('PIN', 'macro'))])
kv = subprocess.check_output(['klayout', '-v']).decode().strip()
j = dict(run_id=rid, what=what, date_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
         question='r1_isense layout: PDK DRC main + maximal 0 markers (density waived at block level), antenna 0, '
                  'LVS match against the netlist of record (unit split), pins at the boundary equal to the CDL ports?',
         command='G1_CPUSET=109-111; G1_RESULTS_ROOT=<G1_RESULTS_ROOT>; G1_WORKDIR=designs/r1-joint/blocks/r1_isense/layout; '
                 'flow/run.sh sh run_checks.sh %s %s' % (rid, what),
         cpuset=os.environ.get('G1_CPUSET'),
         tools=dict(klayout=kv, image_id='sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2',
                    pdk_commit=open('/foss/pdks/ihp-sg13g2/COMMIT').read().strip()),
         inputs={'layout/r1_isense.gds': sha('r1_isense.gds'), 'layout/r1_isense_lvs.cdl': sha('r1_isense_lvs.cdl'),
                 'schematic/r1_isense.spice': sha('../schematic/r1_isense.spice'),
                 'layout/r1_isense_layout.py': sha('r1_isense_layout.py'), 'layout/r1_isense_netlist.py': sha('r1_isense_netlist.py'),
                 'layout/maze_router.py': sha('maze_router.py')},
         drc=markers(os.path.join(outd, 'drc')), antenna=markers(os.path.join(outd, 'antenna')), lvs=lvs, pins=pins,
         drc_log=grab(os.path.join(rep, 'drc.log'), r'Number of DRC errors|DRC Check'),
         raw='<G1_RESULTS_ROOT>/' + os.path.relpath(outd, root) + '/')
j['disposition'] = 'passed' if all(j[k]['status'] == 'passed' for k in ('drc', 'antenna', 'lvs', 'pins')) else \
    ('failed' if any(j[k]['status'] == 'failed' for k in ('drc', 'antenna', 'lvs', 'pins')) else 'partial')
json.dump(j, open(os.path.join(rep, 'run.json'), 'w'), indent=1)
print(json.dumps(dict(drc=j['drc'].get('per_rule', j['drc']['status']), antenna=j['antenna'].get('per_rule', j['antenna']['status']),
                      lvs=j['lvs'], pins=pins['status']), indent=1))

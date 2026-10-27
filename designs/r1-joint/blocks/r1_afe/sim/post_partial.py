#!/usr/bin/env python3
"""Revision F1 (track T3): results of a 'var:' campaign that is still running or was stopped, from the job logs and
loop-gain files present in the run directory (same parsers as run_afe.py). Writes results/<run-id>-partial.json for
revf_post.py.  python3 post_partial.py <run-id> <spec.json>
Merge of a campaign run in parts: python3 post_partial.py <name> <run-id>:<spec.json> [<run-id>:<spec.json> ...]
writes results/<name>.json; a job tag of a later part replaces the same tag of an earlier part (stopped jobs).
"""
import json, os, sys
import run_afe
root = os.environ['G1_RESULTS_ROOT']
if ':' in sys.argv[2]:
    oname, parts = sys.argv[1], [a.split(':', 1) for a in sys.argv[2:]]
else:
    oname, parts = sys.argv[1] + '-partial', [sys.argv[1:3]]


def collect(rid, spec):
  out = os.path.join(root, 'r1_afe', rid)
  S = json.load(open(spec))
  res, missing = [], []
  for vn in S['variants']:
      for jj in S['jobs']:
          name = '%s__%s' % (vn, jj['tag'])
          log = os.path.join(out, name + '.log')
          if not os.path.exists(log):
              missing.append(name); continue
          rows = run_afe.parse(log)
          if jj['tmpl'] == 'tb_afe_stb.cir':
              rows += run_afe.stb_post(dict(name=name), out)
          res.append(dict(name=name, corner=jj['corner'], mismatch=jj.get('mismatch', False), subs=jj.get('subs', {}), rc=0 if rows else -1,
                          rows=rows, log=os.path.relpath(log, root)))
  return res, missing


allres = {}
for rid, spec in parts:
    res, missing = collect(rid, spec)
    for r in res:
        if r['rc'] == 0 or r['name'] not in allres:
            allres[r['name']] = dict(r, run=rid)
    print(rid, len(res), 'jobs with a log;', len(missing), 'not started:', ' '.join(m.split('__')[1] for m in missing))
json.dump(list(allres.values()), open('results/%s.json' % oname, 'w'), indent=1)
print(len(allres), 'jobs written to results/%s.json' % oname)

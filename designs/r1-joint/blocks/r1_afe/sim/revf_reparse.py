#!/usr/bin/env python3
"""Layout E6 (track T3j): rebuild results/<run-id>.json from the logs of the finished jobs of a var: campaign that was
stopped before its end (run_afe.py writes the results file only after the last job). A job counts as finished when its
log exists and it is not listed as running; its rows are parsed with the functions of run_afe.py (working copy, identical to the frozen copy of the run).
  G1_RESULTS_ROOT=<bulk> python3 revf_reparse.py <run-id> <out-run-id> [tag,tag,...]   (container, from sim/)
The tags given are the jobs whose ngspice was still running when the run was stopped. Jobs without a log or listed are listed in 'not_run' of runs/<out-run-id>/run.json."""
import importlib.util, json, os, sys, time
rid, oid = sys.argv[1], sys.argv[2]
skip = set(sys.argv[3].split(',')) if len(sys.argv) > 3 else set()   # tags whose ngspice was still running at the stop
root = os.environ['G1_RESULTS_ROOT']
out = os.path.join(root, 'r1_afe', rid)
spec = importlib.util.spec_from_file_location('ra', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'run_afe.py'))   # working copy; diff it against <run>/frozen/run_afe.py first
ra = importlib.util.module_from_spec(spec); spec.loader.exec_module(ra)
vs = json.load(open(os.path.join(out, 'frozen', 'var_spec.json')))
res, not_run = [], []
for vn in vs['variants']:
    for jj in vs['variants'][vn].get('jobs', vs['jobs']):   # E9b: per-variant job lists
        name = '%s__%s' % (vn, jj['tag'])
        log = os.path.join(out, name + '.log')
        done = os.path.exists(log) and jj['tag'] not in skip
        if not done:
            not_run.append(jj['tag']); continue
        j = ra.job(name, jj['tmpl'], jj['corner'], jj.get('mismatch', False), **jj.get('subs', {}))
        j['subs']['RAW'] = os.path.join(out, name)
        rows = ra.parse(log)
        if jj['tmpl'] == 'tb_afe_stb.cir':
            rows += ra.stb_post(j, out)
        elif jj['tmpl'] == 'tb_afe_cmstep.cir':
            rows += ra.cmstep_post(j, out)
        subs = {k: (v.replace(root, '$G1_RESULTS_ROOT') if isinstance(v, str) else v) for k, v in j['subs'].items()}
        res.append(dict(name=name, corner=j['corner'], mismatch=j['mismatch'], subs=subs, rc=0 if rows else 1, edits=[],
                        rows=rows, log=os.path.relpath(log, root), reparsed=True))
os.makedirs('runs/' + oid, exist_ok=True)
json.dump(res, open('results/%s.json' % oid, 'w'), indent=1)
json.dump(dict(run_id=oid, source_run=rid, method='revf_reparse.py: rows parsed from the finished logs of a stopped run',
               date_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), jobs=len(res), not_run=not_run,
               raw='$G1_RESULTS_ROOT/r1_afe/' + rid + '/'), open('runs/%s/run.json' % oid, 'w'), indent=1)
print(len(res), 'jobs reparsed;', len(not_run), 'not run:', not_run)

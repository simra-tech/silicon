#!/usr/bin/env python3
"""Summarise the T4 post-submission runs (run ids ps4*, psmc*) into runs.json / runs.csv next to this file.

Reads, per tag, sim/logs/<tag>.json (runner record), the last line of <tag>.progress.jsonl (running runs) and the
result lines of sim/logs/<tag>.log (or <tag>.tail.txt). Python 3.6 compatible (host or container).
"""
import csv
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SIM = os.path.abspath(os.path.join(HERE, '..', '..'))
LOGS = os.path.join(SIM, 'logs')
# after the campaign the runner files are moved to bulk storage: PS_EVIDENCE=<dir> with logs/ and decks/ below it
EVID = os.environ.get('PS_EVIDENCE')
LOGDIRS = [LOGS] + ([os.path.join(EVID, 'logs')] if EVID else [])
DECKDIRS = [os.path.join(SIM, 'decks')] + ([os.path.join(EVID, 'decks')] if EVID else [])


def find(dirs, name):
    for d in dirs:
        if os.path.exists(os.path.join(d, name)):
            return os.path.join(d, name)
    return None
KEYS = ('QUIET', 'CLOCK', 'SUPPLY_uA', 'T2F', 'TRIP', 'NO_TRIP_EXPECTED', 'CHARGE', 'REARM', 'POWERUP', 'PORTIMING', 'CAL')


def kv(line):
    toks = line.split()
    out = {}
    i = 1
    while i < len(toks):
        t = toks[i]
        if t.endswith('='):
            k = t[:-1]
            v = toks[i + 1] if i + 1 < len(toks) and not toks[i + 1].endswith('=') else ''
            i += 2 if v != '' else 1
        elif '=' in t:
            k, v = t.split('=', 1)
            i += 1
        else:
            i += 1
            continue
        try:
            out[k] = float(v)
        except ValueError:
            out[k] = v if v != '' else None
    return out


def last_line(path):
    try:
        with open(path, 'rb') as f:
            f.seek(0, 2)
            size = f.tell()
            f.seek(max(0, size - 200000))
            lines = f.read().decode(errors='replace').strip().splitlines()
        return json.loads(lines[-1]) if lines else None
    except (OSError, ValueError):
        return None


def one(jpath):
    tag = os.path.basename(jpath)[:-5]
    ldir = os.path.dirname(jpath)
    d = json.load(open(jpath))
    rec = dict(tag=tag, status=d.get('status'), wall_s=d.get('wall_s'), returncode=d.get('returncode'),
               last_sim_time_s=d.get('last_reported_sim_time_s'),
               solver_message=d.get('solver_failure_diagnostic'), deck_sha256=d.get('deck_sha256'),
               runner_sha256=d.get('runner_sha256'), run_top_sha256=d.get('run_top_sha256'),
               options={k: v for k, v in (d.get('options') or {}).items()
                        if k in ('cases', 'corner', 'temp', 'pads', 'maxstep_ns', 'extra_options', 'fault_mult',
                                 'cal_kind', 'cal_codes', 'tstop', 'por_pin', 'timeline', 'run_id', 'timeout')})
    if rec['status'] == 'running':
        p = last_line(os.path.join(ldir, tag + '.progress.jsonl'))
        if p:
            rec['wall_s'] = p.get('wall_s')
            rec['last_sim_time_s'] = p.get('last_reported_sim_time_s', rec['last_sim_time_s'])
    logp = os.path.join(ldir, tag + '.log')
    if not os.path.exists(logp):
        logp = os.path.join(ldir, tag + '.tail.txt')
    if os.path.exists(logp):
        txt = open(logp, errors='replace').read()
        for l in txt.splitlines():
            m = re.match(r'^(%s)\b' % '|'.join(KEYS), l)
            if m:
                rec.setdefault('results', {})[m.group(1)] = kv(l)
        if rec['status'] == 'completed':
            rec['solver_message'] = None
        elif not rec.get('solver_message') or len(rec['solver_message']) < 20:
            m = re.findall(r'(?m)^.*(?:Timestep too small|trouble with)[^\n]*', txt)
            if m:
                rec['solver_message'] = m[-1].strip()[:300]
        dk = find(DECKDIRS, tag + '.cir')
        m = re.search(r'(?m)^\* psrun\.py PDK mismatch MC: seed (\d+)', open(dk).read()) if dk else None
        if m:
            rec['mc_seed'] = int(m.group(1))
    return rec


def main():
    pats = sys.argv[1:] or ['*_ps4*.json', '*_psmc*.json']
    files = sorted(set(f for d in LOGDIRS for p in pats for f in glob.glob(os.path.join(d, p))))
    recs = [one(f) for f in files]
    with open(os.path.join(HERE, 'runs.json'), 'w') as f:
        json.dump(recs, f, indent=1, sort_keys=True)
    cols = ['tag', 'status', 'wall_s', 'last_sim_time_s', 'mc_seed', 'solver_message']
    with open(os.path.join(HERE, 'runs.csv'), 'w') as f:
        w = csv.writer(f)
        w.writerow(cols + ['trip_cause', 't_trip_d_us', 't_gate_1V_us', 'tripped_max', 'gate_min', 't2f_MHz',
                           'vref_q', 'icmp_q', 'vth_soft_q', 'vth_hard_q', 'cal'])
        for r in recs:
            res = r.get('results', {})
            tr, q, t2 = res.get('TRIP', {}), res.get('QUIET', {}), res.get('T2F', {})
            cal = res.get('CAL')
            w.writerow([r.get(c) for c in cols] + [tr.get('cause'), tr.get('t_trip_d_us'), tr.get('t_gate_1V_us'),
                                                    tr.get('tripped_max'), tr.get('gate_min'), t2.get('f_MHz'),
                                                    q.get('vref'), q.get('icmp'), q.get('vth_soft'), q.get('vth_hard'),
                                                    json.dumps(cal) if cal else ''])
    for r in recs:
        t = r.get('last_sim_time_s')
        print('%-9s %8s s  t=%-10s %s' % (r['status'], '%.0f' % (r['wall_s'] or 0), ('%.3g' % t) if t else '-', r['tag']))


if __name__ == '__main__':
    main()

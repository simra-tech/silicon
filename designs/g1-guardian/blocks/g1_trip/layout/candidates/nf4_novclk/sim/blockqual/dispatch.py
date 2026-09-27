#!/usr/bin/env python3
"""Block qualification 2026-09-27: run a list of jobs, one per CPU, each pinned (the command template gets {cpu}).
  BULK=<bulk root> python3 dispatch.py <jobs file> <cpu list e.g. 45-63> <state dir>
jobs file: '<name>\t<shell command with {cpu}>' per line, run in order from the repo root, normal priority (no nice).
Writes <state dir>/jobs.jsonl (name, cpu, start, end, wall_s, rc) and <state dir>/<name>.out."""
import json, os, subprocess, sys, time
jobs_f, cpus_s, st = sys.argv[1:4]
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), *['..'] * 9))
cpus = []
for part in cpus_s.split(','):
    a, _, b = part.partition('-'); cpus += list(range(int(a), int(b or a) + 1))
jobs = [l.rstrip('\n').split('\t', 1) for l in open(jobs_f) if l.strip() and not l.startswith('#')]
os.makedirs(st, exist_ok=True)
free, running = list(cpus), {}
while jobs or running:
    while jobs and free:
        name, cmd = jobs.pop(0); cpu = free.pop(0)
        out = open(os.path.join(st, name + '.out'), 'w')
        p = subprocess.Popen(cmd.replace('{cpu}', str(cpu)), shell=True, cwd=REPO, stdout=out, stderr=subprocess.STDOUT, executable='/bin/bash')
        running[p] = (name, cpu, time.time())
    time.sleep(5)
    for p in list(running):
        if p.poll() is not None:
            name, cpu, t0 = running.pop(p); t1 = time.time(); free.append(cpu)
            open(os.path.join(st, 'jobs.jsonl'), 'a').write(json.dumps(dict(name=name, cpu=cpu, start=time.strftime('%H:%M:%S', time.localtime(t0)), end=time.strftime('%H:%M:%S', time.localtime(t1)), wall_s=round(t1 - t0, 1), rc=p.returncode)) + '\n')

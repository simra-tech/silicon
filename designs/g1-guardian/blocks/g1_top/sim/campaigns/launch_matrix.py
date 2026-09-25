#!/usr/bin/env python3
"""Pinned-CPU scheduler for run_top.py job matrices (host side, dependency-free).

Each job is {"id": str, "args": [run_top.py arguments], "wall_s": int}; the job file is JSON
(a list, or {"jobs": [...]}) or CSV (columns id,args,wall_s; args shell-quoted). Every job is
launched from the repository root as

    flow/launch_pinned.sh <cpu> designs/g1-guardian/blocks/g1_top/sim <wall_s> <logdir>/<id>.out \
        python3 run_top.py <args...> --timeout <wall_s-300> --run-id <id>

and is complete when the launcher writes <logdir>/<id>.out.rc.

Concurrency N per launch decision = min(--night-cores (21:00-09:00 local) or --day-cores,
--max-concurrent, nproc - 10 - sum(%CPU/100 of processes of other users)). A CPU from --cpus is
free only if this scheduler does not hold it and no process of this user is pinned to it
(/proc/<pid>/status Cpus_allowed_list), so parallel campaigns do not double-book CPUs.
A job is skipped if logs/*_<id>.log already ends with "# run status completed" (unless --force).

Usage:
  launch_matrix.py --example JOBFILE [--cases ..] [--corners ..] [--temps ..] [--extra ..] [--wall S] [--tag T]
  launch_matrix.py JOBFILE --cpus 20-63,88-127 [--logdir DIR] [--dry] [--max-concurrent N] [--force]
  launch_matrix.py JOBFILE --summarize [--logdir DIR]
"""
import argparse, csv, datetime, glob, json, os, re, shlex, signal, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
SIM = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(SIM, '..', '..', '..', '..', '..'))
SIM_REL = 'designs/g1-guardian/blocks/g1_top/sim'
LOGS = os.path.join(SIM, 'logs')
LAUNCHER = os.path.join(REPO, 'flow', 'launch_pinned.sh')
ID_RE = re.compile(r'[A-Za-z0-9_-]+')

EXAMPLE = dict(cases=['c_mid', 'c', 'q', 'f_mid', 'b_s', 'e20'], corners=['tt', 'ss', 'ff'],
               temps=[-40, 27, 85, 125],
               extra=['--blockset', 'c1414', '--netlist', 'pex', '--view-override', 'bgr=sch',
                      '--inpads', 'nodcn'], wall=12600, tag='c1414m')


def temp_tag(t):
    t = float(t)
    s = ('%g' % abs(t)).replace('.', 'p')
    return ('m' if t < 0 else '') + s + 'C'


def expand(cases, corners, temps, extra_args, tag, wall_s=12600):
    """Cartesian product cases x corners x temps -> list of job dicts."""
    jobs = []
    for case in cases:
        for corner in corners:
            for t in temps:
                jid = '%s_%s_%s_%s' % (case, corner, temp_tag(t), tag)
                jobs.append({'id': jid, 'args': [case, '--corner', corner, '--temp=%g' % float(t)] + list(extra_args),
                             'wall_s': int(wall_s)})
    return jobs


def load_jobs(path):
    if path.lower().endswith('.csv'):
        with open(path, newline='') as f:
            jobs = [{'id': r['id'].strip(), 'args': shlex.split(r['args']), 'wall_s': int(r['wall_s'])}
                    for r in csv.DictReader(f) if r.get('id', '').strip()]
    else:
        with open(path) as f:
            data = json.load(f)
        jobs = data['jobs'] if isinstance(data, dict) else data
        jobs = [{'id': str(j['id']), 'args': [str(x) for x in j['args']], 'wall_s': int(j['wall_s'])} for j in jobs]
    seen = set()
    for j in jobs:
        if not ID_RE.fullmatch(j['id']):
            raise SystemExit('job id not usable as run-id: %r' % j['id'])
        if j['id'] in seen:
            raise SystemExit('duplicate job id: ' + j['id'])
        if j['wall_s'] <= 300:
            raise SystemExit('wall_s must exceed 300 s (run_top timeout = wall_s - 300): ' + j['id'])
        seen.add(j['id'])
    return jobs


def write_jobs(path, jobs):
    if path.lower().endswith('.csv'):
        with open(path, 'w', newline='') as f:
            w = csv.writer(f)
            w.writerow(['id', 'args', 'wall_s'])
            for j in jobs:
                w.writerow([j['id'], ' '.join(shlex.quote(a) for a in j['args']), j['wall_s']])
    else:
        with open(path, 'w') as f:
            json.dump({'jobs': jobs}, f, indent=1)
            f.write('\n')


def parse_cpus(spec):
    cpus = []
    for part in spec.split(','):
        part = part.strip()
        if not part:
            continue
        if '-' in part:
            a, b = part.split('-')
            cpus.extend(range(int(a), int(b) + 1))
        else:
            cpus.append(int(part))
    return sorted(set(cpus))


def pinned_cpus_of_user():
    """CPUs to which any (non-kernel) process of this user is pinned (affinity narrower than half the machine)."""
    uid, n, busy = os.getuid(), os.cpu_count() or 1, set()
    for d in os.listdir('/proc'):
        if not d.isdigit():
            continue
        try:
            with open('/proc/%s/status' % d) as f:
                st = f.read()
            with open('/proc/%s/cmdline' % d, 'rb') as f:
                if not f.read(1):
                    continue
        except OSError:
            continue
        m_uid = re.search(r'^Uid:\s+(\d+)', st, re.M)
        m_cpu = re.search(r'^Cpus_allowed_list:\s+(\S+)', st, re.M)
        if not m_uid or not m_cpu or int(m_uid.group(1)) != uid:
            continue
        allowed = parse_cpus(m_cpu.group(1))
        if len(allowed) <= n // 2:
            busy.update(allowed)
    return busy


def foreign_load():
    me = str(os.getuid())
    out = subprocess.run(['ps', '-eo', 'uid=,pcpu='], stdout=subprocess.PIPE, universal_newlines=True).stdout
    s = 0.0
    for line in out.splitlines():
        p = line.split()
        if len(p) == 2 and p[0] != me:
            try:
                s += float(p[1]) / 100.0
            except ValueError:
                pass
    return s


def target_n(a):
    h = datetime.datetime.now().hour
    night = h >= 21 or h < 9
    target = a.night_cores if night else a.day_cores
    load = foreign_load()
    cap = int((os.cpu_count() or 1) - 10 - load)
    n = min(target, cap)
    if a.max_concurrent is not None:
        n = min(n, a.max_concurrent)
    return max(0, n), ('night' if night else 'day'), target, cap, load


def completed_log(jid):
    """Return (path, completed) for logs/*_<id>.log, or (None, False)."""
    paths = sorted(glob.glob(os.path.join(LOGS, '*_%s.log' % jid)))
    if not paths:
        return None, False
    ok = True
    for p in paths:
        ok &= '# run status completed' in tail(p)
    return paths[0], ok


def tail(path, nbytes=4096):
    with open(path, 'rb') as f:
        f.seek(0, 2)
        f.seek(max(0, f.tell() - nbytes))
        return f.read().decode(errors='replace')


def pid_alive(pidfile):
    try:
        pid = int(open(pidfile).read().strip())
        os.kill(pid, 0)
        return True
    except (OSError, ValueError):
        return False


class Scheduler:
    def __init__(self, a, jobs):
        self.a, self.jobs = a, jobs
        self.logdir = os.path.abspath(a.logdir)
        self.state_path = os.path.join(self.logdir, 'state.json')
        self.pool = parse_cpus(a.cpus)
        self.state = {}
        if os.path.exists(self.state_path):
            try:
                self.state = json.load(open(self.state_path)).get('jobs', {})
            except (OSError, ValueError):
                self.state = {}
        self.stop = False

    def out(self, jid):
        return os.path.join(self.logdir, jid + '.out')

    def save(self):
        if self.a.dry:
            return
        os.makedirs(self.logdir, exist_ok=True)
        tmp = self.state_path + '.tmp'
        with open(tmp, 'w') as f:
            json.dump({'updated': now(), 'jobfile': os.path.abspath(self.a.jobfile), 'cpus': self.a.cpus,
                       'jobs': self.state}, f, indent=1, sort_keys=True)
        os.replace(tmp, self.state_path)

    def classify(self):
        """Initial status of every job: skipped (completed log), blocked (incomplete evidence), adopted running, queued."""
        for j in self.jobs:
            jid, st = j['id'], self.state.get(j['id'], {})
            if st.get('status') == 'running':
                if os.path.exists(self.out(jid) + '.rc'):
                    self.reap(jid)
                    continue
                if pid_alive(self.out(jid) + '.pid'):
                    continue  # adopted from an earlier scheduler instance
                st.update(status='failed', note='launcher gone without rc file', finish=now())
                continue
            if st.get('status') in ('done', 'failed') and not self.a.force:
                continue
            if not self.a.dry and pid_alive(self.out(jid) + '.pid') and not os.path.exists(self.out(jid) + '.rc'):
                self.state[jid] = {'status': 'running', 'cpu': None, 'note': 'adopted live launcher (pid file)'}
                continue
            path, ok = completed_log(jid)
            if path and ok and not self.a.force:
                self.state[jid] = {'status': 'skipped', 'note': 'completed log ' + os.path.basename(path)}
            elif path and not ok:
                self.state[jid] = {'status': 'blocked',
                                   'note': 'incomplete log exists; run_top.py refuses to overwrite: ' + os.path.basename(path)}
            elif path and ok and self.a.force:
                self.state[jid] = {'status': 'blocked',
                                   'note': '--force: run_top.py refuses to overwrite ' + os.path.basename(path)}
            else:
                self.state[jid] = {'status': 'queued'}

    def reap(self, jid):
        st = self.state[jid]
        try:
            rc = int(open(self.out(jid) + '.rc').read().strip())
        except (OSError, ValueError):
            rc = -1
        st.update(rc=rc, finish=now(), status='done' if rc == 0 else 'failed')
        path, ok = completed_log(jid)
        if path:
            st['log'] = os.path.basename(path)
            if rc == 0 and not ok:
                st['status'] = 'failed'
                st['note'] = 'rc 0 but log lacks "# run status completed"'

    def free_cpus(self):
        held = {s.get('cpu') for s in self.state.values() if s.get('status') == 'running'}
        busy = pinned_cpus_of_user() | held
        return [c for c in self.pool if c not in busy]

    def counts(self):
        c = {}
        for j in self.jobs:
            s = self.state[j['id']]['status']
            c[s] = c.get(s, 0) + 1
        return c

    def launch(self, j, cpu):
        jid, wall = j['id'], j['wall_s']
        out = self.out(jid)
        cmd = [LAUNCHER, str(cpu), SIM_REL, str(wall), out, 'python3', 'run_top.py'] + j['args'] + \
              ['--timeout', str(wall - 300), '--run-id', jid]
        if self.a.dry:
            print('DRY cpu=%-4d %s' % (cpu, ' '.join(shlex.quote(x if x != LAUNCHER else 'flow/launch_pinned.sh') for x in cmd)))
            self.state[jid] = {'status': 'running', 'cpu': cpu}
            return
        os.makedirs(self.logdir, exist_ok=True)
        for ext in ('.rc', '.pid'):
            if os.path.exists(out + ext):
                os.remove(out + ext)
        # The launcher's detached subshell inherits these descriptors: never a pipe, or run() blocks until the job ends.
        with open(out + '.launch', 'w') as lf:
            r = subprocess.run(cmd, cwd=REPO, stdin=subprocess.DEVNULL, stdout=lf, stderr=subprocess.STDOUT,
                               start_new_session=True)
        if r.returncode != 0:
            msg = open(out + '.launch', errors='replace').read().strip()[-300:]
            self.state[jid] = {'status': 'failed', 'cpu': cpu, 'note': 'launcher rc %d: %s' % (r.returncode, msg),
                               'finish': now()}
        else:
            self.state[jid] = {'status': 'running', 'cpu': cpu, 'start': now(), 'wall_s': wall,
                               'cmd': ' '.join(shlex.quote(x) for x in cmd[1:])}
            print('%s launched %s on cpu %d' % (now(), jid, cpu), flush=True)
        self.save()

    def step(self):
        changed = False
        for jid, st in self.state.items():
            if st.get('status') == 'running' and os.path.exists(self.out(jid) + '.rc'):
                self.reap(jid)
                changed = True
        if changed:
            self.save()
        queued = [j for j in self.jobs if self.state[j['id']]['status'] == 'queued']
        while queued and not self.stop:
            n, period, target, cap, load = target_n(self.a)
            running = sum(1 for j in self.jobs if self.state[j['id']]['status'] == 'running')
            if running >= n:
                break
            free = self.free_cpus()
            if not free:
                break
            self.launch(queued.pop(0), free[0])
        n, period, target, cap, load = target_n(self.a)
        c = self.counts()
        print('%s N=%d (%s target %d, cap %d, foreign %.1f) running=%d queued=%d done=%d failed=%d skipped=%d blocked=%d'
              % (now(), n, period, target, cap, load, c.get('running', 0), c.get('queued', 0), c.get('done', 0),
                 c.get('failed', 0), c.get('skipped', 0), c.get('blocked', 0)), flush=True)
        return c.get('running', 0) + c.get('queued', 0)

    def run(self):
        def on_term(signum, frame):
            self.stop = True
        signal.signal(signal.SIGTERM, on_term)
        signal.signal(signal.SIGINT, on_term)
        self.classify()
        self.save()
        if self.a.dry:
            n, period, target, cap, load = target_n(self.a)
            print('# plan: %d jobs, pool %d CPUs, free now %d, N=%d (%s target %d, cap %d, foreign load %.1f)'
                  % (len(self.jobs), len(self.pool), len(self.free_cpus()), n, period, target, cap, load))
            for j in self.jobs:
                st = self.state[j['id']]
                if st['status'] != 'queued':
                    print('# %s: %s %s' % (j['id'], st['status'], st.get('note', '')))
            self.step()
            for j in self.jobs:
                if self.state[j['id']]['status'] == 'queued':
                    print('QUEUED %s' % j['id'])
            return 0
        while not self.stop:
            if not self.step():
                break
            for _ in range(self.a.poll):
                if self.stop:
                    break
                time.sleep(1)
        self.save()
        if self.stop:
            print('%s signal: state written, running jobs left detached' % now(), flush=True)
        return 0


def now():
    return datetime.datetime.now().astimezone().isoformat(timespec='seconds')


def kv(line):
    toks, d, i = line.split()[1:], {}, 0
    while i < len(toks):
        t = toks[i]
        if t.endswith('='):
            val = toks[i + 1] if i + 1 < len(toks) and not toks[i + 1].endswith('=') else ''
            d[t[:-1]] = val
            i += 2 if val else 1
        else:
            i += 1
    return d


def summarize(a, jobs):
    logdir = os.path.abspath(a.logdir)
    state = {}
    try:
        state = json.load(open(os.path.join(logdir, 'state.json'))).get('jobs', {})
    except (OSError, ValueError):
        pass
    cols = ['id', 'status', 'invalid', 'ngspice_exit', 'wall_s', 't_trip_d_us', 't_gate_1V_us', 'cause', 'kinds', 'log']
    rows = []
    for j in jobs:
        jid = j['id']
        paths = sorted(glob.glob(os.path.join(LOGS, '*_%s.log' % jid)))
        if not paths:
            st = state.get(jid, {})
            rows.append({'id': jid, 'status': 'not run' if not st else st.get('status', '') + (' rc=%s' % st['rc'] if 'rc' in st else ''),
                         'log': ''})
            continue
        for p in paths:
            r = {'id': jid, 'log': os.path.basename(p), 'status': 'incomplete'}
            kinds, bad = [], []
            for line in open(p, errors='replace'):
                if 'mismatched XSPICE/co-simulator' in line and 'cosim mismatch' not in bad:
                    bad.append('cosim mismatch')
                if line.startswith('# run status failed') and 'failed footer' not in bad:
                    bad.append('failed footer')
                w = line.split(' ', 1)[0].strip()
                if w in ('QUIET', 'TRIP', 'NO_TRIP_EXPECTED', 'REARM', 'POWERUP', 'T2F'):
                    kinds.append(w)
                    d = kv(line)
                    for k in ('t_trip_d_us', 't_gate_1V_us', 'cause'):
                        if d.get(k):
                            r[k] = d[k]
                elif line.startswith('# run status'):
                    r['status'] = line.split('# run status', 1)[1].strip()
                elif line.startswith('# ngspice exit'):
                    m = re.match(r'# ngspice exit (\S+), wall time (\S+) s', line)
                    if m:
                        r['ngspice_exit'], r['wall_s'] = m.group(1), m.group(2)
            r['kinds'] = '+'.join(dict.fromkeys(kinds))
            if bad:  # a later completed footer does not rescue an RTL-mismatch or failed run
                r['invalid'] = '+'.join(bad)
                r['status'] = 'failed (invalid)' if 'cosim mismatch' in bad else 'failed'
            rows.append(r)
    widths = {c: max(len(c), *(len(str(r.get(c, ''))) for r in rows)) for c in cols[:-1]}
    print('  '.join(c.ljust(widths[c]) for c in cols[:-1]))
    for r in rows:
        print('  '.join(str(r.get(c, '')).ljust(widths[c]) for c in cols[:-1]))
    os.makedirs(logdir, exist_ok=True)
    path = os.path.join(logdir, 'summary.csv')
    with open(path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, '') for c in cols})
    print('# wrote ' + path)
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('jobfile', help='job list (.json or .csv); with --example the file to write')
    p.add_argument('--example', action='store_true', help='write an example job file (defaults: 6 cases x 3 corners x 4 temps)')
    p.add_argument('--cases', nargs='+', default=EXAMPLE['cases'])
    p.add_argument('--corners', nargs='+', default=EXAMPLE['corners'])
    p.add_argument('--temps', nargs='+', type=float, default=EXAMPLE['temps'])
    p.add_argument('--extra', default=' '.join(EXAMPLE['extra']), help='extra run_top.py args, one shell-quoted string')
    p.add_argument('--wall', type=int, default=EXAMPLE['wall'])
    p.add_argument('--tag', default=EXAMPLE['tag'], help='suffix of generated job ids')
    p.add_argument('--cpus', default='20-63,88-127', help='CPU pool as a range list')
    p.add_argument('--logdir', help='default: <jobfile without extension>_run/')
    p.add_argument('--night-cores', type=int, default=85)
    p.add_argument('--day-cores', type=int, default=60)
    p.add_argument('--max-concurrent', type=int)
    p.add_argument('--poll', type=int, default=30, help='poll period (s)')
    p.add_argument('--dry', action='store_true', help='print the launch plan only')
    p.add_argument('--force', action='store_true', help='do not skip jobs with a completed log')
    p.add_argument('--summarize', action='store_true')
    a = p.parse_args()
    if a.example:
        jobs = expand(a.cases, a.corners, a.temps, shlex.split(a.extra), a.tag, a.wall)
        write_jobs(a.jobfile, jobs)
        print('wrote %d jobs to %s' % (len(jobs), a.jobfile))
        return 0
    a.logdir = a.logdir or os.path.splitext(os.path.abspath(a.jobfile))[0] + '_run'
    jobs = load_jobs(a.jobfile)
    if a.summarize:
        return summarize(a, jobs)
    return Scheduler(a, jobs).run()


if __name__ == '__main__':
    sys.exit(main())

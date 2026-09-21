#!/usr/bin/env python3
"""Persist child output directly; bound wall time and record observable progress.

No simulator-specific assertion is inferred from exit 0. Reference-value chatter
is retained verbatim as the last *reported* simulation time, not an accepted-step
or convergence claim. SIGTERM/SIGINT terminate the child process group as well.
"""
import datetime
import json
import os
import platform
import re
import signal
import shutil
import subprocess
import time
from pathlib import Path


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def atomic_json(path, data):
    tmp = str(path) + '.tmp'
    Path(tmp).write_text(json.dumps(data, indent=2) + '\n')
    os.replace(tmp, path)


def run_bounded(command, log, manifest_path, timeout_s, cwd=None, env=None, metadata=None, interval_s=5):
    if timeout_s <= 0:
        raise ValueError('timeout must be positive')
    state = dict(metadata or {}, command=command, started_utc=utc(), status='running',
                 timeout_s=timeout_s, runtime_arch=platform.machine())
    progress_path = str(manifest_path).replace('.json', '.progress.jsonl')
    if Path(manifest_path).exists() or Path(progress_path).exists():
        raise FileExistsError('refusing to overwrite existing manifest/progress')
    started = time.monotonic()
    if shutil.which('stdbuf'):
        command = ['stdbuf', '-o0', '-e0'] + command
    state['command'] = command
    state['stdio_unbuffered'] = bool(shutil.which('stdbuf'))
    log.flush()
    atomic_json(manifest_path, state)
    try:
        proc = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, cwd=cwd,
                                env=env, start_new_session=True)
    except OSError as exc:
        state.update(status='launch_failed', returncode=None, finished_utc=utc(),
                     wall_s=time.monotonic() - started,
                     launch_error={'type': type(exc).__name__, 'message': str(exc)})
        atomic_json(manifest_path, state)
        with open(progress_path, 'x') as progress:
            progress.write(json.dumps(state) + '\n')
        return state
    state['pid'] = proc.pid
    interrupted = []
    def on_signal(signum, frame):
        interrupted.append(signum)
    old = {s: signal.signal(s, on_signal) for s in (signal.SIGINT, signal.SIGTERM)}
    reason = None
    def stop_group(sig):
        try:
            os.killpg(proc.pid, sig)
        except ProcessLookupError:
            pass
    try:
        atomic_json(manifest_path, state)
        with open(progress_path, 'x') as progress:
            while True:
                elapsed = time.monotonic() - started
                state.update(wall_s=elapsed, sampled_utc=utc(), log_bytes=os.fstat(log.fileno()).st_size)
                with open(log.name, 'rb') as reader:
                    reader.seek(max(0, state['log_bytes'] - 65536))
                    tail = reader.read().decode('utf-8', errors='replace')
                matches = re.findall(r'Reference value\s*:\s*([-+0-9.eE]+)', tail)
                if matches:
                    state['last_reported_sim_time_s'] = float(matches[-1])
                # Linux process resource snapshot; unavailable fields are omitted.
                try:
                    status = Path('/proc/%d/status' % proc.pid).read_text()
                    state['resources'] = {k: v.strip() for k, v in re.findall(r'^(VmRSS|VmHWM|Threads):\s*(.+)$', status, re.M)}
                    state['cpu_ticks'] = Path('/proc/%d/stat' % proc.pid).read_text().rsplit(')', 1)[1].split()[11:13]
                except (FileNotFoundError, ProcessLookupError):
                    pass
                progress.write(json.dumps(state) + '\n'); progress.flush()
                atomic_json(manifest_path, state)
                if proc.poll() is not None:
                    break
                if interrupted or elapsed >= timeout_s:
                    reason = 'interrupted' if interrupted else 'timeout'
                    stop_group(signal.SIGTERM)
                    try:
                        proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        stop_group(signal.SIGKILL); proc.wait()
                    break
                time.sleep(min(interval_s, max(.01, timeout_s - elapsed)))
    finally:
        if proc.poll() is None:
            stop_group(signal.SIGKILL); proc.wait()
            reason = reason or 'runner_error'
        for s, handler in old.items():
            signal.signal(s, handler)
        state.update(status=reason or ('completed' if proc.returncode == 0 else 'failed'),
                     returncode=proc.returncode, finished_utc=utc(), wall_s=time.monotonic()-started)
        if interrupted:
            state['interrupt_signal'] = interrupted[-1]
        atomic_json(manifest_path, state)
    return state

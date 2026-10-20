#!/usr/bin/env python3
"""Run one ngspice deck for r1_adc through flow/run.sh and write sim/runs/<run-id>/run.json.

usage: run_ngspice.py --deck sim/tb_x.cir --run-id <id> [--sub KEY=VALUE ...] [--question "..."] [--timeout S]

The deck is copied to sim/runs/<run-id>/deck.cir with @RAW@ replaced by the bulk results directory
($G1_RESULTS_ROOT/r1_adc/<run-id>) and every @KEY@ replaced by --sub values. ngspice runs in the
container with the block directory as working directory (G1_WORKDIR), so decks include
schematic/... and sim/... paths. Python 3.6 compatible (no capture_output).
"""
import argparse
import datetime
import hashlib
import json
import os
import subprocess
import sys
import time

BLOCK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(BLOCK, "..", "..", "..", ".."))
REL_BLOCK = os.path.relpath(BLOCK, REPO)
PDK_COMMIT = "84374023ee8b4b126bebbba67fcbada0a9c0ff0b"
IMAGE_ID = "sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--deck", required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--sub", action="append", default=[])
    ap.add_argument("--question", default="")
    ap.add_argument("--timeout", type=int, default=14400)
    ap.add_argument("--cpuset", default=os.environ.get("G1_CPUSET", "103-105"))
    a = ap.parse_args()

    results_root = os.environ["G1_RESULTS_ROOT"]
    raw_dir = os.path.join(results_root, "r1_adc", a.run_id)
    run_dir = os.path.join(BLOCK, "sim", "runs", a.run_id)
    if os.path.exists(os.path.join(run_dir, "run.json")):
        sys.exit("run id exists: %s" % a.run_id)
    os.makedirs(run_dir, exist_ok=True)
    os.makedirs(raw_dir, exist_ok=True)
    src = open(os.path.join(BLOCK, a.deck)).read()
    subs = {"RAW": raw_dir}
    for kv in a.sub:
        k, v = kv.split("=", 1)
        subs[k] = v
    for k, v in subs.items():
        src = src.replace("@%s@" % k, v)
    deck_rel = os.path.join("sim", "runs", a.run_id, "deck.cir")
    # tracked copy without the machine-specific bulk path; the executed copy lives in the bulk directory
    with open(os.path.join(BLOCK, deck_rel), "w") as f:
        f.write(src.replace(results_root, "<G1_RESULTS_ROOT>"))
    exec_deck = os.path.join(raw_dir, "deck.cir")
    with open(exec_deck, "w") as f:
        f.write(src)
    lib_names = [n for n in ("r1_adc.spice", "r1_adc_mm.spice") if ("schematic/" + n) in src]
    lib_hash = {n: sha256(os.path.join(BLOCK, "schematic", n)) for n in lib_names}
    log_path = os.path.join(run_dir, "ngspice.log")
    env = dict(os.environ)
    env.update({"G1_CPUSET": a.cpuset, "G1_CPUS": "1", "G1_WORKDIR": REL_BLOCK, "G1_RESULTS_ROOT": results_root})
    cmd = [os.path.join(REPO, "flow", "run.sh"), "ngspice", "-b", exec_deck]
    t_start = time.time()
    started = datetime.datetime.utcnow().isoformat() + "Z"
    with open(log_path, "w") as lf:
        p = subprocess.Popen(cmd, stdout=lf, stderr=subprocess.STDOUT, env=env, cwd=REPO)
        try:
            rc = p.wait(timeout=a.timeout)
            status = "completed" if rc == 0 else "failed"
        except subprocess.TimeoutExpired:
            p.kill()
            rc = None
            status = "timeout"
    wall = time.time() - t_start
    log = open(log_path, errors="replace").read().replace(results_root, "<G1_RESULTS_ROOT>")
    with open(log_path, "w") as f:
        f.write(log)
    banner = [l.strip() for l in log.splitlines() if "ngspice-" in l and "Circuit level" in l]
    errors = [l.strip() for l in log.splitlines() if l.lower().startswith("error") or "fatal" in l.lower()][:20]
    # keep the tracked log small: cut repeated warnings beyond 2000 lines into the bulk directory
    lines = log.splitlines()
    if len(lines) > 2000:
        with open(os.path.join(raw_dir, "ngspice_full.log"), "w") as f:
            f.write(log)
        with open(log_path, "w") as f:
            f.write("\n".join(lines[:200] + ["... (%d lines cut; full log in bulk run directory) ..." % (len(lines) - 400)]
                              + lines[-200:]) + "\n")
    rj = {
        "run_id": a.run_id,
        "block": "r1_adc",
        "question": a.question,
        "command": "G1_CPUSET=%s G1_CPUS=1 G1_WORKDIR=%s G1_RESULTS_ROOT=<bulk> flow/run.sh ngspice -b "
                   "<G1_RESULTS_ROOT>/r1_adc/%s/deck.cir (= %s with the bulk path filled in)" % (a.cpuset, REL_BLOCK, a.run_id, deck_rel),
        "deck": deck_rel,
        "deck_template": a.deck,
        "deck_sha256": sha256(os.path.join(BLOCK, deck_rel)),
        "library_sha256_at_start": lib_hash,
        "substitutions": {k: (v if k != "RAW" else "<bulk>/r1_adc/%s" % a.run_id) for k, v in subs.items()},
        "tool": banner[0] if banner else "ngspice (banner not found in log)",
        "container_image": IMAGE_ID,
        "pdk_commit": PDK_COMMIT,
        "raw_results": "r1_adc/%s (under G1_RESULTS_ROOT)" % a.run_id,
        "started_utc": started,
        "wall_s": round(wall, 1),
        "returncode": rc,
        "status": status,
        "errors": errors,
        "result": "",
        "disposition": "",
    }
    with open(os.path.join(run_dir, "run.json"), "w") as f:
        json.dump(rj, f, indent=2)
    print("%s %s wall %.0f s rc %s" % (a.run_id, status, wall, rc))


if __name__ == "__main__":
    main()

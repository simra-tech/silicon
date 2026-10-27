#!/usr/bin/env python3
"""T2j (r1_adc_sar, D21): run one ngspice deck through flow/run.sh and write the run record.

Deck template: placeholders replaced by --sub K=V (whole-word, in the order given), SAVELIST from --save <file>,
RAW = <G1_RESULTS_ROOT>/r1_adc_sar/<id>. The filled deck and the log go to the results root; the tracked copy in
sar/sim/runs/<id>/deck.cir keeps the <G1_RESULTS_ROOT> placeholder. ngspice runs with the working directory
designs/r1-joint/blocks/r1_adc (includes schematic/..., sim/r5/..., sar/...). Exit code = ngspice exit code, or 3
if an expected output is missing or the log has an error line. No resubmission.

usage: run_ng.py --id ID --cpu 116 --deck sar/sim/tb_x.cir [--sub K=V ...] [--save F] [--expect sar.raw]
                 [--question Q] [--timeout S]
"""
import argparse, datetime, hashlib, json, os, re, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ADC = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.abspath(os.path.join(ADC, "..", "..", "..", ".."))
ap = argparse.ArgumentParser()
ap.add_argument("--id", required=True)
ap.add_argument("--cpu", required=True)
ap.add_argument("--deck", required=True)
ap.add_argument("--sub", action="append", default=[])
ap.add_argument("--save", default="")
ap.add_argument("--expect", action="append", default=[])
ap.add_argument("--question", default="")
ap.add_argument("--timeout", default="7200")
a = ap.parse_args()
bulk = os.environ["G1_RESULTS_ROOT"]
out = os.path.join(bulk, "r1_adc_sar", a.id)
rec = os.path.join(HERE, "runs", a.id)
if os.path.exists(out) or os.path.exists(rec):
    sys.exit("run id %s exists" % a.id)
os.makedirs(out)
os.makedirs(rec)
t = open(os.path.join(ADC, a.deck)).read()
subs = []
for s in a.sub:
    k, v = s.split("=", 1)
    subs.append((k, v))
if a.save:
    subs.append(("SAVELIST", open(os.path.join(ADC, a.save)).read().strip()))
for k, v in subs:
    t = re.sub(r"\b%s\b" % re.escape(k), lambda m: v, t)
t_rec = t.replace("RAW/", "<G1_RESULTS_ROOT>/r1_adc_sar/%s/" % a.id).replace(bulk, "<G1_RESULTS_ROOT>")
t_run = t.replace("RAW/", out + "/")
open(os.path.join(rec, "deck.cir"), "w").write(t_rec)
open(os.path.join(out, "deck.cir"), "w").write(t_run)
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
incs = re.findall(r"^\.include\s+(\S+)", t, re.M)
env = dict(os.environ, G1_CPUSET=a.cpu, G1_WORKDIR="designs/r1-joint/blocks/r1_adc")
t0 = time.time()
started = datetime.datetime.utcnow().isoformat() + "Z"
with open(os.path.join(out, "ngspice.log"), "w") as lg:
    p = subprocess.Popen(["timeout", a.timeout, os.path.join(REPO, "flow", "run.sh"), "ngspice", "-b",
                          os.path.join(out, "deck.cir")], cwd=REPO, env=env, stdout=lg, stderr=subprocess.STDOUT)
    rc = p.wait()
wall = time.time() - t0
log = open(os.path.join(out, "ngspice.log"), errors="replace").read()
errs = [l for l in log.splitlines() if re.search(r"(?i)\berror\b|singular|timestep too small|aborted", l)
        and "no error" not in l.lower()]
miss = [e for e in (a.expect or ["sar.raw"]) if not os.path.exists(os.path.join(out, e))]
ver = re.search(r"ngspice-\d+[^\n]*", log)
status = "completed" if rc == 0 and not miss and not errs else "failed"
d = {"run_id": a.id, "block": "r1_adc_sar", "track": "T2j", "question": a.question,
     "command": "G1_CPUSET=%s G1_WORKDIR=designs/r1-joint/blocks/r1_adc G1_RESULTS_ROOT=<G1_RESULTS_ROOT> flow/run.sh "
                "ngspice -b <G1_RESULTS_ROOT>/r1_adc_sar/%s/deck.cir (runner sar/sim/run_ng.py)" % (a.cpu, a.id),
     "deck_template": a.deck, "deck": "sar/sim/runs/%s/deck.cir" % a.id,
     "substitutions": {k: (v if k != "SAVELIST" else "file " + a.save) for k, v in subs},
     "includes_sha256": {i: sha(os.path.join(ADC, i)) for i in incs if os.path.exists(os.path.join(ADC, i))},
     "pdk_commit": "84374023ee8b4b126bebbba67fcbada0a9c0ff0b (checked by flow/run.sh)",
     "container_image": "tapeoutbench-eda:latest sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2",
     "ngspice_version": ver.group(0) if ver else "not found in log",
     "raw_results": "<G1_RESULTS_ROOT>/r1_adc_sar/%s/" % a.id, "started_utc": started, "wall_s": round(wall, 1),
     "returncode": rc, "status": status, "errors": errs[:20], "missing_outputs": miss,
     "result": "see sar/README.md", "disposition": "pending post-processing"}
open(os.path.join(rec, "run.json"), "w").write(json.dumps(d, indent=2).replace(bulk, "<G1_RESULTS_ROOT>"))
print(a.id, status, "rc", rc, "wall %.0f s" % wall)
sys.exit(rc if rc else (3 if (miss or errs) else 0))

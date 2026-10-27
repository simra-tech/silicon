#!/usr/bin/env python3
"""T2k (layout B5 helper): run one closed-loop deck of sim/post/b5/decks/<tag>/ through flow/run.sh and write the record.

The deck placeholders RAW and GLNET are filled: RAW = <G1_RESULTS_ROOT>/r1_adc/<id>, GLNET = the release gate-level
netlist (only used with gen_b5_decks.py --sar-par none). The filled deck and the log go to the results root; the tracked
copy sim/post/b5/runs/<id>/deck.cir keeps the <G1_RESULTS_ROOT> placeholder. ngspice runs in
designs/r1-joint/blocks/r1_adc. Rules (r5 / sim/post): one job, no resume, no resubmission; a run id is never reused;
exit code = ngspice exit code, or 3 if b5.raw is missing or the log has an error line.
--tstop: shorter transient (smoke test); the run record says so.

usage: run_b5.py --id ID --cpu 105 --deck sim/post/b5/decks/b4/mux_tt.cir [--question Q] [--timeout 7200] [--tstop 50n]
"""
import argparse, datetime, hashlib, json, os, re, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ADC = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
REPO = os.path.abspath(os.path.join(ADC, "..", "..", "..", ".."))
REL = "r1_adc_sar/release-t2j-h"
ap = argparse.ArgumentParser()
ap.add_argument("--id", required=True)
ap.add_argument("--cpu", required=True)
ap.add_argument("--deck", required=True)
ap.add_argument("--question", default="")
ap.add_argument("--disposition", default="pending post-processing (sim/post/b5/b5_post.py)")
ap.add_argument("--timeout", default="7200")
ap.add_argument("--tstop", default="")
a = ap.parse_args()
bulk = os.environ["G1_RESULTS_ROOT"]
out = os.path.join(bulk, "r1_adc", a.id)
rec = os.path.join(HERE, "runs", a.id)
if os.path.exists(out) or os.path.exists(rec):
    sys.exit("run id %s exists" % a.id)
t = open(os.path.join(ADC, a.deck)).read()
if a.tstop:
    t, n = re.subn(r"^tran 1n (\S+) 0 0\.2n$", "tran 1n %s 0 0.2n" % a.tstop, t, flags=re.M)
    assert n == 1
tstop = re.search(r"^tran 1n (\S+)", t, re.M).group(1)
os.makedirs(out)
os.makedirs(rec)
gl = os.path.join(bulk, REL, "r1_adc_sar_gl_sim.spice")
t = re.sub(r"\bGLNET\b", gl, t)
t_run = t.replace("RAW/", out + "/")
t_rec = t.replace("RAW/", "<G1_RESULTS_ROOT>/r1_adc/%s/" % a.id).replace(bulk, "<G1_RESULTS_ROOT>")
open(os.path.join(rec, "deck.cir"), "w").write(t_rec)
open(os.path.join(out, "deck.cir"), "w").write(t_run)
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
incs = re.findall(r"^\.include\s+(\S+)", t, re.M)
env = dict(os.environ, G1_CPUSET=a.cpu, G1_CPUS="1", G1_WORKDIR="designs/r1-joint/blocks/r1_adc")
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
miss = [] if os.path.exists(os.path.join(out, "b5.raw")) else ["b5.raw"]
ver = re.search(r"ngspice-\d+[^\n]*", log)
status = "completed" if rc == 0 and not miss and not errs else "failed"
# timeout (rc 124) sends TERM to flow/run.sh / podman only; ngspice in the container goes on and may still finish
# (run b5-ms-ref-tt-buf-s4). Such a run is labelled completed-late (wall time above the limit), never completed.
late = rc == 124 and not miss and not errs and "Simulation executed from .control section" in log and "No. of Data Rows" in log
if late:
    status = "completed-late"
tsim = float(re.sub(r"[a-z]", "", tstop)) * {"u": 1.0, "n": 1e-3}[tstop[-1]]
incsha = {}
for i in incs:
    pth = i if os.path.isabs(i) else os.path.join(ADC, i)
    if os.path.exists(pth):
        incsha[i.replace(bulk, "<G1_RESULTS_ROOT>")] = sha(pth)
    else:
        incsha[i] = "container path (PDK %s)" % "84374023"
d = {"run_id": a.id, "block": "r1_adc", "track": "T2k (helper)", "harness": "sim/post/b5", "question": a.question,
     "command": "G1_CPUSET=%s G1_CPUS=1 G1_WORKDIR=designs/r1-joint/blocks/r1_adc G1_RESULTS_ROOT=<G1_RESULTS_ROOT> flow/run.sh "
                "ngspice -b <G1_RESULTS_ROOT>/r1_adc/%s/deck.cir (runner sim/post/b5/run_b5.py)" % (a.cpu, a.id),
     "argv": sys.argv[1:], "deck_template": a.deck, "deck": "sim/post/b5/runs/%s/deck.cir" % a.id,
     "deck_template_sha256": sha(os.path.join(ADC, a.deck)), "tstop": tstop, "smoke_test": bool(a.tstop),
     "includes_sha256": incsha,
     "pdk_commit": "84374023ee8b4b126bebbba67fcbada0a9c0ff0b (checked by flow/run.sh)",
     "container_image": "tapeoutbench-eda:latest sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2",
     "ngspice_version": ver.group(0) if ver else "not found in log",
     "raw_results": "<G1_RESULTS_ROOT>/r1_adc/%s/" % a.id, "started_utc": started, "wall_s": round(wall, 1),
     "sim_us_per_wall_min": round(tsim / (wall / 60.0), 4) if wall > 0 else None,
     "returncode": rc, "status": status, "errors": errs[:20], "missing_outputs": miss,
     "result": "", "disposition": a.disposition}
open(os.path.join(rec, "run.json"), "w").write(json.dumps(d, indent=2).replace(bulk, "<G1_RESULTS_ROOT>"))
print(a.id, status, "rc", rc, "wall %.0f s" % wall)
sys.exit(rc if rc else (3 if (miss or errs) else 0))

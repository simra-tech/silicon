#!/usr/bin/env python3
"""Run one ngspice deck template at one or more corners through flow/run.sh (host side driver).

SHARED MODULE (2026-10-21, r1_isense revision 2): this file is the one runner of r1_isense and r1_safe;
r1_safe/sim/run_deck.py is a shim that executes this file. It merges the two hand-edited copies of 2026-10-20/21
(the r1_safe copy differed only in the NET handling, kept here: --set NET=<block-relative netlist> or --netlist).

Usage (from anywhere):
  python3 run_deck.py --block r1_isense --deck tb_isense_step.cir --run-id ID [--corners tt,ss,ff] [--set K=V ...]
                      [--question "..."] [--analyze analyze_x.py]

Corner templates fill @@MOS@@ @@RES@@ @@CAP@@ @@TEMP@@ @@VDDA@@ @@VDD@@ (+ any --set K=V as @@K@@).
Raw output (deck copy, ngspice log, wrdata files) goes to $G1_RESULTS_ROOT/<block>/<run-id>/;
the tree gets sim/results/<run-id>/run.json (+ summary.json from the analyzer).
CPU set: G1_CPUSET (default 109-111), one ngspice job per CPU, at most 3 in parallel.
"""
import argparse, hashlib, json, os, re, subprocess, sys, time, datetime

CORNERS = {
    # name: MOS, RES, CAP, TEMP, VDDA, VDD
    "tt":     ("mos_tt", "res_typ", "cap_typ", 27, 3.3, 1.2),
    "ss":     ("mos_ss", "res_wcs", "cap_wcs", 125, 3.0, 1.08),
    "ff":     ("mos_ff", "res_bcs", "cap_bcs", -40, 3.6, 1.32),
    "ss_cold": ("mos_ss", "res_wcs", "cap_wcs", -40, 3.0, 1.08),
    "ff_hot": ("mos_ff", "res_bcs", "cap_bcs", 125, 3.6, 1.32),
    "tt_hot": ("mos_tt", "res_typ", "cap_typ", 125, 3.3, 1.2),
    "tt_cold": ("mos_tt", "res_typ", "cap_typ", -40, 3.3, 1.2),
    "sf":     ("mos_sf", "res_typ", "cap_typ", 27, 3.3, 1.2),      # stb suite (T4 follow-up c): mixed MOS corners, as r1_afe
    # cross corners (r1_isense revision 2, as r1_afe ssx/ffx; both supplies at the same extreme as VDDA)
    "ssx":    ("mos_ss", "res_wcs", "cap_wcs", -40, 3.6, 1.32),
    "ffx":    ("mos_ff", "res_bcs", "cap_bcs", 125, 3.0, 1.08),
    "fs":     ("mos_fs", "res_typ", "cap_typ", 27, 3.3, 1.2),
    "tt_mm_s1": ("mos_tt_mismatch", "res_typ_mismatch", "cap_typ_mismatch", 27, 3.3, 1.2),
    "tt_mm_s2": ("mos_tt_mismatch", "res_typ_mismatch", "cap_typ_mismatch", 27, 3.3, 1.2),
    "tt_mm_s3": ("mos_tt_mismatch", "res_typ_mismatch", "cap_typ_mismatch", 27, 3.3, 1.2),
    "ss_mm_s4": ("mos_ss_mismatch", "res_wcs_mismatch", "cap_wcs_mismatch", 125, 3.0, 1.08),
    "ff_mm_s5": ("mos_ff_mismatch", "res_bcs_mismatch", "cap_bcs_mismatch", -40, 3.6, 1.32),
}
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", ".."))

def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--block", required=True)
    ap.add_argument("--deck", required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--corners", default="tt")
    ap.add_argument("--set", action="append", default=[])
    ap.add_argument("--question", default="")
    ap.add_argument("--analyze", default="")
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--netlist", default="", help="netlist whose sha256 goes into run.json (repo-relative or absolute); default schematic/<block>.spice")
    ap.add_argument("--pre", default="", help="stb suite: pre-run deck per corner; its log line 'HOLDVALS K=V ...' fills @@K@@ of the main deck")
    a = ap.parse_args()
    simdir = os.path.join(REPO, "designs/r1-joint/blocks", a.block, "sim")
    root = os.environ.get("G1_RESULTS_ROOT") or sys.exit("set G1_RESULTS_ROOT (bulk results directory)")
    rdir = os.path.join(root, a.block, a.run_id)
    if os.path.exists(rdir):
        sys.exit("run id exists: " + rdir)
    os.makedirs(rdir)
    tdir = os.path.join(simdir, "results", a.run_id)
    os.makedirs(tdir, exist_ok=True)
    deckpath = a.deck if os.path.isabs(a.deck) else os.path.join(simdir, a.deck)
    tmpl = open(deckpath).read()
    extra = dict(kv.split("=", 1) for kv in a.set)
    env = dict(os.environ)
    env.update({"G1_CPUSET": env.get("G1_CPUSET", "109-111"), "G1_CPUS": "1",
                "G1_WORKDIR": "designs/r1-joint/blocks/%s/sim" % a.block, "G1_RESULTS_ROOT": root})
    jobs, procs = [], []
    pre_vals, pre_info = {}, {}
    if a.pre:   # stb suite: operating-point pre-run (hold-cap voltages after the auto-zero), same corner substitution
        ptmpl = open(a.pre if os.path.isabs(a.pre) else os.path.join(simdir, a.pre)).read()
        prun = []
        for c in a.corners.split(","):
            mos, res, cap, temp, vdda, vdd = CORNERS[c]
            txt = ptmpl
            for k, v in (("MOS", mos), ("RES", res), ("CAP", cap), ("TEMP", str(temp)), ("VDDA", str(vdda)), ("VDD", str(vdd))):
                txt = txt.replace("@@%s@@" % k, v)
            deck = os.path.join(rdir, "%s_%s.cir" % (os.path.splitext(os.path.basename(a.pre))[0], c))
            open(deck, "w").write(txt)
            prun.append((c, deck))
        pend, run_ = list(prun), []
        while pend or run_:
            while pend and len(run_) < a.jobs:
                c, deck = pend.pop(0)
                lg = open(deck[:-4] + ".log", "w")
                run_.append((c, deck, subprocess.Popen([os.path.join(REPO, "flow/run.sh"), "ngspice", "-b", deck], stdout=lg,
                                                       stderr=subprocess.STDOUT, env=env, cwd=REPO)))
            time.sleep(2)
            for r in list(run_):
                if r[2].poll() is not None:
                    run_.remove(r)
                    pre_vals[r[0]] = {}
                    for line in open(r[1][:-4] + ".log", errors="replace"):
                        if line.startswith("HOLDVALS"):
                            pre_vals[r[0]] = dict(t.split("=", 1) for t in line.split()[1:])
                    pre_info[r[0]] = {"rc": r[2].returncode, "holdvals": pre_vals[r[0]], "deck": a.pre}
                    if not pre_vals[r[0]]:
                        sys.exit("pre-run of corner %s gave no HOLDVALS (see %s.log)" % (r[0], r[1][:-4]))
    for c in a.corners.split(","):
        mos, res, cap, temp, vdda, vdd = CORNERS[c]
        sub = {"MOS": mos, "RES": res, "CAP": cap, "TEMP": str(temp), "VDDA": str(vdda), "VDD": str(vdd),
               "OUT": os.path.join(rdir, c), "CORNER": c,
               "SEED": c.split("_s")[-1] if "_mm_s" in c else "1"}
        sub.update(extra)
        sub.update(pre_vals.get(c, {}))
        txt = tmpl
        for k, v in sub.items():
            txt = txt.replace("@@%s@@" % k, v)
        if "@@" in txt:
            sys.exit("unfilled placeholder in deck for corner " + c)
        deck = os.path.join(rdir, "%s_%s.cir" % (os.path.splitext(os.path.basename(a.deck))[0], c))
        open(deck, "w").write(txt)
        jobs.append((c, deck))
    t0 = time.time()
    try:   # tool version, once per run (batch logs carry no banner)
        vb = subprocess.run([os.path.join(REPO, "flow/run.sh"), "ngspice", "-v"], env=env, cwd=REPO, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, universal_newlines=True, timeout=120)   # python 3.6: no capture_output
        ngv = " ".join(l.strip() for l in (vb.stdout + vb.stderr).splitlines() if "ngspice" in l.lower() and "warning" not in l.lower())[:300]
    except Exception as e:
        ngv = "not read (%s)" % e
    pending = list(jobs)
    running = []
    results = {}
    while pending or running:
        while pending and len(running) < a.jobs:
            c, deck = pending.pop(0)
            log = open(deck[:-4] + ".log", "w")
            p = subprocess.Popen([os.path.join(REPO, "flow/run.sh"), "ngspice", "-b", deck],
                                 stdout=log, stderr=subprocess.STDOUT, env=env, cwd=REPO)
            running.append((c, deck, p, time.time()))
        time.sleep(2)
        for r in list(running):
            if r[2].poll() is not None:
                running.remove(r)
                results[r[0]] = {"rc": r[2].returncode, "wall_s": round(time.time() - r[3], 1),
                                 "log": os.path.relpath(r[1][:-4] + ".log", root)}
    summ = {}
    if a.analyze:
        p = subprocess.Popen([sys.executable, os.path.join(simdir, a.analyze), rdir, tdir],
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out = p.communicate()[0].decode()
        print(out)
        sp = os.path.join(tdir, "summary.json")
        if os.path.exists(sp):
            summ = json.load(open(sp))
    banner = ""
    for c, deck in jobs:
        for line in open(deck[:-4] + ".log", errors="replace"):
            if "ngspice-" in line and "Circuit" not in line:
                banner = line.strip(); break
        if banner:
            break
    if a.netlist:
        netlist = a.netlist if os.path.isabs(a.netlist) else os.path.join(REPO, a.netlist)
    elif "NET" in extra:
        netlist = os.path.join(REPO, "designs/r1-joint/blocks", a.block, extra["NET"])
    else:
        netlist = os.path.join(REPO, "designs/r1-joint/blocks", a.block, "schematic", a.block + ".spice")
    def rel(p):
        p = os.path.abspath(p)
        if p.startswith(root.rstrip("/") + "/"):
            return "<G1_RESULTS_ROOT>/" + os.path.relpath(p, root)
        return os.path.relpath(p, REPO)
    run = {
        "run_id": a.run_id, "block": a.block, "date_utc": datetime.datetime.utcnow().isoformat() + "Z",
        "command": "python3 designs/r1-joint/blocks/r1_isense/sim/run_deck.py " + " ".join(
            ('"%s"' % x if (" " in x or x.startswith("=")) else x).replace(root.rstrip("/"), "<G1_RESULTS_ROOT>") for x in sys.argv[1:]),
        "deck": rel(deckpath), "deck_sha256": sha(deckpath),
        "netlist": rel(netlist),
        "netlist_sha256": sha(netlist) if os.path.exists(netlist) else None,
        "corners": {c: dict(zip(("mos", "res", "cap", "temp_C", "vdda", "vdd"), CORNERS[c])) for c, _ in jobs},
        "overrides": extra, "prerun": {k: dict(v, deck=rel(v["deck"] if os.path.isabs(v["deck"]) else os.path.join(simdir, v["deck"]))) for k, v in pre_info.items()},
        "included_netlists": {m: sha(os.path.join(REPO, m[len("/work/"):])) for m in sorted(set(
            re.findall(r"^\.include\s+(/work/\S+\.spice)", tmpl, re.M)))},
        "included_netlists_results_root": {rel(m): sha(m) for m in sorted(set(
            re.findall(r"^\.include\s+(%s/\S+\.spice)" % re.escape(root.rstrip("/")), tmpl, re.M)))},
        "tool": banner or "ngspice-46 (container banner from flow/run.sh ngspice -v; batch logs carry no banner)",
        "ngspice_version": ngv, "workdir": env["G1_WORKDIR"],
        "pdk_commit": "84374023ee8b4b126bebbba67fcbada0a9c0ff0b (checked by flow/run.sh)",
        "container_image": "tapeoutbench-eda:latest sha256:ddeb6957... (checked by flow/run.sh)",
        "cpuset": env["G1_CPUSET"], "raw_results": "$G1_RESULTS_ROOT/%s/%s/" % (a.block, a.run_id),
        "question": a.question, "jobs": results, "wall_s": round(time.time() - t0, 1),
        "result": summ.get("result", {}), "disposition": summ.get("disposition", "see summary.json"),
    }
    json.dump(run, open(os.path.join(tdir, "run.json"), "w"), indent=1, sort_keys=True)
    print(json.dumps(results))

if __name__ == "__main__":
    main()

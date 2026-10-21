#!/usr/bin/env python3
"""r1_isense revision 2 development screens (2026-10-21): one netlist variant -> loop-gain runs in the three states.

Usage (repository root, G1_RESULTS_ROOT and G1_CPUSET set):
  python3 designs/r1-joint/blocks/r1_isense/sim/dev_r2.py RUN_ID "K=V K=V ..." [CORNERS] [STATES]
    K=V      gen_isense.py size overrides (see SIZES there); "" = netlist of record defaults
    CORNERS  default tt,ss,ff,sf,fs,ssx,ffx;  STATES default stb,stbaz,stbazi
The variant netlist and its decks go to <G1_RESULTS_ROOT>/r1_isense/RUN_ID-net/ (raw, not in the tree); each state is
one run_deck.py run with id RUN_ID-<state> (run.json + summary.json in sim/results/). Development runs, not evidence.
"""
import os, sys, subprocess, json
here = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(here, "..", "..", "..", "..", ".."))
root = os.environ["G1_RESULTS_ROOT"]
rid, ov = sys.argv[1], sys.argv[2].split()
corners = sys.argv[3] if len(sys.argv) > 3 else "tt,ss,ff,sf,fs,ssx,ffx"
states = (sys.argv[4] if len(sys.argv) > 4 else "stb,stbaz,stbazi").split(",")
nd = os.path.join(root, "r1_isense", rid + "-net")
report_only = os.path.isdir(nd)          # re-report an existing screen without running it again
net = os.path.join(nd, "r1_isense.spice")
if not report_only:
    os.makedirs(nd)
    subprocess.check_call([sys.executable, os.path.join(here, "..", "schematic", "gen_isense.py")] + ov + ["--out", net])
    env = dict(os.environ, R1_NET=net, R1_OUTDIR=nd)
    subprocess.check_call([sys.executable, os.path.join(here, "gen_tb_isense_stb.py")], env=env)
out = {}
for st in states:
    if st.startswith("mc"):     # mismatch MC of the variant: "mc:<corners>:<N>", tb_isense_mc.cir with the variant included
        _, mcc, nmc = st.split(":"); mcc = mcc.replace("+", ",")   # corners joined by "+"
        deck = os.path.join(nd, "tb_isense_mc.cir")
        if not os.path.isdir(os.path.join(here, "results", "%s-mc" % rid)):
            open(deck, "w").write(open(os.path.join(here, "tb_isense_mc.cir")).read().replace(
                "/work/designs/r1-joint/blocks/r1_isense/schematic/r1_isense.spice", net))
            subprocess.call([sys.executable, os.path.join(here, "run_deck.py"), "--block", "r1_isense", "--deck", deck, "--run-id", "%s-mc" % rid,
                             "--corners", mcc, "--jobs", "3", "--set", "N=" + nmc, "--netlist", net, "--analyze", "analyze_mc.py",
                             "--question", "revision-2 development screen, variant [%s], mismatch MC incl. output CM" % " ".join(ov)],
                            stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        sm = json.load(open(os.path.join(here, "results", "%s-mc" % rid, "summary.json")))["result"]
        for g, r in sm.items():
            print("MC", rid, g, "ocm mean %.4f sigma %.4f min %.4f max %.4f within30 %d/%d; res sigma %.1f uV max %.1f" % (
                r["ocm_V"]["mean"], r["ocm_V"]["sigma"], r["ocm_V"]["min"], r["ocm_V"]["max"], r["ocm_within_30mV"], r["ocm_V"]["n"],
                r["res_uV"]["sigma"], r["res_uV"]["max_abs"]))
        continue
    cmd = [sys.executable, os.path.join(here, "run_deck.py"), "--block", "r1_isense", "--deck", os.path.join(nd, "tb_isense_%s.cir" % st),
           "--run-id", "%s-%s" % (rid, st), "--corners", corners, "--jobs", "3", "--set", "RL=0.001", "--set", "CL=2p", "--set", "CW=0",
           "--netlist", net, "--analyze", {"stbstep": "analyze_stbstep.py", "stbcm": "analyze_stbcm.py"}.get(st, "analyze_stb.py"),
           "--question", "revision-2 development screen, variant [%s], state %s" % (" ".join(ov), st)]
    if st in ("stb", "stbazi"):
        cmd += ["--pre", os.path.join(nd, "tb_isense_stbpre.cir")]
    if not os.path.isdir(os.path.join(here, "results", "%s-%s" % (rid, st))):
        subprocess.call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    rj = json.load(open(os.path.join(here, "results", "%s-%s" % (rid, st), "run.json")))
    if st in ("stbstep", "stbcm"):
        print(st, rj.get("disposition"))
        continue
    pl = rj.get("result", {}); pl = pl.get("per_loop", pl)
    for c in corners.split(","):
        d = pl.get(c, {})
        cm, dm = d.get("cm_out", {}), d.get("dm_out", {}) if st == "stb" else d.get("dm_aux", {})
        hv = rj.get("prerun", {}).get(c, {}).get("holdvals", {})
        ocm = (float(hv["VOP"]) + float(hv["VON"])) / 2 if hv else None
        out.setdefault(c, {})[st] = (cm.get("worst_pm_deg"), cm.get("worst_gm_db"), dm.get("worst_pm_deg"), dm.get("worst_gm_db"), ocm)
print("variant", rid, ov)
print("corner state  CM_PM CM_GM  DM/aux_PM DM/aux_GM  outCM")
for c, d in out.items():
    for st, v in d.items():
        print("%-4s %-7s %s" % (c, st, "  ".join("-" if x is None else "%.3f" % x if i == 4 else "%.1f" % x for i, x in enumerate(v))))
json.dump(out, open(os.path.join(nd, "dev_summary.json"), "w"), indent=1)

#!/usr/bin/env python3
"""Run a long frame-based ADC deck in pieces and restart after a numerical abort (Python 3.6).

ngspice occasionally stops a long transient with "Timestep too small ... cause unrecorded" just after a
comparator evaluation starts; the same frame converts normally in a fresh run (run debug-abort-s2f173). The ADC
has no state that survives a frame (flags, bottom plates, lsb nodes and boost capacitors are reset in every
track phase), so a fresh run that starts at the aborted frame continues the record. Frame f is sampled at
t0 + f us of its own run; codes of frame f are valid if the run reached 1.2 us + f us.

usage: run_resume.py --kind static|dyn --tag TAG --frames N [--first F] --cpu CPU --sub K=V ... --question Q
  static: needs --sub VSTART=<V at frame 0 of the whole record> and VSTEP; each piece gets its own VSTART.
  dyn:    needs FIN; each piece gets TOFF = first frame * 1 us (phase continuity).
Writes <bulk>/r1_adc/<TAG>-merged.txt (absolute frame, codea, codeb) and sim/results/<TAG>_pieces.json.
"""
import argparse
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BLOCK = os.path.dirname(HERE)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--frames", type=int, required=True)
    ap.add_argument("--first", type=int, default=0)
    ap.add_argument("--cpu", required=True)
    ap.add_argument("--sub", action="append", default=[])
    ap.add_argument("--question", default="")
    ap.add_argument("--max-pieces", type=int, default=30)
    a = ap.parse_args()
    bulk = os.path.join(os.environ["G1_RESULTS_ROOT"], "r1_adc")
    subs = dict(kv.split("=", 1) for kv in a.sub)
    deck = "sim/tb_adc_static.cir" if a.kind == "static" else "sim/tb_adc_dyn.cir"
    f0 = a.first
    rows = {}
    pieces = []
    k = 0
    while f0 < a.frames and k < a.max_pieces:
        n = a.frames - f0
        s = dict(subs)
        s["TSTOP"] = "%.3fu" % (1.2 + n - 1)
        if a.kind == "static":
            s["VSTART"] = "%.7f" % (float(subs["VSTART"]) + f0 * float(subs["VSTEP"]))
        else:
            s["TOFF"] = "%gu" % f0
        rid = "%s-p%02d" % (a.tag, k)
        cmd = [sys.executable, os.path.join(HERE, "run_ngspice.py"), "--deck", deck, "--run-id", rid,
               "--cpuset", a.cpu, "--timeout", "30000",
               "--question", "%s (piece %d, frames %d..%d of %s)" % (a.question, k, f0, a.frames - 1, a.tag)]
        for kk, vv in s.items():
            cmd += ["--sub", "%s=%s" % (kk, vv)]
        subprocess.call(cmd, cwd=BLOCK)
        log = open(os.path.join(BLOCK, "sim", "runs", rid, "ngspice.log"), errors="replace").read()
        m = re.search(r"Timestep too small; time = ([0-9.eE+-]+)", log)
        t_end = float(m.group(1)) if m else 1e9
        path = os.path.join(bulk, rid, "codes.txt")
        got = 0
        if os.path.exists(path):
            for line in open(path):
                p = line.split()
                try:
                    t, ca, cb = float(p[0]), float(p[1]), float(p[2])
                except (ValueError, IndexError):
                    continue
                f = int(round((t - 1.2e-6) / 1e-6))
                if t < t_end and f < n:
                    rows[f0 + f] = (int(round(ca)), int(round(cb)))
                    got += 1
        aborted = m is not None
        if aborted:
            f_ab = int((t_end - 0.25e-6) // 1e-6)       # frame in conversion at the abort
            nxt = f0 + f_ab
        else:
            nxt = f0 + n if got >= n else f0 + got
        pieces.append({"run_id": rid, "first_frame": f0, "frames_valid": got, "aborted": aborted,
                       "abort_time_s": t_end if aborted else None, "next_first_frame": nxt})
        rj = os.path.join(BLOCK, "sim", "runs", rid, "run.json")
        j = json.load(open(rj))
        j["result"] = "frames %d..%d valid%s" % (f0, f0 + got - 1, (", aborted at %.6g s (Timestep too small)" % t_end) if aborted else "")
        j["disposition"] = "piece of %s; merged by run_resume.py" % a.tag
        json.dump(j, open(rj, "w"), indent=2)
        if nxt <= f0:
            nxt = f0 + 1                                # no progress at all: skip one frame (recorded)
            pieces[-1]["skipped_frame"] = f0
        f0 = nxt
        k += 1
    with open(os.path.join(bulk, "%s-merged.txt" % a.tag), "w") as f:
        f.write("frame codea codeb\n")
        for fr in sorted(rows):
            f.write("%d %d %d\n" % (fr, rows[fr][0], rows[fr][1]))
    missing = [fr for fr in range(a.first, a.frames) if fr not in rows]
    out = {"tag": a.tag, "kind": a.kind, "frames": a.frames, "frames_valid": len(rows), "missing_frames": missing,
           "pieces": pieces}
    json.dump(out, open(os.path.join(HERE, "results", "%s_pieces.json" % a.tag), "w"), indent=1)
    print(json.dumps({kk: v for kk, v in out.items() if kk != "pieces"}))


if __name__ == "__main__":
    main()

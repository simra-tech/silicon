#!/usr/bin/env python3
"""Collect MC lines from tb_isense_mc logs; statistics of raw offset, residual offset after AZ, pedestal, gain.
Revision 2 (2026-10-21): also the output common mode (V) per sample at 7.4 us (after AZ, pedestal on, zero shunt current),
read from the raw waveform files <corner>_mc_<i> (columns time v(outp) v(outn) ...)."""
import sys, os, json, glob, statistics as st
rdir, tdir = sys.argv[1], sys.argv[2]
rows = []
for f in sorted(glob.glob(os.path.join(rdir, "*.log"))):
    corner = os.path.basename(f)[len("tb_isense_mc_"):-4]
    for line in open(f, errors="replace"):
        if line.startswith("MC "):
            p = line.replace("=", " = ").split()
            d = {"corner": corner}
            for k in ("raw_uV", "res_uV", "ped_mV", "gain"):
                try: d[k] = float(p[p.index(k) + 2])
                except (ValueError, IndexError): d[k] = None
            try:
                idx = int(p[1])
                wf = os.path.join(rdir, "%s_mc_%d" % (corner, idx))
                last = None
                for l2 in open(wf):
                    a2 = l2.split()
                    try:
                        if float(a2[0]) <= 7.4e-6: last = a2
                        else: break
                    except (ValueError, IndexError): pass
                d["ocm_V"] = (float(last[1]) + float(last[2])) / 2
            except Exception:
                d["ocm_V"] = None
            rows.append(d)
def stats(key, sel=None):
    v = [r[key] for r in rows if r[key] is not None and (sel is None or r["corner"].startswith(sel))]
    if not v: return None
    return {"n": len(v), "mean": st.mean(v), "sigma": st.pstdev(v), "min": min(v), "max": max(v), "max_abs": max(abs(x) for x in v)}
groups = sorted(set(r["corner"].split("_s")[0] for r in rows))
res = {}
for g in groups:
    res[g] = {k: stats(k, g) for k in ("raw_uV", "res_uV", "ped_mV", "gain", "ocm_V")}
    res[g]["ocm_within_30mV"] = sum(1 for r in rows if r["corner"].startswith(g) and r.get("ocm_V") is not None and abs(r["ocm_V"] - 0.6) <= 0.03)
    res[g]["res_within_100uV"] = sum(1 for r in rows if r["corner"].startswith(g) and r["res_uV"] is not None and abs(r["res_uV"]) <= 100)
summ = {"result": res, "criterion": "residual input-referred offset after AZ |res| <= 100 uV in every sample",
        "disposition": "; ".join("%s: %d/%d samples within 100 uV" % (g, res[g]["res_within_100uV"], res[g]["res_uV"]["n"] if res[g]["res_uV"] else 0) for g in groups),
        "samples": rows}
json.dump(summ, open(os.path.join(tdir, "summary.json"), "w"), indent=1)
print(json.dumps({k: v for k, v in summ.items() if k != "samples"}, indent=1))

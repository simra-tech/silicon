#!/usr/bin/env python3
"""Analyse tb_isense_azloop: unity-gain frequency, phase margin and gain margin of the AZ loop (differential and CM).
Usage: analyze_azloop.py RAW_DIR TREE_DIR  (also updates TREE_DIR/run.json result/disposition if it exists)."""
import sys, os, json, glob, math
rdir, tdir = sys.argv[1], sys.argv[2]
def load(f):
    with open(f) as fh:
        hdr = fh.readline().split()
        return [[float(x) for x in l.split()] for l in fh if len(l.split()) == len(hdr)]
def margins(rows):
    # columns: freq tdb freq tph (wr_singlescale writes the scale once: freq tdb tph)
    f = [r[0] for r in rows]; db = [r[1] for r in rows]; ph = [r[-1] for r in rows]
    # unwrap phase
    u = [ph[0]]
    for p in ph[1:]:
        q = p
        while q - u[-1] > 180: q -= 360
        while q - u[-1] < -180: q += 360
        u.append(q)
    res = {"dc_gain_dB": db[0], "phase_at_dc_deg": u[0]}
    fu = None
    for i in range(1, len(f)):
        if db[i - 1] > 0 >= db[i]:
            a = db[i - 1] / (db[i - 1] - db[i]); fu = f[i - 1] * (f[i] / f[i - 1]) ** a; pu = u[i - 1] + a * (u[i] - u[i - 1]); break
    res["max_gain_dB"] = max(db)
    if fu is None:
        res.update({"f_unity_Hz": None, "phase_margin_deg": None, "note": "loop gain below 0 dB at all frequencies (no loop to destabilise)" if max(db) < 0 else "no 0 dB crossing found"}); return res
    # T = -(return)/(injected): loop gain with the negative-feedback sign removed; PM = 180 + phase(T) relative to its DC phase 0
    pm = 180 + (pu - u[0])
    gm = None
    for i in range(1, len(f)):
        if f[i] > fu and (u[i] - u[0]) <= -180 < (u[i - 1] - u[0]):
            gm = -db[i]; break
    res.update({"f_unity_Hz": fu, "phase_margin_deg": pm, "gain_margin_dB": gm})
    return res
out = {}
for f in sorted(glob.glob(os.path.join(rdir, "*_dm.txt"))):
    c = os.path.basename(f)[len("tb_isense_azloop_"):-len("_dm.txt")] if os.path.basename(f).startswith("tb_isense_azloop_") else os.path.basename(f)[:-len("_dm.txt")]
    out[c] = {"dm": margins(load(f)), "cm": margins(load(f[:-6] + "cm.txt"))}
LIM = 45.0
okm = lambda r: (r["phase_margin_deg"] is not None and r["phase_margin_deg"] >= LIM) or (r["f_unity_Hz"] is None and r["max_gain_dB"] < 0)
ok = out and all(okm(v[m]) for v in out.values() for m in ("dm", "cm"))
pms = [v[m]["phase_margin_deg"] for v in out.values() for m in ("dm", "cm") if v[m]["phase_margin_deg"] is not None]
summ = {"result": out, "criterion": "phase margin >= %g deg at every corner, differential and common mode (a mode whose loop gain stays below 0 dB at all frequencies passes)" % LIM,
        "disposition": "%s: differential AZ loop worst phase margin %.1f deg, unity gain %.2f-%.2f MHz, DC loop gain >= %.1f dB over %d corners; common mode: loop gain <= %.1f dB (no loop)" % ("passed" if ok else "failed", min(pms) if pms else -1,
        min(v["dm"]["f_unity_Hz"] for v in out.values()) / 1e6, max(v["dm"]["f_unity_Hz"] for v in out.values()) / 1e6, min(v["dm"]["dc_gain_dB"] for v in out.values()), len(out), max(v["cm"]["max_gain_dB"] for v in out.values()))}
json.dump(summ, open(os.path.join(tdir, "summary.json"), "w"), indent=1)
rp = os.path.join(tdir, "run.json")
if os.path.exists(rp):
    r = json.load(open(rp)); r["result"] = out; r["disposition"] = summ["disposition"]; r["analyzer"] = "sim/analyze_azloop.py (run after the deck)"
    json.dump(r, open(rp, "w"), indent=1, sort_keys=True)
print(json.dumps(summ, indent=1))

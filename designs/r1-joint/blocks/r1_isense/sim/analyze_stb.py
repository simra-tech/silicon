#!/usr/bin/env python3
"""Analyse the stb suite (tb_isense_stb.cir normal state, tb_isense_stbaz.cir AZ closed state): phase and gain margin
per corner, shunt level and loop from the Tian loop-gain files <corner>_t<10*level_index+loop> (columns f dB f phase).
Margin logic as r1_afe/sim/run_afe.py stb_post (worst unity crossing, worst -180 crossing, RHP flag).
Usage: analyze_stb.py RAW_DIR TREE_DIR   (state and levels are read from the deck copy in RAW_DIR)."""
import sys, os, json, glob, re
rdir, tdir = sys.argv[1], sys.argv[2]
PM_MIN, GM_MIN = 60.0, 10.0
azi = bool(glob.glob(os.path.join(rdir, "tb_isense_stbazi_*.cir")))   # intermediate state az = 1, azh = 0 (revision 2)
az = azi or bool(glob.glob(os.path.join(rdir, "tb_isense_stbaz_*.cir")))
STATE = "az1_azh0" if azi else ("az_closed" if az else "normal")
LOOPS = {1: "dm_out", 2: "cm_out", 3: "cmfb", 4: "dm_in", 5: "cm_in", 6: "dm_aux", 7: "cm_aux",
         8: "dm_vso", 9: "cm_vso"}   # 8/9: Tian probe in the output-stage vss return (layout c, layout/tools/vss_tools.py)
INFO = {"cmfb"}                                  # informational: not a valid Nyquist break (other loops closed)
LEVELS = [0.0] if az else [0.0, 0.1, -0.02]       # order of the foreach in the deck
def margins(p):
    f, g, ph = [], [], []
    for l in open(p):
        a = l.split()
        try: f.append(float(a[0])); g.append(float(a[1])); ph.append(float(a[3]))
        except (ValueError, IndexError): pass
    off = 360.0 * round(ph[0] / 360.0); ph = [x - off for x in ph]
    pm = fu = gm = f180 = None
    for i in range(1, len(f)):
        if g[i - 1] >= 0 > g[i]:
            a = g[i - 1] / (g[i - 1] - g[i]); fx = f[i - 1] * (f[i] / f[i - 1]) ** a
            m = 180 + ph[i - 1] + a * (ph[i] - ph[i - 1])
            if pm is None or m < pm: pm, fu = m, fx
        for lim in (-180.0, -540.0):
            if (ph[i - 1] - lim) * (ph[i] - lim) < 0:
                a = (ph[i - 1] - lim) / (ph[i - 1] - ph[i]); gx = g[i - 1] + a * (g[i] - g[i - 1])
                if gm is None or -gx < gm: gm, f180 = -gx, f[i - 1] * (f[i] / f[i - 1]) ** a
    icr = max([i for i in range(len(f)) if fu is None or f[i] <= fu] or [0])
    rhp = max(ph[:icr + 1]) - ph[0] > 30.0
    r = dict(t_dc_db=round(g[0], 2), t_max_db=round(max(g), 2), phase_dc_deg=round(ph[0], 1), f_unity_Hz=fu, pm_valid=bool(not rhp and (pm is None or pm <= 180)),
             pm_deg=None if pm is None else round(pm, 2), gm_db=None if gm is None else round(gm, 2), f_180_Hz=f180, ph_min_deg=round(min(ph), 1))
    if max(g) < 0:
        r["status"] = "not applicable (loop gain below 0 dB at all frequencies)"
    elif not r["pm_valid"]:
        r["status"] = "not applicable (pm_valid = false)" if LOOPS_NAME_INFO(r) else "failed (right-half-plane / invalid)"
    else:
        ok = pm is not None and pm >= PM_MIN and (gm is None or gm >= GM_MIN)
        r["status"] = "passed" if ok else "failed"
    return r
def LOOPS_NAME_INFO(r): return False
out = {}
for c in sorted(set(os.path.basename(x).split("_t")[0] for x in glob.glob(os.path.join(rdir, "*_t[0-9]*")))):
    out[c] = {}
    for li, lv in enumerate(LEVELS):
        for lp, name in LOOPS.items():
            p = os.path.join(rdir, "%s_t%d" % (c, 10 * li + lp))
            if os.path.exists(p):
                r = margins(p)
                if name in INFO:
                    r["status"] = "informational (" + r["status"] + ")"
                out[c].setdefault(name, {})["vsh_%+.3f" % lv] = r
# per corner and loop: worst PM and GM over levels, status
summ = {}
for c, d in out.items():
    summ[c] = {}
    for name, lv in d.items():
        rows = list(lv.values())
        pms = [r["pm_deg"] for r in rows if r["pm_deg"] is not None]; gms = [r["gm_db"] for r in rows if r["gm_db"] is not None]
        st = [r["status"] for r in rows]
        status = "failed" if any(s.startswith("failed") for s in st) else ("passed" if all(s == "passed" for s in st) else
                 ("not applicable" if all(s.startswith("not applicable") for s in st) else ("informational" if name in INFO else "mixed: " + "; ".join(sorted(set(st))))))
        summ[c][name] = dict(status=status, worst_pm_deg=min(pms) if pms else None, worst_gm_db=min(gms) if gms else None,
                             max_t_db=max(r["t_max_db"] for r in rows), f_unity_Hz=[r["f_unity_Hz"] for r in rows])
tab = ["corner loop status worst_PM worst_GM max_T_dB"]
for c, d in summ.items():
    for n, r in d.items():
        tab.append("%s %s %s %s %s %s" % (c, n, r["status"], r["worst_pm_deg"], r["worst_gm_db"], r["max_t_db"]))
valid = [r["status"] for d in summ.values() for n, r in d.items() if n not in INFO]
disp = "%s: state %s, %d corners; %d loop results passed, %d failed, %d not applicable; criterion PM >= %g deg, GM >= %g dB" % (
    "failed" if any(v.startswith("failed") or v.startswith("mixed") for v in valid) else "passed", {"az1_azh0": "az = 1, azh = 0", "az_closed": "AZ closed", "normal": "normal"}[STATE],
    len(summ), sum(v == "passed" for v in valid), sum(v.startswith("failed") or v.startswith("mixed") for v in valid), sum(v.startswith("not applicable") for v in valid), PM_MIN, GM_MIN)
res = {"result": {"state": STATE, "margins": out, "per_loop": summ}, "criterion": "PM >= 60 deg and GM >= 10 dB per loop, corner and shunt level; informational loops excluded",
       "disposition": disp}
json.dump(res, open(os.path.join(tdir, "summary.json"), "w"), indent=1)
rp = os.path.join(tdir, "run.json")
if os.path.exists(rp):
    r = json.load(open(rp)); r["result"] = res["result"]["per_loop"]; r["disposition"] = disp
    json.dump(r, open(rp, "w"), indent=1, sort_keys=True)
print("\n".join(tab)); print(disp)

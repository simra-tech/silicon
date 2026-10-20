#!/usr/bin/env python3
"""r1_safe revision 3: model of the r1_ctrl offset-calibration search on DC mismatch MC data (tb_safe_dcmc3).

For each MC draw (one comparator), the DC MC gives trip (up) and release (dn) input points at 13 cell thresholds T.
They are interpolated (linear in T) to any threshold. The threshold DAC (ideal ratios; string mismatch is covered by
the transient MC tb_safe_mc3) is
    T(c, k) = (2c - 63)/63 * VREF + (k - 32) * VREF/252          c = cell threshold code, k = calibration code 0..63
Calibration (during the zero-current window): the input is the zero-current sense output, Vcal = -14*VREF/26 (OC
cell) or +14*VREF/26 (NEG cell frame). ctrl sets c0 = 14 (OC) / 49 (NEG cell code), then
    ascending  k = 0..63 (output starts high):  k_rel  = first k with dn(T(c0,k)) > Vcal   (output falls)
    descending k = 63..0 (output starts low):   k_trip = first k with up(T(c0,k)) < Vcal   (output rises)
    k_est = (k_rel + k_trip)/2 ;  k_ideal = 32 + (Vcal - T(c0,32)) * 252/VREF  (ratio constant, 36.31 / 27.69)
    k_cal = 32 + round(k_est - k_ideal)          (saturates at 0/63 -> "outside range")
Operation: residual(c) = centre(T(c, k_cal)) - T(c, 32), centre = (up + dn)/2, in LSB = 2*VREF/63.
Usage: python3 cal_model.py OUT_DIR RUN_ID [RUN_ID ...]   (run ids under sim/results/, first = netlist of record)
"""
import sys, os, json, math, hashlib, datetime, statistics as st
import numpy as np
VREF = 1.05; LSB = 2 * VREF / 63; STEP = VREF / 252; G = 14.0
here = os.path.dirname(os.path.abspath(__file__))
T = lambda c, k: (2 * c - 63) / 63 * VREF + (k - 32) * STEP
ROLES = {"OC": {"vcal": -G * VREF / 26, "c0": 14, "codes": [24, 32, 39, 54, 59]},
         "NEG": {"vcal": +G * VREF / 26, "c0": 49, "codes": [54, 59]}}
ALL_CODES = [4, 9, 24, 32, 39, 54, 59]            # measured grid thresholds (cell frame)
# OC useful range: Vod from zero current (-0.565 V) to the isense limit (+0.84 V) -> codes 15..56 (measured: 24..54, 59 kept as the end);
# NEG useful range (cell frame): negative shunt current, thr_neg 4..14 -> cell codes 49..59 (measured: 54, 59)
def model(rows):
    out = []
    for r in rows:
        p = [q for q in r["pts"] if q["up_V"] is not None and q["dn_V"] is not None]
        th = np.array([q["th_V"] for q in p]); eu = np.array([q["up_V"] - q["th_V"] for q in p]); ed = np.array([q["dn_V"] - q["th_V"] for q in p])
        up = lambda t: t + np.interp(t, th, eu); dn = lambda t: t + np.interp(t, th, ed)
        ctr = lambda t: (up(t) + dn(t)) / 2
        d = {"sample": r["sample"]}
        for role, R in ROLES.items():
            vc, c0 = R["vcal"], R["c0"]
            k_rel = next((k for k in range(64) if dn(T(c0, k)) > vc), None)
            k_trip = next((k for k in range(63, -1, -1) if up(T(c0, k)) < vc), None)
            k_ideal = 32 + (vc - T(c0, 32)) / STEP
            raw_err_mV = (ctr(vc) - vc) * 1e3          # uncalibrated offset at the cal point (approx: centre at T = Vcal)
            if k_rel is None or k_trip is None:
                d[role] = {"in_range": False, "raw_err_mV": raw_err_mV}; continue
            k_est = (k_rel + k_trip) / 2
            kc = 32 + int(math.floor(k_est - k_ideal + 0.5))
            sat = kc < 0 or kc > 63
            kc = min(63, max(0, kc))
            resid = {c: (ctr(T(c, kc)) - T(c, 32)) / LSB for c in ALL_CODES}
            rawc = {c: (ctr(T(c, 32)) - T(c, 32)) / LSB for c in ALL_CODES}
            d[role] = {"in_range": not sat, "k_rel": k_rel, "k_trip": k_trip, "k_ideal": k_ideal, "k_cal": kc,
                       "cal_shift_LSB": (kc - 32) * STEP / LSB, "raw_err_mV": raw_err_mV,
                       "raw_LSB": rawc, "resid_LSB": resid,
                       "max_resid_role_LSB": max(abs(resid[c]) for c in R["codes"]),
                       "max_resid_all_LSB": max(abs(v) for v in resid.values())}
        out.append(d)
    return out
def stats(rows, run):
    n = len(rows); res = {"run": run, "samples": n}
    for role in ROLES:
        q = [r[role] for r in rows]
        ok = [x for x in q if x["in_range"]]
        mr = [x["max_resid_role_LSB"] for x in ok]; ma = [x["max_resid_all_LSB"] for x in ok]
        sh = [x["cal_shift_LSB"] for x in ok]
        raw_all = [abs(v) for x in ok for v in x["raw_LSB"].values()]
        res[role] = {"in_range": len(ok), "outside_range": [r["sample"] for r in rows if not r[role]["in_range"]],
                     "pass_role_range_0p25": sum(1 for v in mr if v <= 0.25), "pass_all_codes_0p25": sum(1 for v in ma if v <= 0.25),
                     "worst_resid_role_LSB": max(mr) if mr else None, "worst_resid_all_LSB": max(ma) if ma else None,
                     "resid_sigma_all_LSB": float(np.std([v for x in ok for v in x["resid_LSB"].values()])) if ok else None,
                     "cal_shift_LSB_min_max": [min(sh), max(sh)] if sh else None, "cal_range_LSB": [-32 * STEP / LSB, 31 * STEP / LSB],
                     "raw_max_abs_LSB": max(raw_all) if raw_all else None,
                     "worst_samples_role": sorted(((x["max_resid_role_LSB"], r["sample"]) for r, x in zip(rows, q) if x["in_range"]), reverse=True)[:3]}
    return res
def main():
    odir = sys.argv[1]; os.makedirs(odir, exist_ok=True)
    allres, inputs = [], {}
    for run in sys.argv[2:]:
        sp = os.path.join(here, "results", run, "summary.json")
        inputs[run] = hashlib.sha256(open(sp, "rb").read()).hexdigest()
        rows = json.load(open(sp))["samples"]
        m = model(rows)
        s = stats(m, run); s["per_sample"] = m
        allres.append(s)
        print(run, json.dumps({k: {kk: vv for kk, vv in v.items() if kk not in ("worst_samples_role",)} if isinstance(v, dict) else v for k, v in s.items() if k != "per_sample"}))
    rec = allres[0]
    need = 50 if rec["samples"] == 51 else rec["samples"]          # MC: >= 50/51; nominal corner runs: every corner
    ok = all(rec[r]["pass_role_range_0p25"] >= need and not rec[r]["outside_range"] for r in ROLES)
    disp = "%s (%s): OC %d/%d and NEG %d/%d samples within 0.25 LSB over their role ranges; all codes 4..59: OC %d, NEG %d; outside cal range: %d / %d; cal shift used %s / %s LSB of +-4" % (
        "passed" if ok else "failed", rec["run"], rec["OC"]["pass_role_range_0p25"], rec["samples"], rec["NEG"]["pass_role_range_0p25"], rec["samples"],
        rec["OC"]["pass_all_codes_0p25"], rec["NEG"]["pass_all_codes_0p25"], len(rec["OC"]["outside_range"]), len(rec["NEG"]["outside_range"]),
        ["%.2f" % v for v in rec["OC"]["cal_shift_LSB_min_max"]], ["%.2f" % v for v in rec["NEG"]["cal_shift_LSB_min_max"]])
    summ = {"criterion": "after the modelled search, residual threshold (hysteresis-centre) error <= 0.25 LSB (8.33 mV Vod) at every evaluated code of the role range in >= 50/51 samples; no sample outside the calibration range",
            "model": __doc__.strip().splitlines()[0], "result": [{k: v for k, v in s.items() if k != "per_sample"} for s in allres],
            "disposition": disp, "per_sample": {s["run"]: s["per_sample"] for s in allres}}
    json.dump(summ, open(os.path.join(odir, "summary.json"), "w"), indent=1, default=float)
    run = {"run_id": os.path.basename(odir.rstrip("/")), "block": "r1_safe", "date_utc": datetime.datetime.utcnow().isoformat() + "Z",
           "command": "python3 sim/cal_model.py " + " ".join(["sim/results/" + os.path.basename(odir.rstrip("/"))] + sys.argv[2:]),
           "tool": "python3 %s, numpy %s (host)" % (sys.version.split()[0], np.__version__), "inputs_summary_sha256": inputs,
           "script_sha256": hashlib.sha256(open(os.path.abspath(__file__), "rb").read()).hexdigest(),
           "question": "Does a 6-bit calibration code (step VREF/252 = LSB/8, range -4..+3.9 LSB) found by the zero-current search bring every comparator threshold within 0.25 LSB?",
           "result": summ["result"], "disposition": disp, "raw_results": "none (model on the DC MC summaries)"}
    json.dump(run, open(os.path.join(odir, "run.json"), "w"), indent=1, default=float)
    print(disp)
main()

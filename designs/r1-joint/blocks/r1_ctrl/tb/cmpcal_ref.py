#!/usr/bin/env python3
"""r1_ctrl revision 0.3: model of the r1_cmpcal two-sided calibration search, checked against r1_safe sim/cal_model.py.

Comparator (cell frame, as in r1_safe sim/cal_model.py): input Vcal (zero-current sense output), threshold
T(c0, k) = (2*c0 - 63)/63 * VREF + (k - 32) * VREF/252, trip point up(T), release point dn(T) interpolated from the DC
MC data. Output state s: s = 1 if up(T) < Vcal; s = 0 if dn(T) > Vcal; else s holds (hysteresis).

RTL search (rtl/r1_cmpcal.v, revision 0.3), all four comparators in parallel, one decision per zero-current window:
  pass R (release side): per window apply the preset code 0 (output forced high), then the probe code, sample f = s.
  pass T (trip side):    per window apply the preset code 63 (output forced low), then the probe code, sample f = s.
  Each pass: 6-bit successive approximation (start 32; f = 1 keeps the bit) + 1 check window -> code = largest k with
  f = 1; EXH if (code == 63 and f == 1) or (code == 0 and f == 0).
  pass R: f = 1 <=> dn(T(k)) <= Vcal, so k_rel = a + 1;  pass T: f = 1 <=> up(T(k)) < Vcal, so k_trip = b.
  S = a + 1 + b (7 bit);  result
     variant "half" (implemented):   cal = 32 + floor((S - IDEAL2) / 2),   IDEAL2 = floor(2 * k_ideal) = 72 (OC) / 55 (NEG)
     variant "int6" (brief wording): cal = 32 + floor((S + 1) / 2) - IDEAL,  IDEAL = 36 (OC) / 28 (NEG)
  saturated to 0..63 with EXH.
Reference (r1_safe cal_model.py): k_rel = first k ascending with dn(T) > Vcal, k_trip = first k descending with
up(T) < Vcal, k_cal = 32 + floor((k_rel + k_trip)/2 - k_ideal + 0.5), k_ideal = 36.31 (OC) / 27.69 (NEG).
Criterion (brief): both models give the same k_cal within 1 code on every sample.

Usage:
  python3 cmpcal_ref.py model OUT_DIR SAFE_RESULTS_DIR   -> summary.json, cmpcal_vec.txt (vectors for tb_top +test=calmc)
  python3 cmpcal_ref.py check OUT_DIR                     -> compares the RTL results (calmc_rtl.txt) with the model
"""
import sys, os, json, math, hashlib
import numpy as np

VREF = 1.05; STEP = VREF / 252; LSB = 2 * VREF / 63; G = 14.0
T = lambda c, k: (2 * c - 63) / 63 * VREF + (k - 32) * STEP
ROLES = {"OC": {"vcal": -G * VREF / 26, "c0": 14, "ideal2": 72, "ideal6": 36},
         "NEG": {"vcal": +G * VREF / 26, "c0": 49, "ideal2": 55, "ideal6": 28}}
DC_RUNS = ["safe-dcmc-20261020-r3rppd", "safe-dcmc-20261020-r3", "safe-dccorner-20261020-r3"]
TR_RUN = "safe-mc-20261020-r3"          # transient full-path MC: in-sample k_rel / k_trip only


def kideal(role):
    R = ROLES[role]
    return 32 + (R["vcal"] - T(R["c0"], 32)) / STEP


def ref_kcal(krel, ktrip, role):
    """r1_safe cal_model.py formula (unchanged)."""
    if krel is None or ktrip is None:
        return None, False
    kc = 32 + int(math.floor((krel + ktrip) / 2 - kideal(role) + 0.5))
    sat = kc < 0 or kc > 63
    return min(63, max(0, kc)), not sat


class Cmp:
    """hysteresis comparator; uf(k) = up(T(c0,k)) - Vcal, df(k) = dn(T(c0,k)) - Vcal (volts)."""
    def __init__(self, uf, df, s=0):
        self.uf, self.df, self.s = uf, df, s

    def apply(self, k):
        if self.uf(k) < 0:
            self.s = 1
        elif self.df(k) > 0:
            self.s = 0
        return self.s


def rtl_pass(cmp, preset):
    code, wins = 32, 0
    for bit in range(5, -1, -1):
        cmp.apply(preset); f = cmp.apply(code); wins += 1
        if not f:
            code &= ~(1 << bit)
        if bit:
            code |= 1 << (bit - 1)
    cmp.apply(preset); f = cmp.apply(code); wins += 1
    exh = (code == 63 and f == 1) or (code == 0 and f == 0)
    return code, exh, wins


def rtl_search(cmp, role, variant="half"):
    a, ea, w1 = rtl_pass(cmp, 0)
    b, eb, w2 = rtl_pass(cmp, 63)
    S = a + 1 + b
    if variant == "half":
        kc = 32 + ((S - ROLES[role]["ideal2"]) >> 1)          # python >> is floor for negatives
    else:
        kc = 32 + ((S + 1) >> 1) - ROLES[role]["ideal6"]
    sat = kc < 0 or kc > 63
    return {"a": a, "k_rel": a + 1, "k_trip": b, "S": S, "k_cal": min(63, max(0, kc)), "exh": bool(ea or eb or sat),
            "windows": w1 + w2}


def ref_search(uf, df):
    krel = next((k for k in range(64) if df(k) > 0), None)
    ktrip = next((k for k in range(63, -1, -1) if uf(k) < 0), None)
    return krel, ktrip


def dc_funcs(sample, role):
    p = [q for q in sample["pts"] if q["up_V"] is not None and q["dn_V"] is not None]
    th = np.array([q["th_V"] for q in p])
    eu = np.array([q["up_V"] - q["th_V"] for q in p]); ed = np.array([q["dn_V"] - q["th_V"] for q in p])
    R = ROLES[role]
    uf = lambda k: (T(R["c0"], k) + np.interp(T(R["c0"], k), th, eu)) - R["vcal"]
    df = lambda k: (T(R["c0"], k) + np.interp(T(R["c0"], k), th, ed)) - R["vcal"]
    return uf, df


def step_funcs(krel, ktrip):
    """comparator equivalent to an in-sample linear search: release between krel-1 and krel, trip between ktrip and ktrip+1"""
    uf = lambda k: (k - (ktrip + 0.5)) * STEP
    df = lambda k: (k - (krel - 0.5)) * STEP
    return uf, df


def model(out, sres):
    os.makedirs(out, exist_ok=True)
    rows, inputs, vec = [], {}, []
    stored = {}
    cm = os.path.join(sres, "cal-model-20261020-r3", "summary.json")
    if os.path.exists(cm):
        inputs["cal-model-20261020-r3"] = hashlib.sha256(open(cm, "rb").read()).hexdigest()
        for run, lst in json.load(open(cm))["per_sample"].items():
            for d in lst:
                for role in ROLES:
                    if d[role].get("in_range"):
                        stored[(run, d["sample"], role)] = d[role]["k_cal"]
    cmc = os.path.join(sres, "cal-model-corner-20261020-r3", "summary.json")
    if os.path.exists(cmc):
        inputs["cal-model-corner-20261020-r3"] = hashlib.sha256(open(cmc, "rb").read()).hexdigest()
        for run, lst in json.load(open(cmc))["per_sample"].items():
            for d in lst:
                for role in ROLES:
                    if d[role].get("in_range"):
                        stored[(run, d["sample"], role)] = d[role]["k_cal"]

    def one(run, sname, role, uf, df):
        krel, ktrip = ref_search(uf, df)
        kref, inr = ref_kcal(krel, ktrip, role)
        r = {"run": run, "sample": sname, "role": role, "ref_k_rel": krel, "ref_k_trip": ktrip, "ref_k_cal": kref,
             "ref_in_range": inr, "stored_k_cal": stored.get((run, sname, role))}
        for v in ("half", "int6"):
            for s0 in (0, 1):                          # initial comparator state must not matter
                q = rtl_search(Cmp(uf, df, s0), role, v)
                r["%s_s%d" % (v, s0)] = q
        rows.append(r)
        # vectors for the RTL testbench: per code k, the trip/release offsets in calibration steps
        vec.append((run, sname, role, [uf(k) / STEP for k in range(64)], [df(k) / STEP for k in range(64)],
                    r["half_s0"]["k_cal"], int(r["half_s0"]["exh"])))

    for run in DC_RUNS:
        sp = os.path.join(sres, run, "summary.json")
        inputs[run] = hashlib.sha256(open(sp, "rb").read()).hexdigest()
        for s in json.load(open(sp))["samples"]:
            for role in ROLES:
                uf, df = dc_funcs(s, role)
                one(run, s["sample"], role, uf, df)
    sp = os.path.join(sres, TR_RUN, "summary.json")
    inputs[TR_RUN] = hashlib.sha256(open(sp, "rb").read()).hexdigest()
    for s in json.load(open(sp))["per_sample"]:
        for role, pre in (("OC", "oc"), ("NEG", "ng")):
            kr, kt = s.get(pre + "_krel"), s.get(pre + "_ktrip")
            if kr is None or kt is None:
                continue
            uf, df = step_funcs(int(kr), int(kt))
            one(TR_RUN, s["sample"], role, uf, df)
            rows[-1]["transient_k_cal"] = s.get(pre + "_kc")

    # agreement statistics
    res = {}
    for v in ("half", "int6"):
        d = {"n": 0, "exact": 0, "within1": 0, "worse": [], "s0_s1_differ": 0, "exh_mismatch": 0,
             "krel_ktrip_mismatch": 0}
        for r in rows:
            q, q1 = r[v + "_s0"], r[v + "_s1"]
            d["n"] += 1
            if (q["k_cal"], q["exh"]) != (q1["k_cal"], q1["exh"]):
                d["s0_s1_differ"] += 1
            if q["exh"] != (not r["ref_in_range"]):
                d["exh_mismatch"] += 1
            if (q["k_rel"], q["k_trip"]) != (r["ref_k_rel"], r["ref_k_trip"]) and r["ref_in_range"]:
                d["krel_ktrip_mismatch"] += 1
            if r["ref_k_cal"] is None:
                continue
            dk = abs(q["k_cal"] - r["ref_k_cal"])
            d["exact"] += dk == 0
            d["within1"] += dk <= 1
            if dk > 1:
                d["worse"].append((r["run"], r["sample"], r["role"], q["k_cal"], r["ref_k_cal"]))
        res[v] = d
    st = {"stored_vs_recomputed_mismatch": sum(1 for r in rows if r["stored_k_cal"] is not None and r["stored_k_cal"] != r["ref_k_cal"]),
          "stored_compared": sum(1 for r in rows if r["stored_k_cal"] is not None),
          "transient_vs_recomputed_mismatch": sum(1 for r in rows if r.get("transient_k_cal") is not None and int(r["transient_k_cal"]) != r["ref_k_cal"]),
          "transient_compared": sum(1 for r in rows if r.get("transient_k_cal") is not None)}
    h = res["half"]
    ok = h["within1"] == h["n"] - sum(1 for r in rows if r["ref_k_cal"] is None) and h["exh_mismatch"] == 0 and h["s0_s1_differ"] == 0
    disp = ("%s: implemented search (half-code CAL_IDEAL) vs r1_safe cal_model on %d comparator samples: exact %d, within 1 code %d, "
            "EXH mismatches %d, initial-state dependence %d; brief wording (6-bit integer CAL_IDEAL): exact %d, within 1 %d. "
            "cal_model stored k_cal reproduced on %d/%d, transient in-sample k_cal reproduced on %d/%d") % (
        "passed" if ok else "failed", h["n"], h["exact"], h["within1"], h["exh_mismatch"], h["s0_s1_differ"],
        res["int6"]["exact"], res["int6"]["within1"],
        st["stored_compared"] - st["stored_vs_recomputed_mismatch"], st["stored_compared"],
        st["transient_compared"] - st["transient_vs_recomputed_mismatch"], st["transient_compared"])
    summ = {"criterion": "same k_cal as r1_safe cal_model.py within 1 code on every sample; same out-of-range decision",
            "inputs_sha256": inputs, "agreement": res, "reference_checks": st, "disposition": disp,
            "windows_per_search": rows[0]["half_s0"]["windows"], "per_sample": rows}
    json.dump(summ, open(os.path.join(out, "cmpcal_model.json"), "w"), indent=1, default=float)
    with open(os.path.join(out, "cmpcal_vec.txt"), "w") as f:
        f.write("%d\n" % len(vec))
        for run, sname, role, u, d, kc, ex in vec:
            f.write("%d %d %d\n" % (0 if role == "OC" else 1, kc, ex))
            f.write(" ".join("%.4f" % x for x in u) + "\n")
            f.write(" ".join("%.4f" % x for x in d) + "\n")
    with open(os.path.join(out, "cmpcal_vec_index.txt"), "w") as f:
        for i, (run, sname, role, u, d, kc, ex) in enumerate(vec):
            f.write("%d %s %s %s %d %d\n" % (i, run, sname, role, kc, ex))
    print(disp)
    return 0 if ok else 1


def check(out):
    idx = [l.split() for l in open(os.path.join(out, "cmpcal_vec_index.txt"))]
    rtl = {}
    for l in open(os.path.join(out, "calmc_rtl.txt")):
        p = l.split()
        if p and p[0] == "R":
            rtl[int(p[1])] = (int(p[2]), int(p[3]))
    m = json.load(open(os.path.join(out, "cmpcal_model.json")))["per_sample"]
    n = len(idx); bad = []; within1 = 0; nref = 0
    for i, run, sname, role, kc, ex in idx:
        i = int(i)
        if i not in rtl or rtl[i] != (int(kc), int(ex)):
            bad.append((i, run, sname, role, rtl.get(i), (int(kc), int(ex))))
        r = m[i]
        if r["ref_k_cal"] is not None and i in rtl:
            nref += 1
            within1 += abs(rtl[i][0] - r["ref_k_cal"]) <= 1
    ok = not bad and len(rtl) == n
    disp = "%s: RTL (tb_top +test=calmc) vs Python model of the search: %d/%d identical (code and EXH); RTL vs r1_safe cal_model within 1 code: %d/%d" % (
        "passed" if ok else "failed", n - len(bad), n, within1, nref)
    json.dump({"disposition": disp, "mismatches": bad[:50]}, open(os.path.join(out, "calmc_check.json"), "w"), indent=1)
    print(disp)
    for b in bad[:10]:
        print("MISMATCH", b)
    return 0 if ok else 1


if __name__ == "__main__":
    if sys.argv[1] == "model":
        sys.exit(model(sys.argv[2], sys.argv[3]))
    sys.exit(check(sys.argv[2]))

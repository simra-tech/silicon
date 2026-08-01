#!/usr/bin/env python3
"""READ-ONLY-STAGE2-REPLAY-WAVEFORM-ANALYSIS-V1 - guarded parser/runner.

READ-ONLY analysis of the sealed STAGE2-REPLAY-RUNTIME-V1 pair raws
(456aa04d..., 2f2010d2...). No simulation; no design/deck/data/raw edits;
no waveform modification. Fail-closed on any bound-input hash mismatch.

For each arm, over the closed window [2.0e-9, 4.0e-9] s (inclusive), analyses
  IN  = v(div2_p_1) - v(div2_n_1)   (raw columns 191 - 190)
  OUT = v(div4_p)   - v(div4_n)     (raw columns 193 - 192)
and emits, into ONE rectangular TSV:
  - every strict opposite-sign adjacent-sample crossing (both bracket
    samples in the window) with arm, signal, ordinal, direction, bracket
    raw point indices/times/values, and linear-interpolated crossing time
    t_cross = t_i + (t_j - t_i) * v_i / (v_i - v_j);
  - every exact-zero in-window sample (v == 0.0) listed separately
    (kind=ZERO), never double-counted as a crossing.
All counts all-row-recounted from the sealed TSV. Sampled min/max/peak-to-
peak and adjacent crossing intervals reported per (arm, signal).
No pass/fail, causal, compatibility, source-impedance, specification,
signoff, or tape-out claim. O_EXCL outputs.
GUARDED: STAGE2_REPLAY_WAVEFORM_ANALYSIS_V1=1.
"""
import os, sys, re, array, math, hashlib, bisect

if os.environ.get("STAGE2_REPLAY_WAVEFORM_ANALYSIS_V1") != "1":
    print("GUARDED: STAGE2_REPLAY_WAVEFORM_ANALYSIS_V1=1 marker required; no write.")
    sys.exit(1)

BASE = "."
V1D = BASE + "/NGSPICE46-P1-CML-DIV2-CML-DIV4-STAGE2-REPLAY-RUNTIME-V1"
V3D = BASE + "/NGSPICE46-P1-CML-DIV2-CML-DIV4-STAGE2-REPLAY-RUNTIME-V3-CORRECTION-OF-CORRECTION"
PKG = BASE + "/NGSPICE46-P1-CML-DIV2-CML-DIV4-READ-ONLY-STAGE2-REPLAY-WAVEFORM-ANALYSIS-V1"
P = "NGSPICE46-P1-CML-DIV2-CML-DIV4-READ-ONLY-STAGE2-REPLAY-WAVEFORM-ANALYSIS-V1"
V3P = "NGSPICE46-P1-CML-DIV2-CML-DIV4-STAGE2-REPLAY-RUNTIME-V3-CORRECTION-OF-CORRECTION"

RAW = {
    "UNLOADED": (V1D + "/UNLOADED-RUN/raw_tb_p1_cml_div2_front_unloaded_replay_tran_v2.raw",
                 "456aa04dafc1b8a3023552e31cc1ba1c16fd8c55e04b5171934a7f0670489881"),
    "LOADED": (V1D + "/LOADED-RUN/raw_tb_p1_cml_div2_front_loaded_replay_tran_v2.raw",
               "2f2010d24096030bb0317bf1c774fa16bcb82a61c09eb6f3badca402da357c26"),
}
DECK = {
    "UNLOADED": (V1D + "/UNLOADED-RUN/tb_p1_cml_div2_front_unloaded_replay_tran_v2.cir",
                 "7331ed2ee383c15044a29df4b8bd2f8c2817260f3b2a2ae98b586e68c7a67d2f"),
    "LOADED": (V1D + "/LOADED-RUN/tb_p1_cml_div2_front_loaded_replay_tran_v2.cir",
               "e8ffffeab75e7a75f50a7b1ced2609dfe224a3b9b4930836faffaea1e4082de8"),
}
V3 = [
    (V3D + "/" + V3P + ".log", "cf9638286611366c2d89ebae8349bb45ca3f4b7928b1050ae40f440470aec962"),
    (V3D + "/" + V3P + "-BOUND-INVENTORY.log", "3b3fcdf892e8252daf5e6d9cdb4acb539f298501b009c482cb0d1d0c6805e140"),
    (V3D + "/" + V3P + "-MANIFEST.log", "c2e559283a97a1a40d43a9ac50909b4e01b9d8a9d661c94946be1b21b3ac69f8"),
]

W0, W1 = 2.0e-9, 4.0e-9
SIGNALS = [("IN", 191, 190), ("OUT", 193, 192)]  # (label, plus col, minus col)
NA = "NA"
HEADER = "arm\tsignal\tkind\tordinal\tdirection\ti\tj\tt_i\tt_j\tv_i\tv_j\tt_cross"


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def oexcl(path, text):
    with open(path, "x", encoding="utf-8") as f:
        f.write(text)


def parse_raw(path):
    b = open(path, "rb").read()
    m = b.find(b"Binary:\n")
    if m < 0:
        raise ValueError("no Binary marker")
    hdr = b[:m].decode(errors="replace")
    nv = int(re.search(r"No\. Variables:\s*(\d+)", hdr).group(1))
    np_ = int(re.search(r"No\. Points:\s*(\d+)", hdr).group(1))
    payload = b[m + len(b"Binary:\n"):]
    if len(payload) != nv * np_ * 8:
        raise ValueError("payload length mismatch")
    idx = {}
    for ln in hdr.splitlines():
        mm = re.match(r"^\s*(\d+)\s+(\S+)\s+(\S+)\s*$", ln)
        if mm:
            idx[mm.group(2)] = int(mm.group(1))
    arr = array.array("d")
    arr.frombytes(payload)
    if sys.byteorder != "little":
        arr.byteswap()

    def col(k):
        return [arr[p * nv + k] for p in range(np_)]

    t = col(idx["time"])
    assert all(t[k + 1] > t[k] for k in range(len(t) - 1)), "time not strictly monotonic"
    return nv, np_, t, idx, col


def cross_row(arm, label, ordinal, direction, i, j, ti, tj, vi, vj, tc):
    return "\t".join([arm, label, "CROSS", str(ordinal), direction,
                      str(i), str(j), repr(ti), repr(tj), repr(vi), repr(vj), repr(tc)])


def zero_row(arm, label, ordinal, i, ti, vi):
    return "\t".join([arm, label, "ZERO", str(ordinal), NA,
                      str(i), NA, repr(ti), NA, repr(vi), NA, NA])


if os.path.exists(PKG):
    print("FAIL CLOSED: %s exists" % PKG)
    sys.exit(1)

# fail-closed bound-input verification
for arm, (path, exp) in RAW.items():
    assert sha(path) == exp, f"raw {arm} hash mismatch"
for arm, (path, exp) in DECK.items():
    assert sha(path) == exp, f"deck {arm} hash mismatch"
for path, exp in V3:
    assert sha(path) == exp, f"V3 member hash mismatch: {os.path.basename(path)}"
os.mkdir(PKG)

rows = []
facts = {}   # (arm, label) -> dict(crossings, zeros, mn, mx, p2p, intervals, lo, hi, nwin)
rawfacts = {}  # arm -> dict(npts, nvar, payload, finite)

for arm in ("UNLOADED", "LOADED"):
    nv, np_, t, idx, col = parse_raw(RAW[arm][0])
    payload = nv * np_ * 8
    rawfacts[arm] = dict(npts=np_, nvar=nv, payload=payload)
    lo = bisect.bisect_left(t, W0)
    hi = bisect.bisect_right(t, W1) - 1
    nwin = hi - lo + 1
    for label, kp, km in SIGNALS:
        vp, vm = col(kp), col(km)
        vals = [vp[p] - vm[p] for p in range(np_)]
        assert all(math.isfinite(x) for x in vals), f"{arm} {label} non-finite"
        crossings, zeros = [], []
        rows_cross, rows_zero = [], []
        c_ord, z_ord = 0, 0
        for p in range(lo, hi + 1):
            x = vals[p]
            if x == 0.0:
                z_ord += 1
                zeros.append(p)
                rz = zero_row(arm, label, z_ord, p, t[p], x)
                rows_zero.append(rz)
                rows.append(rz)
            if p < hi:
                y = vals[p + 1]
                if (x < 0.0 and y > 0.0) or (x > 0.0 and y < 0.0):
                    c_ord += 1
                    direction = "POS" if x < 0.0 else "NEG"
                    ti, tj = t[p], t[p + 1]
                    tc = ti + (tj - ti) * x / (x - y)
                    crossings.append((p, p + 1, ti, tj, x, y, tc, direction))
                    rc = cross_row(arm, label, c_ord, direction, p, p + 1,
                                   ti, tj, x, y, tc)
                    rows_cross.append(rc)
                    rows.append(rc)
        wv = vals[lo:hi + 1]
        mn, mx = min(wv), max(wv)
        tcs = [c[6] for c in crossings]
        intervals = [(k + 1, tcs[k], tcs[k + 1], tcs[k + 1] - tcs[k])
                     for k in range(len(tcs) - 1)]
        facts[(arm, label)] = dict(crossings=crossings, zeros=zeros,
                                   rows_cross=rows_cross, rows_zero=rows_zero,
                                   mn=mn, mx=mx, p2p=mx - mn, intervals=intervals,
                                   lo=lo, hi=hi, nwin=nwin,
                                   t_lo=t[lo], t_hi=t[hi])

tsv_text = "\n".join([HEADER] + rows) + "\n"
TSV = PKG + "/" + P + "-FACTS.tsv"
oexcl(TSV, tsv_text)

# all-row recount from the sealed TSV (100% round-trip read-back)
back = open(TSV, encoding="utf-8").read()
assert back == tsv_text, "TSV read-back byte mismatch"
lines = back.splitlines()
assert lines[0] == HEADER
recount = {}
for ln in lines[1:]:
    f = ln.split("\t")
    assert len(f) == 12, "non-rectangular TSV row: %r" % ln
    key = (f[0], f[1], f[2])
    recount[key] = recount.get(key, 0) + 1
tot_cross = tot_zero = 0
for arm in ("UNLOADED", "LOADED"):
    for label, _, _ in SIGNALS:
        k_c = len(facts[(arm, label)]["crossings"])
        k_z = len(facts[(arm, label)]["zeros"])
        assert recount.get((arm, label, "CROSS"), 0) == k_c, (arm, label, "CROSS")
        assert recount.get((arm, label, "ZERO"), 0) == k_z, (arm, label, "ZERO")
        tot_cross += k_c
        tot_zero += k_z
assert len(lines) - 1 == tot_cross + tot_zero

# ---- report ----
R = []
R.append(P + "-REPORT.log")
R.append("Read-only waveform analysis of the sealed STAGE2-REPLAY-RUNTIME-V1 pair")
R.append("(raws 456aa04d..., 2f2010d2...), per Principal Engineer instruction.")
R.append("PROVISIONAL scope (PE statement): zero-source-impedance ideal-drive")
R.append("waveform-sufficiency diagnostic ONLY. No simulation; no design/deck/data/")
R.append("raw edits; no waveform modification.")
R.append("")
R.append("=== bound inputs (CONFIRMED) ===")
R.append("  raw unloaded 456aa04dafc1b8a3023552e31cc1ba1c16fd8c55e04b5171934a7f0670489881")
R.append("  raw loaded   2f2010d24096030bb0317bf1c774fa16bcb82a61c09eb6f3badca402da357c26")
R.append("  deck unloaded 7331ed2ee383c15044a29df4b8bd2f8c2817260f3b2a2ae98b586e68c7a67d2f (tb_p1_cml_div2_front_unloaded_replay_tran_v2.cir)")
R.append("  deck loaded   e8ffffeab75e7a75f50a7b1ced2609dfe224a3b9b4930836faffaea1e4082de8 (tb_p1_cml_div2_front_loaded_replay_tran_v2.cir)")
R.append("  V3-CORRECTION-OF-CORRECTION: note cf9638286611366c2d89ebae8349bb45ca3f4b7928b1050ae40f440470aec962 ;")
R.append("    inventory 3b3fcdf892e8252daf5e6d9cdb4acb539f298501b009c482cb0d1d0c6805e140 ;")
R.append("    manifest c2e559283a97a1a40d43a9ac50909b4e01b9d8a9d661c94946be1b21b3ac69f8")
R.append("  parser (this package, preserved byte-identical) sha256=%s" % sha(sys.argv[0]))
R.append("")
R.append("=== method ===")
R.append("  Signals: IN = v(div2_p_1) - v(div2_n_1) (raw columns 191 - 190);")
R.append("           OUT = v(div4_p) - v(div4_n)   (raw columns 193 - 192).")
R.append("  Window: closed [2.0e-9, 4.0e-9] s inclusive; rows with 2.0e-9 <= t <= 4.0e-9.")
R.append("  Crossing: adjacent samples (p, p+1), BOTH in the window (bracket rule),")
R.append("    with strictly opposite signs (v_p < 0 < v_q or v_q < 0 < v_p);")
R.append("    direction POS (v_p < 0, v_q > 0) / NEG (v_p > 0, v_q < 0);")
R.append("    t_cross = t_p + (t_q - t_p) * v_p / (v_p - v_q) (linear interpolation).")
R.append("  Zero: in-window sample with v == 0.0 exactly; listed separately as a")
R.append("    kind=ZERO row (i = point index, t_i = time, v_i = value); never a")
R.append("    crossing (strictness), never double-counted.")
R.append("  Counts: all-row-recounted from the sealed TSV (kind=CROSS / kind=ZERO).")
R.append("  Stats: sampled min, max, peak-to-peak = max - min over in-window samples.")
R.append("  Adjacent crossing intervals: t_cross[k+1] - t_cross[k] per (arm, signal).")
R.append("  TSV: one rectangular file, header + data rows; every row exactly 12 fields.")
R.append("")
for arm in ("UNLOADED", "LOADED"):
    npts, nvar, payload = rawfacts[arm]["npts"], rawfacts[arm]["nvar"], rawfacts[arm]["payload"]
    R.append("=== %s arm (raw %s) ===" % (arm, "456aa04d..." if arm == "UNLOADED" else "2f2010d2..."))
    R.append("  raw structure: No. Variables=%d No. Points=%d payload=%d exact=True (re-verified);" % (nvar, npts, payload))
    R.append("  four analysed columns finite: NaN=0 Inf=0 (re-verified); time strictly monotonic.")
    for label, _, _ in SIGNALS:
        f = facts[(arm, label)]
        R.append("  signal %s:" % label)
        R.append("    window rows: point indices %d..%d inclusive, count %d (t_lo=%s t_hi=%s)"
                 % (f["lo"], f["hi"], f["nwin"], repr(f["t_lo"]), repr(f["t_hi"])))
        R.append("    sampled stats: min=%s max=%s peak-to-peak=%s"
                 % (repr(f["mn"]), repr(f["mx"]), repr(f["p2p"])))
        R.append("    exact-zero samples (all-row recount from TSV): %d" % len(f["zeros"]))
        for rz in f["rows_zero"]:
            R.append("      " + rz)
        R.append("    crossings (all-row recount from TSV): %d" % len(f["crossings"]))
        for rc in f["rows_cross"]:
            R.append("      " + rc)
        R.append("    adjacent crossing intervals: %d" % len(f["intervals"]))
        for k, a, b, dt in f["intervals"]:
            R.append("      interval %d: crossing %d -> %d, dt=%s" % (k, k, k + 1, repr(dt)))
        if not f["intervals"]:
            R.append("      none (fewer than 2 crossings)")
        R.append("")
R.append("=== TSV identity ===")
R.append("  file: %s-FACTS.tsv ; header + %d data rows (%d crossings, %d zeros); every row 12 fields." % (P, tot_cross + tot_zero, tot_cross, tot_zero))
R.append("  row order: chronological per (arm, signal); ordinals per kind within (arm, signal).")
R.append("")
R.append("=== claims ===")
R.append("CONFIRMED: bound hashes (raws, decks, V3, parser); per-arm window row ranges")
R.append("and sample counts; crossing rows emitted with arm/signal/ordinal/direction/")
R.append("bracket indices/times/values and linear-interpolated crossing time; exact-")
R.append("zero samples listed separately without double-counting; all counts all-row-")
R.append("recounted from the sealed TSV; sampled min/max/peak-to-peak per signal and")
R.append("arm; adjacent crossing intervals listed.")
R.append("PROVISIONAL: waveform-sufficiency diagnostic under zero-source-impedance")
R.append("ideal drive only (PE statement); linear interpolation between samples is")
R.append("the stated crossing-time model.")
R.append("UNKNOWN: all circuit behaviour beyond the listed sampled facts.")
R.append("No pass/fail, causal, compatibility, specification, reliability, engineering-")
R.append("gate, signoff, tape-out, or publication claim.")
R.append("")
R.append("=== stop ===")
R.append("Read-only analysis package complete; awaiting Principal Engineer review.")
rep_text = "\n".join(R) + "\n"
REP = PKG + "/" + P + "-REPORT.log"
oexcl(REP, rep_text)

# external identities
print("READ-ONLY-STAGE2-REPLAY-WAVEFORM-ANALYSIS-V1 created (no simulation):")
for fn in (P + "-FACTS.tsv", P + "-REPORT.log"):
    p = PKG + "/" + fn
    bb = open(p, "rb").read()
    print("  %-60s sha256=%s bytes=%d lines=%d" % (fn, hashlib.sha256(bb).hexdigest(), len(bb), bb.count(b"\n")))
for arm in ("UNLOADED", "LOADED"):
    for label, _, _ in SIGNALS:
        f = facts[(arm, label)]
        print("  %-8s %-4s window=%d rows crossings=%d zeros=%d min=%s max=%s p2p=%s"
              % (arm, label, f["nwin"], len(f["crossings"]), len(f["zeros"]),
                 repr(f["mn"]), repr(f["mx"]), repr(f["p2p"])))
print("  STOP: awaiting Principal Engineer review.")

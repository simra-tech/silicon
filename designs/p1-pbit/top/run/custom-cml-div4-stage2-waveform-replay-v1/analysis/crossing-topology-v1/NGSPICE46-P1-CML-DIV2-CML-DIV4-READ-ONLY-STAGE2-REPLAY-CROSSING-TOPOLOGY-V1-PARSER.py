#!/usr/bin/env python3
"""READ-ONLY-STAGE2-REPLAY-CROSSING-TOPOLOGY-V1 - guarded parser/runner.

READ-ONLY. No simulation; no design/deck/data/raw edits. Fail-closed on
bound inputs: pair raws (456aa04d..., 2f2010d2...), both decks, the sealed
V3-CORRECTION-OF-CORRECTION package, and the accepted waveform-analysis
FACTS TSV (07e95bbe...).

Over the closed window [2.0e-9, 4.0e-9] s, partitions each arm by its
consecutive IN crossings (strict opposite-sign adjacent-sample crossings of
IN = v(div2_p_1)-v(div2_n_1), derived identically to the accepted FACTS TSV
and byte-cross-checked against it), retaining pre-first and post-last
fragments separately. Emits ONE rectangular TSV with:
  - INTERVAL rows (pre-first, each between-crossing interval, post-last):
    sample point range, sample count, boundary IN crossing ordinals,
    sampled CM_IN / CM_OUT min/max/peak-to-peak, OUT-crossing recount;
  - CROSS rows: every OUT crossing with exact bracket provenance (point
    indices/times/values and interpolated crossing time), its containing
    IN-crossing interval, nearest IN crossing with signed delta-t, and
    CM_IN / CM_OUT linearly interpolated at the crossing time.
Facts only; no ringing/oscillation/causality/compatibility/gate labelling;
no pass/fail claim. O_EXCL outputs.
GUARDED: STAGE2_REPLAY_TOPOLOGY_V1=1.
"""
import os, sys, re, array, math, hashlib, bisect

if os.environ.get("STAGE2_REPLAY_TOPOLOGY_V1") != "1":
    print("GUARDED: STAGE2_REPLAY_TOPOLOGY_V1=1 marker required; no write.")
    sys.exit(1)

BASE = "."
V1D = BASE + "/NGSPICE46-P1-CML-DIV2-CML-DIV4-STAGE2-REPLAY-RUNTIME-V1"
V3D = BASE + "/NGSPICE46-P1-CML-DIV2-CML-DIV4-STAGE2-REPLAY-RUNTIME-V3-CORRECTION-OF-CORRECTION"
WFAD = BASE + "/NGSPICE46-P1-CML-DIV2-CML-DIV4-READ-ONLY-STAGE2-REPLAY-WAVEFORM-ANALYSIS-V1"
WFA = "NGSPICE46-P1-CML-DIV2-CML-DIV4-READ-ONLY-STAGE2-REPLAY-WAVEFORM-ANALYSIS-V1"
PKG = BASE + "/NGSPICE46-P1-CML-DIV2-CML-DIV4-READ-ONLY-STAGE2-REPLAY-CROSSING-TOPOLOGY-V1"
P = "NGSPICE46-P1-CML-DIV2-CML-DIV4-READ-ONLY-STAGE2-REPLAY-CROSSING-TOPOLOGY-V1"
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
FACTS = (WFAD + "/" + WFA + "-FACTS.tsv",
         "07e95bbe72cfe9a073b3a6e7156c4cdea7bfb6491a9530ed5641796ac867b682")

W0, W1 = 2.0e-9, 4.0e-9
NA = "NA"
HEADER = ("arm\tkind\tordinal\tinterval_id\ti\tj\tt_i\tt_j\tv_i\tv_j\tt_cross\t"
          "in_from\tin_to\tnearest_in\tdelta_t\tcm_in_cross\tcm_out_cross\t"
          "n_samples\tn_out_cross\tcm_in_min\tcm_in_max\tcm_in_p2p\t"
          "cm_out_min\tcm_out_max\tcm_out_p2p")


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


def scan_crossings(vals, t, lo, hi):
    """Return list of (ordinal, i, j, ti, tj, vi, vj, tc, direction)."""
    out = []
    ord_ = 0
    for p in range(lo, hi):
        x, y = vals[p], vals[p + 1]
        if (x < 0.0 and y > 0.0) or (x > 0.0 and y < 0.0):
            ord_ += 1
            direction = "POS" if x < 0.0 else "NEG"
            ti, tj = t[p], t[p + 1]
            tc = ti + (tj - ti) * x / (x - y)
            out.append((ord_, p, p + 1, ti, tj, x, y, tc, direction))
    return out


def facts_row(arm, signal, ordinal, direction, i, j, ti, tj, vi, vj, tc):
    return "\t".join([arm, signal, "CROSS", str(ordinal), direction,
                      str(i), str(j), repr(ti), repr(tj), repr(vi), repr(vj), repr(tc)])


if os.path.exists(PKG):
    print("FAIL CLOSED: %s exists" % PKG)
    sys.exit(1)

for arm, (path, exp) in RAW.items():
    assert sha(path) == exp, f"raw {arm} hash mismatch"
for arm, (path, exp) in DECK.items():
    assert sha(path) == exp, f"deck {arm} hash mismatch"
for path, exp in V3:
    assert sha(path) == exp, f"V3 member hash mismatch: {os.path.basename(path)}"
assert sha(FACTS[0]) == FACTS[1], "FACTS TSV hash mismatch"

# load accepted FACTS TSV crossings
facts_cross = {}   # (arm, signal) -> list of row strings (CROSS only, in order)
fhead = open(FACTS[0], encoding="utf-8").read().splitlines()
assert fhead[0] == "arm\tsignal\tkind\tordinal\tdirection\ti\tj\tt_i\tt_j\tv_i\tv_j\tt_cross"
for ln in fhead[1:]:
    f = ln.split("\t")
    assert len(f) == 12, "FACTS TSV non-rectangular row"
    if f[2] == "CROSS":
        facts_cross.setdefault((f[0], f[1]), []).append(ln)

os.mkdir(PKG)

rows = []
topo = {}   # (arm, label) -> dict(...)
parts = {}  # arm -> list of fragment dicts
for arm in ("UNLOADED", "LOADED"):
    nv, np_, t, idx, col = parse_raw(RAW[arm][0])
    vp2, vn2, vp4, vn4 = col(idx["v(div2_p_1)"]), col(idx["v(div2_n_1)"]), col(idx["v(div4_p)"]), col(idx["v(div4_n)"])
    vin = [vp2[p] - vn2[p] for p in range(np_)]
    vout = [vp4[p] - vn4[p] for p in range(np_)]
    cm_in = [(vp2[p] + vn2[p]) / 2.0 for p in range(np_)]
    cm_out = [(vp4[p] + vn4[p]) / 2.0 for p in range(np_)]
    assert all(math.isfinite(x) for x in vin + vout + cm_in + cm_out)
    lo = bisect.bisect_left(t, W0)
    hi = bisect.bisect_right(t, W1) - 1
    nwin = hi - lo + 1
    in_cross = scan_crossings(vin, t, lo, hi)
    out_cross = scan_crossings(vout, t, lo, hi)
    # byte cross-check vs accepted FACTS TSV
    for signal, derived in (("IN", in_cross), ("OUT", out_cross)):
        acc = facts_cross.get((arm, signal), [])
        assert len(derived) == len(acc), (arm, signal, len(derived), len(acc))
        for d, a in zip(derived, acc):
            assert facts_row(arm, signal, d[0], d[8], d[1], d[2], d[3], d[4], d[5], d[6], d[7]) == a, \
                (arm, signal, d[0], "FACTS mismatch")
    K = len(in_cross)
    in_times = [c[7] for c in in_cross]
    in_i = [c[1] for c in in_cross]
    # fragments: pre(0), intervals 1..K-1, post(K)
    frags = []
    frags.append(dict(id=0, label="PRE", first=lo, last=in_i[0], in_from=NA, in_to="1"))
    for k in range(1, K):
        frags.append(dict(id=k, label="IN", first=in_i[k - 1] + 1, last=in_i[k],
                          in_from=str(k), in_to=str(k + 1)))
    frags.append(dict(id=K, label="POST", first=in_i[K - 1] + 1, last=hi,
                      in_from=str(K), in_to=NA))
    # OUT crossing mapping
    mapped = []  # (out crossing tuple, interval_id, nearest, delta, cm_in_at, cm_out_at)
    for c in out_cross:
        tc = c[7]
        n = sum(1 for x in in_times if x <= tc)
        interval_id = n if n < K else K
        best = min(range(K), key=lambda k: (abs(tc - in_times[k]), k))
        delta = tc - in_times[best]
        i, j = c[1], c[2]
        w = (tc - t[i]) / (t[j] - t[i])
        cm_in_at = cm_in[i] + (cm_in[j] - cm_in[i]) * w
        cm_out_at = cm_out[i] + (cm_out[j] - cm_out[i]) * w
        mapped.append((c, interval_id, best + 1, delta, cm_in_at, cm_out_at))
    # per-fragment stats + OUT recount
    per_interval = {}
    for fr in frags:
        s, e = fr["first"], fr["last"]
        n_samples = e - s + 1
        fr["n_samples"] = n_samples
        fr["t_first"], fr["t_last"] = t[s], t[e]
        fr["cm_in_min"] = min(cm_in[s:e + 1])
        fr["cm_in_max"] = max(cm_in[s:e + 1])
        fr["cm_out_min"] = min(cm_out[s:e + 1])
        fr["cm_out_max"] = max(cm_out[s:e + 1])
        per_interval[fr["id"]] = 0
    for c, interval_id, nearest, delta, cm_in_at, cm_out_at in mapped:
        per_interval[interval_id] += 1
    for fr in frags:
        fr["n_out_cross"] = per_interval[fr["id"]]
    topo[(arm, "IN")] = dict(crossings=in_cross)
    topo[(arm, "OUT")] = dict(crossings=out_cross, mapped=mapped)
    parts[arm] = frags
    # TSV rows: INTERVAL rows then CROSS rows
    for fr in frags:
        rows.append("\t".join([
            arm, "INTERVAL", str(fr["id"]), str(fr["id"]),
            str(fr["first"]), str(fr["last"]), repr(fr["t_first"]), repr(fr["t_last"]),
            NA, NA, NA, fr["in_from"], fr["in_to"], NA, NA, NA, NA,
            str(fr["n_samples"]), str(fr["n_out_cross"]),
            repr(fr["cm_in_min"]), repr(fr["cm_in_max"]),
            repr(fr["cm_in_max"] - fr["cm_in_min"]),
            repr(fr["cm_out_min"]), repr(fr["cm_out_max"]),
            repr(fr["cm_out_max"] - fr["cm_out_min"])]))
    for c, interval_id, nearest, delta, cm_in_at, cm_out_at in mapped:
        rows.append("\t".join([
            arm, "CROSS", str(c[0]), str(interval_id),
            str(c[1]), str(c[2]), repr(c[3]), repr(c[4]), repr(c[5]), repr(c[6]), repr(c[7]),
            NA, NA, str(nearest), repr(delta), repr(cm_in_at), repr(cm_out_at),
            NA, NA, NA, NA, NA, NA, NA, NA]))

tsv_text = "\n".join([HEADER] + rows) + "\n"
TSV = PKG + "/" + P + "-TOPOLOGY.tsv"
oexcl(TSV, tsv_text)

# all-row recount from the sealed TSV
back = open(TSV, encoding="utf-8").read()
assert back == tsv_text, "TSV read-back byte mismatch"
lines = back.splitlines()
assert lines[0] == HEADER
recount_int = {}
recount_cross = {}
for ln in lines[1:]:
    f = ln.split("\t")
    assert len(f) == 25, "non-rectangular TSV row: %r" % ln
    if f[1] == "INTERVAL":
        recount_int[(f[0], int(f[2]))] = (int(f[17]), int(f[18]))
    elif f[1] == "CROSS":
        recount_cross[(f[0], int(f[3]))] = recount_cross.get((f[0], int(f[3])), 0) + 1
    else:
        raise AssertionError("bad kind %r" % f[1])
for arm in ("UNLOADED", "LOADED"):
    for fr in parts[arm]:
        rs, rc = recount_int[(arm, fr["id"])]
        assert rs == fr["n_samples"] and rc == fr["n_out_cross"], (arm, fr["id"])
    for c, interval_id, nearest, delta, cm_in_at, cm_out_at in topo[(arm, "OUT")]["mapped"]:
        expect = [fr for fr in parts[arm] if fr["id"] == interval_id][0]["n_out_cross"]
        assert recount_cross.get((arm, interval_id), 0) == expect, (arm, interval_id)

# ---- report ----
R = []
R.append(P + "-REPORT.log")
R.append("Read-only crossing-topology analysis of the sealed STAGE2-REPLAY-RUNTIME-V1")
R.append("pair (raws 456aa04d..., 2f2010d2...), per Principal Engineer instruction.")
R.append("PROVISIONAL scope (PE statement): zero-source-impedance ideal-drive")
R.append("waveform-sufficiency diagnostic ONLY. No simulation; no design/deck/data/")
R.append("raw edits; no waveform modification.")
R.append("")
R.append("=== bound inputs (CONFIRMED) ===")
R.append("  raw unloaded 456aa04dafc1b8a3023552e31cc1ba1c16fd8c55e04b5171934a7f0670489881")
R.append("  raw loaded   2f2010d24096030bb0317bf1c774fa16bcb82a61c09eb6f3badca402da357c26")
R.append("  deck unloaded 7331ed2ee383c15044a29df4b8bd2f8c2817260f3b2a2ae98b586e68c7a67d2f")
R.append("  deck loaded   e8ffffeab75e7a75f50a7b1ced2609dfe224a3b9b4930836faffaea1e4082de8")
R.append("  V3-CORRECTION-OF-CORRECTION: cf9638286611366c2d89ebae8349bb45ca3f4b7928b1050ae40f440470aec962 ;")
R.append("    3b3fcdf892e8252daf5e6d9cdb4acb539f298501b009c482cb0d1d0c6805e140 ;")
R.append("    c2e559283a97a1a40d43a9ac50909b4e01b9d8a9d661c94946be1b21b3ac69f8")
R.append("  FACTS TSV (accepted waveform analysis) 07e95bbe72cfe9a073b3a6e7156c4cdea7bfb6491a9530ed5641796ac867b682")
R.append("  parser (this package, preserved byte-identical) sha256=%s" % sha(sys.argv[0]))
R.append("")
R.append("=== method ===")
R.append("  Signals: IN = v(div2_p_1)-v(div2_n_1) ; OUT = v(div4_p)-v(div4_n) ;")
R.append("  CM_IN = (v(div2_p_1)+v(div2_n_1))/2 ; CM_OUT = (v(div4_p)+v(div4_n))/2.")
R.append("  Window: closed [2.0e-9, 4.0e-9] s inclusive (rows with 2.0e-9 <= t <= 4.0e-9).")
R.append("  Crossing: adjacent in-window samples, strictly opposite signs, both")
R.append("  samples in window; t_cross = t_i + (t_j - t_i)*v_i/(v_i - v_j).")
R.append("  Partition: fragments separated at each consecutive IN crossing bracket")
R.append("  (sample i_k belongs to the fragment before crossing k; sample i_k+1 to")
R.append("  the fragment after). Fragments: PRE (before IN crossing 1), IN k")
R.append("  (between crossings k and k+1), POST (after the last IN crossing).")
R.append("  Containing interval of an OUT crossing: by its interpolated time t_out")
R.append("  vs the IN crossing times (n = count of tc <= t_out; n==0 -> PRE, n==K ->")
R.append("  POST, else interval n).")
R.append("  Nearest IN crossing: argmin_k |t_out - tc_k|; tie -> smaller k;")
R.append("  delta_t = t_out - tc_k (signed).")
R.append("  CM at OUT crossing: linear interpolation of CM_IN / CM_OUT at t_out")
R.append("  between the crossing's bracket samples (same interpolation family).")
R.append("  CM stats: sampled min/max/peak-to-peak over the fragment's samples.")
R.append("  Counts: all-row-recounted from the sealed TSV.")
R.append("  TSV: one rectangular file, header + data rows; every row exactly 25 fields;")
R.append("  INTERVAL rows (per arm: PRE, IN 1..9, POST) then CROSS rows (OUT ordinals).")
R.append("")
R.append("=== FACTS cross-check (CONFIRMED) ===")
R.append("  every derived IN/OUT crossing byte-matches the accepted FACTS TSV rows:")
R.append("  UNLOADED IN=10 OUT=5 ; LOADED IN=10 OUT=30 ; exact-zero=0 (unchanged).")
R.append("")
for arm in ("UNLOADED", "LOADED"):
    R.append("=== %s arm (raw %s) ===" % (arm, "456aa04d..." if arm == "UNLOADED" else "2f2010d2..."))
    R.append("  window rows: point indices %d..%d inclusive, count %d"
             % (parts[arm][0]["first"], parts[arm][-1]["last"],
                sum(fr["n_samples"] for fr in parts[arm])))
    R.append("  partition by %d IN crossings -> %d fragments (PRE + %d IN + POST):"
             % (len(topo[(arm, "IN")]["crossings"]), len(parts[arm]), len(parts[arm]) - 2))
    R.append("    id  label  samples(first..last)  n  t_first  t_last  in_from in_to  n_out")
    for fr in parts[arm]:
        R.append("    %2d  %-4s  %5d..%-5d  %4d  %s  %s  %-5s %-5s %d"
                 % (fr["id"], fr["label"], fr["first"], fr["last"], fr["n_samples"],
                    repr(fr["t_first"]), repr(fr["t_last"]), fr["in_from"], fr["in_to"],
                    fr["n_out_cross"]))
    R.append("  per-interval sampled CM stats and OUT-crossing recount (TSV rows):")
    for fr in parts[arm]:
        R.append("    " + "\t".join([
            arm, "INTERVAL", str(fr["id"]), str(fr["id"]),
            str(fr["first"]), str(fr["last"]), repr(fr["t_first"]), repr(fr["t_last"]),
            NA, NA, NA, fr["in_from"], fr["in_to"], NA, NA, NA, NA,
            str(fr["n_samples"]), str(fr["n_out_cross"]),
            repr(fr["cm_in_min"]), repr(fr["cm_in_max"]),
            repr(fr["cm_in_max"] - fr["cm_in_min"]),
            repr(fr["cm_out_min"]), repr(fr["cm_out_max"]),
            repr(fr["cm_out_max"] - fr["cm_out_min"])]))
    R.append("  OUT crossings with topology (TSV rows):")
    for c, interval_id, nearest, delta, cm_in_at, cm_out_at in topo[(arm, "OUT")]["mapped"]:
        R.append("    " + "\t".join([
            arm, "CROSS", str(c[0]), str(interval_id),
            str(c[1]), str(c[2]), repr(c[3]), repr(c[4]), repr(c[5]), repr(c[6]), repr(c[7]),
            NA, NA, str(nearest), repr(delta), repr(cm_in_at), repr(cm_out_at),
            NA, NA, NA, NA, NA, NA, NA, NA]))
    R.append("")
tot_int = sum(len(parts[a]) for a in ("UNLOADED", "LOADED"))
tot_cross = sum(len(topo[(a, "OUT")]["mapped"]) for a in ("UNLOADED", "LOADED"))
R.append("=== TSV identity ===")
R.append("  file: %s-TOPOLOGY.tsv ; header + %d data rows (%d INTERVAL + %d CROSS); every row 25 fields."
         % (P, tot_int + tot_cross, tot_int, tot_cross))
R.append("")
R.append("=== claims ===")
R.append("CONFIRMED: bound hashes (raws, decks, V3, FACTS TSV, parser); every derived")
R.append("IN/OUT crossing byte-matches the accepted FACTS TSV; partition into PRE/IN/POST")
R.append("fragments per arm with sample ranges and counts; every OUT crossing mapped to")
R.append("its containing IN-crossing interval and nearest IN crossing with signed")
R.append("delta-t; OUT crossings recounted per interval; sampled CM_IN/CM_OUT min/max/")
R.append("peak-to-peak per interval; CM_IN/CM_OUT linearly interpolated at each OUT")
R.append("crossing; exact bracket provenance retained on every CROSS row.")
R.append("PROVISIONAL: waveform-sufficiency diagnostic under zero-source-impedance ideal")
R.append("drive only (PE statement); linear interpolation is the stated model for")
R.append("crossing times and CM-at-crossing values.")
R.append("UNKNOWN: all circuit behaviour beyond the listed sampled facts.")
R.append("Facts only; no ringing, oscillation, causality, compatibility, or gate-result")
R.append("labelling; no pass/fail, specification, reliability, engineering-gate,")
R.append("signoff, tape-out, or publication claim.")
R.append("")
R.append("=== stop ===")
R.append("Read-only crossing-topology package complete; awaiting Principal Engineer review.")
rep_text = "\n".join(R) + "\n"
REP = PKG + "/" + P + "-REPORT.log"
oexcl(REP, rep_text)

print("READ-ONLY-STAGE2-REPLAY-CROSSING-TOPOLOGY-V1 created (no simulation):")
for fn in (P + "-TOPOLOGY.tsv", P + "-REPORT.log"):
    p = PKG + "/" + fn
    bb = open(p, "rb").read()
    print("  %-60s sha256=%s bytes=%d lines=%d" % (fn, hashlib.sha256(bb).hexdigest(), len(bb), bb.count(b"\n")))
for arm in ("UNLOADED", "LOADED"):
    n_int = len(parts[arm])
    n_out = len(topo[(arm, "OUT")]["mapped"])
    print("  %-8s fragments=%d OUT crossings=%d" % (arm, n_int, n_out))
    for fr in parts[arm]:
        print("    %s id=%d samples=%d..%d n=%d n_out=%d cm_in_p2p=%s cm_out_p2p=%s"
              % (fr["label"], fr["id"], fr["first"], fr["last"], fr["n_samples"],
                 fr["n_out_cross"], repr(fr["cm_in_max"] - fr["cm_in_min"]),
                 repr(fr["cm_out_max"] - fr["cm_out_min"])))
print("  STOP: awaiting Principal Engineer review.")

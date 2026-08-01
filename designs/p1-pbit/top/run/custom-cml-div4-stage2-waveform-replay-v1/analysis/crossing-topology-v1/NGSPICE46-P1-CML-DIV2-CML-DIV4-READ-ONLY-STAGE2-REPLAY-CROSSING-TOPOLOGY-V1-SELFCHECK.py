#!/usr/bin/env python3
"""READ-ONLY-STAGE2-REPLAY-CROSSING-TOPOLOGY-V1 - independent self-check.

Independent implementation (does NOT import the parser): struct-based raw
loading, sign-product crossing form. Re-derives from the sealed raws:
IN/OUT crossings (byte-cross-checked against the accepted FACTS TSV),
partition fragments, OUT-crossing containing intervals + nearest IN crossing
with signed delta-t, CM_IN/CM_OUT at crossings (linear interpolation), and
per-fragment sampled CM stats. Then verifies the sealed TOPOLOGY TSV:
header exact, every row exactly 25 fields, every row byte-exact vs the
independent derivation (100% TSV row reproduction), all-row recounts,
and that the report contains every TSV row string and recounted value.
Writes the transcript to the given output path with O_EXCL.
No simulation; no design/deck/data/raw edits; no waveform modification.
GUARDED: STAGE2_REPLAY_TOPOLOGY_SELFCHECK_V1=1.
"""
import os, sys, re, struct, math, hashlib, bisect

if os.environ.get("STAGE2_REPLAY_TOPOLOGY_SELFCHECK_V1") != "1":
    print("GUARDED: STAGE2_REPLAY_TOPOLOGY_SELFCHECK_V1=1 marker required; no write.")
    sys.exit(1)

OUT = sys.argv[1] if len(sys.argv) > 1 else None
if not OUT:
    print("usage: STAGE2_REPLAY_TOPOLOGY_SELFCHECK_V1=1 python3 SELFCHECK.py <output-log>")
    sys.exit(2)

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

transcript = []
fails = []


def log(msg=""):
    transcript.append(msg)
    print(msg)


def check(cond, msg):
    log(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        fails.append(msg)


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_raw(path):
    b = open(path, "rb").read()
    m = b.find(b"Binary:\n")
    assert m > 0, "no Binary marker"
    hdr = b[:m].decode(errors="replace")
    nv = int(re.search(r"No\. Variables:\s*(\d+)", hdr).group(1))
    np_ = int(re.search(r"No\. Points:\s*(\d+)", hdr).group(1))
    payload = b[m + len(b"Binary:\n"):]
    assert len(payload) == nv * np_ * 8, "payload length mismatch"
    idx = {}
    for ln in hdr.splitlines():
        mm = re.match(r"^\s*(\d+)\s+(\S+)\s+(\S+)\s*$", ln)
        if mm:
            idx[mm.group(2)] = int(mm.group(1))
    t = [struct.unpack_from("<d", payload, (p * nv + idx["time"]) * 8)[0] for p in range(np_)]

    def col(k):
        return [struct.unpack_from("<d", payload, (p * nv + k) * 8)[0] for p in range(np_)]

    return nv, np_, t, col


def facts_row(arm, signal, ordinal, direction, i, j, ti, tj, vi, vj, tc):
    return "\t".join([arm, signal, "CROSS", str(ordinal), direction,
                      str(i), str(j), repr(ti), repr(tj), repr(vi), repr(vj), repr(tc)])


log("=== independent bound-input verification ===")
for arm, (path, exp) in RAW.items():
    check(sha(path) == exp, f"raw {arm} hash {exp[:16]}...")
for arm, (path, exp) in DECK.items():
    check(sha(path) == exp, f"deck {arm} hash {exp[:16]}...")
for path, exp in V3:
    check(sha(path) == exp, f"V3 {os.path.basename(path)} hash {exp[:16]}...")
check(sha(FACTS[0]) == FACTS[1], f"FACTS TSV hash {FACTS[1][:16]}...")

facts_cross = {}
fhead = open(FACTS[0], encoding="utf-8").read().splitlines()
for ln in fhead[1:]:
    f = ln.split("\t")
    if f[2] == "CROSS":
        facts_cross.setdefault((f[0], f[1]), []).append(ln)

log("")
log("=== independent derivation from sealed raws ===")
expected_int = {}   # (arm, id) -> row string
expected_cross = {}  # (arm, ordinal) -> row string
per_arm_out = {}    # arm -> list of (interval_id, row string)
for arm in ("UNLOADED", "LOADED"):
    nv, np_, t, col = load_raw(RAW[arm][0])
    check(all(t[k + 1] > t[k] for k in range(len(t) - 1)), f"{arm}: time strictly monotonic")
    vp2, vn2, vp4, vn4 = (col(191), col(190), col(193), col(192))
    vin = [vp2[p] - vn2[p] for p in range(np_)]
    vout = [vp4[p] - vn4[p] for p in range(np_)]
    cm_in = [(vp2[p] + vn2[p]) / 2.0 for p in range(np_)]
    cm_out = [(vp4[p] + vn4[p]) / 2.0 for p in range(np_)]
    lo = bisect.bisect_left(t, W0)
    hi = bisect.bisect_right(t, W1) - 1
    # independent crossings (sign-product form)
    def crossings(vals):
        out, ord_ = [], 0
        for p in range(lo, hi):
            x, y = vals[p], vals[p + 1]
            if x * y < 0.0:
                ord_ += 1
                direction = "POS" if x < 0.0 else "NEG"
                ti, tj = t[p], t[p + 1]
                tc = ti + (tj - ti) * x / (x - y)
                out.append((ord_, p, p + 1, ti, tj, x, y, tc, direction))
        return out
    in_cross = crossings(vin)
    out_cross = crossings(vout)
    for signal, derived in (("IN", in_cross), ("OUT", out_cross)):
        acc = facts_cross.get((arm, signal), [])
        ok = len(derived) == len(acc) and all(
            facts_row(arm, signal, d[0], d[8], d[1], d[2], d[3], d[4], d[5], d[6], d[7]) == a
            for d, a in zip(derived, acc))
        check(ok, f"{arm} {signal}: {len(derived)} crossings byte-match accepted FACTS TSV")
    K = len(in_cross)
    in_times = [c[7] for c in in_cross]
    in_i = [c[1] for c in in_cross]
    frags = []
    frags.append(dict(id=0, label="PRE", first=lo, last=in_i[0], in_from=NA, in_to="1"))
    for k in range(1, K):
        frags.append(dict(id=k, label="IN", first=in_i[k - 1] + 1, last=in_i[k],
                          in_from=str(k), in_to=str(k + 1)))
    frags.append(dict(id=K, label="POST", first=in_i[K - 1] + 1, last=hi, in_from=str(K), in_to=NA))
    mapped = []
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
    per_interval = {}
    for fr in frags:
        s, e = fr["first"], fr["last"]
        fr["n_samples"] = e - s + 1
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
        expected_int[(arm, fr["id"])] = "\t".join([
            arm, "INTERVAL", str(fr["id"]), str(fr["id"]),
            str(fr["first"]), str(fr["last"]), repr(fr["t_first"]), repr(fr["t_last"]),
            NA, NA, NA, fr["in_from"], fr["in_to"], NA, NA, NA, NA,
            str(fr["n_samples"]), str(fr["n_out_cross"]),
            repr(fr["cm_in_min"]), repr(fr["cm_in_max"]),
            repr(fr["cm_in_max"] - fr["cm_in_min"]),
            repr(fr["cm_out_min"]), repr(fr["cm_out_max"]),
            repr(fr["cm_out_max"] - fr["cm_out_min"])])
    for c, interval_id, nearest, delta, cm_in_at, cm_out_at in mapped:
        expected_cross[(arm, c[0])] = "\t".join([
            arm, "CROSS", str(c[0]), str(interval_id),
            str(c[1]), str(c[2]), repr(c[3]), repr(c[4]), repr(c[5]), repr(c[6]), repr(c[7]),
            NA, NA, str(nearest), repr(delta), repr(cm_in_at), repr(cm_out_at),
            NA, NA, NA, NA, NA, NA, NA, NA])
    per_arm_out[arm] = [(m[1], expected_cross[(arm, m[0][0])]) for m in mapped]
    log(f"  {arm}: fragments={len(frags)} OUT crossings={len(out_cross)}")

log("")
log("=== TOPOLOGY TSV verification (100% row reproduction) ===")
TSV = PKG + "/" + P + "-TOPOLOGY.tsv"
rep = open(PKG + "/" + P + "-REPORT.log", encoding="utf-8").read()
lines = open(TSV, encoding="utf-8").read().splitlines()
check(lines[0] == HEADER, "TSV header exact")
bad = [i for i, ln in enumerate(lines[1:], 1) if len(ln.split("\t")) != 25]
check(not bad, f"TSV rectangular: all rows exactly 25 fields (bad={bad[:5]})")
tsv_int = {}
tsv_cross = {}
for ln in lines[1:]:
    f = ln.split("\t")
    assert len(f) == 25
    if f[1] == "INTERVAL":
        tsv_int[(f[0], int(f[2]))] = ln
    else:
        tsv_cross[(f[0], int(f[2]))] = ln
for arm in ("UNLOADED", "LOADED"):
    for fr_id in sorted(expected_int):
        if fr_id[0] == arm:
            check(tsv_int.get(fr_id) == expected_int[fr_id],
                  f"{arm} interval id {fr_id[1]} row byte-exact vs independent")
    for (a, ord_), ln in sorted(expected_cross.items()):
        if a == arm:
            check(tsv_cross.get((a, ord_)) == ln,
                  f"{arm} OUT crossing {ord_} row byte-exact vs independent")
    # recounts
    for fr_id in sorted(expected_int):
        if fr_id[0] == arm:
            fields = tsv_int[fr_id].split("\t")
            nsamp, nout = int(fields[17]), int(fields[18])
            got = sum(1 for (a, o), ln in tsv_cross.items()
                      if a == arm and ln.split("\t")[3] == str(fr_id[1]))
            check(nout == got, f"{arm} interval {fr_id[1]}: n_out_cross recount == TSV CROSS rows")
    # report contains every row string + recounted values
    for fr_id in sorted(expected_int):
        if fr_id[0] == arm:
            check(tsv_int[fr_id] in rep, f"{arm} interval {fr_id[1]} row present in report")
    for (a, ord_), ln in sorted(expected_cross.items()):
        if a == arm:
            check(ln in rep, f"{arm} OUT crossing {ord_} row present in report")
check(("header + %d data rows (%d INTERVAL + %d CROSS)" %
       (len(expected_int) + len(expected_cross), len(expected_int), len(expected_cross))) in rep,
      "report TSV identity line matches independent totals")
check(len(lines) - 1 == len(expected_int) + len(expected_cross),
      "TSV physical data-row count == independent totals")
check(all("UNLOADED IN=10 OUT=5 ; LOADED IN=10 OUT=30" in rep for _ in [0]),
      "report FACTS cross-check line present")

log("")
log("SELFCHECK " + ("PASS" if not fails else "FAIL") + f" ({len(fails)} failures)")
with open(OUT, "x", encoding="utf-8") as f:
    f.write("\n".join(transcript) + "\n")
print("transcript written (O_EXCL):", OUT)
sys.exit(1 if fails else 0)

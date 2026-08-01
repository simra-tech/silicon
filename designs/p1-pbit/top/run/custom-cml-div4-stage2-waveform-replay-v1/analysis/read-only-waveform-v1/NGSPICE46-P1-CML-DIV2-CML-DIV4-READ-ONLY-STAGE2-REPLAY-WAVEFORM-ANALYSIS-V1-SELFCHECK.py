#!/usr/bin/env python3
"""READ-ONLY-STAGE2-REPLAY-WAVEFORM-ANALYSIS-V1 - independent self-check.

Independent implementation (does NOT import the parser). Re-parses both
sealed raws from scratch (struct-based, sign-product crossing form), re-
derives window rows, crossings, exact zeros, sampled min/max/peak-to-peak,
and adjacent crossing intervals, then verifies:
  - TSV header exact; every row exactly 13 fields (rectangularity);
  - every TSV row byte-exact against the independently re-derived fact
    (100% byte round-trip line verification); t_cross recomputed from the
    TSV bracket via the stated formula and from raw values - both byte-exact;
  - counts all-row-recounted from the TSV match independent counts;
  - the report contains every TSV data row string and the recounted
    counts / stats / interval values (formatted identically).
Writes the full transcript to the given output path with O_EXCL.
No simulation; no design/deck/data/raw edits; no waveform modification.
GUARDED: STAGE2_REPLAY_WAVEFORM_SELFCHECK_V1=1.
"""
import os, sys, re, struct, math, hashlib, bisect

if os.environ.get("STAGE2_REPLAY_WAVEFORM_SELFCHECK_V1") != "1":
    print("GUARDED: STAGE2_REPLAY_WAVEFORM_SELFCHECK_V1=1 marker required; no write.")
    sys.exit(1)

OUT = sys.argv[1] if len(sys.argv) > 1 else None
if not OUT:
    print("usage: STAGE2_REPLAY_WAVEFORM_SELFCHECK_V1=1 python3 SELFCHECK.py <output-log>")
    sys.exit(2)

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
SIGNALS = [("IN", 191, 190), ("OUT", 193, 192)]
NA = "NA"
HEADER = "arm\tsignal\tkind\tordinal\tdirection\ti\tj\tt_i\tt_j\tv_i\tv_j\tt_cross"

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
    """Independent raw loader: struct-based, per-point access."""
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


def cross_row(arm, label, ordinal, direction, i, j, ti, tj, vi, vj, tc):
    return "\t".join([arm, label, "CROSS", str(ordinal), direction,
                      str(i), str(j), repr(ti), repr(tj), repr(vi), repr(vj), repr(tc)])


def zero_row(arm, label, ordinal, i, ti, vi):
    return "\t".join([arm, label, "ZERO", str(ordinal), NA,
                      str(i), NA, repr(ti), NA, repr(vi), NA, NA])


# ---- bound inputs (independent recompute) ----
log("=== independent bound-input verification ===")
for arm, (path, exp) in RAW.items():
    check(sha(path) == exp, f"raw {arm} hash {exp[:16]}...")
for arm, (path, exp) in DECK.items():
    check(sha(path) == exp, f"deck {arm} hash {exp[:16]}...")
for path, exp in V3:
    check(sha(path) == exp, f"V3 {os.path.basename(path)} hash {exp[:16]}...")

# ---- independent derivation ----
log("")
log("=== independent derivation from sealed raws ===")
expected = {}   # (arm, label) -> dict(crossings=[row strings], zeros=[row strings], mn, mx, p2p, intervals)
for arm in ("UNLOADED", "LOADED"):
    nv, np_, t, col = load_raw(RAW[arm][0])
    check(all(t[k + 1] > t[k] for k in range(len(t) - 1)), f"{arm}: time strictly monotonic")
    lo = bisect.bisect_left(t, W0)
    hi = bisect.bisect_right(t, W1) - 1
    for label, kp, km in SIGNALS:
        vp, vm = col(kp), col(km)
        vals = [vp[p] - vm[p] for p in range(np_)]
        crossings, zeros = [], []
        c_ord, z_ord = 0, 0
        for p in range(lo, hi + 1):
            x = vals[p]
            if x == 0.0:
                z_ord += 1
                zeros.append(zero_row(arm, label, z_ord, p, t[p], x))
            if p < hi:
                y = vals[p + 1]
                if x * y < 0.0:  # independent sign-product form (strict opposite signs)
                    c_ord += 1
                    direction = "POS" if x < 0.0 else "NEG"
                    ti, tj = t[p], t[p + 1]
                    tc = ti + (tj - ti) * x / (x - y)
                    crossings.append(cross_row(arm, label, c_ord, direction,
                                               p, p + 1, ti, tj, x, y, tc))
        wv = vals[lo:hi + 1]
        mn, mx = min(wv), max(wv)
        tcs = [float(f.split("\t")[11]) for f in crossings]
        intervals = [tcs[k + 1] - tcs[k] for k in range(len(tcs) - 1)]
        expected[(arm, label)] = dict(crossings=crossings, zeros=zeros,
                                      mn=mn, mx=mx, p2p=mx - mn, intervals=intervals)
        log(f"  {arm} {label}: independent crossings={len(crossings)} zeros={len(zeros)} "
            f"min={mn!r} max={mx!r} p2p={mx - mn!r} intervals={len(intervals)}")

# ---- TSV verification (100% byte round-trip) ----
log("")
log("=== TSV byte round-trip verification ===")
TSV = PKG + "/" + P + "-FACTS.tsv"
rep = open(PKG + "/" + P + "-REPORT.log", encoding="utf-8").read()
lines = open(TSV, encoding="utf-8").read().splitlines()
check(lines[0] == HEADER, "TSV header exact")
bad_shape = [i for i, ln in enumerate(lines[1:], 1) if len(ln.split("\t")) != 12]
check(not bad_shape, f"TSV rectangular: all rows exactly 12 fields (bad={bad_shape[:5]})")
tsv_rows = {}
for ln in lines[1:]:
    f = ln.split("\t")
    tsv_rows.setdefault((f[0], f[1], f[2]), []).append(ln)
for arm in ("UNLOADED", "LOADED"):
    for label, _, _ in SIGNALS:
        exp = expected[(arm, label)]
        got_c = tsv_rows.get((arm, label, "CROSS"), [])
        got_z = tsv_rows.get((arm, label, "ZERO"), [])
        check(got_c == exp["crossings"],
              f"{arm} {label}: {len(exp['crossings'])} crossing rows byte-exact vs independent")
        check(got_z == exp["zeros"],
              f"{arm} {label}: {len(exp['zeros'])} zero rows byte-exact vs independent")
        # t_cross recomputed from the TSV bracket (same stated formula) must be byte-exact
        tcbad = []
        for ln in got_c:
            f = ln.split("\t")
            ti, tj = float(f[7]), float(f[8])
            vi, vj = float(f[9]), float(f[10])
            tc = ti + (tj - ti) * vi / (vi - vj)
            if repr(tc) != f[11]:
                tcbad.append(ln)
        check(not tcbad, f"{arm} {label}: t_cross recomputed from TSV bracket byte-exact (bad={len(tcbad)})")
        # stats
        check(("min=%s" % repr(exp["mn"])) in rep, f"{arm} {label}: report contains sampled min")
        check(("max=%s" % repr(exp["mx"])) in rep, f"{arm} {label}: report contains sampled max")
        check(("peak-to-peak=%s" % repr(exp["p2p"])) in rep, f"{arm} {label}: report contains sampled p2p")
        # intervals
        for k, dt in enumerate(exp["intervals"]):
            check(("dt=%s" % repr(dt)) in rep, f"{arm} {label}: report contains interval {k + 1} dt")
        # all-row recount
        check(("crossings (all-row recount from TSV): %d" % len(exp["crossings"])) in rep,
              f"{arm} {label}: report recounts crossing count")
        check(("exact-zero samples (all-row recount from TSV): %d" % len(exp["zeros"])) in rep,
              f"{arm} {label}: report recounts zero count")
        # every TSV data row string present in the report
        missing = [ln for ln in got_c + got_z if ln not in rep]
        check(not missing, f"{arm} {label}: every TSV row string present in report (missing={len(missing)})")
# global totals in report
tot_c = sum(len(exp["crossings"]) for exp in expected.values())
tot_z = sum(len(exp["zeros"]) for exp in expected.values())
check(("header + %d data rows (%d crossings, %d zeros)" % (tot_c + tot_z, tot_c, tot_z)) in rep,
      "report TSV identity line matches independent totals")
check(len(lines) - 1 == tot_c + tot_z, "TSV physical data-row count == independent totals")

log("")
log("SELFCHECK " + ("PASS" if not fails else "FAIL") + f" ({len(fails)} failures)")
with open(OUT, "x", encoding="utf-8") as f:
    f.write("\n".join(transcript) + "\n")
print("transcript written (O_EXCL):", OUT)
sys.exit(1 if fails else 0)

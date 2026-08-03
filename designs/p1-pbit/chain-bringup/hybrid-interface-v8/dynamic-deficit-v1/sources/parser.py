#!/usr/bin/env python3
"""DYNAMIC-DEFICIT-V1 parser - PRE-V2 (guarded; UNRUN).
Binds the PRE-V4 plan JSON (e2767fac...) and the two preserved raw hashes
(3242af86... DC transfer; dbab1bd8... transient). Args: <plan.json>
<dc.raw> <tran.raw> <absent-out>. Guard DYNAMIC_DEFICIT_PARSE=1 required.
PRE-V1 freeze record: PRE-V1 (a33887f7...) was HELD - it wrote
SERIES/SUMMARY before validating the ten crossings (partial-output risk),
SUMMARY used reference_range instead of the plan metric
dc_reference_range, SERIES omitted actual cml_p, SNAPSHOTS omitted its
cml_p interpolation coordinate, and one count print was unformatted.
PRE-V1 is frozen UNRUN and NOT patched. PRE-V2 fixes all five: ALL THREE
output byte strings are built IN MEMORY first; the ten crossings, exact
headers, row counts, SUMMARY keys and final LFs are validated BEFORE
mkdir; mkdir happens only after every check; then exactly SERIES.tsv /
SUMMARY.json / SNAPSHOTS.tsv are exclusive-written (xb) and the out dir
closure is verified. SERIES includes cml_p and cml_diff; SNAPSHOTS
includes its cml_p interpolation coordinate; SUMMARY uses
dc_reference_range; all count prints are formatted.
Fail-closed raw parsing: exact nvar variable/type records, payload EXACTLY
nvar*npts*8 (no trailing bytes), all values finite, scale strictly
monotonic increasing (DC sweep v(v-sweep); transient time). Same-input
interpolation: at each transient sample the input is the ACTUAL v(cml_p);
every plan signal's DC series is linearly interpolated at that input
(reference); residual = observed - reference. Reference range = max-min
over the per-sample references; FAIL on out-of-range input or zero
reference range. Outputs (UNRUN now): SERIES.tsv (wide point/time/cml_p/
cml_diff + per-signal observed/reference/residual, .17g, final LF),
canonical SUMMARY.json (per-signal residual min/max/RMS, observed_range,
dc_reference_range, range_ratio as .17g strings, plus input/method/hash
metadata), SNAPSHOTS.tsv (the ten cml_diff SIGN-CHANGE crossings with
linear crossing-time/value interpolation: crossing, time_s, cml_p_V,
cml_diff_V, then per signal observed/reference/residual, .17g, final LF).
No simulation, no causal claim (cause UNPROVEN).
"""
import os, sys, json, re, struct, hashlib, math, bisect

PLAN_EXPECTED = "e2767fac972c1ff6cce258b8624aab3231fdc0d40ee4f32d659dd63c5a17fde3"
DC_EXPECTED = "3242af860cc73eab78ead1972135ec8fe8eb42b866a9651e742a126214190d64"
TRAN_EXPECTED = "dbab1bd80ddaed8c3bee8f0c5ca816ac192fb687a7c31e841c1de46a7f68906c"
SIGNALS = ['EF_P', 'EF_N', 'GP', 'GN', 'E_CM', 'CM_N', 'CM_P']
METHOD = "same_input_linear_interpolation"
METRICS = ['residual_min_max_rms', 'observed_range', 'dc_reference_range', 'range_ratio']
SNAPSHOTS = 10
GUARD = "DYNAMIC_DEFICIT_PARSE"
INPUT_VAR = "v(cml_p)"
OUT_FILES = ['SERIES.tsv', 'SUMMARY.json', 'SNAPSHOTS.tsv']

if sys.flags.optimize != 0:
    sys.stderr.write("FAIL CLOSED: python -O/-OO would strip asserts; aborting\n")
    sys.exit(1)
if os.environ.get(GUARD) != "1":
    sys.stderr.write("FAIL CLOSED: %s=1 required; aborting\n" % GUARD)
    sys.exit(1)
if len(sys.argv) != 5:
    sys.stderr.write("usage: parser.py <plan.json> <dc.raw> <tran.raw> <absent-out>\n")
    sys.exit(1)
plan_path, dc_path, tran_path, out_dir = sys.argv[1:5]
fails = []

def check(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        fails.append(msg)

def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()

def parse_raw(data, label):
    """ANCHORED (?m)^Variables: regex parse. Observed-Binary-only; payload
    starts immediately after the Binary: line ending (LF or CRLF) - no
    whitespace stripping. Payload length must EXACTLY equal nvar*npts*8."""
    text = data.decode("latin-1")
    plot = re.search(r"Plotname:\s*([^\n]*)", text).group(1).strip()
    nvar = int(re.search(r"No\. Variables:\s*(\d+)", text).group(1))
    npts = int(re.search(r"No\. Points:\s*(\d+)", text).group(1))
    vs = re.search(r"(?m)^Variables:\s*\n", text)
    if vs is None:
        raise ValueError("no line-start Variables: section")
    vstart = vs.end()
    m = re.search(r"\n\s*(Binary:|Values:)", text[vstart:])
    if m is None:
        raise ValueError("no Binary:/Values: marker after Variables:")
    marker = m.group(1)
    if marker != "Binary:":
        raise ValueError("unsupported '%s' layout - failing closed" % marker)
    vsec = text[vstart:vstart + m.start()]
    vnames, vtypes = [], []
    for ln in vsec.splitlines():
        ln = ln.strip()
        if not ln:
            continue
        parts = ln.split()
        if len(parts) >= 2:
            vnames.append(parts[1])
            vtypes.append(parts[2] if len(parts) >= 3 else "?")
    pos = vstart + m.start() + m.group(0).index("Binary:") + len("Binary:")
    if data[pos:pos + 2] == b"\r\n":
        pos += 2
    elif data[pos:pos + 1] == b"\n":
        pos += 1
    else:
        raise ValueError("no LF/CRLF terminator after the Binary: marker")
    body = data[pos:]
    need = nvar * npts * 8
    if len(body) != need:
        raise ValueError("payload length %d != required %d" % (len(body), need))
    vals = list(struct.unpack("<%dd" % (nvar * npts), body))
    return plot, nvar, npts, vnames, vtypes, vals, vals[0::nvar]

def col(vals, names, nm, nvar, npts):
    for idx, n in enumerate(names):
        if n == nm:
            return [vals[j * nvar + idx] for j in range(npts)]
    raise ValueError("no variable %s" % nm)

def interp(xs, ys, x):
    """Linear interpolation; xs strictly increasing. FAILS on out-of-range."""
    if not (xs[0] <= x <= xs[-1]):
        raise ValueError("out-of-range input %.17g (sweep %.17g..%.17g)" % (x, xs[0], xs[-1]))
    i = bisect.bisect_right(xs, x) - 1
    if i >= len(xs) - 1:
        return ys[-1]
    x0, x1 = xs[i], xs[i + 1]
    if x1 == x0:
        return ys[i]
    t = (x - x0) / (x1 - x0)
    return ys[i] + t * (ys[i + 1] - ys[i])

def zero_crossing_brackets(y):
    """SIGN CHANGES brackets: exact zeros are SKIPPED (they do not reset the
    last non-zero sign); a crossing is recorded as (i0, i1) when the sign
    flips between consecutive non-zero samples."""
    brackets = []
    prev_sign = 0
    prev_idx = None
    for i in range(len(y)):
        d = y[i]
        s = 1 if d > 0 else (-1 if d < 0 else 0)
        if s == 0:
            continue
        if prev_sign != 0 and s != prev_sign:
            brackets.append((prev_idx, i))
        prev_sign = s
        prev_idx = i
    return brackets

def fmt(v):
    return "%.17g" % v

# ---- bind hashes ----
check(sha(plan_path) == PLAN_EXPECTED, "plan.json hash matches the bound plan")
check(sha(dc_path) == DC_EXPECTED, "dc raw hash matches the bound dc raw")
check(sha(tran_path) == TRAN_EXPECTED, "tran raw hash matches the bound tran raw")
if fails:
    print("PARSER FAIL (hash bindings)")
    sys.exit(1)

# ---- plan object ----
plan = json.loads(open(plan_path, encoding="utf-8").read())
check(plan.get("dc_raw_sha256") == DC_EXPECTED, "plan dc_raw_sha256 matches bound dc raw")
check(plan.get("tran_raw_sha256") == TRAN_EXPECTED, "plan tran_raw_sha256 matches bound tran raw")
check(plan.get("signals") == SIGNALS, "plan signals match")
check(plan.get("method") == METHOD, "plan method matches")
check(plan.get("metrics") == METRICS, "plan metrics match")
check("dc_reference_range" in plan.get("metrics", []), "plan metrics carry dc_reference_range")
check(plan.get("zero_crossing_snapshots") == SNAPSHOTS, "plan snapshots count matches")
check(plan.get("read_only") is True and plan.get("status") == "unrun", "plan read_only/status")
check(plan.get("causal_claim") is False and plan.get("simulation") is False and plan.get("design_edit") is False,
      "plan no causal/simulation/design claims")
if fails:
    print("PARSER FAIL (plan object)")
    sys.exit(1)

# ---- out dir must be ABSENT ----
if os.path.exists(out_dir):
    print("FAIL output dir exists (%s) - STOP, nothing written" % out_dir)
    sys.exit(1)

# ---- parse DC raw (fail-closed) ----
dc_data = open(dc_path, "rb").read()
dc_plot, dc_nvar, dc_npts, dc_names, dc_types, dc_vals, dc_sweep = parse_raw(dc_data, "dc")
check(dc_names[0] == "v(v-sweep)" and dc_types[0] == "voltage", "DC index 0 exactly v(v-sweep)/voltage")
check(len(dc_names) == dc_nvar, "DC EXACTLY %d variable records (got %d)" % (dc_nvar, len(dc_names)))
check(len(dc_types) == dc_nvar, "DC EXACTLY %d variable type records (got %d)" % (dc_nvar, len(dc_types)))
check(len(dc_vals) == dc_nvar * dc_npts, "DC payload EXACTLY %d values (got %d)" % (dc_nvar * dc_npts, len(dc_vals)))
check(all(math.isfinite(v) for v in dc_vals), "DC all %d payload values finite" % len(dc_vals))
check(all(dc_sweep[i] < dc_sweep[i + 1] for i in range(len(dc_sweep) - 1)), "DC sweep strictly monotonic increasing")
for sig in SIGNALS:
    check(("v(xu1." + sig.lower() + ")") in dc_names, "DC signal present: v(xu1.%s)" % sig.lower())
if fails:
    print("PARSER FAIL (dc raw)")
    sys.exit(1)

# ---- parse TRAN raw (fail-closed) ----
tr_data = open(tran_path, "rb").read()
tr_plot, tr_nvar, tr_npts, tr_names, tr_types, tr_vals, tr_time = parse_raw(tr_data, "tran")
check(tr_names[0] == "time" and tr_types[0] == "time", "TRAN index 0 exactly time/time")
check(len(tr_names) == tr_nvar, "TRAN EXACTLY %d variable records (got %d)" % (tr_nvar, len(tr_names)))
check(len(tr_types) == tr_nvar, "TRAN EXACTLY %d variable type records (got %d)" % (tr_nvar, len(tr_types)))
check(len(tr_vals) == tr_nvar * tr_npts, "TRAN payload EXACTLY %d values (got %d)" % (tr_nvar * tr_npts, len(tr_vals)))
check(all(math.isfinite(v) for v in tr_vals), "TRAN all %d payload values finite" % len(tr_vals))
check(all(tr_time[i] < tr_time[i + 1] for i in range(len(tr_time) - 1)), "TRAN time strictly monotonic increasing")
for sig in SIGNALS:
    check(("v(xu1." + sig.lower() + ")") in tr_names, "TRAN signal present: v(xu1.%s)" % sig.lower())
check(INPUT_VAR in tr_names and "v(cml_n)" in tr_names, "TRAN input signals present")
if fails:
    print("PARSER FAIL (tran raw)")
    sys.exit(1)

# ---- same-input interpolation (input = actual v(cml_p) per transient sample) ----
dc_series = {sig: col(dc_vals, dc_names, "v(xu1." + sig.lower() + ")", dc_nvar, dc_npts) for sig in SIGNALS}
cml_p = col(tr_vals, tr_names, INPUT_VAR, tr_nvar, tr_npts)
cml_n = col(tr_vals, tr_names, "v(cml_n)", tr_nvar, tr_npts)
cml_diff = [a - b for a, b in zip(cml_p, cml_n)]
tran_series = {sig: col(tr_vals, tr_names, "v(xu1." + sig.lower() + ")", tr_nvar, tr_npts) for sig in SIGNALS}

refs = {sig: [] for sig in SIGNALS}
resids = {sig: [] for sig in SIGNALS}
try:
    for j in range(tr_npts):
        inp = cml_p[j]
        if not (dc_sweep[0] <= inp <= dc_sweep[-1]):
            raise ValueError("out-of-range input at sample %d: %.17g" % (j, inp))
        for sig in SIGNALS:
            ref = interp(dc_sweep, dc_series[sig], inp)
            res = tran_series[sig][j] - ref
            refs[sig].append(ref)
            resids[sig].append(res)
except ValueError as e:
    print("FAIL same-input interpolation: %s" % e)
    sys.exit(1)
ref_range = {sig: max(refs[sig]) - min(refs[sig]) for sig in SIGNALS}
zero_range = [sig for sig in SIGNALS if ref_range[sig] <= 0.0]
check(not zero_range, "reference range nonzero for all signals")
if zero_range:
    print("PARSER FAIL (zero reference range: %s)" % ", ".join(zero_range))
    sys.exit(1)
print("same-input interpolation complete: %d samples x %d signals" % (tr_npts, len(SIGNALS)))

# ---- ten crossings validated BEFORE any output construction ----
brackets = zero_crossing_brackets(cml_diff)
check(len(brackets) == SNAPSHOTS, "EXACTLY %d cml_diff zero crossings (got %d)" % (SNAPSHOTS, len(brackets)))
if len(brackets) != SNAPSHOTS:
    print("PARSER FAIL (crossing count) - nothing written, no mkdir")
    sys.exit(1)

# ---- build ALL THREE output byte strings IN MEMORY ----
series_hdr = ("point\ttime_s\tcml_p_V\tcml_diff_V"
              + "".join("\t%s_obs\t%s_ref\t%s_res" % (s, s, s) for s in SIGNALS))
series_rows = []
for j in range(tr_npts):
    row = "%d\t%s\t%s\t%s" % (j, fmt(tr_time[j]), fmt(cml_p[j]), fmt(cml_diff[j]))
    for sig in SIGNALS:
        row += "\t%s\t%s\t%s" % (fmt(tran_series[sig][j]), fmt(refs[sig][j]), fmt(resids[sig][j]))
    series_rows.append(row)
series_bytes = (series_hdr + "\n" + "\n".join(series_rows) + "\n").encode("utf-8")

summary = {"summary": {}, "input": INPUT_VAR, "method": METHOD,
           "plan_sha256": PLAN_EXPECTED, "dc_sha256": DC_EXPECTED,
           "tran_sha256": TRAN_EXPECTED, "zero_crossing_snapshots": SNAPSHOTS}
SUMMARY_SIG_KEYS = ["residual_min", "residual_max", "residual_rms",
                    "observed_range", "dc_reference_range", "range_ratio"]
for sig in SIGNALS:
    r = resids[sig]
    obs = tran_series[sig]
    rms = math.sqrt(sum(x * x for x in r) / len(r))
    obs_range = max(obs) - min(obs)
    summary["summary"][sig] = {
        "residual_min": fmt(min(r)), "residual_max": fmt(max(r)),
        "residual_rms": fmt(rms),
        "observed_range": fmt(obs_range), "dc_reference_range": fmt(ref_range[sig]),
        "range_ratio": fmt(obs_range / ref_range[sig]),
    }
summary_bytes = (json.dumps(summary, sort_keys=True, indent=2) + "\n").encode("utf-8")

snap_hdr = ("crossing\ttime_s\tcml_p_V\tcml_diff_V"
            + "".join("\t%s_obs\t%s_ref\t%s_res" % (s, s, s) for s in SIGNALS))
snap_rows = []
for k, (i0, i1) in enumerate(brackets, 1):
    t0, t1 = tr_time[i0], tr_time[i1]
    d0, d1 = cml_diff[i0], cml_diff[i1]
    if d1 == d0:
        tstar = t0
    else:
        tstar = t0 + (0.0 - d0) / (d1 - d0) * (t1 - t0)
    def lv(arr):
        if t1 == t0:
            return arr[i0]
        u = (tstar - t0) / (t1 - t0)
        return arr[i0] + u * (arr[i1] - arr[i0])
    inp_star = lv(cml_p)
    cdiff_star = lv(cml_diff)
    row = "%d\t%s\t%s\t%s" % (k, fmt(tstar), fmt(inp_star), fmt(cdiff_star))
    for sig in SIGNALS:
        obs_star = lv(tran_series[sig])
        ref_star = interp(dc_sweep, dc_series[sig], inp_star)
        row += "\t%s\t%s\t%s" % (fmt(obs_star), fmt(ref_star), fmt(obs_star - ref_star))
    snap_rows.append(row)
snap_bytes = (snap_hdr + "\n" + "\n".join(snap_rows) + "\n").encode("utf-8")

# ---- validate ALL THREE before mkdir ----
check(series_hdr == ("point\ttime_s\tcml_p_V\tcml_diff_V"
                     + "".join("\t%s_obs\t%s_ref\t%s_res" % (s, s, s) for s in SIGNALS)),
      "SERIES header exact")
check(len(series_rows) == tr_npts, "SERIES row count EXACTLY %d" % tr_npts)
check(snap_hdr == ("crossing\ttime_s\tcml_p_V\tcml_diff_V"
                   + "".join("\t%s_obs\t%s_ref\t%s_res" % (s, s, s) for s in SIGNALS)),
      "SNAPSHOTS header exact")
check(len(snap_rows) == SNAPSHOTS, "SNAPSHOTS row count EXACTLY %d" % SNAPSHOTS)
check(set(summary.keys()) == {"summary", "input", "method", "plan_sha256",
                              "dc_sha256", "tran_sha256", "zero_crossing_snapshots"},
      "SUMMARY top-level key set exact")
for sig in SIGNALS:
    check(set(summary["summary"][sig].keys()) == set(SUMMARY_SIG_KEYS),
          "SUMMARY per-signal key set exact (%s)" % sig)
check(all(("dc_reference_range" in summary["summary"][sig]) for sig in SIGNALS)
      and all(("reference_range" not in summary["summary"][sig]) for sig in SIGNALS),
      "SUMMARY uses dc_reference_range (no bare reference_range)")
check(series_bytes.endswith(b"\n") and summary_bytes.endswith(b"\n") and snap_bytes.endswith(b"\n"),
      "all three outputs end with final LF")
if fails:
    print("PARSER FAIL (in-memory output validation) - nothing written, no mkdir")
    sys.exit(1)

# ---- mkdir ONLY after every check, then exclusive-write EXACTLY the three files ----
os.makedirs(out_dir)
written = []
for rel, payload in ((OUT_FILES[0], series_bytes), (OUT_FILES[1], summary_bytes),
                     (OUT_FILES[2], snap_bytes)):
    p = os.path.join(out_dir, rel)
    with open(p, "xb") as f:
        f.write(payload)
    written.append(rel)
check(set(os.listdir(out_dir)) == set(OUT_FILES),
      "out dir closure EXACTLY %s" % "/".join(OUT_FILES))

print("SERIES.tsv written (%d rows)" % tr_npts)
print("SUMMARY.json written")
print("SNAPSHOTS.tsv written (%d rows)" % len(snap_rows))
print("PARSER DONE")
sys.exit(0)

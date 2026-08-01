#!/usr/bin/env python3
"""extract_stage1_replay_waveforms.py - deterministic replay-input extraction.

Reads the sealed MATCHED-LOAD-ISOLATION-RUNTIME-V1 raws and extracts EVERY full
0..4 ns native time/value sample for v(div2_p_1) and v(div2_n_1) - no
decimation, no interpolation - into four PWL FILE replay inputs:
  UNLOADED-REPLAY arm (from CONTROL raw 8317c689...):
    replay_unloaded_div2_p_1.pwl , replay_unloaded_div2_n_1.pwl
  LOADED-REPLAY arm (from EXPERIMENT raw dd0f874e...):
    replay_loaded_div2_p_1.pwl , replay_loaded_div2_n_1.pwl
PWL file format (ngspice PWL FILE): one "time value" pair per line, native
double precision via repr, full sample count, no truncation.

Outputs are written to the target directory with O_EXCL (fail-closed if any
exists). GUARDED: STAGE2_REPLAY_EXTRACT_V1=1.
"""
import os, sys, re, struct, hashlib

if os.environ.get("STAGE2_REPLAY_EXTRACT_V1") != "1":
    print("GUARDED: STAGE2_REPLAY_EXTRACT_V1=1 marker required; no write.")
    sys.exit(1)

PAIR = os.environ.get("MATCHED_LOAD_RUNTIME", "../../../custom-cml-div4-matched-load-isolation-v1/runtime")
CTLRAW = PAIR + "/CONTROL-RUN/raw_tb_p1_cml_div2_front_x1_unloaded_tran_v1.raw"
EXPRAW = PAIR + "/EXPERIMENT-RUN/raw_tb_p1_cml_div2_front_x2_div4_tran_v1.raw"
OUTDIR = os.environ.get("REPLAY_OUTDIR", "replay-output-v1")

EXP_CTL = "8317c689599ff6145f6ff8a70e5dbc4b4e05d8dc870b5d44e91b3fce9e6695f0"
EXP_EXP = "dd0f874ee53e1fff13581f99e3db04185b166705244e81be9ca59a2918a9a97f"

def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()

def oexcl(path, data):
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    try:
        os.write(fd, data.encode())
    finally:
        os.close(fd)

def load_raw(path):
    b = open(path, "rb").read()
    m = b.find(b"Binary:\n")
    assert m > 0
    hdr = b[:m].decode(errors="replace")
    nvar = int(re.search(r"No\. Variables:\s*(\d+)", hdr).group(1))
    npts = int(re.search(r"No\. Points:\s*(\d+)", hdr).group(1))
    payload = b[m + len(b"Binary:\n"):]
    assert len(payload) == nvar * npts * 8
    vidx = {}
    for ln in hdr.splitlines():
        mm = re.match(r"\s*(\d+)\s+(\S+)\s+(\S+)", ln)
        if mm:
            vidx[mm.group(2).lower()] = int(mm.group(1))
    def col(name):
        k = vidx.get(name.lower())
        assert k is not None, name
        return [struct.unpack_from("<d", payload, (p * nvar + k) * 8)[0] for p in range(npts)]
    return nvar, npts, col

# bind raws
assert sha(CTLRAW) == EXP_CTL
assert sha(EXPRAW) == EXP_EXP

_, npts_c, col_c = load_raw(CTLRAW)
_, npts_e, col_e = load_raw(EXPRAW)
assert npts_c == npts_e == 2284

tc = col_c("time")
te = col_e("time")
c_p, c_n = col_c("v(div2_p_1)"), col_c("v(div2_n_1)")
e_p, e_n = col_e("v(div2_p_1)"), col_e("v(div2_n_1)")

def pwl_lines(t, v):
    return ["%.17g\t%.17g" % (t[i], v[i]) for i in range(len(t))] + [""]

os.makedirs(OUTDIR, exist_ok=False)
files = {
    "replay_unloaded_div2_p_1.pwl": pwl_lines(tc, c_p),
    "replay_unloaded_div2_n_1.pwl": pwl_lines(tc, c_n),
    "replay_loaded_div2_p_1.pwl":   pwl_lines(te, e_p),
    "replay_loaded_div2_n_1.pwl":   pwl_lines(te, e_n),
}
for fn, lines in files.items():
    oexcl(OUTDIR + "/" + fn, "\n".join(lines))
    print("%s samples=%d lines=%d sha256=%s"
          % (fn, len(lines) - 1, len(lines), sha(OUTDIR + "/" + fn)))

# verify no decimation: sample count == point count per raw
assert len(files["replay_unloaded_div2_p_1.pwl"]) - 1 == npts_c
assert len(files["replay_loaded_div2_p_1.pwl"]) - 1 == npts_e
# verify full 0..4 ns span
assert tc[0] == 0.0 and abs(tc[-1] - 4.0e-9) < 1e-15
assert te[0] == 0.0 and abs(te[-1] - 4.0e-9) < 1e-15
# verify monotonic time (native order preserved)
assert all(tc[i + 1] > tc[i] for i in range(len(tc) - 1))
assert all(te[i + 1] > te[i] for i in range(len(te) - 1))
print("extraction complete: 4 replay inputs, %d samples each, full 0..4 ns span" % npts_c)

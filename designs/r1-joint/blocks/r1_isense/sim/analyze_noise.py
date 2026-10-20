#!/usr/bin/env python3
"""Collect the 'R:' lines of tb_isense_noise logs into summary.json."""
import sys, os, json, glob, re
rdir, tdir = sys.argv[1], sys.argv[2]
out = {}
for f in sorted(glob.glob(os.path.join(rdir, "*.log"))):
    c = os.path.basename(f)[len("tb_isense_noise_"):-4]
    d = {}
    for line in open(f, errors="replace"):
        if line.startswith("R:"):
            toks = line[2:].replace("=", " = ").split()
            for i, tok in enumerate(toks):
                if tok == "=" and i > 0 and i + 1 < len(toks):
                    try: d[toks[i - 1]] = float(toks[i + 1])
                    except ValueError: pass
    nf = os.path.join(rdir, c + "_noise.txt")
    if os.path.exists(nf):
        rows = []
        with open(nf) as fh:
            fh.readline()
            for line in fh:
                p = line.split()
                if len(p) >= 3: rows.append((float(p[0]), float(p[1])))
        for fq in (1e3, 1e4, 1e5, 1e6):
            r = min(rows, key=lambda r: abs(r[0] - fq))
            d["in_nV_rtHz_at_%g" % fq] = r[1] * 1e9
        # 1/f corner: frequency where density falls to sqrt(2) x the 1 MHz value
        w = d["in_nV_rtHz_at_1e+06"] * 2 ** 0.5
        cr = [r[0] for r in rows if r[1] * 1e9 <= w and r[0] < 1e6]
        d["corner_Hz_sqrt2_of_1MHz"] = min(cr) if cr else None
    out[c] = d
summ = {"result": out, "criteria": "closed-loop -3 dB bandwidth >= 1 MHz; report noise",
        "disposition": "bandwidth >= 1 MHz: " + ", ".join("%s %s" % (c, "passed" if d.get("f3dB_Hz", 0) >= 1e6 else "failed") for c, d in sorted(out.items()))}
json.dump(summ, open(os.path.join(tdir, "summary.json"), "w"), indent=1)
print(json.dumps(summ, indent=1))

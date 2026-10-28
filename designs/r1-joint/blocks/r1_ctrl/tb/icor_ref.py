#!/usr/bin/env python3
"""Integer model of the D27 phase-current correction (r1_ctrl revision 0.9, rtl/r1_icor.v) and the bit-exact check of
tb/tb_icor.v against it.
  python3 icor_ref.py gen <dir>      write icor_<case>_stim.hex and icor_<case>_exp.txt for every case
  python3 icor_ref.py check <dir>    compare icor_<case>_out.txt with the model, write icor_result.json
Model (register map 0.9 section 4.7):
  d = (RAW - 2048) - OFS              OFS: 12-bit two's complement, subtracted
  q = floor((d * GAIN + 8192) / 16384) GAIN: unsigned Q2.14
  I = min(4095, max(0, q + 2048))
SPDX-License-Identifier: Apache-2.0"""
import json
import random
import sys


def s12(x):
    return x - 4096 if x & 0x800 else x


def icor(raw, ofs, gain):
    d = (raw - 2048) - s12(ofs)
    q = (d * gain + 8192) >> 14            # Python >> on int is floor division by 2^14
    return min(4095, max(0, q + 2048))


def cases():
    rnd = random.Random(20261030)
    C = {}
    # id: reset words, every code on both channels (A ascending, B descending)
    C["id"] = [(r, 4095 - r, 0, 0, 0x4000, 0x4000) for r in range(4096)]
    # rnd: random codes and words over the full register range
    C["rnd"] = [(rnd.randrange(4096), rnd.randrange(4096), rnd.randrange(4096), rnd.randrange(4096),
                 rnd.randrange(65536), rnd.randrange(65536)) for _ in range(8192)]
    # sat: corner codes x corner offsets x corner gains (both saturation ends, rounding at the half LSB)
    R = [0, 1, 2047, 2048, 2049, 4094, 4095]
    O = [0x800, 0xFFF, 0, 1, 0x7FF]                  # -2048, -1, 0, 1, +2047
    G = [0, 1, 0x2000, 0x3FFF, 0x4000, 0x4001, 0x6000, 0x8000, 0xFFFF]
    v = [(r, R[(i + 3) % 7], o, O[(j + 2) % 5], g, G[(k + 4) % 9])
         for i, r in enumerate(R) for j, o in enumerate(O) for k, g in enumerate(G)]
    C["sat"] = v
    # cal: field range of the words (gain 0.75 .. 1.25, offset +-200 LSB) on the r1_top current levels
    C["cal"] = [(rnd.randrange(600, 3600), rnd.randrange(600, 3600), rnd.randrange(-200, 201) & 0xFFF,
                 rnd.randrange(-200, 201) & 0xFFF, rnd.randrange(12288, 20481), rnd.randrange(12288, 20481))
                for _ in range(4096)]
    # restart: pairs of vectors 10 ticks apart (tb +restart=1); the second of each pair must win
    C["restart"] = [(rnd.randrange(4096), rnd.randrange(4096), rnd.randrange(4096), rnd.randrange(4096),
                     rnd.randrange(65536), rnd.randrange(65536)) for _ in range(512)]
    return C


def gen(d):
    for name, v in cases().items():
        with open(f"{d}/icor_{name}_stim.hex", "w") as f:
            for ra, rb, oa, ob, ga, gb in v:
                f.write("%03x%03x%03x%03x%04x%04x\n" % (ra, rb, oa, ob, ga, gb))
        with open(f"{d}/icor_{name}_exp.txt", "w") as f:
            for ra, rb, oa, ob, ga, gb in (v[1::2] if name == "restart" else v):
                f.write("I %d %d\n" % (icor(ra, oa, ga), icor(rb, ob, gb)))
        print(name, len(v), "vectors")


def check(d):
    res = {"model": __doc__.strip().splitlines()[0], "cases": {}, "passed": True}
    for name, v in cases().items():
        try:
            out = [l.split() for l in open(f"{d}/icor_{name}_out.txt") if l.startswith("I ")]
        except OSError:
            out = []
        if name == "restart":
            v = v[1::2]                                   # only the second vector of each pair is expected
        exp = [(icor(ra, oa, ga), icor(rb, ob, gb)) for ra, rb, oa, ob, ga, gb in v]
        mism = sum(1 for o, e in zip(out, exp) if (int(o[1]), int(o[2])) != e) + abs(len(out) - len(exp))
        nsat = sum(1 for e in exp for x in e if x in (0, 4095))
        ident = sum(1 for (ra, rb, oa, ob, ga, gb), e in zip(v, exp) if (ga, gb, oa, ob) == (0x4000, 0x4000, 0, 0) and e != (ra, rb))
        res["cases"][name] = {"vectors": len(v), "outputs": len(out), "mismatches": mism, "saturated_outputs": nsat,
                              "identity_violations_at_reset_words": ident}
        if mism or ident or len(out) != len(v):
            res["passed"] = False
    res["criteria"] = "every vector bit-exact (both channels), identity at the reset words, all vectors present"
    json.dump(res, open(f"{d}/icor_result.json", "w"), indent=1)
    print(json.dumps(res, indent=1))
    return res["passed"]


if __name__ == "__main__":
    if sys.argv[1] == "gen":
        gen(sys.argv[2])
    else:
        sys.exit(0 if check(sys.argv[2]) else 1)

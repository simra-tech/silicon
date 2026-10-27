#!/usr/bin/env python3
"""Integer model and stimulus for the D22 channel correction of r1_pos (revision 0.8).

  d22_ref.py gen   <outdir>   write the stimulus and register files of all cases
  d22_ref.py check <outdir>   compare tb_d22 output with the model (bit-exact) and
                              compute the position error before / after the correction

The model is the r1_pos measurement path written from rtl/r1_pos.v at the bit level:
  ds = (sin - 2048) - SIN_OFS, dc = (cos - 2048) - COS_OFS             (13-bit signed, ADC LSB)
  cy = sat18((dc * COS_GAIN) >> 10)    (IDLE tick, 4 fractional bits; Q2.14 gain)
  cx = sat18((ds * SIN_GAIN) >> 10)    (S_M1)
  cx = sat18(cx - ((cy * PH_SIN) >> 15))                              (S_M2)
  y  = clamp22((cx * PH_ICOS) >> 14), x = cy                          (S_M3)
  CORDIC input limit +-49151, quadrant pre-rotation, 18 vectoring iterations
  (18-bit wrap), amplitude = (x * 19898) >> 19 (12 bit, saturated), 3rd-harmonic
  correction with the r1_sinlut table. ">>" is the arithmetic (floor) shift.

Stimulus (case raw / cor): one electrical turn in 4096 equal steps (phase offset 0.3 step),
amplitude 1638 LSB (1.44 Vpp at the ADC, D16; 1 LSB = 1.8 V / 4096 = 0.4395 mV), offsets
+57 LSB (sine, +25.0 mV) and -57 LSB (cosine, -25.0 mV), sine gain 1.03 (3 % mismatch).
Case raw: registers at reset (no correction). Case cor: registers from the host calibration
on the min/max of the same codes (what RAW_SIN_MIN/MAX, RAW_COS_MIN/MAX hold after one turn):
  OFS_x = round((max + min) / 2) - 2048,  A_x = (max - min) / 2,  A_t = (A_s + A_c) / 2,
  GAIN_x = round(16384 * A_t / A_x).
Case sat: random full-range codes with extreme registers (offsets -2048 / +2047, gains
0xFFFF / 0x0000 ... ) to cover every saturation branch. Case full: random codes and random
registers including PH_SIN, PH_ICOS and H3 (bit-exactness of the whole path).
SPDX-License-Identifier: Apache-2.0
"""
import json
import math
import os
import re
import sys

N = 4096
AMP = 1638.0
OFS_S, OFS_C = 57.0, -57.0
GAIN_S, GAIN_C = 1.03, 1.0
LSB_MV = 1800.0 / 4096
HERE = os.path.dirname(os.path.abspath(__file__))


def sx(v, w):
    v &= (1 << w) - 1
    return v - (1 << w) if v >> (w - 1) else v


def sat(v, lim):
    return lim if v > lim else (-lim if v < -lim else v)


def sinlut():
    """r1_sinlut table parsed from the RTL (quarter wave, folded)."""
    txt = open(os.path.join(HERE, "..", "rtl", "r1_sinlut.v")).read()
    q = {int(a): int(b) for a, b in re.findall(r"7'd(\d+):\s*q\s*=\s*7'd(\d+);", txt)}
    lut = []
    for idx in range(256):
        m = (64 - (idx & 63)) if (idx >> 6) & 1 else (idx & 63)
        v = q.get(m, 0)
        lut.append(-v if idx >> 7 else v)
    return lut


ATAN = [32768, 19344, 10221, 5188, 2604, 1303, 652, 326, 163, 81, 41, 20, 10, 5, 3, 1, 1, 0]
LUT = sinlut()


def model(sin_code, cos_code, r):
    """meas_angle (18 bit) and amplitude (12 bit) of one pair."""
    ds = sx((sin_code - 2048) - sx(r["sin_ofs"], 12), 13)
    dc = sx((cos_code - 2048) - sx(r["cos_ofs"], 12), 13)
    cy = sat((dc * r["cos_gain"]) >> 10, 131071)
    cx = sat((ds * r["sin_gain"]) >> 10, 131071)
    d = cx - sx((cy * sx(r["ph_sin"], 16)) >> 15, 22)
    cx = sat(d, 131071)
    y4 = sat((cx * r["ph_icos"]) >> 14, 2097151)
    x5, y5 = sat(cy, 49151), sat(y4, 49151)
    if x5 < 0:
        if y5 >= 0:
            cx, cy, cz = y5, -x5, 0x10000
        else:
            cx, cy, cz = -y5, x5, 0x30000
    else:
        cx, cy, cz = x5, y5, 0
    for i in range(18):
        if cy >= 0:
            cx, cy, cz = cx + (cy >> i), cy - (cx >> i), cz + ATAN[i]
        else:
            cx, cy, cz = cx - (cy >> i), cy + (cx >> i), cz - ATAN[i]
        cx, cy, cz = sx(cx, 18), sx(cy, 18), cz & 0x3FFFF
    a = (cx * 19898) >> 19
    amp = 4095 if (a < 0 or a > 4095) else a
    h3_amp, h3_ph = r["h3"] & 0xFF, (r["h3"] >> 8) & 0xFF
    idx = (((cz >> 8) & 0xFF) + h3_ph) & 0xFF
    corr = (LUT[idx] * h3_amp) >> 5
    th = (cz - (corr & 0x3FFFF)) & 0x3FFFF
    return th, amp


RESET = dict(sin_ofs=0, cos_ofs=0, sin_gain=0x4000, cos_gain=0x4000, ph_sin=0, ph_icos=0x4000, h3=0)
ORDER = ["sin_ofs", "cos_ofs", "sin_gain", "cos_gain", "ph_sin", "ph_icos", "h3"]


def truth():
    return [2 * math.pi * (k + 0.3) / N for k in range(N)]


def codes_meas():
    out = []
    for p in truth():
        s = int(round(2048 + OFS_S + GAIN_S * AMP * math.sin(p)))
        c = int(round(2048 + OFS_C + GAIN_C * AMP * math.cos(p)))
        out.append((min(max(s, 0), 4095), min(max(c, 0), 4095)))
    return out


def host_cal(codes):
    s = [a for a, _ in codes]
    c = [b for _, b in codes]
    smin, smax, cmin, cmax = min(s), max(s), min(c), max(c)
    os_ = int(math.floor((smax + smin) / 2.0 + 0.5)) - 2048
    oc = int(math.floor((cmax + cmin) / 2.0 + 0.5)) - 2048
    a_s, a_c = (smax - smin) / 2.0, (cmax - cmin) / 2.0
    a_t = (a_s + a_c) / 2.0
    r = dict(RESET)
    r.update(sin_ofs=os_ & 0xFFF, cos_ofs=oc & 0xFFF,
             sin_gain=int(round(16384 * a_t / a_s)), cos_gain=int(round(16384 * a_t / a_c)))
    return r, dict(sin_min=smin, sin_max=smax, cos_min=cmin, cos_max=cmax)


def cases():
    import random
    rng = random.Random(20261028)
    meas = codes_meas()
    rcal, mm = host_cal(meas)
    out = {"raw": (meas, dict(RESET)), "cor": (meas, rcal)}
    rnd = [(rng.randrange(4096), rng.randrange(4096)) for _ in range(N)]
    out["sat"] = (rnd, dict(sin_ofs=0x800, cos_ofs=0x7FF, sin_gain=0xFFFF, cos_gain=0xFFFF,
                            ph_sin=0x7FFF, ph_icos=0xFFFF, h3=0xFF80))
    out["full"] = (rnd[::-1], dict(sin_ofs=rng.randrange(4096), cos_ofs=rng.randrange(4096),
                                   sin_gain=rng.randrange(0x3000, 0x5001), cos_gain=rng.randrange(0x3000, 0x5001),
                                   ph_sin=rng.randrange(65536), ph_icos=rng.randrange(0x3800, 0x4800),
                                   h3=rng.randrange(65536)))
    # low gain bound and zero gain (amplitude 0, angle of a zero vector)
    out["lo"] = (rnd, dict(RESET, sin_gain=0x3000, cos_gain=0x0000, sin_ofs=0x7FF, cos_ofs=0x800))
    return out, mm


def gen(outdir):
    cs, mm = cases()
    for name, (codes, r) in cs.items():
        with open(os.path.join(outdir, f"d22_{name}_stim.hex"), "w") as fh:
            for s, c in codes:
                fh.write(f"{s:03x}{c:03x}\n")
        with open(os.path.join(outdir, f"d22_{name}_regs.hex"), "w") as fh:
            for k in ORDER:
                fh.write(f"{r[k]:04x}\n")
        with open(os.path.join(outdir, f"d22_{name}_regs.json"), "w") as fh:
            json.dump(r, fh, indent=1)
    with open(os.path.join(outdir, "d22_minmax_model.json"), "w") as fh:
        json.dump(mm, fh, indent=1)
    print("gen", list(cs), "minmax", mm, "cor regs", {k: hex(v) for k, v in cs["cor"][1].items()})


def check(outdir):
    cs, mm = cases()
    res = {"model": "tb/d22_ref.py (integer model of rtl/r1_pos.v)", "n": N, "cases": {}}
    ok_all = True
    th_true = truth()
    for name, (codes, r) in cs.items():
        fn = os.path.join(outdir, f"d22_{name}_out.txt")
        rtl = []
        for line in open(fn):
            if line.startswith("M "):
                _, a, b = line.split()
                rtl.append((int(a), int(b)))
        exp = [model(s, c, r) for s, c in codes]
        mism = [i for i, (e, g) in enumerate(zip(exp, rtl)) if e != g]
        ok = len(rtl) == N and not mism
        ok_all &= ok
        d = {"points": len(rtl), "mismatches": len(mism), "first_mismatch": mism[:5], "bit_exact": ok,
             "regs": {k: hex(v) for k, v in r.items()}}
        if name in ("raw", "cor"):
            err = []
            for (th, _), p in zip(rtl, th_true):
                e = th / 2 ** 18 * 360.0 - math.degrees(p)
                err.append((e + 180.0) % 360.0 - 180.0)
            mean = sum(err) / len(err)
            d["pos_err_deg_el"] = {"max_abs": max(abs(e) for e in err), "mean": mean,
                                    "pk_pk": max(err) - min(err),
                                    "max_abs_minus_mean": max(abs(e - mean) for e in err)}
            d["amplitude_lsb"] = {"min": min(a for _, a in rtl), "max": max(a for _, a in rtl)}
        res["cases"][name] = d
        print(f"{name}: {len(rtl)} points, {len(mism)} mismatches", d.get("pos_err_deg_el", ""))
    e0 = res["cases"]["raw"]["pos_err_deg_el"]["max_abs"]
    e1 = res["cases"]["cor"]["pos_err_deg_el"]["max_abs"]
    res["stimulus"] = dict(amp_lsb=AMP, ofs_sin_lsb=OFS_S, ofs_cos_lsb=OFS_C, ofs_mv=OFS_S * LSB_MV,
                           gain_sin=GAIN_S, gain_cos=GAIN_C, minmax=mm)
    # criteria: bit-exact on every case; before > 1 deg el; after <= 0.05 deg el (V3 limit)
    res["criteria"] = "bit-exact all cases; raw max error > 1 deg el; cor max error <= 0.05 deg el"
    res["passed"] = bool(ok_all and e0 > 1.0 and e1 <= 0.05)
    with open(os.path.join(outdir, "d22_result.json"), "w") as fh:
        json.dump(res, fh, indent=1)
    print("D22", "PASSED" if res["passed"] else "FAILED", f"error before {e0:.3f} after {e1:.4f} deg el")
    return 0 if res["passed"] else 1


if __name__ == "__main__":
    if sys.argv[1] == "gen":
        gen(sys.argv[2])
    else:
        sys.exit(check(sys.argv[2]))

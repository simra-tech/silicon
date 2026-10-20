#!/usr/bin/env python3
"""Floating-point reference and host calibration for the r1_pos testbench (V3).

  pos_ref.py gen   <case> <outdir>   write stimulus, register values and truth
  pos_ref.py check <case> <outdir>   compare the RTL output with truth and the reference

Head model (S1 tolerance set, values in ADC LSB, 12-bit signed, full scale +-2048):
  cos_m = Ac*(cos p + h3*cos 3p) + Oc
  sin_m = As*(sin(p+a) - h3*sin 3(p+a)) + Os
with Ac = 1400, As = gain*Ac, Oc = Os = offset*Ac, a = phase. The h3 sign pair is the
"same waveform on both channels" case, whose angle error sits at 4p.

Host calibration (what the host does with RAW_SIN/RAW_COS over one period, no reference
encoder): least-squares conic fit -> offsets, gain ratio, phase; then the 4th-harmonic
modulation of the corrected radius -> H3_AMP, H3_PH. Register formats: R1_REGISTER_MAP.md.
SPDX-License-Identifier: Apache-2.0
"""
import json
import math
import sys

import numpy as np

TICK_HZ = 30e6
PAIR_TICKS = 30

CASES = {
    # name: head errors, electrical frequency, number of pairs, calibrate?, noise, extrap ticks
    "ideal":       dict(ofs=0.0,   gain=1.0,  ph=0.0,  h3=0.0,  f=1e3,  n=2000, cal=False, noise=0.0, extrap=0),
    "uncal":       dict(ofs=0.065, gain=1.25, ph=10.0, h3=0.01, f=1e3,  n=2000, cal=False, noise=0.0, extrap=0),
    "cal":         dict(ofs=0.065, gain=1.25, ph=10.0, h3=0.01, f=1e3,  n=2000, cal=True,  noise=0.0, extrap=0),
    "cal_self":    dict(ofs=0.065, gain=1.25, ph=10.0, h3=0.01, f=1e3,  n=2000, cal=True,  noise=0.0, extrap=0, self=True),
    "cal_noise":   dict(ofs=0.065, gain=1.25, ph=10.0, h3=0.01, f=1e3,  n=2000, cal=True,  noise=0.5, extrap=0),
    "cal_neg":     dict(ofs=-0.065, gain=0.8, ph=-10.0, h3=0.01, f=-1e3, n=2000, cal=True, noise=0.0, extrap=0),
    "fast_k0":     dict(ofs=0.065, gain=1.25, ph=10.0, h3=0.01, f=50e3, n=2000, cal=True,  noise=0.0, extrap=0),
    "fast_k30":    dict(ofs=0.065, gain=1.25, ph=10.0, h3=0.01, f=50e3, n=2000, cal=True,  noise=0.0, extrap=30),
    "fast_100k":   dict(ofs=0.065, gain=1.25, ph=10.0, h3=0.01, f=100e3, n=2000, cal=True, noise=0.0, extrap=0),
    # revision 0.3: D17 ADC frame of 36 ticks (833 k pairs/s at 30 MHz). f0: start frequency of a linear
    # ramp to f over the first `ramp` pairs (the loop acquires at f0, then must track the ramp).
    "f36_100k":    dict(ofs=0.065, gain=1.25, ph=10.0, h3=0.01, f=100e3, n=2000, cal=True, noise=0.0, extrap=0, pair=36),
    "f36_208k":    dict(ofs=0.065, gain=1.25, ph=10.0, h3=0.01, f=208e3, n=3000, cal=True, noise=0.0, extrap=0, pair=36,
                        f0=20e3, ramp=1000),
    "f36_208k_n":  dict(ofs=0.065, gain=1.25, ph=10.0, h3=0.01, f=208e3, n=3000, cal=True, noise=0.5, extrap=0, pair=36,
                        f0=20e3, ramp=1000),
    # item 7 (coordinator): 250 kHz, maximum acceleration, and one frame slot per PWM period taken by the
    # current pair (skip = 42 slots of 36 ticks = 1512 ticks, 19.8 kHz PWM: a 72-tick (2.4 us) encoder gap).
    # acc: ramp acceleration in Hz/s (electrical) starting at frame ramp_start. Loop limit (KP 2, KI 11, 36 ticks):
    # steady error e = acc/f_clk^2 * 36 * 2^11 turn; e = 45 deg (snap threshold) at 1.526e9 Hz/s = 9.59e9 rad/s^2.
    "f36_208k_gap": dict(ofs=0.065, gain=1.25, ph=10.0, h3=0.01, f=208e3, n=3000, cal=True, noise=0.0, extrap=0, pair=36,
                         f0=20e3, ramp=1000, skip=42),
    "f36_250k":    dict(ofs=0.065, gain=1.25, ph=10.0, h3=0.01, f=250e3, n=3000, cal=True, noise=0.0, extrap=0, pair=36,
                        f0=20e3, ramp=1000),
    "f36_250k_gap": dict(ofs=0.065, gain=1.25, ph=10.0, h3=0.01, f=250e3, n=3000, cal=True, noise=0.0, extrap=0, pair=36,
                         f0=20e3, ramp=1000, skip=42),
    "f36_250k_amax": dict(ofs=0.065, gain=1.25, ph=10.0, h3=0.01, f=250e3, n=2000, cal=True, noise=0.5, extrap=0, pair=36,
                          f0=20e3, acc=1.5e9, ramp_start=300),
    "f36_250k_amax_gap": dict(ofs=0.065, gain=1.25, ph=10.0, h3=0.01, f=250e3, n=2000, cal=True, noise=0.5, extrap=0,
                              pair=36, f0=20e3, acc=1.5e9, ramp_start=300, skip=42),
    "f36_250k_alim_gap": dict(ofs=0.065, gain=1.25, ph=10.0, h3=0.01, f=250e3, n=2000, cal=True, noise=0.5, extrap=0, pair=36,
                          f0=20e3, acc=1.2e9, ramp_start=300, skip=42),
    # D18 (coordinator, 2026-10-20): encoder pair every 22-tick frame; one frame per PWM period (every 68th slot,
    # 1496 ticks = 20.05 kHz) carries the current pair -> one 44-tick encoder gap. Limit for 45 deg at T = 22:
    # 0.125 * f_clk^2 / (22 * 2^11) = 2.50e9 Hz/s = 1.57e10 rad/s^2 (model; the RTL latency adds lag).
    "f22_100k_gap": dict(ofs=0.065, gain=1.25, ph=10.0, h3=0.01, f=100e3, n=3000, cal=True, noise=0.0, extrap=0, pair=22,
                         skip=68),
    "f22_208k_gap": dict(ofs=0.065, gain=1.25, ph=10.0, h3=0.01, f=208e3, n=4000, cal=True, noise=0.0, extrap=0, pair=22,
                         f0=20e3, ramp=1500, skip=68),
    "f22_250k":     dict(ofs=0.065, gain=1.25, ph=10.0, h3=0.01, f=250e3, n=4000, cal=True, noise=0.0, extrap=0, pair=22,
                         f0=20e3, ramp=1500),
    "f22_250k_gap": dict(ofs=0.065, gain=1.25, ph=10.0, h3=0.01, f=250e3, n=4000, cal=True, noise=0.0, extrap=0, pair=22,
                         f0=20e3, ramp=1500, skip=68),
    "f22_250k_amax_gap": dict(ofs=0.065, gain=1.25, ph=10.0, h3=0.01, f=250e3, n=3000, cal=True, noise=0.5, extrap=0,
                              pair=22, f0=20e3, acc=2.0e9, ramp_start=300, skip=68),
    "f22_250k_alim_gap": dict(ofs=0.065, gain=1.25, ph=10.0, h3=0.01, f=250e3, n=3000, cal=True, noise=0.0, extrap=0,
                              pair=22, f0=20e3, acc=2.5e9, ramp_start=300, skip=68),
    "f22_250k_a2x_gap": dict(ofs=0.065, gain=1.25, ph=10.0, h3=0.01, f=250e3, n=3000, cal=True, noise=0.0, extrap=0,
                             pair=22, f0=20e3, acc=4.0e9, ramp_start=300, skip=68, info=True),
    "f36_250k_a2x": dict(ofs=0.065, gain=1.25, ph=10.0, h3=0.01, f=250e3, n=2000, cal=True, noise=0.0, extrap=0, pair=36,
                         f0=20e3, acc=3.0e9, ramp_start=300, info=True),
}
AC = 1400.0
H3_PSI = 0.7      # phase of the 3rd harmonic in the head model, rad (arbitrary, not 0)
SEED = 20261020


def head(p, c):
    a = math.radians(c["ph"])
    As = c["gain"] * AC
    cm = AC * (np.cos(p) + c["h3"] * np.cos(3 * p + H3_PSI)) + c["ofs"] * AC
    sm = As * (np.sin(p + a) - c["h3"] * np.sin(3 * (p + a) + H3_PSI)) + c["ofs"] * AC * 0.8
    return sm, cm


def quant(v, rng, noise):
    if noise > 0:
        v = v + rng.normal(0.0, noise, size=v.shape)
    q = np.clip(np.round(v), -2048, 2047).astype(int)
    return q


def wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def default_regs():
    return dict(ofs_sin=0, ofs_cos=0, gain=0x4000, ph_sin=0, ph_icos=0x4000, h3_amp=0, h3_ph=0)


def correct_float(s, c, r):
    """Float model of the r1_pos correction chain with quantized register values."""
    gain = r["gain"] / 2.0 ** 14
    sa = (r["ph_sin"] - 65536 if r["ph_sin"] >= 32768 else r["ph_sin"]) / 2.0 ** 15
    ic = r["ph_icos"] / 2.0 ** 14
    x = c - r["ofs_cos"]
    y = ((s - r["ofs_sin"]) * gain - x * sa) * ic
    th = np.arctan2(y, x)
    th = th - (r["h3_amp"] / 65536.0 * 2 * math.pi) * np.sin(4 * th + r["h3_ph"] / 256.0 * 2 * math.pi)
    return th, np.hypot(x, y)


def regs_from(oc, os_, g, sa):
    ca = math.sqrt(1 - sa * sa)
    return dict(ofs_sin=int(round(os_)), ofs_cos=int(round(oc)),
                gain=int(round(g * 2 ** 14)),
                ph_sin=int(round(sa * 2 ** 15)) & 0xFFFF,
                ph_icos=int(round(1 / ca * 2 ** 14)),
                h3_amp=0, h3_ph=0)


def fit(s, c):
    """Host calibration from raw codes only (no reference encoder).
    1. conic fit -> start values; 2. four passes of a harmonic least-squares fit of each
    channel against the corrected angle (1st and 3rd harmonics), which removes the bias
    that the 3rd harmonic puts into the conic fit; 3. 4th-harmonic modulation of the
    corrected radius -> H3_AMP, H3_PH (angle error = -h sin(4 th - psi))."""
    s = s.astype(float)
    c = c.astype(float)
    M = np.column_stack([c * c, c * s, s * s, c, s])
    coef, *_ = np.linalg.lstsq(M, np.ones_like(c), rcond=None)
    a, b, d, e, f = coef
    Q = np.array([[2 * a, b], [b, 2 * d]])
    c0, s0 = np.linalg.solve(Q, [-e, -f])
    r = regs_from(c0, s0, math.sqrt(d / a), -b / (2 * math.sqrt(a * d)))
    for _ in range(4):
        th, _ = correct_float(s, c, r)
        H = np.column_stack([np.ones_like(th), np.cos(th), np.sin(th), np.cos(3 * th), np.sin(3 * th)])
        kc, *_ = np.linalg.lstsq(H, c, rcond=None)
        ks, *_ = np.linalg.lstsq(H, s, rcond=None)
        # c = Oc + Ac cos(th + bc); s = Os + As sin(th + bs)
        Ac, bc = math.hypot(kc[1], kc[2]), math.atan2(-kc[2], kc[1])
        As, bs = math.hypot(ks[1], ks[2]), math.atan2(ks[1], ks[2])
        r = regs_from(kc[0], ks[0], Ac / As, math.sin(bs - bc))
    th, rad = correct_float(s, c, r)
    rn = rad / rad.mean()
    H = np.column_stack([np.ones_like(th), np.cos(2 * th), np.sin(2 * th), np.cos(4 * th), np.sin(4 * th)])
    kr, *_ = np.linalg.lstsq(H, rn, rcond=None)
    h = math.hypot(kr[3], kr[4])
    psi = math.atan2(kr[4], kr[3])
    r["h3_amp"] = min(255, int(round(h / (2 * math.pi) * 65536)))
    r["h3_ph"] = int(round((math.pi - psi) / (2 * math.pi) * 256)) % 256
    return r


def fit_ref(s, c, p_ref):
    """Bench calibration against a reference angle p_ref (e.g. a reference encoder on the
    calibration fixture): Gauss-Newton on offsets, gain ratio, sin(alpha) and the
    4th-harmonic angle term, starting from the self-calibration fit."""
    r0 = fit(s, c)
    s = s.astype(float)
    c = c.astype(float)
    A = r0["h3_amp"] / 65536.0 * 2 * math.pi
    P = r0["h3_ph"] / 256.0 * 2 * math.pi
    sa0 = (r0["ph_sin"] - 65536 if r0["ph_sin"] >= 32768 else r0["ph_sin"]) / 2.0 ** 15
    q = np.array([r0["ofs_sin"], r0["ofs_cos"], r0["gain"] / 2.0 ** 14, sa0,
                  A * math.cos(P), A * math.sin(P), 0.0])

    def resid(q):
        os_, oc, g, sa, hc, hs, z = q
        x = c - oc
        y = ((s - os_) * g - x * sa) / math.sqrt(1 - sa * sa)
        th = np.arctan2(y, x)
        th = th - (hc * np.sin(4 * th) + hs * np.cos(4 * th))
        return wrap(th - p_ref - z)
    for _ in range(12):
        r = resid(q)
        J = np.empty((len(r), len(q)))
        for i in range(len(q)):
            dq = np.zeros_like(q)
            dq[i] = 1e-6 * max(1.0, abs(q[i]))
            J[:, i] = (resid(q + dq) - r) / dq[i]
        step, *_ = np.linalg.lstsq(J, -r, rcond=None)
        q = q + step
    os_, oc, g, sa, hc, hs, z = q
    r = regs_from(oc, os_, g, sa)
    r["h3_amp"] = min(255, int(round(math.hypot(hc, hs) / (2 * math.pi) * 65536)))
    r["h3_ph"] = int(round(math.atan2(hs, hc) / (2 * math.pi) * 256)) % 256
    return r


def ramp_ticks(c):
    """start tick and length (ticks) of the f0 -> f ramp"""
    pt = c.get("pair", PAIR_TICKS)
    ts = 100 + pt * c.get("ramp_start", 0)
    tr = c["ramp"] * pt if "ramp" in c else (c["f"] - c["f0"]) / c["acc"] * TICK_HZ
    return ts, tr


def slots(c, k):
    """frame slot of pair k (skip: every skip-th slot is taken by the current pair)"""
    s = c.get("skip", 0)
    k = np.asarray(k)
    return k + k // (s - 1) if s > 1 else k


def phase(c, p0, t):
    """true electrical angle at tick t: constant f, or f0 until the ramp start, a linear ramp to f, then f"""
    t = np.asarray(t, dtype=float)
    w = 2 * math.pi * c["f"] / TICK_HZ
    if "f0" not in c:
        return p0 + w * t
    w0 = 2 * math.pi * c["f0"] / TICK_HZ
    ts, tr = ramp_ticks(c)
    u = np.clip(t - ts, 0, None)
    ur = np.minimum(u, tr)
    return p0 + w0 * t + 0.5 * (w - w0) / tr * ur ** 2 + (w - w0) * (u - ur)


def gen(case, out):
    c = CASES[case]
    rng = np.random.default_rng(SEED)
    k = np.arange(c["n"])
    pt = c.get("pair", PAIR_TICKS)
    ticks = 100 + pt * slots(c, k)                # track-and-hold instants (TB schedule)
    p0 = 0.3
    w = 2 * math.pi * c["f"] / TICK_HZ            # rad per tick
    p = phase(c, p0, ticks)
    s, cc = head(p, c)
    sq, cq = quant(s, rng, c["noise"]), quant(cc, rng, c["noise"])
    if c["cal"]:
        # calibration data: one full electrical period at standstill-like slow rotation
        pc = np.linspace(0, 2 * math.pi, 1024, endpoint=False) + 0.1
        sc, ccc = head(pc, c)
        qs, qc = quant(sc, rng, c["noise"]), quant(ccc, rng, c["noise"])
        r = fit(qs, qc) if c.get("self") else fit_ref(qs, qc, pc)
    else:
        r = default_regs()
    kp, ki = 2, 11
    words = [r["ofs_sin"] & 0xFFF, r["ofs_cos"] & 0xFFF, r["gain"], r["ph_sin"], r["ph_icos"],
             (r["h3_ph"] << 8) | r["h3_amp"], kp, ki, c["extrap"]]
    with open(f"{out}/pos_{case}_regs.hex", "w") as fh:
        fh.write("\n".join(f"{v & 0xFFFF:04x}" for v in words) + "\n")
    with open(f"{out}/pos_{case}_stim.hex", "w") as fh:
        for a, b in zip(sq, cq):
            fh.write(f"{(a + 2048) & 0xFFF:03x}{(b + 2048) & 0xFFF:03x}\n")
    meta = dict(case=case, head=c, regs=r, kp=kp, ki=ki, p0=p0, w_rad_per_tick=w,
                pair_ticks=pt, first_tick=100, n=int(c["n"]), seed=SEED)
    with open(f"{out}/pos_{case}_meta.json", "w") as fh:
        json.dump(meta, fh, indent=1)
    np.save(f"{out}/pos_{case}_codes.npy", np.vstack([sq, cq]))


def check(case, out):
    meta = json.load(open(f"{out}/pos_{case}_meta.json"))
    sq, cq = np.load(f"{out}/pos_{case}_codes.npy")
    r = meta["regs"]
    n = meta["n"]
    k = np.arange(n)
    c = meta["head"]
    ticks = meta["first_tick"] + meta["pair_ticks"] * slots(c, k)
    ptrue = phase(c, meta["p0"], ticks)
    rows = [l.split() for l in open(f"{out}/pos_{case}_out.txt") if l.strip() and not l.startswith("#")]
    meas = np.array([int(x[1]) for x in rows if x[0] == "M"])
    track = np.array([[int(x[1]), int(x[2]), int(x[3])] for x in rows if x[0] == "T"])
    if len(meas) != n:                               # pairs dropped by r1_pos (overrun): record and fail
        res = dict(case=case, failed="r1_pos produced %d measurements for %d pairs (overrun)" % (len(meas), n))
        json.dump(res, open(f"{out}/pos_{case}_result.json", "w"), indent=1)
        print(json.dumps(res)); return
    th_rtl = meas / 2.0 ** 18 * 2 * math.pi
    th_ref, _ = correct_float(sq.astype(float), cq.astype(float), r)
    d2r = 180 / math.pi
    e_impl = wrap(th_rtl - th_ref) * d2r
    e_tot = wrap(th_rtl - ptrue) * d2r
    e_reft = wrap(th_ref - ptrue) * d2r
    res = dict(case=case, regs=r)

    def stats(e):
        m = float(np.mean(e))
        return dict(max_abs=float(np.max(np.abs(e))), rms=float(np.sqrt(np.mean(e ** 2))),
                    mean=m, max_abs_zeroed=float(np.max(np.abs(e - m))),
                    rms_zeroed=float(np.sqrt(np.mean((e - m) ** 2))))
    res["measured_vs_true_deg_el"] = stats(e_tot)
    res["reference_vs_true_deg_el"] = stats(e_reft)
    res["rtl_vs_float_reference_deg_el"] = stats(e_impl)
    # tracking output: pos_out (18 bit, extrapolated by extrap ticks) at the T&H tick
    # TB logs T <tick> <pos_out> <velocity>
    if len(track):
        tt = track[:, 0]
        po = track[:, 1] / 2.0 ** 18 * 2 * math.pi
        # pos_out logged at tick T holds the NCO value of tick T-1 (one output register)
        target = phase(c, meta["p0"], tt - 1 + meta["head"]["extrap"])
        et = wrap(po - target) * d2r
        settle = n // 4
        if "f0" in c:                                # ramp cases: accuracy after the ramp end + 500 pairs
            ts, tr = ramp_ticks(c)
            settle = int(np.searchsorted(tt, ts + tr)) + 500
        res["tracked_vs_true_deg_el_after_settle"] = stats(et[settle:])
        bad = np.nonzero(np.abs(et - np.mean(et[settle:])) > 0.5)[0]
        res["lock_pairs_to_0p5deg_from_reset"] = int(bad[-1] + 1) if len(bad) else 0
        vel = track[settle:, 2] / 32.0                            # LSB16 per tick
        vtrue = meta["w_rad_per_tick"] / (2 * math.pi) * 65536.0
        res["velocity_lsb_per_tick"] = dict(true=vtrue, mean=float(np.mean(vel)),
                                            rel_err=float(np.mean(vel) / vtrue - 1))
        if c.get("pair", PAIR_TICKS) != PAIR_TICKS:
            # count safety (revision 0.3): per-frame step of the tracked output against the true step,
            # and the multi-turn position (TURNS * 2^18 + POS) against the true unwrapped angle
            rows4 = [l.split() for l in open(f"{out}/pos_{case}_out.txt") if l.startswith("T ")]
            turns = np.array([int(x[4]) for x in rows4], dtype=np.int64)
            pos = track[:, 1].astype(np.int64)
            dstep = wrap(np.diff(po) - np.diff(target)) * d2r
            lock = res["lock_pairs_to_0p5deg_from_reset"]
            # ramp cases: count safety from pair 200 (acquisition at f0 done), i.e. over the whole ramp
            lk = 200 if "f0" in c else max(lock, 1)
            multi = (turns.astype(np.int64) << 18) + pos
            truec = target / (2 * math.pi) * 2 ** 18
            dm = (multi - truec)
            dm0 = dm[lk:] - dm[lk]
            res["count_safety"] = dict(
                pair_ticks=int(meta["pair_ticks"]), frame_rate_hz=TICK_HZ / meta["pair_ticks"],
                f_end_hz=c["f"], deg_el_per_frame_end=360.0 * c["f"] * meta["pair_ticks"] / TICK_HZ,
                lock_pair=int(lock),
                max_abs_step_error_deg_el_after_lock=float(np.max(np.abs(dstep[lk:]))),
                max_abs_error_deg_el_after_lock=float(np.max(np.abs(et[lk:] - np.mean(et[settle:])))),
                multiturn_drift_counts_max=float(np.max(np.abs(dm0)) / 2 ** 16),
                multiturn_offset_end_counts=float(np.mean(dm0[-200:]) / 2 ** 16),
                from_pair=int(lk), skip=int(c.get("skip", 0)), acc_hz_per_s=c.get("acc"),
                max_frame_gap_ticks=int(np.max(np.diff(tt))),
                frames_err_gt45deg_after_lock=int(np.sum(np.abs(et[lk:] - np.mean(et[settle:])) > 45.0)),
                note="one count = 90 deg el = 2^16 of the 18-bit position")
    json.dump(res, open(f"{out}/pos_{case}_result.json", "w"), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    {"gen": gen, "check": check}[sys.argv[1]](sys.argv[2], sys.argv[3])

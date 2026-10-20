"""Post-processing of the r1_gate waveform file (wrdata, ascii, one time column). Pure python (host python 3.6)."""

def load(path):
    f = open(path)
    hdr = f.readline().split()
    cols = [[] for _ in hdr]
    for line in f:
        p = line.split()
        if len(p) != len(hdr):
            continue
        for i, x in enumerate(p):
            cols[i].append(float(x))
    d = {}
    for n, c in zip(hdr, cols):
        d[n.lower()] = c
    return d

def cross(t, v, level, rising, t0, t1):
    """first crossing time of level (linear interpolation) in (t0, t1], or None"""
    import bisect
    i = max(bisect.bisect_left(t, t0) - 1, 0)
    n = len(t)
    while i < n - 1 and t[i] <= t1:
        a, b = v[i], v[i + 1]
        if t[i + 1] > t0:
            if (rising and a < level <= b) or ((not rising) and a > level >= b):
                tc = t[i] + (level - a) / (b - a) * (t[i + 1] - t[i]) if b != a else t[i]
                if tc >= t0:
                    return tc
        i += 1
    return None

def trapz(t, y, t0, t1):
    import bisect
    i0 = bisect.bisect_left(t, t0); i1 = bisect.bisect_right(t, t1)
    q = 0.0
    for i in range(max(i0, 1), min(i1, len(t))):
        q += 0.5 * (y[i] + y[i - 1]) * (t[i] - t[i - 1])
    return q

def window(t, y, t0, t1):
    import bisect
    i0 = bisect.bisect_left(t, t0); i1 = bisect.bisect_right(t, t1)
    return y[i0:i1]

def mean(t, y, t0, t1):
    w = window(t, y, t0, t1)
    return sum(w) / len(w) if w else None

def r(x, n=4):
    return None if x is None else float("%.*g" % (n, x))

def analyze(path, IOVDD, VDD, S, EDGE):
    d = load(path)
    t = d["time"]
    sig = {"pwm": {x: d["v(pwm_%s)" % x] for x in "abc"}, "gc": {x: d["v(gc_%s)" % x] for x in "abc"},
           "pad": {x: d["v(pad_%s)" % x] for x in "abc"}, "gf": {x: d["v(gf_%s)" % x] for x in "abc"}}
    en = d["v(gate_en)"]
    iiov, iiss, icore = d["iiov"], d["iiss"], d["icore"]
    vio, vss, vcore = d["v(iovdd_i)"], d["v(iovss_i)"], d["v(vdd_i)"]
    ev = [("en_rise_b", "en", 0.2e-6, True, "b"),
          ("b_fall_pre", "b", S - 50e-9, False, "b"),
          ("ac_rise", "ac", S, True, "ac"),
          ("ac_fall", "ac", 2 * S, False, "ac"),
          ("b_rise_post", "b", 2 * S + 50e-9, True, "b"),
          ("b_fall_single", "b", 3 * S, False, "b"),
          ("c_rise_single", "c", 4 * S, True, "c"),
          ("c_fall_single", "c", 5 * S, False, "c"),
          ("sso_rise1", "abc", 6 * S, True, "abc"),
          ("sso_fall", "abc", 7 * S, False, "abc"),
          ("sso_rise2", "abc", 8 * S, True, "abc"),
          ("fault_en_fall", "en", 9 * S, False, "abc")]
    out = {"events": {}}
    E = {}   # raw times for the overlap analysis: E[(event, ch)] = dict
    for name, who, te, rising, chans in ev:
        e = {}
        for ch in chans:
            refsig = en if who == "en" else sig["pwm"][ch]
            tr = cross(t, refsig, VDD / 2.0, rising, te - 1e-9, te + EDGE + 5e-9)
            c = {"t_ref": tr}
            if tr is None:
                e[ch] = c; continue
            tend = tr + 0.95 * S
            if name == "b_fall_pre":
                tend = tr + 0.9 * S
            lo, hi = 0.1 * IOVDD, 0.9 * IOVDD
            for nd in ("gc", "pad", "gf"):
                v = sig[nd][ch]
                lv = VDD / 2.0 if nd == "gc" else IOVDD / 2.0
                t50 = cross(t, v, lv, rising, tr, tend)
                c["d50_" + nd] = None if t50 is None else t50 - tr
                if nd == "gc":
                    continue
                if rising:
                    ta, tb = cross(t, v, lo, True, tr, tend), cross(t, v, hi, True, tr, tend)
                else:
                    ta, tb = cross(t, v, hi, False, tr, tend), cross(t, v, lo, False, tr, tend)
                c["slew_" + nd] = None if (ta is None or tb is None) else tb - ta     # 10-90 or 90-10
                c["dstart_" + nd] = None if ta is None else ta - tr                    # to the first 10 % (rise) / last 90 % (fall)
                c["dend_" + nd] = None if tb is None else tb - tr
                # thresholds used by the overlap analysis
                for thn, th in (("half", IOVDD / 2.0), ("1v", 1.0)):
                    c["t_%s_%s" % (nd, thn)] = cross(t, v, th, rising, tr, tend)
                c["t_%s_033" % nd] = cross(t, v, 0.33, rising, tr, tend)
            e[ch] = c
        E[name] = e
        # supply current and bounce metrics over the edge window
        trs = [e[ch]["t_ref"] for ch in chans if e[ch].get("t_ref") is not None]
        if trs:
            t0 = min(trs)
            ends = [e[ch].get("dend_gf") for ch in chans if e[ch].get("dend_gf") is not None]
            wend = max(ends) if ends else 0.5 * S
            tb0, tb1 = t0 - 5e-9, t0 + wend + 20e-9
            base_iov = mean(t, iiov, t0 - 30e-9, t0 - 5e-9)
            base_iss = mean(t, iiss, t0 - 30e-9, t0 - 5e-9)
            base_cor = mean(t, icore, t0 - 30e-9, t0 - 5e-9)
            m = {}
            wi = window(t, iiov, tb0, tb1); ws = window(t, iiss, tb0, tb1); wc = window(t, icore, tb0, tb1)
            m["window_ns"] = (tb1 - tb0) * 1e9
            m["iovdd_peak_mA"] = max(wi) * 1e3
            m["iovdd_min_mA"] = min(wi) * 1e3
            m["iovdd_Q_nC"] = trapz(t, iiov, tb0, tb1) * 1e9
            m["iovdd_avg_mA"] = m["iovdd_Q_nC"] * 1e-9 / (tb1 - tb0) * 1e3
            m["iovss_peak_mA"] = max(ws) * 1e3
            m["iovss_min_mA"] = min(ws) * 1e3
            m["iovss_Q_nC"] = trapz(t, iiss, tb0, tb1) * 1e9
            m["core_peak_mA"] = max(wc) * 1e3
            m["core_Q_nC"] = trapz(t, icore, tb0, tb1) * 1e9
            wv = window(t, vio, tb0, tb1); wvs = window(t, vss, tb0, tb1); wvc = window(t, vcore, tb0, tb1)
            m["iovdd_node_min_V"] = min(wv); m["iovss_node_max_V"] = max(wvs); m["iovss_node_min_V"] = min(wvs)
            m["iovdd_droop_mV"] = (IOVDD - min(wv)) * 1e3
            m["supply_diff_min_V"] = min(a - b for a, b in zip(wv, window(t, vss, tb0, tb1)))
            m["core_node_min_V"] = min(wvc)
            # crowbar estimate: first 200 ns after the reference edge, baseline subtracted
            cw0, cw1 = t0 - 5e-9, t0 + 200e-9
            wi2 = window(t, iiov, cw0, cw1); ws2 = window(t, iiss, cw0, cw1)
            m["cw_iovdd_peak_mA"] = (max(wi2) - (base_iov or 0)) * 1e3
            m["cw_iovdd_Q_nC"] = (trapz(t, iiov, cw0, cw1) - (base_iov or 0) * (cw1 - cw0)) * 1e9
            m["cw_iovss_peak_mA"] = (max(ws2) - (base_iss or 0)) * 1e3
            m["cw_iovss_Q_nC"] = (trapz(t, iiss, cw0, cw1) - (base_iss or 0) * (cw1 - cw0)) * 1e9
            m["base_iovdd_uA"] = (base_iov or 0) * 1e6
            m["base_iovss_uA"] = (base_iss or 0) * 1e6
            out.setdefault("supply", {})[name] = {k: r(v) for k, v in m.items()}
        out["events"][name] = {ch: {k: (r(v, 5) if v is not None and not k.startswith("t_") else r(v, 8)) for k, v in e[ch].items()} for ch in e}
    # idle currents
    out["idle_mA"] = {"all_low_iovdd": r(mean(t, iiov, 6 * S - 100e-9, 6 * S - 10e-9) * 1e3),
                      "all_high_iovdd": r(mean(t, iiov, 9 * S - 100e-9, 9 * S - 10e-9) * 1e3),
                      "all_low_core": r(mean(t, icore, 6 * S - 100e-9, 6 * S - 10e-9) * 1e3),
                      "all_high_core": r(mean(t, icore, 9 * S - 100e-9, 9 * S - 10e-9) * 1e3)}
    # (b) overlaps: gap = t(turn-on edge crosses level) - t(turn-off edge crosses level); positive = no overlap
    ov = {}
    for tag, off, on in (("b_off_then_a_on", ("b_fall_pre", "b"), ("ac_rise", "a")), ("a_off_then_b_on", ("ac_fall", "a"), ("b_rise_post", "b"))):
        for nd in ("pad", "gf"):
            for th in ("half", "1v"):
                if off[0] == "b_fall_pre":
                    # turn-off b falls through the level, turn-on a rises through the level
                    t_off = E[off[0]][off[1]].get("t_%s_%s" % (nd, th)); t_on = E[on[0]][on[1]].get("t_%s_%s" % (nd, th))
                else:
                    t_off = E[off[0]][off[1]].get("t_%s_%s" % (nd, th)); t_on = E[on[0]][on[1]].get("t_%s_%s" % (nd, th))
                ov["%s_%s_%s_gap_ns" % (tag, nd, th)] = None if (t_off is None or t_on is None) else r((t_on - t_off) * 1e9)
    out["overlap"] = ov
    # (b) skew at the simultaneous edges, and rise-fall delay asymmetry
    sk = {}
    for name in ("sso_rise1", "sso_fall", "sso_rise2"):
        ds = [E[name][ch].get("d50_pad") for ch in "abc"]
        if None not in ds:
            sk[name + "_pad_spread_ns"] = r((max(ds) - min(ds)) * 1e9)
            sk[name + "_pad_d50_ns"] = [r(x * 1e9) for x in ds]
    sk["single_rise_c_d50_pad_ns"] = r((E["c_rise_single"]["c"].get("d50_pad") or float("nan")) * 1e9)
    sk["single_fall_c_d50_pad_ns"] = r((E["c_fall_single"]["c"].get("d50_pad") or float("nan")) * 1e9)
    sk["single_fall_b_d50_pad_ns"] = r((E["b_fall_single"]["b"].get("d50_pad") or float("nan")) * 1e9)
    out["skew"] = sk
    # (d) fault path
    fe = {}
    tref = E["fault_en_fall"]["a"].get("t_ref")
    for ch in "abc":
        c = E["fault_en_fall"][ch]
        for nd in ("pad", "gf"):
            for k in ("033", "1v"):
                tx = c.get("t_%s_%s" % (nd, k))
                fe["%s_%s_below_%s_ns" % (ch, nd, k)] = None if (tx is None or tref is None) else r((tx - tref) * 1e9)
        fe["%s_gc_d50_ns" % ch] = r((c.get("d50_gc") or float("nan")) * 1e9)
        # voltage 200 ns after the en 50 % point
    if tref is not None:
        import bisect
        for ch in "abc":
            for nd in ("pad", "gf"):
                v = sig[nd][ch]; i = bisect.bisect_left(t, tref + 200e-9)
                fe["%s_%s_V_at_200ns" % (ch, nd)] = r(v[i])
    worst = [fe.get("%s_pad_below_033_ns" % ch) for ch in "abc"]
    fe["worst_pad_below_033_ns"] = None if None in worst else max(worst)
    out["fault"] = fe
    return out

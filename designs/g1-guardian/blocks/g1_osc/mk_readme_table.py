"""Build the results table of README.md from sim/results_osc.txt (run after run_osc.sh all)."""
import re, statistics as st
rows = []; start = []; seen = set()
tag = None
for l in open("sim/results_osc.txt"):
    if l.startswith("== "):
        tag = l[3:].strip()
    elif l.startswith("OSC "):
        m = dict(re.findall(r"([\w.]+)= ([-0-9.eE+]+)", l))
        t = re.match(r"osc_(mos_\w+)_(res_\w+)_(cap_\w+)_([\d.]+)V_(-?\d+)C_code(\d+)", tag).groups()
        if tag in seen: continue
        seen.add(tag)
        rows.append((t, float(m["f_MHz"]), float(m["duty_pct"]), float(m["idd_uA"])))
    elif l.startswith("STARTUP"):
        m = dict(re.findall(r"([\w.]+)= ([-0-9.eE+]+)", l))
        if tag in seen: continue
        seen.add(tag)
        start.append((tag, float(m["first_edge_us"]), float(m["vdd_at_1.08V_us"]), float(m["f_MHz_end"])))
out = ["| MOS | RES | CAP | VDD (V) | T (°C) | trim code | f (MHz) | dev. from 10 MHz | duty (%) | I<sub>DD</sub> (µA) |", "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
for t, f, d, i in rows:
    note = " (model extrapolated)" if int(t[4]) > 125 else ""
    out.append("| %s | %s | %s | %s | %s%s | %s | %.3f | %+.1f %% | %.1f | %.0f |" % (t[0][4:], t[1][4:], t[2][4:], t[3], t[4], note, t[5], f, (f/10-1)*100, d, i))
mid = [(t, f) for t, f, d, i in rows if t[5] == "8" and t[3] == "1.2"]
fs = [f for t, f in mid]
imin = min(mid, key=lambda x: x[1]); imax = max(mid, key=lambda x: x[1])
print("\n".join(out))
print()
print("Mid-code (8) at 1.2 V over %d corner/temperature points: min %.3f MHz (%s/%s/%s %s °C), max %.3f MHz (%s/%s/%s %s °C): %+.1f %% / %+.1f %% from 10 MHz." % (len(mid), imin[1], *imin[0][:3], imin[0][4], imax[1], *imax[0][:3], imax[0][4], (imin[1]/10-1)*100, (imax[1]/10-1)*100))
sup = {t[3]: f for t, f, d, i in rows if t[5] == "8" and t[0] == "mos_tt" and t[1] == "res_typ" and t[2] == "cap_typ" and t[4] == "27"}
if "1.08" in sup and "1.32" in sup:
    print("Supply: %.3f MHz at 1.08 V, %.3f at 1.2 V, %.3f at 1.32 V -> %.1f %%/V (%.1f %% over +/-10 %%)." % (sup["1.08"], sup["1.2"], sup["1.32"], (sup["1.32"]-sup["1.08"])/0.24/10*100, (sup["1.32"]-sup["1.08"])/sup["1.2"]*100))
trim = {t[5]: f for t, f, d, i in rows if t[0] == "mos_tt" and t[1] == "res_typ" and t[2] == "cap_typ" and t[4] == "27" and t[3] == "1.2"}
lo, hi = trim["15"]/trim["8"], trim["0"]/trim["8"]
print("Trim ratio relative to mid code: x%.3f (code 15) to x%.3f (code 0). Best reachable frequency per corner (f_mid x ratio, nearest to 10 MHz): " % (lo, hi) + ("; ".join("%s/%s/%s %s V %s °C: %.2f MHz" % (t[0][4:], t[1][4:], t[2][4:], t[3], t[4], min(max(10.0, f*lo), f*hi)) for t, f in [(t, f) for t, f, d, i in rows if t[5] == "8"] if not (lo*f <= 10.0 <= hi*f)) or "all corners reach 10 MHz"))
print("Trim (tt, 27 °C): " + ", ".join("code %s -> %.3f MHz" % (c, trim[c]) for c in sorted(trim, key=int)))
for s in start:
    print("Start-up %s: first osc_clk edge at %.2f µs (VDD reaches 1.08 V at %.2f µs), f at end %.3f MHz" % (s[0], s[1], s[2], s[3]))

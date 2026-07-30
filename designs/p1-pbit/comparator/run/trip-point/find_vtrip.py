"""Unity-gain trip point of the output inverter, from a DC sweep raw file.

The inverter's trip point is where Vout crosses Vin. That is the point the
candidate-2 feedback resistor drives the node to at DC, because the resistor
ties output to input and forces Vout = Vin. It is NOT vdd/2.
"""
import sys

def vtrip(path):
    pts = []
    for line in open(path):
        p = line.split()
        if len(p) == 2:
            try: pts.append((float(p[0]), float(p[1])))
            except ValueError: pass
    for i in range(1, len(pts)):
        d0 = pts[i-1][1] - pts[i-1][0]
        d1 = pts[i][1] - pts[i][0]
        if d0 > 0 >= d1:
            return pts[i-1][0] + (pts[i][0]-pts[i-1][0]) * d0/(d0-d1), len(pts)
    return None, len(pts)

for path, vdd, label in (("raw_vtrip_27c.raw", 1.20, "TYPICAL 27C TT"),
                         ("raw_vtrip_-40c.raw", 1.32, "COLD -40C FF"),
                         ("raw_vtrip_125c.raw", 1.14, "HOT 125C SS")):
    tp, n = vtrip(path)
    print(f"{label:<16} VDD={vdd:.2f}  N={n:5d}  Vtrip={tp*1000:.2f} mV "
          f"({tp/vdd*100:.2f}% of VDD)  vdd/2 - Vtrip = {(vdd/2-tp)*1000:+.1f} mV")

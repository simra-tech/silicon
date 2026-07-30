#!/usr/bin/env python3
"""Count P(bit=1) from the transient dump, sampling the held bit once per clock.

The decision is taken at the track-to-latch transition, on multiples of 200 ps.
The regenerated bit is read 100 ps later, in the middle of the following latch
phase, where it is flat -- reading at the transition itself catches the edge.

Sampling starts at 200 ns. Everything before that is inside the interstage
coupling network's ~100 ns settling transient, where a decaying differential
offset of up to +32 mV swamps the ~29 mV of noise and pins the output. Counting
inside that window is what produced the earlier all-zero bitstreams.
"""
import bisect, math, sys

path = sys.argv[1] if len(sys.argv) > 1 else "bits.dat"
t, v = [], []
for line in open(path):
    parts = line.split()
    if len(parts) < 2:
        continue
    try:
        t.append(float(parts[0])); v.append(float(parts[1]))
    except ValueError:
        continue  # ngspice writes a header row

CLOCK = 200e-12
START = 200e-9
ones = zeros = ambiguous = 0
k = int(START / CLOCK)
while True:
    sample_at = k * CLOCK + 100e-12
    if sample_at > t[-1]:
        break
    value = v[bisect.bisect_left(t, sample_at)]
    if value > 0.9:
        ones += 1
    elif value < 0.3:
        zeros += 1
    else:
        ambiguous += 1
    k += 1

n = ones + zeros + ambiguous
p = ones / n
se = math.sqrt(p * (1 - p) / n)
print(f"N = {n}   ones = {ones}   zeros = {zeros}   ambiguous = {ambiguous}")
print(f"P(bit=1) = {p:.4f} +/- {se:.4f} (1 sigma)")
print(f"95% interval: {p - 1.96 * se:.4f} .. {p + 1.96 * se:.4f}")

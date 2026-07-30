#!/usr/bin/env python3
"""Autocorrelation of the bitstream, and of the input samples that produced it.

The point of measuring both in one run is that they separate two causes of a
correlated bitstream which no single measurement can distinguish:

  * the noise arriving at the comparator is already correlated at the sample
    rate -- a bandwidth problem in the amplifier or the source; or
  * the noise is white and the comparator is manufacturing the correlation --
    a latch retaining state between decisions.

The input differential is read at the decision instant (the track-to-latch
transition, on multiples of the clock period). The bit is read 100 ps later, in
the middle of the following latch phase, where it is flat.

Sampling starts at 200 ns, past the ~100 ns interstage coupling settling; see
../rectified-offset/ for why that matters.
"""
import bisect, math, sys

path = sys.argv[1] if len(sys.argv) > 1 else "bits2.dat"
CLOCK = 200e-12
START = 200e-9
HIGH = 0.6  # rail-to-rail output; midpoint discriminates cleanly

t, bit, out_p, out_n = [], [], [], []
for line in open(path):
    parts = line.split()
    if len(parts) < 6:
        continue
    try:
        # wrdata repeats the time column before each vector
        t.append(float(parts[0]))
        bit.append(float(parts[1]))
        out_p.append(float(parts[3]))
        out_n.append(float(parts[5]))
    except ValueError:
        continue

bits, diffs = [], []
k = int(START / CLOCK)
while True:
    read_bit_at = k * CLOCK + 100e-12
    decide_at = k * CLOCK
    if read_bit_at > t[-1]:
        break
    bits.append(1 if bit[bisect.bisect_left(t, read_bit_at)] > HIGH else 0)
    i = bisect.bisect_left(t, decide_at)
    diffs.append(out_p[i] - out_n[i])
    k += 1


def autocorr(series, lags=8):
    n = len(series)
    mean = sum(series) / n
    centred = [x - mean for x in series]
    denom = sum(x * x for x in centred)
    return [sum(centred[i] * centred[i + lag] for i in range(n - lag)) / denom
            for lag in range(1, lags + 1)]


n = len(bits)
p = sum(bits) / n
rms = math.sqrt(sum(d * d for d in diffs) / n)
print(f"N = {n}   P(bit=1) = {p:.4f}")
print(f"sampled input differential: mean {1e3 * sum(diffs) / n:+.4f} mV   rms {1e3 * rms:.3f} mV")
print(f"standard error on rho at this N: {1 / math.sqrt(n):.3f}")
print()
print("lag   rho(bit)   rho(input sample)")
rb, rd = autocorr(bits), autocorr(diffs)
for lag in range(8):
    print(f"{lag + 1:3d}   {rb[lag]:+7.4f}    {rd[lag]:+7.4f}")

# A correlated series has a larger variance of the mean than sqrt(p(1-p)/N)
# implies. This is the inflation factor, and it is why quoting a shot-noise
# error bar on a counted probability is wrong whenever the bits are correlated.
inflation = 1 + 2 * sum((1 - (lag + 1) / n) * rb[lag] for lag in range(len(rb)))
se_ind = math.sqrt(p * (1 - p) / n)
se_cor = se_ind * math.sqrt(max(inflation, 1e-9))
print()
print(f"independent standard error = {se_ind:.4f}")
print(f"variance inflation         = {inflation:.3f}")
print(f"corrected standard error   = {se_cor:.4f}")
print(f"z against 0.5, independent = {(p - 0.5) / se_ind:+.2f}")
print(f"z against 0.5, corrected   = {(p - 0.5) / se_cor:+.2f}")

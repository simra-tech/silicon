#!/usr/bin/env python3
"""Behavioural model of the p-bit bias servo (C167/C168 specification).

Purpose: let the control loop *run* rather than be inspected. Three hours of arithmetic, with every
parameter computed twice by two people, still contained a sign error that made the loop diverge —
invisible to inspection, exposed in seconds by playing the design forward. Any change to the loop
(window length, gain, LSB, dither depth, drift assumption) should be re-checked here before it is
believed.

Model, matching the specification:
    effective correction = (C + p) * LSB,  opposing the offset
    residual seen by a bit = Vos - (C + p_applied) * LSB, where p_applied is 1 with probability p
    ones fraction over a window ~ Binomial(N, p_eff),  p_eff = (1-p)*Phi(r0/sn) + p*Phi(r1/sn)
    update: p <- clamp(p + g*b, 0, 1-1/32)      # NOTE THE SIGN: positive b needs MORE correction
    p railing steps the coarse code C by +/-1 and re-centres p (normal tracking, not a fault)

Verified behaviour with the specification's numbers: converges below 1% bias by window 23 (0.6 ms)
against a predicted 5*tau of 0.52 ms; settled bias 0.23% (the analytic estimate of 0.105% omits the
coarse/fine interaction with loop noise, so the simulated figure is the one of record).
"""
import math
import random

# --- specification constants -------------------------------------------------
SIGMA_N = 3.25        # mV rms, in-band noise at the comparator (C159, band-characterised)
LSB = 0.20            # mV, buildable physical trim step
N = 32768             # bits per servo window (15-bit counter)
GAIN = 1.29           # dimensionless loop gain 0.25 / (db/dp = 0.194, 8-code dither span)
PSTEP = 1.0 / 64      # 6-bit dither resolution
FINE_CODES = 8        # dither spans 8 coarse codes: fine range 8*LSB = 1.6 mV (2.95x worst coarse)
COARSE_LIMIT = 300    # +/- codes, i.e. +/-60 mV of range
BIT_PERIOD = 0.8e-9
WINDOW = N * BIT_PERIOD          # 26.2 us
DRIFT_MV_PER_S = 0.081 / 0.020   # 1% of bias per 20 ms at 1 C/s


def coverage_check(coarse_step_mV, label="coarse step"):
    """Fail loudly if the fine range cannot cover 2x the given coarse step.

    The coarse DAC is not designed yet; its worst step is provisional (the 0.543 mV
    figure comes from C165, a rejected build). Coverage failure is permanent and
    inescapable for an affected part, so the margin rule is 2x, not 1.47x, and this
    check is re-run automatically whenever the coarse design lands (edit the call).
    """
    assert FINE_CODES * LSB >= 2.0 * coarse_step_mV, (
        f"COVERAGE FAILURE: fine range {FINE_CODES*LSB:.3f} mV < 2x coarse step "
        f"{coarse_step_mV:.3f} mV ({label})")


coverage_check(0.543, "C165 ratiometric worst coarse step (PROVISIONAL)")


def phi(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def run(offset_mV=11.79, windows=300, gain=GAIN, sign=+1, drift=DRIFT_MV_PER_S, seed=1):
    """Play the loop forward. sign=-1 reproduces the original (diverging) specification."""
    random.seed(seed)
    C, p, off = 0, 0.5, offset_mV
    history = []
    for k in range(windows):
        off += drift * WINDOW
        corr = (C + FINE_CODES * p) * LSB   # effective correction over the FINE_CODES-wide dither span
        r0 = off - corr                     # dither bit low (p_applied=0 -> 0 extra codes)
        r1 = r0 - FINE_CODES * LSB          # dither bit high (p_applied=1 -> FINE_CODES extra codes)
        p_eff = (1 - p) * phi(r0 / SIGMA_N) + p * phi(r1 / SIGMA_N)
        var = max(N * p_eff * (1 - p_eff), 1e-9)
        count = p_eff * N + random.gauss(0, math.sqrt(var))
        b = count / N - 0.5
        p = p + sign * gain * b
        while p < 0 and C > -COARSE_LIMIT:
            C -= 1
            p += 1 / FINE_CODES
        while p > 1 - PSTEP and C < COARSE_LIMIT:
            C += 1
            p -= 1 / FINE_CODES
        p = min(max(p, 0.0), 1 - PSTEP)
        history.append({'window': k, 'offset_mV': off, 'C': C, 'p': p, 'bias_pc': 100 * b})
    return history


def report(history, label):
    tail = [abs(h['bias_pc']) for h in history[100:]]
    first = next((h['window'] for h in history if abs(h['bias_pc']) < 1.0), None)
    print('%-34s first |bias|<1%%: %-6s  settled mean %.3f%%  max %.3f%%' % (
        label, first if first is not None else 'never', sum(tail) / len(tail), max(tail)))


if __name__ == '__main__':
    report(run(sign=+1), 'as corrected  (p <- p + g*b)')
    report(run(sign=-1), 'as first specified (p - g*b)')
    report(run(gain=0.25), 'corrected sign, original gain')

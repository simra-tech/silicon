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

Verified behaviour with the current constants (re-run 2026-08-10, seed 1): converges below 1% bias
by window 45 (1.18 ms); settled bias 0.254%, worst 0.895% (the analytic estimate of 0.105% omits the
coarse/fine interaction with loop noise, so the simulated figure is the one of record). The earlier
"window 23 / 0.23%" figures in this docstring were measured when FINE_CODES was 4 and were left
behind when it became 8 - re-run this file rather than quoting it.
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
COARSE_LIMIT = 300    # +/- codes. SEE THE UNIT WARNING BELOW: this is +/-7.6 mV, NOT +/-60 mV.

# --- UNIT WARNING (2026-08-10) -----------------------------------------------
# LSB above (0.20 mV) is the DAC's step measured AT THE COLLECTORS. Everything else
# in this model - offset_mV, SIGMA_N, the residual arithmetic - is INPUT-REFERRED.
# Input-referred the step is 0.2078 / 8.17 = 0.0254 mV, so the loop's true authority
# is 300 * 0.0254 = +/-7.6 mV, not the +/-60 mV that 300 * 0.20 implies.
#
# Cross-check, two independent routes agreeing to 14%:
#     300 codes x 0.0254 mV                  = +/-7.63 mV
#     current-domain, I_FS/gm (README)       = +/-6.70 mV
#
# CONSEQUENCE: every convergence figure in the docstring above was obtained with
# roughly 8x the trim range the part actually has, against an offset sigma of
# ~11.8 mV. Only ~43-48% of parts are reachable at the true range, so for the
# majority the real loop rails at COARSE_LIMIT and never converges - a regime this
# model has never exercised. DO NOT quote the convergence results until the model is
# re-run with the input-referred LSB and a railing-aware acceptance criterion.
# Deliberately left unpatched rather than silently rescaled: changing LSB alone also
# changes GAIN, FINE_CODES coverage and the dither-vs-noise ratio, and each of those
# needs re-deriving rather than following the constant.
BIT_PERIOD = 0.8e-9
WINDOW = N * BIT_PERIOD          # 26.2 us
DRIFT_MV_PER_S = 0.081 / 0.020   # 1% of bias per 20 ms at 1 C/s


def coverage_check(coarse_step_mV, label="coarse step"):
    """Fail loudly if the fine range cannot cover 2x the given coarse step.

    Coverage failure is permanent and inescapable for an affected part, so the margin
    rule is 2x, not 1.47x.

    MEASURED 2026-08-10 (C169 v5, HBT-pair steering, b1 boundary: 2 binary units +
    150 unary elements of 4, 603 codes). 250 mismatch draws = 37,750 binary-to-unary
    handovers. Worst observed step 1.85 LSB; handover step sigma 0.265 LSB about a
    1 LSB nominal. The assertion uses a 5-sigma design figure rather than the observed
    maximum, because the observed max of a finite sample understates the population:

        worst coarse step = (1 + 5 * 0.265) LSB = 2.33 LSB = 0.465 mV at LSB 0.200

    This replaces the provisional 0.543 mV from C165, a build later rejected as void
    (its decoder read the sweep voltage as the code count). The margin improves from
    1.47x to 1.72x. Re-derive if the handover sigma changes: it is the one quantity
    this assertion now rests on.
    """
    assert FINE_CODES * LSB >= 2.0 * coarse_step_mV, (
        f"COVERAGE FAILURE: fine range {FINE_CODES*LSB:.3f} mV < 2x coarse step "
        f"{coarse_step_mV:.3f} mV ({label})")


HANDOVER_SIGMA_LSB = 0.265   # measured, C169 v5, 250 draws x 151 handovers
WORST_COARSE_STEP_LSB = 1.0 + 5.0 * HANDOVER_SIGMA_LSB   # 5-sigma design figure, 2.33 LSB

coverage_check(WORST_COARSE_STEP_LSB * LSB, "C169 v5 worst coarse step, 5-sigma (MEASURED)")


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
        # spec rule: at most ONE coarse step per window (a slewing coarse control
        # would be a second integrator -- see the acquisition-scaling record)
        if p < 0 and C > -COARSE_LIMIT:
            C -= 1
            p += 1 / FINE_CODES
        elif p > 1 - PSTEP and C < COARSE_LIMIT:
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

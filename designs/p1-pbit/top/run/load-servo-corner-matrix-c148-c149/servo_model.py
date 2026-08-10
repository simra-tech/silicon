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

Verified behaviour, re-run 2026-08-10 after the H-754 unit correction (seed 1), for a part
whose offset is INSIDE the coarse range: converges below 1% bias by window 23 (0.60 ms);
settled bias 0.255%, worst 0.780%.

**Read the range line before the convergence line.** The coarse control reaches +/-7.63 mV
input-referred, against a population offset sigma of ~11.8 mV, so only ~48% of parts are
reachable at all. For the rest the loop rails and never converges - correctly, because the
part is out of range. That is a hardware limit, not a loop defect, and it is the finding
that matters more than any convergence number here. See the trim-range section of the README.

Earlier figures in this docstring are void, twice over: "window 23 / 0.23%" was measured when
FINE_CODES was 4, and "window 45 / 0.254%" was measured with a trim range 8x larger than the
part has (H-754). Re-run this file rather than quoting it - which is the whole point of it.
"""
import math
import random

# --- specification constants -------------------------------------------------
SIGMA_N = 3.25        # mV rms, in-band noise at the comparator (C159, band-characterised)
# --- reference planes: name the plane in the identifier, never in a comment -----
# The 2026-08-10 defect (H-754) was LSB = 0.20 "mV, buildable physical trim step"
# being the step AT THE COLLECTORS while offset_mV, SIGMA_N and the residual
# arithmetic are all INPUT-REFERRED. The two differ by STAGE_GAIN, and a factor of
# 8 looks plausible on both sides of an equals sign. Two names cannot be added by
# accident; one name can, and was, for the life of this file.
LSB_AT_COLLECTOR = 0.2078   # mV/code, measured DAC step at c_p/c_n (C169)
STAGE_GAIN = 8.17           # collector mV per input mV (three corroborating routes, see below)
LSB = LSB_AT_COLLECTOR / STAGE_GAIN   # 0.02543 mV/code INPUT-REFERRED - the plane everything else uses

N = 32768             # bits per servo window (15-bit counter)
PSTEP = 1.0 / 64      # 6-bit dither resolution
COARSE_LIMIT = 300    # +/- codes  ->  +/-7.63 mV input-referred (NOT +/-60; see H-754)

# The dither is specified by its SPAN IN MILLIVOLTS, not by a code count. FINE_CODES = 8
# was chosen when LSB was believed to be 0.20 mV, i.e. it encoded a 1.6 mV span and was
# right only by accident. At the corrected LSB the same 8 codes span 0.203 mV - 8x too
# small against SIGMA_N - which costs the loop its settled-bias requirement:
#     FINE_CODES   span      settled bias   first |bias|<1%
#          8      0.203 mV      1.188%          window 133   <- fails the <1% spec
#         16      0.407 mV      0.530%          window 117
#         32      0.814 mV      0.253%          window  84
#         64      1.628 mV      0.255%          window  23   <- the original 1.6 mV intent
# The signal the loop detects is proportional to the span; the binomial counting noise
# is not. Shrinking the span 8x therefore costs ~8x in settled bias, and re-deriving
# GAIN does not recover it - GAIN sets the bandwidth, the span sets the SNR.
DITHER_SPAN_MV = 1.63             # input-referred, the C167/C168 design intent
FINE_CODES = round(DITHER_SPAN_MV / LSB)   # 64 at the corrected LSB, 8 at the old wrong one

# STAGE_GAIN corroboration, three unrelated routes (2026-08-10):
#   same-chip staircase inside one ngspice run          -> 8.4-8.5
#   300 codes x LSB vs current-domain I_FS/gm = 6.7 mV  -> 8.17 gives 7.63, 14% agreement
#   the original small-signal derivation                -> 8.17
# The nine-draw sweep that appeared to show ~4.5 is NOT a fourth route: each of its
# points carried its own +/-40 mV draw scatter, so a slope over 10 mV spacing carries
# no information. That sweep established saturation (H-753) and nothing else.

# GAIN is DERIVED, not stored. Rescaling LSB without re-deriving it was the trap that
# kept this file unpatched for an hour: the loop gain is g * (db/dp), and db/dp is
# proportional to the dither span in mV, which is proportional to LSB. Storing a
# number here would silently change the closed-loop gain by 8x when LSB was fixed.
def _db_dp():
    """Bias-fraction change per unit dither probability, at the settled point.

    The dither swings the residual by FINE_CODES*LSB, centred, so
        db/dp = Phi(+h/2sigma) - Phi(-h/2sigma),  h = FINE_CODES * LSB
    Reproduces the file's historical 0.194 when LSB is the (wrong) 0.20 mV.
    """
    h = FINE_CODES * LSB
    return _phi_cdf(h / 2 / SIGMA_N) - _phi_cdf(-h / 2 / SIGMA_N)


def _phi_cdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


GAIN = 0.25 / _db_dp()   # target 0.25 loop gain per update; ~10.0 at the corrected LSB
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
    """Report convergence AND railing. Without the railing column an out-of-range
    part is indistinguishable from a broken loop: both read 'never'."""
    tail = [abs(h['bias_pc']) for h in history[100:]]
    first = next((h['window'] for h in history if abs(h['bias_pc']) < 1.0), None)
    railed = sum(1 for h in history[100:] if abs(h['C']) >= COARSE_LIMIT) / len(tail)
    print('%-36s first |bias|<1%%: %-6s  settled mean %6.3f%%  max %6.3f%%  railed %5.1f%%' % (
        label, first if first is not None else 'never',
        sum(tail) / len(tail), max(tail), 100 * railed))


RANGE_MV = COARSE_LIMIT * LSB   # +/-7.63 mV input-referred


def reachable_fraction(sigma_mV):
    """Fraction of parts whose offset the coarse control can reach at all."""
    return 2 * _phi_cdf(RANGE_MV / sigma_mV) - 1


if __name__ == '__main__':
    print('LSB %.4f mV input-referred (%.4f at collector / gain %.2f); '
          'range +/-%.2f mV; derived GAIN %.2f'
          % (LSB, LSB_AT_COLLECTOR, STAGE_GAIN, RANGE_MV, GAIN))
    print('reachable at offset sigma 11.79 mV: %.1f%% of parts\n' % (100 * reachable_fraction(11.79)))

    # In range: the loop's own behaviour, isolated from the range question.
    report(run(offset_mV=0.5 * RANGE_MV, sign=+1), 'in range (0.5x range), corrected sign')
    report(run(offset_mV=0.5 * RANGE_MV, sign=-1), 'in range, original (diverging) sign')

    # At the population's nominal offset: out of range, and this is the common case.
    report(run(offset_mV=11.79, sign=+1), 'at sigma 11.79 mV - OUT OF RANGE')
    print('\nThe last line is not a loop failure. The part is unreachable: 11.79 mV is '
          '1.55x the\ncoarse range, so C sits on the rail and the dither cannot cover the '
          'remainder. Roughly\nhalf of all parts are in this regime - see the trim-range '
          'section of the README.')

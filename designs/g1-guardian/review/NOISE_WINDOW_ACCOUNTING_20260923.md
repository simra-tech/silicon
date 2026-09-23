# Conditional noise and measurement-window accounting

This saved-evidence review does **not** allocate a new noise target or pass
physical jitter/noise acceptance. The existing targets remain residual offset
<0.5 mV, the adopted engineering ±10% total threshold band, and fixed-calibration
temperature error ±2 °C. No allowed random decision-error probability,
sampling aperture, or off-chip frequency estimator is specified by those limits.

## Analog threshold path: do not double-count BGR

| Existing simulated fixture | Finite band | RMS, at its stated reference plane |
| --- | --- | --- |
| Standalone nominal BGR586 | 1 Hz–10 MHz | 100.111 µV at VREF |
| Original loaded SENSE, actual BGR/full TRIP, frozen clock DC0 | 1 Hz–2 MHz / 1 Hz–10 MHz | 36.1867 / 110.468 µV input-stimulus referred |
| R100 loaded SENSE, actual BGR/full TRIP, frozen clock DC0 | 1 Hz–2 MHz / 1 Hz–10 MHz | 36.2234 / 111.084 µV input-stimulus referred |

These fixtures have different source versions, loading and reference planes.
The loaded SENSE result already includes connected BGR model noise. Adding the
standalone VREF result to it, by RSS or worst-case sum, would double-count
sources and omit their frequency-dependent transfers. No such numerical total
is reported. The R100 output total is 1.263536 mV RMS over 1 Hz–10 MHz; dividing
that total by DC gain is not equivalent to integrating input-referred PSD.
The retained native/integrated input discrepancy is about 1.326%; it is not waived.

For the actual comparator differential input, the needed spectrum is
`Sdiff = Sisense + Sthreshold − 2 Re(Sisense,threshold)`. Shared BGR noise may
cancel or reinforce through different paths. Only compatible, disjoint source
contributions on the same reference plane may be combined; for two such scalar
terms, `sigma² = a² + b² + 2 rho a b`. Unknown correlation is not permission to
assume `rho=0`. The check script tests both correlation endpoints and rejects
double-counting. It does not apply this algebra to incompatible saved fixtures.

A prospective complete accounting would require
`|static error| + |bounded dynamic error| + k*sigma_sampled <= margin`, with
sampling transfer, statistical model and `k` explicitly approved. For example,
the existing ±10% band at 25 mV is 2.5 mV; a hypothetical 0.5 mV static-error
allocation leaves at most 2.0 mV for **all** remaining terms, not an adopted
noise allowance. Neither finite-band RMS nor the <0.5 mV static target is a
deterministic peak-noise bound. Existing failing static decisions cannot be
made acceptable by assigning them a noise budget.

The 20 ns decision latency is not a boxcar aperture. Noise above the exported
band, clocked/cyclostationary comparator behavior, full physical fields and
sample-to-sample/corner variability remain unqualified. Earlier 200 ns boxcar
results are sensitivities only. A numerical stochastic allocation needs an
owner-approved estimator/aperture and risk criterion before acceptance can change.

## Temperature readout: conditional count quantization

The [T2F interface](../blocks/g1_t2f/INTERFACE.md) explicitly sends free-running
TEMP_OUT off-chip and specifies **no on-chip counter**. The current CTRL top
has T2F enable/mode outputs, not a temperature-count input/register. Thus the
saved diagnostic 1/5/10 µs windows are not selected system measurement windows.
The simulation's edge/period estimator is also not an integer gate-time counter.

For an ideal fixed-duration integer edge counter only, one count corresponds
to `1/(gate_time * df/dT)`. Using the specification's nominal 5200 Hz/°C:

| Diagnostic gate time | One-count frequency step | Nominal temperature step |
| --- | ---: | ---: |
| 1 µs | 1 MHz | 192.308 °C |
| 5 µs | 200 kHz | 38.462 °C |
| 10 µs | 100 kHz | 19.231 °C |

An arbitrary-phase ideal count has a less-than-one-count error envelope.
Making that envelope no larger than 2 °C requires at least **96.154 µs** at
the nominal slope, even with zero allowance for calibration residual, clock
error or jitter. This is a conditional design constraint, not a selected gate
time or demonstrated ±2 °C performance. Real calibrated slopes vary. A
reciprocal/period estimator needs its own timestamp-resolution and timebase
error model; it is not subject to this integer-count calculation.

The completed external-reference T2F perturbation cases have simulated period
standard deviations 1.88957 ps / 424.957 ps / 1.98554 ns for 0/1/5 mV, evaluated over
8–32 µs. OSC's separate external perturbations give 21.4698 / 50.5805 /
209.649 ps over 5–20 µs. Zero-amplitude variation is a numerical baseline,
not physical device noise. Their overlapping count windows are correlated;
do not divide by square-root sample count or extrapolate to longer gates.
No conversion from OU perturbation amplitude to actual BGR spectrum or
intrinsic oscillator phase noise has been qualified.

## Reproduction and remaining acceptance

Run, from the repository root:

```sh
python3 designs/g1-guardian/review/check_noise_window_accounting.py --test-only
python3 designs/g1-guardian/review/check_noise_window_accounting.py
```

The read-only script binds the existing specification, interface/RTL and saved
evidence by SHA-256, checks completed synthetic amplitude coverage without
changing original statuses, and prints conditional arithmetic. It performs no
simulation or artifact rewrite. Sources retain their pinned ngspice-46/SG13G2
runtime identities and warnings in the linked block reports; this accounting
does not transfer qualification across them.

Completed here: reference-plane/correlation accounting and conditional window
arithmetic. **Not run:** adopted stochastic allocation, full sampled-noise or
physical phase-noise acceptance, hardware measurement. Required next design
choice is the off-chip measurement method/window/timebase and permitted
decision risk; required evidence is the compatible sampled differential-noise
transfer/cross-spectrum. No arbitrary new target is selected by this record.

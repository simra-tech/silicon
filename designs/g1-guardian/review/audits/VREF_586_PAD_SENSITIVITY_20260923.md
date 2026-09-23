# Current BGR source: actual-pad and fixture-leakage DC sensitivity

Nine cases, each with 34 temperatures from −40 to 125 °C, completed in
198.885 s total. The no-pad control reproduces the original frozen586
nominal waveform byte-for-byte. All 2,842 BGR parameters are identical
before/after and across all nine cases. This is simulation, not measurement.

At 25 °C the modeled 10 MΩ instrument input shifts core VREF by −2.327408 mV
relative to the open pad. An assumed ±10 nA external fixture leakage shifts
it by approximately ±223.10 µV. Fixture loading therefore remains part of
the measurement error budget; no acceptable loading allocation or physical
package-leakage bound has been established.

| External condition | Core VREF at 25 °C (V) | Shift from open pad (µV) | Maximum absolute shift over temperature (µV) |
| --- | ---: | ---: | ---: |
| Open pad | 1.045444701 | 0 | 0 |
| Inject 0.1 nA | 1.045446932 | +2.2310 | 2.2763 |
| Sink 0.1 nA | 1.045442470 | −2.2310 | 2.2763 |
| Inject 1 nA | 1.045467011 | +22.3096 | 22.7625 |
| Sink 1 nA | 1.045422392 | −22.3097 | 22.7626 |
| Inject 10 nA | 1.045667793 | +223.0913 | 227.6216 |
| Sink 10 nA | 1.045221600 | −223.1011 | 227.6290 |
| 10 MΩ input | 1.043117293 | −2327.4079 | 2371.3728 |

The no-pad reference is 1.045449584 V at 25 °C. Its simulated box TC is
8.529823 ppm/°C; open-pad TC is 8.394272 ppm/°C. All nine TCs remain below
the existing 50 ppm/°C target in these nominal-process fixtures. Leakage
cancellation or a lower TC under loading is not a compensation claim.

## Exact scope

The source SHA-256 is
`586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b`.
The original nominal deck, source and simulator initialization are copied
unchanged for the control. Every other case changes only the declared pad,
external load, and output observations; literal inverse transformation returns
the original deck. The detailed installed `sg13g2_IOPadAnalog` is unchanged.

The BGR uses its retained 329-capacitor model-level source, **not a new native
physical RC extraction**. The 613.3424975 Ω route is the previously documented
whole-tree resistance sensitivity, not a newly extracted point-to-point route.
IPTAT retains an ideal 1 V termination. Core/IO rails are ideal 1.2/3.3 V.
Mismatch is disabled. Positive fixture current sinks from the external pad to
ground; negative current injects. The chosen currents are deterministic
sensitivities, not inferred package distributions or rated limits.

| Check | Status |
| --- | --- |
| Original no-pad 34-row waveform byte equality | Passed |
| Nine solver endpoints, finite data, full ordered parameter equality | Passed |
| Nominal-process TC ≤50 ppm/°C for all nine fixtures | Passed |
| Loading-error allocation and acceptance | Not run; no allocation adopted |
| New native full-RC/fill and real SENSE/T2F downstream load | Not run |
| Pad startup/stability, process/mismatch ensemble, IR/EM/lifetime | Not run |
| Physical package/fixture leakage or calibrated measurement | Not run |
| Population/yield interpretation of deterministic cases | Not applicable |

Runtime is ngspice 46, pinned IHP SG13G2
`84374023ee8b4b126bebbba67fcbada0a9c0ff0b`, image configuration
`ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2`.
The runner checks exact library/OSDI/banner/init/source/previous-wave hashes
before execution, uses one CPU and a 120 s watchdog per leaf, and retains
warnings, full logs, decks, parameters and data. No retries, card changes,
rule changes or physical-layout adoption occurred. Full V17 remains incomplete.

Reproduce with `run_586_vref_pad_sensitivity.py --output <unused-directory>`
inside the pinned runtime. The portable evidence manifest records all original
and exported hashes; only declared host-path tokens are normalized. Repeated
identical source/init copies are represented once with their exact hashes.

# Conditional manual-isolation diagnostic

All three matched IO-first attempts **failed numerically** at the unchanged
120 s simulation limit. No complete waveform was produced, so isolation,
load-energy, gate-voltage and safety acceptance are **not run**.

| Electrical pad view | Exact source SHA256 | Last reported simulated time |
|---|---|---:|
| Original explicit-body, original tap R | `c46e32249a04ed75d25d5f2b4f0b79304c25f7d85ce7628ee5a65b1734f43256` | 1.37643 µs |
| Physical A/P, conditional single-P R arithmetic | `b332d78f89653d03f8e9afe0865ddace98a06709fca093a22430bcd4d5fed854` | 1.37644 µs |
| Physical A/P, conditional double-P R arithmetic | `25a4317632da2ce5a06a76592922232b0864a57dac58fe4bee07931e55717efe` | 1.37644 µs |

The two conditional R formulas are sensitivities, **not validated physical
bounds**. Source preparation proves exactly 42 local tap-R edits with an
exact inverse to the original explicit-body library; 386 expanded tap
occurrences are source-mapped. Models, ordered primitive terminals, all
non-tap parameters and explicit body-port propagation remain held. Four
independent source-edit rejection/control tests passed.

The fixture uses the unchanged real CSD16340Q3 model, extracted GATE view,
explicit-body IO pads and EN held low. Its assumed manual disconnect is
10 MΩ with 100 pF contact capacitance, a 10 µF downstream bus capacitor and
10.5 kΩ bleeder. Raw bus remains 5 V, with the existing 5 Ω/100 nH load and
downstream flyback diode. There is no ideal bus-voltage clamp, IC or UIC.

Prospective conditions require measured initial bus ≤10 mV **and** load-current
verification before a transition, followed by ≤10 mA load current and ≤8 nJ
load-resistor energy over 16 µs. The historical 1 V gate/VGS criterion is
reported separately and is not waived. These are unvalidated fixture/design
requirements, not measurements or demonstrated protection.

The original two pre-simulation harness failures (host/container input path,
then host Python pathlib API availability) are retained separately. Correcting
them changed no circuit or numerical setting. All three actual simulations
used identical original solver options and bounds. No watchdog ladder or
solver-tolerance remedy was attempted. Missing-core, closed-switch negative
control, powerdown, brownout and hardware sequencing verification remain
**not run**. No automatic-fault, SOA, lifetime or safety claim follows.

## Built against

| Item | Identity |
|---|---|
| IHP SG13G2 | `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`, unchanged model-library hashes |
| ngspice | 46, creation 2026-07-27; exact runtime identity checked against frozen reference |
| OCI config | `ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2` |
| GATE extracted source | `e91617f5fcf6f5a0dc721a2ba53b507a05cc226d6dbf0bebaa858a1e7d876765` |
| Real FET model | `c5572438f1a79c8e9f48cfcf5a8d152daafdad8e8ec26ac30f807f0211edf2df` |

`prepare_manual_isolation.py` records the exact original-fixture inverse;
`run_manual_isolation.py` binds runtime and source inputs and retains each
timeout. `analyze_manual_isolation.py` contains the prospective electrical
criteria and analytic integration controls; it received no complete waveform
from these attempts.

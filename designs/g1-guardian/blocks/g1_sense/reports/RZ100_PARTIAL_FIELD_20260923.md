# R100 compensation and partial-field verification

The C45/R100 candidate improves the tested conditional loop margins. It is
not adopted and does not have complete physical PEX qualification. All
numbers below are simulated or derived from saved simulation/layout data,
not hardware measurements.

## Source and method

The C45/R62 source is `b8912a862b61554266239634dd388ed0ffad229c0b0e48819ad129d589352e97`.
Two isolated candidates change only `XOTA/XRZ` length, holding width at 1 µm
and the main MIM at 45 × 23 µm:

| Candidate | Canonical source SHA-256 | Disposition |
|---|---|---|
| R80 | `262c5221abc2c7b95a986c8fab40f1bec5c1d35cf6feaded68f161118671386f` | Fast conditional phase margin failed |
| R100 | `bb933fdabf3fd8a5117bf47f33cd40657caf78ef424e6a9bfddda0f11190d782` | Continued bounded characterization; not adopted |

Exact inverse and flattened graph checks retain 159 primitives, 134 source
nets, external nine-port identity, and all model cards. The one intentional
resistor geometry change is recorded explicitly. Matching 11,511 original
model observations and the native C45 mismatch-area relation does not transfer
an old statistical campaign to this changed circuit.

Each differential baseline uses its own changed source. Each Tian pair must
pass the original 1 µV/1 nA within-source operating-point controls and exact
paired model observations. Original exact comparisons against another source
remain separate diagnostics, including the earlier 28.679 pV/109.02 fA
partial-C versus bare-source comparison failure. Saved-data own-baseline
qualification did not rerun or relabel that original exact failure.

## Borrowed-field screening

This first screen uses all 844 proven source-net-pair capacitors from the R62
native extraction, unchanged—not a delta. The 134 unbound VSUBS terms are
explicitly omitted as a diagnostic hypothesis, not physical zero or a bound.
These are **borrowed-field results, not candidate-specific PEX**.

| Source and condition | Gain V/V | −3 dB bandwidth MHz | Conditional PM ° | Lowest observed GM dB |
|---|---:|---:|---:|---:|
| R62, fast/high/hot | 19.983445 | 5.301082 | 55.281213 **failed** | 15.977867 |
| R80, fast/high/hot | 19.983445 | 5.695914 | 59.605811 **failed** | 15.821666 |
| R100, fast/high/hot | 19.983445 | 6.413123 | 63.606789 | 14.475763 |
| R100, nominal | 19.957506 | 5.450706 | 70.935051 | 15.344426 |
| R100, slow/low/cold | 19.998479 | 2.280586 | 82.061511 | 16.601886 |

Limits remain gain 19.9–20.1, bandwidth ≥2 MHz, PM ≥60°, and GM ≥10 dB.
The three R100 cases passed these scoped screens, with all nine leaves passing
source/runtime/model and own-source probe controls. They do not exhaust PVT,
common-mode, statistical, or clocked-system qualification.

## Native and actual-field evidence

The isolated R100 GDS is
`450a49062d17f65be1046736c2ebeff219b4c4d4b22fac0998940c158741a637`.
The hierarchy-preserving replacement changes only main-cell native passive
geometry and associated routing. The R100 CZ feed moves to macro x=224.81 µm;
transistor placement, 835 channels, source graph, and nine external ports
remain held. Independent native/source checks passed. Unchanged stock main
and maximal DRC returned zero markers; strict LVS passed with nine matched
pins. The stock result does not cure the prior 51 extracted A/P annotation
differences or unresolved compact-model terminal-plane applicability.

The actual R100 native extraction completed with 978 finite binary64
capacitances and exact source-label mapping. The full 135-node matrix passed
symmetry, positive-edge energy, and ≤1e−25 F charge-residual checks; the maximum
row residual was 1.283e−28 F. The largest change from R62 was CZ-to-VDD:
1.203731 → 1.299601 fF. No difference-only circuit insertion is used.

Own-source private-node controls passed exact model/operating-point parity,
byte-exact AC/noise data, and byte-exact 6,700 × 18 transient values. They
preserve device hierarchy and mismatch identities without splitting devices
or choosing contact weights. Only after both controls passed was the actual
R100 844-capacitor diagnostic source prepared:
`ffb14762659eaf02b6a62e9edea3caa0e143cbc7881378b329d6ab9945a6554b`.

All three actual-field cases passed the original scoped limits, with all nine
leaves passing full model observations and their own-source probe controls:

| Actual R100 field condition | Gain V/V | −3 dB bandwidth MHz | Conditional PM ° | Lowest observed GM dB |
|---|---:|---:|---:|---:|
| Fast/high/hot | 19.983445 | 6.413233 | 63.607068 | 14.475443 |
| Nominal | 19.957506 | 5.450825 | 70.935340 | 15.344080 |
| Slow/low/cold | 19.998479 | 2.280581 | 82.061860 | 16.601572 |

Complete-field acceptance remains **failed/unresolved**:
native MIM extrinsic fields, tap/contact fields, VSUBS binding, intrinsic versus
extrinsic ownership, distributed terminal planes, finite wire resistance, and
full-chip/fill context are not qualified by this matrix. No full MIM-pair
subtraction, rule/model change, or capacitance fitting is used.

## Own-source noise and settling

The nominal actual-BGR/full-TRIP fixture retains its original source/loading,
seed, simulator settings, 11,512 model observations, and legacy 27 controls.
Input-stimulus-referred noise integrated over 1 Hz–2 MHz is 36.22343 µV RMS;
output noise over 1 Hz–10 MHz is 1.263536 mV RMS. Noise is a frozen-DC,
one-sided-stimulus result; no 20 ns decision interval is treated as a filter.
The native versus numerically integrated noise discrepancy remains recorded,
not waived. No numerical noise allocation is invented.

Rise/fall tests completed through 1.02 µs with independent final-DC targets.
Saved-point final 1% band entries are 306.526/307.323 ns after the step start;
overshoot is 0.03694%/0.003944%. Endpoint gains are 19.95900/19.95760 V/V.
The R62 rise result was 207.879 ns with 1.6876% overshoot. Thus R100 trades
lower overshoot for a slower settling tail; sampled-system requalification
must retain that consequence. These are characterizations, not an invented
settling-time acceptance or between-sample proof.

## Built against

| Item | Pinned identity / verification |
|---|---|
| IHP SG13G2 | `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`; runtime COMMIT and model/deck hashes |
| ngspice | 46, SPARSE; exact version/model inventory versus completed fixture |
| KLayout | 0.30.9; runtime assertion |
| KLayout-PEX | 0.3.12; unchanged native 2.5D API, source hashes |
| OCI config | `ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2` |
| OCI manifest | `5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0` |

Physical/statistical adoption, complete PEX, combined changed-TRIP electrical
qualification, and hardware verification are **not run** by this branch.

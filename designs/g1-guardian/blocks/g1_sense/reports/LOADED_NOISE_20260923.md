# Source-held loaded SENSE AC/noise

The new **conditional frozen-DC noise audit passed** for the exact current
gm4/comp3 SENSE with actual BGR586 and full TRIP loading. It is not physical
PEX, periodic comparator noise, a noise-population result or an electrical
noise-limit pass: no block noise limit has been allocated.

| Check | Result |
|---|---|
| Source/runtime/model identities | Passed; all three circuit sources unchanged |
| Realized model parameters | 11,512 before/after/reference and legacy27 exact |
| Existing operating point | All nine saved bias voltages exact |
| AC/noise spectra | 701 finite positive noise points,1Hz–approximately10MHz |
| ASD input normalization | Output/input ASD divided by AC gain: max relative error3.33e-16 |
| Integration controls | White PSD,1/f PSD,analytic boxcar,ASD-square scaling,invalidPSD/header rejection passed |
| Complete PEX/model-plane coverage | Unresolved; no qualification inherited |
| Periodic/sampled noise acceptance | Not run |

The seed73001 operating point is TT,25°C,3.3V,positive shunt25mV/negative0,
clock at its original DC0 state. The AC stimulus perturbs the positive shunt
terminal by1V with negative fixed: it is an input-stimulus reference, not a
constant-common-mode differential drive. The DC source/circuit/loading and
solver settings are unchanged. Low-frequency gain is19.958435114V/V.

| Finite frequency band | Output RMS | Input-stimulus-referred RMS |
|---|---:|---:|
|1Hz–1kHz|128.302µV|6.42845µV|
|1Hz–100kHz|220.206µV|11.0336µV|
|1Hz–2MHz|699.785µV|36.1867µV|
|1Hz–sampled10MHz endpoint|903.841µV|110.468µV|

These are simulated small-signal noise integrals, not measured values. ASD is
exported inV/√Hz with `unset sqrnoise`; its square is integrated against Hz.
Piecewise log-linear PSD quadrature uses8/16-point crosschecks. The actual last
frequency9999999.999999788Hz is recorded; no tail is extrapolated. Unknown
out-of-band noise prevents a total-noise bound.

The20ns decision latency is **not** a measurement aperture. Separate normalized
boxcar20ns/200ns/1µs filters are reported only as declared sensitivities. For
the200ns assumed boxcar, the sampled full-band input value is41.1516µVrms.
No sampler equivalence or decision-error probability follows.

Native printed integrated totals are903.836µV output and113.054µV input. The
input-total disagreement with independently integrating the exported PSD is
retained explicitly; these are not declared numerically equivalent. Existing
ideal-reference gm4 noise was not rerun: its four saved band integrals replay
exactly, including its separately retained2.3197% input-total discrepancy.
Ideal-reference and actual-loaded runs also differ in operating point/loading;
their difference is not a controlled physical improvement claim.

## Failures and model scope

Initial preparation used a cancellation-prone analytic sinc integral; its
algebraically identical stable expression fixed the unit test without changing
the1e-12 bound. Runtime r1 then failed before simulation by comparing the OCI
config digest to the manifest digest; both identities are now explicitly named.
The r2 simulator completed67.526s and saved AC, but noise failed because the
inherited voltage-only save list excluded noise outputs. The r3 recovery adds
only four output save names, not solver/model changes. r3 ngspice completed
89.074s, outer recorded wrapper93.456s. All failures remain exported.

The successful log still contains1392 resistor-vmax warnings and one model
temperature-limiter NaN warning during operating-point solving. They are
preserved, not waived by finite final spectra. This remains conditional model
evidence, not demonstrated physical validity beyond model limits.

## Built against and reproduction

| Component | Pinned identity and evidence |
|---|---|
| IHP SG13G2 |84374023ee8b4b126bebbba67fcbada0a9c0ff0b;32 model-file hashes exact |
| ngspice |46,creation2026-07-27; exact runtime version text and SPARSE unchanged |
| OCI manifest/config |5fd78498… / ddeb6957…; same pinned image, distinct OCI identities |
| SENSE source |baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877 |
| Loaded source projection |BGR7de0fc30… and TRIPf49e17db…; exact qualified reference |

Use [run_loaded_noise_audit.py](../sim/run_loaded_noise_audit.py) with the pinned
runtime and a fresh `--output` directory;120s simulator bound. Its `--test-only`
mode runs integration/control tests. [audit_existing_noise.py](../sim/audit_existing_noise.py)
reads the prior evidence without simulation. The unchanged reference is
`g1_trip/sim/qualification/joint586-mm-tranqual-20260922-a-enabled`.

Portable evidence: [artifact manifest](loaded-noise-evidence-20260923-r2/artifact_manifest.json).
Only machine path prefixes are reversibly normalized; original and portable
hashes are both recorded. Original r3 summary SHA
`1e09a3dd2ebe9dc330714bb1577e6229ff4b7e797c0486ce0cb54b1b10c091d0`.

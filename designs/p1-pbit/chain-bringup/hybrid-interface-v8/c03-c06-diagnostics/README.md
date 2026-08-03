# C03-C06 controlled V8 diagnostics

This package publishes four one-variable transient diagnostics derived from
the C02 ideal gate-isolation experiment. It preserves each reviewed deck,
native ngspice-46 log, binary raw waveform, exact source binding, and an
independently reproducible facts table.

The source decks are portable copies: only the three model-library prefixes
were changed from the execution environment's PDK path to `$PDK_ROOT`. Native
deck identities are retained in `parent_bindings.txt`. Frozen `UNRUN` comments
record pre-invocation source state; the bound logs and raws establish execution.

## Controlled experiments and supported conclusions

- **C03, cadence:** relative to C02, only the input period changes from 400 ps
  to 4 ns, the observation window from 2 ns to 20 ns, and matching labels and
  output filename. Ten differential input crossings produce zero output
  crossings. The low output's range grows from 13.6153 mV in the first period
  to 120.2843 mV in the fifth. This is a partial analog response, not a logic
  recovery result.
- **C04, settling:** relative to C03, only the stop time changes from 20 ns to
  100 ns, with matching labels and output filename. Its first 10,065 points,
  including every one of 82 vectors, are bit-identical to C03. Across 25
  periods, 50 input crossings produce zero output crossings and the low-output
  range converges near 135 mV. Lower cadence plus additional settling is
  insufficient in this circuit.
- **C05, common mode:** relative to C02, the sole electrical change is `vcm`
  from 1.42 V to 1.549836259081225 V, the retained V2 upper common-mode bound.
  The internal `CM_P` range rises to 269.7889 mV but remains 0.9454–1.2152 V;
  ten input crossings still produce zero output crossings. Available producer
  common mode is insufficient by itself.
- **C06, pair width:** relative to C02, the sole circuit change is `XM1` and
  `XM2` width from 6.0 µm to 24.0 µm. `CM_P` range rises to 371.2934 mV but
  remains 0.8589–1.2302 V, and both outputs remain latched. Four-times pair
  width is insufficient by itself; this does not select a production size.

All output crossing statements use the 0.6 V rail-midpoint proxy. The review
also checked 0.56029, 0.59383, and 0.65602 V, with the same zero-crossing
result; none of these proxies is a measured corner-specific inverter trip
point. The ideal C02 voltage sources are diagnostic, not a production buffer.

## Evidence boundary

For all four runs, execution completed, raw structure is valid and finite, and
the declared scalar measurements reproduce from the native vectors. These
experiments reject four proposed changes as individually sufficient fixes for
the observed V8 no-switch condition. They do not identify a unique cause, prove
the exact current comparator at 5 GS/s, qualify entropy, or evaluate any P1
specification. Engineering gate status remains running.

The decks use model includes and a control block, so they are outside the
current backend-independent OpenADA `circuit.simulate` subset. This package
therefore reports native ngspice evidence and does not relabel it as normalized
OpenADA evidence.

## Verify

From this directory, with the parent C02 package present:

```sh
python3 verify.py
sha256sum -c SHA256SUMS
```

A rerun with a compatible IHP SG13G2 installation is new evidence and is not
required to verify this retained result. No signoff, tape-out readiness, or
foundry acceptance is claimed.

# Fast-corner initialization controls

These are simulated, model-level diagnostics. They do not qualify physical
parasitics, change the frozen calibration rule, or release the fast 30-sample
population. The original SPARSE 1200 s transient timeout and KLU initialization
failure remain failed attempts.

The reference is seed 78001, fast process corner, −40 °C, 3.0/1.08 V rails,
true common mode 0 V, 25 mV differential input, codes 135/151 and 5 MHz clocks.
No canonical device source, model card, tolerance, initial-condition constraint,
or transient timestep was changed. Eight `.nodeset` guesses use the literal
printed original operating-point values on canonical circuit nodes; they are
not internal OSDI node-label interpretations.

## Completed operating-point controls

| Control | Numerical/full-parameter result | Simulated runtime | Exact OP comparison |
| --- | --- | ---: | --- |
| Original SPARSE | Passed | 73.127 s | Eight original printed values exact |
| SPARSE plus eight nodeset guesses | Passed | 37.489 s | Failed exact equality; largest difference 39.650172 pV |
| KLU plus the same guesses | Passed | 27.319 s | Failed exact equality; largest difference 149.712909 pV |

All 11,512 parameters before and after OP, including all 27 legacy anchors,
matched the original realization exactly. The output checks validate all eight
named voltage columns and finite values. The first OP output column is a scale,
not physical time. Initialization warnings are retained: 6,289, 3 and 4
respectively. Finite convergence does not establish model validity or prove the
cause of the original failure. No tolerance is substituted for failed exact OP
comparisons.

The source-bound contract is
[nodeset OP contract b](joint586-fastcold-nodeset-op-contract-20260923-b.json),
SHA-256 `31a0793df39697ec19ced5891d78029b13521f6ea7194cb2be8afafe0f5b8164`.
Each declared run directory contains its exact deck, transform audit, source
copies, command/runtime provenance, full log, output, and parameter summary.

## Prepared full transient pair — not run

[Transient contract b](joint586-fastcold-nodeset-transients-contract-20260923-b.json),
SHA-256 `bbd020b5d3deed23eb1c9ebbb7cecad00e961db69a4a637ce1142f37e9676acd`,
declares two fresh full 1.02 µs diagnostics with the original 1200 s limit.
One uses SPARSE plus the same guesses; the other adds KLU. Inverse deck
transforms restore the original failed fixture byte-for-byte after removing
only the declared initialization/solver lines and restoring the output path.
All eight original measurements, 19 vectors, original sampling and full
parameter checks remain unchanged.

The unrun preparation a is preserved. Revision b adds explicit rejection of
`analysis aborted`, including an exit-zero failure with a printed end marker.
Seven runner/transform tests pass. Four independent pair-comparison tests pass.
The pair analyzer separately records numerical completion, exact parameter
identity, decoded-byte/numeric/grid equality, actual clock events and decisions.
Interpolated voltage differences are descriptive only; duplicate output times
are not silently interpolated. Pair-wave comparison is **not run** until both
diagnostics complete and pass independent integrity checks.

Any subsequent fixture or solver adoption needs its own declared qualification;
the five old successful fast fixtures are not silently inherited.

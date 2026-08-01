# Matched CML Divide-by-Four Load-Isolation Diagnostic V1

## Scope

This package preserves a matched native-ngspice control/experiment pair for
the frozen Candidate V5 CML divider. The control contains one unloaded
divide-by-two stage. The experiment adds a second byte-identical stage whose
clock inputs are driven directly by stage one. Source, stimuli, transient
settings, model references, and simulator executable are held fixed.

The controlled result supports a stage-one loading effect under this
diagnostic condition: adding stage two reduces stage-one differential
peak-to-peak range by 11.94% and the defined mean absolute crossing slope by
93.44%. It does **not** establish that this degradation causes the 27
stage-two reversals, direct-cascade compatibility, a specification result,
signoff, or tape-out readiness. The P1 engineering gate is not advanced by
this package.

## Controlled delta

The source netlist in both sides is byte-identical, SHA-256
`689d4beedfce278f0c13cf0e79a25b87ba8a12d25b9459e51dfbfde041cd3db7`.
The private control and experiment deck identities are respectively
`4127fc03374d9ba777f700016de2e748dc20bf577e5706360a924c12ac55178d`
and
`97a52bb7757c5b36160a28377cf50bede0197656b3a395a411faec19eea5532c`.
Their six differing lines comprise three header comments, one instance
comment, deletion of `XSTAGE2`, and the raw-output filename. Every electrical
line other than the `XSTAGE2` instance is identical. The complete unified
diff and source checkpoint are under `source-checkpoint/`.

The published decks replace only the private PDK prefix with literal
`$PDK_ROOT`. The public diff also uses relative deck names. Original and
public identities are recorded in `PUBLIC-COPY-IDENTITIES.tsv`.

## Execution and raw evidence

The same native ngspice 46 executable, SHA-256
`6aacaca88f656e5e19074ac070fb410bf6cc437df1de88ec28d50a24c6239a1b`,
was invoked exactly once per side with no retry:

- control: rc 0 in 2.274 seconds;
- experiment: rc 0 in 6.143 seconds.

Both invocations produced fresh raw files. Independent byte parsing confirms:

- control: SHA-256 `8317c689599ff6145f6ff8a70e5dbc4b4e05d8dc870b5d44e91b3fce9e6695f0`,
  429 vectors by 2,284 points, 7,838,688-byte payload;
- experiment: SHA-256 `dd0f874ee53e1fff13581f99e3db04185b166705244e81be9ca59a2918a9a97f`,
  849 vectors by 2,284 points, 15,512,928-byte payload;
- both contain only finite stored doubles and strictly increasing time from
  0 to 4 ns.

Execution completion is separate from engineering interpretation. Control
stderr retains a temperature-limiting NaN warning followed by completed
dynamic gmin stepping. Experiment stderr retains the same temperature warning
and a failed dynamic-gmin attempt followed by completed true-gmin stepping.
The streams, decks, pre/post hashes, raw manifest, and pair manifest remain
under `runtime/`.

The runtime pair uses a control block, includes PDK collateral, and saves a
large native vector set. It is therefore outside the self-contained OpenADA
`circuit.simulate/v1alpha2` subset; this package reviews the retained native
evidence and makes no normalized OpenADA conformance claim.

## Read-only matched analysis

The manifest-closed analysis under `analysis/accepted-v1/` recounts every
differential crossing over the closed 2-to-4 ns window. It reports:

| Signal | Crossings | Mean same-direction period | Mean absolute crossing slope |
| --- | ---: | ---: | ---: |
| control clock | 20 | 200.000 ps | 1.200000e12 V/s |
| control stage one | 10 | 399.999 ps | 1.391745e11 V/s |
| experiment clock | 20 | 200.000 ps | 1.200000e12 V/s |
| experiment stage one | 10 | 400.004 ps | 9.123610e9 V/s |
| experiment stage two | 27 | 144.654 ps | 9.589121e10 V/s |

Stage-one differential peak-to-peak range changes from 1.310150093 V in the
control to 1.153711331 V in the experiment, a reduction of 0.156439 V or
11.940522%. The mean absolute bracketing-sample crossing slope changes from
1.391744683e11 to 9.123610262e9 V/s, a 93.444480% reduction. The stage-one
crossing count and approximately 400 ps same-direction period are retained.

Because the electrical delta is the added `XSTAGE2` instance, the matched pair
supports causal attribution of those measured stage-one changes to adding the
stage-two load under this diagnostic condition. It does not isolate the cause
of the stage-two reversals; a separate controlled experiment is required.

The experiment raw's binary payload is byte-identical to the previously
published direct-cascade raw. Their full-file hashes differ only because the
raw headers contain different run metadata.

## Failed-attempt record

The first read-only report-generation attempt wrote the two complete TSVs and
then stopped in the report section because of a multi-line formatting error.
Those TSVs are preserved under `analysis/failed-attempt-v1/`. They are
byte-identical to the accepted TSVs; the accepted package reran only the
read-only report generation and then wrote a closure manifest. No simulation
or design edit occurred in either analysis attempt.

## Package boundary

`PUBLISH-MANIFEST.tsv` covers every payload except itself. Public copies
replace private PDK, tool, and workspace prefixes with `$PDK_ROOT`,
`$TOOLS_ROOT`, and `.`; the identity map records every changed copy. Private
PDK files, the simulator executable, credentials, prompts, transcripts,
reasoning, absolute host paths, symlinks, and executable files are excluded.

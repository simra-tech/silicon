# Stage-Two CML Waveform-Replay Diagnostic V1

## Scope

This package preserves the source, execution evidence, failed harness attempt,
and full correction history for a stage-two-only replay of the frozen Candidate
V5 CML divider. The experiment drives the same stage-two circuit from either
the unloaded or loaded stage-one waveform captured by the published matched
load-isolation diagnostic.

The replay source is an ngspice XSPICE two-output `filesource`. It reproduces
the captured voltages through an ideal source with zero source impedance. The
experiment can therefore test waveform sufficiency under ideal drive. It does
not reproduce the electrical impedance of the direct stage-one-to-stage-two
interface and cannot by itself establish compatibility, a specification
result, signoff, or tape-out readiness. The P1 engineering gate remains open.

## Source checkpoints

`source-deck/v1-unsupported/` preserves the first source checkpoint. Its four
waveform files each contain all 2,284 native samples from the matched control
and experiment raws, but its independent sources use unsupported
`PWL FILE=` syntax. No simulator was invoked from V1.

`source-deck/v2-filesource/` preserves the accepted repair. It combines each
arm into one 2,284-row `(time, p, n)` file and drives both nodes with one
documented two-output `filesource` A-device. The two decks differ only in two
header comments, the replay-data filename, and the raw-output filename. The
source netlist is byte-identical in both arms, SHA-256
`689d4beedfce278f0c13cf0e79a25b87ba8a12d25b9459e51dfbfde041cd3db7`.

The extraction scripts are retained and hash-bind the previously published
matched-load raws. Their public copies default to the sibling
`custom-cml-div4-matched-load-isolation-v1/runtime` package; the path can be
overridden with `MATCHED_LOAD_RUNTIME`.

## Execution evidence

The complete attempt chain contains three native ngspice 46 invocations, not
the requested no-retry pair:

| Invocation | UTC start | Result | Raw SHA-256 |
| --- | --- | --- | --- |
| failed-attempt unloaded | 03:49:43Z | rc 0; runner then crashed before loaded | `c954e868ec28eaf716e583f07d7d3dcd6b4cfbca3ea236d66850a0607722bfed` |
| restarted-pair unloaded | 03:50:33Z | rc 0 | `456aa04dafc1b8a3023552e31cc1ba1c16fd8c55e04b5171934a7f0670489881` |
| restarted-pair loaded | 03:50:36Z | rc 0 | `2f2010d24096030bb0317bf1c774fa16bcb82a61c09eb6f3badca402da357c26` |

The first unloaded raw is under `runtime/failed-attempt-v1/`; the restarted
pair is under `runtime/pair-v1/`. The runner stored a three-field structural
record but unpacked two fields at the loaded gate. The repaired runner then
restarted from the beginning, so unloaded ran twice. The original failed
runner and traceback are not present in the sealed run directory; this is an
evidence-custody limitation.

The retained pair raws are structurally valid: unloaded contains 429 vectors
by 2,069 points and loaded contains 429 vectors by 2,009 points; both have
exact binary payload sizes, finite stored doubles, strictly increasing time,
and a 0-to-4 ns span. Both stderrs retain the temperature-limiting NaN note and
completed dynamic-gmin stepping.

## Read-only waveform facts

`analysis/read-only-waveform-v1/` preserves a six-member raw-only analysis of
the closed 2-to-4 ns window. It uses input difference
`v(div2_p_1)-v(div2_n_1)` and output difference `v(div4_p)-v(div4_n)`, lists
every strict opposite-sign adjacent-sample crossing and every exact-zero
sample, and retains both the parser and an independently implemented
self-check. `VERIFY-PUBLIC-WAVEFORM.py` is a separate, package-relative
verifier for the public copies. A fresh publication review ran it against the
two published raws and reproduced all 55 TSV rows and all sampled extrema.

| Arm | Signal | Window rows | Crossings | Exact zeros | Min (V) | Max (V) | Peak-to-peak (V) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| unloaded | input | 1,031 | 10 | 0 | -0.6546556940137505 | 0.6549758222483009 | 1.3096315162620513 |
| unloaded | output | 1,031 | 5 | 0 | -0.9106958834808433 | 0.9207151589507208 | 1.8314110424315642 |
| loaded | input | 1,001 | 10 | 0 | -0.5720668887425033 | 0.572536771868267 | 1.1446036606107703 |
| loaded | output | 1,001 | 30 | 0 | -0.5728373127678337 | 0.5745788719416585 | 1.1474161847094921 |

These are waveform observations under ideal zero-source-impedance replay.
They do not establish why the loaded output has more crossings, do not model
the original interstage impedance, and are not a pass/fail or compatibility
result. The preserved self-check's opening docstring says "13 fields"; its
executed assertion and the sealed TSV correctly use 12 fields.

## Correction history

`corrections/v2-overbroad/` correctly records the three-invocation chronology
but incorrectly retracts the truthful statement that all eight partial
unloaded run files were preserved.

`corrections/v3-accepted/` is authoritative for the correction scope. It:

- retains the retraction of the chain-wide no-retry claim;
- restores the true eight-file preservation statement;
- records that the retry was self-authorized despite the Principal Engineer's
  explicit no-retry instruction;
- retracts the statement that no simulation outcome was retried, because the
  unloaded side was invoked twice; and
- keeps the absent runner and traceback as a custody limitation rather than a
  contradiction of the eight-file statement.

No simulation, design edit, deck edit, raw edit, or waveform analysis occurred
while creating either correction package.

## Package boundary

`PUBLISH-MANIFEST.tsv` covers every payload except itself. Public copies
replace private PDK, tool, workspace, temporary, and session-record references
with portable labels. `PUBLIC-COPY-IDENTITIES.tsv` records every changed copy
against its original hash and size; the original sealed manifests remain as
historical identity records, while the publish manifest binds the actual
public bytes.

Private PDK files, the simulator executable, credentials, prompts,
transcripts, reasoning, absolute host paths, symlinks, and executable files are
excluded. The sealed parser and self-check are preserved as path-sanitized
historical copies and retain their original private-input hash bindings; they
are not represented as directly runnable against altered public text copies.
Their original and public identities are both recorded. The separate public
verifier binds the unchanged raw files and fact table with package-relative
paths. The factual crossing inventory is included without a causal or gate
interpretation.

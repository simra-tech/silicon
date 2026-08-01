# Stage-Two CML Normalized Replay V1

## Scope

This package is a controlled follow-on to
`custom-cml-div4-stage2-waveform-replay-v1`. It asks one narrow question:
when the loaded stage-one replay waveform is rescaled to the unloaded
differential peak-to-peak amplitude while retaining its loaded common mode and
native timestamp grid, does the stage-two ideal-drive replay reproduce the
unloaded output crossing count?

It does not. Over the closed 2-to-4 ns window, the unloaded, loaded, and
normalized replays have 5, 30, and 35 stage-two output-differential crossings,
respectively; all three have 10 input-differential crossings. Matching
differential peak-to-peak amplitude alone is therefore insufficient to
reproduce the unloaded crossing count under this ideal-source replay. This
observation does not identify a cause, establish improvement or degradation,
or prove direct interstage compatibility.

## Source construction

The retained unloaded and loaded source files each have 2,284 rows. Over the
closed 2-to-4 ns window their differential peak-to-peak amplitudes are:

- unloaded: `1.3101500928117433 V`;
- loaded: `1.1537113306058147 V`; and
- scale factor `K = unloaded / loaded = 1.1355961045505054`.

For each loaded row, the normalized source uses
`CM = (p+n)/2`, `D' = K*(p-n)`, `p' = CM+D'/2`, and `n' = CM-D'/2`.
The normalized time column is byte-identical to the loaded source time column.
Its 2-to-4 ns differential peak-to-peak amplitude is
`1.3101500928117433 V`, and the reconstructed common-mode error is exactly
zero in the stored decimal rows.

`source-deck/` contains the exact normalized source, portable deck, and frozen
Candidate V5 netlist. Model references use `$PDK_ROOT`. The public verifier
reconstructs the source from the previously published control files and
compares every normalized row byte for byte.

## Execution evidence

`runtime/` contains the deck, source, netlist, native stdout/stderr, and the
complete ngspice raw file. One ngspice 46 invocation returned zero and produced
SHA-256 `bc36f6cb1abb3646297b42483fdde1bdd9a1bd0d55877bd4622ac13b3a320b20`:
429 vectors by 2,011 points, finite stored doubles, strictly increasing time,
and a 0-to-4 ns span.

The execution package's outer command recursively pre-cleared its versioned
root before recording prior absence. No loss is asserted, but prior absence is
unproved. That custody limitation is retained in `corrections/CUSTODY.md` and
does not alter the raw bytes or their independently checked structure.

## Read-only waveform facts

`analysis/NORMALIZED-WAVEFORM-FACTS.tsv` contains every strict opposite-sign
crossing, the corresponding input/output common-mode interpolation, and four
native-sample statistics. A package-relative implementation,
`VERIFY-PUBLIC-NORMALIZED.py`, independently reproduces all 49 rows from the
published raw:

| Signal | Native samples | Crossings | Exact zeros | Min (V) | Max (V) | Peak-to-peak (V) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| input differential | 1,002 | 10 | 0 | -0.6527201182530706 | 0.6540131470287651 | 1.3067332652818358 |
| output differential | 1,002 | 35 | 0 | -0.612920518600971 | 0.6157705101546038 | 1.2286910287555748 |
| input common mode | 1,002 | — | — | 1.2879141750537229 | 1.5495658107946064 | 0.26165163574088357 |
| output common mode | 1,002 | — | — | 1.2982009815664295 | 1.4909063857950424 | 0.19270540422861293 |

The output crossings per input-defined interval are
`[0, 4, 3, 4, 3, 4, 3, 4, 3, 4, 3]`.

## Custody correction history

The original six-file analysis package claimed no retry. The retained creation
record instead contains three parser/self-check pipelines with failure counts
6, 4, and 0; the second and third attempts inventoried and removed their
task-owned drafts. A V2 correction recorded the chronology but hashed message
content rather than the separate command-bearing field. V3 repaired those
bindings, but its own final package followed a regenerated draft after a
recursive pre-clear. A mandated single V4 attempt then failed four wording
checks before directory creation and stopped without retry. No V4 directory
exists.

The complete correction chronology is preserved in `corrections/CUSTODY.md`.
Private orchestration records are intentionally excluded. The waveform table
is accepted here only because the public verifier reconstructs it directly
from the published raw; the correction packages are not used as a substitute
for that check.

## Package boundary

`PUBLISH-MANIFEST.tsv` hashes every payload except itself. The raw, source data,
netlist, stdout, stderr, and fact table are byte-identical snapshots. The two
deck copies replace private PDK paths with `$PDK_ROOT`; their original and
public identities are listed in `PUBLIC-COPY-IDENTITIES.tsv`.

No credentials, private PDK files, simulator binary, unrestricted logs, or
absolute host paths are included. The ideal filesource has zero source
impedance, so this package does not establish causality, oscillation,
compatibility, a specification result, signoff, foundry approval, or tape-out
readiness. The P1 gate remains running.

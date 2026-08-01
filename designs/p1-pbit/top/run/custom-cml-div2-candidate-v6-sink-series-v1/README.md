# Candidate V6 Sink-Series Matched Runtime

## Scope

This package preserves Candidate V6, its Candidate V5 control, one matched
native-ngspice runtime pair, the direct raw-data comparison, and the correction
history for the source and runtime reports.

Candidate V6 changes exactly four sink-collector branches. Each affected HBT
collector is moved to a local node and connected to its prior collector net by
one matched `rppd` resistor with `w=2.0u`, `l=1.0u`, `m=1`, and `b=0`. The
source diff contains four removed lines and eight added lines. No other netlist
line changes.

Engineering status: **NOT EVALUATED**. Both simulations completed and the raw
waveform coordinates are independently reproducible, but no applicable
reliability or circuit specification was supplied for these coordinates. This
package does not establish that Candidate V6 improves the design and makes no
signoff or tape-out-readiness claim.

## Source authority

The exact source identities are:

- Candidate V5: `689d4beedfce278f0c13cf0e79a25b87ba8a12d25b9459e51dfbfde041cd3db7`;
- Candidate V6: `174aea1f87d5e8e00eddd9937477ec01968b4f66ac77433e766d2349f5616e0a`;
- V5-to-V6 diff: `ea49605a4edc2b39f0ae1571ef4711e74c7701efc40951e722abce14f0130a46`.

The corrected source audit establishes that the geometry exceeds the exact
installed lower bounds `wmin=0.50 um` and `lmin=0.50 um`. It found no explicit
upper width or length bound. The installed `r3_cmc` source defines `rc` per
contact and includes both end resistances, giving a nominal two-end value of
`164.611167 ohm` for the chosen geometry. These are source and model facts, not
a reliability disposition.

The original Audit V1 is retained under `source/reserved/`. Its final sentence
incorrectly said the diff had four removed and four added lines. The immutable
correction and Audit V2 carry the verified four-removed/eight-added count.

## Matched runtime

The same retained full-rebuild control executable, SHA-256
`c865f1bf2ea99bc684b9e40342cfd6565f6bc995fb47c748474aceb5ef384045`,
was used once for each side. Diagnostic instrumentation is visible in stderr;
the executable is not described as non-instrumented.

The control completed in 1.877 seconds with rc 0. Its raw data region reproduced
the previously accepted SHA-256
`26c62c1942b552ae609f6eb57e9746ee30ad77b7a5c6e433c118ddd965de3de7`
before the experiment was invoked. The experiment then completed in 1.817
seconds with rc 0. There was no retry.

Direct parsing of the copied raw files gives:

- V5 control: 429 variables by 2,284 points, 7,838,688-byte binary payload;
- V6 experiment: 453 variables by 2,284 points, 8,277,216-byte binary payload;
- both payloads contain only finite doubles and have strictly increasing time
  from 0 to 4 ns;
- over 2 to 4 ns, `DIV2_P-DIV2_N` has 10 zero crossings on each side and
  inferred frequencies of 2.500004 GHz for V5 and 2.500003 GHz for V6.

The inferred frequencies are numerical waveform derivatives, not specification
values. Full 0-to-4 ns VCE, VBE, VCB, threshold-duration, and collector-node
coordinates are in `evidence/MATCHED-RUNTIME-V5-PUBLIC.tsv`. The four new branch
currents were not saved and are not inferred.

Each stderr has one native warning: ngspice could not find `spinit`. The retained
diagnostic stderr also has 68 control and 71 experiment lines containing NaN
diagnostic observations. Those observations are distinct from the final raw
payloads, whose stored doubles are all finite.

## Deck and reproduction boundary

The executed V5 and V6 decks had SHA-256 `46e7f223...` and `07189cb1...`.
Published copies replace the private PDK prefix with literal `$PDK_ROOT`; the
substitutions and both identities are recorded in
`PUBLIC-COPY-IDENTITIES.tsv`. Before running, replace `$PDK_ROOT` with an IHP
SG13G2 PDK installation that supplies the referenced model libraries and OSDI
files.

This is native ngspice evidence and is outside the shared backend-comparable
profile. The compiled executable and private PDK files are not published.

## Preserved corrections and package boundary

`evidence/FAILED-ATTEMPTS.tsv` preserves the fail-closed setup attempts, the
read-only parsing failure, the mislabeled-current analysis, the V4 report
defects, and the first V5 report-generation error. The successful ending does
not erase those attempts.

The package includes each binary raw with its deck, source netlist, stdout,
stderr, return code, and timing record. `PUBLISH-MANIFEST.tsv` covers every
published payload except itself. `evidence/ORIGINAL-RUN-MEMBERSHIP.log` records
the complete membership of the closed private run directories; model files
listed there are supplied by `$PDK_ROOT` rather than duplicated here.
Credentials, cookies, prompts, transcripts,
private reasoning, tool arguments, absolute host paths, symlinks, executable
files, and private PDK payloads are excluded.

# Direct CML Divide-by-Four Cascade Diagnostic V1

## Scope

This package preserves the frozen Candidate V5 CML divide-by-two netlist, a
two-instance direct-cascade deck, the complete one-invocation native-ngspice
runtime record, and the corrected read-only crossing evidence. The first
stage's differential outputs directly drive the second stage's clock inputs.
There is no external load, reset, initial condition, or nodeset.

Engineering status: **direct V5-to-V5 compatibility is not established**.
The simulation executed and produced structurally valid raw data, but the
second-stage differential waveform has substantially more zero crossings than
a clean divide-by-four waveform. This diagnostic does not establish a design
improvement, specification result, signoff, or tape-out readiness.

## Source and execution identity

The exact source SHA-256 is
`689d4beedfce278f0c13cf0e79a25b87ba8a12d25b9459e51dfbfde041cd3db7`.
It is a byte-identical copy of retained Candidate V5. The executed private deck
SHA-256 is
`97a52bb7757c5b36160a28377cf50bede0197656b3a395a411faec19eea5532c`.
The public deck changes only the private PDK prefix to literal `$PDK_ROOT`; its
identity is recorded in `PUBLIC-COPY-IDENTITIES.tsv`.

Native ngspice 46 was invoked exactly once. It returned rc 0 after 7.748
seconds, without a retry or timeout. The executable identity, timestamps,
arguments, and source identities are retained in the runtime logs. Public
copies replace the private executable and workspace prefixes with
`$TOOLS_ROOT` and `.` respectively. Before reproducing the run, replace
`$PDK_ROOT` and `$TOOLS_ROOT` with installations providing the referenced IHP
SG13G2 libraries, OSDI models, and ngspice 46.

The runtime streams are retained verbatim. Stdout contains 112 OSDI resistor
voltage-limit warnings. Stderr records that dynamic gmin stepping failed, true
gmin stepping then completed, and the temperature-limiting function reported a
NaN warning with a heat-sink recommendation. Those warnings and the stage-two
waveform prevent rc 0 from being read as an engineering pass.

The raw header's `Sat Aug 1 04:06:18 2026` timestamp is ngspice's local time.
The external invocation record is UTC and reports 02:06:17 through 02:06:25Z;
both are preserved rather than rewritten.

## Raw-data review

The raw SHA-256 is
`c0aed217cc55e8818fdaeeb09c68bcc83ea285c618a91952b08826f9a4adf925`.
Independent parsing of the copied file confirms 849 vectors by 2,284 points,
an exact 15,512,928-byte binary payload, finite stored doubles, and strictly
increasing time from 0 to 4 ns.

Over the closed 2-to-4 ns review window:

- the 5 GHz input clock has 20 differential zero crossings;
- stage one has 10 crossings and a 400.004 ps mean same-direction period,
  consistent with divide-by-two behavior;
- stage two has 27 crossings, a differential range of -0.559743 to +0.560222
  V, and a common-mode range of 1.330887 to 1.477304 V;
- all 26 stage-two sign intervals reach at least 0.3 V absolute differential
  amplitude, so the extra reversals are not removed by a +/-0.3 V amplitude
  screen.

A clean 5 GHz divide-by-four output is 1.25 GHz with an 800 ps period and 400
ps differential zero-crossing cadence. A closed 2 ns window contains
generically five crossings and at most six only when both endpoints coincide
with crossings. Therefore the observed 27 crossings imply **provisionally at
least 21 excess crossings**. No exact ideal phase is assigned.

## Read-only interstage comparison

The accepted read-only audit under
`evidence/interstage-loading-audit-v1/` compares this direct run against the
previously published single-stage Candidate V5 raw. An independent parser
reproduced all 87 crossing-table rows and all 30 stage-two device-coordinate
rows from the two published raws.

The single-stage and direct-run clocks are identical. Stage one retains ten
crossings and a near-400 ps same-direction period when stage two is connected,
while its differential peak-to-peak range changes from 1.310149 V to 1.153711
V and its mean absolute bracketing-sample crossing slope changes from
1.391744e11 V/s to 9.123610e9 V/s. These are confirmed observational deltas.
They do **not** establish interface loading as the cause: the single-stage raw
was produced by the retained probe-instrumented executable, while the direct
run used a different native-ngspice executable, in addition to the circuit
difference. A matched control/experiment run is required for causal
attribution.

The audit also records min, max, mean, and actual sample coordinates for six
saved stage-two clock-terminal voltages and four saved clock-device currents.
It infers neither capacitance nor a failing device or mechanism.

## Correction history

The V1 and V2 read-only evidence packages remain byte-for-byte under
`evidence/reserved/`. V1 used the divide-by-two count of ten as its clean
divide-by-four baseline. V2 corrected the baseline but labeled Hz-valued
numbers as GHz and left its correction outside the manifest. The manifest-
closed V3 package under `evidence/accepted-v3/` supersedes both reports while
retaining their hashes and the byte-identical 57-row crossing table. See
`evidence/RECORD-HISTORY.tsv` for the disposition of each record.

## Package boundary

The binary raw is published with its deck, source, stdout, stderr, invocation
record, pre/post hashes, raw manifest, accepted crossing evidence, and the
independently reproduced read-only interstage comparison.
`PUBLISH-MANIFEST.tsv` covers every payload except itself. Private PDK files,
the simulator executable, credentials, prompts, transcripts, reasoning,
absolute host paths, symlinks, and executable files are excluded.

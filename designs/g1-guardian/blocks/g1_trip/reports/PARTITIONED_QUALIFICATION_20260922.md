# Bounded partition qualification

All results are simulated. Existing failed and interrupted attempts remain
preserved; successful recoveries are not additional independent samples.

## Original joint baseline20 completed

Seeds71001–71020 now have560numerically completed selected probes, with all27
observed parameters exactly frozen within each physical sample. Eight original
failed/interrupted attempts remain preserved behind explicit validated recovery
references. There are no remaining selected-probe numerical incompletions.

Electrical screening is **failed**:11of20samples fail guard checks, all11with
in-range failures (30failed in-range guard probes total). Ten samples fail the
frozen±0.5mV calibration-point residual checks:10failed hot probes and5failed
cold probes. Hard code254 correction clips in16of20samples; soft correction
does not clip. The nominal50mV hard full band remains **not qualified** because
its55mV upper guard exceeds the specified0–50mV input range. Numerical completion
does not turn these electrical failures into passes or demonstrate yield.

[Completed baseline audit](resume-server-20260922/joint-original20-completed-audit.json)
retains every sample, observed decision, recovery and range classification.
Selected probe time totaled23.792core-hours; mean152.951s/probe projects
356.886core-hours for300×28probes before failures or changed-circuit overhead.
The source remains the original baseline; candidate comparisons are separate.

## Comparator original20

Seeds62001–62020 completed all60temperature cases at25/−40/125°C, with the same
32observed parameters frozen within each physical sample. The qualified
individual-temperature partition reused22completed old cases and ran38missing
cases. Original62007/62008multi-temperature timeouts remain recorded.

Every case has401sampled staircase decisions and a finite ambiguity interval.
All60have local nonmonotonic decisions; **no unique offset is claimed**.
Maximum ambiguity width is0.5mV at the comparator. There is no allocated
standalone offset/ambiguity acceptance limit. Ideal symmetric1kΩ/1pF sources
are not the actual25kΩ conditioner/DAC interface or calibrated system yield.

[Full analysis](resume-server-20260922/comparator20-ambiguity-analysis.json)
includes every case, temperature-change interval envelopes and original-case
references. Median newly simulated three-temperature sample runtime is247.0s;
the forecast for100samples of this exact scope is6.965core-hours, not a deadline
or guarantee for a changed circuit.

## Comparator100

The subsequent comparator100 milestone covers seeds62001–62100: all100samples
and300temperature cases completed numerically, with0frozen32parameter failures.
All300cases have finite ambiguity intervals and locally nonmonotonic decisions;
maximum width remains0.5mV. No unique offset or system-yield result is inferred.
[Complete100 analysis](resume-server-20260922/comparator100-ambiguity-analysis.json)
retains the original20 and all80new samples. Eight parent summaries and240new
leaf summaries/provenance/hash inventories are exported alongside it.

The subsequent [300-sample completion](COMPARATOR300_COMPLETION_20260922.md)
covers seeds62001–62300 and900numerical cases, with all900locally nonmonotonic
finite ambiguity intervals. Exact32parameter/source/runtime audit passed;
no unique offset, loaded-chain yield or physical adoption is inferred.

## Actual-BGR DAC full256 nominal pilot results

`dac-chunks256-tight-pilot-20260922-b`, seed51001 at25°C, completed32independent
8code chunks with31observed parameters and source/model/runtime identities
exact across every chunk. Both full switch trees, actualBGR/SENSE reference
buffer and reset-held comparators are included; this is a DC transfer test.

| Metric | Soft | Hard |
|---|---:|---:|
| Numerical/all256code completion | passed | passed |
| Monotonicity | passed | passed |
| Minimum step |1.859mV|1.865mV|
| Minimum endpoint DNL |−0.02295LSB|−0.01858LSB|
| Maximum absolute endpoint INL |0.09883LSB|0.09342LSB|

INL acceptance is **not applicable**: no standalone limit has been allocated.
Temperature sweeps, exact return-temperature transfer, dynamic settling,
statistical all-code yield and candidate physical implementation are **not run**
by this pilot. Numerical leaf time totaled2615.42core-seconds; three workers
ran independent leaves, never multithreaded simulator analyses.

The subsequent125°C eight-code anchor trial is **failed qualification**:
chunks0–7 and120–127 reached120s watchdogs after7and5saved rows respectively,
without final31parameter fingerprints. Chunk248–255 completed110.22s and its
code255OP matched the archived125°C phase exactly. The completed code0OP also
matched, but partial output is not a passed chunk. All three sources/circuits
matched the reference. The [strict failed comparison](resume-server-20260922/dac-hot-partition-comparison-20260922-a.json)
and portable exports retain both watchdogs; smaller four-code diagnostics are
separate attempts, not retries relabeled as successes. Fullhot256transfer and
fulltemperature-return transfer were **not run** by those selected anchors.

Fresh four-code125°C diagnostics0–3 and124–127 completed66.45/88.73s.
Together with the completed248–255chunk, the
[explicit-phase comparison](resume-server-20260922/dac-hot-partition-comparison-20260922-c.json)
**passed** source/circuit/model/runtime equality, exact0/127/255OP values and
all31sampled parameters. Every candidate's final parameter vector equals the
reference's25/125/25vectors before and after the hot phase. The chunk runner
records parameters after its code list, not after each individual code; no
stronger per-code instrumentation claim is made. This qualifies selected hot
anchors and bounded chunk granularity, not fullhot256transfer or yield.

The subsequent fullhot256 attempt `dac-chunks256-hot-tight-pilot-20260922-a`
is **failed/incomplete**:43complete four-code leaves cover0–171, and c172 hit
the unchanged120s watchdog after saving172–174, with no175row or final31parameter
vector. Codes176–255 were **not run** in that attempt. Every completed/failed
leaf is preserved and compactly exported; partial rows are excluded from
accepted coverage.

Fresh two-code diagnostics172–173 and174–175 then passed numerical completion,
exact source/circuit/model/tool identity and31end parameters. Existing125°C
anchors0/127/255 remained exact; saved172–174 printed values match the failed
attempt, while175has no original saved row. The
[two-code qualification](resume-server-20260922/dac-hot-two-qualification-20260922-a.json)
does not repair or alias the failed parent. A fresh bounded172–255 continuation
was launched separately; fullhot256completion and temperature-return256transfer
are not established by this checkpoint.

The first nominal chunk trials completed numerically but failed a strict
literal-deck comparison because an identical repeated tight-options line was
missing. That failure remains in
`sim/qualification/dac-partition-qualification-20260922-b.json`.
Fresh `dac-partition-tight-c{0,120,248}-20260922-a` trials preserved the literal
circuit, all31sampled parameters and exact overlapping0/127/255printedOP values;
`dac-partition-qualification-tight-20260922-c.json` passed. Those checks qualified
the full256partition; they did not imply hot-temperature or dynamic equivalence.

## Portable evidence

Each completed campaign and new leaf has a compact export under
`reports/resume-server-20260922/`: summary, exact command/tool/PDK/model/source
provenance, archived runner and full artifact hash/size inventory. Bulk waves
are retained separately by repository-relative logical run IDs. Newly generated
comparator waves use verified lossless gzip receipts; immutable old evidence
was not compressed or removed.

Built against ngspice46, IHP SG13G2 commit
`84374023ee8b4b126bebbba67fcbada0a9c0ff0b`, pinned image manifest
`sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0`.
Version output, full model hashes and exact settings are in each provenance.

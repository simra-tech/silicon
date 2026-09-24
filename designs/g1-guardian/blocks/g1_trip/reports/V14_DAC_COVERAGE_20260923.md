# V14 DAC coverage and final-source preparation

## Continuation method checks

The subsequent room/hot one-OP continuation controls **failed** their strict
static-overlap/returned-code equality checks, despite exact full11512/27
parameters. Maximum observed voltage differences were28.764pV at room and
16.723pV at hot. Adding a second OP per code in a distinct controlled fixture
also **failed** exact equality; the earlier failures were not overwritten.
Every continued OP re-entered dynamic gmin stepping. These runs demonstrate
neither genuine warm-start reuse nor a qualified speed improvement.

Evidence: [one-OP independent audit](../sim/qualification/dac586-chunk-qualification-20260923-a.json),
[two-OP room audit](../sim/qualification/dac586-twoop-room-audit-20260923-b.json),
and [two-OP hot audit](../sim/qualification/dac586-twoop-hot-audit-20260923-b.json).

A distinct source-controlled behavioral-bit/DC method is now under bounded
qualification, not all-code acceptance. Its eleven static-source controls and
three two-point DC controls retain all analog devices/models/options, the full
parameter inventory and actual16-bit voltage observations. The prospective
100nV/1nA comparison is only a finite-anchor method-consistency screen; exact
comparison failures remain separate. It is not a universal solver-error bound
or an allocated leakage limit. Any interval DNL calculation remains conditional
on separately justified error bounds. All256/statistical expansion, isolated
leakage, dynamic major-carry and settling acceptance remain **not run**.
The [frozen bounded execution](../sim/qualification/dac586-dc-execution-20260923-a.json)
does not authorize those later scopes.

## Subsequent static-control milestone

The earlier preparation-only sections below are retained as prospective history.
All eleven final-source static controls subsequently **passed** independent
reanalysis in
[`dac586-static-qualification-20260923-a.json`](../sim/qualification/dac586-static-qualification-20260923-a.json)
(SHA256 `283fbf71a2a7d3941e8d2de9bdbbad76fd09cda8e5eee07f074670499b85dc6b`).
Every phase retained all11512 parameters and27 anchors exactly. Original
voltage-output parity, full12-column repeat and25→125→−40→25 return were exact.
The ten single-temperature controls took32.393–49.113s each; the return took
166.576s. Total measured single-thread wall time was587.571s, not a process-CPU
measurement or an all-code forecast.

Two bounded same-instance127→128→127 room/hot continuation controls are next;
their strict static overlaps, full parameter vector and measured warm cost must
qualify before any larger chunk. All256 final-source transfer, statistical
transfer, isolated DAC leakage and dynamic major-carry settling remain **not
run**. Initial missing-mount preflight failure is retained separately; no SPICE
process ran in that failed attempt.

All electrical numbers below are simulated. No new DAC simulation was run for
this review. Completed historical all-code evidence is retained, not repeated.

| Required scope | Completed evidence | Remaining scope |
| --- | --- | --- |
| Full switch-tree all256 nominal | Seed51001,25C, both DACs monotonic; minimum DNL −0.02295/−0.01858LSB | Final586 reference/gm4 source and independent all-code samples: **not run** |
| Full256 hot | Same seed125C, exact explicit256-code coverage; minimum DNL −0.023735/−0.018750LSB | Final-source hot coverage and independent samples: **not run** |
| Frozen temperature realization | Historical31 sampled end parameters and selected0/127/255 anchors | Full256 temperature-return transfer and complete final-source parameter instrumentation: **not run** |
| Hot leakage | Hot full-switch transfer includes modeled leakage effects | Isolated DAC leakage ledger, allocated leakage limit and causal decomposition: **not run**; total rail current is not DAC leakage |
| Major carries | Historical actual-RTL128↔127 pilot observed all8 physical bits switching | Final-source, remaining carries, near-threshold/adverse conditions and skew coverage: **not run** |
| Settling | Historical interface requires at least1us after code update | Existing HYS pilot failed this interval at100ns/0ns; no shorter bound adopted |
| Statistical transfer | One physical seed at nominal/hot | New-harness20 smoke,100 screen and subsequent required critical coverage: **not run** |

The historical all-code runner uses BGR source
`944aaf94b9a005718abd0ebd92956acc99e8cb7a23ec8556d406736f4e8ef6f9`
and the original SENSE source, KLU, and a hard-comparator clock connection
rewired to hold both comparators reset. It records31 selected parameter values
after each chunk. Those results are not mislabeled as final586/gm4 or complete
11512-parameter evidence. The ongoing final-source joint calibrated-chain
population tests selected codes, not an all-code statistical DAC transfer.

See [historical nominal transfer](PARTITIONED_QUALIFICATION_20260922.md),
[hot256 completion](DAC_HOT256_COMPLETION_20260922.md), and the
[actual-RTL carry pilot](../sim/HYS_FEEDBACK_PILOT_20260922.md). The latter used
the historical reference/SENSE sources, not the current candidate. HYS interface
remediation is separate; this review changes neither RTL nor the interface.

## Frozen acceptance versus unallocated quantities

Monotonicity and DNL greater than−1LSB remain the transfer requirements.
Endpoint INL is reported, but a standalone INL limit has not been allocated.
A standalone leakage-current limit also has not been allocated. Neither an
invented limit nor nominal0.002LSB is used to turn mismatch characterization
into acceptance. The existing1us post-code-change validity requirement remains
unchanged; a DC result cannot establish transient settling or clocked immunity.

## Prepared final-source controls — not run

[Preparer](../sim/prepare_dac586_static_controls.py) and
[six source-transform tests](../sim/test_dac586_static_controls.py) prepare
eleven controls under logical IDs `dac586-static-controls-20260923-a-*`:

- Output-only existing135/151 code fixture and its repeat.
- Equal soft/hard codes0,127,128,255, each at25C and125C.
- One initial seed/reset followed by25→125→−40→25 at135/151.

These retain the qualified seed73001 realization, all3500 original devices,
11512 full parameters and27 legacy anchors, actual final586 reference, gm4
SENSE and unchanged TRIP sources. Every phase has full BEFORE/AFTER queries.
The only circuit stimulus changes are declared static bit-source values;
temperature is selected using the already-qualified control commands. The
original clock, comparator connections, models, solver, tolerances, body nets
and loading remain unchanged. At OP the original clock is low; this is not a
claim that both comparator cores are held reset.

Two appended supply observations retain the original nine physical voltage
columns first. The scale header is bound to the original OP output, not assumed
to be physical time. The first output-only control must reproduce all original
voltage values and decoded column bytes; the repeat and returned-temperature
outputs have separate exact-equality gates. Total `i(vdda)` and `i(vdd)` include
other blocks: neither is isolated DAC leakage, a per-DAC supply allocation or a
physical-current envelope. No model-current mapping is guessed.

The packet is preparation only. The [execution runner](../sim/run_dac586_static_control.py)
and [post-execution auditor](../sim/audit_dac586_static_controls.py) are implemented;
eleven source/runtime controls passed. Runtime qualification and dynamic
fixtures are **not run**. Output comparisons distinguish numeric equality from
decoded-column token-byte equality; added-column padding is not claimed raw-file
identity. The frozen execution manifest is
`sim/qualification/dac586-static-execution-20260923-a.json`.
No broad population or automatic scheduling follows from these files. Any
first execution needs an available CPU lease, fresh resource/growth gate and
bound source/runtime/input verification. Original model-level physical
limitations remain; no final physical PEX qualification is claimed.

## Throughput before expansion

The exact existing final-source enabled OP control completed its two OP
commands/full inventory in59.778s; the four-temperature return took205.963s.
Applying those observed costs only as a planning estimate gives about804s
(0.223core-hours) for ten single-temperature controls plus one return.
Prospective per-control caps are300s and1200s respectively,4200s in aggregate.
Output allocation is0.02GiB per single-phase control and0.08GiB for return.
Actual new-control throughput has **not run**.

A naive fresh-process, two-OP-per-code implementation would cost roughly170
core-hours for20samples×256codes×2temperatures at the existing room OP rate;
hot behavior can be slower. Historical nominal256 cost2615.42core-seconds, but
that different source/solver/chunk harness is not a final-source forecast.
Before statistical expansion, bounded chunking must be qualified with literal
source/deck/inventory equality and overlapping code/temperature anchors. No
silent carry-history or reset-order change may be hidden as a scheduling
optimization. All original failed watchdogs remain in the historical record.

One preparer invocation failed before allocation because a relative script
path was passed to an absolute-path provenance comparison. The path binding
was corrected before creating this packet; no simulator or evidence run was
started by the failed invocation. Six tests then passed, including all256 bit
transforms, exact restoration, output-only inverse and invalid-source rejection.

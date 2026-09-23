# Slow-corner operational recovery evidence

Four simulated leaves completed under explicitly extended external wall-clock
watchdogs. Their original 1200-second timeout failures remain unchanged. This
is a numerical-continuation milestone, not an electrical population pass or
source adoption.

| Original seed/leaf | Original result | Recovery watchdog | Recovery wall time | Recovery leaf result |
| --- | --- | ---: | ---: | --- |
| 77105/p25 | Failed: timeout | 2400 s | 1437.096 s | Passed |
| 77116/p41 | Failed: timeout | 2400 s | 1663.477 s | Passed |
| 77117/p25 | Failed: timeout | 7200 s | 4440.595 s | Passed |
| 77120/p25 | Failed: timeout | 7200 s | 4773.726 s | Passed |

Each recovery retained the exact original source, seed, physical draw, codes,
stimulus, reset, SPARSE solver, numerical options, 0.2 ns transient settings,
1.02 us endpoint and electrical criteria. The deck inverse check permits only
the waveform destination change. The other operational changes were the
external watchdog and checksum-archived local merged-log storage. No solver
speedup is inferred from these runs.

Independent audits passed all 11,512 before/after parameter comparisons, 27
legacy anchors, complete 19-column waveforms, endpoint and original leaf
decisions. Original-to-recovery full-wave comparison is **not run**: the
original timeouts exported no complete waveform. Hardware measurement is
**not applicable** to this simulated milestone.

The original first20 report remains 14 full passes and 6 failures, with 16
numerically complete samples and 4 numerical failures. Full revalidation of
all 20 original records and the four new recovery audits passed. An explicit
copy with exactly these four recovered leaves satisfies the unchanged
numerical continuation predicate; the original predicate remains failed.
Separate electrical failures and the fixed sample denominator are retained.

## Built against and reproduction

The [machine-readable inventory](joint586-slow-operational-recovery-milestone-20260923.json)
records full hashes of the runtime image, public model libraries, source
netlists, original and recovery decks, logs, waves, audits and projection.

| Component | Pinned identity |
| --- | --- |
| IHP SG13G2 open PDK | `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` |
| Simulator | ngspice-46; version text and image identity in inventory |
| Solver | SPARSE; unchanged original options |
| PSP OSDI | `6538578a272040e70cf4542884e86d1aecd3c6936eee9e43564db49d2d05d5ab` |

The image manifest digest begins `5fd78498`; its config digest begins
`ddeb6957`. They identify the same previously inspected image, not two
runtimes. The inventory labels both namespaces explicitly and binds the
existing inspection receipt. Legacy run provenance calls the manifest digest
`image_id_observed_by_host`; those original records remain unchanged.

In a fresh verification workspace, restore the retained input tree to the
inventory's relative logical paths and verify its hashes before execution.
The exact simulator arguments and working directory are recorded separately
for each case. For example, from `designs/g1-guardian/blocks/g1_trip/sim`:

```sh
ngspice -b qualification/joint586-slow-s77105-p25-watchdog2400-20260923-a/probe.cir
```

Reproduction also requires the recorded external watchdog and qualified
merged-log spool policy; the command alone does not impose them. Never run
over retained evidence. Re-execution for this documentation is **not run**.
The inventory identifies existing retained artifacts without duplicating
waveforms or claiming their payloads are included in this compact report.

The numerical projection SHA-256 is
`eda17023626d7b5449d6f6c50eb60b135af61052f335aff73b263d6b5102477b`;
the unchanged original first20 audit SHA-256 is
`79def175ca177885f87c63c7ae4908ee8b7577d631df6f85eb6c400a4bf77951`.

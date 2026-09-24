# Repository handoff — 24 September 2026

This is a repository-cleanup record, not circuit qualification or tapeout approval.
Engineering was paused at the owner's request. Existing simulation engines may
finish; that does not authorize new campaigns or change acceptance criteria.

## Contents and retention

Sources, layouts, decks, compact reports, and source-control tests are retained
in Git. `handoff-local-retention-20260924.json` lists exact paths, sizes, hashes,
and reasons for newly excluded local artifacts. Those files are preserved, not
deleted. Exclusions use exact paths rather than ignoring future design sources.

Generated JSON dumps larger than 1 MiB, waveform arrays, local-build symlinks,
and machine-bound diagnostic scripts remain local. Some saved reports refer to
these retained artifacts: a fresh clone alone does not contain all raw evidence.
The next engineer must obtain the retained evidence before independently
reproducing or auditing those results. No missing evidence is deemed passed.

An unadopted R0.95 candidate extraction had overwritten the root-level oscillator
netlist. Its exact bytes were privately preserved, and that one working file
was restored to the committed baseline. The candidate's separate source and
reports remain; this cleanup does not adopt it or erase its evidence.

## Cleanup checks

| Check | Status | Scope |
|---|---|---|
| Retained-file hash inventory | passed | Exact local artifacts, no deletion. |
| Public/private separation review | passed | Changed reports reviewed; machine-bound files excluded; credential-marker scan found no matches in the proposed deliverables. This is not a general security certification. |
| Source-control unit tests | passed | 18 controls for analog-pair replacement and hard/SENSE terminal lineage in the pinned EDA container. |
| Retained Python syntax | passed | All 669 retained Python files parsed in the pinned container. |
| Whitespace check on Python/Markdown/ignore changes | failed, cosmetic | 80 extra blank lines at end of existing source snapshots. Original bytes are retained for provenance; no whitespace or scientific acceptance waiver is implied. |
| Host-only execution of those tests | not run | Host Python lacks KLayout; the container execution above passed. |
| New electrical or physical circuit qualification | not run | Git cleanup did not launch circuit simulations or signoff campaigns. |
| Silicon measurements | not applicable | Repository-only handoff; no physical measurements performed. |

Test command from repository root:

```sh
G1_CPUSET=2 G1_CPUS=1 G1_WORKDIR=designs/g1-guardian/review/audits \
  flow/run.sh timeout 90s python3 -B -m unittest \
  test_replace_analog_pair test_hard_only_terminal_lineage test_sense_terminal_lineage
```

The pinned image is `ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2`;
the IHP PDK revision is `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`.
The full engineering plan remains incomplete. Historical failed and incomplete
checks in committed reports are retained; local cleanup is not a new pass claim.

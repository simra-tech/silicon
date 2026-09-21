# Core LVS evidence recovered 2026-09-20

Status: **passed** for the core-only assembly comparison, 52 circuit pairs
matched, zero unmatched pairs. This is recovery of the completed 2026-09-19
run, not a new LVS execution.

- `run_core_lvs.log`, `g1_core.log` and `lvs_run_2026_09_19_15_41_01.log`
  record the passing run against the refreshed chip CDL.
- `xref.txt` was regenerated from that run's saved LVS database using
  `flow/lvs/xref_summary.py` and the pinned KLayout container.
- `lvs_run_2026_09_19_15_20_44.log` is the preserved **failed, superseded**
  attempt against stale CDL, described in INTEGRATION.md. It is not the
  current comparison result.
- The final assembly GDS SHA-256 was checked against `../final_gds.sha256`
  during recovery and matched.

Recovery command, from repository root (saved database is a build artifact):

```
flow/run.sh klayout -b -rd db=/work/build/scratch/corelvs/lvs/g1_core.lvsdb -r /work/designs/g1-guardian/blocks/g1_padring/flow/lvs/xref_summary.py
```

For a fresh comparison, use `flow/lvs/run_core_lvs.sh` as documented in
INTEGRATION.md, with the CDL generated from the same assembly run.
IO cells, bondpads and ring rails are excluded: full-chip LVS remains failed.

# R1 blocks — common rules for every track (P2, started 2026-10-20)

- One directory per block: `r1_<name>/` with `README.md` (what it is, state, status table with passed / failed /
  not run, built-against), `schematic/` (xschem `.sch` or generator), `rtl/` for digital, `sim/` (decks, run
  scripts, `results/` summaries, one `run.json` per run: command, tool versions, PDK commit, inputs, question, result,
  disposition), `layout/`, `reports/`.
- Every tool runs through `flow/run.sh` with an explicit `G1_CPUSET` (3–4 CPUs per track; check `uptime` first).
  Raw waveforms and large logs go to the bulk results root (`G1_RESULTS_ROOT`), referenced from `run.json` by run id,
  never by absolute path in tracked files. Nothing that is evidence lives only under `/tmp`.
- Failed and abandoned runs stay in the record, labelled. A check that did not run is written "not run".
- Reuse G1 blocks under `designs/g1-guardian/blocks/` as sources where the README says so; copy, do not edit G1.
- Do not commit; the coordinator commits from explicit file lists. Do not write outside your block directory except
  to append a dated row to `../PLAN.md` §5 when you reach a milestone.
- Never delete outside your block directory. `rm -rf` only on an absolute path inside your block's `sim/runs/` or the
  results root; print the path first. (Added 2026-10-20 after an agent deleted the G1 working copy with a wrong
  relative path; tracked files were restored from git, untracked local caches were lost.)
- Public repository: block design facts only. No market, pricing, customer or partner material.

| Track | Block(s) | CPU set | Model |
| --- | --- | --- | --- |
| T1 | `r1_osc` | 100–102 | Opus |
| T2 | `r1_adc` | 103–105 | Opus |
| T3 | `r1_afe` | 106–108 | Opus |
| T4 | `r1_isense`, `r1_safe` | 109–111 | Opus |
| T5 | `r1_ctrl` (`r1_pos`, `r1_bus`, `r1_gate` logic, `r1_safe` FSM, registers) | 112–115 | Opus |
| T6 | `r1_padring` | 116–119 | Sonnet |

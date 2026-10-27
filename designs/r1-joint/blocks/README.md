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
- Every block with a feedback loop (amplifier, CMFB, auto-zero servo, regulator, bandgap, oscillator amplitude control) records loop gain and phase margin at the five process corners and the two mixed supply/temperature corners (ssx, ffx) before it is called passed. Transient evidence alone is not enough (2026-10-21, after r1_afe revision B and r1_isense revision 1 were recorded passed with 13–50° margins). Amendment 2026-10-28 (after r1_isense layout c and r1_afe layout E5): a loop row whose validity flag fails because the extracted supply wiring forms a second loop is not "passed" and not "failed"; it is closed only by the supply-network method: the DC loop gain through the supply path (Tian probe inside the vss/vdd segment, or the voltage-only cross-check) ≤ −20 dB at tt, ss and ff, plus a step transient with at most one overshoot, with the supply network drawn as part of the circuit (star returns or straps), as `r1_isense/README.md` "Layout (revision c)" records it. Overshoot count (2026-10-28, after r1_afe layout E6): a step-edge feedthrough spike shorter than the loop time constant is not an overshoot; only loop-response peaks count, and the record shows the waveform with the two marked.
- Block decks use the real source and load of the neighbour block once it exists (its netlist or a fitted model), never an ideal source (2026-10-21, after the ADC reference buffer loaded the bandgap unseen).
- Runners exit non-zero on a failed job and never resubmit or skip silently.

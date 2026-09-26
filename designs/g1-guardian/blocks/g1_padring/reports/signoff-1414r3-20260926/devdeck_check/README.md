# Second opinion: IHP dev-branch DRC deck on r3 (2026-09-26)

This is a check only. The toolchain of record stays the pinned PDK `84374023…` (see `../README.md`).

**Input.** `layout/g1_chip_top_1414_r3.gds`, `7d07a7841a531f51e08b0c90e76fe603889cd2ef29905e309e63f09742e688f2`,
top cell `g1_chip_top`.

**Deck.** IHP-Open-PDK `origin/dev` at `4fd47c5e362914a100eabb2a651b0e3ab8981c25` (2026-09-23), with
`ihp-sg13g2/libs.tech/klayout` extracted by `git archive` to `${BULK}/devdeck-drc-r3-20260926/devpdk/`.
- Changes against `84374023` in the DRC decks: `layers_def.drc` (new `recog_momf` 99/40) and
  `feol/6_7_schottkydiode.drc` (contbar derivation).
- Changes in the tech JSON: MOS-cap parameters added.

**How it ran.** The dev `run_drc.py` ran in the pinned container (KLayout 0.30.9), with the same options as
the r3 sign-off. Maximal used [`run_maximal_dev.py`](run_maximal_dev.py): `flow/signoff/1414/run_maximal.py`
with the deck path pointed at the dev tree. CPUs 64-71.

**Failed first attempt (kept).** main, density, antenna and precheck stopped at start-up because the dev
`run_drc.py` needs the repository's `versions.txt`. That file was then taken from the same commit, and the
four checks were re-run. Attempt 1 is in `${BULK}/devdeck-drc-r3-20260926/attempt1_versions_txt_missing/`.

| Check | Dev deck: rules / markers | Wall | Pinned deck (`../`): rules / markers | Difference |
|---|---|---|---|---|
| Main (`--no_density --disable_extra_rules`) | 561 / **0** | 413 s | 561 / 0 | none |
| Maximal (`sg13g2_maximal`) | 272 / **0** | 835 s | 272 / 0 | none |
| Density | 7 / **0** | 54 s | 7 / 0 | none |
| Antenna | 31 / **0** | 181 s | 31 / 0 | none |
| Precheck (`--precheck_drc --disable_extra_rules`) | 455 / **0** | 364 s | 455 / 0 | none |

- Every rule reports 0 markers in every deck. The rule catalogues (category names) of the dev and pinned
  reports are identical.
- All five runs exited 0.
- Reports and run logs are copied here (paths → `${BULK}`/`${REPO}`).
- Not run with the dev PDK: LVS on r3.

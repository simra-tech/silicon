# Minimal native CMIM reproduction of the R100 PEX failures

The pinned 7 × 7 µm native `cap_cmim` coupon isolates a tool-interface failure
from the R100 macro geometry. Its GDS SHA-256 is
`546c3e33d3894fb4c0d54c623a0cd2ac261cbf074a44d210240921c86194fd20`;
the two-terminal CDL SHA-256 is
`bcc32a78962430e46e7269518c645681c3233e24337e87142e714c7fe85aa974`.
It is the existing native PCell method coupon, not a redrawn or simplified
electrical model. `probe_coupon.py` asserts those inputs, KLayout 0.30.9,
KLayout-PEX 0.3.12, the installed IHP SG13G2 commit
`84374023ee8b4b126bebbba67fcbada0a9c0ff0b`, and the technology JSON
SHA-256 `6ece2ac73930696f77b257d14fcf9d29d9e02451e7df99c72239746c18369a92`.

Both one-CPU, 120 s bounded stock KPEX/2.5D runs used full-device mode
(`--blackbox false`), unchanged coupon/PDK and fresh resource gates. Strict
two-pin LVS matched and the extraction context had no unnamed layers.

| Mode | Observed failure | Relation to R100 macro |
|---|---|---|
| R | Before numerical resistance extraction, the pinned R technology preparation warned that `cmim_top` and `metal5_cap` have unhandled `PURPOSE_MIM_CAP`; device bottom layer was not found, then `KeyError(29)`. | The macro R request independently has a dangling MIM via bottom-conductor reference (via 29 → conductor 27, absent from its conductor table) and stops at `KeyError(27)`. The coupon's different ID is not assumed to name the same object. |
| RC | After LVS, overlap extraction warned `top=<TODO>`, then sidewall/fringe extraction stopped at `KeyError('<TODO>')`, line 380. | The macro full RC run stops in the same extractor and key, line 383. |

The R coupon result is `sense-rz100-minimim-r-20260923-r2/summary.json` in the
simulation bulk root; RC is `sense-rz100-minimim-rc-20260923-r1/summary.json`.
The first R launch stopped before extraction because validation had already
created its output directory; that host-wrapper failure is retained separately.
Both subsequent runs recorded `inputs_unchanged=true`. The probe initially
captured engine failures as data and returned process code zero; its current
source now exits nonzero on a failed extraction. The saved summaries, not the
old wrapper exit code, are the disposition.

These minimal reproductions show that an otherwise LVS-matched native CMIM
alone reaches both KPEX failures. The pinned technology has native stack
geometry for `metal5_cap` and `cmim_top` (including the intervening 6.7-k,
0.04-µm dielectric), but its process-parasitics tables have **no direct**
sheet resistance, substrate-capacitance, overlap, sidewall or side-overlap
entries for either computed layer. The canonical Metal5 sheet value is present;
that alone does not define the `cmim_top` conductor or the intrinsic/extrinsic
ownership boundary. `audit_missing_mim_fields.py` verifies the absent entries
against pinned technology/model hashes and records the result in
`sense-rz100-mim-fields-audit-20260923-r1.json` under the bulk root.

No project-local numerical adapter is justified by these installed fields.
The upstream tool/PDK interface needs a documented mapping and missing
parameters with model-plane ownership, validated first on this coupon and
then on the unchanged R100 macro. No substitute conductor, invented
capacitance or sheet resistance, PDK/deck/model edit, MIM deletion, or circuit
adoption is claimed here. Full physical PEX remains **failed/unresolved**;
numerical R/RC values are **not run**.

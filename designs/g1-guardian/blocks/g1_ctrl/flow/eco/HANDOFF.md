# GLS handoff: g1_digital r3 (2026-09-26)

**Status: promoted 2026-09-26.** This netlist is the digital of the chip of record
`g1_chip_top_1414_r3.gds` (`7d07a784…`); the RTL is frozen. GLS **passed**: 21 tests / 260 checks,
zero-delay and SDF typ (`../../sim/gls_eco_r3v2/`). This file replaced the v1 handoff (history at the end).

## RTL

The flow read a snapshot of the RTL, `${BULK}/digital-eco-r3cand2-20260926/rtl_snapshot/`. Its
SHA-256 values are in `inputs_sha256.txt` there, and they were checked against the
coordinator's list before the run.

| File | SHA-256 |
|---|---|
| `g1_ctrl/rtl_eco_20260925/g1_digital_top.v` | `4e3b8ff6…` (comment-only change against v1) |
| `g1_ctrl/rtl_eco_20260925/g1_regfile.v` | `33d549da…` (MODE reset 0x03, FAST_EN = 0) |
| `g1_digital.v` | `36757122…` |
| `g1_serial.v` | `df4341e1…` |
| `g1_sync2.v` | `c14906d7…` |
| `g1_trip_timer.v` | `5cab0bc3…` |
| `g1_seu/rtl_eco_20260925/g1_tmr_reg.v` | `f53f82d9…` |
| `g1_seu_chain.v` | `6e10bbc0…` |
| `g1_seu.v` | `7c1831c9…` |
| SDC `flow/g1_digital.sdc` | `c36bf030…` |

## Views

The root is `${BULK}/digital-eco-r3cand2-20260926/final/`, where `${BULK}` is the bulk
results root. All hashes are also in `../final_views.sha256`.

| View | Path | SHA-256 |
|---|---|---|
| Gate netlist (GLS) | `nl/g1_digital.nl.v` | `4b83f1812af385d22302123970443cf63d8889d622794671d31a8e05c9cd9347` |
| Powered netlist (LVS) | `pnl/g1_digital.pnl.v` | `476885d7d6c4e95b0f9db6f7cf5104ed4f644be67794337c8934628427a10a8c` |
| SDF typ | `sdf/nom_typ_1p20V_25C/g1_digital__nom_typ_1p20V_25C.sdf` | `f2a807f09a8831696799df61ae47f5b8cdaee31cd8af093e001827fa48c666c5` |
| SDF slow | `sdf/nom_slow_1p08V_125C/g1_digital__nom_slow_1p08V_125C.sdf` | `cdc404bd5ee294518232af80bb8ebcac7774e92ad442f67df142da1f8d71043f` |
| SDF fast | `sdf/nom_fast_1p32V_m40C/g1_digital__nom_fast_1p32V_m40C.sdf` | `f379a55644e66d937e57c97b0a8453f417d07b3650784c23c853d084805eb302` |
| SPEF nominal | `spef/nom/g1_digital.nom.spef` | `0b626c7fb186f0daf5f391017fb726f4afa2c28ea3436d2c419f88201ad63734` |
| GDS | `gds/g1_digital.gds` | `67d049bfeaae1a1aeeaff2c098d306e6ae02228928bb921c3effa87d7a4c5139` |

Notes for GLS:
- `osc_en` is driven by a `sg13g2_tiehi` through `assign osc_en = net385;`.
- The clock-tree dummy loads (`clkload*`) have unconnected outputs.
- Registers: 1170 on `osc_clk` and 52 on `sclk`.

Suggested command, from the repository root:
`flow/run.sh bash designs/g1-guardian/blocks/g1_ctrl/sim/run_gls.sh ${BULK}/digital-eco-r3cand2-20260926/final/nl/g1_digital.nl.v r3cand2`

Macro results for this netlist are in `${BULK}/digital-eco-r3cand2-20260926/summary_main.txt` and `sta/`:
- STA, typ/fast/slow: setup 28.82/29.04/28.45 ns, hold 0.195/0.114/0.337 ns.
- Macro DRC, LVS, antenna and XOR: all 0. Max-slew, cap and fanout violations: 0.

## History

The v1 candidate (superseded, RTL with MODE reset 0x23) is in `${BULK}/digital-eco-r3cand-20260925/final/`:

| View | SHA-256 |
|---|---|
| Gate netlist | `c3aa2856e6f4891c4bce1f677d1d566291e7b1347e6edfe2f9ccc1fd0d7cca65` |
| Powered netlist | `a1bd886008005214207b8f80e11eed8068a8e2cb30c061c08320c002f6c56a3a` |
| GDS | `89bce861d6d91c50e73784dff6d59222e11ed64077ceb2cd855d3ab1fd189576` |

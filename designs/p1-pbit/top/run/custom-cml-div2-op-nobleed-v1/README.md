# Custom CML divide-by-2 no-bleed operating-point package V1

This package preserves one nominal physical-model operating point for the
provisional [`custom-cml-div2-v3-nobleed`](../../candidate/custom-cml-div2-v3-nobleed/)
experiment. Candidate V2 remains retained and unchanged.

## Result boundary

The candidate differs from V2 only by removing four parallel emitter-to-tail
bleed instances. `TWO-SOURCE-NETLIST-MANIFEST.tsv` accounts for all 90 V2
physical lines as 86 `IDENTICAL` and 4 `ONLY_BASE` rows.

The executed deck uses the nominal 27 °C model sections, `VCC_HBT=2.5 V`,
`VSS=0 V`, and a static `CLK_P=1.2 V` / `CLK_N=0 V` phase. There is no
external output load, reset, initial condition, or node-set. The physical
self-heating model remains enabled.

OpenADA 0.4.0 legacy control mode completed with ngspice 46 and retained one
structurally valid binary `Operating Point` plot with 360 variables, one
point, and 360 finite scalars. The native log contains:

- the temperature-limiter NaN and heat-sink warning;
- dynamic gmin stepping; and
- one completed data row.

OpenADA reports `solver_warning_count: 0`; therefore its legacy engineering
`pass` means only that the requested evidence envelope is structurally
complete. The doctor record says `assertion_evaluated: false`. Neither record
is a project engineering disposition.

## Independently checked observations

The exact candidate diff and binary raw data support these static observations:

- `DIV2_P = 1.52836127822571965 V`;
- `DIV2_N = 1.52836127822582757 V`;
- `DIV2_P - DIV2_N = -1.07913677993565216e-13 V`;
- master active clock `Ic = 1.95433260614587745 mA`;
- master tail `Ic = 1.95817316775317128 mA`;
- master clock-Ic/tail-Ic ratio `= 99.80387017499068%`;
- master active clock `VCE = 0.38900521173297498 V`; and
- the active-clock VCE change from V2 is
  `+0.19156598152271775 V`, not `+0.389 V`.

The static point redirects nearly all of the tail collector-current ratio
through the active clock device, but both outputs remain equal. It does not
establish dynamic divider function.

## Cited model-range audit

`CLOCK-TAIL-HBT-AUDIT.tsv` retains exact raw node voltages and terminal-current
vectors for four clock HBTs and two tail HBTs. Independent recount gives:

- the two active clock HBTs have `VCE ≈ 0.389005 V`, below the cited
  `0.40 V` lower range;
- the two off clock HBTs have `VCE ≈ 1.419277 V`, inside that cited VCE
  range, while their negative VBE is outside the cited VBE range;
- both tail HBTs have `VCE ≈ 0.252841 V`, below the cited lower range; and
- none of the six exceeds the cited `1.60 V` ceiling.

A coupled algebraic diagnostic, holding the data-pair bases and tail emitters
fixed, requires approximately `+0.147159 V` at the tail collector and
`+0.158154 V` at the active data-pair emitter to put both tail and active-clock
VCE at `0.40 V`. The resulting active data-pair VBE is approximately
`0.712027 V`, within the cited range. This is only an algebraic feasibility
map; it is not a realizable bias solution or component recommendation.

Two draft data-pair audit TSVs are intentionally not published. The first
reversed the base lineage for `XQ2_M` and `XQ4_S`; its repair retained wrong
physical line numbers for two slave instances and its prose substituted slave
collector values into master rows. The raw-backed observations above were
recounted independently.

## Files

| File | Purpose |
| --- | --- |
| `p1_cml_div2_front_nobleed.spice` | exact no-bleed Candidate V3 used by the deck |
| `tb_p1_cml_div2_front_dc_op_nobleed.public.cir` | path-sanitized executable OP deck |
| `evidence/tb_p1_cml_div2_front_dc_op_nobleed.log` | complete native ngspice log |
| `raw_tb_p1_cml_div2_front_dc_op_nobleed.raw` | one-point binary raw plot |
| `openada-result.public.json` | path-sanitized OpenADA simulation envelope |
| `preflight.public.json` | path-sanitized OpenADA readiness record |
| `evidence/tb_p1_cml_div2_front_dc_op_nobleed.openada-control.public.sp` | path-sanitized generated control script |
| `TWO-SOURCE-NETLIST-MANIFEST.tsv` | exact V2/V3 line relation |
| `CLOCK-TAIL-HBT-AUDIT.tsv` | exact six-device raw audit |
| `RAW-SUMMARY.tsv` | independently checked raw and warning inventory |
| `SOURCE-IDENTITIES.tsv` | frozen and public artifact identities |
| `PUBLISHED-HASHES.sha256` | hashes of every published technical file |

## Publication transform and reproduction

The native log, raw file, candidate, two-source manifest, and six-HBT audit are
published verbatim. The deck replaces PDK paths with `$PDK_ROOT` and includes
the adjacent candidate copy. The OpenADA JSON, preflight record, and generated
control script replace runtime workspace, tool, PDK-catalog, and temporary
paths with relative paths or named placeholders.

Set `PDK_ROOT` to the `ihp-sg13g2` PDK root and run from this directory:

```sh
ngspice -i -n -o reproduced.log tb_p1_cml_div2_front_dc_op_nobleed.public.cir
```

Move the retained raw file first if it must not be overwritten. Compare
reproduced evidence by circuit identity, plot metadata, vector names, numeric
payload, and warning inventory; binary raw timestamps may differ.

Project engineering status remains **unknown**. No function, performance,
specification pass, signoff, or tape-out readiness is claimed.

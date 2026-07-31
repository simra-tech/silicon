# Custom CML divide-by-2 savecurrents OP package V1

This package preserves an instrumentation-only operating-point rerun of the accepted
[`custom-cml-div2-v2`](../../candidate/custom-cml-div2-v2/) seed. It is paired with the
[`warned nominal operating point`](../custom-cml-div2-op-v2/).

## Result boundary

The executed deck differs from the warned nominal deck only in its title, output filename, and
one `.options savecurrents` directive. Circuit source, model sections, 2.5 V and 0 V supplies,
27 °C temperature, static `CLK_P=1.2 V` / `CLK_N=0 V` phase, absent load and startup aids, and OP
analysis are unchanged.

OpenADA 0.4.0 legacy control mode completed with ngspice 46 and retained one structurally valid
binary `Operating Point` plot with 380 variables, one point, and 380 finite scalars. The native
log retains the same temperature-limiter NaN and heat-sink warning as the baseline. OpenADA's
result still reports `solver_warning_count: 0`, so the native log remains authoritative for the
warning inventory.

Independent raw comparison found:

- all 217 shared voltage variables have exact numeric delta 0.0 from the baseline;
- the instrumented plot adds 159 current vectors and removes none;
- 88 added vectors are `ic`, `ib`, `ie`, and `is` for the 22 HBT instances; and
- the static outputs remain approximately 1.5468244042 V each.

OpenADA's legacy engineering `pass` means the requested evidence envelope is structurally
complete. It is not a project specification result. The preflight record explicitly says
`assertion_evaluated: false`.

## HBT current and thermal-node audit

`HBT-CURRENT-THERMAL-AUDIT.tsv` contains the four retained current vectors, their algebraic sum,
the magnitude of collector current divided by the model comment's `0.003*Nx` condition, the
retained thermal-node scalar, and the current through the model's bleed resistor for each HBT.
Independent extraction reproduced all 132 selected raw scalars and every displayed computation
at the table's printed precision.

- All 22 collector-current magnitudes are below `0.003*Nx`; the exact largest ratio is
  0.16606241900291454 at `XQ1_M`.
- All 22 absolute algebraic current residuals are below 100 pA, but only 6 are below 1 pA. The
  exact largest residual is 92.06804627055866 pA at `XQCLK_LATCH_S`.
- The exact largest retained thermal-node scalar is 8.548270752640883 at `XQ1_M`.

The terminal-current sign convention and the physical units of the thermal-node scalars remain
unestablished in this package. These values do not establish device power or the cause of the
thermal warning. Four clock-steering HBTs remain below the model comment's 0.4 V `VCE` lower
boundary in the paired voltage audit, so project engineering status remains **unknown**.

## Files

| File | Purpose |
| --- | --- |
| `tb_p1_cml_div2_front_dc_op_savecurr.public.cir` | path-sanitized executable instrumented OP deck |
| `evidence/tb_p1_cml_div2_front_dc_op_savecurr.log` | complete native ngspice log |
| `raw_tb_p1_cml_div2_front_dc_op_savecurr.raw` | one-point binary raw plot |
| `openada-result.public.json` | path-sanitized OpenADA simulation envelope |
| `preflight.public.json` | path-sanitized OpenADA readiness record |
| `evidence/tb_p1_cml_div2_front_dc_op_savecurr.openada-control.public.sp` | path-sanitized generated control script |
| `RAW-SUMMARY.tsv` | independently checked raw inventory and baseline comparison |
| `HBT-CURRENT-THERMAL-AUDIT.tsv` | independently checked 22-instance current/scalar audit |
| `SOURCE-IDENTITIES.tsv` | frozen and public artifact identities |
| `PUBLISHED-HASHES.sha256` | hashes of every published technical file |

## Publication transform and reproduction

The frozen private deck has SHA-256
`53ca48ef8e6937e903ed56d1c3e354fe64d36f2d3f0de410d7b2941793511f97`. For publication, PDK
and OSDI paths begin with `$PDK_ROOT`, and the candidate include points to the adjacent published
netlist. The OpenADA JSON, preflight record, and generated control script replace runtime
workspace, tool, PDK-catalog, and temporary paths with relative paths or named placeholders. The
native log, raw file, and derived audit table are published verbatim.

Set `PDK_ROOT` to the `ihp-sg13g2` PDK root and run from this directory:

```sh
ngspice -i -n -o reproduced.log tb_p1_cml_div2_front_dc_op_savecurr.public.cir
```

Move the retained raw file first if it must not be overwritten. Compare reproduced evidence by
plot identity, variable names, numeric values, warning inventory, and circuit identity; binary
raw timestamps may change while numeric payloads remain identical.

No transient function, frequency capability, specification pass, signoff, or tape-out readiness
is claimed.

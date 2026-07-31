# Custom CML divide-by-2 isothermal OP diagnostic V1

This package preserves a one-variable A/B diagnostic against the accepted
[`custom-cml-div2-v2`](../../candidate/custom-cml-div2-v2/) seed and its
[`warned operating point`](../custom-cml-div2-op-v2/).

## Result boundary

The diagnostic netlist differs from candidate V2 only by appending `selft=0` to each of its 22
`npn13G2` instances. Removing those 22 tokens reproduces the accepted V2 netlist byte-for-byte.
The model sections, 2.5 V and 0 V supplies, 27 °C temperature, static
`CLK_P=1.2 V` / `CLK_N=0 V` phase, absent load and startup aids, and OP analysis are unchanged.

OpenADA 0.4.0 legacy control mode completed with ngspice 46 and retained one valid binary
`Operating Point` plot containing 221 variables, one point, and 221 finite scalars. The native
804-byte log has no warning or error line; specifically, the temperature-limiter NaN and
heat-sink warning present in the physical-model baseline are absent.

Independent extraction found:

| Quantity | Warned V2 | `selft=0` diagnostic | Signed delta |
| --- | ---: | ---: | ---: |
| `v(div2_p)` | 1.5468244042221109 V | 1.5259012885863479 V | −20.923115635763 mV |
| `v(div2_n)` | 1.5468244042221255 V | 1.5259012885860195 V | −20.923115636106 mV |
| `i(v_vcc_hbt)` | −5.350962919947392 mA | −5.715617182224383 mA | −0.364654262277 mA |
| `i(v_vss)` | 5.350970762916142 mA | 5.715654858694367 mA | 0.364684095778 mA |

Because `selft=0` is the sole electrical change, this diagnostic confirms that the warning and
approximately 20.9 mV operating-point shift depend on the enabled electro-thermal path. It does
**not** establish that disabling self-heating is physically acceptable. The accepted V2 seed and
its warned physical-model OP remain the design evidence; project engineering status remains
**unknown**.

OpenADA's legacy engineering `pass` means that the requested evidence envelope is structurally
complete. It is not a project specification result. The preflight record explicitly says
`assertion_evaluated: false`.

## Files

| File | Purpose |
| --- | --- |
| `p1_cml_div2_front_isothermal.spice` | exact diagnostic netlist with 22 per-instance overrides |
| `tb_p1_cml_div2_front_dc_op_isothermal.public.cir` | path-sanitized executable OP deck |
| `evidence/tb_p1_cml_div2_front_dc_op_isothermal.log` | complete native ngspice log |
| `raw_tb_p1_cml_div2_front_dc_op_isothermal.raw` | one-point binary raw plot |
| `openada-result.public.json` | path-sanitized OpenADA simulation envelope |
| `preflight.public.json` | path-sanitized OpenADA readiness record |
| `evidence/tb_p1_cml_div2_front_dc_op_isothermal.openada-control.public.sp` | path-sanitized generated control script |
| `DIFF-SUMMARY.tsv` | mechanical circuit-difference proof |
| `RAW-SUMMARY.tsv` | independently extracted values and exact signed deltas |
| `SOURCE-IDENTITIES.tsv` | frozen and public artifact identities |
| `PUBLISHED-HASHES.sha256` | hashes of every published technical file |

## Publication transform and reproduction

The deck, control script, and JSON records replace runtime paths with relative paths or named
placeholders. The diagnostic netlist, native log, and raw file are published verbatim.

Set `PDK_ROOT` to the `ihp-sg13g2` PDK root and run from this directory:

```sh
ngspice -i -n -o reproduced.log tb_p1_cml_div2_front_dc_op_isothermal.public.cir
```

Move the retained raw file first if it must not be overwritten. Compare reproduced evidence by
plot identity, variable names, numeric values, warning inventory, and circuit identity; binary
raw timestamps may change while numeric payloads remain identical.

No transient function, frequency capability, specification pass, signoff, or tape-out readiness
is claimed.

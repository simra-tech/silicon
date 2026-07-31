# Custom CML divide-by-2 nominal operating-point package V2

This package retains the first complete OpenADA-wrapped nominal operating-point evidence for
[`candidate/custom-cml-div2-v2/`](../../candidate/custom-cml-div2-v2/).

## Result boundary

- OpenADA 0.4.0 legacy `simulate` control mode completed with ngspice 46 at exit code 0.
- OpenADA found one structurally valid binary `Operating Point` plot with 221 variables, one
  point, and 221 numeric scalars.
- The native log reports one data row and a completed dynamic-gmin sequence.
- The native log also contains the coupled warning:
  `The temperature limiting function received NaN. Please check your power dissipation and improve your heat sink Rth!`
- OpenADA's retained result reports `solver_warning_count: 0`; the native log is authoritative
  for this warning inventory.
- The preflight selected ngspice and found it usable, but explicitly records
  `assertion_evaluated: false`; it is environment readiness, not design evidence.

OpenADA's legacy engineering `pass` means the requested raw/log artifacts are fresh and
structurally valid. The project engineering status remains **unknown** because the authoritative
native log contains the electro-thermal warning. No operating-point value is evaluated against a
specification here.

The equal static outputs, approximately 1.5468244042 V each, describe one symmetric DC solution.
They do not establish startup resolution, toggling, divide-by-2 function, or 5 GHz capability.
No transient, AC, DC sweep, output load, reset, `.ic`, or `.nodeset` is present.

## HBT voltage-domain audit

The accepted candidate maps 22 `npn13G2` instances to 28 unique terminal-voltage vectors in this
raw point. Independent bounded extraction reproduced every value and derived comparison in
`HBT-VOLTAGE-AUDIT.tsv` at its printed precision:

- 2 of 22 HBTs are outside the model comment's 0.65–0.96 V `VBE` range:
  `XQCLK_LATCH_M` and `XQCLK_TRACK_S`;
- all 4 clock-steering HBTs are below the model comment's 0.4 V `VCE` lower boundary; and
- 0 of 22 HBTs exceeds the separate 1.6 V ceiling.

The two positive-`VBE` clock devices are consistent with saturation. The two negative-`VBE`
devices are off; they are not classified as saturated merely because their `VCE` is low. These
range exceptions do not establish the cause of the thermal warning.

The active HBT corner file is 3,975 bytes with SHA-256
`bae3d705445de8d6b8de4aa798a0e3e5e7cab617d6495d9c56473bc5377de462`.
Its included model file is 20,057 bytes with SHA-256
`ae9288f885dd30fab24b07ed1e7e02e69eac9154022a0a6da576985183b0bd79`.
Model comments distinguish the 1.6 V maximum, the 0.4–2.0 V measurement and valid ranges, and
the `vce_max=1.6` parameter. The raw plot contains no per-HBT collector or base current vectors,
so device currents and thermal power remain unavailable.

## Frozen conditions

| Condition | Value | Authority |
| --- | --- | --- |
| HBT supply | 2.5 V | retained Top V3 nominal deck line 30 |
| VSS | 0 V | retained Top V3 nominal deck line 32 |
| Temperature | 27 °C | executed native log |
| Model sections | `hbt_typ`, `res_typ`, `cap_typ`, `mos_tt`, `dio_tt` | retained Top V3 nominal deck lines 6–11 |
| Static clock phase | `CLK_P=1.2 V`, `CLK_N=0 V` | provisional diagnostic condition inherited from Top V3 lines 46–47 |
| External output load | absent | provisional diagnostic condition |
| Startup aid/reset | absent | provisional diagnostic condition |

The retained Top V3 nominal deck SHA-256 is
`a90cb297b1b2d010bf314abe8f855aa686b7e7c220d8ceb42b72743321b81889`.

## Files

| File | Purpose |
| --- | --- |
| `tb_p1_cml_div2_front_dc_op.public.cir` | path-sanitized executable OP deck |
| `evidence/tb_p1_cml_div2_front_dc_op.log` | complete native ngspice log |
| `raw_tb_p1_cml_div2_front_dc_op.raw` | one-point binary raw plot |
| `openada-result.public.json` | path-sanitized OpenADA simulation envelope |
| `preflight.public.json` | path-sanitized OpenADA readiness record |
| `evidence/tb_p1_cml_div2_front_dc_op.openada-control.public.sp` | path-sanitized generated control script |
| `RAW-SUMMARY.tsv` | independently extracted selected scalars |
| `HBT-VOLTAGE-AUDIT.tsv` | independently checked 22-instance terminal-voltage audit |
| `SOURCE-IDENTITIES.tsv` | frozen and public artifact identities |
| `PUBLISHED-HASHES.sha256` | hashes of every published technical file |

## Publication transform

The frozen private deck had SHA-256
`c24046d7959d128a639df42eaa1941fcf0861372d3398897327e42d54cdfa6ec`.
For publication, PDK and OSDI paths now begin with `$PDK_ROOT`, and the candidate include points
to the adjacent published netlist. The OpenADA JSON and generated control script replace runtime
workspace, tool, PDK-catalog, and temporary paths with relative paths or named placeholders.
The native log and raw file are published verbatim.

## Reproduce

Set `PDK_ROOT` to the `ihp-sg13g2` PDK root and run from this directory:

```sh
ngspice -i -n -o reproduced.log tb_p1_cml_div2_front_dc_op.public.cir
```

Move the retained raw file first if it must not be overwritten. Compare reproduced evidence by
plot identity, variable names, numeric values, warning inventory, and circuit identity; binary
raw timestamps may change while the numeric payload remains identical.

Signoff and tape-out readiness are not claimed.

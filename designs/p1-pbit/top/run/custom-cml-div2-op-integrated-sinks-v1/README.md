# Custom CML divide-by-2 integrated-sink operating-point package V1

This package preserves the first static operating point for Candidate V5, which
replaces the four ideal follower-load sources used by the preceding diagnostic
with four physical PTAT-biased HBT sink branches.

## Candidate boundary

Candidate V5 SHA-256
`689d4beedfce278f0c13cf0e79a25b87ba8a12d25b9459e51dfbfde041cd3db7`
differs from no-bleed Candidate V3 SHA-256
`d5900dae655f376e6c2aeeebe18d7753f3c36c73283ca859586e57f25dcedd52`
only by the eight additions in `V3-V5-DIFF.patch`:

- four `npn13G2 Nx=3` sink HBTs;
- four independent `rppd w=12.0u l=0.50u` emitter-degeneration
  resistors;
- master collectors at `ef_p_m` and `ef_n_m`, sharing base
  `c_p1_comp_m`; and
- slave collectors at `DIV2_P` and `DIV2_N`, sharing base
  `c_p1_comp_s`.

The executed deck uses the nominal 27 °C model sections, `VCC_HBT=2.5 V`,
`VSS=0 V`, and static `CLK_P=1.2 V` / `CLK_N=0 V`. It has no external
output load, ideal follower source, reset, initial condition, or node-set.
The physical self-heating model remains enabled.

## Evidence boundary

OpenADA 0.4.0 legacy control mode completed with ngspice 46 and retained a
binary `Operating Point` plot with 428 real variables, one point, and 428
finite scalars. The raw file has an 18,802-byte header and 3,424-byte payload,
for 22,226 bytes total.

The native log retains the temperature-limiter NaN and heat-sink warning,
dynamic gmin stepping, and one completed data row. OpenADA reports
`solver_warning_count: 0`; its legacy engineering `pass` means only that the
requested evidence envelope is structurally complete. The doctor record says
`assertion_evaluated: false`. Neither record is a project engineering
disposition.

## Independently checked observations

`STATIC-HBT-AUDIT.tsv` is a direct 17-digit parse of the frozen raw plot.

- All four new sink collector currents are
  `1.03766564072922066–1.03767334917735806 mA`.
- Their static VBE range is
  `0.82815216849922246–0.82815226091773941 V`; their VCE range is
  `1.33322117318436906–1.33330975745280078 V`.
- The four original followers are at
  `0.87705345813874658–0.87714127894248506 V` VBE and
  `1.14938496056260697–1.14947367245892540 V` VCE at this static phase.
- The active master-track and slave-latch clock HBTs have
  `0.95869755260839618–0.95869764074496788 V` VBE, leaving only about
  `1.302 mV` to the cited `0.960 V` ceiling. Their VCE is about
  `0.2418524–0.2418525 V`, below the cited `0.400 V` floor.
- Both tail HBTs are also below that cited VCE floor at about
  `0.2253090 V`.

`V3-V5-BIAS-COMPARISON.tsv` keeps the cross-candidate arithmetic explicit.
Relative to the frozen no-bleed V3 operating point:

- both PTAT bias nodes fall by about `1.0027 mV`;
- both original tail collector currents fall by about `40.82 uA`, or
  `2.0846%`; and
- each physical sink is about `5.983%` above the provisional half-V3-tail
  current estimate.

This static point establishes a physical bias solution for the four follower
nodes. It does not establish dynamic frequency division or dynamic device
range compliance.

## Files

| File | Purpose |
| --- | --- |
| `p1_cml_div2_front_integrated_sinks.spice` | exact Candidate V5 used by the deck |
| `V3-V5-DIFF.patch` | complete V3-to-V5 candidate delta |
| `tb_p1_cml_div2_front_dc_op_v5.public.cir` | path-sanitized executable OP deck |
| `evidence/tb_p1_cml_div2_front_dc_op_v5.log` | complete native ngspice log |
| `raw_tb_p1_cml_div2_front_dc_op_v5.raw` | one-point binary raw plot |
| `openada-result.public.json` | path-sanitized OpenADA simulation envelope |
| `preflight.public.json` | path-sanitized OpenADA readiness record |
| `evidence/tb_p1_cml_div2_front_dc_op_v5.openada-control.public.sp` | path-sanitized generated control script |
| `STATIC-HBT-AUDIT.tsv` | exact 12-device static voltage/current audit |
| `V3-V5-BIAS-COMPARISON.tsv` | exact bias-node and current comparison |
| `SOURCE-IDENTITIES.tsv` | frozen and public artifact identities |
| `PUBLISHED-HASHES.sha256` | hashes of every published technical file |

## Publication transform and reproduction

The candidate, native log, raw file, and numeric audits are published
verbatim. The deck replaces PDK paths with `$PDK_ROOT` and includes the
adjacent candidate copy. The OpenADA JSON, preflight record, and generated
control script replace runtime workspace, tool, PDK-catalog, and temporary
paths with relative paths or named placeholders.

Set `PDK_ROOT` to the `ihp-sg13g2` PDK root and run from this directory:

```sh
ngspice -i -n -o reproduced.log tb_p1_cml_div2_front_dc_op_v5.public.cir
```

Move the retained raw file first if it must not be overwritten. Compare
reproduced evidence by circuit identity, plot metadata, vector names, numeric
payload, and warning inventory; binary raw timestamps may differ.

Project engineering status remains **unknown**. No dynamic function,
performance, specification pass, signoff, or tape-out readiness is claimed.

# Custom CML divide-by-2 integrated-sink transient package V1

This package preserves the first transient in which Candidate V5 produces an
observed divided terminal waveform using four integrated physical
follower-sink branches and no ideal follower-load sources.

## Candidate and deck boundary

Candidate V5 SHA-256
`689d4beedfce278f0c13cf0e79a25b87ba8a12d25b9459e51dfbfde041cd3db7`
is the same netlist used by the preceding static operating-point package. Its
complete delta from no-bleed Candidate V3 is retained in `V3-V5-DIFF.patch`:

- four `npn13G2 Nx=3` sink HBTs;
- four independent `rppd w=12.0u l=0.50u` emitter-degeneration resistors;
- master sink collectors at `ef_p_m` and `ef_n_m`, sharing base
  `c_p1_comp_m`; and
- slave sink collectors at `DIV2_P` and `DIV2_N`, sharing base
  `c_p1_comp_s`.

The executed deck uses the nominal HBT, resistor, capacitor, MOS and diode
corner sections at 27 °C, `VCC_HBT=2.5 V`, and `VSS=0 V`. Complementary
`0–1.2 V` clocks have a 200 ps period, 2 ps edges, 96 ps plateaus and a
100 ps initial static prephase. The transient step is 2 ps through 4 ns.
There is no external load source, ideal follower source, reset, initial
condition, node-set or transient-noise source. The physical self-heating model
remains enabled.

## Retained execution evidence

OpenADA 0.4.0 legacy control mode completed with ngspice 46 and retained a
binary `Transient Analysis` plot. `RAW-SUMMARY.tsv` independently binds the
raw envelope:

- 429 real variables by 2,284 points;
- 979,836 finite scalars and no non-finite scalar;
- a `Binary:\n` marker beginning at byte 18,781;
- payload beginning at byte 18,789;
- 7,838,688 payload bytes; and
- 7,857,477 bytes total.

The native log records 2,284 data rows and completion. It also retains:

```text
The temperature limiting function received NaN.
Please check your power dissipation and improve your heat sink Rth!
```

OpenADA reports no solver warnings because that native thermal message is not
classified as one by the legacy adapter. Its engineering `pass` means only
that the requested evidence envelope is structurally complete. The doctor
record says `assertion_evaluated: false`. Neither record is a project
engineering disposition.

## Independently checked waveform observation

`CROSSING-SUMMARY.tsv` is a direct parse of the frozen binary payload from
2 ns through 4 ns. Master collector, master follower, slave collector and
terminal-output differentials each have ten linearly interpolated zero
crossings. The terminal output spans
`-0.6550845492118901–+0.6550655435998533 V`.

`OUTPUT-CROSSINGS.tsv` retains all ten terminal crossing times. Adjacent
crossings average `199.99954914269767 ps`; a complete differential cycle
measured across two crossings averages `399.99932096335164 ps`, corresponding
to `2.500004243986257 GHz` under this nominal 5 GHz stimulus.

This is observed nominal physical-sink division in the retained simulation.
It is not a specification pass.

## Device-bound occupancy

`BOUNDARY-OCCUPANCY.tsv` retains a 12-device by four-threshold, 48-row audit
for the 2–4 ns interval. It contains extrema, threshold occupancy sample
counts, linearly interpolated interval counts and durations, and the endpoints
of the longest contiguous interval. It intentionally has no pass/fail or
valid/invalid column.

The audit uses the numeric thresholds `VBE=0.65/0.96 V` and
`VCE=0.4/1.6 V` as reference coordinates:

- each added sink has 20 or 21 high-VCE intervals, totaling
  `874.309–875.919 ps`; its longest interval is about `83.08–87.15 ps`;
- each original follower has five low-VBE and ten high-VBE intervals; their
  longest intervals are about `4.83–4.84 ps` and `1.46–1.56 ps`;
- each audited clock device has ten low-VBE intervals totaling about
  `988.26 ps`, 11 high-VBE intervals totaling `34.59–34.98 ps`, and ten
  low-VCE intervals totaling `32.96–33.74 ps`; and
- each tail device remains below the 0.4 V VCE coordinate for the complete
  2,000 ps window.

The local PDK model file identifies 0.65–0.96 V VBE and 0.4–2.0 V VCE as
model-valid ranges and separately names 1.6 V as a maximum
collector-to-emitter voltage/model parameter. This package does not promote
those literals into a reliability, absolute-maximum, breakdown, harmlessness
or operating-mode claim. The authority and applicability of the dynamic
exceptions remain unresolved.

## Files

| File | Purpose |
| --- | --- |
| `p1_cml_div2_front_integrated_sinks.spice` | exact Candidate V5 used by the deck |
| `V3-V5-DIFF.patch` | complete Candidate V3-to-V5 delta |
| `tb_p1_cml_div2_front_tran_v5.public.cir` | path-sanitized executable transient deck |
| `evidence/tb_p1_cml_div2_front_tran_v5.log` | complete native ngspice log |
| `raw_tb_p1_cml_div2_front_tran_v5.raw` | complete native binary raw plot |
| `openada-result.public.json` | path-sanitized OpenADA simulation envelope |
| `preflight.public.json` | path-sanitized OpenADA readiness record |
| `evidence/tb_p1_cml_div2_front_tran_v5.openada-control.public.sp` | path-sanitized generated control script |
| `RAW-SUMMARY.tsv` | independently checked raw-envelope identity |
| `CROSSING-SUMMARY.tsv` | differential ranges, crossings, periods and inferred frequency |
| `OUTPUT-CROSSINGS.tsv` | exact interpolated terminal zero-crossing times |
| `BOUNDARY-OCCUPANCY.tsv` | rectangular dynamic threshold-occupancy audit |
| `SOURCE-IDENTITIES.tsv` | frozen and public artifact identities |
| `PUBLISHED-HASHES.sha256` | hashes of every published technical file |

## Publication transform and reproduction

The candidate, native log, raw plot, candidate diff and numeric audits are
published verbatim. The deck replaces the PDK root with `$PDK_ROOT` and
includes the adjacent candidate copy. The OpenADA JSON, preflight record and
generated control script replace runtime workspace, tool, PDK-catalog and
temporary paths with relative paths or named placeholders.

Set `PDK_ROOT` to the `ihp-sg13g2` PDK root and run from this directory:

```sh
ngspice -i -n -o reproduced.log tb_p1_cml_div2_front_tran_v5.public.cir
```

Move the retained raw file first if it must not be overwritten. Compare a
reproduced result by circuit identity, plot metadata, vector names, numeric
payload and warning inventory; binary raw timestamps may differ.

Project engineering status remains **unknown**. No reliability disposition,
performance or specification pass, signoff, or tape-out readiness is claimed.

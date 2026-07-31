# Schematic-backed comparator with the 18.5 um feedback resistor

This package binds an isolated Xschem comparator source to a generated symbol and
a hierarchical SPICE netlist. It resolves a source-control gap: the prior active
simulation netlist contained an `XRFB` device that was absent from its named
schematic.

## What this package establishes

- `p1_comparator.sch` contains 46 IHP primitive instances, including
  `XRFB raw_inv cml_out_p sub! rppd w=1.0u l=18.5u`.
- `p1_comparator.sym` exposes the declared 12-port interface in this literal
  order: `PBIT_OUT PBIT_RAW CLK_OUT_DIV IN_P IN_N CLK_P CLK_N TRIM_P TRIM_N
  VCC_HBT VDD VSS`.
- `p1_comparator_hier.sch` instantiates that symbol once and connects all 12
  ports.
- OpenADA 0.4.0 completed Xschem netlist generation with engineering status
  `pass` and zero normalized diagnostics.
- The generated active `.subckt p1_comparator`, its `X1` instance, and the
  symbol all use the same port order. The subcircuit contains 46 device names.

The frozen native result was independently recounted before publication. Its
device map is identical to the standalone generated V3 comparator; the
hierarchy step changes only wrapper and instance context.

## What this package does not establish

This is netlist-generation evidence, not an electrical simulation. It does not
show operating-point validity, transient behavior, correlation, trim range,
PVT closure, layout, signoff, or tape-out readiness. The PDK-backed simulation
decks used elsewhere in this project require model-library and control
constructs outside OpenADA's current shared `circuit.simulate` profile, so the
netlist-generation pass is not promoted into a claim that the circuit works.

## Files

| File | Purpose |
| --- | --- |
| `p1_comparator.sch` | isolated source schematic |
| `p1_comparator.sym` | ordered 12-pin symbol |
| `p1_comparator_hier.sch` | one-instance hierarchy harness |
| `p1_comparator_hier.spice` | path-sanitized generated hierarchy netlist |
| `xschemrc` | exact Xschem/PDK configuration used for generation |
| `openada-netlist-result.public.json` | public projection of the normalized OpenADA result |
| `SOURCE-IDENTITIES.tsv` | identities of the frozen pre-publication artifacts |
| `PUBLISHED-HASHES.sha256` | checkable hashes of the published technical files |

The original frozen netlist had SHA-256
`71642f010562713aaef6f9fe7bc0f933b7f53b0cae16e9c6f8c3cd38053cbeeb`.
Only absolute path comments were rewritten for publication; hierarchy and
device lines are unchanged. The published path-sanitized copy has SHA-256
`3795c56b7e6b6f5fcf1d9e14baa5fea4f11f40d23b457e13c7717479c3b10c34`.
The original normalized result had SHA-256
`509654fec231edcf44561627868adb263e01e030ad5779ea4a7f72f11430d497`;
its public projection removes absolute execution paths and host details.

## Reproduce the generation step

Set `PDK_ROOT` to an installation containing `ihp-sg13g2`, then run from this
directory:

```sh
openada netlist ./p1_comparator_hier.sch \
  --rcfile ./xschemrc \
  --output ./p1_comparator_hier.generated.spice
```

A reproduction should be compared by active subcircuit interface and per-name
device literals. Path comments and temporary runtime paths are not electrical
content.

# Source-backed structural Top V3

This package binds the current noise generator, preamplifier, and comparator
schematics into one 17-port Xschem hierarchy. It is a structural
netlist-generation checkpoint, not an electrical simulation. Relative to Top
V2, it binds the repaired noise-generator substrate tap without changing the
top source, symbols, harness, interfaces, or other block sources.

## What this package establishes

- The top schematic has exactly three block instances. Its only functional
  source changes from rejected V1 are three wires connecting `PBIT_OUT`,
  `PBIT_RAW`, and `CLK_OUT_DIV`; 17 zero-length labeled wire records were also
  removed.
- `p1_top.sym`, the one-instance hierarchy harness, the active
  `.subckt p1_top`, and its wrapper instance use the same literal port order:
  `PBIT_OUT PBIT_RAW CLK_OUT_DIV CLK_P CLK_N TRIM_P TRIM_N NOISE_GEN_VCC
  NOISE_GEN_VSS NOISE_AMP_VCC NOISE_AMP_VSS COMPARATOR_VCC_HBT VDD
  COMPARATOR_VSS VB1 VB2 IE`.
- The active top instantiates the exact source-backed noise-generator,
  preamplifier, and comparator hierarchies once each. Their active lower-block
  device counts are 5, 29, and 46.
- The only normalized generated-netlist change from Top V2 is
  `XTAP1 VSS net1 ptap1` to `XTAP1 VSS sub! ptap1` inside
  `p1_noise_gen`; every other hierarchy and device line is unchanged.
- OpenADA 0.4.0 completed Xschem netlist generation with execution status
  `completed`, exit code 0, engineering status `pass`, and zero diagnostics.
- The source-bound planning record keeps seven supply-related top ports
  distinct. Unsupported harness values remain `UNKNOWN`; prior-bench values
  remain lineage only.

The exact Xschem configuration is already published at
[`../../comparator/source-backed-rfb18p5-v5/xschemrc`](../../comparator/source-backed-rfb18p5-v5/xschemrc).
Its SHA-256 is
`d6d8fa5157ad2072e6d1ce63bda5f5d593ef4eb84631f23eed5e9ae3886f18b5`.

## What this package does not establish

No valid top-level operating point, transient, noise, correlation, power,
timing, PVT, DRC, LVS, or PEX result exists for this hierarchy. The first
operating-point attempt on Top V2 failed and produced no raw dataset; that
failed execution is not part of this structural package. The values retained
in the planning tables do not choose whether `VB1`, `VB2`, and `IE` are
external or integrated. This package makes no signoff, foundry-approval, or
tape-out-readiness claim.

## Files

| File | Purpose |
| --- | --- |
| `p1_top.sch`, `p1_top.sym` | structural top source and ordered symbol |
| `p1_top_hier.sch` | one-instance top hierarchy harness |
| `p1_noise_gen.*`, `p1_noise_amp.*`, `p1_comparator.*` | exact bound block sources and symbols |
| `p1_top_hier.spice` | path-sanitized generated hierarchical netlist |
| `openada-netlist-result.public.json` | public projection of the normalized OpenADA result |
| `p1_top_v2_harness_plan_v2.tsv` | corrected read-only harness plan |
| `planning/` | accepted planning evidence and retained rejected V1 |
| `SOURCE-IDENTITIES.tsv` | frozen pre-publication artifact identities |
| `PUBLISHED-HASHES.sha256` | checkable hashes of published technical files |

The frozen generated netlist had SHA-256
`b8ac82719ffcd365b91fbd7c997b45d9d422e684077fe82f05a691cb7dcbd4ca`.
Only nine absolute path comments were rewritten for publication; subcircuit,
instance, and device lines are unchanged. The path-sanitized netlist has
SHA-256
`d32a15f825da966c0533f6b22fda842cbafcc1ee3bf1109aad5281f046ddbbc8`.
The original normalized result had SHA-256
`4b27929f1448c5948271f05993d9fd400caa01b80590cbee90fc9c6e959dfa20`;
its public projection removes execution paths and host details.

## Reproduce the generation step

Set `PDK_ROOT` to an installation containing `ihp-sg13g2`, then run:

```sh
openada netlist ./p1_top_hier.sch \
  --rcfile ../../comparator/source-backed-rfb18p5-v5/xschemrc \
  --output ./p1_top_hier.generated.spice
```

Compare a reproduction by active subcircuit port order, top instances, and
per-name lower-device literals. Path comments and temporary runtime paths are
not electrical content.

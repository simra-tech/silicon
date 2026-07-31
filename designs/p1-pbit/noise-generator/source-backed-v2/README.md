# Schematic-backed noise-generator substrate repair

This package preserves the first source-backed noise-generator hierarchy and
replaces one ineffective substrate label wire with an Xschem label pin. The
resulting generated netlist connects the `ptap1` instance between `VSS` and the
internal `sub!` node.

## What this package establishes

- `p1_noise_gen.sch` is the exact 2,014-byte repaired source at SHA-256
  `e6785b8c4f9aa8db422fb25012cbda507f6ef5585aca24e7aa8b8d696b4a0d8b`.
- Relative to
  [`../source-backed-v1/p1_noise_gen.sch`](../source-backed-v1/p1_noise_gen.sch),
  the only source change is:

  ```diff
  -N 0 230 0 250 {lab=sub!}
  +C {devices/lab_pin.sym} 0 230 0 0 {lab=sub!}
  ```

- The ordered seven-pin symbol and one-instance hierarchy harness are
  byte-identical to the first source-backed package.
- OpenADA 0.4.0 completed one Xschem netlist operation with engineering status
  `pass` and zero diagnostics.
- The generated five-device subcircuit contains the literal connection
  `XTAP1 VSS sub! ptap1`.

The exact Xschem configuration is already published at
[`../../comparator/source-backed-rfb18p5-v5/xschemrc`](../../comparator/source-backed-rfb18p5-v5/xschemrc).
Its SHA-256 is
`d6d8fa5157ad2072e6d1ce63bda5f5d593ef4eb84631f23eed5e9ae3886f18b5`.

## What this package does not establish

This is source-connectivity and netlist-generation evidence, not an electrical
simulation. It does not establish a valid operating point, noise density, bias
validity, transient statistics, correlation, PVT closure, layout, signoff, or
tape-out readiness. The earlier failed top-level operating-point attempt is not
included here and remains failed.

## Files

| File | Purpose |
| --- | --- |
| `p1_noise_gen.sch` | exact repaired isolated source schematic |
| `p1_noise_gen.raw-generated.sym` | retained raw symbol generator output from V1 |
| `p1_noise_gen.sym` | unchanged ordered seven-pin symbol |
| `p1_noise_gen_hier.sch` | unchanged one-instance hierarchy harness |
| `p1_noise_gen_hier.spice` | path-sanitized generated hierarchy netlist |
| `openada-netlist-result.public.json` | public projection of the normalized OpenADA result |
| `SOURCE-IDENTITIES.tsv` | identities of frozen pre-publication artifacts |
| `PUBLISHED-HASHES.sha256` | checkable hashes of published technical files |

The frozen generated netlist had SHA-256
`a9949b2cfd0a01af88a620e0f2ded157069ce76562c5cac35d2d07945dd5c310`.
Only three absolute path comments were rewritten for publication; hierarchy
and device lines are unchanged. The published path-sanitized netlist has
SHA-256
`3e0af6df1249dce46538e2da10ed27f3180a3cef4f755b68f795e356f051325e`.
The original normalized result had SHA-256
`6cfd4cd32a0c9cc207faebd6c13073bbac08f8de42b244b7563c81d895712f86`;
its public projection removes execution paths and host details.

## Reproduce the generation step

Set `PDK_ROOT` to an installation containing `ihp-sg13g2`, then run:

```sh
openada netlist ./p1_noise_gen_hier.sch \
  --rcfile ../../comparator/source-backed-rfb18p5-v5/xschemrc \
  --output ./p1_noise_gen_hier.generated.spice
```

Compare a reproduction by active subcircuit interface and per-name device
literals. Path comments and temporary runtime paths are not electrical content.

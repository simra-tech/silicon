# Schematic-backed noise-generator hierarchy

This package binds the current differential HBT noise-generator source to an
ordered seven-pin symbol and a one-instance hierarchical SPICE netlist.

## What this package establishes

- `p1_noise_gen.sch` is the exact 1,994-byte source at SHA-256
  `168839d8b0f3b721a46d8336f5932faaaa4cf6bcc166ba626f817b45892b905a`.
- The raw generated symbol is retained separately. `p1_noise_gen.sym` differs
  from it only by whole `B`/`L`/`T` pin-group moves.
- The final symbol, hierarchy `X1` line, and active `.subckt p1_noise_gen` all
  use the literal order
  `RAW_NOISE_P RAW_NOISE_N VCC VSS VB1 VB2 IE`.
- OpenADA 0.4.0 completed Xschem netlist generation with engineering status
  `pass`, zero diagnostics, and an active five-device subcircuit.

The exact Xschem configuration is already published at
[`../../comparator/source-backed-rfb18p5-v5/xschemrc`](../../comparator/source-backed-rfb18p5-v5/xschemrc).
Its SHA-256 is
`d6d8fa5157ad2072e6d1ce63bda5f5d593ef4eb84631f23eed5e9ae3886f18b5`.

## What this package does not establish

This is netlist-generation evidence, not an electrical simulation. It does not
show noise density, bias validity, transient statistics, correlation, PVT
closure, layout, signoff, or tape-out readiness. Numerical annotations in the
schematic are retained source text, not results established by this package.

## Files

| File | Purpose |
| --- | --- |
| `p1_noise_gen.sch` | exact isolated source schematic |
| `p1_noise_gen.raw-generated.sym` | retained raw generator output |
| `p1_noise_gen.sym` | ordered seven-pin symbol |
| `p1_noise_gen_hier.sch` | one-instance hierarchy harness |
| `p1_noise_gen_hier.spice` | path-sanitized generated hierarchy netlist |
| `openada-netlist-result.public.json` | public projection of the normalized OpenADA result |
| `SOURCE-IDENTITIES.tsv` | identities of frozen pre-publication artifacts |
| `PUBLISHED-HASHES.sha256` | checkable hashes of published technical files |

The frozen generated netlist had SHA-256
`8a6d2525417d12a3f61939337784dd68674db9317f9236e27cd47b316f8b10b3`.
Only three absolute path comments were rewritten for publication; hierarchy
and device lines are unchanged. The published path-sanitized netlist has
SHA-256
`02870408651d5b3ee056cb812be3dd779b5a12ec90ce06c578e9f8f4f8018631`.
The original normalized result had SHA-256
`eb951034393e28e8ce7bef89195488d735833fbd1f9022cdce9b05f9efaa5be7`;
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

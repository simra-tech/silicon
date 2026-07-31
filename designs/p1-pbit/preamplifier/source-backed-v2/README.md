# Schematic-backed noise-amplifier hierarchy

This package binds the current two-stage Xschem preamplifier source to an
ordered six-pin symbol and a one-instance hierarchical SPICE netlist.

## What this package establishes

- `p1_noise_amp.sch` differs from source SHA-256
  `b2124e637b6a707950670a37050ea0a0f4d7f01cf6994a48a43f49b006d657f0`
  only by removing four later copies of duplicate same-net labels:
  `e_p1`, `e_p2`, `e_s1`, and `vbias2`.
- The cleaned source has SHA-256
  `8bc1d588bced233fa8c57d9ab8623456d09a981471761f50b558268c8d915107`
  and no duplicate component-coordinate groups.
- `p1_noise_amp.sym`, the harness `X1` line, and the active
  `.subckt p1_noise_amp` all use the literal port order
  `NOISE_AMP_P NOISE_AMP_N RAW_NOISE_P RAW_NOISE_N VCC VSS`.
- OpenADA 0.4.0 completed Xschem netlist generation with engineering status
  `pass`, zero diagnostics, and an active 29-device subcircuit.

The exact Xschem configuration is already published at
[`../../comparator/source-backed-rfb18p5-v5/xschemrc`](../../comparator/source-backed-rfb18p5-v5/xschemrc).
Its SHA-256 is
`d6d8fa5157ad2072e6d1ce63bda5f5d593ef4eb84631f23eed5e9ae3886f18b5`.

## What this package does not establish

This is netlist-generation evidence, not an electrical simulation. It does not
show gain, bandwidth, noise, power, operating-point validity, transient
behavior, PVT closure, layout, signoff, or tape-out readiness. Numerical
annotations embedded in the schematic are retained source text and are not
promoted into evidence by this package.

## Files

| File | Purpose |
| --- | --- |
| `p1_noise_amp.sch` | cleaned isolated source schematic |
| `p1_noise_amp.sym` | ordered six-pin symbol |
| `p1_noise_amp_hier.sch` | one-instance hierarchy harness |
| `p1_noise_amp_hier.spice` | path-sanitized generated hierarchy netlist |
| `openada-netlist-result.public.json` | public projection of the normalized OpenADA result |
| `SOURCE-IDENTITIES.tsv` | identities of frozen pre-publication artifacts |
| `PUBLISHED-HASHES.sha256` | checkable hashes of published technical files |

The frozen generated netlist had SHA-256
`186d52fd57d734dabd150514be417a5d408f6c10d89bf10c48694043aff8a934`.
Only three absolute path comments were rewritten for publication; hierarchy
and device lines are unchanged. The published path-sanitized netlist has
SHA-256
`303bd37d0ceabdefafa24e3576d857d1ceb6546d43310e3828bfd643c6736e6e`.
The original normalized result had SHA-256
`5f2c837d59be379081053502483d54b0afc13bef916cbd3da5adbffc7657c925`;
its public projection removes execution paths and host details.

## Reproduce the generation step

Set `PDK_ROOT` to an installation containing `ihp-sg13g2`, then run:

```sh
openada netlist ./p1_noise_amp_hier.sch \
  --rcfile ../../comparator/source-backed-rfb18p5-v5/xschemrc \
  --output ./p1_noise_amp_hier.generated.spice
```

Compare a reproduction by active subcircuit interface and per-name device
literals. Path comments and temporary runtime paths are not electrical content.

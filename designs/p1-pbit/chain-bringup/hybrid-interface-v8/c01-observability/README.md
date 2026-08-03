# C01 observability derivative

This package publishes the single C01 observability-only transient run for the
P1 V8 CML-to-CMOS interface. It is a portable derivative of a private run
package: container-specific PDK paths in the deck were replaced by
`$PDK_ROOT`, and one container binary path in the original classification was
replaced by its tool identity. The native raw, run log, interface, crossing
table, and correction record are otherwise copied byte for byte.

## Result boundary

- **Confirmed:** the C01 deck adds exactly six `save` lines to the published V8
  baseline deck. It does not change topology, values, models, supplies,
  temperature, stimulus, timestep, or load.
- **Confirmed:** ngspice-46 returned zero, wrote 1,065 points and emitted no
  warning/error line in the retained run log.
- **Confirmed:** the C01 raw has 89 vectors. Every one of the 78 baseline
  vectors, including time, is bit-identical; the 11 additions are device
  current vectors.
- **Confirmed:** the differential input has ten sign-changing crossings and
  both CMOS outputs have zero 0.6 V crossings. The table has 50 data rows plus
  one header, five samples around each input crossing.
- **Retracted:** the original `C01-CLASSIFICATION.md` conclusion that C01 proves
  drive/headroom loss and excludes dynamic loading. MOS `ids` is channel drain
  current, not gate/displacement current, and rail distance does not establish
  device operating region. `C01-CORRECTION.md` supersedes that causal label.
- **Current engineering status:** cause ambiguous; P1 gate still running.
  Simulation execution succeeded, but circuit acceptance is not evaluated.

The original classification is retained so the failed inference remains
auditable. The private root also held an unmanifested `toolcheck/` subtree; it
is intentionally excluded. This public directory is closed by `SHA256SUMS`.

## Reproduce the package checks

From this directory, with the parent V8 baseline package present:

```sh
python3 verify.py
sha256sum -c SHA256SUMS
```

To rerun the portable deck, use an IHP SG13G2 installation compatible with the
recorded model and ngspice identities, set `PDK_ROOT` to the PDK root, and run
ngspice from this directory. A rerun is new evidence and is not required to
verify the retained raw.

No signoff, tape-out readiness, entropy qualification, or foundry acceptance is
claimed.

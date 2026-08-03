# C02 ideal gate-isolation experiment

This package publishes one controlled transient experiment on the P1 V8
CML-to-CMOS interface. C02 inserts non-inverting ideal unity voltage sources
between divider nodes `GP`/`GN` and the first CMOS gates. Both sources are
referenced to the subcircuit `VSS`, so their output currents return through the
same harness rail accounting. No production buffer is proposed by this test.

This is a portable derivative of the retained native run. The three
container-specific model-library prefixes in the deck were replaced by
`$PDK_ROOT`. The interface, native log, and binary raw are otherwise copied
byte for byte. The raw file keeps the baseline-looking basename written by the
deck's explicit `write` command; it is bound here by its hash and 82-vector
shape, not by its name. Frozen deck comments that say `UNRUN` record the
pre-invocation source state; the native log and raw establish execution.

## Controlled change

Relative to the published V8 baseline interface, the only circuit-source delta
is:

```spice
+EGP_BUF gbuf_p VSS GP VSS 1
+EGN_BUF gbuf_n VSS GN VSS 1
-XM1 CM_N GP E_CM VSS sg13_lv_nmos w=6.0u l=0.13u ng=1 m=1 mm_ok=1
-XM2 CM_P GN E_CM VSS sg13_lv_nmos w=6.0u l=0.13u ng=1 m=1 mm_ok=1
+XM1 CM_N gbuf_p E_CM VSS sg13_lv_nmos w=6.0u l=0.13u ng=1 m=1 mm_ok=1
+XM2 CM_P gbuf_n E_CM VSS sg13_lv_nmos w=6.0u l=0.13u ng=1 m=1 mm_ok=1
```

The portable C02 deck differs from the portable V8 deck only at its interface
include. Models, supplies, temperature, 50-ohm source assumption, common mode,
differential swing, edge-slope proxy, cadence, timestep, duration, and output
load are unchanged.

## Result boundary

- **Confirmed execution:** ngspice-46 completed one 2 ns transient, wrote
  1,065 rows, and retained no warning/error text in the native log.
- **Confirmed evidence:** the raw has 82 real vectors by 1,065 points, all
  finite, with strictly increasing time from 0 to 2 ns. It contains all 78
  baseline vectors plus only two buffer voltages and two ideal-source currents.
- **Confirmed control:** `v(xu1.gbuf_p)` is bit-identical to `v(xu1.gp)` and
  `v(xu1.gbuf_n)` is bit-identical to `v(xu1.gn)` at every point.
- **Confirmed measurement:** the input differential has ten sign-changing
  crossings. Both CMOS outputs have zero crossings of the 0.6 V rail-midpoint
  proxy. Output P remains near 1.2 V with 0.1048005 mV peak-to-peak range;
  output N remains near 0 V with 0.8159631 mV peak-to-peak range.
- **Engineering disposition:** removing divider-node gate loading is not
  sufficient to recover switching in this ideal-isolation experiment. This
  rejects gate loading as a sufficient explanation for this V8 no-switch
  condition; it does not identify a unique downstream cause or establish a
  production circuit.
- **Specification status:** not evaluated. The P1 engineering gate remains
  running.

Authoring-session helpers, registry state, skills, memory, and other
out-of-directory material are excluded: none is circuit evidence. The public
directory is closed by `SHA256SUMS` and checked by `verify.py`.

## Reproduce the checks

From this directory, with the parent V8 package present:

```sh
python3 verify.py
sha256sum -c SHA256SUMS
```

To rerun the portable deck, use a compatible IHP SG13G2 installation, set
`PDK_ROOT` to its root, and invoke ngspice from this directory. A rerun is new
evidence and is not required to verify the retained native result.

No signoff, tape-out readiness, entropy qualification, or foundry acceptance
is claimed.

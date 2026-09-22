# Nominal BGR586 full-hot diagnostic — comparison passed

The fresh full1.02µs hot diagnostic completed in922.386s and passed the
prospective comparison contract. Both comparator decisions are LOW at all
three required late samples. This is one controlled model-level experiment,
not calibrated yield, all-block mismatch Monte Carlo or physical adoption.

| Check | Status | Evidence |
| --- | --- | --- |
| Numerical completion | passed |6522 finite rows,18 columns,0–1.02µs; no classified solver errors |
| Strict early-wave parity | passed | All1304 rows through200ns,18 columns and decoded header/bytes exact;541575bytes, SHA142039d3ac6e9583c500cb2c1785fabc96c675c2b0f19939a719b6b3cfc08ce4 |
| Non-BGR random draw | passed |8670 ordered observations before/after match the completed hot baseline OP, including six CMIM inner parameters |
| Replacement BGR | passed |2842 ordered observations before/after equal declared nominal586 values; not a random BGR sample |
| Legacy non-BGR anchors | passed | All24 unchanged; three original BGR observations deliberately change |
| Actual and legacy sampling | passed | Last three soft/hard comparisons LOW/LOW; policies agree |
| Original600s hot run | failed |600.236s watchdog, reported620.2ns; retained unchanged |
| Original219ns fixture | failed | Eight inherited out-of-window measurement requests; separately audited saved prefix remains usable under its explicit contract |
| Model-limit warnings | failed warning screen |14560 resistor-vmax warnings and one NaN during OP/initialization; no warning after Initial Transient Solution; no model-validity waiver |
| New calibration, population, physical fidelity and new-layout PEX | not run | Different nominal reference level; inherited physical limitations remain |
| Source/model/deck modification to obtain completion | not applicable | None; only fresh run paths and external watchdog differ from the600s deck |

Soft actual-clock+20ns samples are approximately3.194µV, with input
differential−3.834mV. Hard samples are approximately3.286µV, differential
−39.486mV. These are **simulated** values at fixed24.5mV shunt input, seed71002,
soft/hard codes136/154,125°C and5MHz. Rail/stimulus/solver/model/source hashes
are in the provenance; no parameter was tuned during this diagnostic.

The raw warning array has14593 entries because32 finite parameter names
containing `nan` also match the historical substring reader. The separate
word-boundary/phase audit classifies7281 warnings before the inventory,
7280 during transient initialization, zero inside the inventory and zero
after Initial Transient Solution. Original arrays and logs remain unchanged.
No warning count is a claim of damage or safe operating area.

## Built against and evidence

Pinned ngspice46, IHP SG13G2
`84374023ee8b4b126bebbba67fcbada0a9c0ff0b`; runtime manifest
`5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0`,
config/image`ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2`.
The runner compares complete runtime/model identity against the bound baseline.
Source586 remains nominal; SENSE/TRIP sources and their full random draw are
unchanged. The original deck is byte-identical after run-name normalization.

```sh
G1_CPUSET=5 G1_CPUS=1 G1_MEMORY=4g flow/run.sh python3 designs/g1-guardian/blocks/g1_trip/sim/run_bgr_full_hot_probe.py --run-id joint-bgr586-fullhot1200s-20260922-a --image-id sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0 --timeout-s 1200
```

The fresh1200s limit was declared before launch, based on the finite prefix;
the earlier job was not extended. One CPU was affinity-bound following a
fresh CPU/RAM/effective-quota/inode/growth gate. Memory is reservation-only in
rootless-v1, not an enforced limit. No automatic retry or batch followed.

[Independent completed-run audit](resume-server-20260922/joint-bgr586-fullhot1200s-audit.json)
binds summary SHA912780d22f0b83b39b3efc1d3aab0389df5e4a130b7a2acf452632fb053b303e,
decoded full-wave SHA3739c8b9ed8e854cb4d66c031e120c45f7781d15403f95defc56755500e81df7,
and the original log. The [portable artifact receipt](resume-server-20260922/portable-runs/joint-bgr586-fullhot1200s-20260922-a/artifact_manifest.json)
exports4,905,428bytes and retains7,360,107bytes of bulk artifacts separately.
The earlier [failed-prefix result](BGR_PREFIX_OBSERVATION_20260922.md) and
[substitution results](BGR_SUBSTITUTION_TRANSIENT_20260922.md) remain historical
evidence, not superseded failures. Recalibration is needed before interpreting
this changed nominal level as a threshold-accuracy improvement.

Commit-review correction: exact artifact/hash/privacy and92 tests passed.
The strict staged whitespace check **failed** one trailing-space context line
in the frozen `declared_runner_difference.diff`; the artifact was preserved
byte-exact. The initial milestone commit message incorrectly said whitespace
checks passed. This correction does not change any simulation evidence.

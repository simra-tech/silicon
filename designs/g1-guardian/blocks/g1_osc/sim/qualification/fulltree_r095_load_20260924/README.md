# OSC r0.95 clock-tree load fixtures

These exact simulation inputs replace the 50 fF oscillator test load with a
94-buffer clock tree and 1,197 static Liberty terminal capacitances. They are
not a full-die post-layout simulation or a qualification of all sink functions.

## Built against

| Item | Identity | Established by |
| --- | --- | --- |
| IHP SG13G2 | `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` | Runtime PDK revision and 32 held model-file hashes in run manifests |
| ngspice | 46, KLU | Runtime `ngspice --version` recorded in manifests |
| Image manifest | `sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0` | Pinned amd64 runtime provenance |
| Image config | `sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2` | Flow image identity check |
| OSC capacitance extraction | `8efd7a09faf173da8604a219f73fd3ea5ec2508618d8361a050770c099d8b1c5` | Exact `common/osc.spice` SHA256 |
| KLayout / KPEX | 0.30.9 / 0.3.12 | Pinned extraction-runtime identity; neither is invoked by these transient decks |

## Scope

The load includes 2,643 resistors and 10,018 capacitor entries from the clock
network representation, including zero-valued and reverse-coupling bookkeeping.
Static sink capacitance totals are 3.47228213 pF nominal and 3.24445625 pF slow/hot.
External coupled nets are held quiet. The OSC-to-root assembly segment is an
estimated 459.7558 ohm / 60.3853 fF pi network, not an extracted full-chip path.
The waveform observes OSC, root input/output and the first 16 buffer outputs:
19 signals, not the functionality of 1,197 sinks.

The four decks retain the same numerical options and six-microsecond transient.
Within each tuple, only trim DC bits change. Nominal uses 1.2 V / 27 C;
slow/hot conditions are stated exactly in its deck. No PDK model or rule is edited.

## Reproduce inputs and a bounded simulation

From the repository root, create a new output directory (existing directories
are rejected):

```sh
python3 designs/g1-guardian/blocks/g1_osc/sim/qualification/fulltree_r095_load_20260924/prepare_run.py nominal_code0 build/g1_osc/fulltree-nominal-code0
```

After checking resources and assigning one CPU, use the pinned container:

```sh
G1_CPUSET="${G1_CPUSET:?set an allocated logical CPU}" G1_CPUS=1 G1_MEMORY=4g \
G1_EDA_IMAGE=sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2 \
G1_EXPECTED_IMAGE_ID=sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2 \
G1_EDA_PLATFORM=linux/amd64 G1_WORKDIR=build/g1_osc/fulltree-nominal-code0 \
flow/run.sh timeout 600 ngspice -b receiver.cir
```

Other cases are `nominal_code8`, `slowhot_code0`, and `slowhot_code15`, each with
a distinct new destination. `INPUTS.json` binds exact input bytes. Preparation
does not launch ngspice or establish a circuit pass. Six preparation tests passed:

```sh
python3 designs/g1-guardian/blocks/g1_osc/sim/qualification/fulltree_r095_load_20260924/test_prepare_run.py
```

## Coverage boundaries

All four six-microsecond simulations passed their scoped waveform observers.
These are simulated values, not measurements:

| Tuple | Trim code | Simulated OSC frequency |
| --- | --- | --- |
| Nominal | 0 | 13.547888408 MHz |
| Nominal | 8 | 9.436194721 MHz |
| Slow/hot | 0 | 10.447416283 MHz |
| Slow/hot | 15 | 5.834252847 MHz |

Each tuple's tested pair brackets 10 MHz. This does not establish an exact
10 MHz code, a frequency-error tolerance, or monotonicity of untested codes
under this load. The independent saved audit binds original inputs, model
hashes, logs, complete 23-column waveforms, bounded completion and all 19
observed signals. Exact manifests and waveform hashes are in `results/`.

| Check | Status |
| --- | --- |
| Nine exported input files identical to original fixture bytes | passed |
| Four preparation cases and two refusal controls | passed |
| Four scoped waveform observers and two endpoint brackets | passed |
| Loaded full-tree re-enable transient | not run in this evidence set |
| Full loaded PVT / mismatch campaign | not run |
| All 1,197 downstream sink functions | not run |
| Extracted full-chip OSC-to-root route | not run |
| Physical jitter, hardware measurement, final integrated qualification | not run |
| New population yield credit from these deterministic load fixtures | not applicable |

Simulation results and their exact waveform hashes are recorded separately;
waveforms are bulk artifacts, not duplicated in this directory.

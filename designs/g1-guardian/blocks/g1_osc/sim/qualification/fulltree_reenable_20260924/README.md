# Loaded oscillator re-enable

Two simulated re-enable cases passed: nominal trim8 and slow/hot trim0.
Each exact deck runs to10us, turns enable off at3.01us and on at5.001us.
All19 observed nodes have at least four rising edges in both the1.8–2.9us
and7–9.8us windows, and zero rising edges during3.1–4.9us.
This is the same approximate clock-tree load described in
`../fulltree_r095_load_20260924/README.md`:94 buffers and1197 static sink
capacitances, with an estimated assembly pi segment. It is not full-die
functional verification or an extracted complete OSC-to-root connection.

## Built against

| Item | Identity | Established by |
| --- | --- | --- |
| PDK | IHP SG13G2 `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` | Runtime revision and32 unchanged model hashes in manifests |
| ngspice |46 with KLU | Runtime version in manifests |
| Image manifest | `sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0` | Pinned amd64 runtime |
| Image config | `sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2` | Flow image identity |
| KLayout / KPEX |0.30.9 /0.3.12 | Pinned extraction runtime; not invoked by these decks |

## Reproduction

From the repository root:

```sh
python3 designs/g1-guardian/blocks/g1_osc/sim/qualification/fulltree_reenable_20260924/prepare_run.py nominal build/g1_osc/reenable-nominal
```

The helper checks all shared input hashes, refuses existing destinations and
installs the exact completed-run deck. Use `slowhot` with a new directory for
the second case. After allocating one CPU and checking memory/storage:

```sh
G1_CPUSET="${G1_CPUSET:?set an allocated CPU}" G1_CPUS=1 G1_MEMORY=4g \
G1_EDA_IMAGE=sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2 \
G1_EXPECTED_IMAGE_ID=sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2 \
G1_EDA_PLATFORM=linux/amd64 G1_WORKDIR=build/g1_osc/reenable-nominal \
flow/run.sh timeout --kill-after=5s 600s ngspice -b receiver.cir
python3 designs/g1-guardian/blocks/g1_osc/sim/qualification/fulltree_reenable_20260924/audit_wave.py build/g1_osc/reenable-nominal/receiver.dat --vdd 1.2
```

For slow/hot use `--vdd 1.08`. Inspect solver exit and logs as well as the
waveform; waveform-only acceptance does not establish clean solver completion.
Raw waves stay in bulk storage; exact hashes are preserved in both manifests.
`saved_audit.json` binds inputs, runtime, clean logs, waveforms and completion.

| Check | Status |
| --- | --- |
| Two full10us transients and19-node re-enable observers | passed |
| Independent saved audit,13 checks per case | passed |
| Six saved-evidence positive/tamper controls | passed |
| Portable preparation tests, both cases and two refusal controls | passed |
| Full1197 sink functionality, loaded population, physical jitter | not run |
| Final integrated qualification and hardware measurement | not run |
| Population yield credit | not applicable |

No PDK model, circuit source, clock-load network or trim value was changed.
Only the enable waveform and transient stop differ from the preceding pilots.

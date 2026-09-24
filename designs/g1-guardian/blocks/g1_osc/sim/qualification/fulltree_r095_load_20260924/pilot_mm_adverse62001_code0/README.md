# Loaded receiver mismatch pilot: adverse seed 62001, trim code 0

This is one **simulated** 6 µs loaded-tree diagnostic leaf, not a population
qualification. With the pinned IHP SG13G2 open PDK and ngspice 46 using
SPARSE 1.3 as its active direct linear solver, the
saved run completed in 210.300617 s, exit 0. Its 23-column waveform has
30,546 rows through 6 µs; the oscillator root and 18 observed receiver nodes
each had 40 rising crossings. The root frequency was 10.563007757 MHz.
The 1197 downstream terminal loads are static capacitance approximations.
The assembly link is an estimated 459.7558 Ω / 60.3853 fF π sensitivity
network, not a fully extracted assembled path;
full-tree function, jitter, and timing are **not run**.

`INVENTORY.json` identifies the exact five input files. `manifest.json` is a
sanitized public derivative, not a byte-for-byte copy of the runtime manifest.
Three inputs are in this
directory; `clock_load.spice` and `.spiceinit` reuse byte-identical files from
the parent preparation directory. The saved stdout/stderr and the original
50 fF sample manifest are included. `evidence.json` records the independent
saved-data result, including exact original 269-parameter core draw and
760 deterministic clock parameters. The original 50 fF result is not
reclassified as loaded-tree evidence.

The raw `receiver.dat` is 16,189,910 bytes and is **not in the public repo**;
its SHA-256 is `66aad51b322f733f27d8736ddf97a6969f4806226e300b0d4ce4c3a306de6644`.
Thus the numeric waveform audit cannot be independently rerun from this
checkout alone. The unmodified PDK model libraries are also an external
prerequisite; their 32 file hashes are in `original_50fF_manifest.json`.

## Reproduce one leaf

From the repository root, stage a new working directory (do not reuse an
existing run directory):

```sh
pilot=designs/g1-guardian/blocks/g1_osc/sim/qualification/fulltree_r095_load_20260924/pilot_mm_adverse62001_code0
stage=build/g1_osc/fulltree-mm-adverse62001-code0
mkdir -p "$(dirname "$stage")"
mkdir "$stage"
cp "$pilot"/receiver.cir "$pilot"/mismatch.spice "$pilot"/stdcells.spice "$stage"/
cp "$pilot"/../slowhot/clock_load.spice "$stage"/clock_load.spice
cp "$pilot"/../common/.spiceinit "$stage"/.spiceinit
```

With the pinned container available, a resource-qualified single-CPU run uses
the exact 600 s watchdog and batch command:

```sh
G1_CPUSET="${G1_CPUSET:?set an allocated logical CPU}" G1_CPUS=1 G1_MEMORY=4g \
G1_EDA_IMAGE=sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2 \
G1_EXPECTED_IMAGE_ID=sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2 \
G1_EDA_PLATFORM=linux/amd64 G1_WORKDIR="$stage" \
flow/run.sh timeout 600 ngspice -b receiver.cir
```

The deck uses the container-standard `/foss/pdks/ihp-sg13g2` model location.
The PDK revision is `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`; no
model card or rule deck was changed. This command is a reproduction recipe,
not a claim that the original raw waveform is bundled or that a new run was
performed for this milestone.

## Acceptance boundary

Only this one loaded leaf passed its scoped numerical and observed-oscillation
checks. The matched loaded populations require 220 distinct samples and 720
leaves: paired 10 MHz endpoint brackets for nominal/adverse 100 each, and
strictly monotonic 16-code curves plus brackets for selected 20. These
population checks are **not run to completion** here. Silicon measurement is
**not run**.

# Bounded G1_TOP runner

Latest scoped evidence (2026-09-22): the compact28µs actual analog C-PEX/RTL
hard-trip anchor [completed and passed](campaigns/INTEGRATED_ANCHOR_20260922.md).
The [six transition/readback regressions](campaigns/TRANSITIONS_BEHAVIORAL_20260922.md)
also passed with a behavioral front end. Earlier dated incomplete runs below
remain historical evidence. [Native integrated-prefix qualification](campaigns/NATIVE_PREFIX_20260922.md)
did not complete; the legacy simulator remains selected for integrated work.

New functional runs preserve full analog and state vectors in deterministic
gzip archives, with decompressed and archive hashes in the run manifest.
`check_campaign.py` can evaluate these archives without the build directory.
The generator rejects exported voltage/current vectors missing from an
explicit `.save` list before launch. Six archived transition fixtures were
independently rechecked with build-file access disabled; all passed.

`run_top.py` generates unique run tags by default and refuses to overwrite any
existing deck/log/manifest with the same tag. `--run-id` selects an explicit
suffix for reproduction. Existing simulation evidence remains unchanged.

`--timeout` limits each ngspice process in wall seconds (default 300). The
runner streams stdout/stderr directly to its log; when available, `stdbuf`
disables child C stdio buffering. A JSON manifest records actual subprocess
return code independently of timeout/interruption status. Five-second JSONL
snapshots retain resource use and the most recent simulator-reported reference
time; this time is not an assertion about accepted steps. Completed diagnostic
analyses print `rusage all`, including iterations and accepted/rejected points.
A timeout stops the process group and stops the requested case queue. OS-level
hard termination can still leave a manifest at `running`; it is not a pass.

`--analysis op` evaluates the initial analog operating point with the ordinary
XSPICE initial digital state; it does not validate configured RTL or power-up.
`--analysis prefix --tstop US` starts at zero and records only in-window
observations and the actual reached time. It does not execute the original
post-configuration/post-event measurements. Prefix waveforms use accepted
analog timepoints; saved review copies may be decimated. They are not analog
plus RTL restart checkpoints. `--analysis functional` retains the original
case measurements and is the default.

Process completion is distinct from functional acceptance. Diagnostic OP
acceptance requires a returned data row and VREF output, absence of detected
analysis errors, and exit zero. Prefix acceptance additionally requires the
reported end time to equal the request and a saved waveform with the expected
vectors, at least two finite data rows, nondecreasing time starting at zero, and
a final time that reaches the request. A launch failure is recorded separately
as `launch_failed` with a null child return code and the launch error. These narrow checks establish analysis
completion, not electrical specification compliance. Functional results require
separate review. Warnings, including recovered gmin steps, remain in raw logs.

Example from repository root (run IDs must be unused):

```
G1_WORKDIR=designs/g1-guardian/blocks/g1_top/sim flow/run.sh python3 run_top.py c --analysis op --timeout 300 --run-id example_op
G1_WORKDIR=designs/g1-guardian/blocks/g1_top/sim flow/run.sh python3 run_top.py c --netlist pex --analysis prefix --tstop 0.2 --timeout 300 --run-id example_prefix
```

For immutable image provenance, obtain the image ID using
`docker image inspect tapeoutbench-eda:latest --format '{{.Id}}'` and pass its
value as `--image-id`. The manifest records image ID as null if not supplied;
it does not infer image identity from a mutable tag. PDK commit, simulator
versions, input/deck/runner hashes and effective selected model settings are
also recorded.

Process-level watchdog tests (no PDK or circuit simulation):

```
python3 -m unittest discover -s designs/g1-guardian/blocks/g1_top/sim -p test_run_bounded.py -v
```

## Optional observation checkpoints (unqualified pilot)

`--checkpoint-us T1 T2 ...` inserts ngspice `stop when time = ...`, writes partial observations, then `resume` within the same process. These files cannot restart a terminated analog/RTL simulation. This option remains unqualified: the initial1µs integrated pilot with0.5/0.8µs requested stops (`...20260921T160232Z_62a38463`) timed out120s before either checkpoint, near1.8ns reported progress. Baseline runs do not enable it. A simple isolated stop/resume test and mixed-signal waveform parity are still not run; do not assume useful checkpoints were saved.

## Observation capture follow-up

The isolated RC stop/resume test completed, but the mixed-signal4µs behavioral-front pilot (`...164049Z_ed3805c6`) reports `Too many iterations without convergence` at its first requested stop, despite saving all three checkpoints and its final endpoint. Qualification **failed**. The uninterrupted reference (`...164131Z_193d8a45`) completes cleanly. Saved digital states agree; interpolated analog GATE differs by up to58.37mV. Comparison evidence is `campaigns/checkpoint_comparison_20260921/comparison.json`. This option remains disabled by default.

`run_stream.py` instead executes the same generated circuit as batch `.tran` with `ngspice -b -r transient.raw`. Complete binary records survive a terminated simulation; the untouched raw header may lack its final point count and its final record may be incomplete. The parser preserves only complete finite monotonic records and reports discarded trailing bytes. Four parser tests cover incomplete headers/trailing bytes, current names, nonfinite records and reversed time. Raw observations cannot restore analog integrator or RTL process state.

Initial stream `164538Z_648a2faf` failed because the Icarus library path was missing; later runs supply it. Behavioral-front stream `165437Z_bd880fb2` completes4µs and matches all original saved analog/state columns within4binary64 ULPs, consistent with reference text rounding. PEX stream `165151Z_34cb6ddb` times out360s, preserving2,203records through3.771112µs; its complete records likewise match the original PEX reference within4ULPs. The predeclared comparison allowance is8ULPs. This qualifies only saved-prefix parity; PEX endpoint qualification is still pending. A timed-out run is **not run to completion** regardless of prefix parity. Later runner versions compile an independent per-run RTL executable and copy their stimulus to avoid mutable shared build files.

PEX streaming endpoint follow-up `stream_20260921T165925Z_e2a0d65a` completes4µs in415.63s and all2,429rows of original saved analog/state vectors match within4ULPs. New independent RTL/stimulus-copy runner pilot `stream_20260921T170741Z_0eafde17` also passes4µs behavioral-front parity, with observations byte-identical to the earlier streaming pilot. The compact28µs in-range fault fixture is now being rerun with streaming; its endpoint and electrical acceptance are not yet established.


## Functional waveform completeness correction, 2026-09-22

`run_top.py` now saves configuration/cause vectors before `linearize` switches
to a plot containing only the selected analog vectors. `check_campaign.py`
requires the state endpoint, configuration/cause checks and a clean solver log.
The first behavioral compact fixture `...20260921T221520Z_672e1d7f` completed
its analog waveform but failed the state export (`fast_en` absent). Its initial
permissive assessment is retained and superseded by
`campaigns/behavioral_compact_20260921T221520Z_assessment_corrected.json`:
**failed**, required configuration/cause checks not run. It is not accepted.

Fresh corrected `...20260921T221716Z_dc63af92` passes all saved-vector checks,
including soft153/hard200 and hard cause. Its analog waveform hash exactly
matches the prior waveform; only export ordering changed. Simulated GATE<1V
occurs1.4004us after the fault by ngspice crossing measurement and1.42us at the
first exported grid point. This is a behavioral BGR/SENSE/TRIP front end with
actual RTL and GATE C-PEX, ideal oscillator, fitted output pads and modeled
external switch. It is not an integrated analog-chain PEX acceptance result.

`check_stream.py` evaluates the fixed compact c_mid source hash directly from
streamed observations: completion, arming, threshold codes, cause, latch,
GATE latency/hold and end current. It does not treat partial records as a pass.
Four distinct electrical-checker tests cover valid acceptance, missing state,
solver errors, incomplete endpoints, wrong configuration/cause and rearming.

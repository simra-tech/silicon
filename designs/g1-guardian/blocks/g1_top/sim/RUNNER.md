# Bounded G1_TOP runner

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

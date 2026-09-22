# Simulated gm4comp3 actual-chain pilots

Status: **failed residual qualification**, despite complete numerical execution
and passed declared guard checks. All84probes of seeds71001/71002/71012 completed;
all27observed parameters stayed exact within each sample. The actual flaggedBGR,
SENSE reference/bias buffers, full DAC switches and clocked comparators are
included. Supplies are ideal; pads/RTL and changed candidate PEX are not included.

| Seed | Programmed soft/hard codes | Frozen guards | Calibration residual |
|---|---|---|---|
|71001|158/226|passed12/12|passed6/6|
|71002|161/230|passed12/12|failed1of6: hard125°C/24.5mV|
|71012|163/229|passed12/12|passed6/6|

The guard codes above are independently corrected for nominalsoft30mV/hard40mV
targets. Neither channel clips. Soft guards are27/33mV; physical hardnominal204
maps to40.03019mV with36.02717/44.03321mV guards. These are inside the0–50mV input
contract. The original baseline nominalhard254/approximately50mV setting is a
different guard scope, so its guard failures cannot be attributed solely to the
geometry change. This is not a yield estimate from three samples.

## Preserved residual failure

Residual tests use the nearest room-temperature calibration-bracket midpoint,
not the corrected application guard codes. Seed71002 holds soft136/hard154 while
testing24.5/25.5mV at25/−40/125°C. Its25°C and−40°C lower points correctly read
both channels low. At125°C/24.5mV, all three late hard decisions remain high
(approximately1.199990974V), while soft reads low (approximately3.215µV).
The125°C upper point remains high as expected. This violates the frozen500µV
calibration-point residual check and must not be waived by the passed wider
guard bands.

| Seed71002 lower24.5mV point |25°C|125°C|
|---|---:|---:|
| Quiet hard differential |−44.6112mV|−40.1250mV|
| Last hard sample differential |−36.0630mV|−29.3152mV|
| Hard decision |low, expected|high, failed|

These observations combine source drift, loaded dynamics and comparator offset;
they do not isolate one block as the cause. The original baseline71002 lowerhot
point read both channels high. The candidate corrects the observed soft decision
there but retains the hard failure. First-probe
[observed-parameter pairing](resume-server-20260922/joint-gm4comp3-p00-observed-pairing.json)
shows23unchanged-subcircuit parameters and unchangedBGR/TRIP source bytes; changed
SENSE geometry prevents a claim of identical whole physical samples or proof
about all unobserved parameters.

## Evidence and exact scope

[Complete audit](resume-server-20260922/joint-gm4comp3-three-completed-audit.json)
lists every guard/residual result and probe. Three parent and84leaf directories
are compactly exported alongside it, including exact arguments, archived
runners, tool/PDK/source/model identity and artifact hashes. No simulation was
discarded or retried to replace this electrical failure.

Each parent used `run_joint_calibration.py`, its one declared710xxseed,
`--guards --temperatures 25,-40,125 --sense-candidate mc-gm4-comp3-smoke20-b1-20260922-a
--hard-nominal-code 204 --solver sparse --leaf-timeout-s 600`.
Each fresh leaf used tightGear,0.2ns maximum step and0.52µs endpoint.
Candidate source SHA256 is
`baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877`.
ngspice46 and IHP SG13G2 revision
`84374023ee8b4b126bebbba67fcbada0a9c0ff0b` ran in image manifest
`sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0`.
Models and source geometry were unchanged throughout these three pilots.

The [complete-pilot forecast](resume-server-20260922/joint-gm4comp3-three-completed-forecast.json)
records actual retained gzip sizes and runtimes. A hypothetical remaining297
samples projects395.13core-hours, ideally32.93h at12or24.70h at16independent
one-thread workers. Mean-observed bulk plus portable/parent metadata and16live
wave overlap totals approximately6.37GiB. Per-leaf-maximum multiplication instead
projects12.22GiB bulk alone; neither is a statistical upper bound. Any further
work needs a declared characterization/remedy scope, source/fit disposition,
fresh resource gates and staged byte-growth guards. **No300sample qualification
is established or launched by this report.** Candidate layout/PEX, full-code
statistical DAC monotonicity, full joint temperature return and silicon
measurement remain **not run** in this pilot scope.

# Coordinated BGR candidate: nominal design-control evidence

The three authorized simulator leaves completed successfully. This is a
**nominal electrical-merit result, not MC, physical fit or adoption**.

The separate source is
`candidates/bgr_loop24_qref4_r253p465/bgr_loop24_qref4_r253p465.spice`, SHA256
`53513ab43c62ead3a4c171f5a026b165e2a0bfda2b5b0cb5b104a30aae33a4e2`.
Baseline SHA256 is
`72417e072003d2ce28a108c47ef6ac86927ce6c6f89f3a614f360165a31c9d77`.
The generator's manifest freezes all2842 ordered unique parameters and the
exact replication mapping. Removing950 added units and reverting six original
R2 length edits reconstructs every baseline byte. Model cards, other original
device geometries and the baseline source remain unchanged.

|Group|Original instances|Copies of each|
|---|---|---:|
|PTAT MOS|XM34–39,41,45,47,48,50,52,54|24|
|PTAT HBT|XQ56,62,67–76|24|
|PTAT resistor|XR16,23–26,77–86|24|
|VREF mirror|XM43,44,51|4|
|Qref HBT|XQ60|4|
|VREF feedback resistor|XR17–22|4|

All HBT units retain0.07×0.9µm geometry, Nx=1,m=1. All resistor units retain
their original full lengths except XR17–22, each fixed at53.465×1µm. That
single hardware coefficient was selected from a frozen nominal-only source
curve before candidate simulation, not from any sample outcome. Total device
counts are336 MOS,301 HBT (including9 unchanged dummies),399 resistors.

## Simulated results

TT,3.3V,R4=0; IPTAT held at ideal1V and VREF loaded by1pF. The temperature
sweep spans−40…125°C in5°C increments; the matched OP probes are at25°C.

|Metric|Result|Status|
|---|---:|---|
|Nominal TC, box range/VREF25/165°C|8.529821ppm/°C|passed ≤50 target|
|VREF25|1.045449584V|simulated|
|IPTAT25|4.106693994µA|simulated|
|Supply current25|317.573550µA|simulated|
|Power25 at3.3V|1.047992715mW|simulated, BGR only|
|All2842 pre/post-sweep parameter strings|exact equality|passed|
|PTAT288 active units, max relative IC change vs baseline|8.607×10⁻⁹|quantified nominal density preservation|
|Qref4 active units, max relative IC change vs baseline|1.934×10⁻⁸|quantified nominal density preservation|
|Sweep/OP VREF difference|−0.375nV|diagnostic agreement|
|Sweep/OP IPTAT difference|−4.23fA|diagnostic agreement|

Every active HBT probe explicitly passed area-factor=1 and original geometry
checks before dividing IC by0.063µm². The collector-current-density comparison
is not a foundry reliability limit or proof of spatially independent mismatch.
Baseline supply current was21.892569µA; the candidate increases total current
while preserving nominal per-unit currents. The VREF increase is about6.107mV;
the preliminary linearized sizing estimate was not substituted for this result.

The sweep used21.002s; baseline and candidate OP probes used0.380s and3.747s.
Each leaf had a120s watchdog and one allocated CPU, with4GiB reserved memory.
Source plus retained three-leaf files total2,734,214bytes before this report
and aggregate audits. No timeout or solver error was hidden.

## Model and physical limits retained

The25°C candidate OP has93 external-terminal pair exceedances of literal PSP
default MAX parameters. Unchanged0.5µm HV NMOS XM31 and XM33 see VGS about
3.256235V and3.300000V. The pinned process specification's3.3V/27°C statement
for HV NMOS applies to gate length≥0.6µm; this result does not resolve that
geometry/voltage concern or generalize the statement to125°C/3.6V. Literal
PSP defaults are not a substitute foundry reliability specification. Maximum
HBT external VCE at25°C is0.725277V; full reliability remains unqualified.

All three stderr records include a temperature-limiter NaN message followed
by completed dynamic gmin stepping. Resistor internal `vmax` warning counts
are0 in the nominal sweep,142 in baseline OP and2394 in candidate OP. Final
exports are finite; this does not erase warnings or identify their intrinsic
trial-state cause. [Voltage/model scope](VOLTAGE_MODEL_SCOPE_20260922.md)
retains the pinned process-document and model-parameter distinctions.

Baseline wiring CPEX was retained while added native device capacitances are
modeled. New layout/wiring/fill/contact extraction and legal whole-floorplan
fit: **not run**. The corrected resistor length/grid audit is not full DRC/LVS.
Startup, load-control, mismatch-draw qualification, independent MC, PVT,
stability/noise/PSRR and downstream calibration requalification on this source:
**not run**. The candidate and any die/floorplan change remain unadopted.

## Reproduction and evidence

[Aggregate audit](coordinated_design_control_20260922_r2.json) binds the exact
source/model/OSDI/init hashes, all numerical checks and warning counts. Its r1
pre-warning-summary snapshot is preserved. Raw evidence resides in
`runs/bgr_loop24q4_nominal_20260922_r1/` and
`runs/bgr_loop24q4_probe_20260922_r1/`; manifests retain deck/source/tool hashes.

Pinned ngspice46, x86_64; image config SHA256
`ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2`;
PDK commit84374023ee8b4b126bebbba67fcbada0a9c0ff0b. Existing qualified settings
remain `gmin=1e-15 abstol=1e-14 reltol=1e-5 vntol=1e-7`; no tolerances/cards
were altered. Regeneration refuses existing output directories.

```sh
python3.11 designs/g1-guardian/blocks/g1_bgr/sim/qualification/prepare_coordinated_candidate.py
G1_CPUS=1 G1_CPUSET=6 G1_MEMORY=4g flow/run.sh python3 designs/g1-guardian/blocks/g1_bgr/sim/qualification/run_campaign.py --run-id bgr_loop24q4_nominal_20260922_r1 --image-id sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2 --suite nominal --all-fingerprints --pex-source designs/g1-guardian/blocks/g1_bgr/sim/qualification/candidates/bgr_loop24_qref4_r253p465/bgr_loop24_qref4_r253p465.spice
G1_CPUS=1 G1_CPUSET=6 G1_MEMORY=4g flow/run.sh python3 designs/g1-guardian/blocks/g1_bgr/sim/qualification/run_coordinated_probe.py --run-id bgr_loop24q4_probe_20260922_r1 --image-id sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2
python3.11 designs/g1-guardian/blocks/g1_bgr/sim/qualification/analyze_coordinated_stage.py --nominal-run bgr_loop24q4_nominal_20260922_r1 --probe-run bgr_loop24q4_probe_20260922_r1 --output designs/g1-guardian/blocks/g1_bgr/sim/qualification/coordinated_design_control_20260922_r2.json
```

Reproduce into fresh IDs/paths after allocated resources and a fresh quota
gate; do not overwrite the retained runs. No additional campaigns are
authorized by these commands or this report.

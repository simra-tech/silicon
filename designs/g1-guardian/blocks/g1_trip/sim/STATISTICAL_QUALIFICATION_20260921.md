# TRIP statistical harness qualification, 2026-09-21

## Status and numerical qualification

**The default-tolerance comparator offset results are numerically unqualified.**
Successful solver completion, repeatable random parameters and identical repeated
runs do not establish accurate near-boundary decisions. This applies to the new
`cmp-fine-pilot`, repeat and second-sample datasets. The historical comparator MC
at 0.75 V common mode remains archived; its offset accuracy has not been
requalified under the stronger numerical checks below. It must not be used as a
qualified joint-threshold yield distribution.

New runs archive exact decks, runner snapshots, source/model SHA256 hashes,
ngspice version, image ID, seed, watchdog result and all output waveforms. The
schematic explicitly enables MOS mismatch. Statistical sources are not paired
between different circuit topologies merely because they use the same seed.

The core fixture uses two equal 1 kΩ/1 pF input networks, symmetric differential
voltage around the declared average common mode, a 10 MHz clock with 0.2 ns edges,
and 10 fF output loads. A −20 to +20 mV staircase has 0.1 mV increments, one per
clock. All 401 decisions are sampled 20 ns after the rising strobe. This source
fixture is not the real 25 kΩ conditioner and DAC interface.

Seeds 61001 and 61002 each completed twelve traces: 0.5/0.75/1.0 V common mode at
25/−40/125/25 °C. Each took approximately 136 s on the x86 image. Twelve observed
MOS random parameters remained fixed across the conditions. Seed 61001 repeated
in a separate process with bit-identical fingerprints and all three 25 °C output
traces; its return to 25 °C was also exact. These facts qualify reproducibility,
not the accuracy of the resulting offset estimates.

## Numerical experiments on seed 61001

The nominal/default settings use trapezoidal integration and ngspice's default
tolerances. The stronger settings use `reltol=1e-5`, `vntol=1e-7`,
`abstol=1e-14`; integration method is explicitly recorded for each case.

| Fixture/settings | Average CM | Decision transition or ambiguity interval |
|---|---:|---:|
| x86, default, maximum step 1 ns | 0.5 V | 5.0–5.6 mV, non-monotonic |
| x86, default, maximum step 0.2 ns | 0.5 V | 5.1–5.5 mV, non-monotonic |
| ARM46, default, maximum step 1 ns | 0.5 V | 5.3–5.4 mV, monotonic |
| x86, default, maximum step 1 ns | 1.0 V | 19.2–19.3 mV, monotonic |
| ARM46, default, maximum step 1 ns | 1.0 V | 16.7–19.3 mV, non-monotonic |
| x86, tighter tolerances + Gear, 0.2 ns | 0.5 V | 5.3–5.4 mV, monotonic |
| ARM46, tighter tolerances + Gear, 0.2 ns | 0.5 V | 5.3–5.4 mV, monotonic |
| x86, tighter tolerances + Gear, 0.2 ns | 1.0 V | 15.3–15.4 mV, monotonic |
| ARM46, tighter tolerances + Gear, 0.2 ns | 1.0 V | 15.3–15.4 mV, monotonic |
| ARM46, tighter tolerances + Gear, 0.1 ns | 1.0 V | 15.3–15.4 mV, monotonic |
| x86, tighter tolerances + trapezoidal, 0.2 ns | 1.0 V | 15.3–15.4 mV, monotonic |

The default ARM comparison differs by only 2.98e−19 V in one observed threshold
perturbation, yet four of the 1203 sampled logic decisions differ. Therefore it
failed near-boundary numerical agreement. The newer tight comparisons agree on
all 401 logic decisions at each selected common mode. Both tolerances and method
changed in the first stronger experiment; the improvement cannot be attributed
to Gear alone. The tight-tolerance trapezoidal control agrees with Gear on all 401 decisions; maximum analog sampled-output difference is 1.40 µV. The step refinement differs by at most 0.70 µV and the tight architecture comparisons by less than 0.3 pV. `qualification/comparator_numerical_assessment_20260921.json` and `analyze_cmp_numerics.py` preserve the complete 401-sample comparisons. These are selected nominal-temperature checks, not blanket numerical qualification.

ARM46 uses image `g1-sim-arm64:20260921`, content ID
`sha256:ab853b72c0b95f467d562afc77b09cfb7093a87910e26bf671ad46566dadd82e`,
with `/opt/ngspice-46/bin` first in PATH. PDK source hashes are recorded in each
run, and native OSDIs are separately compiled. This experiment does not qualify
the native runtime for other blocks or the integrated chip.

## Full-switch DAC pilot

`run_dac_qualification.py` includes both complete DAC strings, all switches and
level shifters, actual SENSE VREF buffer, conditioner and comparator loads. All
schematic mismatch flags remain enabled; input code drives use the actual 1.2 V
logic rail. Ideal BGR voltage/PTAT sources remain in this V14 fixture.

No full all-code statistical pass has been obtained. The original pilot lacked
two saved vectors and timed out after 120 s; its log remains failed evidence.
The corrected sparse-code pilot produced five valid DC points before timing out.
Repeated OP and continuous DC code sweeps, a both-comparators-reset diagnostic,
and a comparator-omission diagnostic all exhausted the 120 s bound. The latter
is a convergence isolation experiment, not an accepted reduced interface. The
first omission-script attempt failed its source assertion before simulation and
is explicitly recorded as not run. A full string/level-shifter nodeset diagnostic
also timed out. No model cards or device dimensions changed.

Progress logs show only a few code points reached before the bound. This cost
prevents a defensible runtime estimate for a complete 20/100/300 all-code campaign
until the DC harness is qualified. Historical string-only MC cannot substitute
for full-switch mismatch or hot leakage.

## Actual joint-chain pilot

`joint-cal-pilot-20260921-a` uses BGR PEX with explicit flags, canonical corrected
SENSE schematic and complete TRIP schematic, all in one sampled circuit. The BGR
snapshot SHA256 is `944aaf94b9a005718abd0ebd92956acc99e8cb7a23ec8556d406736f4e8ef6f9`.
Its actual IPTAT output drives SENSE; the standalone BGR's 1 V clamp is removed.
HBT, both MOS families, resistors and capacitors use mismatch libraries. Seed
71001 at 25 °C, soft code 127, shunt 25 mV completed 0.52 µs in 81.1 s. All three
late soft decisions were high. This is an interior calibration probe, not a
completed calibration or a yield result. A tighter/Gear probe is retained under
a separate run ID for comparison.

A bracketing calibration must establish opposite decisions at codes 0 and 255,
use the same frozen sample for every probe, reject ambiguous late decisions,
verify adjacent codes around the final crossing, and explicitly saturate any
correction applied to nominal soft/hard settings. Both comparators require their
own crossing; no shared offset is assumed sufficient. Full-code monotonicity,
calibration across temperature and actual headroom remain unresolved.

## Remaining work, not run to completion

Qualified fine PEX comparator MC, 20/100/300 qualified comparator distributions,
edge/duty/receiver-time sweeps, complete switch-tree/hot-leakage all-code MC,
major-transition settling, complete joint bracketing calibration, frozen
calibration over temperature/common mode/supply, and joint 20/100/300 samples are
**not run** or **not run to completion** as specified above. No statistical yield
claim follows from these pilots.

## Later actual-chain calibration progress

The preceding incomplete-pilot status is superseded only within the scope below.
`run_joint_calibration.py` now brackets soft and hard comparators independently
at an exact25mV shunt using code0/255 endpoints and eight binary probes, requires
three agreeing late decisions at every probe, checks all27 observed sampled
parameters against the first probe, and checks monotonicity of selected codes.
Four arithmetic unit tests cover independent corrections, sign, rounding and
signed-byte/unsigned-DAC saturation. Full-code V14 monotonicity remains **not run
to completion**.

Seed71001 in `joint-calibrated-pilot-20260921-a/` completed ten calibration probes:
soft crossing[145,146], hard[163,164]. The independent corrections are+18/+36;
applying them to nominal153/254 programs171/255, with **hard-code clipping**.
All27 observed fingerprints match exactly. This is a simulated actual-chain
headroom failure, not an ideal SENSE-only estimate. Frozen system-band and
half-millivolt residual checks at25/−40/125°C are running; incomplete checks do
not count as passes. Twenty baseline samples are now scheduled across this
pilot and `joint-calibrated-smoke-b1-20260921-a` (71002–71011),
`joint-calibrated-smoke-b2-20260921-a` (71012–71020). The latter two campaigns
are running. The100-sample expansion and300-sample campaign are **not run**.

Each tight-Gear probe has maxstep0.2ns, duration0.52µs and a300s bound. Observed
cost is approximately125–150CPU seconds/probe; ten calibration plus18 frozen
checks forecast1.0–1.2CPU hours/sample. At four available cores,100 samples would
need about25–30hours before ambiguous/failed samples or extra qualification.
These are forecasts, not completed work. Longer settling, joint common-mode and
supply grids remain **not run to completion**.

An isolated headroom candidate is running for seed71001 under
`joint-headroom-pilot-20260921-a`: conditioner ratio3/8, DAC taps191…446 and
nominal soft115/hard191. It retains530 resistors and instance ordering; the
fractional pedestal offset is0.25LSB. The exact nominal calibration code is
`0.25 + 3975 * 0.025 / 1.04 = 95.8028846`; hard191 corresponds to49.9069mV under
ideal nominal transfer. No canonical source, default register contract or
specification is migrated. Paired fingerprints, full calibration and guards
must be assessed before claiming a benefit. Candidate three-sample results are
**not run to completion**.

## Standalone comparator cell PEX statistical qualification

The documented revision1 standalone comparator cell extraction is converted
without deleting its109 coupling capacitors; all30 MOS fingers receive explicit
`mm_ok=1`. The converter retains the existing PEX modeling convention for W/L,
ng and m, with substrate tied to vss and AS/AD/PS/PD omitted. This is not new
macro extraction or macro-routing coupling evidence. PDK local threshold and
mobility terms scale with total device area, whereas W/L perturbations are
absolute per-instance draws. The independent-finger PEX distribution therefore
is not interchangeable with lumped schematic variation; equal seeds across
those netlists do not establish paired physical samples.

At CM0.75V, tight trap/Gear and maxstep0.2/0.1ns, the nominal cell reproduces the
same81 sampled decisions and an ambiguous0.25–0.60mV interval. This is a
reproducible ambiguity, not a unique precise offset. Seed62001 retains32 sampled
parameters across25/−40/125/25°C and exactly repeats its first25°C trace. The
25°C staircase ambiguity is−8.3…−8.0mV with trap and−8.3…−7.8mV with Gear;
finer0.1ns steps retain both respective intervals. Thus a0.2mV method envelope
persists and must accompany characterization. An independent repeat matches
all401 sampled voltages exactly. Native ARM46 matches fingerprints and all401
logic decisions, with maximum sampled analog difference14nV. Seed62002 gives
a distinct+1.3…+1.6mV interval. Evidence directories use prefix
`cmp-cellpex-{nominal,mc}` under `qualification/`.

A constant-input late-decision bisection was also implemented. The first three
`cmp-cellpex-steady-*-20260921-a` attempts failed their control-expression
harness and are preserved as failed evidence. The corrected
`cmp-cellpex-steady-mc-trap-20260921-b` completes numerically in6.17s with the
same32 parameters, but at−8.125mV its three late outputs are low/high/low. It
therefore rejects a unique bracket; this result does not qualify a faster
single-offset MC campaign. The observed ambiguity is not solely staircase
input history. Qualified20/100/300 cell-PEX offset distributions remain
**not run**. No precise statistical yield follows from these two samples.


### Input-range qualification limit

The specified SENSE range is0–50mV. Every55mV shunt probe in these baseline and
headroom-candidate campaigns is therefore an **outside-contract diagnostic**.
The driver's raw `guards_status` combines27/33/45/55mV checks and must not be
read as full-band acceptance:27/33/45mV are within range, whereas nominal50mV
hard threshold plus10% requires an unsupported55mV input. A complete in-range
hard robust band requires a nominal threshold at or below45.45mV, with additional
trim-code headroom. Candidate hard191 preserves the nominal50mV transfer target
for characterization; it does not extend the specified SENSE input range.
`analyze_joint_calibration.py` records this limit and identifies all out-of-range
probes, including legacy summaries that predate explicit per-probe labels.
Supported lower hard settings and their full in-range bands are **not run**.

## Campaign paused before server transfer

At the user's requested pause,35leaves across the three baseline campaign drivers
and one candidate driver had run:32completed numerically and3hit their existing
300s watchdog. Baseline71001 retainedp00–p17(17complete pluscold55mVp17timeout);
71002/71012 each retainedp00–p05(5complete plusp05timeout); headroom71001 retained
p00–p04(all5complete, bracket unfinished). All simulation children finished or
reached their bound before stopped orchestrators were terminated. No leaf was
interrupted. No full joint sample completed all28checks;17of20baseline seeds
have not run. Empty71003/71013summary placeholders are not attempted samples.

The explicit expected-versus-observed guard assessment finds **hard no-trip
failure at45mV in both25°C(p12) and−40°C(p16)** for baseline71001, programmedhard255.
A preliminary progress message had mistaken uniform late decisions for guard
acceptance at25°C; this report corrects it.27/33mV guards pass at both temperatures.
55mV remains outside-contract diagnostic; its cold timeout is incomplete. See
`qualification/joint-smoke-paused-20260921-b.json`. Functional failures, numerical
timeouts, clipping and unfinished checks are retained separately.

Resume support preserves old driver/summary snapshots, requires exact cached
leaf arguments and refuses to overwrite incomplete existing leaves. Each parent
has a `PAUSE_REQUESTED` marker. Offline `--resume --rebuild-only` was exercised on
all four campaigns and launched no new analyses. Actual continuation is **not run**
until the user resumes. Three near-boundary timeouts qualify the earlier runtime
forecast: successful-probe throughput alone does not establish campaign completion
or numerical qualification on a faster server.

## Resumed runtime qualification and supported lower hard setting

After explicit user resume, the original three300s watchdog incompletions were
replayed under new IDs with a600s bound. A prelaunch check requires the normalized
deck, SENSE/TRIP/BGR source snapshots, entire model hash inventory, image and
simulator version to match the original. No solver tolerance, integration method,
step size or circuit parameter changes were made. All three replays completed:
71002p05 in151.60s,71012p05 in150.15s,71001cold55mVp17 in258.84s. All27 observed
sampled parameters match each sample's original successfulp00anchor. The timed-out
leaves did not reach their final parameter print, so no nonexistent fingerprint
from those incomplete leaves is claimed. Original300s attempts remain unchanged.

This demonstrates runtime variability and successful recovery, not a numerical
relaxation. Explicit `joint-recovery-map-20260921-b.json` aliases identify recovered
evidence while preserving old parent summaries and avoiding duplicate statistical
samples. New joint leaves now use a600s watchdog; existing completed leaves and
all their original bounds are reused. Failed electrical checks are not retried
into passes. The generic kickback runner's default remains300s. Accepted alias
arguments may differ only in run/watchdog metadata; six arithmetic and argument
preservation tests passed.

`joint-supported40-20260921-a` completed all six hard-band checks on sample71001:
nominalhard204 corresponds to40.0301887mV; its frozen+36correction programs240
without clipping. Both36.0271698mV no-trip and44.0332075mV trip guards pass at
25/−40/125°C, with three agreeing late decisions and exact27parameter equality
to baseline. These guards lie inside the specified0–50mV SENSE range. They show a
supported lower-setting result for this one simulated sample, not ensemble yield,
full common-mode/supply coverage, RTL calibration firmware or adopted defaults.

The original nominalhard254 calibration programs255 after clipping. Its45mV
expected no-trip guard fails at all three tested temperatures, including125°C
leafp20. Soft27/33mV guards pass at all three temperatures. Final residual checks
at24.5/25.5mV and candidate headroom calibration remain ongoing; partial evidence
does not count as completed V04. The derived waveform report
`joint-waveform-characterization-20260921-a.json` records actual loaded comparator
common mode and kickback at selected late cycles; a sampled differential alone
is not substituted for the latched decision.

## Second explicit pause checkpoint

The owner paused work with all four active leaf watchdogs recording interruption
and all parent drivers exiting through stop markers. No simulation remains
running. Retained joint evidence contains70 unique leaf attempts:63 numerical
completions,3 original300s watchdog incompletions and4 owner interruptions. These
include recovery and supported-setting runs, not70 independent statistical
samples. Of20 scheduled baseline seeds,5 were attempted and15 are not run; no
sample has completed all28 calibration/frozen probes.

The four interruptions are not electrical or solver failures. Earlier raw leaf
summaries retain their original failed label; watchdog records and the final
derived assessment `qualification/joint-paused-20260921-1713-b.json` distinguish
not run to completion. Baseline71001 residual probes pass at25/−40°C; its hot
24.5mV probe is interrupted and hot25.5mV is not run. Baseline71002 completes
calibration with independent corrections−2/+16 and hard clipping; one frozen
guard completes, the next is interrupted. The headroom candidate retains seven
completed calibration probes and one interruption, with no final bracket.
The six supported40mV guards reported above are complete. No100/300-sample
campaign or proposed combined compensation/matching candidate has run.

## Resumed interruption recovery — 2026-09-22 local session

Four owner-interrupted leaves were recovered under separate
`joint-pause1713-recovery*-20260922-a` IDs with the same600s bounds. Exact
normalized deck, source snapshots, model inventory, image and simulator checks
passed before launch. All four completed in150.31–155.01s; all27 observed sampled
parameters match their preserved sample anchors. Original interrupted records
remain untouched. `joint-recovery-map-20260922-c.json` adds validated aliases to
the earlier three timeout recoveries; no sample is counted twice.

Baseline20 and the isolated headroom pilot resumed from cached completed probes.
Sample71012 now brackets soft[158,159],hard[174,175], giving corrections+31/+47;
its original nominal254 hard setting clips to255. Frozen checks remain pending.

The driver now accepts an explicit `--hard-nominal-code 204` for new supported
setting campaigns. It preserves the same independent bracketing and saturated
calibration arithmetic, evaluates exact±10% hard guards within0–50mV, and
records per-sample guard definitions. Default254 and all original campaigns
remain unchanged. Analyzer interpretation follows those recorded definitions.
Seven focused arithmetic/recovery tests passed, including unchanged correction
between254 and204 and removal of clipping for the known71001 case. A new
100-sample supported-setting campaign has not run; no default adoption or yield
claim follows from this implementation.

### Resumed numerical qualification (22 September local date)

Baseline physical sample71002 completes all28 probes. Its hot125°C,24.5mV
fixed-calibration check fails; other five fixed-calibration checks pass. This is
an electrical residual failure, independent of baseline hard254 clipping. The
failure remains included when its exact calibration evidence is reused at the
supported hard204 setting. Baseline71001 retains its three45mV no-trip failures.

The first controlled KLU replay,`joint-klu-calibration71001-20260922-a`, changes
only the linear solver. Exact normalized-deck/source/model/image/engine checks
pass; all27 sampled parameters and both comparators' three late decisions agree.
The saved0.52µs traces are compared on52001 points: maximum difference0.117µV,
with analog input/threshold nodes below0.001µV. Printed pre/kick/sample measures
are identical. Cold supported40mV no-trip replay also agrees (all saved nodes
within0.003µV). Hot and second-seed residual comparisons are still running under
`joint-klu-guards-residual-20260922-a`. Neither a shorter endpoint nor a global
KLU qualification follows. Full traces, transitions and differences are retained
in each`solver_comparison.json`; concurrent loads limit timing comparisons.

V14 actual-BGR/reset KLU9OP pilot passes with all31 parameters frozen at three
temperatures and all9 printed OP rows identical to sparse. Runtime73.53s versus
96.89s for sparse is a single controlled fixture observation. The full256code
sparse sweep still times out120s with no final transfer table; full-code KLU
and statistical monotonicity are not run. V15 tight-trap cellPEX20-sample smoke
has started with62001–62010 at25/−40/125°C; numerical completion, bracketing and
nonmonotonic cases are recorded separately. No default-tolerance offset MC is
rehabilitated by these new runs.

The supported204 reuse harness requires a fresh exact normalized-deck, source,
model, image and engine preflight for every referenced completed analysis. Each
logical leaf records the original evidence run; it is not a new simulation.
Only identical calibration/fixed-residual analyses can be reused. Changed-code
guards rerun, except any already completed guard that passes the same exact
preflight. Original timeout/interruption/electrical failures remain preserved.

### Migration pause,22September2026

All simulation jobs stopped at owner request, originals retained. Baseline20 has
525 numerically completed probes and17 complete28-probe samples. Two current
leaves were interrupted; remaining35 probes are incomplete. Supported204 SPARSE
reuse3 completes all84 logical probes (54 exact archived analyses and30 new
changed-code guards):all guard checks pass,71002/71012 residual failures remain.
Headroom candidate71001 completes28 checks with all guards/residual checks passed;
55mV upper guard remains outside specifiedrange, and otherselected samples unrun.

Fresh supported204 KLU batch contains274 completed solver probes,6 completed
numerical-failure leaves and1 owner interruption. Only6 samples have all28 solver
analyses complete. Failed OP/timestep cases involve BGR xbgr.xq55:71022 endpoints,
71024-p19,71025-p13,71026-p12,71031-p19.71031-p26 was interrupted and already showed
similarOP errors. This limits broad KLU MC qualification despite four selected
parity anchors. The raw driver's failed guard/residual status can include solver
failures; assess per-probe numerical completion before interpreting electrical
acceptance. No failed sample is dropped.

V15 first6 cellPEX samples complete all3temperatures.62007/08 hit300s after saving
25/−40°C cases; their125°C cases remain unrun. Individual-temperature cold/hot
qualification for62001 matches all32 parameters,401 sampled outputs and full
400901-point waveform comparisons exactly. Prepared partitioned continuation
retains partialattempts and every missingtemperature; it has not run. V14 chunked
all-code pilot and expandedheadroom samples also remain not run.

The instrumented KLU profiling replay `joint-rusage71021-code255-20260922-a`
reproduces its complete reference waveform exactly. Transient analysis184.313s
includes141.586s matrixload,17.8925s factor,4.9868s solve and7.70249s truncation.
This is one profiled source/sample. Recent valid-leaf runtime is retained in
`joint-runtime-migration-20260922-a.json`; earlier loadedperiods were muchslower,
and no newserver timing has been qualified.

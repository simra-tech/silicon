# Joint extracted BGR/T2F pilot, 2026-09-21

`runs/t2f_joint_cold_20260921_01` completed a **simulated** 32 µs PTAT
transient at −40 °C, typical process, VDDA=3.3 V and VDD=1.2 V. Both BGR
and T2F use their existing capacitance-only extracted netlists.

| Check | Status | Result |
|---|---|---|
| Solver endpoint and finite saved vectors | passed | 32 µs, 16,236 points, exit 0, 26.04 s wall time, no timeout |
| Frequency extraction | passed | 1.187810 MHz between rising edges 8 and 24 |
| T2F comparator HBT external VCE magnitude ≤1.6 V | passed | Maximum 1.036583 V over saved transient |
| Nominal joint-PEX calibrated temperature ±2 °C | passed at six independent points | Eight temperatures completed; 25/100 °C calibration frozen, maximum residual magnitude 0.903 °C |
| Joint mismatch smoke, linear calibration | **failed: 1/20 endpoint samples** | All 80 transients complete; seed 51010 gives −2.645 °C at −40 °C after its own 25/100 °C calibration |
| Larger and full-range statistical acceptance | not run to completion | Intermediate points are in progress; 100/300 samples and process/rail ensembles remain separate |
| Full rail/corner coverage | not run | This is one nominal-process cold pilot |
| Enable/disable, PTAT/REF transition, mismatch | not run | Separate campaigns required |
| All device terminal limits | not run | Only T2F HBT external VCE evaluated here |

Average VDDA current is simulated 49.898 µA, VDD current 0.191 µA, VREF
1.03854 V. Output extrema are −10.33 mV and 1.21882 V; these are recorded,
not interpreted as a full terminal-voltage acceptance check. The load is 50 fF,
IPTAT terminates at an ideal 1 V source, and real pad/clock loading is not included.

The historical `../postlayout/logs/ftemp_ptat_T-40.log` also contains a
completed cold PTAT result (1.202031 MHz), with **schematic** BGR and extracted
T2F. A statement that every previous cold block PEX case aborted is too broad.
The new joint extraction is a separate fixture; their differing frequency is
not a transient solver regression comparison on identical inputs.

Reproduce from the repository root with a new run ID:

```sh
G1_WORKDIR=designs/g1-guardian/blocks/g1_t2f/sim/qualification flow/run.sh python3 run_joint.py --run-id NEW_ID --image-id sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0 --temperatures=-40
```

The manifest records observed ngspice 46 and PDK commit
`84374023ee8b4b126bebbba67fcbada0a9c0ff0b`, image identifier, exact command,
input/model/runner hashes, watchdog and actual exit. The run uses the existing
Gear/tolerance settings and finite 10 ns enable edge. No model card, extraction,
or design source was modified. The 300 s per-case watchdog is a ceiling.


## Nominal joint temperature sweep

`runs/t2f_joint_temp7_20260921_01` adds −20, 0, 25, 50, 75, 100 and
125 °C to the cold pilot. All eight 32 µs transients complete. The frequency
slope from the 25/100 °C calibration is 4995.852 Hz/°C. At the six independent
points (−40, −20, 0, 50, 75, 125 °C), the maximum absolute residual is
0.903 °C. This is one nominal, mismatch-disabled physical sample at
3.3/1.2 V. It does not establish corner, supply or mismatch yield.

`analyze_calibration.py` requires all eight completed cases and preserves
per-temperature frequency, inferred temperature and residual in
`nominal_calibration.csv`, with acceptance status in `nominal_calibration.json`.
Reproduction uses the command above with `--temperatures=-20,0,25,50,75,100,125`
and a new run ID. Other explicit runner options select HBT/MOS/R/C process,
rails and transient endpoint; separate runs do not inherit calibration implicitly.


## Adverse cold extracted pilot

`runs/t2f_joint_slowcold_20260921_01` completes 40 µs at −40 °C,
HBT wcs/MOS ss/resistor wcs/capacitor typ, VDDA=3.0 V and VDD=1.08 V.
Execution **passed** (27.39 s, exit 0, no watchdog). Simulated frequency is
1.048937 MHz and maximum T2F comparator HBT external VCE is 1.024963 V,
passing the 1.6 V check. This completes one selected adverse fixture; it is not
the full corner/rail campaign or an explanation of the historical schematic
numerical abort. Exact corner/rail/endpoint arguments are in its manifest.


## Joint mismatch qualification and endpoint smoke

Twenty independent physical samples (seeds 51001–51020) completed all four
−40/25/100/125 °C points, **80/80** transients, with no numerical failure,
timeout or representative parameter drift. All MOS/HBT/resistor/MIM instances
in simulation-only copies receive the PDK `mm_ok=1` flag and mismatch libraries.
The HBT, MOS, resistor and MIM random parameter fingerprints remain fixed
across temperature and before/after transient. Repeating seed 51001 at 25 °C
produces byte-identical vectors; changing the seed changes every representative
randomized device class. PDK model cards and original extracted netlists stay
unchanged. Equal seed numbers in other netlists are not paired physical samples.

Linear calibration is independently fit to each sample at 25/100 °C and frozen.
**One of twenty samples fails ±2 °C at the independent endpoints:** seed 51010
has −2.644540 °C error at −40 °C and −0.766653 °C at 125 °C. The other 19 pass
these two points. `mc20_summary.json` and `mc20_samples.csv` preserve all samples;
`analyze_mc.py` regenerates them. This smoke count is not a qualified yield
claim. Intermediate temperatures, held-out samples, rail/process ensembles,
jitter and measurement-window quantization require separate evaluation.

A separate diagnostic applies the fixed inverse nominal-PEX temperature curve
after each sample's two-point calibration. `fixed_nominal_curve.json` preserves
the original eight nominal knots and source SHA-256; the curve is not refit to
mismatch outcomes. Piecewise-linear interpolation extends the outer segment
when a reading lies outside the nominal reading range. All 20 endpoint samples
pass under this **unadopted candidate**, with maximum magnitude 1.711021 °C.
The original linear-calibration failure is retained. `curvature_candidate.json`
and `curvature_candidate_samples.csv` record the alternative separately.
Four independent intermediate temperatures per sample (−20, 0, 50, 75 °C)
now complete **80/80** additional transients with no solver failures or
fingerprint drift. All pass ±2 °C using the original per-sample calibration:
maximum absolute residual is 1.609741 °C for linear calibration and
1.045282 °C for the unchanged nominal-curve candidate. These do not remove
the linear cold-end failure. `mc20_intermediate_summary.json` and
`mc20_intermediate_points.csv` retain every point. Their actual temperatures
coincide with nominal curve knots, although shifted MC readings exercise
interpolation between knots. A separate nominal between-knot probe is recorded
in `interpolation_probe.json`; no correction is refit to either dataset.
That probe completes all four new temperatures (−10, 12.5, 62.5, 112.5 °C).
Maximum absolute residual after the unchanged correction is 0.056068 °C.
It supports interpolation for these nominal points, without establishing an
error bound at every temperature or across process, supply and mismatch.

`run_mc_batch.py` executes independent samples in separate processes (up to 4),
with 1 ngspice thread per case and 300 s transient ceilings. It preserves each
case directory, driver log and batch ledger. Source snapshots identify the
runner used. Some earlier copied deck title comments retained the legacy cold
fixture description; actual `.temp`, source lines, solver logs and per-case
manifest values identify the executed conditions. Future runner titles now
report the actual arguments.

## Scoped native-runtime comparison

The larger ensemble uses the separately built native ARM ngspice 47 image
`sha256:ab853b72c0b95f467d562afc77b09cfb7093a87910e26bf671ad46566dadd82e`.
Before expansion, two seed-51001 anchors and all four temperatures of seeds
51002 and 51010 were compared against legacy ngspice 46. The latter includes
the known cold-end electrical failure. Model-library and realized netlist hashes
agree. Maximum frequency difference across these ten anchors is 15.397 ppm;
the two full-sample comparisons differ by at most 0.005437 °C after independently
performing the same calibration in each runtime. Both retain the same electrical
pass/fail outcome and HBT voltage outcome.

The prespecified exact-string fingerprint check **failed** for seed 51010:
one MOS `delvto` differs by 8.67×10⁻¹⁹ V (two binary64 ULP); the other four
representative random parameters agree exactly. `native_sample_qualification.json`
retains that strict failure. A separate, explicitly post-inspection floating-roundoff
assessment allows at most four ULP and passes; see `native_roundoff_assessment.json`.
The 100 ppm frequency and 0.05 °C numerical-error limits were fixed before these
runs and remain unchanged. This supports the specific joint BGR/T2F typical-process
fixture, not global simulator equivalence or the known IO-startup discrepancy.

Seeds 51021–51100 run all four calibration/endpoint temperatures on native 47;
the original twenty legacy samples remain unchanged. No sample mixes runtimes
between calibration and evaluation. The frozen nominal correction also remains
unchanged. Each run retains its image, tool, source and model provenance.
The native image lacks NumPy; vector validation now uses standard Python, checked
against all four retained seed-51001 finite/endtime/HBT-VCE results with exact
agreement. This affects parsing only, not the simulated circuit or solver settings.

## Physical reciprocal-temperature candidate

A separate candidate addresses reference drift using the approximation
`f = K T_K / (V0 + a T_K)`, which gives `1/f = A/T_K + B`.
Each physical sample's existing 25/100 °C frequencies determine A and B;
temperature is then `A/(1/f − B) − 273.15`. It uses no ensemble regression,
extra calibration point, clipping or lookup-table correction. The equation and
implementation hash were frozen before expanded-MC reciprocal outcomes were
evaluated; see `reciprocal_candidate_frozen.json` and `reciprocal_calibration.py`.

The original linear criterion and unchanged nominal-LUT diagnostic remain
separate. `reciprocal_candidate.json` reports completed groups and independent
point counts, with every point retained in `reciprocal_candidate_points.csv`.
The twenty smoke samples include six independent temperatures each; the nominal
group also includes four between-knot temperatures. The larger ensemble adds
physical samples at both endpoints. The physical model was selected after reviewing
linear-error/reference-drift diagnostics; these samples are not presented as a
wholly blind model-selection holdout. This is an **unadopted physical-model
candidate**. Resistor temperature dependence, comparator delay, nonlinear reference
curvature, supply changes, process extremes and package effects limit the approximation.

`reference_drift_diagnostic.json` and `reference_drift_samples.csv` examine the
loaded reference within these actual joint samples. Four-point transient-average
box TC is a sampled diagnostic, not the dense standalone DC sweep. Correlation
with cold-end error does not isolate the reference from all other device variation;
the separate standalone BGR seed ensemble is not paired to these physical samples.

## Completed100 and continued300-sample campaign

`mc100_summary.json` retains100 complete physical samples and400 endpoint/
calibration transients. Five samples fail the original linear±2°C criterion:
51010,51030,51037,51063,51096; worst absolute error2.644540°C. The frozen
nominal-LUT diagnostic has no endpoint failures, worst1.711021°C. The separate
reciprocal candidate has no failures in the completed nominal-rail groups;
neither candidate is adopted or qualifies supply/process coverage.

The prospective300-sample expansion uses seeds51101–51300 after baseline
51001–51100. Its count remains incomplete until `mc300_summary.json` reports
all300. An explicit pause preserved partial51105/51106; full repeats under
`t2f_mc300_resume_20260921_02` match all overlapping−40/25/100°C raw vectors
byte-for-byte and all model/netlist/runtime hashes. `mc300_resume_aliases.json`
selects those repeats without overwriting originals or counting extra samples.
Pass this file to `analyze_mc.py --samples 300 --run-aliases PATH`;
the LUT and reciprocal analyzers consume the
resulting run IDs in `mc300_samples.csv`. Frozen candidate hashes are unchanged.
A later pause also left51137–51139 partial. Full repeats under
`t2f_mc300_resume_20260922_01` reproduce all overlapping−40/25°C vectors
byte-for-byte and preserve model, source and physical-parameter fingerprints.
The alias file records these replacements without deleting original evidence.

`run_mc_batch.py` now limits queued jobs to active worker count and accepts
`--stop-file`; the same option is forwarded to `run_joint.py`. Once the file
exists, a running leaf completes and its result is written before the next
leaf is suppressed. Not-started seeds and temperatures remain explicit.

## Actual up-shifter receiver transitions

Three extracted up-shifters driving actual BGR r4 and T2F enable/mode inputs
complete90µs nominal and slow/cold fixtures in
`t2f_ls_transitions_nominal_20260921_01` and
`t2f_ls_transitions_slowcold_20260921_01`. All receiver logic, disable/reenable,
PTAT/REF and r4-return checks pass; maximum midpoint delays are3.593/4.911ns
with10ns input edges. Disabled output has no rising edges. Route piRC uses
explicit geometry estimates, not extracted route parasitics; via resistance,
coupling and fill remain omitted. The50fF output and ideal1V IPTAT termination
also limit scope. The legacy fast/hot run timed out after300.067s at77.499µs
of the required90µs; its acceptance checks remain not run. A separate6µs
legacy/native anchor agrees within0.0275ppm frequency and76fs matched edge
time; `ls_fasthot_runtime_comparison_20260922.json` records that limited
qualification. `t2f_ls_transitions_fasthot_native_20260922_01` then completes
the full90µs in125.092s. All frequency windows, disable, receiver logic and
HBT VCE checks pass; maximum receiver delay is2.35838ns and maximum HBT
VCE is1.23886V. This does not establish global native-runtime equivalence.
`transition_current_selected.json`
records combined BGR/T2F/three-up-shifter currents and sampled peaks; these
cannot be separated into an isolated up-shifter power number.

All five selected legacy-runtime repeats now complete (51030,51037,51060,
51063,51096). `legacy_crosscheck_comparison.json` preserves comparisons:
maximum frequency difference39.145ppm, maximum linear residual difference
0.017113°C, and all linear/LUT/reciprocal classifications agree. Four samples
have exact parameter fingerprints; seed51096 **fails strict equality** by
2binary64ULP and passes the separately stated4ULP roundoff diagnostic. This
extends scoped T2F runtime evidence without asserting global equivalence.

## Fixed-calibration supply and process screening

`run_joint_adverse.py` selects the PDK's existing corner-specific mismatch
libraries without editing model cards. It captures all580 realized MOS,
resistor, HBT and MIM parameters. `adverse_op_qualification_20260922.json`
records two seeds at each slow/fast corner and a repeated slow seed: all
parameters remain fixed across temperature and rails, repetition is exact,
and changing the seed changes each randomized device class. Equal seed
integers at different process corners do not represent paired physical samples.

`run_adverse_calibration.py` calibrates each physical sample at25/100°C with
3.3/1.2V rails, then freezes those coefficients for independent−40/125°C
points at3.0/1.08V and3.6/1.32V. Separate linear, frozen nominal-LUT and
reciprocal results retain the original acceptance rule. Slow and fast pilot
seed51901 each complete all six transients with all580 parameters fixed.
Original linear calibration fails high-rail/cold at−2.37540°C and−2.70757°C,
respectively. Both frozen candidates pass these pilot points; reciprocal
maximum absolute error is1.48832°C slow and1.61663°C fast. These are screening
pilots, not ensemble or yield qualification. The nominal pilot and selected
30-sample expansion are tracked separately; they are not counted as completed
by the pilot results. `run_adverse_batch.py` supports bounded independent
samples with explicit stop-file and incomplete-point accounting.

## Completed overnight campaigns, migration pause 2026-09-22

The typical-process campaign now completes **300/300 physical samples and
1200/1200 transients**, with14 original linear-calibration failures and no
solver or within-sample fingerprint failures. The frozen LUT and reciprocal
candidates have zero endpoint failures; they remain unadopted. The prospective
200-sample reciprocal maximum is0.975771°C. `mc300_summary.json` and the
corresponding candidate reports contain the final counts. The comparison PNG
is still explicitly labeled220/300 and must be regenerated before final use.

The fast-process fixed-calibration campaign completes30/30 samples and180/180
transients on the legacy runtime. Original linear calibration fails11 samples,
frozen LUT fails4, and reciprocal fails0; their maximum absolute errors are
3.617875°C,2.667278°C and1.787973°C respectively. Four independent rail/
temperature points per sample do not establish continuous-range or packaged
accuracy. `adverse_fast30_summary_20260922.json` retains every sample.

The adverse native comparison completes all six anchor leaves but **fails**
strict580-parameter equality and the separate four-ULP diagnostic(max18ULP).
Numerical frequency/error differences remain within18.071ppm/0.005748°C,
and classifications agree. This does not authorize native adverse campaigns;
all30 samples above used legacy. Three additional prospective legacy checks
(seeds51148,51296,51111) remain not run.

T2F synthetic external-reference perturbation0/1/5mV completes all three
leaves; period standard deviations are1.88957ps,424.957ps and1.98554ns over
the finite saved window. This is external sensitivity, not physical device
phase noise or a passed jitter budget. The actual TEMP_OUT pad fixture is
prepared but not run. Owner paused simulations for migration; no reference
queue or container remains active.

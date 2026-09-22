# BGR extracted reference qualification, 2026-09-21

All numbers below are **simulated**, using the existing capacitance-only BGR
extraction. No circuit, layout, rule deck, or PDK model card changed.

| Check | Status | Evidence/result |
|---|---|---|
| Mismatch flag and seed qualification | passed | Six cases, `bgr_qual_20260921_02`; repeated seed gives identical saved vectors; different seed changes device parameters/output. |
| Fixed physical sample over temperature | passed | MOS `delvto`, resistor `nsmm_rsh`, and HBT `area` fingerprints remain identical before/after DC temperature sweep; reverse sweep agrees within 1.57e-10 V in VREF. |
| Smoke MC completion | passed | 20/20 seeds, 42001–42020, `bgr_mc20_20260921_01`; no timeout/numerical failure. |
| Expanded MC completion | passed | 80/80 additional seeds, 42021–42100, `bgr_mc100_20260921_01`; 100 total, no discarded samples. |
| MC TC ≤50 ppm/°C | **failed** | 54/100 samples fail; worst 178.540 ppm/°C over −40 to 125 °C. |
| 27 process combinations ×3 supplies | passed | 81/81 complete temperature sweeps; maximum TC 49.341 ppm/°C at HBT bcs/MOS ss/R wcs/3.0 V. |
| Screened slow startup | passed | Six of six 1 ms/100 ms supply ramps at 3.0 V complete; nominal/27 °C, wcs/ss/wcs/−40 °C, bcs/ff/bcs/125 °C. Final VREF 1.03325–1.04259 V. |
| Nominal dip, r4 and load-step diagnostics | passed execution | Three 40 µs characterization cases; no recovery-time acceptance budget adopted. |
| Joint actual downstream loads | not run here | Standalone IPTAT clamp and VREF testbench loads; joint BGR/T2F subset is recorded in the T2F qualification directory. |
| Nominal AC PSRR / output noise | passed execution | Simulated 196.05 µV RMS over 1 Hz–10 MHz; 102.956 dB / 75.350 dB PSRR rejection at 1 Hz / 1 kHz. No noise acceptance budget adopted. |
| Feedback-loop stability and switched-capacitance loads | partially complete | Nine capacitive-load cases and six conditional local-loop probes complete; global pole-zero solve failed. Global stability remains unqualified. |
| Full device voltage audit | not run | HBT external VCE sampled; other terminals/reliability limits need separate checks. |
| Wire R, fill/well coupling, global process MC, spatial correlation | not run | Existing capacitance extraction/model limitations apply. |

The 100-sample simulated VREF at 25 °C has mean 1.038770 V, sample sigma
21.132 mV, and range 1.000782–1.103023 V. These are untrimmed reference
results, not calibrated system threshold or temperature yield. MC uses typical
process mismatch models; process corner sweeps are a separate ensemble.
The previous schematic TC failure is retained and is not superseded by the
capacitance-PEX corner result.

TC is `(max(VREF)-min(VREF))/VREF(25 °C)/165*1e6`, using 5 °C steps
from −40 through 125 °C. The 81 process/rail sweeps save 2,754 operating
points. Maximum sampled external BGR HBT |VCE| is 0.858885 V and maximum
supply current is 33.975 µA for that standalone load. Continuous-temperature
extrema, all downstream loading, and statistical confidence outside the
modeled ensemble are not established.

## Harness and physical-sample semantics

The pinned PDK's HBT, HV MOS and resistor mismatch wrappers default to
`mm_ok=0`. Existing extracted instances omit that argument. A separate saved
`pex_mm.spice` adds `mm_ok=1` to every extracted MOS, HBT and resistor
instance; the source PEX and model cards remain unchanged. The PDK models
provide the distributions (including the HBT `agauss(1,0.1,...)` area factor).
Each extracted unit/finger receives its own PDK-local draw. This is not a
claim that layout spatial correlation or packaged silicon distributions are
known. Equal seeds in schematic versus PEX are not treated as paired devices.

`.option seed` is set before parsing; a sample is loaded once and swept with
`dc temp`, with no reset/reparse between temperatures. The qualification also
runs a reverse sweep and a repeated seed. Saved parameter fingerprints cover
one representative instance from each randomized device class. The nominal
control gives identical results for two different seeds. The script explicitly
checks solver exit, timeout, endpoint, finite vectors and error text. Its case
`status` means simulation completion; `tc_status` and `startup_level_status`
are separate acceptance results, so a completed simulation can fail TC.

## Reproduction and provenance

Run from the repository root, substituting a **new** run ID (existing directories
are refused):

```sh
G1_WORKDIR=designs/g1-guardian/blocks/g1_bgr/sim/qualification flow/run.sh python3 run_campaign.py --run-id NEW_ID --image-id sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0 --suite qualify
```

The other saved commands use `--suite mc --samples 20`, then `--suite mc
--samples 80 --seed-start 42021`; `--suite corners`; and `--suite startup`.
Each manifest preserves exact arguments, git revision, input/deck/runner hashes,
all model-library and OSDI hashes, observed PDK commit, ngspice version, solver
settings, per-case runtime, actual exit status and watchdog outcome. Observed
Docker image ID matched the ID above; `/foss/pdks/ihp-sg13g2/COMMIT` matched
`84374023ee8b4b126bebbba67fcbada0a9c0ff0b`; ngspice reported 46. Container
paths are stable reproduction paths, not host-specific paths.

Run `python3 designs/g1-guardian/blocks/g1_bgr/sim/qualification/summarize.py`
to regenerate `summary.json` and `summary.csv` and assert the seed/sweep checks.
The 120 s/sample and 300 s/transient watchdogs are ceilings. Completed DC
samples took approximately 0.5–0.7 s; the six startup transients took 0.8–6.9 s.

Setup failures are retained separately: initial model-introspection invocation
omitted `.spiceinit` and failed with unknown OSDI model; adding the existing
OSDI loader fixed it. The first campaign directory, `bgr_qual_20260921_01`,
was created but simulations were **not run** because container git ownership
prevented provenance collection. The runner now passes `git -c
safe.directory=/work` for that read-only query.

## Temperature sensitivity diagnostic (not calibrated T2F acceptance)

`analyze_temperature_proxy.py` applies the unqualified ideal relation
`frequency proportional to IPTAT/VREF` to each retained MC sample. It fits each
sample at 25/100 °C, freezes that calibration, and evaluates the other 32
independent temperatures. Two of 100 samples exceed ±2 °C in this proxy; the
worst is seed 42093 at −40 °C (−2.361 °C). Actual oscillator/comparator loading,
delay, offset, capacitor variation and coupling are absent. The abstraction has
**not** been qualified against joint extracted temperature and MC anchors, so
this is only a sensitivity diagnostic and cannot establish V11 yield. It does
show why reference TC failure is not numerically equivalent to the calibrated
temperature failure rate. Raw results are `ideal_iptat_vref_proxy.csv`.


## Nominal AC/noise pilot

`runs/bgr_noise_20260921_01` saves the original C-PEX fixture, deck, log,
positive PSRR rejection versus frequency (0.1 Hz–100 MHz), and output noise
spectrum (1 Hz–10 MHz). Both sweeps completed with finite endpoint vectors,
exit 0, in 0.61 s. Simulated integrated output noise is 196.046 µV RMS over
that bandwidth. This uses the PDK noise models and standalone 1 pF/ideal
IPTAT clamp fixture; it is not measured noise, feedback-loop stability,
chip-level rail rejection or a passed noise budget. The known missing well,
fill and wire-R parasitics limit the AC result.

Reproduce with `run_noise.py --run-id NEW_ID --image-id` followed by the
observed image ID above, under the same `G1_WORKDIR` and `flow/run.sh`.


## Supply/mode/current-step diagnostics

`runs/bgr_stress3_20260921_01` has three nominal 27 °C, 40 µs transients;
all complete with finite vectors and exit 0 in about 7 s each. No system
recovery-time acceptance budget is adopted by these characterization fixtures.

- A 3.3 V supply falls to 1.8 V in 10 ns at 5 µs, holds until 10 µs and
  returns in 10 ns. Simulated VREF spans 0.866120–1.250076 V and returns to
  its 1.039310 V baseline by the saved endpoint. The dip is below the normal
  3.0 V operating rail, and this does not establish safe system brownout behavior.
- r4 rises from 0 to 3.3 V in 10 ns at 5 µs and returns at 20 µs. VREF
  spans 0.910073–1.039360 V and returns to baseline. Coupled temperature/trip
  behavior during this transition is not established.
- A 100 nA sink is applied to VREF over the same 5–20 µs interval, with
  10 ns edges. VREF droops by 8.786 mV, an approximately 87.9 kΩ incremental
  sensitivity in this fixture, then returns to baseline. This is a load
  sensitivity, not a model of a selected downstream receiver or instrument.

Use `run_campaign.py --suite stress` with the usual new run ID/image arguments
to reproduce. The original capacitance-only extraction limitations apply,
particularly for fast supply feedthrough. HBT external VCE maxima are saved;
full transistor terminal-voltage qualification remains not run.
## Additional load-capacitance characterization

`runs/bgr_capload9_20260921_01` completes nine 40 µs simulations of the same
100 nA load pulse (5–20 µs, 10 ns edges), with 0.1, 10 and 100 pF VREF load
at nominal/3.3 V/27 °C, wcs-ss-wcs/3.0 V/−40 °C and
bcs-ff-bcs/3.6 V/125 °C. All simulations complete with finite vectors.
For 0.1/10 pF, simulated droop is 7.835–9.866 mV and VREF returns essentially
to its initial value by 40 µs. The 100 pF load has not fully recovered at the
40 µs endpoint: residual droop is 0.520–1.015 mV. These are explicit load
sensitivity fixtures, not actual downstream loads or a feedback phase-margin
measurement. No system recovery acceptance budget has been adopted for them.
Reproduce with the normal `run_campaign.py` command and `--suite capload`.

## Mismatch mechanism and model scaling

`mismatch_mechanism.json` correlates all 100 retained BGR samples. Unit Q1
(XQ56) area factor has correlation −0.9500 with signed 25→100 °C reference
slope, versus +0.0323 for the R1 normalized sheet-resistance random parameter
and −0.1213 for one NMOS-cascode threshold parameter. These representative
parameters do not constitute a complete causal variance decomposition.

The pinned `sg13g2_hbt_mod_mismatch.lib`, npn13G2 section, defines
`qarea=agauss(1,0.1,(mm_ok!=1?0:1))` and uses it as the VBIC instance area.
This distribution does not depend on Nx; increasing a single instance's Nx
cannot be claimed to reduce its modeled relative mismatch. Separate physical
unit HBT instances receive separate draws, with no spatial correlation model.
A larger real array therefore requires explicit instance geometry, current
density, power/bias and regenerated physical checks; statistical averaging in
this model alone is not a silicon-yield prediction.

Some retained logs contain temperature-limiting NaN and resistor vmax warnings
during solving. Saved final sweep vectors are finite and numerical completion
is checked, but those logs remain intact. The complete internal-terminal and
model-warning audit is not closed by the reported external HBT voltage check.

## Q1 diagnostic and physical-array pilot

`runs/bgr_q1_counterfactual_20260921_02` holds all PDK mismatch draws fixed,
then sets only Q1's realized area to unity after the operating point. All 86
recorded device fingerprints verify that the remaining draws are unchanged;
the all-on vectors match the original samples. TC changes from178.540→9.899,
177.529→21.932 and165.061→67.279 ppm/°C for seeds42081,42093 and42031.
The last sample still fails. This is a causal diagnostic, not a hardware fix.
The earlier pilot's interleaved stdout/stderr corrupted fingerprint capture;
that failed pilot remains retained, followed by a rerun with separate stderr.

`candidates/bgr_array4` instead adds real independent unit instances: four Q1,
four diagnostic Q1B and32 Q2. Normal-mode nominal TC is23.022 ppm/°C,
VREF25=1.038751 V and IPTAT25=4.09995 µA, versus22.558 ppm/°C,
1.039343 V and4.10669 µA for the baseline. Branch currents remain nearly
unchanged, reducing current density per unit by about four. Q2 VBE25 falls
from0.65065 to0.61416 V, below the model header's stated0.65 V lower range.
`hbt_current_density_audit.json` also records baseline and candidate temperature
points below that fixed voltage boundary; the header's temperature-dependent
validity interpretation is unresolved. Neither broad measured Gummel coverage
nor finite numerical output establishes validity. Array mismatch, new wiring,
physical placement, DRC/LVS and extraction are **not run**; no adoption.

## Local loop diagnostic and failed pole analysis

`run_stability.py` implements the two-injection return-ratio method from
[Tian et al., equations21–30](https://community.cadence.com/cfs-file/__key/communityserver-discussions-components-files/38/00900125_5F00_striving_5F00_for_5F00_small_5F00_signal_5F00_stability_5F00_circuits_5F00_devices_5F00_2001.pdf).
The bilateral analytic RC anchor agrees to2.37e−13 relative error over901
frequencies,1 Hz–1 GHz (`bgr_stability_anchor_20260921_01`). Zero-valued
injection sources retain the DC connection. Actual PEX gate-fanout probes at
PBIAS and PCASC complete for nominal, slow/cold and fast/hot tuples in
`bgr_local_stability_20260921_01`. Conditional PBIAS phase margins are
118.5–119.0° at3.53–3.75 MHz; PCASC has no unity crossing. Other internal
loops remain closed, so this does not establish global BGR stability or an
accepted all-loop phase/gain margin. See `local_stability_summary.json`.

The unmodified full-PEX pole pilot `bgr_pole_pilot_20260921_01` **failed**:
ngspice reached its pole-zero iteration limit after1426 trials. It printed
unqualified roots including right-half-plane values. These are retained but
cannot establish physical instability or stability without a converged,
validated pole solution. Global stability closure remains **not run**.

## Density-preserving array candidates, 2026-09-22

Two isolated four-unit candidates now have qualified mismatch evidence. Both
replicate the physical core MOS/HBT units while preserving the output mirror
XM40/XM46/XM53. The first uses quarter-length resistors; the second uses four
parallel original-geometry resistor units. The earlier candidate incorrectly
excluded XM41 instead of XM40: its IPTAT rose to10.06µA and it failed the
intended current-preservation check. That result is retained, not adopted.

| Simulated candidate | Nominal TC (ppm/°C) | IPTAT25 (µA) | Current25 at3.3V (µA) | TC failures /100 | Worst TC (ppm/°C) |
|---|---|---|---|---|---|
| Baseline |22.5578|4.10669|21.8926|54|178.540|
| Four-unit core, quarter-length R |23.4507|4.04260|74.1276|23|104.762|
| Four-unit core, parallel full-length R |22.5578|4.10669|75.2502|19|100.763|

The candidates improve the modeled failure fraction but **neither closes the
50ppm/°C requirement**. Fresh seeds43001–43100 were retained in `mc20` and
`mc80` runs with prefixes `bgr_array4_density_v2` and
`bgr_array4_parallel_r`, suffix `_20260922_01`. All200 candidate samples
completed; all581/905 recorded parameters respectively remained fixed across
temperature. Separate qualification runs verify exact seed repeats, reverse
sweeps, disabled-seed invariance and variation in each device class. No failing
sample was removed. Added units and changed geometry prevent a paired-yield
interpretation even where original-device fingerprints remain identical.

`run_density_probe.py` directly measures VBIC collector/base currents. The
quarter-length candidate retains98.33–98.61% of baseline per-unit HBT current
at−40/25/125°C; nominal Q2 VBE25 is0.650235V. The parallel-resistor candidate
preserves baseline nominal VREF/IPTAT/bias to numerical precision. Resistor
body area is four times baseline for parallel units; added routes, legal
placement, DRC/LVS and fresh extraction remain **not run**. Independent PDK
unit draws do not model physical spatial correlation. Neither candidate has
been adopted. `analyze_candidate.py RUN_ID` reproduces qualification and
separate numerical/TC outcomes; each manifest records the complete command,
image, model, source and deck hashes.

A proposed16× expansion was rejected as a credible local implementation before
simulation: actual PCell bounding boxes total58,020.53µm² before new guards,
routing and dummies, versus a broad36,888µm² neighboring region already containing
routes/decoupling. The4× parallel-resistor device boxes total14,932µm² versus the
existing84×124µm macro, so its physical fit is also unproven. This is area
accounting, not an optimal-packing proof. See the [GDS area audit](../../../../review/audits/BGR_ARRAY_AREA_20260922.md).
No16× circuit simulation, production adoption or die expansion was performed.

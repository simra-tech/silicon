# Selective-loop BGR fixed-draw diagnostic plan

Original prospective status: **not run; design review required before launch**. The candidate100
screen retains7 TC failures, maximum68.7592ppm/°C. No new geometry, larger array,
model-card edit or broad PEX is proposed by this diagnostic.

Freeze failing seed43047 (62.7382155ppm/°C) and passing control43001
(42.7912628ppm/°C, first prespecified pilot sample). For each seed use four
separate exact-source loads of the existing selective16 mismatch netlist:

| Variant | Intervention after initial OP | All other1877-parameter entries |
|---|---|---|
| `all_on` | none | exactly retained |
| `qref_nominal` | only XQ60 VBIC area set to1 | exactly retained |
| `ptat_hbt_nominal` |16 Q1 and128 Q2 VBIC areas set to1 | exactly retained |
| `both_nominal` | the union of the preceding145 areas set to1 | exactly retained |

Setting an already realized device area to its nominal value is a diagnostic
counterfactual, not physical resizing or evidence that manufacturing variation
can be removed. The PTAT intervention removes both aggregate Q2/Q1 area-ratio
error and within-group area variation; it is not a pure ratio-only derivative.
Q1B and bias HBTs, all MOS/resistors and the original wire capacitances remain
unchanged. Separate factorial variants expose interaction rather than assuming
the two contributions add linearly.

Use the same pinned ngspice46 image, PDK libraries/OSDI, netlist byte order,
seed, rails, loads, numerical settings and −40…125°C5°C DC sweep as the archived
sample. Source candidate SHA-256 is
`b6810892a4e258bb206af3b6a87c3a046bff4b2b1c4d304e385eacb2765edbed`.
The canonical mismatch snapshot and all1877 original parameter names/values are
in `bgr_selective_loop16_mc20_20260922_r1` and
`bgr_selective_loop16_mc80_20260922_r1`. Their100-sample audit freezes source,
deck, waveform, runtime and model hashes.

Required gates:

1. Before every intervention, all1877 printed parameters must exactly match
   the archived sample. No reseeding, reset or reparse within a leaf.
2. Each `all_on` DC waveform must be byte-identical to its archived original.
   Stop counterfactual interpretation if the baseline replay fails.
3. After intervention and after the DC sweep, every non-target parameter must
   match its pre-intervention value exactly. Target areas must equal exactly1;
   parameter-count, unsupported-alter or missing-vector failures stop expansion.
4. Preserve all34 finite temperature points and VREF/IPTAT/supply/VBE/bias vectors.
   Record signed endpoint slope, TC box, full voltage-current deltas and original
   electrical classification separately. Keep both failing and passing controls.

Proposed budget:8 DC leaves,120s ceiling per leaf, one CPU6 process/thread,
4GiB memory reservation and0.25GiB fresh resource gate. Existing selective DC
leaves take roughly8–13s, so approximately2min compute and under15MiB output are
expected. A new runner must snapshot the exact source and intervention list;
the old Q1-only diagnostic covers fewer parameters and cannot be used unchanged.
No simulation or causal conclusion is claimed by this preparation.

## Completed approved diagnostic

Root reviewed this plan before launch. `bgr_selective_fixed_draw_20260922_r1`
completed all8 leaves with the required exact1877 initial/non-target final
fingerprints and byte-identical `all_on` waveforms. The original candidate100
failures remain unchanged and the candidate remains unadopted.

| Seed | Original TC | Qref intervention | PTAT intervention | Both |
|---|---:|---:|---:|---:|
|43047 failing|62.7382|46.2862|36.0823|21.7847|
|43001 passing control|42.7913|29.9780|32.7898|21.4116|

All values are simulated ppm/°C over the original34-point temperature sweep.
`factorial_analysis.json` retains full11-vector voltage/current differences at
every temperature and the interaction `both − Qref − PTAT + original`.
Maximum VREF interaction is0.596703µV for43047 and0.189109µV for43001;
maximum IPTAT interaction is1.08e−15A and4.50e−16A. TC is nonlinear and its
differences are not assumed additive.

For43047 at25°C, Qref intervention leaves IPTAT unchanged at4.019459µA
and raises VREF4.714884mV. PTAT intervention raises IPTAT87.194864nA and
total supply current4.366243µA; both raise VREF12.398123mV. Thus these
interventions have measurably different current and voltage effects. This
identifies contributions in two frozen samples, not a manufactured mismatch
remedy, full-population causal decomposition or authorization for new arrays.

Reproduction: the pinned flow in this block's qualification workdir runs
`python3 run_selective_fixed_draw.py --run-id NEW_ID --image-id PINNED_IMAGE`,
then host analysis `python3 analyze_selective_fixed_draw.py NEW_ID`.
Runtime/source/model/deck/wave hashes are in
the run manifest. Original prospective text above is retained as chronology.

## Approved remaining-failure Qref-only extension — prospective

Status at preparation: **not run**. Root approves the remaining six observed
failing seeds43026,43039,43056,43058,43068,43077, each with exact `all_on` and
`qref_nominal` leaves (12total,120s each, CPU6,4GiB reservation, fresh0.25GiB
resource gate). Seed43047 already has the retained exact pair above and is
not repeated. All1877 before/after/sweep/non-target and original-wave-byte
gates are unchanged. No successful sample is selected after observing this
diagnostic; existing passing43001 control remains the original control.

```sh
python3 run_selective_fixed_draw.py --run-id bgr_selective_qref_remaining6_20260922_r1 --image-id sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0 --seeds 43026,43039,43056,43058,43068,43077 --variants all_on,qref_nominal
```

This tests whether ideal removal of Qref area error could bring all seven
observed TC failures below50ppm/°C. Even if all pass, it does not establish
a manufacturable remedy or improved yield. If any remain above50ppm/°C,
Qref-only averaging is insufficient to close the observed failing set even
in this idealized intervention. Report full34temperature VREF/IPTAT/current
changes, not only TC boxes. A physical/current-density/resistor-scaled candidate
requires a separate source-design review before new-source Monte Carlo runs.

Extension result: **12/12 exact diagnostic gates passed**. Combined with the
retained43047 pair, ideal Qref intervention leaves2/7 original failures above
50ppm/°C:43039 becomes52.089674 and43068 becomes59.544122ppm/°C. The other
five become37.979068–46.286207ppm/°C. Therefore Qref-only averaging is not
sufficient even in this idealized zero-Qref-error intervention. All original
seven failures and passing43001 control remain unchanged. Full per-temperature
voltage/current deltas and exact source/deck/wave identities are recorded in
`selective_qref_all7_audit_20260922_r1.json`; no geometry or new-source MC
was authorized or run by this extension.

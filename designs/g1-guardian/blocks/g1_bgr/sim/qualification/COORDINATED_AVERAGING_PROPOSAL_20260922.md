# Coordinated PTAT/Qref averaging — proposal, not implemented

Status: **not run / source-design and physical feasibility review required**.
No candidate netlist, layout, new-source MC or model-card change is made by
this proposal. The original TC requirement remains≤50ppm/°C; no limit change,
per-sample calibration or fitted temperature correction is proposed.

## Evidence and smallest staged question

Selective-loop16 has7/100 TC failures. Exact1877-parameter counterfactual
checks over every failure show that even ideal Qref-area-error removal leaves
43039 at52.0897 and43068 at59.5441ppm/°C. The original43047 four-way experiment
also shows a separate PTAT-area contribution. Qref-only averaging is therefore
insufficient. These observations motivate coordinated averaging, not a claim
that the following unit counts are optimal or sufficient.

A first power-of-two screening point would double the selective PTAT loop
from16 to32 original legal units and use4 independent original Qref units.
Only one such candidate should be prepared after geometry feasibility and
source-design review. Do not escalate arrays automatically after failures.

## Exact scaling hypothesis

| Branch | Original instances | Proposed total units | Preservation hypothesis |
|---|---|---:|---|
|PTAT/bias MOS|XM34–39,41,45,47,48,50,52,54|32 each|Same W/L/contact geometry and nominal current per unit|
|PTAT/bias HBT|XQ56,62,67–76 except none of this listed set omitted|32 each|Same0.07µm×0.9µm,Nx1 device and per-unit VBE/current|
|PTAT/bias feedback R|XR16,23–26,77–86|32 full-length parallel units each|Equivalent R÷32 and total branch I×32 retain voltage drops|
|VREF mirror|XM43,44,51|4 each|Same per-unit W/L/current, total VREF branch I×4|
|Qref|XQ60|4 independent Nx1 units|Current×4 and area×4 retain each unit's current density|
|VREF feedback R|XR17–22|4 full-length parallel units each|Equivalent R÷4 maintains original VREF−VBE3 drop|
|Startup/detector/IPTAT output|Existing unchanged instances|Original counts|Exported bias voltages and IPTAT current intended unchanged|

The PTAT HBT set is exactly
`56,62,67,68,69,70,71,72,73,74,75,76` (12 originals), not the entire BGR.
Full original units, including resistor length/width and MOS diffusion/contact
geometry, are retained. No subminimum emitter, fractional Nx or blind Nx-based
variance reduction is used. The pinned HBT `qarea=agauss(1,0.1,...)` term is
independent of Nx; separate instances have separate modeled draws. Spatial
correlation of a manufactured array remains unknown and is not qualified.

At nominal25C the existing density probe gives Q1 IC4.09494µA/unit,
Q2 IC0.513332µA/unit and Qref IC4.10112µA/unit. Those are the densities to
preserve, not just VREF. Baseline/candidate per-unit terminal-voltage and
current comparisons must precede mismatch runs. Targeting nominal equivalence
does not imply startup or AC equivalence: native added-device capacitance,
loop gain, reference impedance, start detector drive and new wiring change.

## Area and power are not preserved totals

Counts from the existing explicit netlist would become440 MOS,397 HBT
(including9 unchanged dummy HBTs),519 resistor units. The corresponding
all-parameter mismatch fingerprint inventory is expected to be3714 entries
(4/MOS,1/HBT,3/R); the generator must independently verify that count.

The original generator's84×124µm macro is10,416µm². The physical owner's
read-only audit confirms the existing local envelope36,888µm², x638–850µm,
y855–1029µm, with neighboring macros/ring and existing decaps/PDN/routes.
Keeping the generator's1.9µm resistor-column
pitch gives the selected-loop32 resistor-body pitch area alone
`32×(51.5+4×48+10×50)×1.9=45,204.8µm²`, before terminals, dummies, other
resistors, HBTs, MOS, guard rings, vias or routing. Under that preserved-pitch
constraint the proposal already exceeds the prior local envelope. This is a
specific conditional no-fit bound, not a claim from summing arbitrary cell
bounding boxes or assuming1.9µm is the foundry minimum.

The physical owner's `review/audits/bgr-selective-area-20260922-r1.json`
reuses exact native-GDS/PCell inventory. Selective16 native bbox sum is
36,521.86µm² (99.0% of that envelope before external contacts/guards/routes),
and loop32+Qref4 is72,959.25µm². Native boxes can overlap legally, so these
are not rigorous packing lower bounds. Baseline-overhead extrapolations are
91,448.06/182,684.60µm² respectively, estimates rather than placement results.
With retained1.9µm pitch, native resistor heads increase loop32 footprint
to46,317.44µm²; Qref4 resistors add2,449.632µm².

Thus this full-unit coordinated proposal is **not ready for a new-source
campaign** under the existing local envelope. Legal placement, global2mm²
fit, DRC/LVS/new PEX are **not run**. The existing die is1.8225mm², but the
difference from2mm² is not freely available local core area. The owner permits
expansion up to2mm² with demonstrated need: the local envelope is not an
absolute die-area cap. A bounded read-only whole-floorplan assessment including
gm4 SENSE is now requested. No geometry or macro movement is performed by this
proposal; any enlargement still requires coordinated ring/PDN/routes/decaps,
whole-floorplan fit and stock checks. A blanket no-expansion policy does not
apply. The separate remedy review compares repacking and smaller alternatives.

Using the two simulated nominal points (baseline21.892569µA and loop16
206.693157µA) gives an inferred incremental loop unit current12.320039µA.
Qref emitter current is4.106693µA. If nominal branch scaling holds, loop32+
Qref4 would draw approximately416.134µA at3.3V, or1.37324mW, versus loop16
0.682087mW and baseline0.0722455mW. This is an **analytical forecast from
simulated anchors, not a candidate simulation**. It assumes output/no-load
conditions match the original probe. Total power roughly doubles versus
loop16; no unchanged-power claim is possible. Adverse/static/dynamic current,
rail drop, contact/via current margin and startup power are **not run**.

## Prospective qualification, only after review

1. Freeze the selected candidate, original-unit mapping, all model/OSDI/runtime
   hashes and a fresh run ID. Equal seeds across changed topology are not
   identical physical samples; preserve originals and label comparisons.
2. Nominal −40…125C sweep and25C per-unit density/terminal probe. Preserve
   VREF/IPTAT/DC density, diagnose any changed bias/startup state; unchanged
   TC≤50 target and HV model-scope constraints remain. No relaxed solver knobs.
3. All3714-parameter seeded repeat/freeze/disabled-mismatch/reverse-temperature
   qualification before new-source sample work. Select failing controls43039,
   43068,43047 and the original passing43001 for mechanism comparison, not yield.
4. Only after selected controls and physical feasibility pass, request an
   independently seeded prospective campaign. The observed candidate100 is
   development evidence and cannot be relabeled independent validation.
5. Physical layout/via-current/stock DRC/LVS/geometry freeze/new extraction,
   then repeated electrical qualification/startup/load/stability/actual downstream
   regressions before adoption. The existing short-channel HV concern remains.

Initial electrical screening, if authorized after fit: one CPU,4GiB reservation,
120s per DC leaf and≤0.25GiB gated output. Roughly2× existing solve cost is a
planning estimate, not measured throughput. Actual layout/PEX resource forecasts
must come from the physical owner. No current candidate has been adopted.

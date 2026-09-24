# BGR remedy design review — no new circuit simulation or source

Status: **proposal / whole-floorplan feasibility pending**. The owner allows
up to2mm² with demonstrated need. The existing36,888µm² local BGR envelope
is not a blanket no-expansion rule, but unused die-area arithmetic is not a
placement result. Include the gm4 SENSE candidate, ring, supplies, decaps,
routes, pad access and other macros before choosing a larger BGR region.
No new netlist, model, geometry, calibration policy or qualification limit
is changed by this review. TC≤50ppm/°C remains the requirement.

## What the evidence rules out

The selective-loop16 candidate has7/100 TC failures. All seven were replayed
with exact1877-parameter/non-target/sweep and original-wave-byte gates.
Ideal removal of Qref area error still leaves43039=52.0897 and
43068=59.5441ppm/°C. Qref-only averaging is therefore insufficient. The original
43047 four-way counterfactual separately demonstrated PTAT-HBT contribution;
this is not an assumption that TC differences add linearly.

The nominal selective16 signed endpoint slope is−20.856325ppm/°C, with
TC box22.5563ppm/°C. Candidate100 signed slopes range−68.7592…+36.6362ppm/°C.
The positive-tail sample43053 has Qref area1.00233, close to nominal, and
Q2/Q1 log-area ratio0.09144. Therefore adding Qref averaging and simply
centring the nominal slope at unchanged loop16 is not a defensible promise
of closure: its positive-tail excursion is roughly57.49ppm/°C from nominal.
This is diagnostic sizing evidence, not a prediction of independent yield.

## Candidate comparison

| Option | Geometry/electrical mechanism | Why it might help | Main unresolved risks |
|---|---|---|---|
|Loop32 +Qref4, original units|Coordinated32-unit PTAT/bias loop and4-unit VREF branch, current and parallel feedback R scaled together|Keeps the validated nominal unit-current-density mechanism; addresses both mismatch contributors|~72,959µm² native bbox,~1.373mW forecast; still no demonstrated TC closure or whole-floorplan fit|
|Same32/4, legal repacking/pitch review|Merge only legally shareable enclosure/guard geometry and reduce excess pitch without changing device dimensions/contact requirements|Preserves electrical unit sizing; can reduce placement overhead|Native bbox sums are not packing bounds;1.9µm existing R pitch is not a foundry minimum. Minimum pitch, matching environment, cut arrays and routes need stock-rule validation|
|Wide equivalent feedback resistors|ReplaceN full parallel W1/L units by one nominal WN/L resistor where legal|Same ideal R/N and current per width; fewer repeated spacing/head overheads|Material area is stillN×; maximum width, contacts, parasitics, mismatch semantics and correlation need new qualification. One draw cannot be calledN independent draws|
|Compact shorter feedback R|Choose new W/L for R/N with less material area|Large area reduction is possible geometrically|Current density, power density, capacitance and resistor mismatch change. The earliercompact4 candidate had23/100 TC failures versus19/100 full-R4; it is not evidence compact24/32 will work|
|Fixed-current HBT-only arrays|Average selected Q1/Q2/Qref devices without scaling whole bias loop|Much smaller area and potentially low power|HBT current density changes; VBE shifts, beta/leakage/startup/loop poles change. Qref area4 alone gives an idealized−VT ln4 shift and requires re-design of compensation; not a drop-in preserved-density remedy|
|Chopping/dynamic element matching/new bandgap topology|Temporal mismatch averaging or a different reference architecture|Could avoid very large static arrays|New switching/ripple/clock/interface/startup behavior, coupling into SENSE/T2F and broad new verification. Not the smallest defensible next experiment|
|Fixed nominal TC coefficient centring +loop24/Qref4|One global hardware feedback-ratio update from nominal-only curve, plus coordinated averaging|Uses less replication than32/4 while addressing the strong negative nominal bias and both stochastic contributors|New absolute VREF, PVT optimum, startup, source impedance and all downstream calibration inputs require actual qualification. It must not be represented as output calibration of existing samples|

## Smallest defensible next candidate to review

Recommend **one loop24/Qref4 candidate with a fixed nominal-only feedback-ratio
centring hypothesis**, conditional on whole-floorplan fit and explicit source
review. This is the smallest staged candidate supported here, not a proof of
globally minimum size or successful qualification. Loop16/Qref4 is a lower-area
alternative but has no adequate margin against the observed positive tail.
Loop24 is a practical integer replication stage above16; no candidate outcomes
have been used to select or tune it because none has been simulated.

Retain exactly the existing selective loop's13 MOS,12 HBT and15 resistor
original-instance sets, each with24 independent original legal units. Retain
startup/detector/IPTAT-output geometries. Use4 original units of XQ60,
XM43/XM44/XM51 and XR17–22. HBT units remain0.07µm×0.9µm,Nx1, not fractional
devices or enlarged Nx asserted to reduce variation. The pinned HBT qarea
variation is independent of Nx; separate-unit simulation and spatial physical
correlation remain distinct concepts.

PTAT loop branch currents scale24× and feedback resistances becomeR/24;
the VREF branch scales4× and feedback R becomes approximately1.01837R/4.
The latter intentionally changes VREF compensation while preserving Qref
current density to first order. All per-unit currents, VBE, MOS headroom,
IPTAT output, detector/startup behavior and HV model limits must be measured
in the new candidate before mismatch screening. Total power is not preserved.

The nominal-only sizing estimate uses the retained−40…125C curve:

`delta_alpha = −[VREF(125)−VREF(−40)] / [dVBE(125)−dVBE(−40)] = 0.112154879`.

At25C, `alpha=(VREF−VBE3)/dVBE=6.10675364`. Holding those internal curves
fixed gives a **linearized estimate**, not a new simulation: feedback ratio
increases1.836571%, six original52.5µm lengths become approximately53.4642µm,
and VREF25 increases6.13353mV to approximately1.04548V. Final dimensions must
be rounded only after a declared PDK/grid check and then simulated; do not
silently substitute that rounded source into an old result. Source curve SHA:
`a74da41206c410fb2b4cef21cdc5fcac576940e86beb152ff875dfda5a66cb2c`.

This is a single design-time hardware coefficient based only on the nominal
curve. It is not per-device trim, fitted postprocessing of the100 samples,
a temperature calibration correction, or permission to relabel any original
failure as passed. Existing corner signed slopes−49.341…+11.197ppm/°C suggest
centring deserves examination, but all81 candidate corner/rail sweeps are
**not run**; no PVT pass is inferred by shifting old waveforms.

The pinned stock off-grid deck and technology file now establish a5nm drawing
grid, distinct from1nm GDS database units. The proposed single rounded length
is **53.465µm** for each of the24 XR17–22 parallel units: coefficient
`53.465/52.5 = 1.0183809523809524`, or+1.8380952381%. This rounding is frozen
from the nominal-only source curve before any candidate result. The first
in-memory grid audit produced an identical1.4×2.55µm resistor head/default
bbox for both requested lengths; it does **not** establish full-body geometry
or length binding. Preserve `rppd-grid-20260922-r1.json` as inadequate coverage;
corrected full-body grid verification is separately recorded below; stock
full DRC remains not run.

`rppd-grid-20260922-r3.json` now passes full-length coverage: explicit
`Calculate=R` yields exact1×52.5 and1×53.465µm PolyRes bodies, bbox height
L+1.22µm, all polygon vertices on5nm grid. The short-body r1 and intermediate
wrong-layer r2 failures remain preserved. This establishes length binding and
grid only, not placement, full DRC/LVS or electrical merit.

Exact proposed original-instance mapping (explicit independent unit instances,
all untouched devices preserved):

|Group|Original instance suffixes|Copies of each|
|---|---|---:|
|PTAT MOS XM|34,35,36,37,38,39,41,45,47,48,50,52,54|24|
|PTAT HBT XQ|56,62,67,68,69,70,71,72,73,74,75,76|24|
|PTAT resistor XR|16,23,24,25,26,77,78,79,80,81,82,83,84,85,86|24|
|VREF mirror XM|43,44,51|4|
|Qref XQ|60|4|
|VREF resistor XR, each53.465µm×1µm|17,18,19,20,21,22|4|

## Quantified area and power forecasts

The native PCell inventory is
`review/audits/bgr-selective-area-20260922-r1.json`. Per added selective loop
unit native bbox sum is2157.4664µm²; per Qref branch unit639.3074µm²;
baseline4159.8664µm². These boxes include legally shareable enclosures and
are neither legal placements nor rigorous area lower bounds.

| Candidate | Native bbox arithmetic | Baseline-overhead extrapolation | Nominal current forecast | Power at3.3V |
|---|---:|---:|---:|---:|
|Loop16/Qref4, unchanged R2|38,439.8µm²|96,250.4µm²|219.013µA|0.722744mW|
|Loop24/Qref4, centred R2|~55,731.9µm²|~139,549µm²|~317.574µA|~1.04799mW|
|Loop32/Qref4, unchanged R2|72,959.2µm²|182,684.6µm²|416.134µA|1.37324mW|

Power estimates use simulated baseline/loop16 anchors:
Ibaseline21.892569µA, incremental loop unit12.320039µA and Qref emitter
current4.106693µA. They assume nominal branch scaling; new candidate current,
centred-R2 finite-output-resistance effects, adverse/startup power and total
chip power with gm4 SENSE are **not run**. The<10mW total target remains.
Loop24/Qref4 would contain336 MOS,301 HBT including9 unchanged dummies,
399 resistor units, with an expected2842-parameter mismatch inventory.

At the retained1.9µm column pitch, loop24 R bodies alone consume33,903.6µm²;
contacts, Qref resistors and other devices still require space. Repacking,
a larger region within the existing die, or a justified die increase up to
2mm² must be evaluated against the *whole* floorplan including gm4 SENSE.
The1.8225→2.0mm² difference is177,500µm² of die area, not automatically usable
core area.

The physical owner's preliminary read-only
`review/audits/floorplan-area-options-20260922-r1.json` confirms this distinction.
The existing708×708µm gross core is501,264µm², with276,414µm² macro bbox union
and59,871µm² decap bbox union. Keeping other macros fixed and reserving the
current72,480µm² SENSE envelope, the largest macro-free rectangle is54,984µm²,
but26,802µm² of decaps lie inside; it is not available BGR placement area.

A square2mm² die would have side1414.2136µm,64.2136µm greater than the current
1350µm die. With fixed ring depth, the arithmetic gross-core increase is
95,049.8µm², not177,500µm². Moving the ring east/north yields a hypothetical
83,100.7µm² macro-free top strip, but this is not an implemented ring/PDN/pad
option. It can contain the loop24/Qref4 native bbox sum *arithmetically* while
falling below the conservative baseline-overhead extrapolation; that gap must
be resolved by actual packing, matching/guard, cut-current and route budgets.
The follow-up `floorplan-area-options-20260922-r2.json` includes exact gm4
source SHA`baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877`.
Native main-OTA MOS bbox sum is14,227.88µm². Baseline-overhead extrapolation
gives71,256.003µm² for whole SENSE, only1,223.997µm² below its reserved region;
legal folded matching, guards and routing are **not run**. Keeping the SENSE
reservation and existing decap bbox sum, loop24/Qref4 with rounded R2 has an
estimated490,176.544µm² aggregate reservation, leaving11,087.456µm² in the
existing gross core or106,137.242µm² in the expanded-core hypothesis. These
are fragmented arithmetic remainders, not usable routing budgets or placement.
The loop24 native estimate including retained resistor column pitch is
65,529.760µm²; the conservative baseline-overhead BGR estimate139,548.685µm².
Whole-floorplan fit and legal reduced resistor pitch remain **not run**, with
no geometry change or enlargement adopted. This supports prioritizing one
loop24 screening proposal over a parallel loop32 campaign, not adoption.

## Gates before adoption

1. Whole-floorplan candidate placement budget including gm4 SENSE, pad/ring
   movement if any, power grid/decap reservations, routing and fill. Demonstrate
   need and≤2mm² fit; do not assume bbox arithmetic is placement.
2. Review/freeze exactly one candidate mapping, coefficient/grid, source hashes,
   model/runtime pins and constraints. No statistical fitting or limit changes.
3. Bounded nominal/current-density/terminal probes and startup first; compare
   to original source and explicit proposed changes. Keep all voltage-model
   concerns. Preserve VREF/IPTAT and actual interface validity as separate gates.
4. All-parameter repeat/freeze/disabled-mismatch/reversed-temperature harness
   qualification. Then selected development controls43039,43068,43047,
   positive-tail43053 and passing43001. Equal seeds across changed source are
   not identical physical samples. These selected controls are not yield data.
5. Independent prospective100-sample screen and relevant PVT/startup/load/
   stability/noise/PSRR checks only after pilot timing and resource gates.
6. Physical candidate stock DRC/LVS/via-current/fill/route checks, frozen new
   PEX and requalification. New BGR source invalidates old-source adoption
   claims for the joint SENSE/TRIP and BGR/T2F chains: rerun their critical
   qualified calibration campaigns; do not combine old and new populations.

No new-source or solver launch is authorized by this document. The first
screening proposal, if approved after fit, remains one CPU/4GiB reservation,
120s DC-leaf bound and≤0.25GiB fresh storage gate. No local commit/staging is
performed by this worker; coordinator owns reviewed integration commits.

## Bounded design-control stage, before larger layout investment

The coordinator subsequently authorized a separate electrical-merit stage
despite unresolved legal packing: one nominal−40…125°C sweep and matched
baseline/candidate25°C current-density/external-terminal OP probes. This is
not MC, source adoption, a die enlargement or removal of physical-fit gates.
The candidate produced by `prepare_coordinated_candidate.py` is
`candidates/bgr_loop24_qref4_r253p465/bgr_loop24_qref4_r253p465.spice`, SHA
`53513ab43c62ead3a4c171f5a026b165e2a0bfda2b5b0cb5b104a30aae33a4e2`.
Its manifest freezes the exact2842 ordered unique parameter inventory and
950 added units. Reversing only those additions and the six original R2
lengths reconstructs every baseline byte (SHA72417e…9d77). Simulation is
**not run** at this prelaunch source-review checkpoint. Source current-density
preservation remains a hypothesis to measure; no parameter fitting is allowed.

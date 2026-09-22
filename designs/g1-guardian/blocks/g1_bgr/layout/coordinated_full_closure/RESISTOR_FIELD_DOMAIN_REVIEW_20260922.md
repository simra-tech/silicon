# Resistor-field domain: bounded remedy review

Status: read-only design review. No alternate field extraction, compact-model
split, source/card change, geometry change or candidate adoption has run.

## Established omission

The source-pinned native audit finds 399 PolyRes bodies, 19494.66 µm² total,
exactly equal to the sum of source W×L. Their intersection with extracted
`poly_con` is zero. Installed `res_mk`/`poly_con` rules and actual saved LVSDB
agree exactly; blackbox true/false does not change any of 24 present BGR layers.
This is an installed model-domain limitation, not a routing connectivity error.

| Overlying metal | Overlap with native bodies (µm²) | Affected resistors |
|---|---:|---:|
| M1 | 32.676 | 399 |
| M2 | 2729.694 | 399 |
| M3 | 2735.828 | 399 |
| M4 | 5678.054 | 398 |
| M5 | 28.272 | 2 |

These are projected overlap areas, not capacitance values or bounds. Fringing,
intervening-metal shielding and neighboring resistor-body coupling also matter.
The unchanged R3 CMC primitive already contains substrate area/perimeter C, but
has no port for an independently routed metal crossing its distributed body.
Neither arbitrarily connecting a body to one endpoint nor adding guessed C to
the current 979-entry matrix is a qualified remedy. Including a body changes
shielding and therefore can change existing metal-to-metal/substrate entries.

The first audit failed because it sought resistor bodies on GatPoly 5/0;
the pinned native generator places them on PolyRes 128/0. The failed helper and
receipt are retained. The corrected audit independently matches every native
body area to source W×L; it does not edit a layer or reinterpret a golden source.

## Primitive-first ownership

Any next representation must begin with `source instance → native PolyRes
polygon → two actual head terminals → physical substrate`, before grouping
global nets. Preserve 399 distinct resistor bodies, even where parallel replicas
share endpoint nets. Each coupling needs an owning primitive/surface and a stated
intrinsic-versus-extrinsic domain. Adjacent resistive bodies are not automatically
equipotential merely because one or both endpoints share a net.

FasterCap/fastcap executables are available in the pinned runtime, but a perfect-
conductor field solver alone does not represent longitudinal voltage variation
inside a biased resistor. Artificially cutting a resistive strip into separated
perfect-conductor pieces introduces nonphysical gaps; mesh refinement is not by
itself proof of equivalence to a continuous finite-conductivity strip.

## Smallest defensible next control (not launched)

Use a source-pinned local coupon containing an actual worst-overlap resistor,
its immediate resistor neighbors, actual crossing M2/M3/M4 conductors, relevant
contacts, dielectric stack and an explicit substrate boundary. Preserve native
dimensions and head positions; record all clipping boundaries and swept halo.
Keep each resistor body as a named *primitive-owned* conductor, not an arbitrary
global net. No full-macro 3-D job is justified before this control.

An equipotential/common-mode coupon can establish geometry translation, coupling
and shielding for that explicitly controlled condition. It cannot establish a
differentially driven distributed resistor model. Require dimensional/material
coverage, independent net ownership, symmetry/charge conservation/passivity,
mesh and boundary convergence, and a simple analytical geometry control. Do not
regularize failures away or omit small couplings without a reviewed error budget.

For the distributed case, a possible **new reduced-order model**, requiring
explicit review, is a primitive-local small-signal potential basis `v_body=T·v`
and energy projection `C_reduced=Tᵀ·C_field·T`. A partition-of-unity basis can
preserve charge conservation; projection of a valid positive-semidefinite field
matrix preserves passivity. This mathematics does **not** validate the basis:
linear interpolation is only a candidate low-frequency/uniform-strip hypothesis.
It must be compared against an independently resolved distributed RC/PDE model
over the required bias, PVT and frequency range, including intrinsic-charge
ownership. The original nonlinear R3 primitive must remain unchanged unless a
separate consequential source-model decision is authorized.

The combination must explicitly prevent double counting model-owned substrate
charge and must regenerate external shielding consistently. It is not sufficient
to append body-crossing C while keeping a field solution that omitted the body.
No empirical subtraction from golden capacitances, arbitrary endpoint weights,
or hidden splitting of the nonlinear compact model is authorized here.

## Decision and remaining checks

| Check | Status |
|---|---|
| Native/body ownership and all 399 W×L matches | passed |
| Body exclusion from current geometric CC input | passed, confirms omission |
| Intended body-to-cross-metal coverage in current view | failed |
| Corrected read-only geometry audit | passed |
| Common-mode field coupon / material translation | not run |
| Distributed potential basis / independent RC validation | not run |
| Quantitative electrical-error bound | not run |
| Adoptable complete-field parasitic view | not run |
| Changing/splitting golden nonlinear primitives | not applicable to authorized scope |

Escalation is required to choose a reviewed reduced-order approximation, a
validated distributed field method, or a physical-routing remedy with an explicit
error budget. The current raw CC and assumption-grounded view remain diagnostic.
Finite return-wire/current-cut work is independent and can continue.

# Draft: clarify tap geometry and electrical resistance cross-view semantics

Not submitted. No upstream issue, PR, model or rule modification has been made.

## Reproducer scope

IHP Open PDK commit `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`,
KLayout0.30.9 and the unmodified installed tap extraction/reader rules.
Original IO GDS SHA4281a855377b6a1ca46356e9391258dc14e8efc3b8051a65befc0fe9db3c7825;
CDL SHA7a30e902099e8a8f85e0ae853167904df3793357a793a7b4dc82237b72b3eec4;
SPI SHA1d53ab7df431b717ef5aff43e1117c0224681d5cc84886da37a319280ee958d6.

The prior pinned unit reproducer and raw reader evidence are retained in
the parent `RESULTS_20260922.md` and `UPSTREAM_ALTERNATIVES_20260923.md`.
This draft adds independent raw-polygon and source-ownership controls;
it does not use extracted A/P as replacement golden parameters.

## Confirmed discrepancy: rectangular physical tap versus supplied A/P

For `sg13g2_LevelUpInv.XR0`, the supplied CDL is
`XR0 vss sub! ptap1 A=1.051p P=4.1u`.
The independent active/implant/well/exclusion geometry gives a rectangle
of area1.053µm² and perimeter7.62µm. The unchanged native unit extraction
agrees with those dimensions. The tap reader treats A and P as physical
area and boundary perimeter, rather than converting an equivalent square.

Other cells include guard rings and more complicated geometry. A project-local
source correction is in progress. Its hierarchy/overlap accounting must be
resolved before a fullchip physical-dimension source is adopted. No global
counts or fitted aggregate values are offered as a replacement reference.

## Confirmed formula inconsistency; intended electrical convention requested

The pinned `ptap1.sym` and PyCell `CbTapCalc` compute conductance as
`A/(9.8e-10 Ω·m²) + P/(9.8e-4 Ω·m)`. In numerical micrometre units this
is `R = 980/(A + P)` ohms. The pinned `ptap1_ring.sym` emits a total
inner-plus-outer perimeter `P = 4(w+l−2rw)` for LVS but computes its
electrical conductance using **twice that same total perimeter**.

For a3µm×3µm outer ring with0.3µm uniform width, A=3.24µm² and total
P=21.6µm. The two formulas therefore evaluate to `980/24.84` and
`980/46.44` ohms. This is a source-expression distinction, not simulated
or measured process evidence. The ngspice tap wrapper uses the supplied R;
its w and l parameters do not independently resolve the convention.

Please clarify whether the ring factor is intentional and what expression
applies to arbitrary tap polygons or multiple disconnected same-net pieces.
We have not selected a factor to obtain LVS, altered the resistor model,
or claimed a new physical resistance is qualified by geometric LVS.

## Separate body-interface question

Original IO CDL/SPI contain local `SUB!` nodes without an explicit global
declaration. A project-local explicit VSS bulk-port derivative is independently
tracked and owner-authorized. Please clarify the library's intended assembly
contract; a trailing exclamation mark alone is not treated as an electrical
global-net declaration by our source parser. This question is separate from
both A/P and resistance and must not justify silently shorting supply domains.

## Disposition

Passed: pinned identities; isolated rectangle/raw geometry discrepancy;
literal rectangle-versus-ring expression comparison. Failed/unresolved:
current fullchip per-source tap ownership and complete source/native match.
Not run: new physical-R power sequencing/ESD, silicon measurement, upstream
submission. Not applicable: rule/model edits or extracted-as-golden repair.

## Subsequent geometry result (2026-09-23)

The original unresolved ownership statement above is retained historically.
Source-bound local ownership now passes for all 42 reachable local tap records
and 386 instantiated taps. The decisive distinction is the pinned local
`TIE ∩ SUB` junction, rather than the entire raw active TIE polygon. Three
source-local body clips explain the earlier aggregate discrepancy. The
independent raw-mask proof reads no extracted device parameter as an input.
Full native-context parity also passes on candidate GDS
`4cffddc5ae8369c9fd5c574cb9571b4641cdee26876370c93bfbe042c4049df2`.

The resulting physical-dimension CDL is
`796a724df08e1da81bbb43e6b54399e6ac338ff33db6a56535f8a89f91f24abf`;
the reversible tap-reader syntax derivative is
`d39ce8512f167545ab2818582bd1e51e88f6402ff810dcf3368cd7d277ddb4d4`.
Strict native LVS is in progress, not yet passed. These source changes do not
resolve the electrical resistance convention. Two explicitly conditional
electrical sensitivities are being prepared; they are not physical bounds.

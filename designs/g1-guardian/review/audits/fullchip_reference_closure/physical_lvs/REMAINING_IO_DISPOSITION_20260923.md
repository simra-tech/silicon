# Concrete remaining IO count differences

This is a read-only disposition, not a fullchip LVS pass. Saved comparison and
new native geometry audits retain original source, library GDS, rule decks and
model cards. The two geometry audits passed in 1.520 s and 2.050 s.

## Resistors: an implementable recognition correction, with explicit scope

The 557-versus-573 post-combination RPPD count has an exact decomposition:

| Source-owned structure | Count | Primitive source intent | Missing combined devices |
|---|---:|---|---:|
| SecondaryProtection | 14 | One W=1 µm/L=2 µm resistor per instance | 14 |
| RCClampResistor in VDD and IOVDD supply pads | 2 | 26 series W=1 µm/L=20 µm resistors per instance | 2, combined L=520 µm |

The 19 other unmatched RPPD records have the same dimension/count inventory
on both sides: eleven W0.5/L3.54 and eight W0.5/L12.9. They are not additional
missing resistor bodies; their terminal/substrate comparison remains failed.

All polygon layers of the current SecondaryProtection and RCClampResistor
cells have zero XOR against the pinned stock library. Both contain zero
PolyRes 128/0. For the RC cell, 26 existing GatPoly rectangles measure
1×20.86 µm including heads, with 156 physical contacts and existing serpentine
M1 connections. Independently intersecting GatPoly, SalBlock, EXTBlock and pSD
produces exactly 26 rectangular 1×20 µm bodies, with no contact overlap. This
agrees with the original 26 source statements before any extraction-derived
parameter selection. The same construction gives one 1×2 µm body in the
SecondaryProtection cell. Missing recognition leaves the native RC input and
supply on one extracted conductor; it does not prove the fabricated resistor
is a physical short.

An ordinary isolated design candidate can add exactly these source-supported
128/0 bodies in namespaced local cells, preserving every other polygon, text,
instance transform and logical pin. Required checks are all-layer XOR equal
only to the declared bodies, no contact/body overlap, unchanged source intent,
affected stock main/maximal DRC and strict device-aware LVS. The RC source
must remain 26 devices before stock combination, not a hand-fitted L520 device.
The prior SecondaryProtection marker experiment extracted the intended
resistor and passed hard/recommended DRC but retained other LVS failures.
New RC and fullchip candidate checks have **not run**.

This can be a declared design-layer correction; it must not be represented as
proven fabrication-mask-inert annotation. Public process documentation calls
PolyRes a resistor marking layer but does not establish that broader claim.
No source/model parameter or rule change is needed for the isolated candidate.

## PMOS: stock purge of explicit all-VDD dummy devices

The single post-combination PMOS difference is the three LevelDown source
`MP0` instances, each W4.65/L0.45 µm with all four terminals at VDD. Stock
source combination makes one W13.95/L0.45 record. The current LevelDown cell
is polygon-identical to the stock cell. Existing native dummy geometry and
connectivity evidence and the pinned unconditional native `purge_devices`
explain why this all-shorted device class is absent before comparison.

It is not evidence of a missing functional PMOS and does not justify adding
another transistor. A separately proven extraction-reference dummy exclusion,
analogous in principle to the explicitly retained BGR grounded-dummy proof,
could be a legitimate view boundary: three exact source records, all four
actual physical terminals, native area/dimensions and pinned purge behavior
must be bound. Canonical electrical/source records must remain present.
That current-chip three-record exclusion proof/candidate has **not run**;
the stock original-reference mismatch remains **failed**.

## Diodes: multiplicity and substrate ownership, not missing diode area

The DANTENNA primitive-count difference is −2, but all mismatched DANTENNA
records have equal summed multiplicity on both sides: 64. Native unmatched
records include two m=4 groups, whereas four unmatched source records have
m=2. The source model A=35.003 µm²/P≈58.08 µm also differs from native
A=35.0028 µm²/P=58.08 µm; no tolerance change is proposed.

The current DCNDiode is polygon-identical to stock. Actual parent connectivity
combines physical substrate terminals; source `SUB!` remains local without an
explicit declaration. A comparer-selected pair is not an independent instance
correspondence, so equal total multiplicity is only accounting—not evidence
that a specific diode may be removed or that local body nodes may be joined.
No diode addition/deletion is justified by this count delta. A complete
source-owned body/interface reconciliation is required before claiming the
diode comparison fixed.

## Taps: unresolved electrical model/interface contract

The reversible source-prefix adapter is an ordinary faithful syntax fix and
its reader controls passed. It exposes 386 reachable original tap records:
151 TIE=VSS, 235 TIE=IOVSS, and 243 locally scoped WELL nodes. Native extraction
instead has two combined tap devices with WELL on physical VSS. Source A/P
values encode equivalent-square perimeter and reproduce the original SPICE
tap resistance; raw guard shapes have different perimeter and sometimes area.
Thus changing source A/P to extracted values changes electrical model intent.

The original IO source chunk is byte-preserved in the fullchip assembly, so
absence of `.GLOBAL SUB!` is not a newly introduced assembly omission. Neither
an exclamation mark nor a global declaration proves `SUB!` equals VSS. A
source-held design interface needs an explicit justified substrate model and
reference semantics; adding a global or a zero-ohm body short solely to force
LVS is not such a justification. VSS and IOVSS must remain distinct metal nets.

| Check | Status |
|---|---|
| Exact current/stock geometry and source-supported resistor bodies | Passed |
| Full residual device/net accounting, including non-IO records | Passed |
| Faithful tap syntax and physical port metadata controls | Passed |
| Strict current fullchip comparison | Failed |
| Isolated resistor-marker repair and affected DRC/LVS | Not run |
| Three-dummy extraction-reference proof/candidate | Not run |
| Substrate/guard-model applicability and final diode/tap reconciliation | Not run; unresolved |
| Rule/model-card edits or forced net-join hints | Not applicable; prohibited |

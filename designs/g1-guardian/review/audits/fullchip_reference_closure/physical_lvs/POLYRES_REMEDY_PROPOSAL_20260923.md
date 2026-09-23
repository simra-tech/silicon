# Separate IO resistor-recognition remedy proposal

No IO geometry, original reference, PDK file or rule deck has been changed by
this proposal. This is separate from the source-only tap-prefix adapter and
the unchanged-input flat extraction experiment.

## Established facts

The current sealed chip's `sg13g2_SecondaryProtection` has zero polygon XOR
against the pinned stock cell on every layer. Both lack PolyRes 128/0. The
saved native comparison consequently omits the source's W=1 µm/L=2 µm
`rppd` series resistor and reports a combined `core,pad` conductor. The
original source and all of its parameters remain held.

This is not a new speculative remedy. The retained
[recognition diagnostic](../../io-recognition-20260921/manifest.json)
added precisely `[0.94,1.37;1.94,3.37]` µm on layer 128/0 within the existing
GatPoly/SalBlock body. All other polygon layers were unchanged. The unchanged
stock deck then extracted the intended series resistor and the merged
`core,pad` discrepancy disappeared. The diagnostic's overall LVS **failed**
because independent IO/tap problems remained. The subsequent unchanged
hard/recommended DRC comparison found zero markers in both original and
annotation-only variants; see
[the retained topology report](../../IO_TOPOLOGY_20260921.md).

## Pinned process boundary

The installed public `SG13G2_os_layout_rules.pdf` layer table describes
PolyRes drawing 128/0 as marking net resistors. The pinned
`res_derivations.lvs` lines 36–46 require PolyRes intersecting EXTBlock and
GatPoly, with the pSD/SalBlock conditions, to recognize `rppd`.

That establishes extraction recognition, **not an unrestricted claim of
fabrication-mask inertness**. The same layout-rules document's section 3.1
explicitly lists layers not considered for mask generation; PolyRes is not
in that list. This omission is not proof that PolyRes is fabricated either.
The final process/mask-generation interpretation is unresolved from these
two statements alone. No foundry approval is inferred from a clean DRC run.

## Bounded candidate, if separately authorized

1. Keep the stock library and held assembled GDS immutable. Make a distinctly
   namespaced design-local derivative of the leaf and only its required
   hierarchy ancestors. Preserve source logical interfaces and instance
   placement; record an exact alias/ancestry mapping.
2. Add only the independently specified 1×2 µm recognition rectangle. Require
   exact local/assembled XOR equal to those transformed 128/0 additions, zero
   XOR on every other polygon layer, and exact native text, pin, transform,
   device-body, contact, well, guard and metal inventories.
3. Recheck marker enclosure against the actual native body, EXTBlock and all
   extraction exclusions, with negative controls for misplaced/oversized
   rectangles. Do not infer matching from its bounding box alone.
4. Run unchanged main/maximal DRC and strict IO-inclusive LVS using source-held
   model, node, width, length and A/P parameters. Preserve the original failure
   and all remaining tap warnings, missing ports and unexpected device counts.
   A separate tap-prefix syntax adapter must have its own exact reverse/source
   and pinned-reader controls; it cannot replace physical A/P with extraction.
5. Resolve mask-generation applicability before treating this derivative as
   an adopted fabrication input. An extraction-only annotated view may be
   investigated with explicit scope, but is not a pass of the original native
   input and does not establish IO electrical/ESD equivalence.

| Check | Status |
|---|---|
| Current failing leaf equals stock polygon geometry | Passed |
| Missing recognition and original source intent localized | Passed |
| Prior bounded annotation extracts intended resistor | Passed |
| Prior annotation-only hard/recommended DRC | Passed, zero markers |
| Original and diagnostic overall IO LVS | Failed |
| New namespaced current-chip derivative | Not run |
| New complete main/maximal/LVS/electrical/ESD qualification | Not run |
| Fabrication-mask applicability of the marking layer | Not run; unresolved |
| Rule-deck or model-card changes | Not applicable; prohibited |

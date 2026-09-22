# Computed-layer geometry repair and remaining field boundary

An isolated generic selector fixes the demonstrated computed-layer/GDS alias
without changing the installed extractor, technology, rules, models or GDS.
Computed requests select their exact LVS identity, preserving polygon/net
properties. Canonical requests retain the stock fallback. Missing computed
identities return no geometry; ambiguous duplicates fail closed.

Saved full-SENSE-r5 and7×7MIM coupon controls passed:43 computed identities
and20 canonical fallbacks per case, plus26 and2 M5 net memberships. Native
M5 union, MIM intersection, partition overlap and geometry XOR checks pass.
The audit completed in13.989s without meshing or a solver. Nine synthetic
identity/property/isolation/fail-closed controls also passed. Their first
test-only attempt failed on an unsupported Box API spelling and is retained.

The coupon's native domain builder was independently observed before mesh
generation. This runs its unchanged conductor/dielectric construction and
stops only at the meshing boundary:

| Domain | Stock area µm² | Exact computed identity µm² |
|---|---:|---:|
| M5 designated capacitor bottom |67.24 |49 |
| M5 designated non-capacitor |67.24 |18.24 |
| MIM dielectric `ismim` |67.24 |49 |
| Thin MIM top plate |49 |49 |
| TopMetal1 access |39.69 |39.69 |
| MIM vias |4.41 |4.41 |

The physical M5 conductor union is67.24µm² in both cases, but the original
alias also assigned MIM dielectric over the access region. Correcting its
identity repairs that domain error. All stack dimensions and material
permittivities remain unchanged. Thin top plate and thick TopMetal1 access
are separately represented; their shared net does not make the access an
intrinsic plate.

The actual MIM via drawing is129/0. Its extracted `mim_via` identity uses
virtual125/10; this is not a claim that native drawing125/0 is the via.
A follow-up audit initially used125/0 as the oracle and failed4.41µm² XOR.
The error is preserved; the revised native oracle is129/0, independently
established from the saved GDS and computed technology mapping.
The corrected audit passed in10.969s: all five native layer unions have
zero XOR, and both native primitive terminal masks bind exactly to their
corrected conductor domains. The stock bottom-domain/native-terminal XOR
is18.24µm²; the corrected value is zero. These are pre-mesh geometry checks,
not an extracted capacitance or final meshed-boundary result.

## What remains unqualified

The pinned2.5D technology maps `cmim_top` to canonical name `<TODO>`.
Its substrate/overlap/fringe tables have conventional-metal entries but no
thin-MIM entry. Owner-aware geometry propagation alone therefore cannot
qualify complete2.5D MIM extraction with the existing tables.

The3D geometry domains can contain native plates, vias and access metals, but
the inspected API still aggregates capacitance by electrical net and exposes
no primitive-owned field-pair decomposition. The canonical MIM model owns
both area and perimeter capacitance. Dropping the complete same-net pair
would also drop routing/access coupling; appending the full whitebox pair
would double-count intrinsic capacitance. Neither is performed.

Thus the geometry-query defect is repaired in an isolated, tested adapter;
**complete source-preserving MIM CPEX remains blocked by the model/field
composition boundary**. No field solve, model-capacitance subtraction,
pseudo-net split, coefficient fitting or intrinsic-model replacement follows
from these checks. Final meshed-domain completeness, later-r8 fields and
full-macro3D are **not run**. Supporting another composition method requires
an explicit validated model/extractor contract, not a tolerance waiver.

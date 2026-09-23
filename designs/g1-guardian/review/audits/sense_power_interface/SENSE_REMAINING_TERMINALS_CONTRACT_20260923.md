# Remaining SENSE terminal support geometry

The bounded native support inventory **passed**. This continues the
source-held r8 geometry branch;
no source, compact model, primitive identity, mismatch path, GDS or port
annotation changes are proposed. No simulator or resistance solve is part
of this step.

The completed all-Cont network covers 41,384 actual contact footprints and
all 134 metal nets. Geometry ownership covers 370 of 541 source slots.
The other 171 slots are 58 MOS body, 98 resistor BN, six MIM and nine macro
ports. Contact classification is not a terminal-current allocation.

## Prospective read-only screen

Use exact r8 GDS `8060e30a...`, canonical source `baab6183...`, the bound
reference manifest and completed all-Cont classification. Require source
hashes before and after, exact 835 gate/channel identities, original 58 MOS
and 134 source nets. Save JSON only; no candidate GDS.

1. For each PMOS, locate all source-owned channel polygons in actual NWell
   components. Enumerate the material-proven well-tap contact support sets
   inside those same components and check their actual metal source net.
   A missing or ambiguous well association is an explicit failure, not a
   nearest-contact fallback. This does not select the compact-model body
   reference plane or assign weights through the finite well.
2. For each NMOS and resistor BN, report source-defined substrate net and
   the existing compatible substrate-tap pool separately. Do not turn the
   pool into a claimed local substrate path: the layout alone does not
   supply a three-dimensional spreading-resistance/current-distribution
   contract. Preserve source body/BN identity and any unresolved isolation.
3. For each of the three MIMs, identify its exact native layer-36 plate
   from the source-bound witness. Enumerate actual Vmim (129) footprints,
   top-metal coverage/net membership, and underlying M5 plate overlap/net
   membership. Do not replace Vmim with TopVia1 or append a second intrinsic
   capacitor. Physical support geometry does not resolve the canonical
   model's electrode/series-resistance ownership.
4. For each of the nine macro ports, enumerate the actual top-cell pin
   polygon and matching same-layer label, exact source net and metal
   coverage. Preserve all pin polygons. A pin polygon is not automatically
   an equipotential injection boundary; the fullchip route attachment is
   a separate interface.

Deduplicate shared support sets by exact geometry and report each slot's
membership without expanding one logical model into multiple devices.
Require all contact polygons to be existing native geometry and all metal
membership to agree with the already checked 134-net graph. No invented
contact, nearest-node assignment, uniform sharing, or independent body/BN
node insertion is permitted.

## Runtime and disposition

One pinned KLayout process, at most 120 seconds and 0.1 GiB new output, after
an explicitly allocated CPU and fresh global resource gate. The completed
run took 15.444 wrapper seconds and 3.779 geometry seconds. This is a support-geometry inventory,
not closure of 171 compact-model attachment slots. Complete model-boundary
applicability, distributed nonlinear current response, full-parameter and
waveform zero-R parity, IR/EM and adoption remain **not run**.

The exact passive-coupon parity failures remain unchanged. No further
numerical coupon variants are proposed by this contract.

## Completed geometry result and consequential boundary

All 171 records are present, with exact source/native hashes held. There are
ten NWell components and 6,223 physically classified well-tap contacts.
All 33 PMOS body slots have explicit same-well support sets. Two logical
main-input MOS devices each have channels in **two separate NWell
components**. The other 31 PMOS devices each occupy one component.

There are 15,581 compatible substrate-tap contacts. The 25 NMOS B and 98
resistor BN records reference that pool without asserting a local spreading
path. All 98 source-owned resistor bodies have zero projected NWell overlap;
that two-dimensional observation does not prove a substrate impedance.

The three MIMs have 972, 324 and 324 actual Vmim cuts, respectively. Their
native plate areas are 1,587, 529 and 529 um²; all top and bottom metal-net
memberships pass. All nine source port pin polygons and matching labels are
present and covered by the correct native metal. No new GDS was saved.

This makes the remaining issue concrete: a logical four-terminal PSP model
offers one scalar B terminal, while its physical fingers can occupy more
than one well and see distributed metal/well potential. Same-net connectivity
alone does not make those local body potentials equal. Choosing one tap,
uniformly weighting contacts, splitting the logical MOS, shorting all tap
nodes, or adding a substrate mesh without an ownership contract would change
the model boundary. None is adopted here. The source internal body network
must not be double-counted by an external network.

Next decisions require either a supported compact-model reference-plane and
distributed-contact convention, or an explicitly conditional sensitivity
contract whose results are not substituted for physical qualification.
The existing exact passive-adapter zero-R failure remains independent; this
geometry result does not waive it or justify further numerical variants.

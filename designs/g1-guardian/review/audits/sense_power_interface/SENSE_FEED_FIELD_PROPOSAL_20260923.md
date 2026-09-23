# Affected field verification for the four SENSE feeders

Prepared only; native adjacency inventory, clipping, extraction, AC and
electrical checks below are **not run**. This is a new branch outside the
completed feed-remedy evidence. Canonical source, cards, rules, primitive
geometry and mismatch identities remain fixed.

## Inputs and first bounded operation

Use original r8 GDS `8060e30a...`, isolated feeder candidate `4b8a82d4...`
and exact source `baab6183...` as fully pinned in
`prepare_sense_feed_field_inventory.py`. No new fullchip source is assumed.
The first operation is one native process, at most 120 s / 0.02 GiB output,
after a separately allocated CPU and fresh resource gate. It writes JSON
only: no GDS, PEX, solver or electrical model.

Require all four M2 additions and 32 Via1 cuts to equal the exact candidate
minus baseline, with all other geometry exact. Reconstruct both complete
134-net source graphs independently. For every changed feeder, inventory
all neighboring ordinary-metal source identities and the projected
primitive layers in prospective windows. Unassigned metal is explicitly
unassigned, never inferred to be ground.

Four candidate sites per feeder are the longitudinal middle, first and
last groups of new cuts, and M2/M3 trunk. Each uses a fixed 20 um
longitudinal interval and transverse contexts of 24 / 48 um. They are
proposals, not automatic extraction authorization. Exact changed-area
coverage and uncovered area are reported. Overlapping windows cannot be
summed into a full-route capacitance. Original and new geometry at each
target point must belong to the same source-bound rail.

## Prospective first paired pilot

After inspecting that inventory, freeze one representative feeder/site
and every physical conductor's source membership, exact window, hashes
and labels. Start with only that site's baseline/candidate at the two
contexts: four extractions, no 200 um full-strip retry. Each extractor
child is limited to 120 s, AC child 30 s, and the pilot to 128 MiB growth.
A timeout or missing conductor stops expansion; there is no watchdog
ladder. The second feeder/site requires measured scope and cost review.

Use unchanged supported ordinary-metal extraction, preserving exact
M1–TM2/via geometry and unique labels for physically disconnected clipped
components. Independently proven same-full-net components may be grouped
only as a declared ideal outside-window diagnostic boundary; labels must
not create physical joins. Save the complete source-net-group capacitance
matrix, not only one favored mutual term. Retain floating versus grounded
fill as distinct diagnostics if any actual fill is present. Zero fill is
reported explicitly, not replaced by synthetic fill.

Require exact clip XOR, target membership and component accounting,
finite passive matrix terms, existing synthetic controls, finite Schur
charge residual at most 1e-25 F, and all declared independent AC checks.
Keep the existing **1% transverse-context criterion unchanged** for every
reported baseline/candidate load and mutual term, not only their difference.
A zero denominator without the already defined valid comparison is a
failure, not an epsilon or absolute-tolerance replacement. Signed candidate
minus baseline terms must retain signs. A negative delta is not an
independently insertable negative physical capacitor.

A local ordinary-metal diagnostic does not include Active/Poly/depletion,
substrate spreading, device-owned fringe or complete MIM extrinsic fields.
Their projected presence is inventoried explicitly. Even a converged
ordinary-metal delta cannot simply be appended to canonical compact models:
changing upper metal can alter field interactions involving device-owned
conductors. Required ownership/deembedding and final filled/fullchip context
remain separate. No electrical pass transfers from the previous clock or
SENSE input-route fixtures to these four source feeders.

## Concrete terminal-composition boundary

The supported PSP instance has one D/G/S/B terminal set. Its internal
gate/body network and geometry conventions are fixed by the pinned model.
The completed native ledger instead has many contacts per logical terminal,
48 shared diffusion strips and two separate NWell components for each main
input logical device. The native R extractor's PolygonPort is only a node
marker. It supplies neither a device current-distribution law nor an
equipotential terminal surface.

Therefore the finite-R problem cannot be closed merely by assigning every
contact to the correct logical source net. Any single point, weighted
average, ideal equipotential plate, finger split or replacement multiport
device makes an additional consequential model assumption. No supported
distributed external-terminal API has been established. The failed passive
coupon exact-time/wave comparisons remain failed; no new numerical variant
is proposed.

The next implementable **source-compiler control**, independent of any
finite-R attachment, is an exact-zero-metal-R canonical-restoration test:
set only the external ordinary-metal graph edges to zero in that diagnostic,
contract them, check the 134-net bijection,
retain all 58 MOS / 98 resistor / 3 MIM source lines and physical mismatch
paths, and require the emitted canonical source to be byte-identical after
the declared temporary-net inverse. Any future actual composed-deck zero-R
test must also pass all 11,512 parameters and the original exact waveform
criteria; byte restoration alone is not that run. This is a necessary
compiler/provenance control, not finite-R physical applicability.

Finite-R adoption still requires either a supported device-owned terminal
reference-plane/distribution contract, or an explicitly reviewed approximate
composition with justified error bounds. The latter is a consequential
method choice and is **not authorized by this proposal**. Current bounds
are incomplete and the existing global metal-graph coefficients are too
general to justify an unproved terminal-weight approximation. No tolerance,
model card, calibration acceptance or mismatch identity is changed here.

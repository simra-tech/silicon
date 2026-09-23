# Three-instance LS feed gate

Source-native `g1_ls_up.gds` SHA256
`85de277ca1c2de41fa59e577db1d6d7633edddb24abf3b6d57e6787afd335546` stays fixed.
The source PNL/OpenDB inventory binds three separate instances: `u_ls_en`,
`u_ls_r4`, `u_ls_mode`, each with VDD, VDDA and VSS. Repeated cell-local cluster
numbers are not global identities. Require nine distinct pre-feed physical
pin components in a flattened verification-only metal view.

Prospective access is inside actual M1 pin windows: VDDx734/754/774,y500;
VDDAx739.3/759.3/779.3,y501.4; VSSx734/754/774,y490.575 µm. Each has3 Via1
and3 Via2 cuts. Separate0.8 µm M3 collectors connect like-named source nets.
Root handoffs are VDD TM1(750,500) and VSS TM1(774,490.575); each uses3 Via3,
3 Via4 and4 TopVia1 cuts. VDDA ends at M3(783,501.4), initially unpowered.
No new route crosses the SENSE macro to reach the shared VDDA bus in this gate.

The first screen failed before GDS save against actual PDN lower feeders;
that failure is retained. The read-only flat corridor inventory identified
the complete root-net regions independently of repeated cell names. Revision2
uses those proven regions for same-net contact classification, without ignoring
existing-cut spacing. VDDA native M1 access shifts to x739/759/779, extends
with0.30 µm M1 to a new Via1/Via2 landing at y502.7, then joins the0.8 µm M3
collector at y503.0 and the unchanged unpowered handoff(783,501.4). This avoids
the core-VDD M2 feeder crossing the middle native pin. Last-instance VSS access
is x776 within its original M1 window. New root stacks move along the same
unchanged spines to VDD(750,499.5), VSS(774,488), avoiding existing cuts.
All74 cut identities remain newly drawn and independently checked. The original
requested root points remain on the same continuous existing TM1 spines.

Total74 new cuts. Each branch target0.1 mA and three-branch aggregate0.3 mA
are provisional layout-screen assumptions, not operating bounds. The retained
0.16 µm native M1 source neck motivates caution (engineering half-table0.18 mA),
but this is not a complete native source/contact/return-current audit. Actual
transient currents, sharing, current crowding and hot lifetime remain unqualified.

Required build gates: exact native/source hashes, every actual pin ownership,
all-layer foreign-metal/cut screen against frozen PDNr4, no cross-net new-route
contact, exact saved additive/native-text comparison and flat post-feed pin
binding. Require three VDD pins to root VDD, three VSS pins to root VSS, and
three VDDA pins to their separate unpowered handoff; all three domains distinct.
Then run every-new-cut-open, unchanged isolated/main/maximal stock checks and
actual final signal context. Preserve failures and all not-run gates.

Initial build bound360 s/one CPU, expected external growth0.15 GiB. No canonical
source, primitive, port annotation, model, rule deck or existing spine changes.

# BGR586 coordinated routing review — not routed

Use hierarchical, source-net-aware collection: M1 native contacts, short M2
terminal escapes, reusable M3 row segments, and a small number of dedicated
inter-bank trunks. Preserve every device position and all 50 replicated-group
centroids. Do not scale the original 84 × 124 µm track map to this 420 × 354 µm
placement or connect individual replicas directly to one global bus.

This read-only audit checks source lines, replica counts, point centroids and
projected track demand. It does **not** establish legal routed placement. No
production geometry, CDL, circuit source, PDK rule or model was changed.

## Frozen inputs and scope

| Input | SHA256 / identity |
| --- | --- |
| [Exact source586](../sim/qualification/candidates/bgr_loop24_qref4_r253p465_hv06/bgr_loop24_qref4_r253p465_hv06.spice) | `586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b` |
| [Refreshed pack](../../../review/audits/coordinated-bbox-pack-586-20260922-r1.json) | `2663805a5180a1961850c1068b0c1c3615c010cd2ec47d38a228d65dde4800cb` |
| [Original routing/contact generator](g1_bgr_layout.py) | `dee7f8fa5ab94165946e342625ed72c00e6a174592bb47a0af9f9054b8ce171e` |
| Existing isolated MOS stock summary | `1019a2233428e4331c2402802a2bb391fb99d972284fd0598ba827c3c966f0b7`; eight DRC and two LVS checks passed, independently read |
| PDK / geometry tool used by those stock checks | IHP `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`; KLayout 0.30.9 |
| This numeric audit | Python 3.6.8 standard library; no geometry engine or solver |

The [under-ring access plan](../../../review/audits/BGR_UNDER_RING_ACCESS_PLAN_20260922.md)
was written for source535. Its strategy remains a proposal; its source identity
must not be copied into this implementation. The refreshed pack retains all
positions except the declared right-edge/reservation growth of XM31/XM33 for
their 0.6 µm gate length. Their native origins remain fixed.

## Quantitative terminal and replica audit

Every one of the 1,036 packed `source_line` strings exactly matches its named
device in source586. There are 86 original names: 40 groups of 24 units, ten
groups of four units, and 36 singletons. All 50 stored replicated centroids
match recomputed native-bbox center averages within 1e-8 µm. This does not
establish electrically balanced routing or orientation matching.

| Zone | Devices | Source terminal incidences | Distinct nets, including supply/body |
| --- | ---: | ---: | ---: |
| Resistor | 399 = 384 rppd + 15 rhigh | 1,197 | 40 |
| HBT | 301 | 1,204 | 8 |
| PMOS W10 | 77 | 308 | 11 |
| PMOS W5 | 156 | 624 | 8 |
| NMOS W10 | 96 | 384 | 6 |
| Startup MOS | 7 | 28 | 9 |
| Total | 1,036 = 336 MOS + 301 HBT + 399 R | 3,745 | 55 globally |

Counts use D/G/S/B for MOS, C/B/E/substrate for HBT and two resistor ends/body.
Thus 1,036 incidences are explicit body/substrate terminals and 2,709 are other
terminals. These are **not** required independent via counts: same-net local
straps and shared legal body contacts can consolidate access, whereas current
and reliability requirements can require multiple cuts per connection.

| Largest source-net loads | Terminal incidences |
| --- | ---: |
| vss | 933 |
| vdd (BGR analog supply, to chip VDDA) | 316 |
| vbe | 313 |
| c2 | 240 |
| dvbe | 216 |
| pbias | 205 |
| pcasc | 149 |
| vb2 | 144 |
| d1, d2, d5 | 96 each |

The eight Q2 originals each have 24 replicas: 192 HBT emitters on `dvbe`,
192 collectors on `c2`, and 192 bases contributing to `vbe`. Other HBT emitter
loads are 85 on VSS (including nine original dummies) and 24 on `vd2`. Never
tie all emitters to the substrate guard. PMOS well/source domains are 24 d1,
24 d2, 24 d5, four d3, one d4 and 158 vdd: six distinct well nets. Distinct
domains must not merge even where their replicas are adjacent.

The replicas are electrically parallel **per original source device**, not
24 independent complete circuits. For example every XR77 replica shares
`n_4` and `pbias`, and every XR78 replica shares `n_11` and `n_34`. Preserve all
these common intermediate nets. Replacing them with separately named replica
chains is a topology change, even if a nominal resistance happens to match.
Do not copy the original generator's resistor-chain ordering by instance index.

## Track demand and actual bottlenecks

The table uses the original recipe's 0.3 µm signal wire and proposed 0.6 µm
track pitch. This pitch is a planning assumption, not a replacement for stock
spacing checks. `0.3 + (N−1)×0.6` gives occupied signal-track width.

| Location | Quantitative finding | Routing consequence |
| --- | --- | --- |
| HBT rows 7 and 11, zero-based | Five simultaneous signals: c2/dvbe/vbe/vd1/vd2; 17 devices per row; 4 µm native inter-row gap | Five tracks occupy 2.7 µm; adding 0.8 µm VSS and 0.3 µm separation occupies 3.8 µm before turns, edge clearance or larger landing pads |
| Other HBT rows | Zero to four non-VSS nets, except rows 7/11; common Q2 rows have three | Reuse shorter tracks locally rather than reserving all seven HBT signals in every row |
| Resistor rows | 33 and 32 non-VSS nets, but only six overlapping per-row net-center intervals at the worst horizontal cut | A naive 33-track global channel is needlessly pessimistic; interval segmentation is essential |
| PMOS W10 row 1 | Nine non-supply signals; only three overlapping net-center intervals within that row | Collect local drain/body domains separately; a nine-track full-width bus is not required, but inter-row links add demand |
| NMOS W10 rows | Five non-VSS nets in every row; five overlapping intervals in the center row | This is a genuine shared channel demand, not removable by merely renaming tracks |

Actual native bbox gaps are not empty contact-routing channels. Translating
the passed MOS prototype **bbox recipes** to the fixed pitch gives:

- PMOS rows: 4 µm native gap minus 1.78 µm upper well/tie growth and 0.88 µm
  lower gate/TGO growth leaves 1.34 µm between full prototype bboxes.
- NMOS W10 rows: 4 µm minus 0.81 µm upper and 1.61 µm lower guard growth leaves
  1.58 µm vertically. Horizontally, the 6.22 µm pitch minus the prototype's
  5.94 µm full width leaves 0.28 µm between full bboxes.

These are geometric arithmetic checks, **not** new DRC results and **not** a
proof that M3 routing is impossible: wells/guards on lower layers do not block
all upper routing layers. They do show why via landings, M1/M2 escapes and
same-layer guard spacing need an actual neighboring-device test. A track may
need to pass over a device or well, introducing capacitance that the rectangle
pack does not account for. PMOS gate nets `pcasc`/`pbias` and NMOS `vb2` can be
collected over their rows on M3 if a separately checked M2 access map permits it.

The HBT native bank spans x10–187.9 µm; its 2 µm reservations reach x189.9.
The PMOS W10 reservations begin x202.0, leaving a nominal 12.1 µm inter-bank
corridor. HBT `vbe`, `c2`, `dvbe`, `b1b`, `vd1`, `vbe3` require connections
outside the HBT bank; `vd2` can stay bank-local. Six 0.6 µm-pitch signal tracks
occupy 3.3 µm before wider precision returns, shields, via enclosures and turns.
Do not try to fit all 17 cross-zone signals into this one corridor: d1–d5
belong to the eastern PMOS interface, not the western HBT trunk.

### Concrete resistor channel decomposition

A provisional assignment of each resistor's first listed end to its bottom
head and second end to its top head gives three horizontal collection bands:
below row 0, between rows, and above row 1. This is a proposed terminal mapping
to verify by extraction, not a claim that extracted pin order supplies physical
orientation. The computed local interval demands are:

| Band | Resistor-end incidences | Non-VSS nets | Maximum overlapping local intervals |
| --- | ---: | ---: | ---: |
| Lower | 200 | 14 | 4 |
| Middle | 399 | 33 | 5 |
| Upper | 199 | 18 | 2 |

The middle native-bbox gap is y64.685–72.000, or 7.315 µm. Collect short runs of
same-net heads on M3, with M2 drops from M1 heads, then connect segment ends
through assigned M2 columns. Twenty-seven resistor end nets occur in both
rows, including VSS, so local interval counts do not include all inter-band
trunk extension and bend costs. Prove a full net-conductor graph; interval
coloring alone is not routing. Use the lower and upper bands as well as the
middle band to avoid opposite-end escapes occupying the same M2 column.

The R1 group XR16 is particularly demanding: its 24 units span 379.5 µm in x
and 114.725 µm in y, with twelve at the lower-left and twelve at the upper-right.
Preserve a dedicated low-resistance collection tree from all XR16 VSS ends to
the reference HBT-emitter return tree, joining general VSS at a defined star.
The 24 XQ56 reference units themselves span the HBT bank; one original short
R1-to-ring jumper cannot implement this distributed return. Keep guard/startup
return current off the precision branch as far as physical topology allows.
The electrical net remains VSS; route-ownership tags may distinguish precision
and general-return conductors without changing the source nets. Equal replica
resistance/current sharing and substrate-mediated error are not established.

## Concrete full-source grouping strategy

1. Build a source-derived terminal ledger keyed by `(instance, terminal)` and a
   physical contact ledger keyed by native PCell origin. Preserve exact W/L,
   HBT dimensions, resistor dimensions, and fourth-terminal nets. Attach
   replicated-group and route-role tags without changing names or topology.
2. Route native contacts and local same-net straps first. Keep HBT substrate
   returns separate from dvbe/vd2 emitter access. Retain exactly nine dummy
   HBTs. Reuse the passed MOS contact recipes only with adjacency checks; the
   two isolated LVS passes do not cover every bulk configuration in the array.
3. Form segmented M3 row collectors and short M2 escapes. Allocate local
   resistor intermediate nets by actual source connectivity. Avoid one bus
   per original group where multiple groups share a source net, but retain
   branch resistance and path-length diagnostics by original group.
4. Join HBT rows through western/central bank trunks. Route d1–d5 locally
   between eastern cascode and mirror rows, with pbias/pcasc/vb2 distribution
   trees and short protected vref/iptat escapes. Match reciprocal replica
   paths where practical; unchanged point centroids do not compensate for
   unmatched route capacitance or common-impedance error.
5. Reserve distributed supply/body/guard returns separately from precision
   R1/emitter collection. Use redundant cuts where required, without assuming
   equal sharing. If M2 columns cannot cross row collectors legally, review
   selected M4 inter-bank trunks with explicit Via3 landing and coupling
   checks. M4 is a proposed new routing choice, not an inherited pass.
6. Only after lower-metal connectivity closes, add source-mapped VDDA/VSS
   accesses against the **actual expanded ring and grid**. BGR source `vdd`
   is analog VDDA, not the nearby core VDD ring. No blind TopVia placement at
   a crossing. Preserve the no-upper-metal-short requirement with physical
   net IDs and stock checks; a native-layer inventory cannot prove it after
   feeds, fill or new routing are added.

The source also contains 329 inherited `Cext` parasitic entries. They are not
additional native devices to place. A newly routed macro requires new
extraction; the old capacitance network is not source-specific evidence for
this 420 × 354 µm implementation. Do not tune golden device parameters or
reuse old PEX results as qualification for the changed routing.

## Bounded next routing test — proposal, not run

First use the two maximum-demand HBT rows 7 and 11 as one isolated 34-device
pilot, retaining their exact packed positions and native geometry. This is all
24 XQ75 units, eight XQ76 units and two XQ74 units; the corresponding paired
subsets remain mirrored. Route the five signal nets and VSS, retaining vd2
emitters and dvbe emitters as distinct from VSS guards. Connect row collectors
through the reserved bank-side corridor, not through omitted interior devices.
Provide six explicit source-net ports and exact subset CDL. No extra dummies,
flattened-to-golden device fitting or parameter changes.

Freeze the selected names, source lines, positions, contacts, route rectangles,
via cuts and expected connected components before stock checks. Include a
read-only spacing/obstruction check against all neighboring packed native and
contact shapes; isolated-cell stock DRC alone does not qualify those neighbors.
Require terminal coverage and no cross-net connected component, all via
enclosures/landings, complete stock DRC reports and strict stock LVS. Preserve
any failure under a new ID; do not launch an automatic routing ladder.

Proposed resource contract for owner/root review: one CPU, 180 s per geometry
or stock-check invocation, 0.10 GiB maximum output growth, after a fresh resource
gate. No analog simulation. This pilot would establish only the chosen local
HBT channel/access strategy, not all-1,036-device routing, R1 star quality,
PMOS/NMOS adjacency, supply feeds, density, antenna, PEX or physical adoption.

## Disposition

| Check | Status |
| --- | --- |
| Exact 1,036 source-line binding, 55-net incidence audit, all 50 point centroids | passed, independent numeric audit |
| Existing isolated MOS recipe stock checks | passed, eight DRC and two LVS results inspected; no new stock run |
| Per-row and provisional resistor-head interval arithmetic | passed as defined; not a routed capacity proof |
| Full-macro source-preserving routing, neighbor legality and terminal connectivity | not run |
| New HBT worst-row pilot and complete R1/emitter star implementation | not run |
| Upper-metal feed/ring no-short checks on newly routed geometry | not run |
| New density/antenna/PEX/coupling/current-sharing/analog qualification | not run |
| Failed checks in this read-only audit | none; omitted physical checks are not run, not passed |
| Simulation seed | not applicable; no simulation |

Audit method: tokenize every packed `source_line`, compare to the exact named
source line, count terminal incidences, group by `original`, and recompute bbox
center averages. Row index is `slot_index // zone.nx`. For interval demand,
form `[min(x_center), max(x_center)]` for each non-supply net in a row/band and
count overlaps at midpoints between successive interval endpoints. Singleton
terminals, physical pin offsets, vias, cross-band connections and width/spacing
expansion are excluded from that lower-bound calculation and remain explicit
implementation work.

# SENSE terminal support and isolated four-feed remedy

The isolated four-feed candidate passed native/source preservation,
independent reference generation, stock main/maximal DRC and strict LVS.
It is **not adopted** into the fullchip. Model-terminal composition,
affected capacitance/coupling, electrical parity and physical IR/EM
acceptance remain unresolved or **not run** as detailed below.

## What changed

The source remains SHA256
`baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877`.
Baseline r8 GDS is
`8060e30ac14a1c4aeb1cf62204c9e95d9a68dbad3d73412fbb34c6a33be8b4f7`;
candidate GDS is
`4b8a82d4a19127e5975d558381cd0f1057235cf51dfbbc58e2219b0f0c4a8bd1`.

Four 0.4 um Metal2 source feeders, for main XM14/XM11/XM4/XM3,
are widened to 4 um. Eight new Via1 cuts per feeder land entirely inside
its unchanged native Metal1 source bar. The 6 um width trials failed the
conservative foreign-net clearance screen and are retained. No maximum
legal-width claim is made. Additions total 2,931.424 um² of Metal2 and
32 actual 0.19 um-square Via1 cuts. All other polygons, text and hierarchy
are exact, including Cont, gate, channel, diffusion and Metal1 geometry.
The existing nine port locations/labels, 385 by 240 um boundary and every
primitive identity are held. The separately checked opposite-end gate
prototype is **not** silently combined with this r8-derived candidate.

## Completed checks

| Check | Result and scope |
|---|---|
| Native connectivity | Passed: 134 source nets, 229 physical components, no source opens or shorts |
| Independent saved reference | Passed: 58 MOS, 835 channels, 893 strips, exact W/L/ng and native default junction allocation, matching centroids, 98 resistors, 3 MIMs, 9 ports, 5 nm grid |
| Source CDL | Byte-exact `e3e3c22fa0e59c61f5acc79f3733833ec2a144fe3f133ed09f7922a395deec20` |
| Stock main/maximal DRC | Passed: zero markers in both unchanged decks; 29.987 s wrapper total |
| Strict stock LVS | Passed: explicit netlist match, all cross-reference objects matched, nine top ports; 15.470 s wrapper |
| Source-oriented stock A/P | Exact delta vs original r8 passed; original 7 passed / 51 failed annotations retained |
| All-contact metal-R topology | Passed: 41,384 exact contact footprints and 211 source witnesses, 134 native/source/R component bijection |
| Positive-edge accounting | 46,761 raw / 44,797 reduced nodes; 47,236 raw / 45,184 positive edges; 2,015 exact-zero edges contracted and 37 redundant positive edges accounted |
| Physical current/IR/EM acceptance | Not run; complete current bound and model/external attachments are not qualified |
| Fullchip context, field/electrical and adoption | Not run for this new isolated candidate |

The original stock MOS comparison uses L/W/rfmode as primary parameters;
it does not qualify ng or junction annotations. The independent geometry
audit and the preserved 51 annotation failures therefore remain separate.
No model cards, stock decks or golden netlists were tuned.

## What the resistance calculation establishes

The original graph contains actual 55.31615 ohm M2 bridge edges for
XM14/XM11 and 51.11375 ohm edges for XM4/XM3. Each cuts all 575/483 proven
source contacts of one device from the rest of its supply component.
This is a distribution-independent reason to inspect these four rails.

The new graph's largest VDD bridge coefficient is 47.552525 ohm, down from
55.31615; the VSS coefficient is 41.903833 ohm, down from 51.11375.
The exact tree upper coefficients remain 437.933997/774.785025 ohm because
other graph paths dominate. These bounds are not predicted operating drops.
The exact all-contact separating-cut comparison also passed (11.357 s
wrapper, after eight rejection/selection controls). It enumerates actual
bridges that separate **every** proven source contact of the named device
from its existing source-owned rail-port witness:

| Logical device | Source contacts | Largest separating bridge before / after (ohm) |
|---|---:|---:|
| XOTA/XM14 | 575 | 55.31615 / 4.421275 |
| XOTA/XM11 | 575 | 55.31615 / 4.421275 |
| XOTA/XM4 | 483 | 51.11375 / 2.273724 |
| XOTA/XM3 | 483 | 51.11375 / 15.8929 |

XM3's remaining leading cut is the unchanged vertical M3 rail at x231.4,
y35.53–97.25 um. The two VDD devices now share a leading M3 cut at x230.2,
y89.53–106.7 um. A graph cut coefficient is not total path resistance or
an actual voltage drop; the port witness is not a qualified physical
equipotential attachment. No current or terminal weights were selected.

The fixed ordinary-metal graph excludes Cont, Poly, Active, substrate,
PolyRes, MIM and Vmim resistance. Its PolygonPort objects are node markers,
not equipotential plates. No compact-model weights, single-point current
injection, finger split or new mismatch identity was selected. The LEF
0.103 ohm/square and 20 ohm Via1–4 values are tabulated maxima, not nominal
targets or a guaranteed hot-temperature bound.

## Remaining source-terminal support inventory

The completed 171-slot inventory found physical support, not a model
attachment: 33 PMOS body slots map to ten native NWell components with
6,223 well taps. The main XM1/XM2 logical devices each span **two separate
NWell components**, so a single model body terminal still needs justified
distributed semantics. The 25 NMOS body and 98 resistor BN slots have only
a 15,581-contact compatible substrate pool; no local spreading impedance
or current allocation follows from a common substrate label. All 98 resistor
body projections have zero NWell overlap in the inspected 2D geometry.

The three MIMs have exact native plate areas 1,587/529/529 um² and
972/324/324 actual Vmim cuts, with source-bound TM1 TOP / M5 BOTTOM
membership. The nine actual pin polygons and labels were checked. Required
extrinsic MIM field decomposition remains unsupported by the qualified
method; no whole-net capacitance subtraction or intrinsic replacement was
used. All 171 compact-model attachments remain unqualified.

## Built against

| Item | Pinned identity / verification |
|---|---|
| IHP SG13G2 PDK | `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`, runtime COMMIT checked |
| KLayout | 0.30.9, native API version asserted |
| Container | `sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2`, launcher identity gate |
| DRC/LVS | Unchanged pinned stock decks; before/after file hashes retained |
| R engine | Native SquareCounting, binary hash `99e5f8d32fbebe4e72c97c40d4190800f698cc93164251ef0d6b14e26ca5c3fb`; analytic rectangle/via controls reused by exact hash |
| ngspice | Not run in this geometry/resistance milestone |

The adjacent export manifest retains exact commands, source and original
artifact hashes. Portable text changes only path prefixes; large text/JSON
may be losslessly gzipped. Candidate GDS bytes remain exact. Earlier failed
coupon parity, intrinsic gate/junction and stock annotation dispositions
remain in the preceding committed terminal-method evidence; none is waived
by this isolated metal remedy.

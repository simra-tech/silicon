# SENSE source-held metal topology

The MOS-contact check and subsequent all-Cont topology check **passed**.
Neither is a complete
terminal-attachment model, extracted circuit, or electrical qualification.
The r8 native source remains unchanged; the separately checked dual-ended
gate prototype is not substituted here.

## Source and method

| Item | Exact binding |
|---|---|
| Canonical gm4/comp3 source | `baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877` |
| r8 GDS | `8060e30ac14a1c4aeb1cf62204c9e95d9a68dbad3d73412fbb34c6a33be8b4f7` |
| KLayout | 0.30.9, exact pinned native R engine |
| PDK | `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` |
| Native R engine | `99e5f8d32fbebe4e72c97c40d4190800f698cc93164251ef0d6b14e26ca5c3fb` |

`extract_sense_contact_topology.py` uses unchanged native M1–M5, TM1/TM2
and actual Via1–4/TopVia1/TopVia2 polygons. It binds the existing twelve
single/two-cut controls and five rectangle/via controls to the exact helper
and engine hashes. The resistance scenario is pinned LEF: M2–M5 0.103 ohm
per square and Via1–4 20 ohm are tabulated maxima, not nominal values or a
guaranteed hot bound. Actual cut dimensions are 0.19, 0.42 and 0.90 um.

Every one of the 19,384 catalogued MOS contacts is represented by its exact
M1-covered footprint. A native PolygonPort is a node marker; it is **not**
an assertion that the entire contact footprint is equipotential. No model
current, distribution weight, or selected single-contact injection is used.
Another 211 existing source-owned witnesses bind the remaining metal nets.

## Completed result

All observations map bijectively to 134 source/native/resistance components.
There are no missing markers, mixed-source components or split source nets.
The raw network has 24,680 nodes and 25,086 edges. Contracting only exact
zero-resistance glue yields 22,935 nodes and 23,271 positive edges in the
same 134 components. Nine positive edges have endpoints already joined by
exact-zero paths; these redundant edges are counted explicitly.

Actual cut counts are 1,174/419/255/268/59/16 for Via1/Via2/Via3/Via4/
TopVia1/TopVia2. Every cut has the expected actual dimensions and full lower
and upper metal coverage. Native extraction took 0.583 tool wall
seconds; the recorded wrapper took 13.613 seconds. These are computation
timings, not measured circuit results.

The first result is deliberately **MOS-contact scope**. Native r8 contains
41,384 Cont polygons; the other 22,000 were not assigned by that result.
The 541-slot source ledger has 174 MOS D/G/S slots with contact ownership,
leaving 367 other slots without complete contact ownership. Existing net
witnesses do not establish their compact-model attachment planes.

## Complete Cont geometry classification and topology

The later classification covers all 41,384 actual Cont polygons:

| Geometry class | Contacts | Scope |
|---|---:|---|
| MOS gate/diffusion | 19,384 | Existing exact source orientation and native ownership |
| Resistor heads | 196 | All 196 source endpoints, unique Poly-minus-PolyRes component |
| Shared taps with existing witnesses | 17,676 | Native Active component and source-net membership |
| Buffer shared taps without earlier witnesses | 4,128 | Four Active components, material and source-net proof |

The buffer tap proof requires no adjacent channel within 1 nm; n-type Active
must lie wholly inside NWell and outside pSD, while p-type Active lies wholly
inside pSD and outside NWell. Their actual metal components bind to VDD and
VSS respectively. This identifies physical tap conductors, **not** which
body or BN current belongs at each contact. The original full-reference
ledger had no buffer body witnesses; the missing witness coverage was not
evidence of missing physical metal.

Classification r1 failed on the port-slot schema; r2 exceeded its original
120-second bound. Both are retained. R3 replaced repeated whole-macro
Boolean operations with one exact coverage check and spatial indexing,
cross-checked against the original lookups. R4 added the explicit buffer-tap
material proof and passed in 14.848 seconds, without increasing the bound.
There are no remaining unclassified Cont polygons. Every polygon is exactly
rectangular and fully M1-covered; no bounding-box replacement of a general
polygon is accepted.

The all-Cont topology then passed in 16.488 wrapper seconds (1.084 native
extraction seconds, 426 MB peak RSS): all 41,384 footprint markers plus 211
witnesses map bijectively to 134 source/native/R components. Its 46,696 raw
nodes and 47,140 edges reduce to 44,733 nodes and 45,087 positive edges.
There are 2,015 exact-zero edges and 38 positive edges redundant through
exact-zero paths. No model current or weight is selected.

Physical contact ownership now covers 370 source slots (174 MOS D/G/S plus
196 resistor endpoints). The other 171 slots are 58 MOS B, 98 resistor BN,
six MIM and nine external ports. They still lack complete distributed
attachment qualification; shared tap classification does not assign them.
Cont itself, Poly, Active, PolyRes, MIM and Vmim resistance are not included
in this ordinary-metal network. In particular, Vmim is not reinterpreted as
TopVia1 to bypass the unresolved MIM model/electrode boundary.

## Separate failed and not-run gates

Three passive multiport-adapter coupon attempts are retained. After a
frontend-only 17-digit export correction, all five individual dispositions
pass (including intentional wrong-sign rejection), but exact zero-R
direct-versus-adapter time/model-wave parity **failed**: 1,266 versus 1,275
rows. A sole rationally equivalent differential-expression control also
failed that exact comparison. No interpolation or tolerance waiver is used.
These coupons do not use actual SENSE device weights or qualify an adapter.

Contact/poly/active/resistor/MIM/substrate resistance ownership, per-device
body and BN attachment, actual compact-model composition, full-parameter
zero-R waveform parity, nonlinear electrical response, IR/EM and adoption
are **not run** by this topology check. The prior 51 stock A/P annotation
failures, shared-strip applicability gap, XGW convention and unsupported
complete-field decomposition remain independent unresolved gates.

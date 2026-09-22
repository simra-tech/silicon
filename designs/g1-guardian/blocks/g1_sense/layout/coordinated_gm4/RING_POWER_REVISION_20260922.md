# Isolated SENSE r7 ring-clearance remedy

The r7a isolated macro passes native/source geometry, 134-net connectivity,
saved nine-port identity, stock DRC and strict LVS. It is a candidate for the
separate whole-core integration check, **not production adoption**.

The preceding r6 macro passed its isolated checks but **failed** the actual
whole-core ring-distinctness check after R90 placement at (1031,331) µm.
Local x maps to global y +331: its new TM2 x3/7.3 branch intersects the VSS
ring y327.16–342.16, and its x20 collector intersects the 1.2 V ring
y347.16–362.16. Neither ring may join the SENSE 3.3 V rail. Frozen r6 and both
failed core attempts remain preserved; isolated block DRC did not cover this
integration interaction.

## Exact revision and interface

`build_ring_power_revision.py` derives the hash-locked prior generator with
four exact, counted replacements, saving the complete derived text. It starts
from unchanged r5 native geometry, reproduces r6's redundancy remedy, and:

- moves the main VDD collector/pod from x20 to x36;
- moves the XBUF VDD Via4/upper pod from x7.3 to x36 using a 2 µm M4 bridge;
- starts the VDD TM2 backbone/left buffer branch at x36 instead of x3;
- asserts every saved TM2 and TopVia2 polygon lies at local x≥33.16.

The new M4 bridge passes an independent foreign-net spacing screen. All native
Activ/Poly/Cont polygons and nine external annotations have zero XOR/change.
All three MIM 5 µm neighborhoods retain exact M5/TopMetal1/Vmim geometry.
Only M4, Via4, M5, TopVia1, TopMetal1, TopVia2 and TopMetal2 drawing changes
are present. No source, card, deck, primitive or pin-interface change occurred.

Actual saved TM2 minimum x=33.92 µm maps to global y364.92, giving 2.76 µm
clearance above the nearest ring top362.16. TopVia2 minimum local x=34.57.
This coordinate/keepout gate does not replace the parent's full-core check.

| Port | Drawing / pin / label layer | Center µm | Pin box µm |
|---|---|---|---|
| vdd | 134/0, 134/2, 134/25 | (383,218) | (381,216)–(385,220) |
| vss | 126/0, 126/2, 126/25 | (383,226) | (381,224)–(385,228) |
| Seven signals | Unchanged M4 annotations | Unchanged | Exact saved r6 comparison passed |

GDS: `sense-ring-routing-20260922-r7a/g1_sense_physical.gds`, top
`g1_sense_physical`, SHA256
`9559f0d309f0c14d2f226e56138dfd0283cf2b847f0b536929565e4a739b9b02`.
Source remains `baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877`;
CDL remains `e3e3c22fa0e59c61f5acc79f3733833ec2a144fe3f133ed09f7922a395deec20`.

## Completed checks and limitations

| Check | Status | Evidence |
|---|---|---|
| Generation / full 134-source-net graph | passed | 17.305 s; exact source binding and bounded 385×240 µm reservation |
| Independent native/source reference | passed | 17.897 s; 58 MOS, 835 channels, 893 diffusion strips, 98 R, 3 MIM, source centroids/default allocation and 5 nm grid |
| Saved r6→r7 delta, pin identity, ring keepout | passed | 13.461 s; exact nine pins and native/MIM context preservation |
| Stock main DRC, density excluded | passed | 0 markers, 32.112 s |
| Strict stock hierarchical LVS | passed | 4.936 s; explicit comparison and all nine pins Match |
| Via-only graph cut capacity | passed topology inventory | 18.076 s; zero single-cut articulations for either supply; minimum individual-target 50% engineering capacity0.4 mA |
| Actual branch/current-sharing/metal-contact EM margin | not run | Ideal metal islands in cut-capacity graph; published105 °C/11-year scope, no125 °C/pulse qualification |
| Whole-core integration and whole-chip density/fill | not run here | Parent owns these checks |
| Complete PEX / intrinsic shared-junction applicability | not qualified / not run | Existing extractor and model-boundary limitations remain |
| Adoption | not run | Candidate only |

Stock LVS compares primary L/W/rfmode and does not qualify written A/P or ng.
The independent native source-default allocation gate is distinct from the
known extracted A/P annotation failures and from model-junction applicability.
No failed annotation or earlier geometry/core check is waived.

## Built against and reproduction

Pinned IHP SG13G2 PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`, KLayout
0.30.9, unchanged stock decks. Versions established by the pinned runtime gate;
exact deck hashes and commands are in the stock summary. No ngspice simulation
was launched for this revision. KLayout-PEX0.3.12 was inspected separately,
not used to qualify r7 parasitics.

Use the recorded `build_ring_power_revision.py`, `audit_power_reference.py`,
`audit_ring_power_revision.py`, `run_power_stock.py` and
`audit_power_capacity.py` commands with fresh outputs, pinned runtime and a
fresh resource gate. Raw artifacts use `${RESULTS_ROOT}/sense-ring-*-20260922-r7a`;
portable evidence records explicit runtime-prefix replacements and original
hashes. Do not overwrite the r6 artifacts or earlier failed core geometries.

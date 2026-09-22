# Isolated SENSE power-routing revision

The final isolated r6 candidate is the `sense-power-routing-20260922-r4`
build, cell `g1_sense_physical`, GDS SHA256
`5d640799cb0a4257d34e82a1018237a6bfa0d595bc0d6520522d40125322c170`.
It is unfilled and not adopted. Complete PEX and full current-margin
qualification are **not run**; the earlier extraction-completeness failures
remain in [the method review](PEX_COMPLETENESS_REVIEW_20260922.md).

## Built against

| Item | Pinned identity and evidence |
|---|---|
| IHP SG13G2 | `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`, runtime COMMIT file and unchanged stock-deck pre/post hashes |
| KLayout | 0.30.9, runtime API version assertion |
| Canonical gm4 source | `baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877`, live pre/post hash |
| Source-derived CDL | `e3e3c22fa0e59c61f5acc79f3733833ec2a144fe3f133ed09f7922a395deec20`, exact unchanged reference |
| Baseline r5 GDS | `6609a77884a0009924422bf9871ea699e2393c8988412e1b000057cf3448beda`, preserved |

## Geometry and port contract

The 385 × 240 µm reservation, 58 MOS devices, 835 channels, 893 diffusion
strips, 98 resistors, three native MIM capacitors, original source parameters,
matching centroids and seven signal ports remain unchanged. Native source
W/L/ng and adjacent-gate junction allocation pass independently of stock LVS.
The actual source graph covers all **134** source nets, including both buffer
RZ-to-MIM `cz` nodes omitted by the older 132-probe view.

Only the two macro power ports move. Each new port has an explicit 4 × 4 µm
datatype-2 pin polygon and datatype-25 label, covered by its drawing metal.
The saved view has exactly nine top-level pin polygons and nine unique labels;
old top-level M4 VDD/VSS pin annotations are removed.

| Port | Old layer / center (µm) | New layer / center (µm) | New pin rectangle (µm) |
|---|---|---|---|
| VDD | M4 / (384,184) | TopMetal2 / (383,218) | (381,216)–(385,220) |
| VSS | M4 / (384,184.8) | TopMetal1 / (383,226) | (381,224)–(385,228) |

The implementation adds 44 declared array/access stages and 114 individually
screened redundant local cuts. The original physical cut inventory had 63 VDD
and 51 VSS single-cut articulation stages. The exact final graph has **zero**
such stages between either external power port and the inventoried native
source/metal-access probes. This is a metal/via connectivity result, not a
metal-break, arbitrary-defect or EM-current qualification.

## Completed gates and retained failures

| Gate | Status and scope |
|---|---|
| Saved native/source reference | **Passed**: all 58 MOS, 835 channels, 893 strips, 98 R, three MIM, matching centroids, 5 nm grid and reservation |
| Complete physical source graph | **Passed**: 134 nets, no source-probe opens/shorts |
| Final stock DRC | **Passed**: zero markers, 31.744 s, density excluded explicitly |
| Final strict stock LVS | **Passed**: 4.226 s, strict hierarchical comparisons and all nine external pins |
| Final via-only cut graph | **Passed**: zero single-cut articulation stages; per-target capacities reported separately |
| Native supply contacts | **Passed inventory**: 285 diffusion components, at least four physical contacts each; no single-contact components |
| Native MIM drawing context | **Passed**: unchanged M5, TopMetal1 and Vmim context; final notch repair changes only 0.06 µm² of M4 |
| Stock per-device A/P annotation | **Failed**, unchanged: 51 mismatches and seven matches; strict LVS compares L/W/rfmode, not ng or junction A/P |
| Intrinsic shared-junction model applicability | **Not run**; native geometric allocation is not a model-equivalence waiver |
| Full branch-current / EM margin | **Not run** |
| Complete PEX / extracted electrical regression | **Not run**; prior method failures retained |
| Final fill, density, antenna, wholechip checks | **Not run** on this isolated block revision |

Power-routing r1 failed stock DRC with three TopMetal2 same-net notches; its
conditional LVS did not run. R2 passed stock checks. R3 added distributed main
feeds and a second buffer Via3 row, then failed with two 0.20 µm M4 notches;
its conditional LVS did not run. R4 fills only those two same-net notches and
passes. The first r4 revision-audit assertion incorrectly expected new M3
area; the corrected audit proves M3 is unchanged because the additions lie
inside the existing 1.2 µm trunk. Its failed receipt is retained privately.
Earlier inventory r1 selected an internal VSS witness rather than the external
port; inventory r2 failed with a syntax error; corrected r3 is the accepted
baseline inventory. None of these failures is reclassified as passed.

## Current-capacity limits

The exploratory total-macro target is **2 mA**, using a declared 50% engineering
utilization target, not a foundry derating rule. The published current limits
apply at **105 °C / 11 years**; 125 °C lifetime, pulses, crowding and equal
sharing are not qualified by these calculations.

At 50% utilization, each of the six XOTA/XBUF/XREF supply-access targets has
2.8 mA **via-only** minimum-cut capacity. The buffer VDD upper-bar route has
1.0 mA, increased from 0.6 mA before its added row. Individual native-device
access minima remain 0.4 mA. These numbers model metal islands as ideal and
sum cut capacities; they must not be read as guaranteed current sharing.

Actual saved cross-sections measure buffer M3 trunks at 1.2 µm and M4 bars at
1.0 µm; main M3/M4 collectors remain 0.4 µm. The global VDD TopMetal2 backbone
is 2.2 µm and VSS TopMetal1 is 2.0 µm. Distributed feeds remove the old single
0.4 mA Via4 entrance, but per-device/branch current allocation is still needed
to qualify the narrow internal collectors. Contact sums similarly do not prove
equal sharing, and this contact inventory does not cover resistor contacts.

Separate electrical diagnostics report representative hot/room branch currents;
they are not source-contact, VSS, startup or worst-case envelopes. No complete
current-margin pass is inferred from them or from this physical milestone.

## Reproduction

Use the pinned runtime with one CPU per command. `build_power_revision.py`
takes the preserved r5 GDS, corrected 134-net coverage and accepted baseline
cut inventory, and writes a fresh candidate directory. Run
`audit_power_reference.py` before `run_power_stock.py`, supplying fresh
resource-gate JSON. The stock wrapper uses unchanged DRC/LVS decks, 180-second
child bounds and conditional strict LVS. Exact commands and hashes accompany
the retained reports. `audit_power_capacity.py`, `audit_power_contacts.py`,
`audit_power_ports_revision.py` and the unchanged
`audit_full_sense_junctions.py` provide the separate physical/model checks.
All original bulk artifacts are retained. Portable exports explicitly identify
any runtime-prefix replacement; original hashes are never presented as hashes
of rewritten reports.

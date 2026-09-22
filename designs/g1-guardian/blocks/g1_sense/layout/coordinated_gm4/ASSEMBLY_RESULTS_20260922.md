# Isolated gm4 full-SENSE assembly — 22 September 2026

The isolated, unfilled nine-port full-SENSE candidate passes source-native
geometry, physical terminal connectivity, stock DRC and strict hierarchical
LVS. It is **not adopted**. Stock-written per-node junction A/P fidelity remains
**failed**; shared intrinsic PSP applicability, fill/density, antenna, current/IR,
PEX and whole-chip retained-PDN fit remain **not run** for this candidate.

Exact electrical source SHA256:
`baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877`.
Final isolated GDS SHA256:
`6609a77884a0009924422bf9871ea699e2393c8988412e1b000057cf3448beda`.
Source-derived hierarchical CDL SHA256:
`e3e3c22fa0e59c61f5acc79f3733833ec2a144fe3f133ed09f7922a395deec20`.
Canonical production geometry, source, models and rule decks were not changed.

## Completed checks

| Scope | Status | Evidence |
|---|---|---|
| Main core8: eight large MOS,400 channels408 strips,13 nets | Passed native/source/terminal; DRC0 and strict LVS | [Core8 stock](assembly-evidence-20260922-r1/sense-core8-stock-20260922-r1/summary.json) |
| Complete main19MOS+RZ+CC:478 channels497 strips,17 nets | Passed; DRC0 in30.771s, strict21-device LVS in3.858s | [Main stock](assembly-evidence-20260922-r1/sense-fullmain-stock-20260922-r2/summary.json) |
| 95 native2×76.7µm resistor bank | Passed; DRC0 in14.852s, strict95-device/98-net/9-pin LVS in3.014s | [Bank stock](assembly-evidence-20260922-r1/sense-resbank-stock-20260922-r1/summary.json) |
| Full SENSE58MOS,835 channels893 diffusion strips,98R/3MIM | Passed independent saved-polygon W/L/ng, default-junction allocation, centroids, grid and physical graph | [Full reference](assembly-evidence-20260922-r1/sense-fullassembly-reference-20260922-r5/manifest.json) |
| Final full-SENSE stock DRC | Passed zero markers,40.697s | [Final stock](assembly-evidence-20260922-r1/sense-fullassembly-stock-20260922-r4/summary.json) |
| Final strict hierarchical LVS and nine-port gate | Passed4.226s; two OTA definitions21 devices each, top96 devices+3 instances, exactly9 top pins; all Match | [Final stock](assembly-evidence-20260922-r1/sense-fullassembly-stock-20260922-r4/summary.json) |
| Annotation-only correction of accidental internal bank pins | Passed all non-pin-annotation layer XOR0 | [Revision audit](assembly-evidence-20260922-r1/sense-fullassembly-annotation-revision-20260922-r1.json) |
| Stock per-node A/P versus exact source/default geometry | Failed51/58 records,7 passed; attribution reader completed | [Junction audit](assembly-evidence-20260922-r1/sense-fullassembly-stock-junctions-20260922-r2.json) |

The main is at local origin(5,5). Source-faithful buffers are at(15.5,185.8)
and(135.5,185.8), with actual bboxes[5,181,105.61,232.2] and
[125,181,225.61,232.2]µm. The unchanged native resistor bank and its local guard
remain at their checked coordinates. Complete bbox is
[0.67,0.67,385,239.4]µm inside the385×240µm reservation. This proves an isolated
macro fits that rectangle; it does not prove legal placement under the full-chip
PDN or with new fill and top-level feeds. Buffer and stacked-pair evidence already
committed elsewhere in this folder is referenced, not repackaged.

The actual external pin order is the original source order:
`sense_p sense_n vref iptat isense vped vref_buf vdd vss`.
All top pin shapes are on Metal4. Sense_n and sense_p centers are(384,16)
and(384,22)µm. The remaining ports vref/iptat/isense/vped/vref_buf/vdd/vss
have centers x384, y180/180.8/181.6/182.4/183.2/184/184.8µm. These are new
candidate interfaces, not inherited top-level routing or current qualification.

## Preserved failures and diagnostic distinctions

- Main r1 failed three M3.b markers at a0.20µm RZ collector gap. R2 changes
  added collector offsets±0.30→±0.32µm only; native/source unchanged.
- Bank r1 failed a reader classification that counted XREF as a resistor.
  R2 uses the source model token; its geometry generator section is unchanged.
- Full assembly r1 failed a VREF open and crossed sense input escapes. R2
  corrected only added collectors; both the saved failed GDS and graph remain.
- Independent full-reference r1 failed because stacked-pair probe names`s/d`
  were not included alongside`source/drain`; the audit-only correction keeps
  exactly893 diffusion strips and preserved the failed reader snapshot.
- Full stock r1 failed27 spacing markers; r2 failed two remaining M4 markers.
  Only added track pitch, access position and supply spacing changed.
- Full geometry r4/stock r3 passed stock DRC/LVS with12 top pins because copied
  bank diagnostic annotations exposed vn/vp/vped_ref. It is retained as a
  diagnostic, not nine-port interface acceptance. Geometry r5 removes those
  annotations only; the final reader and stock runner explicitly require9.

All stage directories retain their original status fields. In particular,
earlier main stock summaries inherit a stale `full_main: not run` template
field; their named top and actual21-device comparison certify the complete
main only, not complete SENSE. Later full-SENSE summaries use explicit
`fullchip_fit: not run`. Do not read a historical stage's `stock_checks: not run`
preparation field as overriding its subsequent separately bound stock report.

## Junction/model boundary

All58 source W/L/ng and native diffusion polygons independently match automatic
source defaults under the declared adjacent-gate allocation. The complementary
split pairs retain common centroids and aggregate area/perimeter, but intrinsic
shared PSP junction applicability is still not proven. Stock classes compare
only L/W/rfmode; AS/AD/PS/PD are nonprimary and ng is absent. The51 asymmetric
stock-written records fail just as prior independent native controls failed:
this is not evidence that the physical independent-array control is wrong, nor
permission to tune the source or a model card to extraction. See the separate
[PSP source-equation review](PSP_JUNCTION_APPLICABILITY_20260922.md).

Any next parasitic extraction must keep source-native devices and model cards
unchanged, map every external parasitic node explicitly, and preserve this
failed attribution. A source-preserving RC augmentation needs a frozen mapping
and zero-parasitic control; a strict LVS Match alone cannot provide it.

## Built against and reproduction

| Component | Pinned identity and verification |
|---|---|
| IHP SG13G2 open PDK | `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`; runtime COMMIT and stock deck hashes checked before/after |
| KLayout |0.30.9, asserted in geometry/reference/stock processes |
| Runtime image config |`sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2`, pinned flow identity gate |
| ngspice |46 in the qualified image; no analog simulation in this physical assembly milestone |
| KLayout-PEX |0.3.12 in the qualified image; new candidate extraction not run in this milestone |

Use the saved snapshots and contracts for exact inputs and commands. All
generation/reference children are bounded at180 seconds, stock children at180
seconds plus5-second termination grace, one thread on an allocated CPU.
Stock DRC uses unchanged deep decks with `--no_density`; LVS uses the exact
source-derived CDL and `--no_series_res`. Fresh resource checks are required.
The final reproducible sequence is:

```sh
G1_CPUS=1 G1_CPUSET=7 G1_MEMORY=4g flow/run.sh timeout --kill-after=5 180 python3 designs/g1-guardian/blocks/g1_sense/layout/coordinated_gm4/build_full_sense.py --output build/scratch/sense-fullassembly-fresh
G1_CPUS=1 G1_CPUSET=7 G1_MEMORY=4g flow/run.sh timeout --kill-after=5 180 python3 designs/g1-guardian/blocks/g1_sense/layout/coordinated_gm4/audit_full_sense_reference.py --candidate build/scratch/sense-fullassembly-fresh --output build/scratch/sense-fullassembly-reference-fresh
G1_CPUS=1 G1_CPUSET=7 G1_MEMORY=4g flow/run.sh python3 designs/g1-guardian/blocks/g1_sense/layout/coordinated_gm4/run_full_sense_stock.py --candidate build/scratch/sense-fullassembly-fresh --reference build/scratch/sense-fullassembly-reference-fresh --output build/scratch/sense-fullassembly-stock-fresh --resource-gate build/scratch/fresh-resource-gate.json
```

The builders bind the checked core/main/buffer/bank inputs by SHA256; restore
the exported scratch hierarchy or reproduce those prerequisites first. Output
paths must be fresh. No worker Git write or push is part of these commands.

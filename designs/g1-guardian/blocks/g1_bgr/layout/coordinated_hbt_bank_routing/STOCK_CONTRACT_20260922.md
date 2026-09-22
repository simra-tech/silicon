# Frozen 301-HBT bank r2 — proposed stock DRC and strict LVS

Stock checks are **not run** at this contract's preparation. No full-BGR or
full-macro claim follows from a local HBT-bank result. Root review is required
before launch; one DRC and one strict LVS invocation, separately CPU0 / 180 s
each, 4 GiB reservation, at most 0.20 GiB combined HOME output, with a fresh
resource gate before each. No source, PDK deck, model, geometry or extraction
tuning; no automatic retry or reroute.

## Frozen candidate and demonstrated scope

R2 contains exactly 301 fixed native HBTs / 1204 source terminal incidences /
eight source ports, nine original dummies, four functional grounded-emitter
trees and general guard VSS joined at the declared finite star. Complete CDL
preserves every original source tuple and `npn13G2 we=0.07u le=0.9u Nx=1 m=1`
card; parallel combination by stock LVS is reported separately from native
physical device count.

All eleven preparation gates passed. Saved-GDS source graph has eight physical
components; removing each of five star interfaces gives nine components;
removing all five gives thirteen, preserving five separate VSS route-role trees
and the hub component. No implicit text-label joins. Local route ownership,
0.055 µm via enclosure and 0.30 µm other-role spacing have zero findings.
All 336 exact MOS contacts/reservation rectangles and actual routed399-R r2
obstacles pass, with only explicit resistor-star intersections. All 166848
polygon vertices are on the 5 nm grid. These screens do not replace stock rules.

R1 remains failed with a real VBE3/VD2 port overlap and nine missing dummy-base
observation points. The approved r2 change moves six source-port escapes and
nine probes only. Exact delta gate passed: 24 removed/24 added route records,
12 removed/12 added Via2 cuts, nine dummy-B plus six source-port point changes;
source CDL and all star interfaces unchanged. Native and other route geometry
remain identical. Serialized XOR is confined to the declared port strip.

| Frozen artifact | SHA256 |
| --- | --- |
| bank.gds | `7a8c57b6a05b0cadd4443bb04a3b629b9da23b3919cf16d723122c12fae34e2c` |
| bank.cdl | `57c27168d72461f1a0def4f0a1d38bac1829462e0a1f76e3829840f0102196e6` |
| preparation.json | `efd1448404d08281b0cb4c781074f9578d6e088c83a859eb33d5d4e161d4d218` |
| revision_audit.json | `6bed84066b8ab07e6c0b9ca1215dd76f8910946189bb7840737c6395ed213112` |
| local_spacing_ownership.json | `f94856f4d914d937e5b803fc547d89b01d741d70ffe51ebec98319beab20947a` |
| neighbor_obstructions.json | `c33dcfdb2f2c71860880ed1ba285deb443b07efba08c922b16ef8357a96510cc` |

The runner freezes fifteen completed artifact hashes, all 23 source/contact /
resistor-bank input hashes and all nine completed-launch source/contract
bindings. The included preparation `run.json` is completed, not running.
It independently requires 301 physical top instances, 301 unchanged native
CDL cards and eight source nets. IHP SG13G2 PDK
`84374023ee8b4b126bebbba67fcbada0a9c0ff0b` and KLayout 0.30.9 are checked in
the pinned amd64 runtime; all DRC/LVS rule/helper hashes are recorded before
and checked after each invocation.

## Stock acceptance, without waivers

DRC uses the unchanged stock deep-mode driver with `--no_density --mp=1`;
every generated report must exist and have zero markers, and the process must
exit zero. Density remains not run. LVS uses the unchanged stock deep-mode
driver against the complete frozen CDL; require explicit match text plus
every circuit, device, net, pin and subcircuit cross-reference status **Match**.
MatchWithWarning, Skipped, None, mismatch, missing/malformed reports, timeout,
nonzero exit, changed input/deck/runner or output bound failure are failures.
Preserve the exact logs and databases even when a check fails.

Proposed invocation forms after approval:

```sh
G1_CPUS=1 G1_CPUSET=0 G1_MEMORY=4g flow/run.sh python3 designs/g1-guardian/blocks/g1_bgr/layout/coordinated_hbt_bank_routing/run_stock.py --kind drc --resource-gate RESOURCE_GATE_JSON
G1_CPUS=1 G1_CPUSET=0 G1_MEMORY=4g flow/run.sh python3 designs/g1-guardian/blocks/g1_bgr/layout/coordinated_hbt_bank_routing/run_stock.py --kind lvs --resource-gate RESOURCE_GATE_JSON
```

| Check outside this local stock proposal | Status |
| --- | --- |
| Density, antenna, full1036-device BGR assembly / stock / ring fit | not run |
| PEX, analog, current sharing, IR/noise, matching and startup | not run |
| Physical adoption and chip-level qualification | not run |
| Simulation seed | not applicable |

# Source-preserving core placement and initial supply-ring connection

This is a physical implementation milestone, **not a connected-chip qualification**.
The original production GDS is unchanged. Results are computed geometry checks,
not measurements. The 1414 µm square floorplan retains 12 macro instances and all
4662 native decaps (4645 decap8 plus 17 decap4).

## Built against

| Item | Identity and verification |
| --- | --- |
| IHP SG13G2 | `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`; runtime COMMIT checked, all stock technology files hashed before/after DRC |
| KLayout / pya | 0.30.9; runtime version asserted |
| EDA image config | `ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2`; previously verified pinned runtime |
| ngspice / xschem / LibreLane | Not applicable to these placement and geometry runs; no electrical or new digital synthesis result claimed |

## Results

| Check | Status | Evidence and limitation |
| --- | --- | --- |
| Analog placement r1 | Failed | Incorrect single-top-cell assumption; SENSE also contains an auxiliary resistor-bank view. No geometry waiver. |
| Analog placement r2 labels | Failed | Transforming a displacement vector omitted translation. Geometry was copied correctly, but reported labels were wrong. |
| Analog placement r3 | Passed | Explicit primary cells, Point transforms, 18 external ports, every native polygon/text and saved-GDS round trip. No ring overlap or 5 µm margin intrusion. |
| Full core placement | Passed | Ten retained macro instances plus BGR/SENSE, all 4662 decaps, original native geometry/text and alternating row rail polarity preserved. |
| Decap physical domains | Passed | 9324 metal-backed probes, no supply short or merge of distinct original nets; independent single-extraction supply anchors identify all original decaps as VDD/VSS, not VDDA. |
| Initial stock DRC command | Failed | 300 s watchdog expired during maximal deck after main deck completed. Original failure retained. |
| Main DRC deck | Passed | Zero markers, 101.57 s, on placed-core hash `095db0fa913612f464c096f9c92fe7fde1bd773dfe745c8d0e4f3cf57c3e299f`. |
| Maximal-only recovery | Passed | Zero markers, 312.230 s stock API work / 321.176 s launcher. Same geometry and rule hashes; explicit one thread replaces implicit 128 under unchanged one-CPU affinity. Completed main deck was not repeated. |
| Native ring corner connection | Passed | Eight copied source-native arrays, 350 TopVia2 cuts; exactly two distinct connected supply rings. All other geometry/text unchanged. Output hash `9bb58f7da060d0128290edcea55bb937c0d7cd01e7affe711509944816a96877`. |
| DRC of newly connected ring | Not run | Prior DRC covers placement before these added cuts, not this derived GDS. |
| Decap/macro feeds, signal routes, pads/sealring | Not run | Ring connectivity alone does not connect the core. |
| Density/fill, antenna, complete LVS/PEX, current/IR/EM | Not run | Main/maximal geometry checks explicitly disabled density. |
| Integrated electrical adoption | Not run | These candidates have not replaced the production layout or electrical source. |
| Tapeout qualification from placement alone | Not applicable | No such inference is valid. |

The BGR source-native layout is hash `0083eabb0f730b2cb27eeb0bda1ac8f173a21e03e2aa5a329b01ef5cba21b3ed`;
SENSE is the r5 layout `6609a77884a0009924422bf9871ea699e2393c8988412e1b000057cf3448beda`.
Later power-routing candidates require separate placement binding and affected checks.

## Reproduction and records

Use the pinned image through `flow/run.sh` with one assigned CPU and sufficient
checked RAM/storage. Run `place_closed_analog.py --output ANALOG`, then
`place_remaining_core.py --analog-placement ANALOG --output CORE`.
Run `audit_placed_decap_domains.py --placement CORE --output CORE/decap_domains.json`
and `audit_decap_supply_names.py` as recorded in its source. The original main/maximal
command and all switches are in the DRC summaries. The recovery helper accepts
`--parent-drc DRC --placement CORE --output MAXIMAL` and checks the exact completed
main report before running only the unfinished stock maximal deck.
Run `connect_core_ring.py --placement CORE --output RING` to copy the native arrays.

`core-placement-evidence-20260922-r1/manifest.json` lists exact original/exported
hashes. Host paths alone are normalized to `@REPO@`, `@RESULTS@` and
`@SESSION_RECEIPTS@`; original evidence remains retained. Failed r1/r2 script
revisions were not independently snapshotted, so their exact script replay is
**not run**; original error logs and incorrect r2 label output are retained.

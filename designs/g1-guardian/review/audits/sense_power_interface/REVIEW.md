# SENSE chip-level supply interface — isolated candidate

The source-held r8 SENSE macro now has an independently checked additive route
candidate to pad07 VDDA and the reserved root VSS handoff. No production layout,
root spine, package pin, model card or electrical source was changed. **Absolute
full-native stock main DRC still fails the original 60 pad markers.** The
candidate adds and removes zero markers under an exact comparison.

| Check | Result |
|---|---|
| Native polygons, texts, additive XOR and saved roundtrip | Passed |
| SENSE VDDA → pad07 bare M3 and external TM2 | Passed physical connection |
| SENSE VSS → reserved TM1 handoff; both core rings distinct | Passed physical connection |
| Isolated overlay stock main DRC | Passed, zero markers, 7.358 s |
| Exact native parent stock main DRC | Failed, 24 Pad.fR_TM1 + 36 Pad.fR_TM2, 327.447 s |
| Native parent plus overlay stock main DRC | Failed, same 60 markers, 390.881 s |
| Exact category/cell/value marker multiset comparison | Passed, zero added/removed |
| All 38 individual new cuts removed in turn | Passed endpoint connectivity |
| Frozen signal-route overlay clearance, seven metals/six cuts | Passed, zero overlap/proximity |
| Native pad07 bare-to-pad via topology | Passed inventory; no single-cut articulation |
| Root final PDN and combined routed stock checks | Not run in this work |
| Full-chip LVS, maximal DRC, density/antenna, complete PEX/IR/EM | Not run in this work |
| Electrical/production adoption | Not run |

The first coupon invocation failed before executing rules because its report
directory was absent. Its source, summary and log are retained; only directory
creation was corrected for the successful retry. The initial x805 VSS landing
failed the conservative proximity screen and was not built. The frozen
implementation uses x803.8. Neither is silently replaced by a pass.

## Integration contract

The exact routes and array geometry are in [CONTRACT.md](CONTRACT.md).
The overlay contains no native macro copies and no root spines. Its cell is
`sense_power_interface_NOT_ADOPTED`, DBU 0.001 µm, chip coordinates. Import it
with the identity transform; do not align or normalize its bounding box.

- Overlay SHA256: `a16aa0d622329a4d5de51b658a3d57f0e7cf1d1be1cdd4228dfead0856f56ca0`.
- Exact native parent: `8b66a958759478987fa9de59746a0554f9bd065307e730342f10e891082134e6`.
- Native-plus-overlay diagnostic: `7f79e3d1fe9fda97c943e3045c6c3e08ef209c488dd1943c41e82070599540b2`.
- Frozen signal-route-only clearance source: `03473e0dd19b9d69be9faa5e7b9edb4254c7aabab354b8899d18b0bba586703b`.

The VSS handoff is TM1 centre (736.8,722) µm, footprint
[734.72,719.92,738.88,724.08]. Its root lane-5 spine is not included. Proposed
TM1 axes x750 VDD and x774 VSS cross the VSS TM2 flyover without cuts.
SENSE supply is **VDDA**, not the 1.2-V core VDD ring.

## Current and extraction limits

This is a SENSE-only branch, not a shared VDDA trunk. The exploratory envelope
is 2 mA. Under additive via capacities at 50% of the pinned 105 C / 11-year
table, VDDA is 2.4 mA, falling to 2.1 mA with the worst individual cut removed;
VSS is 20 mA, falling to 15 mA. Native pad07's via-only path is 24 mA at the
table limit (12 mA at the engineering half-table target), with 60 limiting
lower vias. These assume ideal metal islands and do not prove actual sharing,
wire bottlenecks, current crowding, aggregate pad load, bond/ESD capacity,
125 C lifetime or pulse applicability. Worst-single-cut load allocation for
lower vias fails the target and is explicitly retained in the array ledger.

The representative simulated SENSE pin peak, 1.5091687157 mA, is one hot
nominal-process/supply fixture, not a worst-case bound. The new external field
geometry requires parasitic review. The independent MIM intrinsic/extrinsic
composition blocker remains open; no complete PEX claim follows here.

## Reproduction and evidence

Use the pinned runtime in CONTRACT.md. Scripts accept explicit parent, spine,
candidate and output directories under a caller-supplied `G1_RESULTS_ROOT`.
`build_interface.py` constructs and audits; `check_overlay_stock.py` runs the
unchanged main deck on the overlay. Root's existing `run_core_candidate_drc.py`
ran each exact full-native input with `--only main --main-watchdog 600`.
`compare_native_markers.py` compares the completed reports without tolerance.
`audit_overlay_graph.py`, `audit_pad_access.py` and `audit_signal_overlay.py`
provide the independent bounded checks. No stock deck or rule switch was
relaxed; density was explicitly excluded from these local-geometry checks.

The portable evidence export records every original hash and any path-only
sanitization, and includes the 3.3-KiB overlay, not another 63-MiB native GDS.
Root must independently validate the final merged geometry and supply graph.

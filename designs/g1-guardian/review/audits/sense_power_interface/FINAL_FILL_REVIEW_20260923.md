# Final routed candidate fill review — 2026-09-23

The filled candidate passes the unchanged stock density deck. Its main check
retains exactly the original 60 pad violations, with no added markers; maximal
retains the original four pad violations with a byte-identical report. This is
not tape-out acceptance: inherited pad failures remain unwaived, and complete
fill-sensitive extraction and electrical qualification are not run.

## Built against

| Item | Pinned value / evidence |
| --- | --- |
| IHP SG13G2 PDK | `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`; runtime COMMIT and complete stock-rule hashes in check summaries |
| KLayout | `0.30.9`; runtime version assertion and stock check output |
| Stock fill | Unchanged PDK `filler.py` and three macro hashes in the stock-fill analysis |
| Supplementary poly | Existing `add_native_poly_fill.py`, SHA `fdb434e02b1635b40a1f5e6e31c2918c54ebb17e88fdcc0bc115214842784051`; unchanged rule-table SHA `07930b016cdffe14c2cb82b47fbec193643347607db6d44aa1abfdece056cd2f` |
| Simulation | Not run for this fill milestone; no compact-model or source edits |

## Exact geometry chain

| Stage | GDS SHA256 | Result |
| --- | --- | --- |
| Routed, sealed native input | `3a24f4d76b3d91141d09515e498383ec36bec4f5bbcffbb7a53456f82259c0e9` | Frozen input; original density failed 19 markers |
| Stock additive fill | `c14378022010857bdef4cd4108a7a7e03c6e4bffd7fb9698ed1996dc73933579` | Geometry passed; density failed one global poly minimum |
| Coarse supplementary poly | `6940019d6424780736d2b4a31f33f03812319633aab9d7b38298847cea28ea6a` | Geometry passed; 1,458 rectangles / 10,206 µm²; intermediate density not run because area arithmetic still fell short |
| Fine supplementary poly, final candidate | `4d3907c50f07946ef27a6d53402cf319264499a21379d2de80e9c4f1adbae299` | Geometry and density passed; 325 further rectangles / 2,275 µm² |

All stages use top `placed_core_NOT_CONNECTED_FULLCHIP`, 1 nm database units,
and the unchanged 1,414 µm square boundary. The density deck measures
1,999,396 µm². The input already includes the source-bound removal of 56 TRIP
fill polygons; this subsequent fill operation removes no existing fill.

The independent stock-fill delta audit preserves all 53,720 original
hierarchical instance records, all non-datatype-22 polygons and all text.
12,792 stock-fill instance records were added. Original filler is a subset of
the result on every layer. The saved nine-layer addition overlay has exact
polygon XOR zero against the computed additions. Each supplementary-poly
stage independently verifies saved-layout polygons, text and original
instances against its immediate source plus its exact added rectangles.
These are geometric reconstruction proofs, not a claim that flattening an
overlay reproduces byte-identical hierarchical GDS serialization.

The three portable addition overlays are:

- Stock delta: `4a75fbe469d9fdf3d189ffa77667dc6da22dd3f73caadd34f6fcd9689dbcb4ff`.
- Coarse poly: `8dc36b8a4b09aa07ae961ccac504a3e978a1392e93d58ca2acd06d2157f06ee1`.
- Fine poly: `8bc14205de724eab755d2f2272517e1e19530a2bf92744a3f486d93e74548038`.

## Fill spacing and exclusions

The stock fill recipe and rule decks are unchanged. Supplementary poly uses
the stock 5.0 × 1.4 µm rectangle dimensions. Each phase is filtered against
existing and earlier-added poly with 0.8 µm exclusion. Functional active/poly,
whole NWell/nBuLay regions, selected device-recognition regions and active
fill receive conservative 1.1 µm exclusion; both active and poly no-fill
regions are excluded. Rectangles must lie wholly inside the sealring interior;
none are clipped to screening-tile edges. No functional geometry, pin, text,
bondpad or route is moved. These geometric gates do not substitute for the
independent final stock spacing checks.

## Check disposition

| Check | Status | Evidence / scope |
| --- | --- | --- |
| Stock-fill source preservation | Passed | `final-native-stock-fill-20260923-r1`; independent `final-stock-fill-delta-20260923-r2` |
| Initial delta-auditor instance identity | Failed, retained | r1 compared layout-local cell indices embedded in string formatting; no geometry changed |
| Corrected delta-auditor controls | Passed | Cell-index reorder remains equal; 5 nm placement change is rejected; r2 repeats complete geometry proof |
| Final density | Passed | `final-poly-density-20260923-r2`, zero markers, 59.868 s |
| Final main | Failed, inherited markers unchanged | `final-filled-main-20260923-r2`: 24 `Pad.fR_TM1` + 36 `Pad.fR_TM2`, 386.380 s; exact marker comparison passed with zero added/removed |
| Final maximal | Failed, inherited markers unchanged | `final-filled-maximal-20260923-r2`: four `Pad.d1R`, 637.326 s; report byte-identical to unfilled source |
| Unfilled maximal | Failed, retained | Four `Pad.d1R` markers, exact RDB SHA `904444f0f3a988baa65483932753287210ab32ab87681c9df9d9bec9573b1424`, identical to earlier candidate reports |
| Filled antenna | Passed in separate coordinator check | `final-filled-antenna-20260923-r1`: zero markers, 128.716 s wrapper; separately exported, not duplicated here |
| Complete device-aware fullchip LVS | Not run in this milestone | No inference from metal connectivity or preserved native instances |
| Fill-sensitive PEX / electrical acceptance | Not run | New floating conductor environment is not electrically waived |
| Adoption | Not run | No canonical layout replacement |

Final density reports poly 15.05%, M1 46.97%, M2 37.74%, M3 48.05%, M4
48.15%, M5 50.39%, TopMetal1 49.62% and TopMetal2 46.71%; all local windows
pass. The original density failures and the post-stock-fill global-poly failure
remain retained. Unfilled main/density evidence is already in the preceding
integration milestone and is not duplicated here.

The filled main report is byte-identical to the unfilled report, SHA
`4adae846926e89678814758385d3c3a477e6ff8c8de1102da9ad1a7d503c5713`.
This is an incremental fill-spacing result, not an absolute main-deck pass.

Commands and exact input/output/helper/rule hashes are retained in the exported
group analyses and summaries. `${BULK}` and `${REPO}` replace machine-specific
paths only; original and exported evidence hashes are recorded separately.

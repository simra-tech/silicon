# Source-faithful buffer and stacked pair: local physical gates

The isolated source-faithful buffer and stacked64 input pair pass stock DRC
and strict LVS. These results do not qualify the complete SENSE macro,
intrinsic mismatch model, new-layout PEX or system performance.

| Check | Status | Result |
| --- | --- | --- |
| Buffer r1 audit | failed | Odd-finger ownership index error before qualified GDS; failed receipt/snapshots retained |
| Buffer r2 geometry and independent saved audit | passed |19 source MOS W/L/ng, actual terminal partitions, adjacent-gate junction allocation, RZ1×6.2µm, CC23×23µm; bbox100.61×51.2µm |
| Buffer source reference | passed | Exactly19MOS+R+C from unchanged source; boundary rename and standard converter only |
| Buffer stock DRC | passed | Zero markers;33.781s |
| Buffer strict stock LVS | passed |21 devices,17 nets,6 pins all Match;3.353s |
| Buffer stock per-node junction fields | failed |17 of19 MOS disagree with source-default A/P;2 odd-finger bias devices agree; D/S reversal accounted through strict net cross-reference |
| First stock-junction reader | failed | API TypeError before output; retained original source; r2 uses terminal-name overload only |
| Stacked pair r1 geometry | failed | Four dummy-poly/guard-active intersections total7.632µm²; no native channel or Activ removal |
| Output-only failed geometry capture | passed | Identical generation through first failed invariant, exact four added-channel polygons saved; no geometry repair in diagnostic |
| Stacked pair r2 geometry | passed | Only ring sidewalls moved outside end dummies;128 native gates, no unintended channel, original source and coincident centroids unchanged |
| Stacked pair independent saved audit | passed | Two logical W384/L2/ng64 devices;130 physical diffusion strips,5nm grid, all physical terminal partitions, bbox224.8×107.26µm within230×164µm |
| Other19 native-device screen | passed | Zero same-layer overlap and zero200nm-expanded overlap; future contacts/guards/routes absent |
| Stacked pair stock DRC | passed | Zero markers;20.400s |
| Stacked pair strict stock LVS | passed |2 devices,6 compared nets and6 compared pins all Match;2.954s |
| Shared-junction intrinsic/mismatch applicability | not run | Geometric bookkeeping and strict LVS do not establish model applicability |
| Stacked stock per-node junction attribution | not run | Must not extrapolate buffer attribution findings into a measured pair result |
| Whole-main/SENSE routing, density, antenna, new-layout PEX, current/IR and dynamic qualification | not run | Local gates only; no adoption |
| Simulation seed | not applicable | Geometry and read-only model-source analysis only |

The stacked CDL exposes seven source/guard ports; the stock comparison contains
six after the unused substrate-guard-only net is simplified. Physical VSS
guard connectivity is checked independently, not silently inferred from that
six-pin match. Stock decks and source references were not changed to fit a
comparison. Strict MOS comparison uses primary L/W/rfmode; ng and junction
fields require their separate audits.

## Built against

| Item | Identity / establishment |
| --- | --- |
| PDK | IHP SG13G2 `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`; COMMIT and unchanged deck hashes |
| KLayout |0.30.9, checked via pya in pinned runtime |
| Image/config |`ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2`; checked by flow |
| SENSE source |`baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877` |
| Buffer GDS |`320df90ee046c73b628005da9384c80fbd21a715a39b0e8b96b10923726fc500` |
| Stacked pair GDS |`8818ee050f60243b34b8985f9630ed3d9704351d9874ef656a7202bba8290bf3` |
| Stacked source pack |`d70eeefb4a31de454c785a2f92a2320fc2d457ecf8a5b50f8a27abfb5adb2f56` |

Exact prospective limits are in the [buffer stock contract](STOCK_BUFFER_CONTRACT_20260922.md),
[stacked guard revision](STACKED_GUARD_R2_CONTRACT_20260922.md) and
[stacked stock contract](STACKED_STOCK_CONTRACT_20260922.md). Each stock child
used CPU7 and180seconds plus5seconds kill grace after fresh resource gates;
phase bound50MiB. Geometry children used60seconds except the separately
reviewed initial buffer preparation. Memory reservations are not enforced
under rootless-v1. Commands, hashes and full databases/logs are preserved in
[buffer stock](source-faithful-buffer-stock-20260922-r1/summary.json) and
[stacked stock](stacked-pair-stock-20260922-r1/summary.json).

The [read-only buffer attribution](source-faithful-buffer-stock-junctions-20260922-r2.json)
maps every stock device and net to the source through strict cross-reference.
It does not copy extracted values into the reference. The
[PSP applicability review](PSP_JUNCTION_APPLICABILITY_20260922.md) explains why
equal aggregate A/P alone is insufficient: gate-edge width, internal junction
voltages/resistance and limiting matter. No model/card/deck modifications,
OSDI rebuild, or unconditional shared-source equivalence claim followed.

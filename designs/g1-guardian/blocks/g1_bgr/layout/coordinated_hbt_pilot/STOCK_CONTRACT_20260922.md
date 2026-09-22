# Frozen 34-HBT stock-check contract — not run

Preparation r1 passed in15.143s on CPU0: exact34 source devices/136 terminal
incidences, six connected metal/via components and six ports, no cross-net
component, copied-prototype polygon parity, unchanged Activ/GatPoly, complete
added-via enclosure, and no0.3um clearance-screen intersection against known
geometry of all1002 non-pilot devices.156 Via1 and260 Via2 cuts were added, all
as two-cut transitions. No redundancy/current-sharing qualification follows.

Frozen preparation directory: `build/scratch/bgr-hbt-worstrows-20260922-r1`.

| File | SHA256 |
| --- | --- |
| pilot.gds | `20990b281b617df935f9fc31071a2369ebdafdc953e5da22a325ddd805ebfc00` |
| pilot.cdl | `8aeac3748ccc6c00a6804bb75e63f07332a67acf64b27daf6cac71f8e3990e72` |
| subset.json | `68ced7b87dd0bf504f5a9c090ec7cd744609515a1ee0a24ba55a4f9298184211` |
| terminal_graph.json | `8efe887b385113ee2d1773280a0bbd39133b0abcbdd9d950d6da24c3b35509e9` |
| neighbor_obstructions.json | `dbde90dcb63d10dd97a7395e7085331cd589a68b078478017b5aeadc731000cd` |
| route_ledger.json | `276ff347fc54469d0bb971a9a23545bbd65396f35e5b6882473e6f5a7d8c28d8` |

The preparation's output_sha256 entry for run.json describes its then-running
receipt; the launcher subsequently finalized run.json. Do not falsely require
that historical running hash to match the final receipt. All source/deck/
geometry/graph hashes above are immutable and bound again before stock use.

After root review and a fresh resource gate, run one unchanged pinned stock DRC
and one unchanged strict stock LVS, separately. One CPU0,180s watchdog per
invocation,.10GiB combined output bound. Retain logs, all reports, deck hashes,
timeouts and failures; no reroute/automatic retry permitted by this contract.

DRC: stock hard/recommended/off-grid/angle checks using run_drc.py, deep mode,
topcell bgr_hbt_worstrows, --no_density, --mp=1. Require zero markers in every
completed report and successful command completion. Density and antenna are
not run in this local gate, not silently passed.

LVS: stock run_lvs.py, deep mode, same topcell, exact frozen GDS and subsetCDL.
Require explicit match and every circuit/device/net/pin/subcircuit cross-
reference status Match only. MatchWithWarning/Skipped/None/missing reports,
timeout or nonzero exit fails. Do not alter golden parameters or PDK decks.

The neighbor audit covers actual known native geometry and passed HBT/MOS
contact recipes, not future macro guards, neighbor-to-neighbor legality, global
fill, final R1 star, power feeds, or fullmacro placement. Uppermetal use is
absent from this pilot; full-ring feed no-short/current/extraction checks remain
not run. No analog simulation or physical adoption. Seed not applicable.

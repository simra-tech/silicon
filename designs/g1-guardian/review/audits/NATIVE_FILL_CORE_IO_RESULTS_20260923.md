# Native fill and core-to-IO supply milestone

The supplemented sealed-layout candidate passes the unchanged stock density
deck with zero markers. Core VDD/VSS now physically join their corresponding
native IO rails in a separate source-held supply candidate. Neither result
is full-chip signoff; final routing and the remaining supply branches still
require integration and affected checks.

## Fill candidate

The stock filler alone left GatPoly at 14.43%, below its 15% minimum. The
supplemental generator adds only stock-sized 5 × 1.4 µm GatPoly filler
rectangles, respecting existing no-fill regions and conservative well,
active, contact and functional-poly exclusions. It changes no rule or macro.
Original functional polygons, original filler, texts and instances are held.

The first global filtering implementation timed out after 480 s without
producing a candidate; that failure is retained in the preceding routing
milestone. Tiled complete-rectangle queries, with a direct untiled control,
completed in 239.099 s and added 1,458 rectangles / 10,206 µm². A finer phase
pass completed in 252.998 s and added 325 rectangles / 2,275 µm².

Final candidate SHA-256:
`608d38b5ff5d3a1b57123c5237306d673e9478975d056bcc2503aa60fceced16`.

| Check | Status |
| --- | --- |
| Additive geometry, native preservation, saved roundtrip | Passed |
| Stock density on actual 1414 × 1414 µm boundary | Passed: zero; GatPoly 300,971.85 µm² / 15.05%; all other global/local checks passed; 54.877 s wrapper |
| Stock main | Failed: 63 inherited R5 markers; 387.778 s; exact marker multiset preservation passed |
| Stock maximal | Failed: four inherited Pad.d1R markers; 825.311 s; byte-identical report to the prior sealed baseline |
| Final all-feed/rerouted fill, antenna, fill-sensitive PEX | Not run |
| Fabricated density or electrical measurement | Not run |
| Stochastic seed for this deterministic geometry operation | Not applicable |

The three inherited M5 spacing markers are repaired in the separate R6
signal branch, not in this fill experiment. The 60 inherited main pad
markers and four maximal pad markers are unwaived failures.

## Core-to-IO supply candidate

The source-held candidate connects native core VDD through a 10.2 µm M3
extension at x = 410 µm and redundant upper-layer arrays to the south VDD
TM2 rail. VSS uses a 6 µm TM1 extension at x = 520 µm and six TopVia2 cuts.
These positions avoid the digital VSS extension. All five VDD, VSS, VDDA,
IOVDD and IOVSS domains remain distinct.

Candidate SHA-256:
`9940011f4061ec17815ff65f86c2448ad07145cf6a1d87645f4ab80bbb815669`.
Overlay SHA-256:
`9d4db07be32473599d8e0b0622abe49de2c4e9a51871ae7e175ab3d9933d1ff6`.

| Check | Status |
| --- | --- |
| Actual flat conductor connections, no foreign contact, all 4,904 native instances and saved geometry/text preservation | Passed: 347.882 s |
| Every one of 160 new cuts removed independently | Passed: connectivity retained; 16.607 s |
| Stock main | Failed: exactly the 60 inherited pad markers; 335.212 s; exact baseline comparison passed |
| Stock maximal | Failed: four inherited Pad.d1R markers; 626.125 s; byte-identical report to prior sealed baseline |
| Actual current sharing, native pad/wire IR, hot EM and lifetime | Not run |
| Remaining supply branches and final signal-routing context | Not run |
| Physical removal of cuts from the implementation | Not applicable: analysis-only graph controls |

Via-only arithmetic at half the 105 °C / 11-year table gives VDD 12.8 mA
nominal / 12.6 mA after the worst one-cut loss; VSS 30 / 25 mA. The 10 mA
screen is prospective sizing, not an established operating-current envelope
or evidence of equal sharing. Wire and native-IO limits remain independent.

## Integration controls and provenance

The manifest-driven integration helper binds input/overlay/evidence hashes,
checks every contact against instance-resolved physical nets, preserves source
geometry/text/instances, and checks all declared supply terminals in the saved
result. Five synthetic controls pass: a valid join is accepted; wrong-net
metal, capture through an old via, a cut lacking enclosure, and a stale hash
are rejected. The original synthetic positive control failed because empty
in-memory layer definitions are omitted by GDS. The corrected check requires
all original nonempty polygon layers, plus the independent text equality;
the original failure is retained. These controls do not establish native
integration, stock DRC, device LVS or current capacity.

Runtime: KLayout 0.30.9, pinned IHP SG13G2
`84374023ee8b4b126bebbba67fcbada0a9c0ff0b`, image configuration
`ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2`.
Checks use one CPU per process, exact input/rule hashes, bounded watchdogs and
unique run directories. The portable evidence manifest records original and
exported hashes; only declared host-path tokens are normalized. Bulk native
GDS files remain hash-bound externally; additive overlays and reconstruction
sources are included. No full-chip qualification or tapeout readiness is claimed.

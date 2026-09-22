# Coordinated BGR/gm4 SENSE floorplan screen

The smaller loop24/Qref4 BGR proposal is arithmetically plausible within a redesigned ≤2 mm² floorplan, but **physical fit is not run**. It is not shown to fit the existing local BGR envelope or an otherwise unchanged placement. This is a bounded read-only assessment, not a floorplan, source-candidate, geometry-freeze or simulation approval.

The [whole-floorplan accounting](floorplan-area-options-20260922-r3.json) uses the qualified delivered-GDS placement inventory (SHA-256 `38c1d6d13bbfee4ed0e3c01477742c3d2d28317d9215d9e5bd9a35551285ae59`). All device geometry comes from the pinned public PDK and KLayout 0.30.9. No design geometry was saved or changed by this assessment.

## Exact SENSE candidate

The [in-memory PCell inventory](gm4-pcell-footprint-20260922-r2.json) binds source SHA-256 `baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877`. Only the main OTA changes; the buffer/reference OTAs remain unchanged. Main input devices are W384/L2/ng64, the two selected NMOS W320/L4/ng40, four PMOS W384/L4/ng48, and compensation is 69×23 µm. This is the current gm4/comp3 source, not the earlier gm3 footprint.

Candidate main-OTA MOS native bounding boxes sum to 14,227.88 µm². Using the existing OTA-to-native-MOS overhead gives a main-OTA estimate of 28,544.64 µm² and a whole-SENSE estimate of 71,256.00 µm². The previous SENSE reservation is 72,480 µm², leaving only 1,224 µm² arithmetic headroom. Folding, matching, dummies, external contacts, guards and routing have not been placed. Regenerated baseline MOS bounding boxes total 2,497.16 µm² versus 2,495.34 µm² in the delivered inventory; the overhead is an estimate, not exact generator replay. MIM can overlap underlying circuitry and is not simply added as a strict area lower bound.

## BGR area comparison

| Proposal | Native footprint accounting | Existing-overhead estimate | Same-area square |
|---|---:|---:|---:|
| Loop24/Qref4, fixed nominal R2 length 53.465 µm | 55,731.94 µm² | 139,548.68 µm² | 373.56 µm side |
| Loop32/Qref4, no R2 change; comparison only | 72,959.25 µm² | 182,684.60 µm² | 427.42 µm side |

For loop24/Qref4, retaining the generator's 1.9 µm resistor-column pitch raises the native accounting to about 65,529.76 µm² before additional MOS/HBT spacing, guards, routing and matching overhead. This is not a rigorous packing lower bound because native enclosures can overlap legally. A roughly 140,000 µm² placement-search reservation is supported by existing overhead; a smaller legal region has not been demonstrated. The 36,888 µm² old BGR envelope is a local constraint, not the owner's total-area cap.

The fixed nominal R2 coefficient change is a proposed circuit-design change, not per-sample calibration. The [corrected grid audit](rppd-grid-20260922-r3.json) independently verifies stock `3_1_offgrid.drc` uses a 5 nm drawing grid, distinct from the 1 nm GDS database unit. Nearest rounding is 53.4641998819→53.465 µm, +0.0008001181 µm (+14.9655 ppm length). Baseline and rounded resistor PCells were instantiated only in memory with `Calculate=R`; their complete PolyRes bodies match exact 1×52.5 and 1×53.465 µm rectangles, bounding-box heights equal L+1.22 µm, and every polygon vertex was on the 5 nm grid. This is not full resistor DRC/LVS, electrical acceptance or source adoption. No legal minimum pitch reduction is claimed from the native 1.4 µm resistor bounding-box width or the current 1.9 µm pitch.

The original grid probe omitted `Calculate=R` and generated identical short default bodies; its [failed full-length coverage](rppd-grid-20260922-r1-coverage-review.json) is retained. An intermediate assertion incorrectly searched for a long GatPoly body; pinned rppd uses PolyRes for its body and GatPoly for its contact heads, so that run stopped without acceptance. The corrected audit checks the actual PolyRes layer. The gm4 all-device total was also corrected for its XRZ resistor; MOS-only totals and the reported SENSE overhead estimate are unchanged. BGR unit accounting came from the delivered full-length geometry inventory, not the defective short-body probe.

## Whole-floorplan constraints

The present IO-ring inner rectangle is 708×708 µm = 501,264 µm². Macro bounding-box union is 276,413.96 µm²; 4,662 decap instances have a 59,871.18 µm² union. Neither the remainder nor the die outline is freely available placement area: PDN, signals, clearances and matching constraints remain.

With other macro bounding boxes fixed, the BGR replaceable and the SENSE envelope reserved, the largest macro-free rectangle is x397–1029/y321–408 µm: 54,984 µm². It contains 26,802.05 µm² of existing decaps and therefore cannot be called available while preserving them. No rectangle in this fixed-macro screen accommodates the BGR overhead estimate.

A square 2 mm² die would have a 1,414.214 µm side, 64.214 µm larger than today. In the explicit hypothesis that the north/east ring move by that increment while retaining ring depth, gross inner-area growth is about 95,049.79 µm², not the 177,500 µm² die-area increase. The largest macro-free top strip becomes 83,100.65 µm²; that still does not establish a roughly 140,000 µm² BGR placement. Ring/PDN/routes/bonding changes and some wider macro relocation or repacking are necessary before claiming fit.

Retaining decap area, reserving the full SENSE envelope and using the BGR overhead estimates gives the following gross arithmetic balance:

| Proposal | Current inner-area remainder | Expanded-hypothesis remainder |
|---|---:|---:|
| Loop24/Qref4 | +11,087.46 µm² | +106,137.24 µm² |
| Loop32/Qref4 | −32,048.46 µm² | +63,001.33 µm² |

These balances do not constitute a packing proof or a routing budget. They support investigating the smaller proposal within the owner's area budget, not assuming the existing placement can be kept. Minimum legal resistor pitch, matched folded placement, actual PDN/feed allocation, decap retention/relocation, routing congestion, guard/dummy overhead, IO/bonding revision and final DRC/LVS/PEX all remain **not run**. Models, decks, existing layout, die outline and source netlists are unchanged.

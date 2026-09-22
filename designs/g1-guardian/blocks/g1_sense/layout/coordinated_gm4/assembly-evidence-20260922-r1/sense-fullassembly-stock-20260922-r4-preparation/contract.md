# Isolated full-SENSE assembly contract — 22 September 2026

This new geometry combines the checked full main OTA, two checked source-faithful
buffers, and checked 95-unit resistor bank with the exact source top-level MBI.
It does not replace a canonical layout or alter the schematic, PDK models or decks.
The source SHA256 is
`baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877`.

The initial assembly is limited to one pinned KLayout 0.30.9 process on CPU 7,
180 seconds plus five seconds termination grace, after a fresh resource check.
The initial output forecast is 0.15 GiB in the repository scratch directory.
Independent saved-view reference checks and stock checks follow in separate
bounded runs; they are **not run** at this contract's creation.
The subsequent stock runner uses one CPU 7 process with 180 seconds plus five
seconds grace per child and 50 MiB cumulative output acceptance. It binds the
live source, input GDS/CDL, manifests and stock decks before and after. Deep DRC
without density must have zero markers before LVS can run; every comparison
entry must be strict Match. Missing output, warnings in comparison status, time
limits and nonzero exit status fail closed. Each new batch requires a fresh
resource check with at least 0.1 GiB forecast headroom.
The final interface gate also requires exactly nine top-level pin comparisons.
The earlier r4 geometry/r3 stock run passed the stock comparator with twelve
pins because three copied bank diagnostic labels exposed internal nodes. That
result is retained as a diagnostic, not nine-port interface acceptance. The
next candidate removes only bank pin annotations; native conductive geometry
and source reference remain unchanged.

Fixed placement is main origin (5,5), buffer origins (15.5,185.8) and
(135.5,185.8), and the resistor bank's checked absolute coordinates. The complete
outline is at most 385 by 240 micrometres. New M4 horizontal and M5 vertical
collectors connect the existing terminals; no native device is resized.
The full candidate must preserve 835 physical channels, 58 logical MOS devices,
98 native resistor bodies, three native MIM capacitors and all nine source ports.
The physical graph must have no shorts or opens between the independently
declared device/port probes. Native channel XOR before/after added routing and
guards must be zero, and every saved vertex must lie on the stock 5 nm grid.
Failures and partial saved candidates are retained with their exact inputs.

Stock LVS must compare against the source-derived complete hierarchy, retaining
individual resistor units with `--no_series_res`. A strict Match is topology and
the stock primary-parameter comparison only: source W/L/ng and native junction
allocation need their separate physical audits. The existing asymmetric stock
A/P annotation failures and unqualified shared-junction PSP applicability remain
open. Density, antenna, current/IR, new PEX, full-chip fit and adoption remain
**not run** until their own evidence exists. No full-chip or analog performance
claim follows from this isolated assembly.

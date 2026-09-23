# Isolated physical-interface metadata diagnostic

Scope: normalize only the saved extraction's promoted top-pin metadata on an
in-memory copy. This is not a native extraction rerun, source rewrite, physical
layout change, or fullchip LVS acceptance. Original 71-pin saved database and
all original failures remain held.

The read-only certificate
`e7f9c8eef1ca1631aaa9fd7c2fdbc142bf5f7c3fe33afb1dc4eefc831c308177`
binds the exact native TopMetal2 geometry by zero XOR to exactly one saved
extraction layer. Actual probes of 24 audited external pad rectangles and
existing label coordinates map to 22 distinct top-circuit nets. It does not
join them by text. Duplicate physical supply pads resolve consistently; the
five supply domains remain distinct.

On the copied parent-connected netlist, the diagnostic replaces 71 promoted
internal-name pins with 22 names bound to those exact physical nets. All
electrical net IDs/names and every device ID/model/binary64 parameter/terminal
incidence are fingerprinted before, after projection, after reverse logical
restoration, and after the final projection. Every fingerprint must agree.
Swapped, missing, and duplicated physical mapping controls must fail before
any pin change. No device/net purge or implicit name join occurs in this
metadata operation; the subsequent stock simplification remains separately
reported as in the original saved-netlist diagnostic.

KLayout allocates numeric pin IDs monotonically. Reverse restoration proves
the exact original 71-name order and net-ID binding, **not reuse of the old
numeric pin IDs**. Original, projected, restored and final IDs are all recorded.
This API bookkeeping does not change an electrical node or external geometry.

The first arm exposed a missing reciprocal-pin disconnection in the harness.
The separately retained [lifecycle controls](API_LIFECYCLE_RESULTS_20260923.md)
require disconnection before removal and exact bidirectional pin-reference
audits at every stage. No electrical wrapper reconstruction is required.

Original and prefix-only tap-adapter sources are separate arms, each bounded
to one CPU and 180 seconds, with source/runtime/database/certificate/worker
hashes held before and after. Strict disposition requires the actual engine
result, nonempty complete comparison pairs, exact physical/source pin sets,
and exact paired pin identity; `Match` with a missing pin side is rejected.
All A/P, missing resistor, source-substrate and other device discrepancies
remain visible. No `.GLOBAL` source hypothesis is part of this experiment.

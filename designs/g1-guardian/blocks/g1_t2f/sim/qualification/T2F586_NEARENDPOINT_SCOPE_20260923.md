# Near-endpoint timeout scope

The simulated original 600-second watchdog failures remain failures. The separate
prepared recovery contract does not overwrite them, replace seeds, or change the
original population denominator. Recoveries are **not run**.

Read-only source/deck/full-BEFORE checks passed for the prepared same-input
74140/p00, 74144/p03, 74145/p03, 74149/p03 and 74150/p01 cases. Their final
telemetry windows advanced; conditional linear remaining-time estimates were
65.76, 53.95, 52.83, 0.17 and 1.28 seconds respectively. These estimates are not
accepted-step waveform evidence or guarantees of completion. The failed leaves
have no complete AFTER inventory or exported waveform.

The older generic failed-leaf analyzer's `frequency_and_calibration_status`
text says the frozen 25/100 fit is unavailable. For a failed hot heldout p03
(74144, 74145 and 74149), that phrase is too broad: the original room and 100°C
leaves completed, so their calibration anchors remain available. The failed
hot-leaf frequency and complete four-condition acceptance are unavailable.
For failed calibration p00/p01, the original complete two-anchor fit is indeed
unavailable. Original JSON reports and analyzer hashes are preserved unchanged.

The prepared b contract binds all three completed sibling leaves, the failed
leaf's original runtime/log/deck, the full 3180-parameter realization and the
13-column header. A future recovered calibration or heldout result must be a
separate derivation with the unchanged original linear ±2°C criterion. No solver,
model, timing, source or tolerance change is authorized by this preparation.

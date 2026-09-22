# Pinned current-limit basis and pending implementation audit

The SG13G2 process specification revision1.2, section2.15/page16 and
conditionA.v/page24, was read from the pinned PDK and the table visually
checked. Its SHA256 and machine-readable piecewise limits are in
[current_limits_20260922.json](current_limits_20260922.json).

These limits describe **11 years at105°C**. The separate SG13RH parenthetical
does not qualify SG13G2 at125°C. No temperature/lifetime extrapolation or
pulse-duty relaxation is inferred. Actual G1 current-margin qualification is
**not run**, not implied by copying the PDK table.

For the prospective geometry screen, use50% of the applicable table limit as
an engineering utilization target. This reserves nominal headroom and helps
prioritize bottlenecks; it is not a foundry derating rule. A screening pass
cannot replace current-sharing, local-temperature and workload evidence.
Unknown input current or applicability yields **not run**, never adequate margin.

Record each actual net/stack/location, minimum metal width, cut count,
current source and operating condition, and retained/proposed geometry.
Separate steady DC, waveform RMS and sampled absolute peak. For arrays,
show a worst-single-cut allocation and an explicitly conditional equal-sharing
calculation. Check every lower contact/via stage and access-metal bottleneck.
One-cut-unavailable connectivity is a robustness diagnostic, not yield proof.

`gate_o` in assembly DEF is the low-current GATE-core-to-pad-control signal;
it is not the bondpad gate-charge path. Actual high-current GATE output and
IOVDD/IOVSS paths traverse stock pad internals and must be inventoried there.
Do not assign the complete joined-rail source current to the GATE core feed.
Do not alter stock IO cells or rule decks to create an apparent pass.

Existing partial current evidence is in [V18 supply accounting](V18_SUPPLY_MODEL_20260921.md)
and [integrated supply observations](INTEGRATED_SUPPLY_20260922.md). These have
explicit fixture, omitted-load and rail-allocation limitations. Candidate BGR
or SENSE changes require new affected-current accounting before promotion.

Source/table verification **passed**. Comprehensive current mapping, unequal
sharing, hot lifetime applicability and implementation margin are **not run**.
Physical measurements are **not run**; no fabricated-sample result is inferred.

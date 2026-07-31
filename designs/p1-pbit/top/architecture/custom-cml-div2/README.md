# Standalone custom CML divide-by-2 proposal history

The current divide-by-16 clock-monitor requirements call for a custom high-speed front stage
because the retained standard-cell timing data does not support a 5 GHz first stage and no
complete reusable local HBT CML divider was found. This directory records the requirements-only
architecture work that precedes any transistor-level implementation.

The current proposal uses a CML master-slave DFF with inverted output feedback as a research
direction for a standalone divide-by-2 front stage. The direction comes from a different-process
SiGe study and transfers no device sizing, current, power, frequency capability, or performance
claim into SG13G2. The existing Top V3 comparator contributes one clock-steered latch only as
lineage evidence; it is not a reusable DFF.

## Record dispositions

| Record | Disposition | Reason |
| --- | --- | --- |
| [`rejected-v1/`](rejected-v1/) | Rejected | Four raw backspace bytes, incorrect authority labels, and an incomplete measurement plan. |
| [`rejected-v2/`](rejected-v2/) | Rejected | The unresolved output-load model was dropped and diagram values lacked provenance. |
| [`current-v3/`](current-v3/) | Current | Text integrity, authority categories, load uncertainty, and diagram provenance were checked. |

The supporting [`lineage/`](lineage/) record audits the existing Top V3 comparator latch that
was retained only as a provisional implementation seed.

The resulting [`candidate/custom-cml-div2-v2/`](../../candidate/custom-cml-div2-v2/) and its
[`run/custom-cml-div2-op-v2/`](../../run/custom-cml-div2-op-v2/) package preserve the first
transistor-level seed and a thermally warned nominal operating point. The run remains
engineering-unknown and establishes no divider function.

The original rejected V1 identity is retained in its publication note; its unsafe control bytes
are represented as literal markers rather than committed raw bytes. V3 remains a proposal with
no schematic, simulation, electrical pass, signoff result, or tape-out-readiness claim. Device
topology and count, bias, common mode, swing, reset/startup, load, PVT bounds, power, and
acceptance limits remain unresolved.

# Custom CML divide-by-16 requirements history

The published P1 architecture requires a divided monitor clock at a top-metal probe pad and
allows divide-by-16 or divide-by-64. A 2026-07-31 architecture decision selected divide-by-16 as
the baseline ratio. At the published 1–5 GS/s assumed input range, that arithmetic yields
62.5–312.5 MHz. The ratio is selected; the implementation topology is not.

The current Top V3 source directly buffers `CLK_P` onto `CLK_OUT_DIV`; it does not instantiate a
divider. The installed standard-cell DFF models were rejected for the 5 GHz first stage because
their retained minimum-clock-pulse constraint is longer than the available 100 ps half-cycle.
A local source audit found no complete reusable HBT CML DFF or divider. A custom high-speed front
stage is therefore required, but no circuit behavior has been evaluated.

## Record dispositions

| Record | Disposition | Reason |
| --- | --- | --- |
| [`rejected-v1/`](rejected-v1/) | Rejected | Authority categories were conflated and the ratio decision cited a superseded note. |
| [`rejected-v2/`](rejected-v2/) | Rejected | Two paraphrases were labeled as exact published source lines. |
| [`rejected-v3/`](rejected-v3/) | Rejected | Markdown escape bytes changed a quotation labeled exact. |
| [`current-v4/`](current-v4/) | Current | Source literals and authority categories were independently checked. |

The three rejected records are deliberately preserved. V4 is a requirements record, not an
electrical pass, signoff result, or tape-out-readiness claim. The architecture partition,
CML-to-CMOS interface, startup/reset behavior, probe load, power budget, PVT bounds, and
acceptance tolerances remain open.

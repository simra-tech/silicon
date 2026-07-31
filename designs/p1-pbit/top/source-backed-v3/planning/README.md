# Top-planning evidence

These files retain the source-bound planning history used before and after the
structural Top V2 netlist was generated.

- `interface/port_matrix.tsv` is the accepted 25-row block-interface map. Every
  line/literal pair was independently reproduced against the named source
  digest.
- `bias-supply/` separates current source interfaces, prior testbench stimulus
  lineage, and explicit absence searches. Prior stimulus is not a top-level
  architecture decision.
- `README_harness_plan_v2.md` and `p1_top_v2_harness_plan_v2.tsv` retain the
  corrected 17-port electrical-harness plan. Nine proposed values or loads
  remain `UNKNOWN`; the other eight are explicitly
  `LINEAGE_ONLY / UNKNOWN_TOP_DECISION`.
- `p1_top_v2_manifest_v2.tsv` is the Design Engineer's 14-row source manifest.
  It does not inventory the three retained V1 planning files or itself.
- `rejected-harness-v1/` preserves the rejected first harness plan. Nine of its
  17 value cells cited source lines that did not contain those values. It is
  retained as failed history and must not be used to build a testbench.

The Design Engineer's V2 report described 15 directory files. The frozen source
directory actually contained 18: 14 V2-listed artifacts, the V2 manifest, and
three retained V1 planning files. That report-level inventory claim is not
carried forward as evidence.

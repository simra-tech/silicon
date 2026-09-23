# Unchanged-input flat representation diagnostic

This is one documented stock `--run_mode flat` experiment, not a reference
repair or a strict-LVS waiver. The original failed deep extraction and all
parser revisions remain preserved.

Inputs are the exact sealed native GDS
`3a24f4d76b3d91141d09515e498383ec36bec4f5bbcffbb7a53456f82259c0e9`
and original top-name-only source
`f4ce6848bd7dd179d2ef4cbd8a4ea6bf9788bcfa1ff4b93fabae8bf18b6378f9`.
No PolyRes marking, source tap adapter, global substrate declaration, implicit
connection, label edit, model edit or rule-deck edit is included.

The current saved deep database proves that 31 duplicated-name clamp/diode
terminal groups are physically joined through actual parent pin connections.
All 14 failed IO cells have zero polygon XOR to the pinned stock library.
The coordinator separately found all 22 expected external labels already in
the native routed hierarchy. Flat extraction can therefore test a genuine
hierarchy representation hypothesis, without joining nets by their names.
Original tap-source reader binding and missing PolyRes recognition failures
remain expected independent problems, not assumed harmless.

`run_fullchip_stock_r3.py` defaults to deep and accepts only deep/flat. Parser
revision 4 requires the actual log mode to equal the requested mode, exactly
one unrelaxed value for each extraction switch, explicit strict-port mode and
missing-port enforcement, all reachable saved circuit/device/net/pin pairs
strictly Match, and the exact source top pins. Positive/wrong-wire/wrong-top,
case-collision, mode, ignored-port and implicit-join controls must pass first.
The stock wrapper's exit-zero/PASS text is never sufficient.

Bound: one CPU, 900 seconds plus existing five-second kill grace; saved result
analysis 120 seconds; 16 GiB RAM reservation, 2 GiB bulk growth, 0.02 GiB home
growth. Rootless memory reservation is not enforcement. A fresh resource gate
must meet the coordinated 45-CPU ceiling before launch. No automatic rerun,
timeout escalation or source substitution follows a failure.

| Prospective check | Status at contract preparation |
|---|---|
| Native same-cell XOR and parent-cluster evidence | Passed |
| Original deep strict comparison | Failed |
| Flat native strict comparison | Not run |
| Syntax-only adapter used in this run | Not applicable; explicitly excluded |
| Geometry/source/model changes | Not applicable; inputs held |
| Electrical/ESD/model applicability | Not run |

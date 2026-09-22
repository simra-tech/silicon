# SENSE r8 representative terminal-current mapping

The separate source/body electrical observations bind to29 of51 physical
via-only targets in each of the representative room/hot runs. The other22
targets per condition remain **not run** for physical current partition or
aggregate attribution. This is not full current-margin qualification.

The input is the exact r8 GDS
`8060e30ac14a1c4aeb1cf62204c9e95d9a68dbad3d73412fbb34c6a33be8b4f7`
and the electrical owner's102 external-terminal records. All58 transistor
bodies are observed separately from supply-connected source pins. Source
collectors sum individual sampled absolute peaks, a conservative upper bound
within the saved samples that avoids source/body cancellation. The resistor
bank is mapped only at its common VSS access, not to individual resistors.

The largest descriptive ratio is0.469591: main XM20's hot source current is
approximately0.187836mA against a0.4mA via-only50%-engineering target. This
comparison does **not** qualify125°C operation: the stock current limits apply
to11years at105°C. The50% factor is a declared engineering target, not a
foundry derating. Shared cuts, actual parallel-current distribution, contact
and wire limits, individual body-tap allocation, startup and full PVT remain
unqualified. A per-target graph maximum flow is not a simultaneous
multi-target current-flow solution.

The simulated fixture is seed73001, nominal process,3.3V, CM0,25mV shunt,
25°C/125°C,5MHz,1.02µs and DC-initialized. Full11512 parameter and27 legacy
bindings plus accounted KCL passed in the electrical controls. Their original
exact voltage/time-grid comparisons **failed** and remain recorded; the
interpolated voltage differences are not silently substituted for that gate.
The three retained model/initialization warning instances per input are
carried into the mapping report.

Reproduce with `map_supply_terminal_currents.py`, the r8 capacity JSON, and
the public electrical summaries under
`g1_trip/sim/qualification/portable_evidence/sense-rail-terminals-20260922/`.
The generated report pins every input and helper hash, includes all102
condition/physical-target rows, and keeps missing assignments explicit.
No circuit run, GDS mutation, rule/model change or adoption occurs in this
read-only mapping.

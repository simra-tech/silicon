# BGR published-emitter-pin diagnostic contract

This is a distinct conditional DC view, not an adopted parasitic source or
proof of model de-embedding. Canonical source586, all device cards, native GDS
6d86, nine macro ports, source positions, 329 historical capacitors, and the
earlier M1-boundary diagnostic remain unchanged.

The native PCell exposes HBT E on Metal2. The original metallic diagnostic
deliberately injected on Metal1 at the same x/y. Read-only geometry checks
establish this difference for all 301 HBTs and their 2408 native Via1 cuts.
The new view changes exactly those 301 point layer tags to M2, at their
unchanged x/y inside the actual native M2 pin rectangles. It does not assume
that the selected x/y is the geometric center of the pin. All other points,
including 798 resistor M1 head points and all substrate assumptions, remain
unchanged. Native metal and vias remain byte-identical in the extraction
input. No positive resistor is subtracted and no VBIC or R3CMC value changes.

## Prospective controls

- Require a unique source-bound native pin for each changed emitter, exact
  reversal of the 301 point-layer changes, unchanged coordinates/currents,
  and the same 55 physical-net equivalence classes. Numeric graph cluster
  IDs are not stable across construction order; compare old and new points
  within the same graph, not unrelated numeric IDs.
- Re-extract the unchanged nine-layer geometry with the unchanged native
  engine and separate KPEX/LEF resistance tables. Port insertion can change
  graph segmentation and node/edge counts. Retain every resulting positive
  edge at exact binary64 value; contract exact-zero edges only. Never force
  the previous node/edge counts onto a differently placed port mesh.
- Independently check raw-edge endpoints/values against the emitted complete
  resistor ledger, all 55 components, nine ports, 1036 model records including
  nine grounded dummies, and byte-exact reconstruction of canonical source586
  by full routing-graph contraction. Keep all 329 capacitor lines byte-exact.
- A fresh exact-original zero-R OP must reproduce all 2842 parameter values,
  3885 raw current fields, and original OP output bytes before nonzero runs.
- Nominal DC: unchanged 3.3 V / 27 C / seed44001 fixture, R4=0 V, IPTAT=1 V,
  original 1 pF VREF load/options/cards. Require finite complete 3355 point
  observations and every node in the frozen new graph, unchanged full 2842
  parameter vector, no simulator errors, and exact input hashes before/after.
- Bound zero to 120 s; each KPEX/LEF leaf to 600 s plus 5 s kill grace. At most
  two one-thread processes on CPUs 0/1 after a fresh 50%-policy resource gate;
  8 GiB reservation per OP leaf (not enforced under rootless cgroups v1).
  No automatic longer timeout or tolerance/model tuning. Preserve failures.

## What remains unresolved

The geometric pin layer is evidence for an interface convention, not proof
of the measurement de-embedding plane used to fit VBIC `re`, `rcx`, `rci` or
R3CMC end resistance. No claim is made that 1.1549/2.5364 ohm isolated native
emitter access coupons equal an identifiable portion of VBIC `re`, nor that
small native M1 head resistance should be removed from R3CMC. Do not subtract
whole-net values. Generic Cont resistance is not added.

Body/well/substrate spreading, all 399 resistor BN physical attachment
planes, historical-capacitor landing, complete resistor-field capacitance,
temperature/startup/stability/mismatch and calibrated-source adoption remain
not run or unqualified. A changed VREF in this view is a simulated sensitivity,
not a new qualification or a correction to the canonical circuit.

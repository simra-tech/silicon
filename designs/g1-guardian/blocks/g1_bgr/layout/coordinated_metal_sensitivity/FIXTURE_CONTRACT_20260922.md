# Conditional full-metal nonlinear DC sensitivity fixture

Preparation passed; simulation **not run**. This experiment is not a qualified
parasitic view, a complete IR result, a no-double-count proof or design adoption.
Canonical source586, model cards, calibration and other campaigns remain held.

## Exact attribution

The physical input is the source-held BGR candidate with GDS SHA256
`6d86b9d40333958cb8186d486d29db1532a816e302871e11d07e0f1d999cfc04`.
Its nine original ports, 1036 native devices, placement and source parameters
have separate stock DRC/LVS and 336-MOS junction-parameter checks. The
conditional metal-only network covers drawn M1–M5 and Via1–Via4 from selected
native M1 terminal points to actual macro ports; it does not model substrate,
well, semiconductor, EmWind or Cont transport.

Two **separate** resistance scenarios retain the previously pinned LEF and
KPEX tables. Neither is a process corner or a guaranteed uncertainty bound.
The prepared raw network hashes are:

| Scenario | Unpruned raw network SHA256 |
| --- | --- |
| KPEX | `cb692b7977f794a30d75480ffbaedf2281ad287836ab3aaa6feef13cccc41521` |
| LEF | `ac93ba817124a62b4b1503ef75d532ecd2d177931451e9fb9739be029bdc258a` |

Each network has 39937 raw nodes and 49142 edges. Exactly 6287 zero-ohm edges
become node equivalences, leaving 33650 nodes and **all 42855 positive
resistors**. Values are emitted with round-trip-exact binary64 decimal text;
none is rounded away, pruned, fitted or clamped. The minimum positive values
are 0.282958 mΩ (KPEX) and 0.331190 mΩ (LEF). No zero-edge surrogate resistance,
fixed-current injection or artificial internal-net voltage source is added.

3346 terminal tokens are rebound to proved metallic point nodes across the
same 336 MOS, 301 HBT and 399 resistor instances. All instance identifiers,
model names and parameter tokens remain unchanged. Nine grounded dummy HBT
models remain, including their existing internal substrate/thermal behavior;
no internal thermal node is inferred to be VSS. Their external terminals use
their actual local metal points, not a claim that finite routing is ideal.

The independent saved-source audit contracts the **entire positive-R graph**
to its 55 original source nets, removes only the enumerated added resistor
records and reconstructs source586 byte-for-byte:
`586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b`.
This is a topology/literal-source control, not an electrical OP result.

## Explicit unresolved boundaries

- Native M1 electrode spreading may overlap resistance already represented by
  VBIC `re` or R3CMC `rc`. No generic contact resistance is added and no model
  term is subtracted. The physical reference plane remains unqualified.
- MOS body and HBT substrate terminals connect to the existing selected guard
  M1 points. This is a lumped boundary, not finite well/substrate extraction.
- All **399 resistor BN terminals remain at original ideal global VSS**.
  There is no qualified extracted point for them. Prior nominal zero-current
  inference is not extended silently to the new OP, temperature or transients.
  Their unobserved external current remains a separate coverage limitation.
- All 329 historical Cext records are byte-identical. The nine original port
  names attach to their actual macro-pin metal points; 46 other old net names
  alias recorded real metal nodes only so historical capacitor records and
  diagnostic names remain defined. These are **not qualified capacitor landing
  sites**. Only DC OP is proposed, where those ideal capacitors are open.
- The earlier resistor-field capacitance-completeness failure remains failed.
  This experiment supplies no replacement capacitance model or adoption waiver.

## Frozen fixture and proposed execution

The original raw-current fixture is SHA256
`06afbd5138cc67283dd27130ee942210498c8fd6d1fc55df4f79c4335373bc3e`.
Retain its exact HBT/MOS/resistor libraries, `.spiceinit`, ngspice 46/runtime
identity, PDK revision, options and seed44001. Its conditions are 3.3 V supply,
default 27 °C, R4 held at 0 V, IPTAT port held at 1 V, and the original 1 pF
external VREF load. No startup, initial-condition, load or tolerance tuning.

The fixture is truncated before its temperature DC sweep, after the original
OP, 3885 current/polarity fields, 55 source-name/supply outputs and 2842
runtime-parameter queries. The later DC sweep and post-sweep parameter query
are **not run**, not described as before/after equality.

Additional output-only commands print all 3355 selected point voltages and
all 33650 metal-node voltages with `numdgt=17`, after the unchanged original
queries. That formatting change does not change simulator tolerances.

Proposed bounded sequence, pending coordinator review:

1. One exact-zero-R control, identical source586 and the truncated original
   fixture; maximum 120 s plus 5 s kill grace, CPU0, one thread. Require original
   2842 parameter key/value pairs, 3885 raw fields and OP data bytes exactly.
   No tiny nonzero resistor is used as the zero control.
2. If the control passes, one KPEX nominal OP and one separate LEF nominal OP,
   each at most 600 s plus 5 s kill grace, sequential CPU0/one thread, 8 GiB RAM
   reservation only, at most 0.20 GiB combined output growth. Fresh resource
   gate before each leaf. No automatic watchdog extension or extra corners.

Require pinned source/network/runtime checks before every leaf, completion,
finite observations, no missing fields or simulator errors, all 1036 model
instances and exact 2842 parameter inventory. Save every failure separately.
For nonzero R, changed OP values and current redistribution are expected data,
not a parity failure; compare with the exact-zero control explicitly.

Analyze all-node metal-edge KCL and selected terminal voltage changes. External
MOS current mapping must use actual new terminal voltages and `ctype`, not the
old fixed-current injection ledger. HBT current mapping retains its separately
qualified wrapper signs. Resistor BN current completeness remains unqualified;
do not report a complete independently metered 1036-device terminal ledger.
Report actual supply currents, VREF/VBE/DVBE and bias shifts, largest local
rail/return changes, device-state changes, warnings, residuals and all failures.
Numerical convergence alone does not make an electrical design check pass.

| Check | Status before execution |
| --- | --- |
| Source/model tokens and 55-net topology reconstruction | Passed, two scenarios |
| 42855 positive R retained; exact zero equivalence | Passed, two scenarios |
| Original source586 bytes and 329 historical Cext preserved | Passed |
| Original preparation r1 generic audit-status assertion | Failed, retained |
| Corrected preparation r2; output-expanded r3 | Passed, retained separately |
| Independent source/network audit | Passed |
| Zero-R OP parity and nonlinear OP | Not run |
| Runtime model/seed parity for these new leaves | Not run |
| Physical electrode ownership / no-double-count qualification | Not run / unresolved |
| Resistor-field capacitance completeness | Failed in prior bound evidence |
| AC, transient, startup, mismatch, PVT and adoption | Not run |
| New stochastic sweep for this deterministic preparation | Not applicable |

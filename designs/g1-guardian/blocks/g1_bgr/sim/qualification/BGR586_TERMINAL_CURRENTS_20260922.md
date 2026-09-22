# Nominal BGR terminal-current evidence

The [1,036-device external-port ledger](bgr586-inferred-external-port-ledger-20260922.json)
is a **model-based inference at one nominal OP**, not 1,036 individually metered
devices. It preserves the exact canonical source
`586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b`.
Conditions are 27 C, 3.3 V, mismatch disabled, ideal 1 V IPTAT termination and
1 pF VREF load. Positive port current enters the device; injection into the
connected wire has the opposite sign.

| Evidence | Status and scope |
|---|---|
| Representative model-field discovery | Passed output-only control; all 2,842 parameters and original 34-point DC waveform bytes exact. |
| Full raw ledger | Passed: 3,885 model/current fields for 336 MOS, 301 HBT and 399 resistors, plus 55 source-node voltages; original parameters and DC waveform bytes exact. |
| 22 external zero-volt port probes | Simulation completed in 22.089 s; original runner **failed** afterward on NumPy-boolean JSON serialization. No rerun. |
| Independent saved-data port audit | Passed the prospective 1 pA per-port mapping bound; maximum difference 2.694 fA. Full parameters and exact canonical source restoration passed. |
| Probe-control original DC equality | **Failed** byte and numeric equality; maximum voltage-column difference 1.0813 nV. This is not replaced by the mapping tolerance. |
| Full 55-node mapped-current consistency | Maximum residual 1.296 pA reported without adopting an acceptance bound afterward. |
| Full IR, transient-current envelope, process/mismatch envelope, lifetime | **Not run** by this evidence. |

The representative probes cover forward NMOS XM34, reverse NMOS XM35, PMOS
XM38, rhigh XR1, rppd XR16 and HBT XQ56. Their 22 measured external currents
verify these nominal mappings:

- PSP total-current fields require `ctype` polarity normalization and internal
  drain/source orientation correction. Directly assigning `ide` and `ise`
  without these corrections is incorrect.
- HBT external C/B/E use the corresponding intrinsic currents; external BN
  includes the separate substrate resistor and capacitor, with their signs
  reversed. The thermal node is excluded from electrical return current.
- Resistor end currents follow `−ibody` and `+ibody`. Both representative
  substrate terminals were explicitly measured as zero at this OP. Zero for
  the other 397 resistor substrate terminals remains an inference from the
  common model wrappers, not a direct query or a transient zero-current claim.

Unlike the joint SENSE fixture, this standalone deck, local initialization,
pinned system initialization and model libraries contain no `rshunt` setting.
No shunt was added. The source copies differ only in the declared terminal
rerouting and zero-volt meters; removing them reconstructs source 586 exactly.
The original runner failure remains in `summary.json`; its separately named
`analysis.json` holds the saved-data audit. The future serialization fix has a
regression test and did not rerun or overwrite this simulation.

The ledger includes the 76 emitter ports in the XQ56/XQ60/XQ62/XQ67 families.
Their inferred total injection into the return wires is 214.823182 µA.
This supports a scoped first-order nominal wire/LEF sensitivity calculation,
not physical-capacitance adoption or a full IR-drop signoff.

[Raw-ledger receipts](portable_evidence/raw-terminal-ledger-20260922) and
[external-control receipts](portable_evidence/external-terminal-control-20260922)
retain source/model/tool/PDK identities, commands, full parameter checks,
declared differences and bulk-wave hashes. Runtime is pinned ngspice 46,
image manifest `5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0`,
PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`; no model-card edits.

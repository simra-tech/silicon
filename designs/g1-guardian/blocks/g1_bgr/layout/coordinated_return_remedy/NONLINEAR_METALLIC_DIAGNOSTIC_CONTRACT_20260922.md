# Nonlinear metallic-boundary diagnostic: preparation only

Status: **not run**. This proposal does not authorize an electrical-source
replacement or establish complete IR/PEX qualification. The current canonical
source586, all 1036 compact-model calls, nine grounded dummy models, 329
historical Cext records, model cards, calibration and existing campaigns stay
unchanged. A separate experimental source would be required for any later run.

## Reference-plane problem, not an omitted bookkeeping step

The qualified external-current probes establish the signs and names of
wrapper terminal currents. They do not identify the physical electrode plane
at which the model was calibrated.

- R3CMC already includes its two contact terms through `c1`, `c2` and `rc`.
  The pinned wrapper uses `postsim=0`. Its internal equation includes these
  terms in DC resistance. Adding generic Cont resistance or subtracting `rc`
  would therefore need separate ownership evidence; neither is proposed.
- The actual npn13G2 wrapper is VBIC level 9 with explicit `re` and its
  existing internal substrate network. The native emitter uses EmWind to M1,
  not generic Cont. No independent electrode reference-plane identification
  has been found that partitions native M1 spreading from calibrated `re`.
- MOS body/HBT substrate currents are currently injected at native M1 guard
  accesses. This is an explicit lumped boundary, not a finite-substrate model.
- Nominal zero resistor BN current is not a transient/PVT zero-current proof.

Consequently, the existing full metallic network is suitable for a labelled
fixed-current routing diagnostic, but **no-double-count qualification for a
nonlinear source insertion has not passed**. Passing geometry, LVS or KCL
does not resolve that gap. No parameter subtraction or hidden zero-resistance
assumption repairs it.

## Bounded alternatives requiring disposition before generation

1. **Explicit full-metal boundary sensitivity.** Use the current native-M1
   point boundary, retain all drawn metallic elements and unmodified compact
   models, and label possible native-electrode overlap as unresolved. This
   could quantify sensitivity to the stated boundary assumption, but cannot
   be called a qualified parasitic view or used to accept the design.
2. **External-route-only boundary experiment.** First identify each original
   native terminal's conductor domain from exact native geometry provenance,
   separately from subsequently added routes. Exclude/collapse only that
   device-owned metallic domain, retaining all outside route metal and vias.
   Boundary-crossing extracted edges must be split at proved interfaces;
   classifying an entire edge by its midpoint or excluding every shape in a
   device bounding box is not adequate. Routes over native devices must remain.
   This avoids claiming a second native metallic contribution, but still needs
   a demonstrated boundary projection and must not be called a complete
   physical model or a rigorous electrical upper/lower bound.

Neither alternative is implemented by this contract. The second is not a
license to collapse different terminals, functional return roles or substrate
connections together. Any ambiguous native-domain ownership is a failed
preparation check, not grounds for inventing a connection.

## Prospective common controls if a boundary is later accepted

- Freeze exact geometry, source, native provenance, source-terminal mapping,
  unpruned raw network, resistance table, solver and runtime hashes.
- Keep LEF and KPEX resistance tables separate; neither becomes a process
  corner, an uncertainty interval or a model-card tuning parameter.
- Preserve every original compact-model record and all non-node parameters,
  including the nine dummy models and their internal substrate/thermal calls.
  No extracted primitive substitutes for a source primitive.
- Derive unique node names only for physically proved metallic partitions;
  retain all nine macro ports and all source-net ownership. Explicitly record
  functional-return/star topology and guards. Never infer internal thermal
  nodes to be ground from a dummy's external all-ground terminals.
- A zero-routing-R control must reconstruct the original electrical topology
  exactly and produce the original source bytes through a stored reversible
  terminal-name substitution map. No small finite resistance is an exact-zero
  control. Check all source records and 2842 runtime parameter values before
  comparing the qualified original operating point/waveform.
- Do not append the new CC matrix to historical Cext. For a routing-R-only
  sensitivity, keep the original 329 Cext byte-identical and label them as
  historical, non-final physical capacitances. The unresolved resistor-field
  CC completeness failure remains explicit.
  A split wire net does not give historical Cext a proved physical landing
  point. The initial proposal is DC OP only, where ideal capacitances are open;
  retaining their records is not a transient attachment qualification.
  Transient/AC use requires a separately proved capacitor-node mapping.
- Start with one nominal OP/control only, on one assigned CPU under a fresh
  resource gate and a prospective watchdog. Save all wrapper terminal currents,
  terminal voltages, supply currents, source-node conservation, and actual
  route voltage differences. Check 1036 model coverage and finite data.
- Evaluate any changed device operating points or current redistribution as
  experimental results, not as improvement solely because the solver converged.
  New calibration, PVT, mismatch, transients and stability are separate later
  gates. No automatic matrix expansion follows an OP result.

## Current disposition

| Check | Status |
| --- | --- |
| Native/source geometry and fixed-current metallic diagnostics | Passed in separately bound results |
| Complete physical electrode/contact ownership | Not run / not qualified |
| Demonstrated no-double-count nonlinear boundary | Not run / not qualified |
| Outside-native route partition and edge-interface proof | Not run |
| Zero-routing-R original-source control | Not run |
| Nonlinear OP or transient with metallic network | Not run |
| Full finite substrate/well model | Not run |
| Resistor-field CC completeness | Failed, retained separate audit |
| Canonical source substitution, recalibration or adoption | Not run |
| Random-seed parity for this document | Not applicable |

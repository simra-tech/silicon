# Proposed native-junction charge-difference observation — not run

The supported PSP OP interface exposes static `ijs` and `cjs`, but not the
native `qjun_s` state. A possible observation of **charge difference**, without
modifying cards or connecting internal nodes, follows the already-pinned
source equations and the independently reconstructed native-node mapping.

For the single canonical PMOS control, physical BS connects to the BS–BI
resistor, its intrinsic source junction, and the simulator's known rshunt.
The pinned source declares the junction contributions
`I(BS,SI) = -MULT*ijun_s + ddt(-MULT*qjun_s)` for PMOS. Its reported `ijs`
is `MULT*ijun_s` under the established orientation. Thus define

```
I_R = MULT * (V_BS - V_BI) / RJUNS
I_shunt = V_BS / 1e12
dQ_BS/dt = -I_R - I_shunt + ijs
```

Here MULT=64 for the held m1/ng64 prototype, RJUNS is the native exposed
internal resistance, and BS/BI mean physically reconstructed nodes, not their
misleading raw labels. The integrated quantity is the native signed BS-side
charge change, not absolute charge and not total external terminal charge.

The existing static controls give residual `I_R + I_shunt - ijs` of
−1.79e−17A at body3.3V and−4.87e−18A at body3.0V using saved raw values.
This is a promising static sign/scaling/shunt check; no transient or charge
result follows from it.

Before a transient run, freeze:

1. Exact unchanged one-PMOS source/cards/realization and all seven native
   resistance/collapse identities; explicit dynamic `ijs` save availability.
2. A body3.3→3.0→3.3V finite ramp with long constant-bias windows and no
   internal electrical ties; source/gate/drain remain ideal fixed terminals.
3. A zero-amplitude ramp control, measured shunt subtraction, and a return-cycle
   charge residual gate. Never infer individual junction current from the
   external bulk terminal, which includes other body/channel contributions.
4. A second finer timestep and independently integrated quasistatic native
   `cjs` versus **actual SI−BS**, with explicit sign/orientation and common
   temperature/parameter controls. Integration and finite-difference error
   bounds must be declared prospectively.
5. A numerical-residual budget adequate for subtracting nearby BS/BI voltages;
   17-digit output is not17-digit physical accuracy. Any missing dynamic field,
   mapping failure, nonfinite vector, or lack of convergence fails closed.

This would establish an observation method on one ideal-biased instance.
Applying it to all six actual devices and comparing physical shared-junction
allocation is a separate future gate. It cannot establish silicon truth or
remove the independent complete-MIM-PEX blocker. Launch is **not run** pending
method review and frozen numerical gates.

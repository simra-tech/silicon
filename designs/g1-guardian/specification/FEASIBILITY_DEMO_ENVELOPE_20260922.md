# Proposed supervised feasibility-demo envelope

This is a conservative **assumed fixture design envelope**, not a completed
board design or a qualified real-use safety specification. Hardware/BOM and
physical validation are **not run**. The purpose is to demonstrate useful
breaker behavior while clearly exposing the gaps to an autonomous product.

| Parameter | Proposed scope | Classification / unresolved work |
| --- | --- | --- |
| Load | Current-limited, nominal 5 V resistive bench load; no intentional inductive energy | Assumed; real FET, supply dynamics and fixture parasitic energy must be established |
| Shunt | Four-wire 25 mΩ, 1 A nominal / 25 mV | Assumed nominal; measured tolerance/TC and lead resistance required |
| Thresholds | Calibrated soft 30 mV / hard 40 mV targets | Targets, not fixed DAC codes; reachable codes, residual error and temperature behavior must pass independently. **Corrected 2026-09-25:** the effective hard threshold is 40–56 LSB below the code (simulated), so a 40 mV hard target (code ≈ 204) needs code ≈ 244–260, beyond 255 at the upper end; the usable hard range is about 25–40 mV (`G1_TOP_LEVEL_SPECIFICATION.md` §4, §6). Use a hard target ≤ about 39 mV (code ≤ 199, so that a search ≥ 56 codes above the target stays ≤ 255) |
| Demonstration fault | 1.8 A / 45 mV sustained step, with event-phase checks | Assumed in-range stimulus; above 1.1× the hard target |
| Positive stimulus ceiling | 2 A / 50 mV including transient overshoot at the actual sense pins | Fixture requirement; supply compliance alone does not prove transient enforcement |
| Reverse current and negative shunt faults | Excluded from the initial powered demonstration; separate low-energy characterization | Not qualified; no reverse-current blocking claim |
| Wiring | Verified intact Kelvin pair, known return path, supervised operation | Open/short fault tolerance not claimed; both fault polarities and reconnection still require characterization |
| Independent protection | Physical load-bus isolation through setup/calibration and an independent fault-energy limit | Required fixture functions, implementation and timing not run; EN is not an independent safety disconnect |
| Initial control mode | Hysteresis and FAST_EN disabled; threshold and offset codes static while energized | Assumed demo restriction; automatic DAC-update settling and loaded asynchronous receiver qualification remain not run |
| Fault duration | Existing hard-path target <10 µs, measured separately from actual current interruption | Chip timing target is not an independently enforced fault-duration/energy bound; external cut-off bound must be verified before power testing |

Start with low-energy source/emulator tests. Do not energize a real load until
the independent inhibit, pin-level overshoot ceiling, external cut-off timing,
stored-energy/clamp behavior and instrumentation have been checked without
relying on G1's own trip output. The specified 50 mV precision range does not
by itself establish overload survival. The 75/100/150 mV screens remain separate
stress characterization, not ordinary accuracy tests or adopted survival ratings.

The reduced open-SENSE_N and high-temperature comparator-overload findings
remain unresolved risks for a real autonomous application. A supervised demo
does not convert them into passed single-fault or reliability checks. Any later
board that exceeds this envelope requires a newly declared credible fault
voltage/time/source-impedance envelope and affected circuit/physical qualification.

Actual pad/package effects, both-comparator saturation/recovery, current-limiter
overshoot, real-FET thermal/energy behavior and open-lead/reconnection behavior
remain **not run** for this proposed fixture. Numerical tests of an ideal
inhibit are **not applicable** as proof of independent hardware protection.
Use the executable EN/configuration sequence in [the measurement plan](../measurement/README.md).
Apply code changes only under the independent load inhibit and allow settled
analog decisions before load application. The unresolved automatic-hysteresis
timing contract is recorded in [the TRIP interface](../blocks/g1_trip/INTERFACE.md).

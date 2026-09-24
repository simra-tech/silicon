# Candidate known-failure replay and decision diagnosis

All four original-step C45/R62 replays completed numerically and passed the independent full-source/runtime/11512-parameter audit. All four original ±0.5 mV residual failures remain **failed**. No source or population adoption follows.

| Frozen condition | Expected hard | Simulated hard | Wall seconds |
|---|---|---|---:|
| 73023, 125°C, 24.5 mV | LOW | HIGH | 331.007 |
| 73073, 125°C, 24.5 mV | LOW | HIGH | 365.757 |
| 78101, low rails, −40°C, 25.5 mV | HIGH | LOW | 284.567 |
| 78101, low rails, 125°C, 25.5 mV | HIGH | LOW | 253.573 |

The last three actual-clock-plus-20 ns decisions agree with the original legacy-time decisions. Their outputs are near 1.2 V for the first two failures and 1.37/5.62 µV for the fast failures. This is not an observed mixed late decision. At edge−1 ns, the four saved comparator frontend nodes are near their supply; they regenerate to opposite rails by approximately +0.5–1 ns. These observations do not prove every internal state reset, nor establish a universal metastability bound.

The source has clock-low PMOS precharge devices XM7–XM10, a clock-high NMOS tail, and a separate cross-coupled output latch. The output retaining its previous state during frontend reset is consistent with that topology; it is not by itself failed reset.

For fast cold p57, simulated xn−yn initially favors HIGH: −14.91 mV at +0.1 ns, −3.26 mV at +0.2 ns. It reverses to +71.83 mV at +0.3 ns, then +1.072 V at +0.5 ns. Meanwhile the actual hard input difference remains positive, approximately +9.03 to +7.44 mV, and xp−xq remains negative. Hot p59 similarly reverses its regenerative differential between +0.1 and +0.2 ns. This localizes a useful hypothesis to regeneration and clock/input-path-dependent effective offset, rather than merely insufficient time before reading the latch. It does not isolate an individual transistor or prove clock slew is the sole cause.

Room calibration already observes a sizable dynamic offset. Fast seed78101 is HIGH at hard code143 but LOW at144, with +0.1 ns input differences +9.035 and +7.002 mV respectively. Low-rail cold p57 is LOW even at +9.031 mV; high-rail cold p61 is HIGH at +12.788 mV. These are condition-dependent dynamic observations, not transferable DC input-offset measurements. At +20 ns the input can have reversed sign after the decision; that late input must not be substituted for the decision-time input.

For the typical hot failures, prior source-held saved-wave contrasts find +0.1 ns hot-minus-room input-difference shifts of +5.491/+6.796 mV. They include sense/pedestal, DAC/reference, input loading and clock-state effects. The corresponding periodic input slopes remain approximately 10 V/V at the comparator and 20 V/V at SENSE. The shifts therefore cannot be attributed to a loss of gain alone. Neither grouped thermal nor grouped rail comparisons are isolated causal tests.

C45/R62 changes the failed-condition +0.1 ns input differences by only −0.123, −0.294, −0.302 and +0.085 µV relative to the old source. It improves the separate bandwidth/stability problem but does not cure these calibration failures.

The next bounded hypothesis is a stronger *dedicated* hard-clock inverter, leaving the comparator, all external interfaces, original input clocks, rails, sampling criteria, models and numerical options unchanged. This is **not run** at report creation. Native layout, clock loading/power, source qualification and affected statistical populations would all need requalification before adoption. No sequence of unbounded sizing trials or relaxation of residual limits is authorized by this report.

Evidence: `joint586-c45rz62-knownfailures-audit-20260923-a.json` SHA256 `602993af52a2fd922f02b86e98d9fe14012a30e48325d5b37098b32b01910e86`; saved-observation diagnostic `joint586-c45rz62-knownfailure-decisions-20260923-a.json` SHA256 `654b456f18860aff7ca3420545bf07a47cc580a5afaa77bfa173aabb2a53f890`. Four analyzer controls pass. The first host preflight used an incorrect relative import directory and failed before analysis; the corrected root-directory preflight passed. No analog run was repeated.

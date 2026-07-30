# Current-steering trim: 670 uA static experiment

This package evaluates one fixed-tail current-steering trim candidate at the
27 °C typical corner. It is a static comparator-front-end experiment, not a
full-chain result and not an architecture selection.

The steering pair shares a **670 uA** tail. The comparator differential input
is swept at three explicit base-voltage pairs, and trim authority is the
movement of the collector-differential zero crossing relative to midpoint.
Every raw row records the actual trim-base voltages, collector and
emitter-follower nodes, and total VCC current.

| code | `TRIM_P` / `TRIM_N` | input zero crossing | authority from midpoint | total VCC current | collector common mode |
| --- | --- | ---: | ---: | ---: | ---: |
| minimum | 0.900 / 1.100 V | -34.580837 mV | **-34.592758 mV** | 2.625327 mA | 2.125465 V |
| midpoint | 1.000 / 1.000 V | +0.011921 mV | 0 | 2.626794 mA | 2.125256 V |
| maximum | 1.100 / 0.900 V | +34.618521 mV | **+34.606600 mV** | 2.625328 mA | 2.125465 V |

The total-current variation is **1.467 uA** and the collector common-mode
movement is about **0.209 mV** across these three points. The candidate does
**not** meet the specified ±40.10 mV authority: it is short by about 5.49 mV
per side.

This experiment does not establish a code transfer, DNL, INL, yield, dynamic
behavior, or full-chain headroom. It makes no signoff or tape-out-readiness
claim.

## Reproducing

From this directory, with `PDK_ROOT` set to the IHP SG13G2 PDK root:

```sh
ngspice -b tb_current_steering_explicit.cir > log_current_steering_explicit.log
```

The single deck runs all three codes and regenerates:

- `raw_explicit_steer_min.txt`
- `raw_explicit_steer_mid.txt`
- `raw_explicit_steer_max.txt`

The retained log contains three completed 601-row DC analyses and no parser
error, NaN, abort, or missing-simulation message.

# Current-steering trim: 780 uA static experiment

This package changes only the shared steering-tail current from the verified
670 uA experiment to **780 uA**. It uses the same 27 °C typical-corner static
comparator front end, explicit trim-base voltages, and collector-differential
zero-crossing method.

| code | `TRIM_P` / `TRIM_N` | input zero crossing | authority from midpoint | total VCC current | collector common mode |
| --- | --- | ---: | ---: | ---: | ---: |
| minimum | 0.900 / 1.100 V | -40.692257 mV | **-40.721947 mV** | 2.735042 mA | 2.109810 V |
| midpoint | 1.000 / 1.000 V | +0.029690 mV | 0 | 2.736750 mA | 2.109566 V |
| maximum | 1.100 / 0.900 V | +40.707065 mV | **+40.677375 mV** | 2.735042 mA | 2.109810 V |

Both measured endpoints exceed the nominal **±40.10 mV** authority requirement
at this tested condition. Total VCC current changes by **1.708 uA**, and
collector common mode moves by about **0.244 mV** across the three points.

That is a nominal static endpoint result, not a gate disposition. This package
does not establish a DAC code transfer, local resolution, monotonicity,
mismatch, dynamic behavior, yield, corner coverage, architecture selection, or
signoff.

## Reproducing

From this directory, with `PDK_ROOT` set to the IHP SG13G2 PDK root:

```sh
ngspice -b tb_current_steering_780u.cir > log_current_steering_780u.log
```

The single deck runs all three codes and regenerates the three
`raw_780u_steer_*.txt` files. Every raw row retains the actual trim-base
voltages, collector and emitter-follower nodes, and total VCC current. The
retained log contains three completed 601-row analyses and no parser error,
NaN, abort, or missing-simulation message.

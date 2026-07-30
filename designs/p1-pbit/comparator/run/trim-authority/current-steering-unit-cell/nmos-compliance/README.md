# Unit NMOS drain compliance

This package directly sweeps the drain of the proposed `sg13_lv_nmos`
current-sink device from 0.05 V through 0.60 V in 5 mV steps at 27 C typical.
The device is `w=2.0u`, `l=1.0u`; its gate is held at 0.25515 V.

An independent recount of the 111 raw points gives:

| metric | recounted result |
| --- | ---: |
| drain current at 0.342 V | 0.762525105 uA, linearly interpolated |
| local fit interval | 10 grid points, 0.320 V through 0.365 V |
| fitted small-signal output resistance | 1.479714 Mohm |
| first grid point at or above 99% of the 0.342 V current | 0.335 V |
| interpolated low-side 99% threshold | about 0.33075 V |

The 0.335 V result is a grid-limited **low-side 99% compliance threshold**.
It is not a voltage above which current remains within plus or minus 1% of the
0.342 V reference: only the 0.335, 0.340, 0.345 and 0.350 V grid points lie in
that absolute band, and the 0.355 V point is already 1.149% above the reference
because of finite output resistance.

This corrects the preceding unit-cell report's 12.5 Gohm calculation, which
divided a 300 mV HBT collector-common-mode sweep by a sink-current change even
though the NMOS drain itself moved only 36.053 uV. The direct drain sweep is the
appropriate experiment and measures about 1.48 Mohm near the intended bias.

This package does not establish PVT or mismatch behavior, a physical bias
reference, digital base drivers, segmented-array matching, code transfer,
dynamic settling, architecture selection, a gate disposition, or signoff.

## Reproducing

From this directory, with `PDK_ROOT` set to the IHP SG13G2 PDK root:

```sh
ngspice -b tb_nmos_compliance.cir > log_nmos_compliance.log
```

The retained log contains one completed 111-row analysis and no error, fatal,
abort, or NaN message. The published deck differs from the executed deck only
by replacing machine-specific model and output paths with `$PDK_ROOT` and a
repository-relative raw path.

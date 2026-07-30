# Retained failed-target base-driver experiment

This is the first loaded-base DC experiment, retained because it missed the
requested approximately 200 mV base differential. It uses a 0.9 V ideal
reference and nominal 40/20 kohm level-shifting resistors.

The two raw states exchange symmetrically and give:

| quantity | value |
| --- | ---: |
| sensed NMOS sink current | 0.762612292 uA |
| active / inactive loaded base voltage | 1.000159490 / 0.599594372 V |
| loaded base differential | 400.565118 mV |
| loaded base common mode | 0.799876931 V |
| selected / unselected collector current | 0.764476756 / 0.000013715 uA |
| selected share of collector sum | 99.998206% |
| signed ideal-source delivery power | 15.145597 uW |

The earlier 33.32 uW report is retracted: it double-counted a zero-volt source.
The positive delivery total, `-sum(Vsource * Isource)`, over the two logic
sources and 0.9 V reference is 15.145597 uW. Raw voltage/current ratios imply
about 39.584 kohm for R1 and 19.832 kohm for R2, versus nominal 40/20 kohm
values.

This failed experiment does not establish a suitable driver, reference,
segmented array, gate disposition, architecture selection, or signoff. The
follow-up corrected-target experiment is in the [parent directory](../).

## Reproducing

From this directory, with `PDK_ROOT` set to the IHP SG13G2 PDK root:

```sh
ngspice -b tb_driver_loading_dc.cir > log_driver_loading_dc.log
```

The retained log contains two completed one-row analyses and no error, fatal,
abort, or NaN message. The published deck differs from the executed deck only
by replacing machine-specific model and output paths with `$PDK_ROOT` and
repository-relative paths.

# Loaded base-driver DC evidence

This 27 C, typical-corner two-state DC experiment replaces the ideal steering
base sources with a passive level-shifting network. Each HBT base is driven
from complementary ideal 0 V / 1.2 V logic through an IHP `rppd` resistor
nominally 100 kohm, with a nominal 20 kohm resistor to an explicit ideal
0.96 V reference. The reference and logic sources are testbench stimuli, not
implemented circuits.

The retained raw rows independently give the same result after exchanging the
two logic states:

| quantity | value |
| --- | ---: |
| sensed NMOS sink current | 0.762598405 uA |
| active / inactive loaded base voltage | 1.000124840 / 0.799622395 V |
| loaded base differential | 200.502445 mV |
| loaded base common mode | 0.899873618 V |
| active / inactive HBT base current | 1.85009289 / 0.00115857 nA |
| selected / unselected collector current | 0.764070263 / 0.000406823 uA |
| selected share of collector sum | 99.946784% |
| signed ideal-source delivery power | 8.246657 uW |

The reported positive source-delivery power is
`-sum(Vsource * Isource)` over the two logic sources and the 0.96 V reference.
It does not count the zero-volt sense or collector sources. Raw voltage/current
ratios imply about 98.881 kohm for R1 and 19.832 kohm for R2, rather than
exactly the nominal 100/20 kohm values.

The preceding 0.9 V, nominal 40/20 kohm experiment is retained under
[`failed-vref900/`](failed-vref900/). It missed the requested loaded-base
differential and its original source-power claim was corrected.

The follow-up [`loaded 16x steering segment`](segment16x/) scales both the NMOS
sink multiplier and HBT emitter count while retaining this base network.
The [`loaded binary-weight package`](binary-weights248/) measures the remaining
2x, 4x, and 8x cells with their exact executed decks.

This package does not implement the 0.96 V reference, a dynamic CMOS logic
driver, a segmented array, mismatch, code transfer, settling, corners, layout,
architecture selection, a gate disposition, or signoff.

## Reproducing

From this directory, with `PDK_ROOT` set to the IHP SG13G2 PDK root:

```sh
ngspice -b tb_driver_loading_dc.cir > log_driver_loading_dc.log
```

The retained log contains two completed one-row analyses and no error, fatal,
abort, or NaN message. The published deck differs from the executed deck only
by replacing machine-specific model and output paths with `$PDK_ROOT` and
repository-relative paths.

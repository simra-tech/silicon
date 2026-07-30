# Current-steering trim: one sensed physical unit cell

This package is a 27 C, typical-corner DC operating-point experiment on one
proposed digital current-steering unit: an IHP `sg13_lv_nmos` sink at
`w=2.0u`, `l=1.0u` feeding one `npn13G2` differential steering pair. The HBT
bases are driven by explicit 1.0 V / 0.8 V test sources. The digital level
driver is **not implemented**.

A zero-volt series source retains the actual NMOS sink current separately
from both HBT base-source currents and both collector currents. An independent
recount of the six raw rows gives:

| steering | collector common mode | sensed sink current | selected / unselected collector current | selected share of collector sum |
| --- | ---: | ---: | ---: | ---: |
| left | 1.9 V | 0.762499864 uA | 0.762125324 / 0.000411119 uA | 99.946085% |
| left | 2.1 V | 0.762516130 uA | 0.763981898 / 0.000414316 uA | 99.945798% |
| left | 2.2 V | 0.762524236 uA | 0.765485229 / 0.000416347 uA | 99.945640% |
| right | 1.9 V | 0.762499864 uA | 0.762125324 / 0.000411119 uA | 99.946085% |
| right | 2.1 V | 0.762516130 uA | 0.763981898 / 0.000414316 uA | 99.945798% |
| right | 2.2 V | 0.762524236 uA | 0.765485229 / 0.000416347 uA | 99.945640% |

At 2.1 V collector common mode, the sensed sink current is within 0.007% of
the 0.762463 uA unit target. Reversing the ideal base stimulus exchanges the
two collector currents as expected.

## Output-resistance correction

This experiment does **not** measure NMOS output resistance from a 300 mV
drain-voltage sweep. Although collector common mode moves from 1.9 V to 2.2 V,
the NMOS drain voltage moves only from 0.341966803 V to 0.342002856 V, or
36.053 uV; the HBTs absorb almost all of the collector-voltage change. Dividing
300 mV by the 24.372 pA sensed-current change and reporting 12.5 Gohm is
retracted. The local secant using the actual NMOS drain-voltage change is about
1.48 Mohm. A subsequent
[`direct drain-compliance sweep`](nmos-compliance/) measures 1.479714 Mohm by
linear fit near this bias and places the low-side 99% compliance threshold at
about 0.33075 V.

The follow-up [`loaded base-driver DC experiment`](base-driver-dc/) replaces
the ideal base sources with a passive 0.96 V / nominal 5:1 resistor network;
it retains the preceding failed-target network alongside the corrected result.

The collector-current sum changes by about 3.365 nA across the three common-
mode settings. That is effective delivered-collector-current dependence for
the driven cell, including HBT behavior; it is not a pure NMOS or HBT output
resistance.

This package does not establish the digital level driver, segmented-array
weighting, mismatch, monotonic digital code transfer, dynamic settling,
corners, architecture selection, a gate disposition, or signoff.

## Reproducing

From this directory, with `PDK_ROOT` set to the IHP SG13G2 PDK root:

```sh
ngspice -b tb_unit_cell_dc.cir > log_unit_cell_dc.log
```

The retained log contains six completed one-row analyses and no error, fatal,
abort, or NaN message. The published deck differs from the executed deck only
by replacing machine-specific model and output paths with `$PDK_ROOT` and
repository-relative paths.

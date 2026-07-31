# Width-scaled 900 uA unit-cell experiment

This 27 °C, typical-model DC experiment scales only the retained unit-cell
NMOS sink width from 2.0 µm to **2.307692307692 µm** at the unchanged
0.25515 V gate bias. The scale factor, 900/780, was intended to move the
physical unit target from 0.762463 µA to **0.879765395894 µA**. The same HBT
steering pair, ideal 1.0/0.8 V base sources, and three collector common-mode
points are retained in both steering directions.

An independent recount of the six one-row raw files gives:

| direction | collector common mode | sensed sink current | selected / unselected collector current | selected share | NMOS VDS |
| --- | ---: | ---: | ---: | ---: | ---: |
| left | 1.9 V | 0.907902718 µA | 0.907467017 / 0.000487342 µA | 99.946325% | 0.337345000 V |
| left | 2.1 V | 0.907922503 µA | 0.909677712 / 0.000490874 µA | 99.946068% | 0.337369510 V |
| left | 2.2 V | 0.907932373 µA | 0.911467772 / 0.000493153 µA | 99.945924% | 0.337381737 V |
| right | 1.9 V | 0.907902718 µA | 0.907467017 / 0.000487342 µA | 99.946325% | 0.337345000 V |
| right | 2.1 V | 0.907922503 µA | 0.909677712 / 0.000490874 µA | 99.946068% | 0.337369510 V |
| right | 2.2 V | 0.907932373 µA | 0.911467772 / 0.000493153 µA | 99.945924% | 0.337381737 V |

The nominal 2.1 V result overshoots the unit target by
**0.028157107106 µA**, or **+3.2005245%**. Sink-current change from 1.9 V
to 2.2 V is 0.029655 nA (+0.0032663%). Width-only proportional scaling is
therefore not exact, while steering selectivity and common-mode stability are
retained in this nominal static experiment.

The original report's `P_tail = 1.0895 uW` column is rejected. It multiplies
the sink current by the declared 1.2 V `VDD`, but that rail is disconnected
from this unit cell and `i(VDD)` is not retained. Summing only the retained
collector and trim-base source voltage/current pairs gives **1.725087,
1.909136, and 2.002315 µW** across the three common-mode points. The reporting
failure is recorded as H-395 in the live-event findings ledger; it does not
invalidate the retained current and selectivity measurements.

This experiment still uses ideal base sources and does not establish a
digital level driver, assembled-array code transfer, mismatch, switching,
settling, corners, layout, architecture selection, a gate disposition, or
signoff.

## Artifact identity and reproduction

The exact executed deck was 3,281 bytes with SHA-256
`9d0449b272d952c2169c4b8e8810c818333866f23f8d855c29db309e133ffe71`.
The public deck has SHA-256
`0ac9a4eb5fba3e6c090b7fe573bf1eb101f5ced6a293066ed976abefe77d74b1`;
it differs only by replacing machine-specific PDK, OSDI, and output paths
with `$PDK_ROOT` and repository-relative paths. The native log and all six
raws are byte-identical to the executed artifacts.

From this directory, with `PDK_ROOT` set:

```sh
ngspice -b tb_unit_cell_900ua_dc.cir > log_unit_cell_900ua_dc.log
```

The retained log contains six completed one-row analyses and no error, fatal,
abort, NaN, voltage-limit, or convergence-recovery token.

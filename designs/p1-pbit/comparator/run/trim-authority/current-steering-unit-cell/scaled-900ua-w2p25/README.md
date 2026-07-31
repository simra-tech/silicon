# Corrected 900 uA unit-cell sizing: W = 2.25 µm

This 27 °C, typical-model DC experiment corrects the preceding proportional
width estimate. It changes only the NMOS sink width from 2.307692307692 µm
to the round **2.25 µm** candidate at the unchanged 0.25515 V gate bias.
The target remains **0.879765395894 µA** per unit for 900 µA across 1023
full-scale intervals.

An independent recount of the six one-row raw files gives:

| direction | collector common mode | sensed sink current | selected / unselected collector current | selected share | NMOS VDS |
| --- | ---: | ---: | ---: | ---: | ---: |
| left | 1.9 V | 0.879992124 µA | 0.879568040 / 0.000472709 µA | 99.946286% | 0.338171872 V |
| left | 2.1 V | 0.880011227 µA | 0.881710757 / 0.000476177 µA | 99.946023% | 0.338196296 V |
| left | 2.2 V | 0.880020755 µA | 0.883445776 / 0.000478409 µA | 99.945877% | 0.338208478 V |
| right | 1.9 V | 0.879992124 µA | 0.879568040 / 0.000472709 µA | 99.946286% | 0.338171872 V |
| right | 2.1 V | 0.880011227 µA | 0.881710757 / 0.000476177 µA | 99.946023% | 0.338196296 V |
| right | 2.2 V | 0.880020755 µA | 0.883445776 / 0.000478409 µA | 99.945877% | 0.338208478 V |

At 2.1 V the target error is **+0.000245831106 µA**, or
**+0.0279428%**. Sink-current change from 1.9 V to 2.2 V is
0.028631 nA (+0.0032536%), and left/right results are identical.
Power is not evaluated because this deck does not retain every relevant
source branch current under an explicit power definition.

This sizes one nominal physical sink unit. It still uses ideal steering-base
sources and does not establish a loaded digital driver, assembled-array code
transfer, mismatch, switching, settling, corners, layout, architecture
selection, a gate disposition, or signoff.

## Artifact identity and reproduction

The exact executed deck was 3,314 bytes with SHA-256
`564f1c90a10bb4647b5a4a5857c3b46a09898feeeec35cdcac5bc659d020713f`.
The public deck has SHA-256
`93602197ebcd4abf7ad7ac07b3feabd5976386288b48b06963fd10d8d1176ef3`;
it differs only by replacing machine-specific PDK, OSDI, and output paths
with `$PDK_ROOT` and repository-relative paths. The native log and all six
raws are byte-identical to the executed artifacts.

From this directory, with `PDK_ROOT` set:

```sh
ngspice -b tb_unit_cell_900ua_w2250_dc.cir > log_unit_cell_900ua_w2250_dc.log
```

The retained log contains six completed one-row analyses and no error, fatal,
abort, NaN, voltage-limit, or convergence-recovery token.

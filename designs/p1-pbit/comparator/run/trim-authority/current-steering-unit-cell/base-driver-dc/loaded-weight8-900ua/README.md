# Loaded weight-8 cell with the corrected 900 uA unit

This 27 °C, typical-model DC experiment applies the corrected **2.25 µm**
NMOS unit width to one loaded binary weight-8 steering cell. The NMOS uses
`m=8`, both steering HBTs use `Nx=8`, and the passive base network remains
nominally 100 kΩ from complementary 0/1.2 V logic and 20 kΩ to an ideal
0.96 V reference. The reference and logic sources are testbench stimuli, not
implemented circuits.

An independent recount of the two one-row raw files gives:

| steering | sensed sink current | target error | selected / unselected collector current | selected share | loaded base differential | NMOS VDS |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| left | 7.042425980 µA | +4.302813 nA (+0.0611358%) | 7.056006940 / 0.003614037 µA | 99.9488069% | +0.200754947 V | 0.338570439 V |
| right | 7.042425980 µA | +4.302813 nA (+0.0611358%) | 7.056006940 / 0.003614037 µA | 99.9488069% | −0.200754947 V | 0.338570439 V |

The target is **7.038123167152 µA**, eight times the
0.879765395894 µA unit target. Reversing the logic exchanges the branches,
and the sensed currents are identical at the retained precision.

This establishes a nominal loaded-cell measurement, not a specification
result: no acceptance tolerance was supplied. Source power is not evaluated
because the run did not retain every supply operand under one explicit total
power definition.

## Artifact identity and reproduction

The exact executed artifacts were:

| artifact | bytes | native SHA-256 |
| --- | ---: | --- |
| `tb_w8_900ua_dc.cir` | 2,732 | `bc9a1beec88bffcb2648a6e5bba8e6f3ebe2db5c19413019239f04f474e5247a` |
| `log_w8_900ua_dc.log` | 400 | `31669d015844c97fdaa1f03521adb541703514fc64f79ec1455c597bc24f732c` |
| `raw_w8_900ua_run1.txt` | 481 | `bba4e3590f5cb73f80f7381ab7964321906af307f6596426b334e3df1e4a1ced` |
| `raw_w8_900ua_run2.txt` | 481 | `a5b4e016a83be002a60832a467e92f42244e2af6f2c1b829c04b61c295826965` |

The public deck differs only by replacing machine-specific PDK, OSDI, and
output paths with `$PDK_ROOT` and repository-relative paths; its SHA-256 is
`7a110d5768916b5db3388da47f4e6564e8a3ce13dee3acedf6102d54e9fc722e`.
The retained log and raw files are byte-identical to the native artifacts.

This deck contains model includes, a `.control` block, and two analyses, so it
is outside the single-analysis shared OpenADA circuit-simulation profile. The
evidence here is the retained native ngspice 46 deck, log, and raw data rather
than a normalized OpenADA result.

From this directory, with `PDK_ROOT` set:

```sh
ngspice -b tb_w8_900ua_dc.cir > log_w8_900ua_dc.log
```

The log retains two completed one-row analyses and no parser, fatal, abort,
NaN, voltage-limit, or convergence-recovery token.

This experiment does not establish an implemented reference or logic driver,
multi-cell code transfer, mismatch, switching, settling, corners, layout,
architecture selection, a gate disposition, or signoff.

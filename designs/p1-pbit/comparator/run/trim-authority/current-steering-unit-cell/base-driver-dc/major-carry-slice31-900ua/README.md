# Corrected 900 uA loaded 31-unit major-carry slice

This 27 °C, typical-model static experiment applies the corrected **2.25 µm**
NMOS unit width to the retained five-cell slice weighted 16, 8, 4, 2, and 1.
All five cells share ideal 2.1 V collector sources and one ideal 0.96 V
reference; each cell retains its passive 100/20 kΩ loaded-base network and
complementary ideal 0/1.2 V logic sources.

The four measured codes cross the code-15-to-16 major carry:

| code | effective P / N units | shared P / N collector current | collector differential | adjacent differential-current step |
| ---: | ---: | ---: | ---: | ---: |
| 14 | 14 / 17 | 12.3548499 / 15.0036591 µA | −2.6488092 µA | — |
| 15 | 15 / 16 | 13.2361991 / 14.1223098 µA | −0.8861107 µA | 1.7626985 µA |
| 16 | 16 / 15 | 14.1223098 / 13.2361991 µA | +0.8861107 µA | 1.7722214 µA |
| 17 | 17 / 14 | 15.0036591 / 12.3548499 µA | +2.6488092 µA | 1.7626985 µA |

The central step is **9.5229 nA**, or **0.540246%**, larger than either
neighboring step. This is a direct nominal step comparison, not DNL and not a
specification result. The preceding 780 µA slice measured a 7.1073 nA
(0.465342%) central excess; no acceptance tolerance is assigned to either.

Every code retains the same five sensed sink currents:

| weight | sensed current | target | target error |
| ---: | ---: | ---: | ---: |
| 16 | 14.088328300 µA | 14.076246334 µA | +0.0858323% |
| 8 | 7.042425980 µA | 7.038123167 µA | +0.0611358% |
| 4 | 3.520774650 µA | 3.519061584 µA | +0.0486796% |
| 2 | 1.760276490 µA | 1.759530792 µA | +0.0423805% |
| 1 | 0.880110137 µA | 0.879765396 µA | +0.0391856% |

Their **27.291915557 µA** total is 19.188284 nA (+0.0703570%) above
the 27.272727273 µA target. Power is not evaluated because the run did not
retain every supply operand under one explicit total-power definition.

## Artifact identity and reproduction

The exact executed artifacts were:

| artifact | bytes | native SHA-256 |
| --- | ---: | --- |
| `tb_major_carry_slice_900ua_dc.cir` | 6,047 | `099a50ce310e4f8bd3a91e19a6be09ca4449e567cc761e83191dac844986156f` |
| `log_major_carry_slice_900ua_dc.log` | 702 | `4c5f9c7a12b1959144ede5f888ea3b0ea763e84577ee0f91fd5a777d17efe9b9` |
| `raw_major_carry_900ua_code14.txt` | 1,217 | `a11c1891cd1b277543290d8d4ebad6287a07dd13c189aa22e7ed603bfa44e27a` |
| `raw_major_carry_900ua_code15.txt` | 1,217 | `8d8439c4458fe37ba5318b011b3c1883e8c0d93bc49c46558b0af88cbd8fadb4` |
| `raw_major_carry_900ua_code16.txt` | 1,217 | `52157d498b582f17b9575b5dcd802cc2ff6c3841d52909ef118fcde4257ae8bc` |
| `raw_major_carry_900ua_code17.txt` | 1,217 | `52ced52df7b47fee1d2776eef366630de24b0177bd771bb359543aceea76f253` |

The public deck differs only by replacing machine-specific PDK, OSDI, and
output paths with `$PDK_ROOT` and repository-relative paths; its SHA-256 is
`d53993ddefd0019e4f5ee7cd4515949e9d7004b3ae0813e12de20a03b3b9522f`.
The native log and all four raw files are byte-identical to the executed
artifacts.

From this directory, with `PDK_ROOT` set:

```sh
ngspice -b tb_major_carry_slice_900ua_dc.cir \
  > log_major_carry_slice_900ua_dc.log
```

The retained log contains four completed one-row analyses and no parser,
fatal, abort, NaN, voltage-limit, or convergence-recovery token.

This slice does not establish the full 1023-unit array, mismatch, DNL,
monotonicity yield, dynamic switching, glitch energy, settling, corners,
physical reference or logic drivers, layout, architecture selection, a gate
disposition, signoff, or tape-out readiness.

# Loaded 31-unit major-carry slice

This 27 C, typical-corner static experiment combines one weight-16 steering
cell with binary cells weighted 1, 2, 4, and 8. All five cells share ideal
2.1 V collector sources and one ideal 0.96 V reference; each retains its own
corrected passive loaded-base network and ideal complementary logic sources.

The four measured codes cross the 15-to-16 major carry:

| code | effective P / N units | shared P / N collector current | collector differential | adjacent differential-current step |
| ---: | ---: | ---: | ---: | ---: |
| 14 | 14 / 17 | 10.7049081 / 12.9994521 uA | -2.2945440 uA | — |
| 15 | 15 / 16 | 11.4685715 / 12.2357886 uA | -0.7672171 uA | 1.5273269 uA |
| 16 | 16 / 15 | 12.2357886 / 11.4685715 uA | +0.7672171 uA | 1.5344342 uA |
| 17 | 17 / 14 | 12.9994521 / 10.7049081 uA | +2.2945440 uA | 1.5273269 uA |

The major-carry step is 7.1073 nA, or 0.465342%, larger than either neighboring
step in this nominal static slice. This is a direct step comparison, not a DNL
or mismatch-yield result.

Every code retains the same five sensed sink currents, ordered by weight 16,
8, 4, 2, and 1: 12.206470300, 6.101938360, 3.050642300, 1.525238570, and
0.762598405 uA. Their 23.646887935 uA total is 0.044571% above the
23.636353 uA requested target. Positive source-delivery power is
41.185263960 uW at every code. The raw rows also retain every loaded base pair
and all ten actual 0 V / 1.2 V logic-source voltages.

## Execution identity and retained failure

The first retained deck used `PARAMS:` on each X-instance call. Ngspice 46
parsed that token as an extra electrical node and stopped before analysis with
a formal-versus-actual parameter mismatch. That exact failed source is retained
as `tb_major_carry_slice_dc_failed.cir`; its original failed log was not
retained, so the file is history rather than a complete failed-run package.

The executed correction follows ngspice User's Manual section 2.11.3: the
`.subckt ... PARAMS:` declaration remains, while each X-instance passes
`n_sink=<value> nx_hbt=<value>` directly after the subcircuit name. The retained
successful log contains four completed one-row analyses and no parser, fatal,
abort, convergence, or NaN message.

An independent rerun of the corrected retained deck in a fresh directory
reproduced all four raw files byte-for-byte:

| raw file | SHA-256 |
| --- | --- |
| `raw_carry_code14.txt` | `046e9be8aa42077a805daab8a7789322d6389845c9169b89499eea4fa3dc375a` |
| `raw_carry_code15.txt` | `86ba4e17c621e91e49c0b3fb8b8a175aaf38ef4aabe3ec34154aa4c61b26d383` |
| `raw_carry_code16.txt` | `e7b7fc2f25b7a88d35f92cfe499edea6928cee51fb234441b630bfaf227eacf9` |
| `raw_carry_code17.txt` | `d7c6bde3c5abd1feb5205b57ba55582c8a1df8b95f46afc78c7331814f8f19c3` |

This slice does not establish full-array comparator threshold transfer,
mismatch, DNL, monotonicity yield, dynamic switching, glitch energy, settling,
corners, a physical reference or logic driver, layout, architecture selection,
a gate disposition, or signoff.

## Reproducing

From this directory, with `PDK_ROOT` set to the IHP SG13G2 PDK root:

```sh
ngspice -b tb_major_carry_slice_dc.cir > log_major_carry_slice_dc.log
```

The published corrected deck differs from the executed deck only by replacing
machine-specific model and output paths with `$PDK_ROOT` and repository-relative
paths.

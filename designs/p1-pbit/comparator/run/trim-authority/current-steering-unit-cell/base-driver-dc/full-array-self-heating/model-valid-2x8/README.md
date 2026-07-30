# Model-valid 2xNx8 self-heating diagnostics

This package preserves four 27 C, typical-corner code-0 DC experiments on the
67-cell current-steering array connected directly to comparator candidate 2
(`XRFB` length 18.5 um).

The original thermometer representation used one `Nx=16` HBT call per side in
each of 63 cells. The installed IHP model documents `Nx=1..10`. These decks
replace each thermometer-side `Nx=16` call with two explicit parallel `Nx=8`
calls, producing 252 in-range thermometer HBT calls. The four binary cells
retain their original in-range `Nx` values of 8, 4, 2, and 1.

Two parallel `Nx=8` devices are not model-equivalent to one extrapolated
`Nx=16` device. These are model-domain diagnostics, not a selected
implementation or replacement candidate measurement.

## Results

| experiment | comparator self-heating | thermometer self-heating | binary self-heating | thermal warning | dynamic gmin | raw shape | collector crossing |
| --- | --- | --- | --- | --- | --- | --- | ---: |
| model-valid baseline | 4 calls on | 252 calls on | 8 calls on | present | present | 1,201 x 28 finite | -40.866795 mV |
| comparator off | off | 252 calls on | 8 calls on | present | present | 1,201 x 28 finite | -50.565834 mV |
| binary only | off | off | 8 calls on | absent | absent | 1,201 x 28 finite | -50.564546 mV |
| thermometer only | off | 252 calls on | off | absent | absent | 1,201 x 28 finite | -50.565817 mV |

The comparator-off combined-steering run retains the temperature-limiter NaN
and heat-sink warning even though every active steering HBT uses a documented
`Nx` value. Out-of-range `Nx=16` use is therefore not the sole cause.

Neither isolated steering class warns. The eight binary HBT calls alone and
the 252 thermometer HBT calls alone each complete without the thermal warning
or dynamic-gmin recovery. In this frozen diagnostic, the warning requires the
combined thermometer-plus-binary self-heating configuration. The smallest
binary contribution that crosses that interaction or aggregate threshold
remains under investigation.

## Artifact identity

| file | SHA-256 |
| --- | --- |
| `tb_full_array_code0_modelvalid_2x8.cir` | `2533c6403c42c760d8d6f416433691378317af7c279c6a301dbc86cd3d1633ca` |
| `log_modelvalid_2x8_code0.txt` | `33a841e4a2d90cfa75cc9360bfa5edb99670c80dd6d243b397ed7733bc61d3d7` |
| `raw_modelvalid_2x8_code0.txt` | `d3259ccf4e47ad7c6831abb4c4478f0235cda8aec424e592b03354e85c84ae7d` |
| `tb_full_array_code0_modelvalid_2x8_comp_selft0.cir` | `13d2f4ffd25f1fcaf2c5ab0e73c656b7e9b3b7bcf8433b4dafb8f68a8e791f98` |
| `log_modelvalid_2x8_comp_selft0_code0.txt` | `680a3235d67d7c8d45bec339afc31bc140672a05b05a5aa1ad45f79ae59c6f34` |
| `raw_modelvalid_2x8_comp_selft0_code0.txt` | `66d106dd9c44423f1f16bca91f8839983bfb692a04fc6e4b1fdffed83cc59741` |
| `tb_full_array_code0_modelvalid_binary_only_selft1.cir` | `58d5328d782ec3dfc2dd859f42798d25b4af0e9f22c765f13a32ea369b49c94f` |
| `log_modelvalid_binary_only_selft1_code0.txt` | `6edfb413e75f64f0cefbf053fbfc004ef031b17c2c2e7f56c8e0dcd1b32f2ea8` |
| `raw_modelvalid_binary_only_selft1_code0.txt` | `7a2024d7dcdb8a0d50d45031996da22239f9e886c7cf406856642fcec11b78d3` |
| `tb_full_array_code0_modelvalid_therm_only_selft1.cir` | `20864a94a5ae76741b7bc5d063d37dac1286e1acef7a728f5d0c0bfd887e0636` |
| `log_modelvalid_therm_only_selft1_code0.txt` | `43e06ad13c7769def289eb9b3497903a6693466c677a2aa69c94f563c8417f64` |
| `raw_modelvalid_therm_only_selft1_code0.txt` | `9675e64cf1cc90f2fe0c80ab589ab39565ef6199a91818e01671c9a99c55e180` |
| `p1_noise_amp.spice` | `5f6d03e5f945821d6c0af7b7446ca7a1774107cbefeb4a589cfbeceb45e3727d` |

The published decks differ from the executed decks only by replacing
machine-specific PDK, include, output, and schematic-source paths. Fresh
raw-empty reruns of all four sanitized decks reproduced the retained raw files
byte-for-byte and preserved the warning pattern above.

## Reproducing

Resolve the allowlisted PDK-root placeholder and use the IHP ngspice startup
configuration. An empty `SPICE_USERINIT_DIR` can fall back to an unrelated home
startup file and change compatibility behavior.

```sh
IHP_ROOT=/path/to/ihp-sg13g2
PDK_ROOT="$IHP_ROOT" envsubst '$PDK_ROOT' \
  < tb_full_array_code0_modelvalid_2x8.cir > resolved.cir
PDK_ROOT="$(dirname "$IHP_ROOT")" \
PDK=ihp-sg13g2 \
SPICE_USERINIT_DIR="$IHP_ROOT/libs.tech/ngspice" \
  ngspice -b resolved.cir > rerun.log 2>&1
```

Repeat the substitution and invocation for the other three decks in fresh
raw-empty directories.

This package does not establish valid self-heating-on full-array measurements,
a selected weight-16 implementation, mismatch or yield, dynamic switching,
settling, corners, layout, a gate disposition, signoff, or tape-out readiness.

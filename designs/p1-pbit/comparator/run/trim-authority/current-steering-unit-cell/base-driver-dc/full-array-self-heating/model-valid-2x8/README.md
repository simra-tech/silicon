# Model-valid 2xNx8 self-heating diagnostics

This package preserves nine 27 C, typical-corner code-0 DC experiments on the
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
| thermometer + XB8 | off | 252 calls on | XB8: 2 calls, weight 8 | absent | absent | 1,201 x 28 finite | -50.565827 mV |
| thermometer + XB8 + XB4 | off | 252 calls on | 4 calls, weight 12 | absent | absent | 1,201 x 28 finite | -50.565832 mV |
| thermometer + XB8 + XB4 + XB2 | off | 252 calls on | 6 calls, weight 14 | absent | absent | 1,201 x 28 finite | -50.565834 mV |
| thermometer + all binary | off | 252 calls on | 8 calls, weight 15 | present | present | 1,201 x 28 finite | -50.565834 mV |
| all binary; VIN initialized at -60 mV | off | 252 calls on | 8 calls, weight 15 | present | present | 1,201 x 28 finite | -50.565834 mV |

The comparator-off combined-steering run retains the temperature-limiter NaN
and heat-sink warning even though every active steering HBT uses a documented
`Nx` value. Out-of-range `Nx=16` use is therefore not the sole cause.

Neither isolated steering class warns. The eight binary HBT calls alone and
the 252 thermometer HBT calls alone each complete without the thermal warning
or dynamic-gmin recovery. In this frozen diagnostic, the warning requires the
combined thermometer-plus-binary self-heating configuration. In the descending
cumulative sequence, weights 8, 12, and 14 remain warning-free; adding the
final XB1 pair at weight 15 reproduces the warning and dynamic-gmin recovery.
This localizes an aggregate threshold crossed by that addition. It does not
identify XB1 as an intrinsically defective cell.

Changing only the pre-sweep `VIN_SRC` DC value from 0 to -60 mV does not remove
the warning. The weight-15 endpoint, the earlier comparator-off combined-class
run, and the VIN-initialized control all produce the same raw file byte for
byte. The initialization hypothesis is therefore falsified.

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
| `tb_full_array_code0_modelvalid_therm_plus_xb8_selft1.cir` | `af1bdbdf137d7af418ba3e155469838d9548a9f639e11f9aceb3560041acecbb` |
| `log_modelvalid_therm_plus_xb8_selft1_code0.txt` | `6d20e3bc88344bdd8b79487f80184df706984e3178e3b761c45e567cdf7ce942` |
| `raw_modelvalid_therm_plus_xb8_selft1_code0.txt` | `dd17813f782d84771fbed7bf712cf325784a6f53269a87a796d3eb156cbe99a0` |
| `tb_full_array_code0_modelvalid_therm_plus_xb8_xb4_selft1.cir` | `8eff05f9e4d09c6452bb7d381e7c855db4040414aa8336f8e16f31acf1f1344c` |
| `log_modelvalid_therm_plus_xb8_xb4_selft1_code0.txt` | `5032886f7844ca9df488023e0d432ba3a9fe276078c915ea9855a1517a2f50ec` |
| `raw_modelvalid_therm_plus_xb8_xb4_selft1_code0.txt` | `b1f4e0b2e6258174889f87dfd2f23456f103a899d41948a39f31cd07ae1b91b8` |
| `tb_full_array_code0_modelvalid_therm_plus_xb8_xb4_xb2_selft1.cir` | `ae9ced8b2eb9ad9b8e5f916d8a1f4928fd02a3f118d0d937a2981d41cacd171b` |
| `log_modelvalid_therm_plus_xb8_xb4_xb2_selft1_code0.txt` | `89279cc64787719cdeecc0129f4d4b0625662d69b0d18921101e8bde7fdcbc16` |
| `raw_modelvalid_therm_plus_xb8_xb4_xb2_selft1_code0.txt` | `1530b6f706915c2967cdc682d0f5630f6ff29a249b020aaea425a261f356aa44` |
| `tb_full_array_code0_modelvalid_therm_plus_all_binary_selft1.cir` | `dbe7b23237483ab7aad117032e41081468723b778e5510d5cc4218db5d2857aa` |
| `log_modelvalid_therm_plus_all_binary_selft1_code0.txt` | `9b1cbbdfa4f374df39797aaf4bda81d24b9467f8d2028940a2bbc5f968426d3a` |
| `raw_modelvalid_therm_plus_all_binary_selft1_code0.txt` | `66d106dd9c44423f1f16bca91f8839983bfb692a04fc6e4b1fdffed83cc59741` |
| `tb_full_array_code0_modelvalid_therm_plus_all_binary_vininit_m60mV.cir` | `64e45738a9cf9b39766c9f48396735311a401231110c704b1d08cafa4c8e227d` |
| `log_modelvalid_therm_plus_all_binary_vininit_m60mV_code0.txt` | `566c3c5013e95d231283b4f3a981d259681685b0a5a6bf2d56f6e770357f470d` |
| `raw_modelvalid_therm_plus_all_binary_vininit_m60mV_code0.txt` | `66d106dd9c44423f1f16bca91f8839983bfb692a04fc6e4b1fdffed83cc59741` |
| `p1_noise_amp.spice` | `5f6d03e5f945821d6c0af7b7446ca7a1774107cbefeb4a589cfbeceb45e3727d` |

The published decks differ from the executed decks only by replacing
machine-specific PDK, include, output, and schematic-source paths. Fresh
raw-empty reruns of all nine sanitized decks reproduced the retained raw files
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

Repeat the substitution and invocation for the other eight decks in fresh
raw-empty directories.

This package does not establish valid self-heating-on full-array measurements,
a selected weight-16 implementation, mismatch or yield, dynamic switching,
settling, corners, layout, a gate disposition, signoff, or tape-out readiness.

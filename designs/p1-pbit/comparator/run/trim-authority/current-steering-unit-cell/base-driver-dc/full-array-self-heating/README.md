# Full-array self-heating diagnostics

This package preserves four 27 C, typical-corner code-0 DC experiments on the
67-cell current-steering array connected directly to comparator candidate 2
(`XRFB` length 18.5 um). Each experiment changes only which active HBT class
receives the instance-level `selft=0` diagnostic override.

These are numerical-warning diagnostics, not replacement candidate
measurements. The self-heating-on candidate still emits a temperature-limiter
NaN and heat-sink warning. Its full-array threshold and step measurements
therefore remain checking.

| experiment | comparator HBT self-heating | steering HBT self-heating | thermal NaN / heat-sink warning | other retained diagnostics | raw shape | collector crossing |
| --- | --- | --- | --- | --- | --- | ---: |
| candidate baseline | on | on | present | dynamic gmin | 1,201 x 28 finite | -40.866879 mV |
| comparator off | off | on | present | dynamic gmin; one resistor-model `vmax` warning | 1,201 x 28 finite | -50.565936 mV |
| steering off | on | off | present | dynamic gmin | 1,201 x 28 finite | -40.865716 mV |
| all active HBTs off | off | off | absent | dynamic gmin | 1,201 x 28 finite | -50.564537 mV |

The all-off control establishes that the collective instance overrides remove
the thermal warning. It does not establish that disabling self-heating is an
acceptable design change. Each partial ablation leaves the warning present, so
neither partial run identifies one exclusive offending class.

## Model-domain limit found during review

The installed IHP `sg13g2_hbt_mod.lib` documents `Nx=1..10` and collector
current below `0.003*Nx` A. It defines thermal resistance as
`selft*3.26e3*(4/Nx)^0.9`. The full-array source sets all 63 thermometer cells
to `nx_hbt=16`, creating 126 active HBT calls outside the documented `Nx`
range. The four binary cells use in-range values 8, 4, 2, and 1.

That out-of-range use may contribute to the steering-class warning, but it
cannot by itself explain the comparator-only warning: the steering-off run
still warns with four `Nx=1` comparator HBTs. A model-valid weight-16
representation is under review; this package makes no architecture selection.

## Artifact identity

| file | SHA-256 |
| --- | --- |
| `tb_full_array_code0_isolated.cir` | `a64f5f5bd2d4a27e5228df207497ed5e18465c749ad335f0e3a8b20478a7f313` |
| `log_isolated_code0.log` | `b533f61e848bbe347c0074ab5247a938cee0fe64e419745435c8f1f0fc78f5f7` |
| `raw_isolated_code0.txt` | `bd7833d92f830f173e70e025c5aaf2552afcf403f71408223f7a82dd9c0ddfb3` |
| `tb_full_array_code0_comp_selft0.cir` | `efab4c98ce363550a5071072639c1a2074b4117751ab868b51639a32808a1d51` |
| `log_ablation_comp0.log` | `1b9f8e373e9d46c2ce69f0d73344292cfa73dcf12a238e07f8a39abd29d8bfd3` |
| `raw_ablation_comp0.txt` | `e404f05dc0434ebb9d71acc637eff7f533afa28d1b0988fc2d1f0a3ac723928f` |
| `tb_full_array_code0_steer_selft0.cir` | `586e8966232c7e679d108cc34723b2dc639e2fcabb5d046c63ff04a1d4a99f54` |
| `log_ablation_steer0.log` | `258dde1394e04cf994b24fc7e3935a9d23a112aeed92b404671404a3bf355be0` |
| `raw_ablation_steer0.txt` | `a2ece9fc426698c75d92bfc8cb70c0f0fb4a746750b2ed5ab42d34c424edd0fb` |
| `tb_full_array_code0_all_selft0.cir` | `5f6b7f7c5c1c17a1c2c179e92b5b68f0503277b0640d2d5faade18b42784f800` |
| `log_ablation_all0.log` | `b7d697ba63a8eb8a7ca537ac2f5e2baed92510359dd4376d62e06f99fb994604` |
| `raw_ablation_all0.txt` | `000806faaf179e24727bbda71215144be5048aa563a99db47cdd61d634be65c4` |
| `p1_noise_amp.spice` | `d86a898590962e14c9e95277b8fc889f14bfd88e7aef2c27ba56fca2d2e19633` |

The Design Engineer reported the all-off execution log as 210 lines. The
retained file has 17 newline records; carriage-return progress output accounts
for the discrepancy. The warning, marker, row-count, raw-shape, and hash claims
above were checked directly from the retained files.

## Reproducing

The published decks differ from the executed decks only by replacing
machine-specific PDK, include, and output paths. Ngspice compatibility mode
changes this circuit's initialization behavior, so resolve `$PDK_ROOT` before
invoking ngspice and use the IHP init rather than an unrelated user init:

```sh
IHP_ROOT=/path/to/ihp-sg13g2
PDK_ROOT="$IHP_ROOT" envsubst '$PDK_ROOT' \
  < tb_full_array_code0_isolated.cir > resolved.cir
PDK_ROOT="$(dirname "$IHP_ROOT")" \
PDK=ihp-sg13g2 \
SPICE_USERINIT_DIR="$IHP_ROOT/libs.tech/ngspice" \
  ngspice -b resolved.cir > rerun.log 2>&1
```

Repeat the substitution and invocation for the other three decks. Fresh
raw-empty reruns of all four sanitized decks reproduced the retained raw files
byte-for-byte. The baseline, comparator-off, and steering-off reruns retained
their respective warning patterns; the all-off rerun remained warning-free.

This package does not establish valid self-heating-on full-array measurements,
model-valid weight-16 implementation, mismatch or yield, dynamic switching,
settling, corners, physical reference or logic drivers, layout, a gate
disposition, signoff, or tape-out readiness.

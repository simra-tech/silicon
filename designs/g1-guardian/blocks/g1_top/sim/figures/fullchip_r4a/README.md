# Full-chip waveforms, r4 candidate (`r4a` / `r4b` campaign)

Every waveform and every number in these figures is **simulated** (ngspice-46 with the Icarus d_cosim, IHP SG13G2
open PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`). No run was repeated to make them. The PNGs are drawn from the
waveforms and logs of the runs recorded in [`../../FULLCHIP_CDL_R4_20260927.md`](../../FULLCHIP_CDL_R4_20260927.md).
That deck is the r3x deck with the r4 CDL (`e060c0c5`) and the `nf4_novclk` TRIP extraction (`6f518e07`).

## Generator

`sim/campaigns/plot_fullchip_waves.py` (SHA-256 `6843322f39424d1349f3cf00a57229bb52d804e125f1bea1fe095c3f1d68e0d1`), matplotlib 3.3.4 (Agg), 1600 px wide at 110 dpi.
Command, from the repository root, run while the full logs were still in `sim/logs/`:

```
W=designs/g1-guardian/blocks/g1_top/sim
python3 $W/campaigns/plot_fullchip_waves.py --glob 'cdl_*_r4a*' --glob 'cdl_*_r4b*' \
  --exclude 'ss_125C.*optreltol|tt_27C_gear_compact_cdle060c0c5_rtleco20260925_icx_maxstep1ns_optreltol|fm1p25_t19' \
  --record $W/FULLCHIP_CDL_R4_20260927.md --out $W/figures/fullchip_r4a
```

Inputs:
- the waveforms `sim/results/waves/<tag>.txt` (gitignored), written with ngspice `linearize` at 20 ns;
- the logs `sim/logs/<tag>.log`. Logs over 300 kB were moved afterwards to
  `${BULK}/g1-freeze-retention-20260925/g1_top_logs_r4a/` (hash in `index.json` and in
  `review/local-retention-20260925.json`).

Only runs whose log says `# run status completed` are drawn. The `--exclude` pattern keeps one figure per case:
- ss 125 °C is drawn from the 5 ns runs. The 1 ns `reltol 5e-4` twins agree within 0.1 ns (record) and are left out.
- c_mid tt nominal is drawn from the `--tstop 19` run (r4b). The `reltol 5e-4` run to 28 µs agrees within 0.2 ns.
- c_mid tt 1.25× is drawn from the `reltol 5e-4` run to 28 µs, not the `--tstop 19` twin.

`index.json` lists, for every figure: the tag, case, corner and temperature, the record row and status, and the
waveform and log paths with their SHA-256. It also lists the tags matched by the globs and skipped because their
log status is `failed`, `timeout` or still running (25 tags).

## What each figure shows

The layout is the same as `../fullchip_r3full/README.md`:
- **Load-event cases:** (a) load current with the commanded profile; (b) logic lanes EN, `cmp_soft`, `cmp_hard`,
  `trip_d`, `tripped`; (c) `GATE` pad with 1 V and 0.33 V marked; (d) internal VREF; (e) supplies. A ±3 µs zoom
  column adds the comparator input `icmp` against `vth_soft` / `vth_hard`.
- **Power-up cases (gB, gB_pd, gS):** supplies, `GATE` with the `POWERUP` measures, EN / RTL `trip` / `tripped`,
  and load current.
- **The calibration rehearsal (`cal`)** is drawn as a load-event case. The DAC code schedule is in the deck's
  `* CALSCHED` line.

The titles of the near-threshold figures carry the scaled fault level from `--fault-mult`. Their description line
quotes the tt nominal ("~39.25 mV") at every corner. The corner nominals are 39.32 mV (ss 125 °C) and 39.14 mV
(ff −40 °C), as the record states.

| PNG | Case | Corner | Record status | PNG sha256 (16) | Waveform sha256 (16) | Log sha256 (16) |
|---|---|---|---|---|---|---|
| `cdl_c_mid_pex_ff_-40C_gear_compact_cdle060c0c5_rtleco20260925_icx_fm1p15_maxstep1ns_functional_r4a.png` | c_mid fault x1.15 | ff -40 °C | passed | `9569d845d50e750d` | `b1f0acc300ba2a54` | `0591add9b69c89e9` |
| `cdl_c_mid_pex_ff_-40C_gear_compact_cdle060c0c5_rtleco20260925_icx_fm1p1_maxstep1ns_functional_r4a.png` | c_mid fault x1.1 | ff -40 °C | passed | `7e1ec324a4dd6f3f` | `621b0c3cf81e5017` | `bcf420d5a7ef56ad` |
| `cdl_c_mid_pex_ff_-40C_gear_compact_cdle060c0c5_rtleco20260925_icx_fm1p5186_maxstep1ns_functional_r4a.png` | c_mid fault x1.5186 | ff -40 °C | passed | `de4ff112bd22fe6b` | `e3f0e052c90ce432` | `a017295af0b74535` |
| `cdl_c_mid_pex_ff_-40C_gear_compact_cdle060c0c5_rtleco20260925_icx_fm1p6126_maxstep1ns_functional_r4a.png` | c_mid fault x1.6126 | ff -40 °C | passed | `043b0f7e4703802b` | `b25c09ed4387e699` | `d15ff25600a47d2d` |
| `cdl_c_mid_pex_ff_-40C_gear_compact_cdle060c0c5_rtleco20260925_icx_maxstep1ns_functional_r4a.png` | c_mid | ff -40 °C | passed | `8fa16ddca3dbdb77` | `f3fa6e48ca1ddd3e` | `2b53edfa4ce957ae` |
| `cdl_c_mid_pex_ss_125C_gear_compact_cdle060c0c5_rtleco20260925_icx_fm1p25_maxstep5ns_functional_r4a.png` | c_mid fault x1.25 | ss 125 °C | passed | `be3a2df1e4faf346` | `999533ec66baa3d0` | `0a624e56e38ac359` |
| `cdl_c_mid_pex_ss_125C_gear_compact_cdle060c0c5_rtleco20260925_icx_fm1p2_maxstep5ns_functional_r4a.png` | c_mid fault x1.2 | ss 125 °C | passed | `5b65183cccbfc663` | `8f7bb68195a017bb` | `7a5ebd7c00010d43` |
| `cdl_c_mid_pex_ss_125C_gear_compact_cdle060c0c5_rtleco20260925_icx_fm1p5256_maxstep5ns_functional_r4a.png` | c_mid fault x1.5256 | ss 125 °C | passed | `e0157a3514f180cc` | `dae1691d435f5981` | `7309cf6813b84153` |
| `cdl_c_mid_pex_ss_125C_gear_compact_cdle060c0c5_rtleco20260925_icx_fm1p62_maxstep5ns_functional_r4a.png` | c_mid fault x1.62 | ss 125 °C | passed | `1b8baade01717db8` | `bf62ee3adb057c13` | `25a54f3b9ab0e04d` |
| `cdl_c_mid_pex_ss_125C_gear_compact_cdle060c0c5_rtleco20260925_icx_maxstep5ns_functional_r4a.png` | c_mid | ss 125 °C | passed | `4fde2cb42c7e45fe` | `1d6a6a722c9caf08` | `26ae11393662cbcd` |
| `cdl_c_mid_pex_tt_27C_gear_compact_cdle060c0c5_rtleco20260925_icx_fm1p25_maxstep1ns_optreltol5em4_functional_r4a.png` | c_mid fault x1.25 | tt 27 °C | passed | `caeb55a95f2d3052` | `f29470bbfbfca7be` | `a3e5fd63f5697a4c` |
| `cdl_c_mid_pex_tt_27C_gear_compact_cdle060c0c5_rtleco20260925_icx_fm1p2_maxstep1ns_functional_r4a.png` | c_mid fault x1.2 | tt 27 °C | passed | `0d420bdf1616845a` | `6268ba9d85f136a9` | `639c1071d494d410` |
| `cdl_c_mid_pex_tt_27C_gear_compact_cdle060c0c5_rtleco20260925_icx_fm1p5229_maxstep1ns_functional_r4a.png` | c_mid fault x1.5229 | tt 27 °C | passed | `9215cab1bb36fd81` | `d59df5e9fb5e0d5a` | `a34b69cda3305b14` |
| `cdl_c_mid_pex_tt_27C_gear_compact_cdle060c0c5_rtleco20260925_icx_fm1p6171_maxstep1ns_functional_r4a.png` | c_mid fault x1.6171 | tt 27 °C | passed | `013d015a956ca4d6` | `735438dd64fdfe8f` | `e3e9ac1da0c06d54` |
| `cdl_c_mid_pex_tt_27C_gear_compact_cdle060c0c5_rtleco20260925_icx_t19_maxstep1ns_functional_r4b.png` | c_mid | tt 27 °C | passed | `e50d365edcfd8a5a` | `d7493008e8f3ebec` | `0363676d7844efeb` |
| `cdl_c_mid_pex_tt_27C_gear_osctl_compact_cdle060c0c5_rtleco20260925_icx_maxstep1ns_functional_r4a.png` | c_mid (osc tl) | tt 27 °C | passed | `f9545e1f2fb456ca` | `4305df0185b74691` | `4e7d5903030be01e` |
| `cdl_cal_pex_tt_27C_gear_cdle060c0c5_rtleco20260925_ser4_icx_soft130-124-2_maxstep1ns_functional_r4b.png` | cal | tt 27 °C | passed | `ba33c75f96d79091` | `3c6688f369430ef4` | `c72f8ed978feb097` |
| `cdl_e20_pex_tt_27C_gear_cdle060c0c5_rtleco20260925_icx_maxstep1ns_functional_r4a.png` | e20 | tt 27 °C | passed | `26d623fd213ba3f5` | `7fc2743de69a795e` | `e9509213c5c07316` |
| `cdl_gB_pd_pex_ff_-40C_gear_por_cdle060c0c5_rtleco20260925_icx_maxstep2ns_functional_r4a.png` | gB_pd | ff -40 °C | passed | `cf66981ca29f3bb1` | `0f4513275a96a4f3` | `113a27e57360ffa9` |
| `cdl_gB_pd_pex_ss_125C_gear_por_cdle060c0c5_rtleco20260925_icx_functional_r4a.png` | gB_pd | ss 125 °C | passed | `2c145937863a2471` | `f01a3cc87a5a4db8` | `52bcce566b364f34` |
| `cdl_gB_pex_ff_-40C_gear_por_cdle060c0c5_rtleco20260925_icx_maxstep2ns_functional_r4a.png` | gB | ff -40 °C | passed | `913e591365cb576f` | `7be2f1bc1a49fa49` | `99b8bee898ec7060` |
| `cdl_gB_pex_ss_125C_gear_por_cdle060c0c5_rtleco20260925_icx_functional_r4a.png` | gB | ss 125 °C | passed | `1493c7b1c7cdd3b7` | `cbf0bac1ed3165c0` | `2812200d9986cdb9` |
| `cdl_gS_pex_ss_125C_gear_por_cdle060c0c5_rtleco20260925_icx_functional_r4a.png` | gS | ss 125 °C | passed | `67980a374edbbeed` | `8c74061cf98cbc05` | `5955b40949ae3cf9` |
| `cdl_q_pex_tt_27C_gear_cdle060c0c5_rtleco20260925_icx_maxstep1ns_functional_r4a.png` | q | tt 27 °C | passed | `fdd49e63bb8a52e1` | `c74dd48f62f030a0` | `ac49d652a1bfcf6e` |

## Not drawn

| Item | Status |
|---|---|
| b_s tt, f_mid tt, hard_pulse tt, hard 2-code calibration | **not run to completion or still running** (see the record); no figure yet |
| Failed attempts (ss 1 ns / 2 ns, tt 28 µs first attempts, coarse hard cal after its crossing) | **failed (numerical)**; no figure. The coarse hard cal and the tt c_mid first attempt emitted their measures, which are in the record. |
| 1 ns `reltol 5e-4` twins at ss 125 °C, c_mid tt `reltol 5e-4`, 1.25× tt `--tstop 19` | completed, **not drawn** (excluded as duplicates) |

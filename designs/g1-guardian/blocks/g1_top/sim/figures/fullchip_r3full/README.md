# Full-chip waveforms, r3 chip of record (`r3full` campaign + `gS`)

Every waveform and every number in these figures is **simulated** (ngspice-46 with the
Icarus d_cosim, IHP SG13G2 open PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`). No run was
repeated to make them: the PNGs are drawn from the waveforms and logs of the runs recorded in
[`../../FULLCHIP_CDL_R3_20260926.md`](../../FULLCHIP_CDL_R3_20260926.md) and, for `gS`, section 5 of
[`../../campaigns/RESULTS_20260925.md`](../../campaigns/RESULTS_20260925.md).

## Generator

`sim/campaigns/plot_fullchip_waves.py` (SHA-256 `6843322f39424d1349f3cf00a57229bb52d804e125f1bea1fe095c3f1d68e0d1`),
matplotlib 3.3.4 (Agg), 1600 px wide at 110 dpi. Command, from the repository root:

```
python3 designs/g1-guardian/blocks/g1_top/sim/campaigns/plot_fullchip_waves.py \
  --glob 'cdl_*_r3full*' \
  --glob 'gS_pex_c1414_beh_tt_27C_ovr-bgrsch_padsnodcn_clockfix_rtleco20260925_functional_eco4_gS' \
  --exclude 't2foff|optreltol|padspdk|125C_gear_compact_cdl5e47ae02_rtleco20260925_icx_functional' \
  --out designs/g1-guardian/blocks/g1_top/sim/figures/fullchip_r3full
```

Inputs:
- the waveforms `sim/results/waves/<tag>.txt` (gitignored). They are written by `run_top.py` /
  `run_top_cdl.py` with ngspice `linearize` at 20 ns, so the VREF spikes are under-sampled.
- the logs `sim/logs/<tag>.log`: header description, `# run status`, and the measures
  (`TRIP`, `REARM`, `POWERUP`, `CLOCK`, `t_tripped`, `t_gate1v`).

Only runs whose log says `# run status completed` are drawn. The `--exclude` pattern keeps one
figure per recorded case:
- the T2F-off witnesses and reltol variants are left out; the record shows they agree with
  the primary row within 0.2 ns;
- ss/125 °C is drawn from the 1 ns run, not the 5 ns run.

`index.json` lists, for every figure:
- the tag, case, corner and temperature;
- the record row and status;
- the waveform and log paths (as `${REPO}/…`) with their SHA-256;
- the parsed log measures.

It also lists the tags matched by the glob and skipped because their log status is `failed`.

## What each figure shows

**Load-event cases** have a shared time axis on the left and a zoom on the right. The zoom
covers ±3 µs around the `tripped` rise when the run trips, or around the load event when it
does not.
- (a) Load current `I(Vim)` with the commanded profile. The shunt voltage is I × 25 mΩ.
- (b) Logic lanes: `EN` (core side), `cmp_soft`, `cmp_hard`, `trip_d` (RTL decision) and
  `tripped` (G1_GATE latch).
- (c) `GATE` pad, with 1 V and 0.33 V marked. The GATE < 1 V and < 0.33 V times are the
  log's measures, counted from the load event. For f_mid the re-arm measures are shown too.
- (d) Internal VREF net.
- (e) Supplies: VDDA and IOVDD come from one 3.3 V rail; VDD is the 1.2 V core supply.
- The zoom column shows (a)–(c), the comparator input `icmp` against `vth_soft` / `vth_hard`,
  and VREF.
- Dotted line: load event. Red dashed line: `tripped`.

**Power-up cases (gA, gB, gB_pd, gS):**
- (e1) VDDA = IOVDD and VDD;
- (e2) `GATE` pad with 1 V marked, and the `POWERUP` measures;
- (e3) `EN`, RTL `trip`, and the `tripped` latch;
- (e4) load current.

| PNG | Case | Corner | Record status | PNG sha256 (16) | Waveform sha256 (16) | Log sha256 (16) |
|---|---|---|---|---|---|---|
| `cdl_b_s_pex_tt_27C_gear_cdl5e47ae02_rtleco20260925_icx_maxstep1ns_functional_r3full.png` | b_s | tt 27 °C | completed, 18 802 s ; pass (soft window: 256 samples = 27.13 µs + decision) | `363b1b33e2f5a486` | `4b1026581c247402` | `b9e22ccb0c417207` |
| `cdl_c_mid_pex_ff_-40C_gear_compact_cdl5e47ae02_rtleco20260925_icx_maxstep1ns_functional_r3full.png` | c_mid | ff -40 °C | completed, 12 586 s ; pass | `dbd16fba0c325fdb` | `981e77db54c6de42` | `64b6161f7327332c` |
| `cdl_c_mid_pex_ss_125C_gear_compact_cdl5e47ae02_rtleco20260925_icx_maxstep1ns_functional_r3full.png` | c_mid | ss 125 °C | completed, 12 368 / 10 322 / 7698 s ; pass | `be80d0a29bc6c598` | `5d8a99d2d1493718` | `d7f38f484cd755e6` |
| `cdl_c_mid_pex_tt_27C_gear_compact_cdl5e47ae02_rtleco20260925_icx_fm1p15_maxstep1ns_functional_r3full2.png` | c_mid fault x1.15 | tt 27 °C | completed, 8591 s ; consistent with the documented hard-comparator kick offset | `63ae6c4dfc573ebf` | `df6087c25b0d5f90` | `9d2484f9fa5be4fd` |
| `cdl_c_mid_pex_tt_27C_gear_compact_cdl5e47ae02_rtleco20260925_icx_fm1p25_maxstep1ns_functional_r3full2.png` | c_mid fault x1.25 | tt 27 °C | completed, 8645 s ; trips inside the uncalibrated no-trip region (0.80T), as documented by the comparator kick offset → calibration requirement (not counted as a pass) | `bd2c3e3b56e8efae` | `433984d7e1bcaea9` | `51a990e5af69bc35` |
| `cdl_c_mid_pex_tt_27C_gear_compact_cdl5e47ae02_rtleco20260925_icx_maxstep1ns_functional_r3full.png` | c_mid | tt 27 °C | completed, 12 316 s ; pass (≥1.1T, < 10 µs) | `3a1cbd4ce1a4f7c2` | `a6251fc6400dbdbe` | `0941928032e008ff` |
| `cdl_c_pex_tt_27C_gear_cdl5e47ae02_rtleco20260925_icx_maxstep1ns_functional_r3full.png` | c | tt 27 °C | completed, 12 821 s ; pass | `de41518862f79c94` | `cb569d5307cdc38d` | `3c5cd2a9981d83e3` |
| `cdl_e20_pex_tt_27C_gear_cdl5e47ae02_rtleco20260925_icx_maxstep1ns_functional_r3full.png` | e20 | tt 27 °C | completed, 12 987 s ; pass | `e8d16bea45d7955b` | `9573ddb7ebb0fce2` | `1e371016da21dfd4` |
| `cdl_f_mid_pex_tt_27C_gear_cdl5e47ae02_rtleco20260925_icx_maxstep1ns_functional_r3full.png` | f_mid | tt 27 °C | completed, 17 123 s ; pass (trip + re-arm) | `af8b4fa808917db1` | `31ecf6acce36f31c` | `0235209a44de2fe8` |
| `cdl_gA_pex_tt_27C_gear_por_cdl5e47ae02_rtleco20260925_icx_maxstep2ns_functional_r3full.png` | gA | tt 27 °C | completed, 2928 s ; expected condition, recorded (P1 excludes this order) | `637327eaa8f938d8` | `ce7a3707af0c829f` | `6cb5f9c72f898fc0` |
| `cdl_gB_pd_pex_tt_27C_gear_por_cdl5e47ae02_rtleco20260925_icx_functional_r3full.png` | gB_pd | tt 27 °C | completed, 2360 s ; pass | `ab46dce8f99409ce` | `00d149d3395b7fbf` | `c166d0400686d3a2` |
| `cdl_gB_pex_tt_27C_gear_por_cdl5e47ae02_rtleco20260925_icx_functional_r3full.png` | gB | tt 27 °C | completed, 2594 s ; pass (no false GATE at power-up, no false trip at EN) | `1da98ac7598059fb` | `c3924044f3a4e837` | `04f16dc9e9a81ab1` |
| `cdl_hard_pulse_pex_tt_27C_gear_cdl5e47ae02_rtleco20260925_icx_maxstep1ns_functional_r3full.png` | hard_pulse | tt 27 °C | completed, 13 295 s ; pass (a pulse shorter than HARD_N decisions does not trip) | `eceb4201e35a33e1` | `5c3a916f80bae664` | `afc1656045e28d04` |
| `cdl_q_pex_tt_27C_gear_cdl5e47ae02_rtleco20260925_icx_maxstep1ns_functional_r3full.png` | q | tt 27 °C | completed, 15 184 s ; pass (no false trip) | `b5102f3dd2655513` | `2ad8e46061bb6cec` | `4aba084d905d4eb6` |
| `cdl_q_pex_tt_27C_gear_osctl_cdl5e47ae02_rtleco20260925_icx_maxstep1ns_functional_r3full.png` | q (osc tl) | tt 27 °C | completed, 22 993 s ; pass | `ead3e217b8bcaa34` | `1ab17367268b1ed1` | `864a6fe97ca26392` |
| `gS_pex_c1414_beh_tt_27C_ovr-bgrsch_padsnodcn_clockfix_rtleco20260925_functional_eco4_gS.png` | gS | tt 27 °C | passed | `2ee0f4a1ec3eecea` | `4a7f87ed835bd784` | `88b62f4ed35b8554` |

Full hashes are in `index.json`.

**How the tags map to what the figures show (simulated):**
- **Trip cases:** GATE < 1 V at +1.543 µs (c_mid tt), +1.726 µs (ss/125 °C), +1.433 µs
  (ff/−40 °C), +1.532 µs (c, e20, f_mid) and +28.131 µs (b_s, soft).
- **No-trip cases:** q, q with the transistor-level oscillator, hard_pulse, and c_mid ×1.15
  do not trip.
- **Near threshold:** c_mid ×1.25 trips. The record classes it as a calibration requirement,
  not a pass.
- **Power-up:** gA drives GATE to 3.3 V for 2.38–6.72 µs while EN is low, which is expected and
  excluded by P1. gB and gB_pd keep GATE ≤ 31 µV. gS peaks at 0.545 V.

**Figure notes:**
- The two figures near 76 kB (f_mid, c_mid ×1.25) were palette-reduced to stay under 250 kB.
- The titles of the c_mid ×1.15/×1.25 figures carry the scaled fault level from `--fault-mult`.
  Their log header still describes the unscaled 1.8 A case.

## Not drawn

| Item | Status |
|---|---|
| T2F-off witnesses, reltol 5e-4 variants, c_mid ss/125 °C 5 ns | completed, **not drawn** (excluded; they agree with the drawn rows per the record). Drop the `--exclude` terms to draw them. |
| Stock-pad (`padspdk`) runs, 5 ns tt runs, loose-tolerance osc runs, gA 20 ns | **failed / not run to completion** (see record); no figure |
| IOVDD as a separate trace | **not applicable**: it is not saved; it comes from the same rail source as VDDA (0.5 Ω each) |

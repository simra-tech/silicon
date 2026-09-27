# nf4_novclk (r4 candidate TRIP macro): block qualification, 27 Sep 2026

This covers the block-level items that `README.md` in this directory left **not run**:
- the post-layout comparator delay, settle and DAC decks on the new extraction;
- a mismatch Monte Carlo of the non-overlap window.

Everything is simulated (ngspice, kpex 2.5D CC extraction, no silicon). The candidate is still not adopted. The chip
of record stays r3.

- Extraction under test: `sim/postlayout/g1_trip_nf4_novclk_pex.spice`, `6f518e07…` ("r4").
- Reference: `sim/postlayout/g1_trip_nf4_pex.spice`, `ba86b7b2…` ("r3").

Both were re-run in this session with the same decks. 1 LSB = 1.962 mV at `icmp` = 0.196 mV of shunt.

## Status

| Check | r3 (NF4 extraction) | r4 (novclk extraction) | Status (r4) |
|---|---|---|---|
| Comparator delay deck, tt 1.2 V 27 °C, 50 / 5 / 1 mV | all decisions right; 1 mV in 0.859 ns | 50 and 5 mV right. **1 mV: strobe 1 decided high with the input below threshold**, so no delay was measured | **failed** (1 mV at tt) |
| Comparator delay deck, ss 1.08 V −40 °C, 50 / 5 / 1 mV | all right; 1 mV in 1.694 ns | all right; 1 mV in **1.996 ns** | passed |
| Settle deck, tt 1.2 V 27 °C (the recorded corner) | 104.4 / 227.2 / 156.7 / 95.5 ns | 104.4 / 227.2 / 156.7 / 95.5 ns | passed (equal to r3) |
| Settle deck, ss 1.08 V −40 °C and ff 1.32 V 125 °C (not recorded before) | see §1.2 | equal to r3 within 0.003 ns | passed (equal to r3) |
| DAC deck, tt 27 °C res_typ: 256 soft codes, 26 hard codes, soft settling | run for the first time on NF4 here | equal to r3 | passed |
| Window mismatch MC, ss/1.08 V/−40 °C, 30 seeds | n/a (r3 has no window) | w_fall min **10.09** / mean 10.32 / σ 0.087 ns; w_rise min **8.30** / mean 8.40 / σ 0.057 ns; max 10.49 ns | passed (> 2.5 ns, < 20 ns) |
| Window mismatch MC, ff/1.32 V/125 °C, 30 seeds | n/a | w_fall min 9.77 / max **10.03** / σ 0.064 ns; w_rise min 8.50 / max 8.77 / σ 0.063 ns | passed (< 20 ns; also < the README's 15 ns) |
| Kick brackets under mismatch (kick_rt.py), tt, 30 seeds, hard 200 / soft 153 | — | Brackets: not run. A screen at ud ±10 LSB was run instead: 19 complete seeds (83 of 120 points), every point as expected, none mixed | screen passed on 19 seeds; brackets **not run**; seeds 3019/3020 partial, 3022–3030 **not run** (time box) |
| Resistor or capacitor mismatch; MC at corners other than the two above; MC of the comparator delay | — | — | **not run** |

"Passed" for the delay deck uses the deck's own criterion: every first strobe decides low and every second strobe
decides high. The window limits come from `review/redteam-20260927/trip_path/FINDINGS.md` §6.2:
- lower limit > 2.5 ns at ss/1.08 V/−40 °C;
- hard cap < 20 ns;
- both edges count.

## Built against

| Item | Value | How established |
|---|---|---|
| PDK | IHP-Open-PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` | `cat /foss/pdks/ihp-sg13g2/COMMIT` in the container (also checked by `flow/run.sh` on every run) |
| Container image | `sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2` | `podman image inspect`; `flow/run.sh` identity check |
| ngspice | ngspice-46, KLU, build date 27 Jul 2026 | `ngspice -v` in the container |
| Model cards (unmodified) | `cornerMOSlv.lib` `03d50584…`, `cornerMOShv.lib` `5a1f862d…`, `sg13g2_moslv_mismatch.lib` `2d3251e2…`, `sg13g2_moshv_mismatch.lib` `2e9612bd…` | `sha256sum` in the container |

Every run went through `flow/run.sh` (podman) with `G1_CPUSET` set to one CPU in 45–63, at normal priority (no
`nice`). The host was heavily loaded by other users (load average 210–236 on 128 CPUs), so the wall times below are
long. `${REPO}` is the repository root and `${BULK}` the external artifact root. The run root is
`${BULK}/r4-20260927/blockqual/`.

## 1. Post-layout decks, r3 vs r4

### 1.1 Comparator delay (`sim/postlayout/tb_trip_cmp_pex.cir`)

The deck is unchanged: soft DAC at code 128, 5 MHz strobe, and an ISENSE step 1 ns after the first strobe. The
delay is measured from the second `cmp_clk` pin edge to `cmp_soft` = 0.6 V. The columns are: od at the 1st strobe
/ effective od at the 2nd strobe / delay.

| Corner, overdrive | r3 recorded 24 Sep | r3 re-run today | r4 |
|---|---|---|---|
| tt 1.2 V 27 °C, 50 mV | −52.9 / 49.7 mV / 0.675 ns | identical | −53.7 / 50.3 mV / **0.963 ns** |
| tt 1.2 V 27 °C, 5 mV | −7.4 / 4.77 mV / 0.796 ns | identical | −8.6 / 5.20 mV / **1.082 ns** |
| tt 1.2 V 27 °C, 1 mV | −3.89 / 0.77 mV / 0.859 ns | identical | −4.62 / 1.19 mV / **—**: strobe 1 decided **high** (q = 1.2 V at 60 ns); no rising edge after strobe 2 |
| ss 1.08 V −40 °C, 50 mV | −51.8 / 49.9 mV / 1.014 ns | identical | −52.4 / 50.5 mV / **1.428 ns** |
| ss 1.08 V −40 °C, 5 mV | −6.9 / 4.95 mV / 1.435 ns | identical | −7.6 / 5.41 mV / **1.771 ns** |
| ss 1.08 V −40 °C, 1 mV | −2.88 / 0.95 mV / 1.694 ns | identical | −3.56 / 1.40 mV / **1.996 ns** |

**Why r4 is slower (a measurement-reference effect).**
- The deck measures from the macro pin `cmp_clk`. In r4 the soft comparator is clocked by `cmp_clk_s`, which is
  the pin through the generator's NOR + inverter.
- That path adds 0.27 ns at tt and 0.40 ns at ss/−40 °C (`ev_soft` of the window bench, nominal extraction). These
  match the extra delay: +0.29 ns at tt 50 mV and +0.41 ns at ss 50 mV.
- The comparator's own decision time is therefore unchanged within about 0.05 ns.
- The latency from the chip clock to the soft decision grows by one gate pair.
- The hard comparator's evaluate latency from the pin (`ev_hard`) is 0.17–0.28 ns in r4. Through r3's `XCLKI` it
  was 0.23–0.37 ns (`evidence/sim/window_r3_reference.txt`).

**Why tt 1 mV fails.** The deck's criterion needs the first strobe, taken from the DC operating point, to decide
low. Only the difference that ISENSE sets separates it from a high decision: −1.47 mV at `icmp` before the edge
(`evidence/blockqual/cmp_1mV_diag.txt`).
- At that input, r3 decides low and r4 decides high, at 21.25 ns. So the r4 soft path's effective offset in this
  first-strobe situation is more than 1.47 mV (0.75 LSB) toward tripping.
- The soft kick moves `icmp` and `vth_soft` by about 80 mV during evaluation in both extractions (min 0.673 / 0.670 V
  between 20 and 22 ns). The 1 mV case sits inside the kick residue. The postlayout README already said this for
  r3: "bracket set by the kick residue".
- This agrees with the strobe-train brackets on the same extraction (README gate 3, `evidence/sim/gate3_table.txt`):
  soft code 153 trips at ud +1 and not at +2, so the effective threshold is 1–2 LSB below the code. r3 gave 0 / −1.
- So the r4 soft path trips about 1 LSB (≈ 0.2–0.4 mV of shunt) earlier than r3's.
- This is within the ≤ 2 LSB acceptance of FINDINGS §6.4. It still fails this deck's 1 mV criterion at tt, and the
  status says so. The deck was not changed to make it pass.
- ss/−40 °C decided correctly at 1 mV: od1 −3.56 mV for r4 against −2.88 mV for r3. Whether the tt first-strobe
  flip also occurs at other corners or supplies was **not run**.

### 1.2 Settle (`sim/postlayout/tb_trip_settle.cir`, clock static low, x1 hold capacitors)

The fields are: `vth_hard` within 1 LSB after the DAC step 254→200 / `icmp` within 1 LSB after the 10-LSB-fault
ramp / `icmp` crosses `vth_hard` (10-LSB fault) / the same for the 2.2 V fault. All values are in ns.

| Corner | r3 recorded (24 Sep, tt only) | r3 re-run | r4 |
|---|---|---|---|
| tt 1.2 V 27 °C | 104.394 / 227.245 / 156.712 / 95.529 | 104.394 / 227.245 / 156.712 / 95.529 | 104.394 / 227.246 / 156.712 / 95.529 |
| ss 1.08 V −40 °C | not run | 100.871 / 225.597 / 155.805 / 95.236 | 100.871 / 225.599 / 155.806 / 95.236 |
| ff 1.32 V 125 °C | not run | 112.923 / 229.415 / 158.347 / 96.125 | 112.921 / 229.416 / 158.347 / 96.125 |

This is expected: with the clock static, the generator only changes which clock node each comparator sees. In both,
the soft comparator is in reset and the hard comparator evaluates.

### 1.3 DAC (`sim/postlayout/tb_trip_dac_pex.cir`, tt, res_typ, 27 °C)

`run_postlayout.sh dac()` always includes `g1_trip_pex.spice`, the Sep-19 macro. So `make_step1.sh` swaps the
include to the extraction under test. Everything else is unchanged, and the metrics use the same endpoint-fit
formulas. This deck had never been run on the NF4 extraction: the postlayout README lists it as "not run for NF4".

| Metric | r3 | r4 |
|---|---|---|
| Soft DAC code 0 / 128 / 255 | 0.50037 / 0.75154 / 1.00075 V | 0.50037 / 0.75154 / 1.00075 V |
| LSB, I(VREF) at code 128 | 1.9623 mV, 41.20 µA | 1.9623 mV, 41.20 µA |
| INL / DNL (endpoint fit, 256 codes) | 0.002 LSB (code 253) / 0.002 LSB (code 255) | 0.002 LSB (code 253) / 0.002 LSB (code 255) |
| Absolute error vs 1.04·(255+code)/530 | −0.004 … −0.001 LSB | −0.004 … −0.001 LSB |
| Hard DAC, 26 codes, error | −0.0052 … −0.0039 LSB | −0.0052 … −0.0038 LSB |
| Soft settling to 1 LSB, 0→255 / 255→0 | 74.06 / 193.05 ns | 74.03 / 193.05 ns |

The Sep-19 macro, for reference (`results_postlayout.txt`): INL 0.002 and DNL 0.002 LSB, 72.8 / 190.4 ns.

## 2. Mismatch Monte Carlo of the non-overlap window

**Method.**
- `mm_netlist.py` appends `mm_ok=1` to all 1264 MOS instances of the r4 extraction: 66 LV NMOS, 50 LV PMOS, 1084 HV
  NMOS and 64 HV PMOS. It changes nothing else. The mismatch-enabled copy is
  `${BULK}/r4-20260927/blockqual/mm/g1_trip_mm.spice`, `23e7c8d2…`.
- Each seed gets a wrapper `seed<N>.spice` containing `.option seed=<N>` and `.include g1_trip_mm.spice`.
- The PDK libraries `mos_ss_mismatch` / `mos_ff_mismatch` (LV and HV) then draw per-device `delvto`, `factuo`, `w`
  and `l`. This is the same mechanism as the existing MC benches in `blocks/g1_trip/sim/qualification`, for example
  `cmp-cellpex-mc-gear-20260921-a`: `mos_tt_mismatch` and per-instance `mm_ok=1`.
- Those benches select the draw with `setseed` in `.control`. Here the draw is fixed with `.option seed` in the
  netlist, which ngspice applies before parameter evaluation.
- Controls (`evidence/blockqual/seed_check.txt`):
  - the same seed gives identical draws;
  - different seeds give different draws on LV and HV devices;
  - the mm netlist with the plain `mos_ss` library reproduces the nominal window exactly.
- The deck is `sim/win_pex.py`, unchanged: the full macro, soft 153 / hard 200, ISENSE 1.5 V, a 212 ns clock with
  0.2 ns edges, measured at the 2nd period.
- The two edges:
  - `w_fall` = soft comparator reset (`cmp_clk_s` falls) − hard evaluate (`cmp_clk_n` rises). This is the
    "soft-reset to hard-eval" edge.
  - `w_rise` = hard reset (`cmp_clk_n` falls) − soft evaluate (`cmp_clk_s` rises). This is the "hard-reset to
    soft-eval" edge.
- Seeds: 1001–1030 at ss/1.08 V/−40 °C and 2001–2030 at ff/1.32 V/125 °C.

| Corner (30 seeds each) | Edge | min | max | mean | σ | Nominal extraction | Limit | Margin to limit (min or max) |
|---|---|---|---|---|---|---|---|---|
| ss/1.08 V/−40 °C | w_fall (soft reset − hard eval) | **10.09** (seed 1014) | 10.49 | 10.32 | 0.087 | 10.31 | > 2.5 ns | 7.6 ns = 87 σ |
| ss/1.08 V/−40 °C | w_rise (hard reset − soft eval) | **8.30** (seed 1021) | 8.50 | 8.40 | 0.057 | 8.41 | > 2.5 ns | 5.8 ns = 102 σ |
| ff/1.32 V/125 °C | w_fall | 9.77 | **10.03** (seed 2030) | 9.89 | 0.064 | 9.90 | < 20 ns | 10.0 ns |
| ff/1.32 V/125 °C | w_rise | 8.50 | **8.77** (seed 2017) | 8.60 | 0.063 | 8.60 | < 20 ns | 11.2 ns |

All values are in ns. Every seed ran to completion (rc 0), both clocks swung rail to rail, and the hold excursion was
within 30 mV:
- `cmp_clk_s` min −29 mV / max 1.106 V at ss;
- `cmp_clk_n` min −18 mV / max 1.091 V at ss;
- at ff, −12 / −11 mV and 1.326 / 1.328 V.

The other edge quantities across the 60 seeds:
- evaluate latency from the pin: `ev_soft` 0.375–0.426 ns (ss), 0.203–0.222 ns (ff); `ev_hard` 0.270–0.292 ns
  (ss), 0.162–0.180 ns (ff);
- hard clock 10–90 % times: 0.58–0.63 / 0.78–0.87 ns (ss), 0.32–0.36 / 0.56–0.59 ns (ff);
- soft clock 10–90 % times: 0.27–0.29 / 0.24–0.25 ns (ss).

Per-seed values are in `evidence/blockqual/window_mc.txt`.

**Why the spread is small.** The window is set by the three long-L inverters (n 0.3/2.5 µm, p 0.6/2.5 µm):
- their `delvto` σ is about 4.5 mV (n) and 1.8 mV (p);
- a 2 nm length error is 0.08 % of 2.5 µm.

So mismatch moves the window by about 1 %. The corner, the supply and the temperature dominate it: the nominal
range across five corners is 5.26–15.11 ns (README gate 3).

## 3. Kick brackets under mismatch

**Can kick_rt.py take a seed?** Not as an argument, but its `net` field is included verbatim. Pointing it at a
seed wrapper `${BULK}/r4-20260927/blockqual/mm/seed<N>.spice`, with `mos` = `mos_tt_mismatch`, therefore runs the
unchanged bench under mismatch with a fixed seed. `kick_rt.py` itself was not modified.

**Brackets: not run.**
- One strobe-train run took 8–9 min on this host: median 512 s, range 485–560 s over 83 runs.
- A 1-LSB bracket needs about 4–6 runs, so 60 brackets are 36–54 CPU-h. That does not fit the 3 h box on 19 CPUs
  after the window MC.
- The 60 bracket jobs in `jobs.txt` were therefore disabled before they started (their `claim_000` was pre-created,
  so each exited at once).

**Run instead: a race screen at ud ±10 LSB.**
- Tool: `kick_rt.py points`, tt 1.2 V 27 °C, `mos_tt_mismatch`, hard code 200 / soft code 153, 212 ns, VDDA 3.3 V,
  res_typ.
- ud is in LSB of `icmp` below the DC threshold node (`vth_hard` or `vth_soft`) of the comparator under test. Trip
  means at least 2 of 3 strobes are high.
- The screen separates the F1 race from comparator mismatch:
  - r3 tripped the hard path 40–51 LSB early;
  - ±10 LSB is ±19.6 mV at `icmp`, 4.3 σ of the comparator offset (σ 4.55 mV, block README MC).
- Expected per seed: hard +10 n, hard −10 T, soft +10 n, soft −10 T.
- 30 seeds (3001–3030) × 4 points were queued in seed order. At the time box, new claims were stopped
  (20:17, points 85–119 pre-claimed). The last two running points (mc3019 soft +10, mc3020 hard −10) were killed at
  20:38; they were on CPUs 45/46, which foreign load held at about 28 %.

| Point | Runs | As expected | Mixed (strobes disagree) |
|---|---|---|---|
| hard 200, ud +10 (no trip expected) | 22 | 22 (n) | 0 |
| hard 200, ud −10 (trip expected) | 20 | 20 (T) | 0 |
| soft 153, ud +10 (no trip expected) | 20 | 20 (n) | 0 |
| soft 153, ud −10 (trip expected) | 21 | 21 (T) | 0 |

- 19 seeds have all four points: 3001–3018 and 3021.
- 3019, 3020 and 3022 are partial; each point that ran was as expected.
- 3023–3030: **not run**.

**What this shows.** No seed shows a hard early trip of 10 LSB or more. The r3 race was 40–51 LSB. The screen does
not measure the per-seed threshold to 1 LSB: the brackets are **not run**.

Per-seed table: `evidence/blockqual/kick_points.txt`.

## Commands

From `${REPO}`, with `BULK` set to the external artifact root:

```
S=designs/g1-guardian/blocks/g1_trip/layout/candidates/nf4_novclk/sim/blockqual
python3 $S/mm_netlist.py designs/g1-guardian/blocks/g1_trip/sim/postlayout/g1_trip_nf4_novclk_pex.spice \
    ${BULK}/r4-20260927/blockqual/mm $(seq 1001 1030) $(seq 2001 2030) $(seq 3001 3030)
bash $S/make_step1.sh ${BULK}/r4-20260927/blockqual/step1      # 12 decks: r4 and r3; cmp tt/ss, settle tt/ss/ff, dac tt
(cd $S && BULK=${BULK} bash make_jobs.sh)                      # ${BULK}/r4-20260927/blockqual/jobs.txt (135 jobs)
(cd $S && BULK=${BULK} python3 dispatch.py ${BULK}/r4-20260927/blockqual/jobs.txt 45-63 ${BULK}/r4-20260927/blockqual/state)
python3 $S/analyze.py ${BULK}/r4-20260927/blockqual
```

Each step-1 and window job is:

```
G1_CPUSET=<cpu> G1_CPUS=1 G1_CONTAINER_ENGINE=podman G1_RESULTS_ROOT=${BULK} \
G1_WORKDIR=designs/g1-guardian/blocks/g1_trip/sim flow/run.sh \
sh -c 'ngspice -b <deck> 2> <deck>.err | grep -av "Reference value" > <deck>.log'
```

Kick screen, from `${REPO}`. The queue has 120 lines of the form
`mc<N> ${BULK}/r4-20260927/blockqual/mm/seed<N>.spice mos_tt_mismatch 1.2 27 <hard|soft> 200 153 212 3.3 res_typ <10|-10>`,
for N = 3001–3030. One worker ran per free CPU in 45–63:

```
O=${BULK}/r4-20260927/blockqual/kickpts
BULK=${BULK} python3 designs/g1-guardian/review/redteam-20260927/trip_path/kick_rt.py points <cpu> $O $O/q
```

The command for the tt 1 mV diagnostic is in `evidence/blockqual/cmp_1mV_diag.txt`.

## Wall times (loaded host; one ngspice per CPU)

| Job | Wall time |
|---|---|
| Comparator delay deck (3 overdrives, one corner), r3 / r4 | 17–20 min each (1034–1180 s) |
| Settle deck, per corner | 21–23 min (1240–1401 s) |
| DAC deck (256 + 26 op, 4.1 µs tran) | 56 min (r3), 62 min (r4) |
| Window deck, per seed | median 21.7 min, range 19.9–63 min (the 63 min run shared its CPU with foreign load) |
| Kick point (880 ns strobe train) | median 8.5 min, range 8.1–9.3 min |
| Whole campaign | 18:03–20:38, CPUs 45–63 |

Per-job records: `evidence/blockqual/jobs_walltime.jsonl`. The 60 `kick_s*` entries there are the disabled
bracket jobs, which exited immediately.

## Files and hashes

| File | SHA-256 |
|---|---|
| `sim/postlayout/g1_trip_nf4_novclk_pex.spice` (r4, under test) | `6f518e0758a87b334ab5ae98a8ad43d79dd03ab4ba52c241f742280b6d2f770b` |
| `sim/postlayout/g1_trip_nf4_pex.spice` (r3, reference) | `ba86b7b2a530abae365d539297909e033b24a54597f9cc75d8dff273c30d401c` |
| `${BULK}/r4-20260927/blockqual/mm/g1_trip_mm.spice` (mm_ok=1 copy of r4, 0.68 MB, bulk only) | `23e7c8d24cd5102d652d6934923fe20d79c715da2f35136e22ec634f849096e7` |
| `sim/postlayout/tb_trip_cmp_pex.cir` | `055b7123ccabf943091f2d724c26e172ecb8058a4603dcf8d8e71596bc14bb6f` |
| `sim/postlayout/tb_trip_settle.cir` | `f79202323c0a02ffdfb7b85fc30766f60b873c4654a6d4935c40e1a285dda3fc` |
| `sim/postlayout/tb_trip_dac_pex.cir` | `46621d30d76a0d37aa01fc3ef0dbd6591542f158673232ab791ed5940c7900a2` |
| `sim/postlayout/run_postlayout.sh` (substitutions copied, not run) | `d15b55c42bd0eef6d78495e254d7a25b48e1049aa1095a1567cdbf7c811f86c7` |
| `layout/candidates/nf4_novclk/sim/win_pex.py` | `db961e5065a0acd126b406a4807da72967dfc3d2939bdf8f55992b786a6b0116` |
| `review/redteam-20260927/trip_path/kick_rt.py` / `tb_kick_rt.cir.tmpl` | `0690d3e2…6e16` / `9d7abd2b…063e` |
| `sim/blockqual/mm_netlist.py` / `make_step1.sh` / `make_jobs.sh` / `dispatch.py` / `analyze.py` | `cba9edeb…7d798c80` / `efcf2fb9…77489b50` / `0c321e96…eb783607` / `e9fc7ffd…cdd41667` / `aa149da3…2ef21dd0` |

Bulk outputs, none committed: the decks, logs and `.dat` waveforms under `${BULK}/r4-20260927/blockqual/`, in
`step1/`, `win/<corner>_s<seed>/`, `kick*/`, `diag/`, `seedtest/` and `state/jobs.jsonl`. The committed evidence
is the small text extracts in `evidence/blockqual/`, each under 300 kB.

## Not run

- Mismatch of resistors (`rppd`/`rhigh` DAC strings) and MIM capacitors. Only MOS mismatch was drawn.
- Window MC at tt, at ff/−40 °C (the shortest nominal window, 6.40 / 5.26 ns) and at ss/125 °C (the longest,
  15.11 / 13.07 ns). The window's MC σ at the two corners run is about 1 % of the mean. Applying it to the nominal
  corners does not bring either corner near a limit, but that is an extrapolation, not a run.
- Global (process) variation combined with mismatch (`mos_*_stat`).
- The comparator delay deck under mismatch, and at ff.
- Kick **brackets** under mismatch (1-LSB threshold per seed): not run (time box). The ±10 LSB screen ran on 19 complete seeds; seeds 3023–3030 were not run, and 3019, 3020 and 3022 are partial.
- Chip-level re-runs with this extraction are done by another agent, not here. Measurement: not run (no silicon).

# S5 — clock for R1: 30 MHz oscillator options (2026-10-20)

Study by an agent (Opus 5.5); nothing simulated. "estimated" = calculation in this study. G1 block files under
`designs/g1-guardian/blocks/g1_osc/` (written `g1_osc/`).

## G1 oscillator record (R0.95)

| Item | Value | Source |
| --- | --- | --- |
| Topology | 1.2 V ping-pong RC relaxation: two `cmim` banks charged through `rppd`, two 5-T comparators against a vdd/2 divider, SR latch, 50 % duty | `g1_osc/README.md` |
| Nominal | 9.436 MHz at trim 8, tt/1.2 V/27 °C with clock-tree load (simulated) | `g1_osc/sim/qualification/fulltree_r095_load_20260924/README.md` |
| Trim | 4-bit C trim, 1.50 pF + 100 fF × code; tt code 0 13.55 MHz, code 15 7.53 MHz (simulated, CPEX) | `g1_osc/reports/r095_newpex_pvt_20260924/README.md` |
| Code-8 corners | ss/1.08 V/125 °C 7.30 MHz; ff/1.32 V/−40 °C 12.24 MHz: −22.7 % / +29.7 % (simulated) | `g1_osc/sim/qualification/osc_r095_newpex_pvt80_exact_audit_20260924_r1.json` |
| Trim reach | ss/1.08 V/125 °C reaches 10.45 MHz at code 0 | same |
| Supply | +4 % over 1.08–1.32 V (≈ 17 %/V), post-layout | `g1_osc/README.md` |
| Temperature (tt) | 9.992 → 9.814 MHz over −40…125 °C (−1.8 %, schematic) | `g1_osc/README.md` |
| Delay | ≈ 4 ns extra per half period after layout; layout costs 9–13 % of frequency | `g1_osc/README.md` |
| Jitter, mismatch MC | not run | `g1_osc/README.md` |
| Area, current | 0.0228 mm²; 107 µA tt, 110 µA post-layout (simulated) | S3; `g1_osc/README.md` |

## Options for 25–32 MHz

| Option | Change | Spread at default code (estimated) | Risk |
| --- | --- | --- | --- |
| (a) Re-tuned G1 RC | half period 16.7 ns = RC·ln 2 + t_d; C ≈ 1.15 pF mid code (0.75 pF fixed + 5-bit trim, 25 fF LSB); R ≈ 17 kΩ (rppd 1 µm × ≈ 65 µm); comparator tail 20 → ≈ 60 µA so t_d ≤ 3–4 ns | t_d 20–30 % of the period adds ≈ ±6 % MOS-corner term: ≈ −30 % / +40 % | low: generator, decks, layout flow exist |
| (b) Current-starved std-cell ring | 7–11 stages, constant-gm bias, 5-bit current trim | ±40–50 % untrimmed; supply ≈ 80–100 %/V; ±10 % drift after trim | medium: supply-coupled FM |
| (c) Ring PLL from a 10 MHz RC reference, M = 3 | IHP `30_MHz_Fractional_N_PLL` (TO_July2025: 10 MHz ref, 11-stage starved ring VCO ≈ 50 MHz, 304 µW, blocks ≈ 3 640 µm²) reports post-layout 27.71 MHz at M = 3 and 8.03 MHz at M = 1, which suggests no lock; no corner or jitter data; "Measurement results await" (https://github.com/IHP-GmbH/TO_July2025/tree/main/30_MHz_Fractional_N_PLL) | copies the reference spread | high |
| (d) Keep ≈ 10 MHz | CORDIC 2 iterations/clock (+0.5–1 kGE, 0.9 µs); shared SAR ≈ 0.6 MSPS → ≈ 0.3 M pairs/s | count-safe falls from 250 kHz to ≈ 75 kHz | low analog risk, fails the S1 target |

## Jitter budget

σ_φ = 2π·f·σ_j: 0.05° el at 100 kHz allows 1.39 ns rms; staying below 12-bit angle quantisation (1.76e-4 rad) allows
0.28 ns (estimated). Both track-and-holds share one edge, so jitter moves the angle, not the sin/cos skew; the relevant
accumulation is sample-to-latch, ≤ ≈ 1 µs (≈ 30 cycles).

| Source | Period jitter | Over ≈ 1 µs (×√30) |
| --- | --- | --- |
| Relaxation, literature best (10.5 MHz 9.86 ps; 8.2 MHz 7.66 ps) | — | — |
| (a) G1-class comparator, 0.05–0.1 % of 33 ns | 17–33 ps (estimated) | 90–180 ps |
| (b) Ring at 100 µW (Abidi floor 3.2 ps × 3–10) | 10–30 ps (estimated) | 55–170 ps |

Sources: swing-boosted relaxation oscillator (https://dgist.elsevierpure.com/en/publications/an-ultra-low-noise-swing-boosted-differential-relaxation-oscillat/),
Abidi JSSC 41(8) 2006 doi 10.1109/JSSC.2006.876206, Hajimiri JSSC 34(6) 1999 doi 10.1109/4.766813.
Random jitter is ≥ 8× inside the budget for every option. The larger term is supply-coupled frequency modulation: 10 mV
ripple ≈ 0.17 % for (a), ≈ 0.8 % for (b); over 1 µs of extrapolation ≈ 1.7 ns (0.06° el) and ≈ 8 ns (0.29° el). If
velocity is measured in radians per oscillator tick and extrapolated in ticks, the static frequency error cancels.

## BiSS timeout and SSI monoflop from the main clock (600 ticks at 30 MHz)

| Case | f spread | Timeout | Inside 12.5–40 µs |
| --- | --- | --- | --- |
| G1 code 8 (CPEX) | −22.7 / +29.7 % | 15.4–25.9 µs | yes |
| (a) untrimmed (estimated) | −30 / +40 % | 14.3–28.6 µs | yes |
| (b) untrimmed (estimated) | −45 / +50 % | 13.3–36 µs | yes, small margin |

The SSI monoflop (15–25 µs) fails untrimmed for (a) and (b); the digital block must close STA at the fastest untrimmed
frequency (≈ 42 MHz for (a)) or use a slow-side reset code. Trim scheme: the chip counts oscillator ticks over 16 MA (or
SCLK) periods into `OSC_COUNT`; the host knows the MA frequency, computes f_osc, writes `OSC_TRIM` (5 bit) and
`TIMEOUT_TICKS`; at 1 MHz MA the count is ≈ 480 ticks (≈ 0.2 % resolution); out-of-window sets the clock-fault STATUS
bit; repeating the count tracks drift.

## Recommendation: option (a)

G1-lineage relaxation oscillator, 30 MHz nominal, 5-bit trim, MA-referenced trim count. Area ≈ 0.015–0.02 mm²;
current ≈ 250–400 µA at 1.2 V (2–4× the S3 entry). Fallback (b) if area is short; (c) not until the IHP PLL has lock and
corner data.

First decks (from `g1_osc/sim/tb_osc.cir` and `run_osc.sh`): `tb_osc30.cir` full PVT × trim (monotonic trim, step ≤ 2 %,
32 MHz reachable at ss/1.08 V/125 °C); `tb_osc30_cmpnoise.cir` comparator noise PSD; `tb_osc30_jitter.cir` `trnoise`
2000 periods, period and 30-cycle jitter; `tb_osc30_psrr.cir` 10 mV step and 20 kHz / 1 MHz ripple; `tb_osc30_mc.cir`
100-sample mismatch MC; `tb_osc30_startup.cir`; RTL `tb_clkcal` for `OSC_COUNT`, `TIMEOUT_TICKS`, SSI monoflop with MA
80 kHz–10 MHz at both spread limits.

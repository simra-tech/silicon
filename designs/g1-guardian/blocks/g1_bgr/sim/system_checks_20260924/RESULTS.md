# G1_BGR system check, 2026-09-24: VREF driving the VREF pad

**The bandgap on the chip is `bgr_loop24_qref4_r253p465_hv06` (SHA-256 586ffb58…, 301 HBTs). Its results
are in the section "Chip BGR (586)" at the end.** The first sections cover the Sep-19 `g1_bgr_pex.spice`,
which is not the placed bandgap. Keep them only for comparison.

All numbers are **simulated** (ngspice 46, pinned image
`sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2`, IHP SG13G2 PDK
`84374023ee8b4b126bebbba67fcbada0a9c0ff0b`). No model card, rule deck, netlist or layout changed.

## Fixture

`bgr_sys.py` writes `decks/`. Each deck is built like `../tb_g1_bgr.spice.tmpl`: the same `.lib` sections,
`.option gmin=1e-15 abstol=1e-14 reltol=1e-5 vntol=1e-7`, the post-layout kpex CC netlist
`../postlayout/g1_bgr_pex.spice`, `Vload iptat 0 1.0`, and `../.spiceinit` copied. The following was added:

- the stock `sg13g2_IOPadAnalog` (`padres` on the core side, `pad` on the pin, vdd = 1.2 V, iovdd = 3.3 V).
  Its LV MOS, diode and cap models use the matching corner sections (`cap_typ`).
- `Rroute` 613.34 Ω from vref to padres. This is the whole-tree estimate from
  `review/audits/VREF_PAD_LOADING_20260922.md`, not an extraction.
- an internal load of **100 kΩ in series with 2 pF**, which replaces the testbench's 1 pF. A 100 kΩ DC
  shunt instead would pull VREF to 0.413 V. That case is shown in `startup_10nF_tt27_shunt100k`, so the
  series reading is the one used here.
- the board capacitor on the pin: 0, 10 nF or 100 nF, each with 1 Ω ESR.

Corners: tt27 (hbt_typ/mos_tt/res_typ/dio_tt, 27 °C), ss125 (hbt_wcs/mos_ss/res_wcs/dio_ss, 125 °C) and
ff-40 (hbt_bcs/mos_ff/res_bcs/dio_ff, −40 °C). The settling reference is each deck's own `.op` at full
supply.

- Startup: both rails ramp from 0 to 3.3 V and 0 to 1.2 V in 10 µs with `uic`.
- vstep: a 10 mV step with 1 µs rise, in series with the board C, at 100 µs (50 µs for 0 nF). With the
  pad open (0 nF) the step goes through a 10 pF probe coupling cap instead.
- istep: a 10 nA step into the pin.

```sh
cd designs/g1-guardian/blocks/g1_bgr/sim/system_checks_20260924
python3 bgr_sys.py gen && python3 bgr_sys.py run --cpus 50-57   # host; each deck via flow/run.sh, 1 pinned CPU
python3 bgr_sys.py diag <cpu,...> [name-filter]                  # stall diagnostics (DIAG list in the script)
python3 bgr_sys.py analyze                                        # -> summary.json
```

Waveforms are in `${BULK}/blockchecks-20260924/bgr/*.dat`. Logs are in `logs/`.

## (1) Startup, VREF settling time to within 1 % (and 0.1 %) of the DC value, measured from the ramp start

| corner | 0 nF (pad open) | 10 nF | 100 nF |
|---|---|---|---|
| tt27 | **not converged** with the stock pad (trap and gear) | 4.85 ms (6.90 ms) | 48.5 ms (69.0 ms) |
| ss125 | **not converged** with the stock pad | **not converged** with the stock pad | **not converged** with the stock pad |
| ff-40 | 10.0 µs (10.7 µs) | 4.66 ms (6.44 ms) | 46.5 ms (64.3 ms) |

The DC values of VREF are 1.03929 V (tt27), 1.04039 V (ss125) and 1.03744 V (ff-40).

**Stalls.**
- tt27 and ss125 at 0 nF stop at t ≈ 2.93 µs. The supply is at about 0.97 V there and pad ≈ 0.07 V.
- ss125 with 10 nF stops at 214 µs and with 100 nF at 2.10 ms. In both, VREF and pad are at ≈ 0.10 V
  while VREF is still slewing up. The ramp is linear at about 4.8 µA / C.
- Trap stalled with no progress and was killed. Gear aborted at tt27/0 nF with "timestep too small, node
  vload#branch" and stalled in the other three cases.
- These variants **stall at the same point**: gear with reltol 1e-4, rshunt 1e12, KLU, gear maxord 2, and a
  0→1 V ramped IPTAT termination.

**Which part of the pad causes it.** The cell was split into parts, with instances copied verbatim and the
PDK file untouched:

| variant | result |
|---|---|
| no pad | completes |
| primary clamps and diodes only | completes |
| secondary-protection rppd only | completes |
| **secondary-protection `dantenna`/`dpantenna` only** | **stalls** |

At the stall these two diodes are reverse-biased by only about 0.1 V and about 3.2 V. The stall is
therefore **numerical, in the PDK antenna-diode model inside `sg13g2_SecondaryProtection`**. It is not an
established circuit behaviour, and it does not establish that the silicon starts. It matches the 125 °C
timeout in `review/audits/VREF_PAD_DYNAMIC_20260922.md`.

**Without the pad, for the stalled cases only** (`diag_*_nopad`), 1 % (0.1 %) settling is:

| case | settling |
|---|---|
| tt27 / 0 nF | 7.8 µs (10.7 µs) |
| ss125 / 0 nF | 9.6 µs (10.8 µs) |
| ss125 / 10 nF | 5.15 ms (7.50 ms) |
| ss125 / 100 nF | 51.5 ms (75.0 ms) |

The rppd-only variant gives the same numbers. The primary-only variant gives the same numbers at ss125 /
10 nF, and 10.0 µs (10.8 µs) at tt27 / 0 nF.

**Oscillation and ringing.** None in any completed startup:
- **With 10 or 100 nF:** VREF approaches its DC value from below and never exceeds it.
- **With the pad open (0 nF):** VREF overshoots by 18.9–22.4 mV (1.8–2.2 %) at about 6.8 µs, while the
  supply is still ramping. It then decays monotonically, with no sign change of the error after the peak.
- **Tail of the window:** in the last 20 % of each window the peak-to-peak is at most 12.8 µV (10 nF). At
  100 nF it is 126–547 µV, which is the exponential tail, with one sign change of the detrended residual.

## (2)+(3) Small-signal recovery with the loop settled (all nine corner × C cases completed with the stock pad)

| corner | Rout = ΔV/10 nA | 0 nF: vstep peak, 1/e, 1 % | 10 nF: τ(1/e), 1 % | 100 nF: τ(1/e), 1 % |
|---|---|---|---|---|
| tt27 | 87.8 kΩ | 5.31 mV, 1.05 µs, 5.1 µs | 0.890 ms, 4.10 ms | 8.89 ms, 41.0 ms |
| ss125 | 101.4 kΩ | 5.61 mV, 1.22 µs, 5.9 µs | 1.027 ms, 4.73 ms | 10.27 ms, 47.3 ms |
| ff-40 | 76.1 kΩ | 4.99 mV, 0.91 µs, 4.4 µs | 0.772 ms, 3.56 ms | 7.71 ms, 35.5 ms |

- **Pin excursion.** With 10 or 100 nF the pin moves 9.99 mV, and core VREF 9.84–9.87 mV.
- **No ringing anywhere.** In all 18 step runs the residual never crosses the baseline or final value after
  the peak by more than 0.1 % of the peak (vstep) or 1 % of the final value (istep). There is no undershoot
  or overshoot, so no ringing frequency exists.
- **Single-pole recovery.** τ = Rout·C to within 1.3 %, for example 87.8 kΩ × 10 nF = 0.878 ms against
  0.890 ms simulated. At 0 nF, τ ≈ 1 µs corresponds to about 12 pF on VREF: the 10 pF probe, the 2 pF
  load and the pad.
- **Time resolution.** The maximum step was 5 ns at 0 nF, 200 ns at 10 nF and 1 µs at 100 nF. A mode
  faster than that would not be resolved.

## Status

| Check | Status |
|---|---|
| Startup with stock pad, tt27 10/100 nF and ff-40 0/10/100 nF | passed (completed, no oscillation); no acceptance limit on settling time adopted |
| Startup with stock pad, tt27 0 nF and ss125 0/10/100 nF | **failed to converge** (simulator stall in the PDK secondary-protection antenna diodes; trap, gear and four option variants tried) |
| Same cases without the pad / without the secondary-protection diodes | passed (completed, no oscillation); substitutes, not the chip |
| Small-signal step recovery, 3 corners × 0/10/100 nF, stock pad | passed: single-pole, no ringing or undershoot |
| Pole-zero / loop-gain stability of the BGR | not run (unchanged; this is time-domain evidence only) |
| Real SENSE/TRIP/T2F loads, extracted VREF route, package ESL/leakage, mismatch | not run. The T2F comparator bases draw about 21 nA (tt27) to 72 nA (ss125) from VREF, see `../../../g1_t2f/sim/system_checks_20260924/RESULTS.md` |

## Chip BGR (586): `bgr_loop24_qref4_r253p465_hv06`

**Netlist.** `../qualification/candidates/bgr_loop24_qref4_r253p465_hv06/bgr_loop24_qref4_r253p465_hv06.spice`,
SHA-256 `586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b` (336 MOS, 301 HBT, 399 R).
It carries the 329 model-level capacitors inherited from the older extraction. It is **not a native
capacitance extraction of the placed layout**, which does not exist yet.

**Fixture.** The fixture, corners and tests are identical to the sections above: stock pad, 613 Ω route,
100 kΩ + 2 pF series internal load, 1 Ω ESR. Every startup was also run with the pad-less stand-in
(`startupnopad_*`).

**Watchdog.** `run_one` kills ngspice if the simulated time does not advance for 300 s.

```sh
cd designs/g1-guardian/blocks/g1_bgr/sim/system_checks_20260924
BGR586=1 python3 bgr_sys.py gen && BGR586=1 python3 bgr_sys.py run --cpus 50-57
BGR586=1 python3 bgr_sys.py vreftemp 50,51,53 && BGR586=1 python3 bgr_sys.py analyze   # -> bgr586/summary.json
```

Decks are in `bgr586/decks`, logs in `bgr586/logs`, and waveforms in
`${BULK}/blockchecks-20260924/bgr586/`.

### VREF value (stock pad, pin open, internal load, 3.3 V; `.op`)

| process | −40 °C | 27 °C | 125 °C |
|---|---|---|---|
| typ (hbt_typ/mos_tt/res_typ) | 1.04403 V | 1.04546 V | 1.04410 V |
| slow (hbt_wcs/mos_ss/res_wcs) | 1.04732 V | 1.04934 V | 1.04859 V |
| fast (hbt_bcs/mos_ff/res_bcs) | 1.04217 V | 1.04328 V | 1.04177 V |

- **Pin versus core.** The pin equals core VREF to within 5 µV (typ at 125 °C, pad leakage).
- **T2F comparator load not included.** The T2F comparator bases add about 21–72 nA of DC load (T2F
  RESULTS). With this bandgap's 19–26 kΩ output resistance that lowers VREF by about 0.5–1.9 mV.
- **100 kΩ DC shunt.** Used instead of the series load, it gives 0.850 V (tt27).

### Startup: time to within 1 % (0.1 %) of the DC value, from the ramp start

| corner | 0 nF | 10 nF | 100 nF |
|---|---|---|---|
| tt27 stock pad | **not converged** (trap and gear, timestep too small at 3.62 µs) | 1.26 ms (1.80 ms) | 12.5 ms (17.9 ms) |
| tt27 no pad | 7.2 µs (10.1 µs) | 1.24 ms (1.77 ms) | 12.4 ms (17.7 ms) |
| ss125 stock pad | **not converged** (4.05 µs) | **not converged** (52.6 µs) | **not converged** (480 µs) |
| ss125 no pad | 7.6 µs (10.2 µs) | 1.32 ms (1.93 ms) | 13.2 ms (19.3 ms) |
| ff-40 stock pad | 7.0 µs (10.1 µs) | 1.20 ms (1.67 ms) | 12.0 ms (16.7 ms) |
| ff-40 no pad | 7.0 µs (10.1 µs) | 1.19 ms (1.65 ms) | 11.8 ms (16.4 ms) |

**Stalls.** The stock pad stalls in the same cases as with the Sep-19 bandgap: trap and gear both abort
with "timestep too small" on `vload#branch` or `vr4#branch`. The component split into parts of the pad
cell was **not repeated** on this netlist. The attribution to the pad's secondary-protection diodes is
carried over from the Sep-19 split and is **unconfirmed for 586**. The pad-less stand-in completes every
case.

**Where the stock pad converges, it agrees with the stand-in** to within 1.5 %.

**Ringing.** None.
- **0 nF:** VREF overshoots 13.9–17.3 mV (1.3–1.7 %) while the supply is still ramping (about 7 µs),
  then decays monotonically.
- **10 and 100 nF:** VREF never exceeds the DC value by more than 2 nV.
- **Last 20 % of each window:** peak-to-peak is at most 1.5 nV, with no sign changes.

### Small-signal recovery (stock pad, all 18 cases completed)

| corner | Rout (10 nA step) | 0 nF: 10 mV step via 10 pF: peak, τ, 1 % | 10 nF: τ, 1 % | 100 nF: τ, 1 % |
|---|---|---|---|---|
| tt27 | 22.3 kΩ | 2.14 mV, 0.27 µs, 1.47 µs | 235 µs, 1.08 ms | 2.35 ms, 10.8 ms |
| ss125 | 25.8 kΩ | 2.43 mV, 0.31 µs, 1.66 µs | 271 µs, 1.25 ms | 2.71 ms, 12.5 ms |
| ff-40 | 19.3 kΩ | 1.88 mV, 0.23 µs, 1.30 µs | 205 µs, 0.94 ms | 2.05 ms, 9.43 ms |

- **No ringing.** There is no undershoot beyond 0.3 µV and no crossing of the baseline after the peak.
- **Single pole.** τ is 5–6 % above Rout·C.
- **Output resistance.** About 4× lower than the Sep-19 netlist's 76–101 kΩ.

### Wall time (1 CPU, pinned, shared host)

**One startup of the 586 netlist takes 301 s** (tt27, 10 nF, 15 ms simulated) and 280–670 s across the
other completed startups. Two pad-less ss125 startups took 2000–2140 s. For comparison, the Sep-19 netlist
took 32–66 s per deck, and a 586 `.op` at three temperatures takes 20 s.

| Check (586) | Status |
|---|---|
| VREF at −40/27/125 °C, 3 process corners, with pad | passed (completed) |
| Startup with stock pad, tt27 10/100 nF and ff-40 all | passed (completed, no oscillation) |
| Startup with stock pad, tt27 0 nF and ss125 all | **failed to converge** (trap and gear); pad-less stand-in passed |
| Pad component attribution on 586 | not run (carried over from Sep-19) |
| Step recovery, 3 corners × 0/10/100 nF | passed: single pole, no ringing |
| Native capacitance extraction of the placed 586 layout, loop-gain/pole-zero, real downstream loads | not run |

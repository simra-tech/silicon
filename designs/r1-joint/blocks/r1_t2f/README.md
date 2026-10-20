# r1_t2f - temperature-to-frequency converter (G1 T2F revision 2, reused unchanged)

State (2026-10-20): reused. The G1 schematic is copied without change. The G1 nominal, supply and corner
decks were re-run at the R1 supplies (VDDA 3.0, 3.3, 3.6 V). The G1 numbers carry over. Every number below is
simulated. Nothing is measured. Layout, DRC, LVS and PEX of the macro are the G1 ones and were not repeated here.

## What it is

The G1 block `g1_t2f` revision 2 is a relaxation oscillator. Its frequency is proportional to absolute temperature
(PTAT mode, f = I_PTAT / (2 C V_REF)). In REF mode the frequency is nearly constant (f = 1 / (4 R_REF C)).
The ratio f_PTAT / f_REF does not depend on C, the threshold or the comparator delay to first order.
The block takes the rails `pbias`, `pcasc` and `vref` from the bandgap.
Pins: `vdd vdd12 vss pbias pcasc vref en mode fout`. Control bits: see `schematic/G1_INTERFACE.md` (copy of the G1 file).

- Source: `designs/g1-guardian/blocks/g1_t2f/xschem/g1_t2f.spice` (G1 path in the repository).
- Copy: `schematic/g1_t2f_rev2.spice`, sha256 `8011b76104e9faa4a29dae4323ce59fb6f5864373a087df0767a61672a7b4391`
  (equal to the G1 file at the time of the copy).
- Bias source in the decks: the Sep-19 G1 bandgap netlist `designs/g1-guardian/blocks/g1_bgr/xschem/g1_bgr.spice`,
  copied to `sim/g1_bgr_sep19.spice`, sha256 `fa92550727c36fc47419001799cf399f58f18ecf5414a47323a706fc8edc9701`.
  This is the same bandgap as in the G1 T2F decks. It is not the G1 chip-of-record bandgap (BGR586) and not `r1_bgr`.
- Area: the G1 macro is 92 x 102.6 um (GDS and LEF in the G1 block directory; not copied here).
- Current from the sims (T2F plus the Sep-19 bandgap, 3.3 V rail, PTAT mode): see the f(T) and supply tables.
  The 1.2 V rail (`vdd12`, output level shifter only) takes 0.13 to 0.24 uA.

## Built against

| Item | Value | Established by |
| --- | --- | --- |
| PDK | IHP SG13G2 open PDK, commit `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` | `flow/run.sh cat /foss/pdks/ihp-sg13g2/COMMIT`, 2026-10-20 |
| ngspice | 46 (compiled with KLU) | `flow/run.sh ngspice -v`, 2026-10-20 |
| Container image | `tapeoutbench-eda:latest`, id `sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2` | pinned in `flow/run.sh`, checked on every call |
| Run settings | one CPU (`G1_CPUSET=118`), `num_threads=1` in `sim/.spiceinit` | `sim/runs/*.json` |
| Deck options | `gmin=1e-15 abstol=1e-13 reltol=1e-4 vntol=1e-6 method=gear`, `tran 5n`, period averaged over cycles 8 to 24 | `sim/r1_run_t2f.py` (same as the G1 runner) |
| xschem, KLayout, LibreLane, CACE | not used in this block (netlist reused as is) | not applicable |

Bulk logs: `<G1_RESULTS_ROOT>/r1_t2f/20261020-a` and `<G1_RESULTS_ROOT>/r1_t2f/20261020-b`.

## Status

| Check | Status | Evidence |
| --- | --- | --- |
| f(T) PTAT, 3.3 V, tt, 8 temperatures -40..125 C | passed (oscillates, matches G1) | `sim/results/ftemp_20261020-a.json`, `sim/runs/run_20261020-a_ftemp.json` |
| f(T) REF, 3.3 V, tt, -40/27/125 C | passed | same |
| f(T) REF at the other 5 temperatures | not run | - |
| Supply 3.0/3.3/3.6 V, PTAT, 27 and 125 C | passed | `sim/results/supply_20261020-a.json` |
| Supply 3.0/3.3/3.6 V, REF, 27 C | passed | same |
| Supply, REF, 125 C | not run | - |
| Corners ss/tt/ff x 3.0/3.6 V x -40/27/125 C, PTAT (18 decks) | 15 passed first time; 3 failed first time (VBIC NaN at -40 C, 3.6 V); all 3 passed on retry with tight options | `sim/results/corners_20261020-a.json`, `sim/results/tight_20261020-b.json` |
| Corners in REF mode | not run | - |
| Corners with separate hbt/mos/res/cap combinations, cap corners | not run (G1 ran 9 combinations at 3.3 V, 27 C) | G1 README |
| 3.3 V corner decks, 85 C, 150/175 C | not run | - |
| Re-run with `r1_bgr` (the R1 bandgap) | not run (pending) | open item 1 |
| Layout, DRC, LVS, antenna, PEX of the macro | not run here (G1 results apply to the copied G1 macro only) | G1 `g1_t2f/reports` |
| Monte Carlo, V_CE check, start-up with the R1 supplies | not run | - |
| Measurement | not run | - |

## Results (all simulated)

### f(T), 3.3 V, tt (simulated)

| T [C] | f PTAT [MHz] | f REF [MHz] | f_PTAT/f_REF | I(3.3 V) [uA] | I(1.2 V) [uA] | V_REF [V] | fit residual [C] |
| --- | --- | --- | --- | --- | --- | --- | --- |
| -40 | 1.2463 | 1.5827 | 0.7875 | 49.0 | 0.13 | 1.0373 | -0.33 |
| -25 | 1.3260 | not run | not run | 52.0 | 0.14 | 1.0373 | -0.12 |
| 0 | 1.4582 | not run | not run | 57.0 | 0.16 | 1.0369 | +0.13 |
| 27 | 1.6003 | 1.5978 | 1.0015 | 62.5 | 0.17 | 1.0360 | +0.26 |
| 50 | 1.7209 | not run | not run | 67.1 | 0.19 | 1.0350 | +0.29 |
| 75 | 1.8513 | not run | not run | 72.2 | 0.20 | 1.0335 | +0.20 |
| 100 | 1.9810 | not run | not run | 77.2 | 0.22 | 1.0318 | -0.03 |
| 125 | 2.1100 | 1.5793 | 1.3360 | 82.3 | 0.24 | 1.0299 | -0.40 |

Least-squares slope over -40..125 C: 5.237 kHz/C; local slope 5.157 .. 5.309 kHz/C; fit residual of one straight line -0.40 .. +0.29 C.

### Supply sensitivity (simulated)

| mode | T [C] | f at 3.0 V [MHz] | 3.3 V | 3.6 V | sensitivity [ppm/V] | [kHz/V] | [C/V] | I(VDDA) 3.0/3.3/3.6 V [uA] |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PTAT | 27 | 1.6043 | 1.6003 | 1.5962 | -8394 | -13.43 | -2.57 | 61.8 / 62.5 / 63.3 |
| PTAT | 125 | 2.1147 | 2.1100 | 2.1046 | -7983 | -16.84 | -3.22 | 81.6 / 82.3 / 83.1 |
| REF | 27 | 1.6018 | 1.5978 | 1.5939 | -8275 | -13.22 | -2.52 | 61.8 / 62.5 / 63.3 |

[C/V] divides the frequency change per volt by the simulated PTAT slope (LS, kHz/C above).

### Process corners at 3.0 and 3.6 V, PTAT (simulated; ss = hbt_wcs+mos_ss+res_wcs, ff = hbt_bcs+mos_ff+res_bcs)

| corner | VDDA [V] | f(-40 C) [MHz] | f(27 C) | f(125 C) | slope -40..125 C [kHz/C] | note |
| --- | --- | --- | --- | --- | --- | --- |
| ss | 3.0 | 1.0991 | 1.4098 | 1.8571 | 4.594 |  |
| ss | 3.6 | 1.0936 | 1.4027 | 1.8479 | 4.572 | -40 C point: tight options (retry) |
| tt | 3.0 | 1.2495 | 1.6043 | 2.1147 | 5.243 |  |
| tt | 3.6 | 1.2431 | 1.5962 | 2.1046 | 5.221 | -40 C point: tight options (retry) |
| ff | 3.0 | 1.4308 | 1.8379 | 2.4236 | 6.017 |  |
| ff | 3.6 | 1.4234 | 1.8289 | 2.4123 | 5.993 | -40 C point: tight options (retry) |


## Comparison with the G1 numbers

The G1 numbers are in `designs/g1-guardian/blocks/g1_t2f/README.md` and `sim/results/tables.md` (Sep-19 bandgap, 3.3 V).

| Quantity | G1 (simulated) | R1 re-run (simulated) | Verdict |
| --- | --- | --- | --- |
| f PTAT at 27 C, 3.3 V | 1.6003 MHz | 1.6003 MHz | same |
| f PTAT at -40 / 125 C | 1.2463 / 2.1100 MHz | 1.2463 / 2.1100 MHz | same |
| Slope, 25/100 C line (R1: 27/100 C points) | 5.217 kHz/C | 5.215 kHz/C | same |
| f REF at -40 / 27 / 125 C | 1.5827 / 1.5978 / 1.5793 MHz | 1.5827 / 1.5978 / 1.5793 MHz | same |
| Supply sensitivity PTAT, 3.0 to 3.6 V, 27 C | -8394 ppm/V (-2.52 C/V) | -8394 ppm/V (-2.57 C/V with the LS slope) | same in ppm/V |
| Supply sensitivity REF, 27 C | -8275 ppm/V | -8275 ppm/V | same |
| Current from 3.3 V, 27 C, PTAT, with bandgap | 62.5 uA | 62.5 uA | same |
| Corner spread at 27 C, ss / ff against tt | -12.2 % / +14.7 % (3.3 V) | -12.1 % / +14.6 % (3.0 V); -12.1 % / +14.6 % (3.6 V) | same |
| ss / ff f at -40 C | 1.0962 MHz (ss, 3.3 V); ff not run | 1.0991 / 1.0936 MHz (ss, 3.0 / 3.6 V); ff 1.4308 / 1.4234 MHz | consistent |

Reading: the supply moves f by -0.84 %/V in both modes. The ratio f_PTAT/f_REF removes this term to first order.
The frequency at fixed T falls by about 13 to 17 kHz/V, which is 2.6 to 3.2 C/V in PTAT mode.
The bandgap used here (Sep-19) is the one the G1 numbers used. The G1 README says the chip-of-record bandgap (BGR586) gives
1.5074 MHz at 25 C. The R1 frequency will follow `r1_bgr`, not these numbers (open item 1).

## TEMP_COUNT resolution, ctrl counting with a 30 MHz clock

Two ways to read the T2F in `r1_ctrl`:

- Method A (gate window in clock cycles): open a gate for N cycles of the 30 MHz clock and count `fout` rising edges.
  LSB in frequency = f_clk / N. LSB in degC = that value divided by the slope. Quantisation is +/-1 count.
- Method B (gate window in T2F periods): count 30 MHz clock cycles over K periods of `fout`. The count is K f_clk / f_T2F.
  It falls with temperature. It has finer resolution for the same gate time because the clock is much faster than `fout`.

Method A needs a divider-free edge counter on a 1.2 V `fout` that is asynchronous to the clock.
Method B needs a counter for K periods plus a wide clock counter. Choose in `r1_ctrl`.

The 30 MHz clock is the untrimmed RC oscillator (23 to 39 MHz, see `../r1_osc/README.md`).
The count in method A scales with 1/f_clk. A 23 to 39 MHz spread changes the gate time from 0.71 to 0.42 ms at N = 2^14.
Hence the absolute count is not a temperature reading by itself. Two remedies are possible:
read the REF mode in the same gate and use the ratio N_PTAT / N_REF (the clock and the gate time cancel,
so the ratio is f_PTAT/f_REF), or calibrate the clock. The ratio also removes C, V_REF and the comparator delay to first order.
The LSB figures below use the nominal 30 MHz clock and the least-squares slope.

**Method A** (count `fout` edges in N clock cycles)

| N [clk cycles] | gate at 30 MHz | count at -40 C | 27 C | 125 C | LSB [Hz] | LSB [C] (+/-1 count) | gate at 23 / 39 MHz clock |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2^14 = 16384 | 0.546 ms | 681 | 874 | 1152 | 1831 | 0.350 | 0.712 / 0.420 ms |
| 2^16 = 65536 | 2.185 ms | 2723 | 3496 | 4609 | 458 | 0.087 | 2.849 / 1.680 ms |
| 2^18 = 262144 | 8.738 ms | 10891 | 13984 | 18437 | 114 | 0.022 | 11.398 / 6.722 ms |

**Method B** (count clock cycles in K `fout` periods)

| K [T2F periods] | gate at -40 / 27 / 125 C [ms] | count at -40 C | 27 C | 125 C | LSB [C] at -40 / 27 / 125 C (+/-1 count) |
| --- | --- | --- | --- | --- | --- |
| 2^10 = 1024 | 0.822 / 0.640 / 0.485 | 24649 | 19197 | 14559 | 0.010 / 0.016 / 0.028 |
| 2^12 = 4096 | 3.286 / 2.560 / 1.941 | 98594 | 76786 | 58237 | 0.002 / 0.004 / 0.007 |
| 2^14 = 16384 | 13.146 / 10.238 / 7.765 | 394377 | 307145 | 232949 | 0.001 / 0.001 / 0.002 |

Ratio readout: f_PTAT/f_REF changes by 0.00332 per C (mean over -40..125 C, simulated). One count in each of two counts N_P, N_R (method A, 2^16 window: N_P = 3496, N_R = 3491 at 27 C) gives a ratio step of about 0.00057, i.e. about 0.17 C (worst case, both counts +/-1).

The slope used for LSB in degC is the least-squares slope over -40..125 C. The local slope runs 5.16 to 5.31 kHz/C,
so the LSB in degC changes by about +/-1.5 % over the range. LSB in degC for method A is the same at all temperatures
(first order). Method B LSB in degC rises with temperature, because the same one count is a larger part of f at high T.
The window length decides the conversion time: 0.55 ms (2^14), 2.2 ms (2^16), 8.7 ms (2^18) for method A.
The quantisation figures cover the counter only. They do not cover noise, jitter, the clock spread or V_REF and supply effects.
The PTAT-mode reading also moves by -13 kHz/V (-2.6 C/V at 27 C) with VDDA, if the ratio is not used.

## Open issues

1. Re-run with `r1_bgr`: not run (pending). `r1_bgr` keeps the 10/4 um PMOS unit leg at about 4.1 uA and the same
   `pbias` / `pcasc` pins, so the netlist should drop in. The deck uses `Xbgr vdd 0 r4 vref iptat pbias pcasc vbe dvbe g1_bgr`.
2. The Sep-19 bandgap is not the G1 chip-of-record bandgap. The G1 README lists the BGR586 numbers (1.5074 MHz at 25 C, 4.9085 kHz/C).
   Expect about 5 % lower f and slope with a BGR586-like bias.
3. Corner decks were run only with all three process groups moved together (ss, ff). Mixed combinations and cap corners: not run here.
4. The -40 C decks at 3.6 V need the tight options (reltol 1e-5, 10 ns maximum step). With the standard options they abort with a
   VBIC NaN (timestep too small). The same effect is in the G1 README. Keep the tight options for any further -40 C run.
5. REF mode at the other temperatures, REF mode in corners and REF at 125 C and other supplies: not run.
6. Edge counting of `fout` by `r1_ctrl` needs a synchroniser. `fout` is a 1.2 V CMOS square wave of 1.1 to 2.4 MHz, well below 30 MHz, so a
   two-flop edge detector at 30 MHz is enough. Not simulated here.
7. `fout` is undefined for about 1 us after `en` rises (G1 interface note). `r1_ctrl` must wait before the gate opens.

## Files

- `schematic/g1_t2f_rev2.spice`, `schematic/G1_INTERFACE.md` - copies of the G1 cell and its interface note.
- `sim/tb_g1_t2f.spice.tmpl`, `sim/ctl_freq.txt` - G1 testbench template and control block (include paths changed to the copies).
- `sim/g1_bgr_sep19.spice` - bias source (copy of the Sep-19 G1 bandgap).
- `sim/r1_run_t2f.py` - deck generator and runner. `sim/analyze_r1_t2f.py` - tables and `results/summary.json`.
- `sim/decks/*.cir` - decks. `sim/results/*.json` - parsed .meas values. `sim/results/tables.md` - generated tables.
- `sim/runs/run_*.json` - one record per run (command, tool versions, PDK commit, inputs, question, result, disposition).

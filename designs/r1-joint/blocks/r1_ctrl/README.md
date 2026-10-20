# r1_ctrl — R1 digital macro (RTL draft 0.1)

State (2026-10-20): the first RTL exists. It is simulated at RTL level and synthesized for a gate
count. It is not hardened (no LibreLane, no STA, no gate-level simulation). Track T5, CPU set
112–115.

`r1_ctrl` is the digital core of R1. It holds these parts:

- `r1_pos`: sin/cos correction, CORDIC, tracking loop, turn counter.
- `r1_bus`: BiSS-C, SSI and SPI on the shared pads, and `OSC_COUNT`.
- `r1_gate` logic: PWM, dead time, current-sample strobes and the ADC scheduler.
- `r1_safe` digital part: fault latch, I²t, T2F counter and watchdog.
- The register file.

The contract with the host and the analog blocks is [`R1_REGISTER_MAP.md`](R1_REGISTER_MAP.md),
draft 0.1. All RTL is clean-room Verilog-2005 under Apache-2.0, written from the specification and
studies S1, S2, S3 and S5. No third-party RTL is used. Patterns copied from G1 `g1_ctrl` (not
shared): the two-flop synchroniser, the async-assert/sync-release reset, the SCLK-domain shift
logic with a hand-off to the core clock, the `run_sim.sh` style and the `ALL TESTS PASSED`
convention.

## Built against

| Item | Version | How established |
| --- | --- | --- |
| PDK | IHP SG13G2 open PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` | `flow/run.sh` checks `/foss/pdks/ihp-sg13g2/COMMIT`; recorded in `sim/results/<run>/versions.txt` |
| Container | `tapeoutbench-eda:latest`, id `sha256:ddeb69576f28…` | pinned and checked by `flow/run.sh` |
| Icarus Verilog | 14.0 (devel) s20260301-328-geda9fdcd | `iverilog -V` in the run (`versions.txt`) |
| Yosys | 0.67 (git 2d1509d1b) | `yosys -V` in the run |
| Python / numpy | 3.12.3 / 2.5.1 (container) | recorded in the run |
| Verilator (lint only) | 5.050 | `verilator --version`; lint is not part of the recorded run |
| Standard cells | `sg13g2_stdcell_typ_1p20V_25C.lib` from the pinned PDK | `flow/synth.tcl` |
| ngspice, KLayout, xschem, LibreLane, CACE | not used in this step | — |

## Files

| Path | Content |
| --- | --- |
| `rtl/r1_ctrl_top.v` | macro top: reset, instances, pad mux `SLO`/`SDO`, `OSC_COUNT`, `STATUS`, gate enable |
| `rtl/r1_pos.v`, `rtl/r1_sinlut.v` | position path (one shared 20 × 17 multiplier; 27 ticks per pair) |
| `rtl/r1_biss.v`, `rtl/r1_idrom.v` | BiSS-C / SSI slave (MA domain + clk domain), control channel, ID bytes |
| `rtl/r1_spi.v` | SPI (native mode 0, 24 bit; AS5047P-compatible mode 1, 16 bit) |
| `rtl/r1_gate.v` | PWM, dead time, strobes, ADC scheduler, gate AND with `EN` |
| `rtl/r1_safe.v` | fault sources and latch, I²t, T2F counter, watchdog |
| `rtl/r1_regs.v` | register file, read multiplexer, calibration CRC-8 checker |
| `rtl/r1_sync2.v` | two-flop synchroniser |
| `tb/tb_pos.v`, `tb/pos_ref.py` | testbench (a): RTL against a floating-point reference, host calibration fits |
| `tb/tb_top.v` | testbenches (b)–(f) on the macro top: BiSS/SSI master, SPI host, encoder + ADC model, checks |
| `sim/run_all.sh`, `sim/summarize.py` | full run, summary, `run.json` |
| `sim/results/<run-id>/` | summary, `run.json`, test logs, synthesis statistics, input hashes |
| `flow/synth.tcl` | Yosys gate-count synthesis |

To run, from the repository root:

```
G1_CPUSET=112-115 G1_CPUS=4 G1_WORKDIR=designs/r1-joint/blocks/r1_ctrl \
G1_RESULTS_ROOT=/opt/sim/<user>/r1-traces/sims flow/run.sh sh sim/run_all.sh <run-id>
```

The run takes about 12 minutes on 4 CPUs. Bulk outputs (stimulus, per-pair traces, netlist) go to
`$G1_RESULTS_ROOT/r1_ctrl/<run-id>/`. No VCD is written.

## Status (run of record `r1ctrl_20261020_r3`)

| Check | Gate | Status | Evidence |
| --- | --- | --- | --- |
| (a) CORDIC + correction vs float reference, S1 head set, before/after calibration | V3 | passed (simulated) | `sim/results/r1ctrl_20261020_r3/summary.md` §(a), `pos_*_result.json` |
| (a) tracking loop, velocity, latch extrapolation (`EXTRAP` = 30) | V3 | passed (simulated) | cases `fast_k0`, `fast_k30`, `fast_100k` |
| (b) BiSS-C S2 items 1–8: CRC vectors, MA 80 kHz–10 MHz at 40/60 % duty, t_busy, timeout, back-to-back, aborted frame, nE/nW/Null, control channel reads, CRC-4 error, 14 × CDM = 0 | V4 | passed (simulated, own master model) at clk 42 / 30 / 21 MHz | `top_biss_{23.810,33.333,47.619}.log`, 41 checks each |
| (b) S2 item 10: SPI and BiSS on the shared pads | V4 | passed (simulated) | `top_spi_33.333.log` |
| (b) interop against ≥ 3 independent masters | V4 | not run (bench item) | — |
| (c) SSI binary / Gray, 100 kHz–2 MHz, monoflop, host trim from `OSC_COUNT` | V4 | passed (simulated) at 42 / 30 / 21 MHz | `top_ssi_*.log` |
| (d) SPI register read/write, status byte, ID mirror, error count, `OSC_COUNT`, AS5047P frames, mode switch | V4 | passed (simulated) | `top_spi_33.333.log`, 21 checks |
| (e) PWM on-times, dead time, phase, wrap-around window, centre strobes, guard, shadow update, EN gating | V5 (digital part) | passed (simulated) | `top_gate_33.333.log`, 14 checks |
| (f) each fault source latches, clear rule, CAL CRC, EN/STO, I²t trip time, watchdog, POR | V5 (digital part) | passed (simulated) | `top_safe_33.333.log`, 32 checks |
| Yosys synthesis, gate count | V6 | done; over budget (see below) | `stat_flat.txt`, `stat_hier.txt` |
| Lint (Verilator `-Wall`) | — | passed, apart from the intended `SYNCASYNCNET` on `CS_N` and `ma_rst_n` (dev run, not in the run record) | — |
| LibreLane hardening, STA at 3 corners with derate, GLS with SDF, formal equivalence | V6 | not run (not in this step) | — |
| CDC formal / structural check | V6 | not run | — |
| Gate-level or analog co-simulation with `r1_adc`, `r1_osc`, `r1_safe` (analog) | V7 | not run | — |

### Run history

| Run | Result | Disposition |
| --- | --- | --- |
| `r1ctrl_20261020_r1` | 3 checks failed | **SLO read 1 (ready) while the slave was not armed**, so an SSI frame at 42 MHz was ignored. **The tracking loop did not re-lock after signal loss at 21 MHz**: the integrator ran away on zero-amplitude samples. Both fixed for r2. |
| `r1ctrl_20261020_r2` | 7 checks failed, 3 position cases failed | the r2 acquisition aid (snap and zero ω at \|e\| > 45°) stopped lock at 50–100 kHz, because the snap fired again on each pair (a one-pair snapshot delay). Fixed for r3: a pending snapshot receives the correction, and the snap keeps the integrator. |
| `r1ctrl_20261020_r3` | all 217 chip-level checks passed; V3 within limits | run of record |

Development runs before r1 (`dev_*` under the results root) are exploratory and not evidence.
They found these bugs, all fixed before r1:

- unsigned part-select sign loss in the phase correction;
- frame word packing that dropped MT bits;
- OSC_COUNT windows that spanned frame gaps (now arm and hold);
- T2F window compare on a register shrink;
- AS-mode parity and exit from AS mode.

They also found three testbench errors (ADC hold instant, BUS_CFG test value, I²t history).

## Results (simulated, run r3)

### V3 position (`tb_pos`, 2000 pairs per case, 1 M pairs/s at 30 MHz)

The head model is the S1 tolerance set: offset 6.5 %, gain ratio 1.25, phase 10°, h3 1 % (vector
form e^{iφ} + h e^{−i(3φ+ψ)}), amplitude 1400 LSB.

| Case | Max / rms error vs true (° el) | Max, constant removed (° el) | RTL vs float reference, max (° el) |
| --- | --- | --- | --- |
| ideal head, no calibration | 0.027 / 0.012 | 0.027 | 0.005 |
| S1 head, before calibration | 13.95 / 8.48 | 12.45 | 0.006 |
| S1 head, after bench calibration (reference angle) | 0.170 / 0.128 | 0.051 | 0.021 |
| same, 0.5 LSB rms ADC noise | 0.205 / 0.126 | 0.085 | 0.020 |
| mirrored head (−6.5 %, 0.8, −10°), reverse rotation | 0.215 / 0.167 | 0.055 | 0.019 |
| S1 head, self-calibration from raw codes only | 0.555 / 0.310 | 0.441 | 0.019 |

- The fixed-point chain adds ≤ 0.021° el over the floating-point model of the same register values.
- Bench calibration meets the S1 budget (±0.25° el electronic): 0.051° el after the constant offset,
  which `ZERO_OFFSET` removes. The S1 head has a 3rd harmonic together with a phase error. This
  gives a residual at 2φ (an e^{+i3φ} component) that a self-calibration from the raw signals cannot
  separate from gain/phase errors. The result, 0.44° el, is outside the budget. The host must
  calibrate against a reference, or the head must have a smaller h3·α product. The register set
  supports both cases; only the host procedure differs.
- Tracking loop (KP = 2, KI = 11): error after settling is 0.009° el at 50 kHz and 0.004° el at
  100 kHz (constant removed). Velocity error is −0.01 % at 50–100 kHz. At 1 kHz, the 2^−5 LSB/tick
  quantisation gives −1.1 %.
- Lock from reset takes 40–96 pairs (40–96 µs) to stay within 0.5° el.
- With `EXTRAP` = 30, the output equals the angle 30 ticks ahead (same error as `EXTRAP` = 0).

### Bus

- CRC-6 wire values 0x3A / 0x02 / 0x0D for 0x00000 / 0x3FFFF / 0x12345 (S2 vectors) are
  reproduced on SLO.
- t_busy is 2 T_MA for MA ≤ 5 MHz at 30 and 42 MHz clock. It is 3 T_MA at 10 MHz (all corners)
  and at 5 MHz with a 21 MHz clock (latch handshake).
- Timeout with 600 ticks: 14.37 / 20.10 / 28.73 µs at 42 / 30 / 21 MHz. All values are inside the
  12.5–40 µs range.
- Position latched at BiSS LAT: within 0.12° el of the head angle at the LAT instant at 10 kHz el,
  at every clock corner (≈ 1 tick).
- Control channel reads 0x42/0x43/0x78/0x7F return the ID bytes with the start bit and CRC-4.
- Host trim: `OSC_COUNT` = 672 / 480 / 336 gives `TIMEOUT_TICKS` = 840 / 600 / 420 and a monoflop
  of 20.09–20.16 µs. Untrimmed, 600 ticks is 14.29 µs at 42 MHz, below the 15 µs SSI minimum. This
  is the S5 finding; the host trim corrects it.
- AS5047P-compatible ANGLECOM at 0.2 turn reads 3277 / 16384.

### Gate and safety

- On-times are DUTY − 2·DEAD exactly: 570 / 270 / 870 ticks, including a window that wraps the
  period. The strobes are at the window centre within ±1 tick. No current conversion started late
  over 20 periods.
- `EN` low forces the gates low within 1 ns (combinational path in the RTL; the real delay is a
  pad/STA item).
- Comparator flag to `FAULT_N` low: 4 ticks (133 ns at 30 MHz).
- I²t (i² = 2500, LIM 2000, TAU 6): trip after 102.8 PWM periods. The integer model gives 103
  updates; the closed form gives 102.2.
- Watchdog fires 4091 ticks after the last SPI frame (period 4096).
- T2F count is 273 for 273.1 expected.

## Gate count (Yosys, run r3, typical library)

| Item | Value |
| --- | --- |
| Cells / flip-flops | 15 201 / 1 738 |
| Cell area | **220 968 µm²** (30.4 kGE at 7.26 µm² per `nand2_1`); 39 % in flip-flops |
| Ratio to the 0.18 mm² digital budget (cell area only) | **1.23** |
| Macro estimate at the G1 run7 ratio (129 600 µm² macro / 84 796 µm² synthesis) | **0.338 mm² = 1.88 × budget** |
| Per module (µm²) | `r1_pos` 79 637, `r1_regs` 42 799, `r1_gate` 37 886, `r1_safe` 23 021, `r1_biss` 21 785, `r1_spi` 11 494, top 4 808, `r1_sinlut` 1 235 |

The 0.18 mm² budget (D6) was set before open item 6. Open item 6 moved the PWM generation back
on chip; `r1_gate` alone is 0.038 mm² of cells. These are candidate reductions, estimated and not
run:

- Narrow PWM/period/phase registers to 12–13 bit and use per-channel relative counters instead of
  five modular subtractors: −10 to −15 k µm².
- Trim register widths, `TEST_POS` and the diagnostic counters: −5 to −8 k µm².
- Remove the AS5047P mode: about −3 k µm².
- Share the comparators and adders of `r1_pos` (40-bit loop terms, saturation): −5 to −10 k µm².

Even with all of these, the macro is about 0.28 mm². The floorplan owner must choose: more area
(the D9 1.5 mm die), or functional cuts (for example the AS5047P mode, the SSI mode, or the
on-chip I²t). This is a floorplan decision.

## Open issues

1. **Area: 1.88 × the digital budget (estimated macro).** See the section above. A decision is
   needed before hardening.
2. **BiSS D2 details are interpretations.** They need the D2 figures and interop (V4 bench):
   - the slave start bit and its position in the CDS reply;
   - whether CTS is covered by CRC-4;
   - the ID byte order;
   - the stop-bit clock after the CRC;
   - the Profile ID value (placeholder 0x0001);
   - `MFR_ID` 0x0000 (not assigned, spec open item 5).
3. **LAT quantisation.** The latch instant is quantised to one clk tick (33 ns at 30 MHz). This is
   0.12° el at 10 kHz and 1.2° el at 100 kHz, which uses most of the ±0.64° el total target at the
   top of the range. A half-tick capture (both clock edges) would halve it. Not designed yet.
4. **Self-calibration.** It does not reach the S1 accuracy with h3 and phase error together
   (0.44° el). A reference calibration is needed, or a 2φ angle-correction term (one more LUT
   term, about 1 kGE).
5. **Acquisition range.** The snap aid works up to 45° el per pair. The locked loop tracks up to
   90° el per pair. At 21 MHz (slow corner), the pair rate falls to 0.7 MHz, so count-safe speed
   falls to about 175 kHz el. S1 count-safe is 250 kHz at 1 M pairs/s.
6. **ADC interface timing is assumed.** The testbench assumes 12 ticks per conversion. A pair needs
   ≤ 15 ticks per conversion to fit `PAIR_TICKS` = 30. This must be agreed with `r1_adc` (T2).
7. **`ANA_CTRL` bit assignment.** It is open until the AFE, ADC, T2F and BGR interfaces exist. The
   comparator flag names `cmp[3:0]` must be agreed with the analog `r1_safe` (T4).
8. **STA.** The design must close at the fastest untrimmed clock (about 42 MHz, S5). The critical
   candidates are the shared multiplier plus adder in one cycle (`S_M2`) and the 40-bit loop update
   in `S_L1`. Not run.
9. **EN response.** EN is combinational to the gates in the RTL. The pad-to-pad delay and the
   glitch filter on `EN`/`STO_IN` are not decided.
10. **Shared-pad rule.** The host must keep `SCLK` low before `CS_N` falls and wait one timeout
    after the SPI use (register map §1). A `CS_N` glitch shorter than 3 ticks can release the
    BiSS reset asynchronously (not simulated).

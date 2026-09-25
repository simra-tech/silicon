# G1 red-team review: digital and mixed-signal interface (2026-09-25)

Scope: `g1_digital` (RTL in `blocks/g1_ctrl/rtl`, `blocks/g1_seu/rtl`), the
on-chip gate-level netlist, its interfaces to G1_TRIP / G1_GATE / G1_OSC, and
the documents that tell a host how to drive it. The question is which digital
or mixed-signal errors could make the silicon unusable or the breaker unsafe.
All numbers are **simulated** (Icarus Verilog, behavioural analog models). No silicon.

Paths starting `blocks/` are under `designs/g1-guardian/blocks/`. `RT/` means
`blocks/g1_ctrl/sim/redteam_20260925/`. Line numbers refer to the RTL at HEAD
`e1627e8c`.

## Built against

| Item | Value | How established |
|---|---|---|
| PDK | IHP SG13G2 `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` | `flow/run.sh` refuses to start otherwise; printed in every log header |
| Simulator | Icarus Verilog 14.0 (devel) s20260301-328-geda9fdcd-dirty | `iverilog -V`, log headers |
| Container | `tapeoutbench-eda:latest` = `sha256:ddeb6957…` | `flow/run.sh` image identity check |
| Gate models | PDK `sg13g2_stdcell.v` + `sg13g2_udp.v`, `-DFUNCTIONAL -DUNIT_DELAY=#1`, no SDF | `RT/run_redteam.sh` |
| On-chip netlist | `g1_digital.nl.v` `6181b988…` (`${BULK}/digital-final-nlrename-20260923-r1/`), copied to `build/g1_redteam/chipnl/` (gitignored) | sha256 in the log header; identity chain in `blocks/g1_padring/reports/signoff-1414-20260924/README.md` |

## What was run

| Run | Command (repository root) | Result | Log |
|---|---|---|---|
| Existing RTL suite | `G1_CPUSET=40-41 G1_CPUS=2 G1_CONTAINER_ENGINE=podman G1_WORKDIR=designs/g1-guardian/blocks/g1_ctrl/sim flow/run.sh ./run_sim.sh` | passed: tb_g1_digital 15 tests / 204 checks; tb_g1_seu 11 tests / 43 checks | `RT/baseline/tb_g1_digital_rerun.log`, `RT/baseline/tb_g1_seu_rerun.log` (the script overwrites the committed logs; those were restored unchanged) |
| Existing system tb on the **on-chip** netlist `6181b988` | `flow/run.sh bash …/redteam_20260925/run_redteam.sh gls-system /work/build/g1_redteam/chipnl/g1_digital.nl.v chip6181b988` | passed: 13 tests / 193 checks (T11/T12 skipped as in every GLS run) | `RT/tb_g1_digital_gls_chip6181b988.log` |
| Red-team bench, RTL | `… run_redteam.sh rtl` | 5 tests: R1 passed; R2–R5 reproduce hazards (11 failed checks, by design of the bench) | `RT/tb_redteam_rtl.log` |
| Red-team bench, on-chip netlist | `… run_redteam.sh gls /work/build/g1_redteam/chipnl/g1_digital.nl.v chip6181b988` | identical to RTL, line for line (checks, observations, 9651-cycle latency) | `RT/tb_redteam_gls_chip6181b988.log` |

`RT/tb_redteam.v` uses the environment models of `tb_g1_digital.v` with two
changes that match the chip: `por_n` is tied 1 (canonical CDL: `sg13g2_tiehi`),
and the oscillator runs only while `osc_en === 1`. A "check" states what the
register map or the top-level specification promises, so **a FAIL line in this
bench is a reproduced hazard**; "OBSERVE" lines report behaviour outside the
documented operating contract.

## Findings, ranked

Ranks: **blocker** = the chip is unusable or unsafe inside its documented bench
contract; **must-fix** = before tape-out, change the design or the contract
(an ECO or an explicit, documented host rule); **should-fix** = evidence or
documentation gap; **note** = checked, no action or cosmetic.

No blocker was found. The digital logic on the chip is functionally the RTL
(GLS below), the pin maps are consistent, and the comparator sampling phase is right.

### M1 (must-fix). A stopped oscillator removes all protection, FAST_EN included, and serial reads return stale data

- Cause: `osc_en` is one unprotected register bit (`g1_regfile.v:124,148,165`).
  Writing `OSC_CTRL[4]=0` stops `osc_clk`. So can an upset of that flop (the
  configuration registers are not triplicated), a mis-framed write (M4), or an
  analog oscillator failure. There is no clock-loss detector.
- The top-level spec §6 says the <10 µs target does not apply "to a stopped
  clock with FAST_EN disabled", which implies FAST_EN covers a stopped clock. It
  does not. Both comparators are dynamic and strobed by `cmp_clk`
  (`g1_digital_top.v:111-115`; CDL `g1_trip`: `XCH … cmp_clk_n … g1_cmp_regenpair4`,
  tail NMOS gated by the clock). No clock means no decision, so `cmp_hard`
  holds its last value and the fast path can never fire.
- In SCLK-domain reads, `rd_hold` is only updated in `osc_clk` (`g1_serial.v:398-399`).
  After the clock stops, every read returns the value of the last read before
  the stop. A host that polls `STATUS` keeps reading 0x80 (EN, not tripped).
- Evidence (R4, RTL and on-chip netlist): with MODE=0x23 (FAST_EN=1) and INRUSH=0,
  write OSC_CTRL=0x08, then apply a hard overload. 10 µs later the G1_GATE latch
  is still 0 and the GATE pad is still on. The `CHIP_ID` read returns 0x80 (stale
  STATUS) instead of 0x47. A serial write cannot restart the clock (the map
  documents this). Only an EN cycle recovers.
- Fix options: (a) ECO to tie `g1_osc.en` high at chip level; (b) keep the
  silicon, correct spec §6, and add a host watchdog rule: alternate reads of
  `CHIP_ID` and a moving `OSC_CNT_L`, and on a stale or non-advancing result drop EN
  and assert the external inhibit; (c) in a future revision, triplicate
  `OSC_CTRL` and gate the fast path with an unclocked comparator.

### M2 (must-fix). A live write that raises INRUSH re-opens the inrush mask while the breaker is armed

- Cause: `inrush_cnt` stops at the old limit (`g1_trip_timer.v:78-80,155-156`).
  `inrush_active = inrush_cnt < {INRUSH,9'd0}` becomes true again as soon as
  INRUSH is raised. Soft and hard counters are then held at zero
  (`:86,114,159,179`). Register map §4.2/§5 masks only "after reset release and
  after every retrigger re-enable".
- Evidence (R2, RTL = netlist): INRUSH=1 expires; STATUS.INRUSH_ACTIVE=0; write
  INRUSH=0x14 → INRUSH_ACTIVE=1 immediately; a hard overload then trips after
  **9651 cycles** (≈1 ms) instead of 9–12. The blind time is up to
  (255−old)×512 cycles, which is 13 ms.
- Fix: RTL `inrush_cnt` saturating at 17'h1FFFF instead of stopping at the limit
  (a re-harden). Without that, add a host rule to the map and the bench plan:
  change INRUSH only with the external inhibit asserted, then wait for
  INRUSH_ACTIVE=0 before releasing it.

### M3 (must-fix: owner decision). Defaults leave each EN rise and each retry unprotected for about 1 ms

- By specification (§3, §4.2, §5) the hard path is masked for INRUSH×512 cycles
  (reset 0x14, ≈1 ms) after every EN rise and every retrigger re-enable, and
  FAST_EN resets to 0. EN low also erases any host configuration
  (`g1_digital_top.v:96`), so a host cannot arm FAST_EN before the gate turns on.
  G1_GATE turns the gate on as soon as `en_core` rises (INTERFACE.md,
  `gate_core = en_core & !tripped`). The chip has no current limit (spec §6).
  With no host, a short at EN therefore conducts for ≈1 ms, limited only by the
  FET and the bus, and again at every retry (RETRY_MAX, or without limit at 0xFF).
- This matches the documentation (T05 tests it). The bench contract relies on an
  external inhibit. It is ranked must-fix because it is the largest remaining
  hazard to the external switch. The owner must accept it explicitly in the
  README/spec, or change it: exempt the hard path from the inrush mask, or reset
  MODE with FAST_EN=1. Both need a re-harden.

### S1 (should-fix). Serial framing: one SCLK glitch or one stall silently redirects writes

- Cause: no chip select, no parity/CRC and no write acknowledge. Framing is by
  bit count (`g1_serial.v:326-343`) and is restored only by a 64-cycle idle
  (`:304-315`). Register map §1.2 allows back-to-back frames. The map gives no
  minimum SCLK rate, yet any SCLK-low phase of 64 osc cycles or more
  (≈5.3–8 µs) resets the frame counter mid-frame.
- Evidence (R3, RTL = netlist):
  (a) one 5 ns spurious edge before two back-to-back host writes
  (DAC_SOFT=0x50, MODE=0x07) produces a write of **SOFT_TIME_H=0x83**. That sets
  the soft window to 0x8327×25.6 µs ≈ **0.86 s** instead of 1 ms. Neither intended
  write happens.
  (b) a 10 µs stall after the command byte (a bit-banged host) turns the data
  byte into a command: the host's DAC_HARD=0x0B write becomes **MODE=0x02**, which
  disables the soft path.
- A redirected write can also land on OSC_CTRL (M1).
- Fix (host/contract): read back every write (already in `measurement/README.md`),
  idle ≥128 osc cycles before each frame (drop "back-to-back frames are legal"
  for safety-relevant writes), state a maximum SCLK-low time (<64 osc cycles at
  +20 % oscillator, i.e. <5.3 µs), keep SCLK low when idle, and route SCLK
  with signal integrity in mind (the pad input is used as a clock).

### S2 (should-fix). The documented SOFT_TIME byte order can create a transient 0x0000 window

- Register map §4 says "write `_H` then `_L`". Going from 0x0100 to 0x00FF, `_H`
  first gives 0x0000 for one frame, and 0x0000 means "trip on the first sample"
  (`g1_trip_timer.v:85,91`). Going from 0x00FF to 0x0100, `_L` first gives the
  same. No single byte order is safe in both directions. A transient that is
  larger than the new value delays a trip for one frame.
- Evidence (R5, RTL = netlist): with a continuous soft overload and the
  accumulator at ≈2100 cycles, following the documented order trips at once,
  cause soft. The old window was 65536 cycles and the new one 65280.
- Fix (doc): "clear MODE.SOFT_EN while writing SOFT_TIME" is the only safe rule.
  The failure is a nuisance trip, on the safe side.

### S3 (should-fix). The chip-context STA timed the run7 netlist, not the netlist on the chip

- `blocks/g1_ctrl/reports/sta_merged_sdc_20260924/sta.tcl:14-15,27,47` read
  `layout/g1_digital.nl.v` (`fce14375`) and the run7 SPEF. The README says
  the 1414 µm GDS "keeps the same run7 `g1_digital` macro unchanged". The
  signoff identity chain says the on-chip macro is run7 logic with a **new CTS,
  resize, reroute and fill** (nl `6181b988`, SPEF `e6c89575`).
- What does exist for `6181b988`: the macro-level STA in
  `${BULK}/digital-postroute-20260923-r1/flow/02-openroad-stapostpnr`. It shows
  setup ≥ 28.49 ns and hold +0.104 / +0.183 / +0.323 ns (fast/typ/slow), 0
  violations, and `independent_sta_audit.json` gives max clock fanout 8 and
  222 clock buffers. The worst hold paths are the SCLK input shift chain
  (`_6673_→_6674_`).
- Consequences: the "78 max-fanout flags" in the STA README and in the
  g1_ctrl README describe the run7 clock tree, not the chip's. The
  pad-to-macro timing with the merged SDC on the real netlist is **not run**.
  Only nominal RC was used, with no derate. The hold margin is 104 ps on a
  scan-less design whose hold failures cannot be fixed by slowing the clock.
- Fix: rerun `sta.tcl` with `6181b988` and `e6c89575`. Add min/max-RC or a hold
  derate if extraction allows it.

### S4 (should-fix → partly closed here). Gate-level simulation of the on-chip netlist

- Before this review, GLS had run on run5/6/7 but not on `6181b988`. It has now
  run: the existing system tb passed 13/193 on `6181b988`, and the red-team
  bench gives results identical to the RTL. Together with the recorded
  equivalence proof (`6181b988 ≡ 2b342c24 ≡ fce14375`), this closes the
  functional question.
- **Not run**: SDF-annotated (timing) GLS of `6181b988`. SDFs exist in
  `${BULK}/digital-postroute-20260923-r1/flow/final/sdf/`. The earlier run7 SDF
  pilot (`blocks/g1_ctrl/sim/campaigns/sdf_20260921T141228Z_6a81b6d5`) failed T05
  (`fault_n` sampled 1 ns after the edge) and was never dispositioned.

### S5 (should-fix). EN is the only reset: no deglitch, no POR

- `arst_n = por_n & en` (`g1_digital_top.v:96`), with `por_n` tied high on the chip.
  (a) If EN is high at power-up, the core is never reset (R1 OBSERVE: `osc_en`,
  `dac_hard`, `trip_d/clr_d/fast_en` are X). In silicon that state is random,
  and `osc_en=0` would leave the chip dead until EN toggles. Contract P4 (EN low
  ≥2 ms) covers this. The EN input pad has no pull-down, so the board must
  hold EN low.
  (b) A short EN glitch that reaches `rs0/rs1` restores every default, clears
  a latched trip in both latches (G1_GATE also clears on `en_core` low), and
  restarts the unprotected inrush window (M3). The only sign is a
  configuration read-back.
- Verified in-contract (R1 passed on RTL and netlist): with EN low and before
  the first `osc_clk` edge, every analog-facing output is defined: `osc_en`=1,
  `osc_trim`=8, `dac_soft`=0x99, `dac_hard`=0xFE, `trip_d`=`clr_d`=`fast_en`=`cmp_clk`=0,
  `trip_set_sel`=0, `t2f_en/mode/bgr_r4`=1/0/0, `sdo`=0, `gate_en`=0. The first
  frame after EN rise read CHIP_ID correctly after 130 cycles.
- Fix: document the EN glitch behaviour and a host canary-register check.
  Add a board RC or Schmitt filter on EN.

### S6 (should-fix, not run). Digital switching noise on the VDD/VSS shared with the comparators

- The canonical CDL connects `g1_digital`, `g1_trip` (DACs and both comparators)
  and `g1_osc` to the same `VDD`/`VSS`. The SEU scrubber is on by default
  (`SEU_CTRL`=0x01, checkerboard). About 640 chain flops, plus 1200 flops in
  total, switch on every `osc_clk` rising edge. That is the same edge on which
  `cmp_clk` toggles and both comparators strobe.
- The chip co-simulation runs the digital as RTL through `d_cosim`
  (`blocks/g1_top/sim/run_top.py:890-913`), so the digital supply current is
  never simulated. The effect of supply and ground bounce on the decisions and
  on the relaxation oscillator is **not run**.
- Fix: a current-profile or PEX supply simulation. On silicon, repeat the
  threshold calibration with the scrubber off (SEU_CTRL=0) and with the
  all-zeros pattern, and compare.

### S7 (should-fix). Configuration registers are not triplicated on a radiation test chip

DAC codes, MODE, INRUSH, OSC_CTRL and the other configuration registers are
plain flops (`g1_regfile.v:131-170`). A single upset persists until rewrite or EN
(`FAULT_INJECTION_20260921.md`). Host periodic read-back and rewrite mitigates
all of them except OSC_EN (M1). Document the read-back and scrub duty for the
irradiation plan.

### Notes (checked; no defect or cosmetic)

- **N1 Comparator strobe phase: correct.** `cmp_clk_q` toggles on every
  `osc_clk` rise (`g1_digital_top.v:111-115`). G1_TRIP inverts it for the hard
  comparator (`XCLKI clk cmp_clk_n`; `XCH … cmp_clk_n`). So the hard comparator
  evaluates when `cmp_clk` falls at osc edge k. Its NOR output latch
  (`MMNA*/MMNB*`) holds until edge k+2. `s0` samples at k+1, mid-window and about
  98 ns after a ≤2 ns decision; `s1` takes it at k+2. The count happens at k+3,
  where `hard_sample = ~cmp_clk` = 1 (`g1_trip_timer.v:108-115,181-186`). Each
  decision is counted exactly once, and the 9–12-cycle latency (T05, GLS)
  matches. The soft comparator (clk = `cmp_clk`, rising) is accumulated as a level
  every cycle, as specified.
- **N2 TRIP_SET_SEL does nothing on silicon.** `g1_trip` has no `trip_set_sel`
  pin. In the canonical CDL `i_core_trip_set_sel` has no load, and the TRIP_SET
  pad's core net `i_core_trip_set` goes only to the pad. Register map §2/§4.3
  (MODE[3]) should say so.
- **N3 Soft decay is truncated.** `decay_pre` restarts on every high sample
  (`g1_trip_timer.v:162-169`), so DECAY=1/2/3 needs 4/16/64 *consecutive* low
  samples before one count down. Example: DECAY=1 with 2 cycles high and 6 low
  gives +1 per 8 cycles, not the +0.5 of "1 per 4 samples", so it trips in half
  the time. This errs toward tripping earlier. Correct the §4.2 wording.
- **N4 DAC lines** are combinational from registers through the hysteresis mux
  and the offset adders (`g1_trip_timer.v:95-105`). They can glitch for ns after
  a register write or a hysteresis change. The 26×26 µm MIM caps on
  `vth_soft/vth_hard` filter this, and the INTERFACE ≥1 µs settle rule applies.
  Register writes change all bits in one clock (atomic). The open hysteresis
  update-timing item in `blocks/g1_trip/INTERFACE.md` is unchanged. SENSE_OFS
  arithmetic is correct: a 10-bit signed sum with saturation (`:101-105`), with
  range −128…382 inside ±512.
- **N5 Pin order: consistent.** The `g1_dig_cosim.v` ports (7 in, 48 out) and
  the `adig`/`adac` lists in `run_top.py:900-913` match position for position,
  MSB first. The CDL `.SUBCKT g1_digital` (46 ports) against
  `Xi_core_u_digital`: every net matches its port name, and `por_n` goes to
  `net`, driven by `Xi_core_u_digital_1 … sg13g2_tiehi`. Bit order is consistent
  with `g1_trip` (`dac_*[0..7]`) and `g1_osc` (`trim[0..3]`). `g1_gate` pin order
  matches.
- **N6 Timer arithmetic: no overflow.** `inrush_cnt` 17 b (max limit 0x1FE00),
  `hold_cnt` 21 b (0x1FE000), `soft_cnt` 24 b saturating (maximum window
  0xFFFF00), `hard_cnt` saturating, HARD_N=0 → 1. HOLD/re-arm, give-up and
  cool-down follow §5. `trip_cnt`, `soft_peak` and the SEU counters saturate.
  The SEU TMR vote and rewrite, fill restart and injection are as specified
  (tb_g1_seu 11/43 passed).
- **N7 CDC.** All crossings go through 2-flop synchronisers or toggle
  handshakes. Write address and data are stable for ≥16 SCLK periods after the
  toggle. The read margin of ≥3.5 osc cycles relies on f_SCLK ≤ f_OSC.
  Metastability MTBF is **not run** (also listed in the STA README). SCLK idling
  high never times out.
- **N8 Stale committed log.** `blocks/g1_ctrl/sim/tb_g1_digital.log` (2026-09-18)
  ends at tb line 588, while the testbench is now 600 lines. Today's rerun
  passes 15/204 with the current testbench.

## Not run

SDF-annotated GLS; chip-context STA of `6181b988`; min/max-RC timing;
synchroniser MTBF; digital supply-noise co-simulation; any transistor-level
run of the stopped-clock (M1) or EN-glitch (S5) cases; silicon.

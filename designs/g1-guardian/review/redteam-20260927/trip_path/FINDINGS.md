# Red team 2026-09-27: trip path (SENSE → TRIP → GATE, BGR as the threshold reference, hand-off to the timer)

Chip of record: r3 `g1_chip_top_1414_r3.gds` (`7d07a784…`). Every number here is **simulated** unless it
is quoted from an existing record, which is then named. Nothing was measured. Paths: `${REPO}` is the
repository root, `${BULK}` the external artifact root. Scripts, deck templates and evidence are in this
directory.

## 1. Verdict

**Yes, r3 is safe to submit as is for the trip path.** No finding stops the silicon from working or from
being tested. The breaker trips, a tripped state survives VDD or IOVDD dips, and the hard-threshold error
is systematic and can be calibrated.

**F1 (MAJOR) is worth a layout change if the owner wants a hard threshold that does not need per-part,
per-temperature calibration.**
- The 8–11 mV hard early trip is a 0.20–0.34 ns race between two clock edges inside G1_TRIP. It is not
  caused by the size of the hold capacitors.
- In simulation with ideal edges, a non-overlapping comparator clock takes the hard offset from 46–48 LSB
  to within 2 LSB at tt, ss/1.08 V/−40 °C and ff/1.32 V/125 °C. The soft path stays within 1–2 LSB.
- The metal-only clock swap does not work. It moves 16–31 LSB of early trip onto the soft path.
- The real fix costs about 18–22 h, which is at or just over the budget.

If r3 goes as is, the calibration contract must change (F2). F3 and F4 are board and firmware rules only.

## 2. Findings

| ID | Title | Severity | Evidence | Proposed fix | Effort / GDS |
|---|---|---|---|---|---|
| F1 | The hard early trip is a clock-edge race. It is 46–48 LSB at tt/27 °C on the block bench and 53–59 LSB at ff/−40 °C on the r3 chip deck. `XCLKI` (PMOS 1/0.13 µm, NMOS 0.5/0.13 µm) makes the hard comparator strobe 0.20–0.34 ns after the soft comparator starts its reset. A non-overlapping clock removes it | **MAJOR** | §3.1; `evidence/kick_r1…r8_results.jsonl`; variant netlists in `${BULK}/redteam-20260927/trip_path/net/` | Replace `XCLKI` with a non-overlap generator: soft clock = OR(`cmp_clk`, `cmp_clk` delayed about 3 ns), hard clock = NAND(`cmp_clk`, delayed). About 12–16 LV devices plus a delay element next to the existing inverter. No new pins and no RTL change (§6) | 18–22 h: layout 4–6; macro DRC/LVS/kpex 1.5; block brackets over corners 3; chip DRC/LVS/XOR 1.5; chip `c_mid`/near-threshold/`cal` re-run 6–8 (wall); records 2. **Changes the GDS** (G1_TRIP cell) |
| F2 | H6 and the calibration procedure are not sufficient as written. (a) The fallback "k(T) from the simulated margin table" mixes process with temperature. (b) The offset moves with oscillator frequency and with the soft comparator's decision. (c) The rehearsed and documented hard bracket keeps the soft comparator deciding low, which is not its state in operation | MINOR (bench and documentation; safety-relevant) | §3.2; `evidence/kick_r1/r2/r6_results.jsonl` | Spec §6 H6 and `measurement/README.md` step 2: remove the table fallback and declare hard accuracy only at the calibration temperature until a per-part bench table exists. Bracket hard with `DAC_SOFT` set so the soft comparator decides high, at the `OSC_TRIM` used in operation, with T2F in its operating state. Repeat at every declared temperature | 1–2 h, no GDS change |
| F3 | A VDD dip or brownout with EN held high. GATE stays on (3.30 V) while protection is dead. On VDD recovery the digital core is not reset, because `por_n` is tied high. Configuration, `clr_pulse` and `tripped` can come back random, and a random `clr_d` clears a held analog trip | MINOR (board and firmware) | §3.3; `evidence/brownout_summary*.txt`; RTL `rtl_eco_20260925/g1_digital_top.v` lines 58–95 and `g1_trip_timer.v` lines 140–200 | P8/B7: the VDD supervisor asserts the inhibit **and** drives EN low. After VDD returns, hold EN low ≥ 2 µs, rewrite and read back the configuration (H5), then release the inhibit | 1 h, no GDS change |
| F4 | Drain dV/dt turns the FET on. With the CSD16340Q3 model, a gate loop of 5 nH + 10 Ω and a drain edge to 12 V of 1.2 V/ns or faster, V<sub>GS</sub> peaks at 1.08–1.25 V against V<sub>th</sub> 0.861 V | MINOR (board and bench) | §3.4; `evidence/dvdt_summary.txt` | Board: a gate–source capacitor of at least 10× C<sub>rss</sub>, a short gate loop, or a bus dV/dt limit of 0.1 V/ns or less. Add a drain-step hold-off test to the bench plan | 0.5 h, no GDS change |

## 3. Per-finding detail

### 3.1 F1: a clock-edge race

**What was checked.** The existing record points at edge timing rather than capacitor size. The "hclk"
what-if in `blocks/g1_trip/sim/postlayout/README.md` gives −3 LSB with an ideal hard clock at zero delay,
and −47/−41/−30 LSB at 5/10/20 ns. Three questions were tested:
1. How far apart are the two edges in the extraction?
2. Does reversing their order fix the offset?
3. What does a symmetric non-overlapping clock give on both paths?

**Bench.**
- `tb_kick_rt.cir.tmpl` is a copy of `tb_trip_kick_train.cir` with the strobe period as a parameter and
  `cmp_clk_n` written out.
- The driver `kick_rt.py` uses the same criterion as `kick_threshold.py`: 4 strobes per comparator,
  strobes 1–3 read 50 ns after the edge, trip when at least 2 of 3 are high.
- The netlist is the r3 TRIP extraction `g1_trip_nf4_pex.spice` (`ba86b7b2…`), either unchanged or
  rewired for simulation only:
  - `make_swap_variant.py`: `eb8a9ad0…`;
  - `make_nov_variant.py`: nov3 `d2522109…`, sdl3 `b2c32e4e…`, sdl1p5 `3343d02f…`.
- Settings: hard code 200, soft code 153, ideal ISENSE, VREF 1.04 V, strobe period 212 ns.
- "ud" is the underdrive of `icmp` below the DC threshold, in LSB. 1 LSB = 1.962 mV at `icmp` =
  0.196 mV of shunt.
- Each run is one ngspice-46 job through `flow/run.sh`, with `G1_CPUSET` inside 0–7 and PDK `84374023`.

**Edge timing.** The delay from `cmp_clk` falling to `cmp_clk_n` rising (50 %) is:

| Corner | Delay |
|---|---|
| tt/27 °C | 0.266 ns |
| tt/−40 °C | 0.27 ns |
| tt/125 °C | 0.32 ns |
| ss/1.08 V/−40 °C | 0.34 ns |
| ff/1.32 V/125 °C | 0.21 ns |

The hard decision takes 0.8–1.7 ns (existing delay record), so the soft reset kick lands in the middle
of it.

**Results.** T = trip, n = no trip, \* = mixed decisions. The offset column is relative to the code, in
LSB; negative means an early trip.

| Variant | Path and corner | Points | Offset |
|---|---|---|---|
| as extracted | hard, tt | 40 T, 46 T, 49 n, 52 n | **−46…−48 (−9.0…−9.4 mV)** |
| **swap** (soft on `cmp_clk_n`, hard on `cmp_clk`; metal only) | hard, tt | −8 T, −3 T, −1 T, +1 n, +4 n, +8 n, +16 n | −1…+1 |
| swap | hard, ss/1.08 V/−40 °C and ff/1.32 V/125 °C | +2 n, +8 n | better than −2 |
| swap | soft, tt | −2 T, 0 T, +2 T, +4 T, +8 T, +16 T, +32 n | **−16…−31: rejected** |
| **nov3** (ideal non-overlap: each comparator resets 3 ns after the other evaluates) | hard, tt | −2 T, +1 n, +3 n, +6 n | −2…+1 |
| nov3 | soft, tt | −2 T, +1 T\*, +3 n, +6 n | about −1…−2 |
| sdl3 (only the soft reset delayed by 3 ns; hard on the real inverter) | hard; tt / ss/1.08 V/−40 °C / ff/1.32 V/125 °C | at each corner: −2 T, +1 n, +3 n | −2…+1 |
| sdl3 | soft; tt / ss/−40 °C / ff/125 °C | −2 T, +1 T\* / −2 T, +1 T\* / −2 T, +1 n | −1…−2 |
| sdl1p5 (1.5 ns delay) | hard, ss/1.08 V/−40 °C | +1 n, +3 n | better than −1 (trip side not run) |

**Why it matters.** Once the evaluating comparator decides before the other comparator's reset edge, the
kick does no harm. That removes three things the project now carries:
- the 40–56 LSB offset, its 10–11 LSB corner spread, and with them H6;
- the lost top of the hard range: usable 25–40 mV instead of 25–50 mV;
- the `FAST_EN` threshold, which sits 8–11 mV below its code.

The swap result shows that whichever comparator evaluates within about 0.25 ns after the other's reset
takes the error, so a symmetric non-overlap is needed. sdl3 works on this bench. In silicon, though, the
soft evaluate edge would then pass through an OR gate while the hard reset passes through the inverter,
which is again a sub-ns race. The recommended form is the NAND/OR pair driven from one delayed copy of
the clock.

The fallback is the parked hold2x candidate. It is DRC/LVS clean and gives −21…−25 LSB with a spread of
4 LSB (existing record). It takes 10–12 h, but H6 stays.

### 3.2 F2: what the hard offset depends on

Same bench, as extracted, hard code 200, brackets of 3 LSB.

| Condition | Offset below the code (LSB) |
|---|---|
| tt/1.2 V/27 °C, 212 ns (`osc_clk` 9.44 MHz), soft code 153 | 46–48 |
| tt/−40 °C | **43–45** |
| tt/125 °C | 46–51 |
| 27 °C, 161 ns (`osc_clk` 12.4 MHz, the ff/−40 °C oscillator) | 43–45 |
| 27 °C, 263 ns (`osc_clk` 7.6 MHz, the ss/125 °C oscillator) | 46–48 |
| 27 °C, soft code 100 (the soft comparator always decides high) | **40–45** |
| 27 °C, soft code 255 (the soft comparator always decides low) | **46–51** |
| r3 chip deck, ff/−40 °C, ideal 9.436 MHz clock (existing record) | 53–59 |

**(a) Temperature against the table.** At tt, temperature alone moves the offset by about 3 LSB, and cold
goes the opposite way to the table's cold row. The table's +12 LSB at ff/−40 °C is mostly process. Using
the table as k(T) could over-correct a cold part by about 3 mV. That error points toward a missed trip
and only just fits the ±10 % guard band at T = 30 mV.

**(b) Frequency.** Every corner row used the ideal 9.436 MHz clock. The R0.95 oscillator actually spans
7.61–12.43 MHz over corners at trim 8, so the frequency effect (about 3 LSB) is missing from the table.

**(c) Soft comparator state.** The `cal` rehearsal (`FULLCHIP_CDL_R3_CORNERS_20260927.md`) and
`measurement/README.md` step 2 bracket the hard path at 25 mV with the soft code at its default of 153
(30 mV). The soft comparator therefore decides low during calibration. In operation the soft threshold
sits below the hard one, so at the hard threshold the soft comparator decides high. The offset is 40–45
LSB with soft high and 46–51 LSB with soft low. The calibrated code is therefore too high by up to about
6 LSB (about 1.2 mV), which biases the trip late.

### 3.3 F3: supply dips at the GATE driver

**Bench.** `tb_gate_brownout.cir.tmpl` and `run_brownout.sh`:
- G1_GATE schematic netlist with the real `sg13g2_IOPadIn` (EN) and `sg13g2_IOPadOut30mA` (GATE);
  10 Ω + 5 nF on GATE;
- EN driven through 1 kΩ from a 3.3 V host rail, low until 3 µs, then high;
- `trip_d` = VDD if tripped, 0 if armed;
- case BV: VDD 1.2 → 0 V from 5 to 25 µs, held at 0 V, back at 35 µs, with IOVDD = VDDA = 3.3 V;
- case BA: IOVDD/VDDA 3.3 → 0 V and back, with VDD at 1.2 V;
- the ss and ff runs use the deck-local `nodcn` pad copy (`run_top.nodcn_io_lib()`), because the stock
  pads stalled at 1.17 µs at ss/125 °C.

Command, run with `G1_WORKDIR=designs/g1-guardian/blocks/g1_gate/sim` and `G1_CPUSET=2`:

```
flow/run.sh env NODCN=<0|1> bash run_brownout.sh <BV|BA> <1|0> <mos> <T> ${BULK}/redteam-20260927/trip_path/bo
```

| Case | tt/27 °C | ss/125 °C | ff/−40 °C |
|---|---|---|---|
| BV armed: GATE during the collapse / after it | 3.30 / 3.30 V | 3.30 / 3.30 V (nodcn) | 3.30 / 3.30 V (nodcn) |
| BV tripped: GATE maximum | 1.9 nV | 0.12 µV (nodcn) | 4.4 nV |
| BA tripped: GATE maximum after IOVDD returns (`gate_core` maximum) | 9.4 µV (0.065 V) | 12.7 µV (0.12 V) (nodcn) | 7.8 µV (0.10 V) (nodcn) |
| BA armed | GATE follows IOVDD down and back to 3.30 V (nodcn) | not run | not run |

The ff BV-tripped row and the ss and ff BA-tripped rows come from the first version of the deck, with EN
high from 2 µs (`evidence/brownout_summary_firstdeck.txt`).

**Reading.**
- The analog side is robust. The VDDA-domain latch and the pad's level-up hold a trip through a full VDD
  collapse, and `trip_d` sets the latch again after an IOVDD dip.
- With the FET on, it stays on for the whole dip and nothing protects it, because the comparators, the
  oscillator and the timers all run on VDD.
- The gap is the recovery. In the r3 RTL:
  - `por_n` is tied high;
  - `en_sync`, `en_hist`, `en_off` and `en_seen` are reset only by `por_n`;
  - `arst_n = por_n & ~en_off & (en | en_seen)`.
- With EN high when VDD returns, the core is reset only if `rs1` happens to power up at 0. Otherwise the
  following come back random: `MODE`, the DAC codes, `FAST_EN`, `HARD_N`, `INRUSH`, `clr_pulse` and
  `tripped`.
- `clr_d = (clr_pulse != 0)` is reset-dominant on the analog latch. It can clear a held trip and, with
  `tripped` = 0, re-energise the fault, or leave both paths disabled.
- This is RTL reasoning. The power-up randomness cannot be simulated in the X-propagating co-simulation.

### 3.4 F4: drain dV/dt while the FET is held off

**Bench.** `tb_gate_dvdt.cir.tmpl` and `run_dvdt.sh`:
- G1_GATE C-PEX and the 30 mA pad, with EN low;
- gate loop of 5 nH + 10 Ω (22 Ω where stated);
- CSD16340Q3 vendor model, unchanged, with the `run_fet_campaign.py` wrapper;
- 10 kΩ gate to source, 25 + 10 mΩ source return;
- drain driven 0 → 12 V through 1 Ω at 2 µs;
- V<sub>th</sub> 0.861 V (`REAL_FET_20260921.md`).

The tt runs with the stock pads **failed (numerical)** at `xfet.10`, as in the REAL_FET record. The rows
below use the `nodcn` pads. The drain current in brackets is from a reference run with the gate shorted
to the source, which leaves only the displacement current.

| Corner | Drain edge | V<sub>GS</sub> maximum | Pad maximum | I<sub>D</sub> peak (gate shorted) |
|---|---|---|---|---|
| tt/27 °C | 100 ns | 0.365 V | 0.278 V | 0.243 A |
| ss/125 °C | 100 ns | 0.446 V | 0.371 V | 0.255 A |
| tt/27 °C | 10 ns | **1.082 V** | 0.893 V | 1.810 A (1.817 A) |
| ss/125 °C | 10 ns | **1.133 V** | 1.016 V | 1.866 A |
| ss/125 °C, Rg 22 Ω | 10 ns | **1.150 V** | 0.871 V | 1.866 A |
| tt/27 °C | 2 ns | **1.226 V** | 1.205 V | 6.620 A |
| ss/125 °C | 2 ns | **1.248 V** | 1.298 V | 6.739 A (6.739 A) |
| ff/−40 °C | 2 ns | **1.127 V** | 1.027 V | 6.519 A |

The Miller current exceeds what the pad can sink. The drain current is dominated by displacement
current; the channel share was not separated. This is a limit set by the board and the choice of FET,
not a silicon defect.

## 4. Checked and found clean

- A tripped state through a VDD collapse and through an IOVDD/VDDA dip: GATE ≤ 13 µV at tt, ss and ff
  (§3.3).
- Comparator metastability and slow ramps. The decision takes ≤ 1.7 ns at 1 mV overdrive (NF4 PEX
  record) against a 106 ns half period. Behind it are the SR latch, a 2-flop synchroniser, and `HARD_N`
  consecutive decisions with clear-on-low.
- Glitches and ringing. `hard_pulse` (45 mV, 200 ns) gives no trip at tt, ss/125 °C and ff/−40 °C (r3
  record). `HARD_N` = 4 filters anything shorter than about 640 ns. The exception is `FAST_EN` = 1, which
  is documented (P7).
- DAC monotonicity: DNL ≤ 0.032 LSB and INL ≤ 0.22 LSB (existing `rppd` MC). Not repeated.
- Sense-amplifier common mode. The DC range −0.1/+0.3 V is covered. The common-mode gain at 1 MHz is
  −36 dB (schematic) and −48.6 dB (post-layout), so a 0.3 V ground bounce gives ≤ 0.24 mV of shunt
  (derived, not simulated).
- Reference start-up against comparator arming. A low VREF moves the thresholds in the early-trip
  direction (N2), and the EN ≥ 2 ms rule covers settling with 10 nF on the VREF pin.
- PEX against schematic. The hard offset appears in the schematic joint MC (+7.95 mV), the NF4 kpex
  bench (9.0 mV) and the r3 CDL deck (8.0–9.3 mV). The SENSE post-layout overshoot (18–21 mV on a 1 V
  step) settles within 226 ns. No quantity that the schematic view hides changes a trip decision.
- The clock-inverter delay is 0.20–0.34 ns at every corner run, and no corner reverses the edge order.

## 5. Not run

- F1 on a drawn cell (extraction, a real delay element, corners, chip-level re-run): **not run**. Only
  ideal-edge variants of the unchanged extraction were run.
- nov3 at ss and ff: **not run**. The late side of the swap variant's hard path at ss and ff:
  **not run**.
- Hard offset against VDD at 1.08/1.32 V: **not run** here (another aspect ran it). VDD bounce at the
  strobe (ELECTRICAL_SYSTEM S2): **not run**.
- DAC code change while armed (a switch-tree glitch, relevant with `FAST_EN` = 1 and with H6 re-coding):
  **not run**.
- Near-threshold cases and `hard_pulse` with `FAST_EN` = 1 on the r3 deck: **not run**.
- F3 recovery with the digital in the loop: **not run**.
- F4 with the stock pads at tt: **failed (numerical)**. Channel current, energy, other FETs, and a gate
  loop inductance other than 5 nH: **not run**.
- Sense transient with shunt ESL, cable and ground bounce: **not run**.

## 6. Implementation notes for F1 (for the layout engineer)

### 6.1 What exists today

**Schematic netlist** (chip deck `blocks/g1_trip/sim/qualification/joint586-softinputpair4-nf4-roomcal-s73133-20260924-r1/trip.spice`,
`f5f0a90a…`, lines 33–35):

```
XCLKI cmp_clk cmp_clk_n vdd vss g1_inv
XCS icmp vth_soft cmp_clk   cmp_soft cmp_soft_n vdd vss g1_cmp              (soft, NF4)
XCH icmp vth_hard cmp_clk_n cmp_hard cmp_hard_n vdd vss g1_cmp_regenpair4   (hard)
```

- The LVS reference `reports/pex/nf4/g1_trip_nf4_lvs.cdl` has the same instances. Its port is named
  `clk`, so the line reads `XCLKI clk cmp_clk_n VDD VSS g1_inv`.
- The macro pin `cmp_clk` is unchanged by the fix. The digital drives it at `osc_clk`/2.

**Extraction** (`sim/postlayout/g1_trip_nf4_pex.spice`, flat):
- Clock inverter: `XM1234` (PMOS 1/0.13 µm) and `XM1141` (NMOS 0.5/0.13 µm), output `cmp_clk_n`.
- Soft comparator, gates on `cmp_clk`:
  - tail `XM1110`–`XM1113` (4 × 4/0.13 µm NMOS, node `n1692`);
  - precharge `XM1226`–`XM1229` (PMOS 6/3/3/6 µm).
- Hard comparator, gates on `cmp_clk_n`:
  - tail `XM1130`–`XM1133` (node `n1700`);
  - precharge `XM1239`–`XM1242` (same sizes).
- Both comparators present the same clock load: about 16 µm of NMOS gate plus 18 µm of PMOS gate.

### 6.2 Required change

1. Delete `XCLKI`. Add a cell, for example `g1_nov`, with input `cmp_clk` and outputs `soft_ck` and
   `hard_ck`:
   - `cmp_d` = `cmp_clk` delayed by D;
   - `soft_ck` = OR(`cmp_clk`, `cmp_d`);
   - `hard_ck` = NAND(`cmp_clk`, `cmp_d`).
2. Change `XCS` so that its clock is `soft_ck`, and `XCH` so that its clock is `hard_ck`.
3. Change nothing else.

Resulting timing (checked against the `make_nov_variant.py` sources, which use ideal 0.2 ns edges):
- `soft_ck` rises with `cmp_clk` rising, which is the soft evaluate edge (unchanged).
- `soft_ck` falls D after `cmp_clk` falls. That is the soft reset, which comes after the hard comparator
  has decided.
- `hard_ck` rises when `cmp_clk` falls, which is the hard evaluate edge.
- `hard_ck` falls D after `cmp_clk` rises. That is the hard reset, which comes after the soft
  comparator has decided.
- Edge arithmetic with real gates. At `cmp_clk` falling, `hard_ck` rises after t<sub>NAND</sub> and
  `soft_ck` falls after D + t<sub>OR</sub>, a margin of D + t<sub>OR</sub> − t<sub>NAND</sub>. At `cmp_clk`
  rising, `soft_ck` rises after t<sub>OR</sub> and `hard_ck` falls after D + t<sub>NAND</sub>, a margin
  of D + t<sub>NAND</sub> − t<sub>OR</sub>. Both margins must exceed the decision time; with matched
  gates they are about D.

The simulated what-ifs map onto this as follows:
- `make_nov_variant.py <nf4_pex> out.spice 3` moves the 8 soft clock gates to `soft_ck` and the 8 hard
  clock gates to `hard_ck`. It drives both from ideal pulses: `soft_ck` high from 20 ns for PER/2 + D;
  `hard_ck` high from 20 ns + PER/2 for PER/2 + D.
- The `softonly` option keeps the hard comparator on the extracted inverter.

**Non-overlap window.** The margin is (evaluate-edge time at the victim comparator) to (reset-edge time
at the other comparator).
- Minimum margin: **≥ 2.5 ns at ss/1.08 V/−40 °C**. The hard decision takes 1.694 ns at 1 mV overdrive
  on the NF4 extraction (existing record), plus the edge skew. sdl1p5 (1.5 ns) passed its hard no-trip
  points at ss/−40 °C, but its trip side was not bracketed. Treat 1.5 ns as unproven.
- Design target: D = 3 ns typical, at least 2.5 ns at the ss corner.
- Maximum margin: **≤ 20 ns at ff/1.32 V/−40 °C**. The reset must still leave the precharge time before
  the next evaluate edge. The shortest half period is 40 ns at `osc_clk` 12.43 MHz (ff/−40 °C, trim 8).
  At 20 ns, the extracted precharge has 20 ns left, where it now has 40 ns.
- The 10 and 20 ns what-ifs (hclk) show that the delay does not have to be tight. A delay element with
  ±50 % spread is acceptable.
- Ordering constraint: D − |t<sub>OR</sub> − t<sub>NAND</sub>| ≥ 2.5 ns at every corner. Use
  matched-size OR and NAND output stages.

**Delay element options.**
- 4–6 LV inverters with a MOS-cap load of about 5–10 fF each.
- One inverter into an RC made of an `rppd` resistor of about 30 kΩ and about 50 fF of MOS cap, followed
  by a restoring inverter.
- Current does not matter. The existing inverter load is about 34 µm of gate, so the final NAND/OR
  drivers should be at least 2/0.13 µm (NMOS) and 4/0.13 µm (PMOS). The present 1/0.5 µm inverter is
  weak and makes the slow edge worse.

### 6.3 Where it goes

`layout/gen_trip_layout.py`:
- The inverter is at `XI, YI = 175.0, 185.0` (lines 890–926).
- The clock enters at the east pin at `Y_CLK = 196.9` and runs on M3 west to `XCLK = 172.0`. It drops on
  M2 to the M3 line at y = 192.0, which feeds the soft comparator clock and the inverter input.
- `cmp_clk_n` leaves on M3 at y = 188.0 to the hard comparator clock.
- The soft comparator is centred at x = 141.7 µm and the hard comparator at x = 208.0 µm, both at
  CY = 162.0. Each cell is 29.4 × 22.7 µm.
- The VDD bar is at y = 206 and the IOVDD bar at y = 202.75 (M3).

Measured on the cut macro `${BULK}/trip-nf4-pex-20260924-r1/g1_trip_nf4.gds` (KLayout region
intersection, drawn datatype 0):
- The window (160–200, 176–190) µm, 560 µm², holds only 8.0 µm² of Activ, 9.1 µm² of M1, 7.0 µm² of M2
  and 5.3 µm² of M3. That is the inverter and the clock risers.
- The window (150–172, 176–191) µm holds 7.9 µm² of Activ and no M2 or M3.
- The strip x ≈ 160–190 µm, y ≈ 176–190 µm is therefore effectively free, about 30 × 14 µm.
  - The generator (about 16 devices) fits there beside `XI`.
  - Keep clear of the hard comparator's west edge at x ≈ 193 µm.
  - Keep clear of the MIM keep-outs of `CHH` at (162.5, 158.5) + 26 µm.
- Route `soft_ck` on the existing M3 y = 192 line (cut it off `cmp_clk`) and `hard_ck` on the existing
  M3 y = 188 line.
- The chip-level filler regenerates fill over the macro, so run chip density and antenna again.

### 6.4 Acceptance: what a drawn cell must reproduce

1. Block LVS of the new macro against the edited CDL: `XCLKI` removed, `g1_nov` added, `XCS`/`XCH` clock
   nets renamed.
2. kpex 2.5D CC, same flow as `sim/postlayout/README.md`, then `make_pex_netlist.py`, giving
   `g1_trip_nov_pex.spice`.
3. Run brackets on that extraction with the bench here. The queue line format is
   `tag net mos vdd temp cond hard_code soft_code period_ns vdda res ud`, and the tag must not contain
   "swap". From `${REPO}`:

```
cd designs/g1-guardian/review/redteam-20260927/trip_path
N=<container path of g1_trip_nov_pex.spice>; O=${BULK}/redteam-20260927/trip_path/nov_drawn; mkdir -p $O
for c in "mos_tt 1.2 27" "mos_ss 1.08 -40" "mos_ff 1.32 125"; do set -- $c
  for u in -2 2; do echo "novd $N $1 $2 $3 hard 200 153 212 3.3 res_typ $u"; echo "novd $N $1 $2 $3 soft 200 153 212 3.3 res_typ $u"; done
  echo "novd $N $1 $2 $3 hard 254 153 212 3.3 res_typ 2"
done > $O/q
for cpu in <8 CPUs>; do BULK=${BULK} python3 kick_rt.py points $cpu $O $O/q & done; wait
python3 kick_rt.py ptable $O
```

Expected pass (≤ 2 LSB bracket = ≤ 0.4 mV of shunt) at every corner, for both the hard and the soft
path:
- ud −2 → T;
- ud +2 → n;
- hard code 254 at ud +2 → n.

For reference, the ideal-edge results are:
- nov3 and sdl3 at tt: hard −2 T / +1 n; soft −2 T / +1 T\*;
- sdl3 at ss/1.08 V/−40 °C and ff/1.32 V/125 °C: hard −2 T / +1 n; soft −2 T / +1 (T\* at ss, n at ff).

The baseline for comparison is ud 46 T / 49 n (hard, tt).

Also run:
- the strobe periods 161 and 263 ns at tt (hard, ud ±2);
- soft code 100 and 255 (hard, ud ±2). These show that the F2 dependencies are gone.

Then run the existing comparator delay deck (`run_postlayout.sh cmppex` with `PEXNET`), which must give
all decisions correct at 1 mV, and the settle deck.

4. At chip level, on the r3full deck with the new TRIP extraction, re-run:
   - `c_mid` compact at tt, ss/125 °C and ff/−40 °C;
   - near-threshold at code 200: 1.10×, 1.15× and 1.20× must not trip; 1.25× is inside the ±10 %
     band;
   - the `cal` hard sweep, whose crossing should now land within about 2 codes of the ideal 127;
   - `hard_pulse` and `q`.

   Commands are as in `blocks/g1_top/sim/FULLCHIP_CDL_R3_CORNERS_20260927.md`, with the TRIP extraction
   swapped in.
5. Then run chip DRC (main, maximal, precheck, density, antenna), projected LVS and XOR against r3. Only
   the G1_TRIP cell may differ.

# Red team 2026-09-27: bring-up, calibration and observability (aspect `bringup`)

Scope: `measurement/` (bench plan, `bringup/FIRST_SILICON_SEQUENCE.md`, `BOARD_CHECKLIST.md`,
`g1_host.py`), the hard/soft threshold calibration (spec §6, host rule H6, the `r3x` calibration
rehearsal), the pin map and QFN24 bond map `bondmap_20260926_r4.csv`, and the observability of each
block from the pins and registers. Chip of record r3 `7d07a784…`, register map 1.2.
All new numbers here are **simulated** (block level or model) or **computed**. Nothing has been measured.
Tools are the pinned container: ngspice-46, OpenSTA 3.1.0, PDK `84374023`. CPUs 36–43.

## 1. Verdict

**Yes: r3 is safe to submit as it is, for the bring-up aspect.** Every block can be observed and
exercised from the 24 pins and the register map:
- the comparator decisions in `STATUS2`, the analog latch in `TRIPPED_A`, the driven DAC codes in
  `DAC_*_EFF`;
- gate-off through `MODE.FORCE_TRIP`;
- the SEU counters, with on-chip injection;
- `f_OSC` through `OSC_CNT`;
- the temperature on `TEMP_OUT`, `VREF` on its pin, and the device coupons on their pins.

The hard/soft calibration can be run as written and takes seconds, not minutes. A dead or partly dead
part can be told apart without the serial interface, because the supply currents, `TEMP_OUT` and
`GATE`-follows-`EN` each give a separate signature.

I found no BLOCKER and no finding that justifies a GDS change for this aspect. There are two
calibration findings; both are fixed in the host software and the procedure:
- **BR-1:** a single calibration point at 25 mV mis-sets 35–39 mV hard targets by −1.1 to −1.4 mV.
- **BR-3:** the H6 fallback table mixes up process and temperature.

Fix both before the first bench calibration. The rest is bench and documentation.

## 2. Findings

| ID | Title | Severity | Evidence | Proposed fix | Effort, GDS change |
| --- | --- | --- | --- | --- | --- |
| BR-1 | Hard calibration at one 25 mV point does not carry over to the 35–39 mV operating targets: the kick offset grows with the driven code by 0.10 LSB per code | MINOR (bench; must-fix before the first calibration) | New block runs: offset 43 / 46 / 50 LSB at codes 172 / 200 / 240 (tt/27 °C, `kick_block/table.txt`). Unmodified `g1_host` against that model: target 35 mV gives an effective 33.92 mV (−1.08 mV, −3.1 %); 39 mV gives 37.63 mV (−3.5 %) (`calmodel/calsim_tt.txt`). Calibrating at the target gives −0.02 mV (`calmodel/calsim_tt_at35.txt`); control with a code-independent offset −0.09 mV (`calmodel/calsim_control.txt`) | Bracket the hard crossing at the operating target, or at 25 mV and at the target and interpolate the offset against the code. Update S9/S10, `calibrate_hard`/`codes_for` and the spec §6 "±0.5 mV at calibration temperature" wording | 2 h; no GDS change |
| BR-2 | The hard-threshold reach is below the 35–39 mV targets that S10/S11 use, on part of the population and at cold | MINOR (bench planning) | Reach at driven code 255 is 40.1 mV at tt (block model), 39.4 mV at ff/−40 °C (block, 55–56 LSB at code 254). Joint MC total hard offset spans 5.51–9.63 mV (sd 1.06), which takes up to 1.7 mV more. The chip-deck ff/−40 °C offset is 2.3 mV above tt. Result: about 38.4 mV (worst of 22 seeds, room) and about 34.6 mV (3σ, chip ff/−40 °C). `codes_for` then refuses the target (safe), so the S10/S11 temperature points stall | Use hard targets ≤ 33 mV for the temperature matrix (soft ≤ 28–30 mV; the 45 mV demo fault stays ≥ 1.1×). Add a "reach" check at each temperature to S9. The design option is the parked `nf4_hold2x` candidate; see §5 | 1 h; no GDS change |
| BR-3 | H6 fallback: "k(T) from the simulated margin table" applies a process/chip-context offset as if it were temperature | MINOR (host rule, spec §6) | In the TRIP macro (ideal ISENSE source), temperature moves the offset by ≤ 2 LSB: tt −40/27/125 °C 45/46/47; ff −40/27 °C 49/49; ss −40/125 °C 41/44. VDD 1.08/1.32 V gives 45/47 (`kick_block/table.txt`). The r3x ff/−40 °C 53–59 LSB is therefore not a comparator temperature effect. The fallback would lower a typical part's threshold at −40 °C by about 12 LSB (2.3 mV, +6.6 % at 35 mV) toward the 1.1T trip bound | Use only per-part measured k(T) (S9 at −40/25/125 °C); delete the simulated-table fallback, or set k(T) = 0 until measured. To attribute the chip-deck effect, run chip-level tt/−40 °C and ff/27 °C near-threshold cases (not run, §6) | 1 h; no GDS change |
| BR-4 | Calibration input cannot be applied as written: a "traceable 25 mV source at the Kelvin pins" looks into a fixed 25 mΩ shunt | MINOR (board) | `BOARD_CHECKLIST.md` §4 calls for a 25.00 mV source plus DMM and forbids a jumper in `SENSE_P`. The shunt stays in circuit, so 25 mV across it needs 1 A | Put the calibration current injection through the shunt on the board (current source plus 6½-digit DMM on the Kelvin pins), or use a make-before-break relay that swaps the Kelvin pair to a mV source with `EN` low. Never open `SENSE_P` while powered | 1 h (board spec); no GDS change |
| BR-5 | f<sub>OSC</sub> measurement: a 50 ms host interval with adapter-latency timestamps gives about 1–2 % error. That is comparable to the 2.7 % trim step and the ±1.5 % trim screen, and 3–5× the S11 soft-window acceptance of "± 1 sample" (0.39 %) | MINOR (host) | `g1_host.measure_fosc(interval_s=0.05)` timestamps around USB frames. Computed: δ = 0.5–1 ms per transaction (assumed, typical of USB SPI adapters; not measured) / 50 ms | Use `OSC_DIV` = 3 (wrap 10.8 s at 12.43 MHz) and a 5 s interval (error ≤ 0.02 %), or take 1 s at `OSC_DIV` = 0 (under the 1.35 s wrap) | 1 h; no GDS change |
| BR-6 | No dead-part triage in the sequence; S3 only says "check wiring". The expected `I(VDD)` in S6 is "not simulated" | MINOR (procedure) | New vectorless STA estimate of the r3 macro (`4b83f181` + SPEF `0b626c7f`, typ, 9.436 MHz): clock running with static data 0.876 mW = **0.73 mA**; 0.83 mA at 0.1 data activity; leakage 2.0 µW = 1.7 µA (`digital_power/pwr.log`). RTL: `TEMP_OUT` runs with `EN` low and with a dead oscillator (`TEMP_CTRL` reset 0x01, asynchronous reset, synchronous release never happens without a clock) | Add a no-serial triage step S2b (table in §3 BR-6). Put the `I(VDD)` expectation of 0.85–1.2 mA (osc 115 µA + macro) in S6 | 1 h; no GDS change |
| BR-7 | The S3 register pattern test cannot be run with `g1_host` | MINOR (host) | `G1.write` refuses `MODE` bit 3 (0xAA/0xFF), `TEMP_CTRL` bit 2 (0x55/0xFF), `OSC_CTRL` bit 4 = 0 (0x00/0xAA) and `SOFT_TIME` (must use `write_soft_time`). No pattern-test function exists | Define the pattern per register (e.g. `MODE` & 0x37, `TEMP_CTRL` & 0x03, `OSC_CTRL` \| 0x10, `SOFT_TIME` through H-then-L) and add `pattern_test()` with a unit test | 1–2 h; no GDS change |
| BR-8 | Pin numbers and the chip identity in the bench documents | MINOR (documentation) | Register map §1 has "`SCLK` (14), `SDI` (15), `SDO` (16)". These are **die-pad** numbers: QFN leads are 17/16/15, and lead 14 is `TEMP_OUT` (16 mA push-pull), so a board wired from the map drives SCLK into an output. Bench plan "Board and bench requirements" names `g1_chip_top_1414.gds` (`629d303a…`, r1) as the chip of record | Write "die pad 14 / QFN lead 17" etc. in the map; name r3 `7d07a784…` in the bench plan | 0.5 h; no GDS change |
| BR-9 | Supply-lead continuity in S1 cannot see an open supply bond | MINOR (procedure) | S1 forces ±10 µA at ±0.5 V compliance on leads 1/3/7 and screens only for shorts (\|V\| > 0.1 V). An open bond and a diode near 0.5 V both read at compliance. "Disabled but connected" bench outputs may float instead of sitting at 0 V | Use ≥ 1 V compliance in the forward (−10 µA) direction and flag compliance as "open". Tie the rails to ground with a switch, not with a disabled output. S2 supply currents confirm the result | 0.5 h; no GDS change |
| BR-10 | No analog-off debug mode on the board | MINOR (board option) | `VDDA` (lead 7) and `IOVDD` share one source. `VDDA` below `IOVDD` is permitted (spec §3, P3), and the oscillator, digital macro and IO run from `VDD`/`IOVDD`, so serial access with `VDDA` open is possible in principle. **Not simulated.** `GATE` state in that mode is unknown, so keep the inhibit asserted | Add a removable 0 Ω link in the `VDDA` branch after its sense link, for supervised isolation of a `VDDA` short | 0.5 h (board); no GDS change |

## 3. Per finding

### BR-1: one-point hard calibration and the code dependence of the kick offset

- **What was checked.**
  - The spec §6 contract and S9/S10 calibrate the hard path at 25 mV and then arm at 35 mV (S10)
    or 35–39 mV (S11).
  - `hard_extra` is one constant.
  - The TRIP README records that "the early trip also depends on the code: it is 2–5 LSB smaller at
    code 200 than at 0xFE", but that dependence was never carried into the calibration.
  - New block runs isolate the dependence at tt/27 °C.
- **Commands.**
  - Block runs, from the repository root, with
    `designs/g1-guardian/blocks/g1_trip/sim/postlayout/kick_threshold.py` (unmodified); the netlist
    is `g1_trip_nf4_pex.spice`, the soft code is 153 and the queue is `kick_block/queue.txt`:
    `BULK=${BULK} python3 designs/g1-guardian/blocks/g1_trip/sim/postlayout/kick_threshold.py worker <cpu> ${BULK}/redteam-20260927/bringup/kick kick_block/queue.txt`
    Eight workers ran on CPUs 36–43; each ngspice run is pinned through `flow/run.sh`
    (`G1_CPUSET=<cpu>`) and takes about 6.5 min.
  - Table: `kick_threshold.py table ${BULK}/redteam-20260927/bringup/kick`.
  - Model runs: `HOSTDIR=designs/g1-guardian/measurement/bringup python3 calmodel/calsim.py 46 0.103 0 25 30 33 35 37 39`
    and the same with `HARDV=35` and with `0.0` for the slope (control).
- **Result (block, simulated).**
  - Offsets: code 172 → 43 LSB, 200 → 46, 240 → 50. The slope is 0.103 LSB per code. The code-200
    value reproduces the documented 46.
  - The unmodified host calibration against this model:

    | Target | Effective threshold | Error |
    | --- | --- | --- |
    | 30 mV | 29.49 mV | −1.7 % |
    | 35 mV | 33.92 mV | −3.1 % |
    | 39 mV | 37.63 mV | −3.5 % |

  - With a code-independent offset (control) the same code lands within 0.1 mV. Calibrating at the
    target lands within 0.02 mV.
- **Why it matters.**
  - Spec §6 promises ±0.5 mV hard accuracy at the calibration temperature. That holds only at 25 mV.
  - At the S10/S11 targets the error is 2–3× that bound. It uses up a third of the ±10 % guard band
    before temperature, supply or SEU pattern have been counted.
  - The error is in the direction that trips early, toward the 0.9T no-trip bound.
- **Fix.** Bench only: add a `vin_mV` = target (or a second point) to `calibrate_hard`, store
  offset(code), and have `codes_for` use it.

### BR-2: DAC reach of the effective hard threshold

- **Offsets.** From the block results, code 255 carries 51.7 LSB of offset at tt (46 + 0.103 × 55), so
  the effective reach is (255 − 51.7) × 0.1973 mV = **40.1 mV** (V<sub>REF</sub> 1.04546 V). At ff/−40 °C the
  block offset at code 254 is 55 LSB (56 at 1.32 V), giving a reach of about 39.4 mV.
- **Lower reach at the population tail.** Two inputs lower it further:
  - The joint MC seeds are all tt: total hard offset at 25 mV calibration ranges from +5.51 to
    +9.63 mV, mean 7.95, sd 1.06 (`blocks/g1_trip/sim/qualification/joint_r3_mc_20260926/RESULTS.md`).
  - The r3 chip deck shows +2.3 mV at ff/−40 °C against tt
    (`blocks/g1_top/sim/FULLCHIP_CDL_R3_CORNERS_20260927.md`).

  | Case | Reach (computed) |
  | --- | --- |
  | Worst of the 22 seeds, room temperature | 40.1 − 1.7 = about 38.4 mV |
  | 3σ with the chip ff/−40 °C shift | 40.1 − 3.2 − 2.3 = about 34.6 mV |

- **Effect on the plan.**
  - The S11 hard target of 39 mV is not reachable on the tail of the population even at room
    temperature.
  - The S10 35 mV target at −40 °C is marginal.
  - The host refuses an unreachable code (`G1SafetyError`), so the failure mode is a stalled test
    point, not a wrong threshold. The plan should still pick targets that every part can reach: hard
    ≤ 33 mV for the temperature matrix.
- **The spec code range is not changed.** "0.5 to 1.0 of the sense full scale" still describes the
  code; the effective range is about 25–38 mV.

### BR-3: what H6's simulated k(T) actually is

New block brackets (NF4 PEX, ideal ISENSE, soft code 153; `kick_block/table.txt`), hard offset in LSB
below code 200:

| | −40 °C | 27 °C | 125 °C |
| --- | --- | --- | --- |
| tt 1.2 V | 45 | 46 | 47 |
| ff 1.2 V | 49 | 49 | not run |
| ss 1.2 V | 41 | not run | 44 (43 at 1.08 V) |

Supply at tt/27 °C: 45 at 1.08 V, 47 at 1.32 V. Code 254 at ff/−40 °C: 55 (56 at 1.32 V). Soft path at
tt: −1 LSB at −40 °C, 0 at 125 °C, so it needs no temperature correction (confirmed).

- **What the block shows.** Inside the TRIP macro, temperature moves the hard offset by at most 2–3 LSB
  over −40…125 °C, and process by ±4. The r3 full-chip deck gives 53–59 LSB at ff/−40 °C against 40–47
  at tt/27 °C. That +12 is therefore a chip-context effect: the real SENSE output driving the kicked
  `icmp` node, or the bandgap/VREF path.
- **What is not known.** Whether that effect is temperature or process is not known, because the chip
  deck was run only at tt/27, ss/125 and ff/−40 °C.
- **Why the fallback is unsafe.** The H6 fallback "k(T) from the simulated margin table" would apply
  the full ff/−40 °C shift to any part at −40 °C. On a part that does not need it, the threshold rises
  by about 2.3 mV (+6.6 % at 35 mV). Combined with other errors this crosses the 1.1T trip-region
  bound.
- **Fix.** Per-part measured k(T) only. S9 already measures at −40/25/125 °C.

### BR-4: calibration input on the board

The bench plan and checklist both describe a mV source at the Kelvin pins, and `SENSE_P` must never
open while powered. With the shunt fixed, the only executable version is a known current through the
shunt, with the DMM reading the Kelvin voltage. That needs about 1 A at 25 mV and 1.4 A at 35 mV, from
a source separate from the inhibited load bus. The board needs that path, or a make-before-break relay
switched with `EN` low. The alternative (a jumper) is ruled out by P9 and B8.

### BR-5: host f<sub>OSC</sub> measurement

`measure_fosc` reads `OSC_CNT` twice, each read being two SPI frames, around a 50 ms `sleep`, with
host timestamps. With `OSC_DIV` = 0 the counter ticks every 27 µs at 9.4 MHz, so quantisation is
0.05 %. The timestamp uncertainty dominates. S4 (±1.5 % trim screen) and S11 (soft window "± 1 sample
period", 0.106 µs in 27.1 µs = 0.39 %) both depend on this number.

### BR-6: dead-part triage without the serial interface (proposed S2b)

Signatures that exist on r3, all obtained without serial access:

| Observation | Healthy (simulated/computed) | Points to |
| --- | --- | --- |
| `VREF` pin | 1.045 V (BGR586, tt) | BGR / `VDDA` |
| `I(VDDA)` | 1.28–1.73 mA over corners (R3/RES) | analog bias |
| `TEMP_OUT`, `EN` low | 1.52 MHz at 27 °C | T2F, `g1_ls_up`, 16 mA pad, `IOVDD`. It runs even with a dead oscillator (RTL `temp_ctrl` reset 1) |
| `I(VDD)`, `EN` low | osc 115 µA [R3] + macro 0.73 mA static (new STA) ≈ **0.85 mA** | oscillator and clock tree alive. A dead oscillator leaves ≲ 0.12 mA (osc bias + 1.7 µA leakage) |
| `I(VDD)`, `EN` high minus `EN` low | + about 0.1–0.4 mA (checkerboard scrubber; STA 0.83–1.21 mA at 0.1–0.5 activity) | reset released, scrubber running |
| `GATE` with `EN` high, no shunt voltage | 3.3 V | `EN` pad, G1_GATE, 30 mA pad |
| Serial write `TEMP_CTRL` = 0 → `TEMP_OUT` stops; `MODE.FORCE_TRIP` → `GATE`/`FAULT_N` low | — | write path works even if `SDO`/reads fail |
| 45 mV at the Kelvin pins with reset defaults (hard 0xFE, effective about 39–42 mV) | `GATE` < 1 V within about 1.5 µs | whole breaker path without the host |

**STA command** (the netlist and SPEF are in `${BULK}/digital-eco-r3cand2-20260926/final/`):
`G1_CPUSET=43 G1_CPUS=1 G1_CONTAINER_ENGINE=podman G1_RESULTS_ROOT=${BULK} flow/run.sh sta -no_init -exit digital_power/pwr.tcl`,
with `$::env(BULK)` set to the bulk root inside the script. The estimate is vectorless: the per-cell
switching activity is set globally, not from a waveform.

**Cross-check.** LibreLane's own `power__total` for the same macro at 10 MHz is 1.152 mW
(`metrics.json`), in the same range.

### BR-7 to BR-10

See the table. Each was checked by reading `g1_host.py` (`write`, `measure_fosc`, `_calibrate`),
`FIRST_SILICON_SEQUENCE.md` S1/S3, `G1_REGISTER_MAP.md` §1 and the bond map. No runs were needed.

## 4. Checked and clean

- **Comparator observability.** `STATUS2.CMP_SOFT`/`CMP_HARD` are the synchronised raw comparator
  latches (`g1_regfile.v` line 214). `cmp_clk` runs whenever the core is out of reset, independent of
  `MODE` (`g1_digital_top.v` 98–103), so the sweep with `MODE` = 0 is valid.
- **Gate-off during characterisation.** `MODE.FORCE_TRIP` holds `GATE` low with the configuration
  kept. `FAST_EN` = 1 exposes single-strobe hard decisions on `GATE`, if timing is wanted.
- **SEU counters.** They are readable (0x1B–0x20), with `INJ_PLAIN`/`INJ_TMR` self-test. S8 is
  executable.
- **T2F readout for H6.** Resolution and time are ample: 4.909 kHz/°C on 1.5 MHz, so a 10 ms timer
  capture resolves about 0.02 °C. Even if the whole chip-deck 12 LSB per 67 °C were temperature, ±2 °C
  of T2F error gives ±0.07 mV of threshold (computed).
- **Convergence.** Soft plus hard calibration is 916 + 726 frames, about 1.6 s at 1 ms per USB
  transaction, and 96 ms of chip-side time (DummyTransport count, `calmodel/`). At 25 mV the hard
  crossing stays ≤ 255 for every simulated offset: at most 127 + 59 + 9 ≈ 195.
- **Soft path.** Within 0–1 LSB at tt −40/125 °C (new block runs). No k(T) is needed.
- **Lead numbers.** `FIRST_SILICON_SEQUENCE.md`, `BOARD_CHECKLIST.md` and `g1_host.py` match
  `bondmap_20260926_r4.csv` for every lead mentioned (manual check). The one exception is the
  register map (BR-8).
- **Host tests.** `g1_host.py` unit tests: 29/29 passed (`python3 -m unittest test_g1_host`,
  Python 3.6.8, re-run 2026-09-27).
- **S1 currents.** The ±100 µA forcing on the HBT pins stays below E–B reverse breakdown, because the
  pad diodes clamp at about 0.6–0.7 V under ±1 V compliance (reasoned, not simulated). `G_SHARED` uses
  ±10 µA / ±0.8 V.
- **Power-up and handling.** Order (P1/P2/P4/P6), inhibit handling and ESD handling (checklist §7:
  shorting jumper on `G_SHARED` and the device pins) are consistent between spec, bench plan, checklist
  and sequence. They were not re-derived; see `review/redteam-20260925/ELECTRICAL_SYSTEM.md`.
- **Pad map.** No die-pad number is used as a lead number in the bring-up documents.

## 5. Cheap on-die additions evaluated (angle 5)

None removes a BLOCKER, because none was found. For the record:

- **(a) `clk_div_out` to the `TRIP_SET` pad.**
  - The macro pin already exists (buffered, `sg13g2_buf_1`) and the pad core net `i_core_trip_set` has
    no load, so this is a top-level route plus re-signoff (DRC/antenna/density/LVS, CDL): about 8–10 h.
  - It adds a 1.2 V square wave on the north side near `VREF`.
  - It is not needed: `I(VDD)` and `OSC_CNT` already show the oscillator. **Not recommended.**
- **(b) External-clock bypass.**
  - XOR at the `osc_clk` root, with `TRIP_SET` as input and an on-chip pull-down.
  - It removes the single point of failure: a dead oscillator means no serial access, no breaker and
    no SEU test, and there is no clock input.
  - Cost about 14–18 h, including re-signoff and two chip-level re-simulations (`c_mid`, `osc`).
  - It puts an ESD-exposed thin-oxide input, which floats if the pull-down fails, on the clock of every
    flop.
  - The oscillator has a transistor-level in-loop pass and trim-reach evidence. **Recommended for run 2,
    not for r3.**
- **(c) `nf4_hold2x`** (`blocks/g1_trip/layout/candidates/nf4_hold2x/`, block DRC/LVS passed).
  - It halves the hard offset (block tt 46 → 23 LSB at code 200), cuts the corner spread from 11 to
    4 LSB and restores about 45 mV of reach. It would shrink BR-1 to BR-3.
  - Effort per its README: about half a day plus sign-off and re-simulation, about 10–14 h.
  - It is a GDS change whose decision belongs to the trip-path review. The bench works without it
    once BR-1 to BR-3 are fixed.

## 6. Not run

- Chip-level near-threshold cases at tt/−40 °C and ff/27 °C, which would split the r3x ff/−40 °C
  +12 LSB into temperature and process: **not run**. Cost about 3.3 h per run (r3x ff/−40 °C 1.15×:
  11 799 s wall).
  Command: `flow/launch_pinned.sh <cpu> designs/g1-guardian/blocks/g1_top/sim 25200 <log> python3 run_top_cdl.py c_mid --timeline compact --fault-mult 1.15 --corner tt --temp -40 --maxstep-ns 1 $C`,
  with `$C` as in `FULLCHIP_CDL_R3_CORNERS_20260927.md`.
- The chip-context mechanism behind the ff/−40 °C excess (SENSE output impedance vs BGR): **not run**.
- Digital `VDD` current with real switching activity (VCD from GLS) and its effect on the comparators:
  **not run**. Only the vectorless STA estimate above exists.
- The `VDDA`-open digital-debug state (BR-10): **not simulated**.
- ESD/latch-up at chip level, pad leakage floor, package parasitics: **not run** (unchanged from the
  spec).
- Block kick brackets at ff/125 °C and ss/27 °C: **not run**.
- Any physical measurement: **not run**.

## Evidence files (this directory)

- `kick_block/`: `queue.txt`, `brackets.jsonl`, `results.jsonl`, `table.txt`, from 66 ngspice runs.
  The raw decks, logs and waveforms (114 MB) are in `${BULK}/redteam-20260927/bringup/kick/`.
  `table.txt` sha256 `138f4222…`.
- `calmodel/`: `calsim.py`, a wrapper that runs the unmodified `g1_host` calibration against a
  code-dependent kick model, and its three outputs.
- `digital_power/`: `pwr.tcl` and `pwr.log` (OpenSTA 3.1.0 `report_power`, typ 1.20 V 25 °C,
  `osc_clk` 105.98 ns).

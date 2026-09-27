# G1 red team 2026-09-27: power sequencing, IO ring and ESD (`power_io`)

## Scope

- Supplies: `VDD` 1.2 V and `IOVDD`/`VDDA` 3.3 V.
- Power-up, power-down and brownout.
- The `EN` pin, the IO-first `GATE` constraint and reset generation.
- The `sg13g2_io` ring and the bond plan.
- Nodes that float when a domain is absent.
- Latch-up and ESD between the domains.
- The `dantenna` pad-diode model.
- The `GATE` drive.

## Chip of record and baseline

- GDS: r3, `blocks/g1_padring/layout/g1_chip_top_1414_r3.gds` (SHA-256 `7d07a784…`).
- Canonical CDL: `blocks/g1_padring/netlist/g1_chip_top_1414_r3.cdl` (`5e47ae02…`).
- Builds on `review/redteam-20260925/ELECTRICAL_SYSTEM.md` (M1, S6, N5, N6) and `PHYSICAL_TAPEIN.md`. Items closed there are not repeated here.
- Nothing here has been measured. Every number is either simulated in a run named in this record or read from a named file.

## 1. Verdict

**Yes: r3 is safe to submit as is for this aspect.**

- No finding needs a mask change.
- No on-die fix for the power-order behaviour fits 20 h without adding more risk than it removes (F1).
- The pad ring, the pin map, the GDS cell types and labels, and the bond plan agree one to one.

Two board rules are wrong or missing. The test board must be designed to the corrected rules:

- **Rule P1 is wrong.** It lets `VDD` come up "together with" `IOVDD`. With the 1–10 ms ramps of bench supplies and regulator soft-starts, that order drives `GATE` to 1.47–2.37 V for 0.5–4.2 ms while `EN` is low (F1).
- **The 3.3 V rail is unsupervised.** No rule covers it. When `IOVDD`/`VDDA` sags into about 1.5–1.8 V (up to about 2.0 V at the default hard code), `GATE` still enhances the FET while `ISENSE` saturates below the hard threshold, so the breaker is blind (F2).

Both close in the specification and on the board: about 1–2 h of document edits and no GDS change.

The mandatory independent load-bus inhibit (P2) covers every unsafe case found here. That is why the verdict is "submit". It is also why the inhibit must be real, default-off hardware on the test board, not a procedural step.

## 2. Findings

No BLOCKER was found.

| ID | Title | Severity | Evidence | Proposed fix | Effort / GDS |
| --- | --- | --- | --- | --- | --- |
| F1 | P1 ("`VDD` before **or together with** `IOVDD`", spec §6 P1, measurement B1, board checklist §2) is unsafe for ms ramps. With both rails rising in proportion and `EN` low, `GATE` follows `IOVDD` until `VDD` passes the HV-NMOS threshold of the `GATE` pad's level shifter | **MAJOR** | Reduced pad deck, 10 ms proportional ramp, `GATE` maximum and time above 1 V:<br>• tt/27 °C: 1.833 V, 2.52 ms<br>• **ss/−40 °C: 2.373 V, 4.16 ms**<br>• ff/−40 °C: 1.890 V, 0.54 ms<br>• ss/125 °C: 1.466 V, 1.41 ms<br>1 ms ramp: ≥ 1.71 V (not run to completion). The only evidence for "together" so far is `gS`: 1–3 µs ramps, 0.545 V (RESULTS §5) | P1, B1 and board checklist §2: delete "or together". Require `VDD` in regulation (≥ 1.08 V, power-good) **before** `IOVDD`/`VDDA` starts to rise. At shutdown, `IOVDD` must be below 0.5 V before `VDD` falls below 1.08 V. State that a dual-output supply with a common soft-start, or a 1.2 V LDO fed from the 3.3 V rail, violates the rule by construction | about 1 h, documents only; no GDS |
| F2 | No undervoltage rule for the 3.3 V rail. In a 3.3 V brownout to about 1.5–1.8 V (up to about 2.0 V at the default code), `GATE` = `IOVDD` keeps a logic-level FET on while the trip chain cannot reach its threshold | **MAJOR** | Static trip-chain sweep (BGR586, SENSE R100 and TRIP NF4 extractions), 45 mV (1.8×) at hard code 200:<br>• `icmp` 0.8887 V < `vth_hard` 0.8969 V at `VDDA` = 1.80 V<br>• margin +4.0 mV at 1.825 V<br>• the chain is unchanged down to 2.1 V<br>The default hard code 254 needs `ISENSE` ≈ 2.0 V, which is lost at about 2.0 V (derived). Transient sag to 1.5 V: blind for the whole sag (5.12–9.20 µs). Spec P8 and B7 supervise `VDD` only | Board: a 3.3 V supervisor (threshold ≥ 2.9 V, below the 3.0 V specification minimum) asserts the load-bus inhibit **and** drives `EN` low. The host re-enables after P4. Spec §4: breaker operation below `VDDA` = 3.0 V is undefined. Next revision: an on-die `VDDA` UVLO into the G1_GATE set input | about 1 h, documents only; no GDS (r4: UVLO) |
| F3 | `VDD` brownout: the output pads **hold** their last state rather than floating high (S6 of 2026-09-25 says they reproduce the IO-first state) | MINOR | Reduced pad deck:<br>• armed, 5 µs `VDD` dropout: `GATE` 3.300 V throughout<br>• tripped, same dip: `GATE` 0.000 V, with `trip_d` restored or lost<br>• `EN` low, `VDD` absent for 5 ms: `GATE` ≤ 22.7 mV (stock pads)<br>`por_n` is a top-level `sg13g2_tiehi` (CDL line 17903) | P8/B7: the `VDD` supervisor asserts the inhibit **and holds `EN` low until `VDD` has returned and the host has reprogrammed and read back the configuration**. Supervisor threshold ≥ 1.08 V (the lowest simulated `VDD`). Correct the S6 wording | 0.5 h, documents only; no GDS |
| F4 | A 3.3 V dropout while armed reconnects the load by itself when the rail returns. The discharged `VREF` pin capacitor then leaves the hard threshold low for about 75 µs, so the nominal load produces a spurious hard trip that is logged as a fault | MINOR | Reduced pad deck, 3 µs dropout with `VDD` and `EN` held:<br>• tripped: stays tripped<br>• armed: `GATE` back to 3.30 V<br>Analog-chain transient:<br>• `VREF` 1.0455 → 0.532 V during the dropout, still 0.713 V 109 µs after the rail returned<br>• at nominal 25 mV, `icmp` > `vth_hard` from 10.04 to 85.2 µs<br>• 1.8× fault blind from 5.08 to 11.26 µs (1.26 µs past the rail return) | Covered by the F2 rule (UV drives `EN` low; re-enable after P4). Telemetry note: a trip right after a 3.3 V glitch is a supply artefact, not a latch-up | 0.5 h, documents only; no GDS |
| F5 | The `dantenna` removal hides the pad leakage floor and the negative-excursion clamp. The kept `dpantenna` stalls slow power runs too | MINOR | Model sweep of the DCN pair:<br>• reverse current jumps 159× at 78 mV (27 °C) and 240× at 104 mV (125 °C)<br>• above the jump: 0.165 nA at 1.045 V (27 °C), 1.33 nA (125 °C)<br>Four `nodcn` power runs stopped on `dparea` of `d.xpen.xi0.xi0.xdd0.d1` (`EN` pad `dpantenna`) | Bench plan (B8, S7): the analog-pad leakage floor on `D_STD`, `D_ELT` and `HBT_*` is ≥ 1–2 nA at 125 °C (model value, DCN alone). Measure it per part on an unbiased pin. RESULTS: `nodcn` decks do not clamp negative pad excursions | 0.5 h, documents only; no GDS |
| F6 | The mandated core-first order with a slow `IOVDD` ramp puts up to 1.14 V on `GATE`. This is the M1 mechanism, now bounded at the corners | MINOR | `VDD` up, `IOVDD` over 10 ms, `EN` low, `GATE` maximum:<br>• tt/27 °C: 0.698 V (stock and `nodcn` agree to 0.1 mV)<br>• **ss/−40 °C: 1.140 V, above 1 V for 0.42 ms**<br>• ss/125 °C: 0.566 V<br>• ff/−40 °C: 0.0001 V<br>1 ms ramp at tt: 0.980 V | Add these numbers to P2 (< 100 µs 3.3 V ramp, inhibit). Board checklist, FET line: V<sub>GS(th),min</sub> at the hottest board temperature > 1.2 V, or accept that only the inhibit holds the load | 0.5 h, documents only; no GDS |

## 3. Per finding

### Common set-up

**Runner and tools.**

- ngspice-46 in the pinned container (`flow/run.sh`, image `ddeb6957…`). The runner checks the PDK commit `84374023…`.
- CPUs pinned with `G1_CPUSET` within 8–15.
- Workdir `designs/g1-guardian/blocks/g1_top/sim`. Its `.spiceinit` loads the PSP and r3_cmc OSDI models. The d_cosim runs also need `LD_LIBRARY_PATH=/foss/tools/iverilog/lib`.
- Decks, logs and waveforms are under `${BULK}/redteam-20260927/power_io/`. `${BULK}` is the bulk simulation root.
- Generator scripts and SHA-256 values: section 6.
- No tracked file was changed. The only file added is this one.
- Generic command line:
  `G1_CPUSET=<cpu> G1_CONTAINER_ENGINE=podman G1_WORKDIR=designs/g1-guardian/blocks/g1_top/sim G1_RESULTS_ROOT=${BULK}/redteam-20260927 flow/run.sh ngspice -b ${BULK}/redteam-20260927/power_io/<dir>/<case>.cir`

**Reduced power-sequencing deck ("pad deck", `pg/`, generator `scripts/mkpg.py`).**

- Pad cells: the `EN` `sg13g2_IOPadIn`, the `GATE` `IOPadOut30mA`, the `FAULT_N` `IOPadOut4mA`, and the `IOPadVdd`/`IOPadIOVdd` RC clamps. Every pad subcircuit (`G1_VSS_DERIVATIVE__*`) is copied verbatim from the `run_top_cdl.py` translation of the r3 CDL.
- The chip's G1_GATE extraction (`blocks/g1_gate/sim/postlayout/g1_gate_pex.spice`).
- The `_stock` variants restore the removed `dantenna` lines.
- G1_GATE's digital inputs are `VDD`-scaled sources (`trip_d = v(vdd)·logic`), so they collapse with `VDD` as a real core output does. `fast_en` and `hard_cmp` are held at 0.
- Supplies: 0.5 Ω and 1 nF each. `VDDA` = `IOVDD` from one source, as on the board (P3).
- FET gate network: 10 Ω + 5 nF, the fixture of every chip-level run.

### F1. Proportional ("together") ramps drive `GATE` high for milliseconds

**What I checked.** The only evidence for the "together" half of P1 is `gS` (RESULTS §5): both rails ramp in 2 µs and `GATE` peaks at 0.545 V. I repeated the case with 1 ms and 10 ms proportional ramps. `VDD` rises 0 → 1.2 V and `IOVDD`/`VDDA` 0 → 3.3 V over the same interval, with `EN` held low throughout.

| Case (`pg/`) | Corner | `GATE` max | `GATE` > 1 V | `GATE` > 0.5 V | Status |
| --- | --- | --- | --- | --- | --- |
| `sim_10ms_nodcn` | tt, 27 °C | 1.833 V at 5.55 ms (`VDD` 0.66 V) | 3.03–5.55 ms (2.52 ms) | 3.67 ms | completed |
| `sim_10ms_ssm40_nodcn` | ss, −40 °C | **2.373 V** at 7.19 ms | 3.03–7.19 ms (4.16 ms) | 4.88 ms | completed |
| `sim_10ms_ffm40_nodcn` | ff, −40 °C | 1.890 V at 5.73 ms | 5.19–5.73 ms (0.54 ms) | 0.85 ms | completed |
| `sim_10ms_ss125_nodcn` | ss, 125 °C | 1.466 V at 4.44 ms | 3.03–4.44 ms (1.41 ms) | 2.84 ms | completed |
| `sim_1ms_r2_nodcn` | tt, 27 °C | ≥ 1.71 V, still rising at `VDD` 0.62 V | from 0.30 ms | from 0.23 ms | **not run to completion** (timestep too small at 0.519 ms, `dparea` of the `EN` pad `dpantenna`; the first attempt stopped at 0.514 ms) |
| `sim_10ms_stock` | tt, 27 °C | — | — | — | **not run to completion** (stopped at 0.84 ms after about 1 h, `dantenna` stall) |

**Mechanism** (read from the waveforms):

1. In the `GATE` pad's `sg13g2_LevelUpInv`, the pull-down of the cross-coupled pair (`MN3`, HV NMOS 1.9/0.45 µm) is gated by an inverter on `VDD`.
2. Below the HV-NMOS threshold, the pair node `net4` follows `IOVDD`, `pgate` stays low, and the 2 × 99.9/0.6 µm driver PMOS pulls the pad to `IOVDD`.
3. At tt the pair flips at `VDD` ≈ 0.66 V, when `IOVDD` = 2.75 × 0.66 V ≈ 1.82 V. At ss/−40 °C the threshold is higher and the peak reaches 2.37 V.
4. This is the IO-first mechanism of P1. Ramping the rails "together" does not avoid it once the ramp is slower than the internal time constants of the pad.

**Why it matters.** A logic-level FET is fully enhanced at 1.8–2.4 V. On the bench, only the P2 inhibit keeps the load off. A board built to the letter of P1, with a dual-output supply or a common soft-start, would depend on the inhibit at every power-up without its designers knowing. The document fix costs almost nothing.

**On-die fix: considered and rejected for r3.** The cause sits inside the stock output cell: the level shifter that feeds the driver PMOS.

| Candidate | Why it does not work in the window |
| --- | --- |
| Change `c2p` | Has no effect while `VDD` is below the HV-NMOS threshold |
| Tri-state pad variant | Has the same `LevelUp` on `c2p_en` |
| Core-side pull-down on the pad net | Must beat tens of mA of PMOS drive, and `IOPadOut30mA` exposes no pad node to the core |
| Analog pad with a custom `VDDA`-domain driver and a `VDD`-good interlock | About 25–35 h for design, layout, driver ESD ballasting, re-DRC/LVS and chip re-simulation; adds ESD risk on the 30 mA pin |

This is the recommended next-revision change.

### F2. The breaker is blind in a 3.3 V brownout while the FET is still on

**What I checked.** The analog trip chain against `VDDA`, which equals `IOVDD` on the board.

- Static deck `dc/floor.cir`: the BGR586 extraction with 10 nF on `vref`; the SENSE R100 partial-C extraction with 1 Ω Kelvin leads; the TRIP NF4 extraction at hard code 200 and soft code 255.
- `VDD` held at 1.2 V. `VDDA` swept from 3.6 V down to 1.2 V in 25 mV steps, at 45, 31.25 and 25 mV of shunt.
- Run on `G1_CPUSET=15`.
- The comparator inputs `icmp` and `vth_hard` are compared statically, without the comparator kick offset.

| `VDDA` | `ISENSE` (45 mV) | `icmp` | `vth_hard` | `vref` |
| --- | --- | --- | --- | --- |
| 3.3 V | 1.9069 V | 0.9534 V | 0.8974 V | 1.0455 V |
| 2.2 V | 1.9077 V | 0.9538 V | 0.8973 V | 1.0453 V |
| 2.0 V | 1.9036 V | 0.9518 V | 0.8971 V | 1.0452 V |
| 1.9 V | 1.8668 V | 0.9334 V | 0.8970 V | 1.0451 V |
| 1.825 V | — | 0.9009 V | 0.8969 V | — |
| **1.8 V** | 1.7775 V | **0.8887 V** | **0.8969 V** | 1.0449 V |
| 1.6 V | 1.5790 V | 0.7895 V | 0.8409 V | 0.9799 V |

**Transient check** (`ach/sag15_45`, `ach/sag15_25`). Deck: the same three extractions, the `VREF` `IOPadAnalog` (`nodcn`) with 10 nF on the pin, and a 3.3 → 1.5 V sag (1 µs fall, 3 µs hold, 1 µs rise).

- 45 mV: `icmp` ≤ `vth_hard` from 5.12 to 9.20 µs, i.e. for the whole sag. The chain recovers at once, and `VREF` moves by only 6.7 mV.
- 25 mV: no lasting spurious crossing (12 samples at 9.24–9.46 µs during the rise).

**Result.**

- **Good part (clean list).** `VREF` and the DAC thresholds hold down to about 1.7 V, and the chain is unchanged down to 2.1 V.
- **Below 2.0 V.** `ISENSE` saturates about 20 mV under `VDDA`. The in-range 1.8× fault falls below the hard threshold at 1.80 V.
- **Default hard code 254.** It needs `ISENSE` ≈ 1.0 + 20 × 49.8 mV ≈ 2.0 V, so it is lost at about 2.0 V. This is derived from the saturation level, not from a separate run.
- **`GATE` in the same window.** `GATE` equals `IOVDD`, 1.5–2.0 V, because the pad pull-up is in the same domain and the digital state holding it high is on `VDD`. That voltage enhances a logic-level FET. The blind state lasts as long as the brownout does, and a current-limited bench supply in foldback or a sagging LDO input can sit there for seconds.
- **Kick offset.** The −8…−11 mV kick offset (spec §6) makes the hard path trip early. It narrows the blind band slightly and does not close it.

**Why it matters.** P8/B7 supervise `VDD` only. A 3.3 V UV supervisor on the inhibit and on `EN` closes this hole, and closes F4 as well.

### F3. `VDD` brownout: pads hold state; an armed breaker is blind; no reset on return

**Runs** (`pg/`, tt/27 °C, core-first power-up, `EN` high at 10 µs unless stated):

| Case | Stimulus | Result | Status |
| --- | --- | --- | --- |
| `vdddip5_armed_nodcn` | `VDD` 1.2 → 0 V in 1 µs, 5 µs at 0, back in 1 µs | `GATE` stays **3.300 V** throughout; `gate_o` 0.09–0.19 V; pad pair `net4` 3.300 V | completed |
| `vdddip5_trip_keep_nodcn` | tripped at 15 µs, same dip, `trip_d` restored after | `GATE` 0.000 V throughout | completed |
| `vdddip5_trip_lost_nodcn` | tripped at 15 µs, same dip, `trip_d` = 0 after (digital lost its state) | `GATE` 0.000 V throughout; the VDDA-domain G1_GATE latch keeps `q`, and `tripped` reads 1.2 V after the dip | completed |
| `vddoff5ms_enlow_stock` | `EN` low, `VDD` ramped off 20–120 µs, absent until 5 ms | `GATE` ≤ 22.7 mV for 5 ms (peak during the power-up ramp) | completed |

The `nodcn` twins of the 5 ms runs stopped at 5.4–5.7 µs on the `EN` pad `dpantenna` (not run to completion). `vddoff5ms_trip_stock` stalled at 15 µs and was stopped (not run to completion).

**Why the pads hold.** In the pad's level-shifter pair, the off PMOS (0.3 µm) leaks far less than the off pull-down NMOS (1.9 µm). With `VDD` gone, the pair keeps its last state.

**What this means.**

- The 2026-09-25 S6 statement "a `VDD` brownout reproduces the IO-first unsafe state" is not what the pads do at tt/27 °C.
- A disabled or tripped breaker stays off, which is safe. An **armed** breaker keeps the FET on with no working comparator, clock or digital core, for as long as `VDD` is out.
- When `VDD` returns with `EN` high, nothing resets the core:
  - `por_n` is tied high at the top level: `Xi_core_u_digital_1 net VDD VSS / sg13g2_tiehi`, CDL line 17903.
  - The r3 EN deglitch acts only on an `EN`-low history.
- The digital state after a real `VDD` loss is therefore undefined. That covers the registers, `trip_d`, a possible `clr_d` pulse and inrush.
- The RTL co-simulation cannot show this state: the `d_cosim` flops keep their values and the bridges drive 1.2 V whatever `VDD` does.
- The existing P8/B7 supervisor asserts the inhibit on `VDD` UV and covers the first part. The rule for recovery is missing.

**Not run:** retention at 125 °C (roughly 30× the leakage) and beyond 5 ms.

### F4. `IOVDD`/`VDDA` dropout with `VDD` held

**Pad deck** (`pg/iodrop_*`, 3.3 → 0 V in 1 µs, 3 µs at 0, back in 1 µs, from 20 µs):

| Case | Result |
| --- | --- |
| Tripped (`iodrop_trip_nodcn`) | `GATE` stays 0.000 V. `trip_d` is a level held by the core (RTL `g1_digital_top.v`: "set (level = digital latch state)"), and it re-sets the G1_GATE latch when `VDDA` returns. `en_i` stays 1.2 V (the `LevelDown` node holds charge) |
| Armed (`iodrop_armed_nodcn`) | `GATE` follows the rail down: 1.38 V at `IOVDD` 0.34 V, then 0.38 V. It returns to 3.30 V as the rail recovers, with no `EN` edge and no inrush mask |

**Analog-chain transient** (`ach/drop0_45`, `ach/drop0_25`). Deck as in F2 with a 3 µs dropout to 0 V.

- **`VREF` pin capacitor.** The 10 nF on the `VREF` pin discharges into the collapsing rail through the pad's DCP and secondary diodes.
  - The on-chip `VREF` falls from 1.0455 V to 0.532 V at 9 µs.
  - It then recovers only through the BGR output resistance (22 kΩ × 10 nF): 0.548 V at 12 µs, 0.610 V at 50 µs, 0.713 V at 119 µs.
- **Threshold shift.** The pedestal and the DAC thresholds scale with `vref_buf`, but 20 × V<sub>shunt</sub> does not, so the hard threshold sits low.
  - At nominal 25 mV, `icmp` > `vth_hard` from 10.04 to 85.2 µs (+44 mV at 12 µs).
  - With inrush masking not re-opened, the hard path (`HARD_N` = 4) will trip the nominal load and record it as a hard-fault trip.
- **Blind interval at 1.8×.** From 5.08 to 11.26 µs, which is 1.26 µs past the rail return.
- **Scaling.** With 100 nF on the pin (P5 option) the low-threshold window scales to about 0.75 ms. That is derived, not run.

**Severity: MINOR.** The failure is in the safe direction (a spurious trip), but it corrupts the event telemetry. The F2 rule (UV drives `EN` low, re-enable after P4) removes it.

The full-chip version was attempted and stopped (section 5).

### F5. What the `dantenna` deviation hides

**What I checked.** The PDK `dantenna` reverse characteristic with the `sg13g2_DCNDiode` geometry (2 × w 1.26 µm × l 27.78 µm). Deck `diode/dant.cir`, `dio_tt`, a DC sweep of the cathode from −0.3 V to +1.2 V at 27 °C and 125 °C.

| T | Below the jump | Jump | Above the jump | At 1.045 V |
| --- | --- | --- | --- | --- |
| 27 °C | 0.47 pA at 78 mV | ×159 between 78 and 79 mV | 74.7 pA at 80 mV | 165 pA |
| 125 °C | 3.2 pA at 103 mV | ×240 between 103 and 104 mV | 759 pA at 105 mV | 1.33 nA |

The step sits at 3·n·V<sub>T</sub>. It is a switch between two model formulas, not physics. It stalls any transient in which a pad crosses it, which is why every r3 chip deck removes `dantenna`. Removing it hides three things:

1. **Negative pad excursions.** No DCN diode clamps them, so no chip run bounds undershoot on `SENSE_N`, `GATE` or the device pins. The fixtures have no inductance, and none occurred.
2. **The leakage floor of the analog pads.** It does not matter for the breaker: at `VREF`, 1.3 nA × 22 kΩ ≈ 30 µV. It does matter for the `D_STD`/`D_ELT` off-current and the `HBT_B` base-current measurements at 125 °C. The DCN pair alone gives about 1.3 nA there, before the DCP diodes and the `Clamp_N20N0D` drain junction are added.
3. **Power-up latch resolution.** M1 showed one stock-pad corner resolving differently. In this round, stock and `nodcn` agree to 0.1 mV where both complete (`cf_io10ms`: 0.6976 V in both).

**The kept `dpantenna` diodes stall too.** They stopped four `nodcn` power runs ("trouble with dparea-instance d.xpen.xi0.xi0.xdd0.d1"). The `nodcn` label is therefore not a numerical guarantee for slow ramps. The stock-pad slow runs did not complete either (section 5).

### F6. Core-first with a slow `IOVDD` ramp (the mandated order)

**Runs.** `cf_io10ms`: `VDD` up in 100 µs, then `IOVDD`/`VDDA` ramps over 10 ms from 0.2 ms, with `EN` low. `cf_io1ms`: the same with a 1 ms ramp.

| Run | Corner | `GATE` max | Duration / note |
| --- | --- | --- | --- |
| `cf_io10ms` | tt/27 °C | 0.698 V | > 0.5 V for 0.25 ms; `nodcn` and stock identical |
| `cf_io10ms` | ss/−40 °C | **1.140 V** | > 1 V for 0.42 ms; `en_i` reached 1.183 V (`EN` read "enabled") |
| `cf_io10ms` | ss/125 °C | 0.566 V | — |
| `cf_io10ms` | ff/−40 °C | 0.0001 V | — |
| `cf_io1ms` | tt/27 °C | 0.980 V | > 0.5 V for 74 µs |

This is the M1 mechanism (floating `EN` `LevelDown`, undefined G1_GATE latch) with numbers at the corners. P2 already addresses it: a < 100 µs 3.3 V ramp plus the inhibit. The new information is the size: up to 1.14 V for 0.4 ms. Logic FETs specified with V<sub>GS(th)</sub> ≈ 1 V, lower when hot, can conduct at that level.

## 4. Checked and clean

- **Pin map, one to one.** Four sources agree for all 24 pads:
  - spec §3 (die pad, lead, net, cell);
  - the r3 CDL pad instances (`Xpad01_vdd` … `Xpad24_hbt_c`, lines 17914–17937);
  - the GDS IO-cell instance at each pad position, from KLayout `scripts/padcells.py` → `padcells.json`;
  - the 22 `134/25` labels at the opening centres.

  | Side | Cells in the GDS, in pad order |
  | --- | --- |
  | South | `IOPadVdd`, `IOPadVss`, `IOPadIOVdd`, `IOPadIOVss`, `IOPadVss`, `IOPadIOVss` |
  | East | `Analog` ×3, `Out30mA`, `Out4mA`, `In` |
  | North | `Analog`, `In`, `In`, `Out4mA`, `Out16mA`, `Analog` |
  | West | `Analog` ×6 |

  The two unlabelled pads are the second `VSS` (843, 101) and the second `IOVSS` (955, 101).
- **Bond map r4 against spec and board.** `bondmap_20260926_r4.csv` die pad → QFN24 lead matches spec §3 and BOARD_CHECKLIST §1: 13–18 → 18–13 and 19–24 → 24–19. The geometry is consistent with a 90° clockwise die rotation, with GDS south facing leads 1–6.
- **Ring inventory.** 4 `sg13g2_Corner`, 112 fillers and 24 bondpads. There is one IO supply domain and no breaker or cut cells. `VDDA` enters only through the bare terminal of pad 7.
- **`63/0` registration texts.** They now read 1414 × 1414 µm, 1.999396 mm² and PDK `84374023…`. The r1 finding is closed on r3.
- **Supply clamps.** Both are stock RC clamps: the `VDD` clamp (`Clamp_N43N43D4R` to `IOVSS`) and the `IOVDD` clamp.
- **`GATE` driver.** 2 × 99.9/0.6 µm HV PMOS and 66/0.6 µm HV NMOS (`Clamp_P15N15D` / `Clamp_N15N15D` in the CDL). Into 10 Ω + 5 nF, `GATE` falls below 1 V 0.27–0.56 µs after `tripped` (r3 full-chip record). The output high level equals `IOVDD`, minimum 3.0 V.
- **Trip chain against a 3.3 V sag (static).** Unchanged down to 2.1 V: `VREF` moves 0.2 mV and `ISENSE` 0.8 mV between 3.6 V and 2.2 V at 45 mV (`dc/floor_45m.txt`). A 3.3 V sag that stays above about 2.1 V does not blind the breaker.
- **Loss of `VDD` while disabled or tripped.** `GATE` stays low: tt/27 °C, 5 µs (tripped) and 5 ms (`EN` low, stock pads) (F3).
- **3.3 V dropout while tripped.** The breaker stays tripped: `trip_d` is a level and re-sets the G1_GATE latch (F4).
- **`por_n` source.** A single top-level tie cell feeds the macro's `por_n` pin. A future POR can replace it with a top-level edit, without re-hardening the macro.
- **Cross-domain crossings.** No crossing lands a signal from one supply domain on a junction in the other, in either power order. `g1_lvlup`, `g1_lvldn`, `g1_ls_up`, `g1_tlvlup` and the pad `LevelUp`/`LevelDown` all drive gates only (N6 of 2026-09-25, rechecked against the r3 CDL cells).

## 5. Not run

- **Full-chip r3 CDL deck through a 3.3 V dropout.** Three cases were built from the r3 `c_mid` compact deck (`--netlist pex --interconnect extracted --rtl-dir eco_20260925`) with `V33` replaced by a dip: `fc/armed_io0` (0 V), `fc/armed_io2` (2.0 V) and `fc/trip_io0`.
  - Once the rail started to fall, the solver slowed to roughly 3 000 s per simulated µs.
  - They were stopped at 13.14 µs, 13.1 µs and 11.9 µs, at or before the start of the dip.
  - **Not run to completion.** No result is claimed. The block-level transients of F2/F4 stand in for them.
- **Any `VDD` dip with the gate-level digital.** The post-brownout digital state is not simulated (F3).
- **Pad level-shifter retention** at 125 °C, and without `VDD` for longer than 5 ms.
- **Stock-pad (`dantenna`) versions of the slow and dip runs.** `sim_10ms_stock`, `cf_io1ms_stock`, `vdddip5_armed_stock`, `vdddip5_trip_keep_stock` and `vddoff5ms_trip_stock` were stopped after 15–60 min, stalled at 1.4 µs to 0.84 ms. Not run to completion. `vdddip5_trip_lost_stock`: not run.
- **Trip-chain transients at corners** (only tt/27 °C), and with 0 nF or 100 nF on `VREF`.
- **ESD (HBM/CDM) on any pin pair.** Open concerns:
  - `VDDA` → `VSS` has no local clamp; its path is DCP → `IOVDD` clamp → `IOVSS` → substrate.
  - The `VDD` clamp discharges into `IOVSS`, and `VSS` and `IOVSS` meet only through the substrate.
  - `G_SHARED` is a bare thin gate.
- **Latch-up / SEL** beyond the DRC `LU.*` rules.
- **`EN` toggling during a ramp.** Not run because it is by design: `EN` high commands `GATE` at whatever `IOVDD` is, and P6 requires `EN` low.
- **`VDD` bounce at the comparator strobe** (S2 of 2026-09-25): still not run, because the digital supply current is not modelled.
- **Package and bond-wire inductance** in any power case.

## 6. Evidence

All files are under `${BULK}/redteam-20260927/power_io/` and are not committed: the waveforms are larger than 300 kB, and the decks carry absolute container paths. The first 16 hex digits of each SHA-256 are listed.

| File | SHA-256 (16) | What |
| --- | --- | --- |
| `scripts/padcells.py` | `d6902d7b26f4bd48` | KLayout: IO-cell instances and top labels of r3 |
| `padcells.json` | `10a39dce7724884e` | its output |
| `scripts/mkpg.py` | `6c282a07beba347f` | pad-deck generator (all `pg/` cases) |
| `scripts/mkcorner.py` | `f32232a6c629eb83` | corner variants of `sim_10ms` and `cf_io10ms` |
| `scripts/sum_pg.py` | `22421b2c57432b93` | pad-deck summary (the numbers in F1, F3, F4, F6) |
| `scripts/an_ach.py` | `5ebdd300350c18a7` | analog-chain transient summary (F2, F4) |
| `scripts/mkdecks.py`, `scripts/compile_rtl.py` | `4c30e48e32caf1fd`, `be433ec8a11fa55c` | full-chip dip decks (stopped) and the ECO RTL compile |
| `dc/floor.cir`, `dc/floor_45m.txt` | `d2a0e34ca8f5ead1`, `ae8be6229e37b0ce` | F2 static sweep |
| `diode/dant.cir`, `dant_27.txt`, `dant_125.txt` | `73c063f4d70187db`, `d303d19ea808e3b6`, `927dea22b30f2722` | F5 |
| `ach/drop0_45.txt`, `drop0_25.txt`, `sag15_45.txt`, `sag15_25.txt` | `48e7631ec44a1b6c`, `2d69b5085d4b2598`, `7784bcd64f685d26`, `6844670c79bc1a51` | F2, F4 transients (decks `ach/*.cir` alongside) |
| `pg/sim_10ms_nodcn.txt`, `_ssm40_`, `_ffm40_`, `_ss125_` | `46f0bdc5a05b184b`, `ef611057f8404e2b`, `7cdd3a12772f3af3`, `6d6fe458c69f8d00` | F1 |
| `pg/sim_1ms_r2_nodcn.txt` | `f0a1d9c432328ce6` | F1 (not run to completion) |
| `pg/cf_io10ms_nodcn.txt`, `_stock`, `_ssm40_`, `_ffm40_`, `_ss125_`, `pg/cf_io1ms_nodcn.txt` | `642d3bc170bce610`, `a4a964ef6d293753`, `a99f64399402eb94`, `150347451b57625f`, `31d080c58e545e04`, `cfe3cebacc808f0c` | F6 |
| `pg/vdddip5_armed_nodcn.txt`, `vdddip5_trip_keep_nodcn.txt`, `vdddip5_trip_lost_nodcn.txt`, `vddoff5ms_enlow_stock.txt` | `7e8b65666f3370f2`, `7b691ae95fe7c8ab`, `e93891debe298787`, `e6ce9fac7d4ce9a1` | F3 |
| `pg/iodrop_trip_nodcn.txt`, `pg/iodrop_armed_nodcn.txt` | `b942ebc533baec44`, `36e0f44ed8400b03` | F4 |
| `fc/armed_io0.cir`, `armed_io2.cir`, `trip_io0.cir` | `0169c4f4979f5d44`, `32f240d985f5e9cb`, `90fb7d09829d4193` | full-chip dip decks (not run to completion) |

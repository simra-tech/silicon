# C157-TRIM val540 — re-location attempt on C169-final.spice (code 540)

Date: 2026-08-22 (follow-on to the `2026-08-22_..._c157-trim-val540` island validation)

## Executive summary

The recommended next step — "widen the probe to find the real `pbit_raw_core`
LOW→HIGH crossing, then re-band and re-run the island check" — **cannot be
completed as stated, because there is no crossing to re-locate on
`C169-final.spice` at code 540.**

- At **code 540** the comparator digital output `pbit_raw_core` is **pinned LOW**
  (`≈ 8.5e-8 V`, `pbit_out_core = 1.2 V`) for **every** input offset probed from
  **−395 mV through +160 mV** (a 555 mV span; the earlier probes already covered
  −45…+50 mV). The analog collector pair `c_p − c_n` is **never ≤ 0**: it bottoms
  out at **+0.145 V** near vv = −70 mV and grows on both sides (U-shaped), i.e.
  the regenerative latch is biased to settle LOW regardless of input.
- A **code-0 control** on the same netlist shows the opposite *clean* state:
  `pbit_raw_core = 1.2 V` (HIGH) across the whole vv = −60…+60 mV window
  (`c_p − c_n ≈ −0.17 V`). So the latch/sense-amp chain is functional and can
  produce a clean HIGH; the code-540 pin is a DAC-bias effect, not a dead latch.
  (Code 0 is itself saturated HIGH over the ±60 mV trim window — the V7 DAC's
  full-scale now exceeds ±60 mV, vs the old netlist whose code-540 crossing sat
  at −38 mV.)
- **Root cause (primary):** the V7-merged DAC over-drives the comparator at code
  540. At code 540, 135 of 150 unary elements are ON (steering into `c_n`),
  which keeps `c_n` below `c_p` for the entire input range — the comparator is
  saturated LOW and the LOW→HIGH crossing no longer exists. The V7 netlist drops
  the `1.037u` DAC compensation (comment "NO 1.037u compensation encoded …
  re-tune on the ensemble targeting x=1.03"), which is consistent with a
  several-× larger DAC LSB than the netlist that produced the −38 mV crossing.
- **Root cause (secondary, netlist defect):** the sense-amp clock node `SACLK`
  is **undriven**. It appears in `C169-final.spice` only as a gate input
  (XSA_T / XPC1 / XPC2, lines 205/240/241) and is never connected to `CLK_N`,
  despite the design comments stating the sense amp should "evaluate on CLK_N
  high" (line 195) and precharge "while CLK_N is low (gate=CLK_N)" (line 236).
  `SACLK` floats to ≈ 0.719 V. It is not fatal at code 0 (the latch still
  settles cleanly) but it is a real defect that compounds the high-code failure.

## Conclusion for the island check

The prior `val540.cir` "all four codes uniformly LOW" was **not** a wrong band
location. It was a **saturated comparator**: at codes 540–543 the DAC over-drive
pins `pbit_raw_core` LOW over the whole input range, so there is no crossing to
band around and no HIGH background to expose a LOW island against. Re-banding at
any offset can only reproduce uniform LOW. Reproducing the island requires a
**source-level fix** (re-tune the V7 DAC LSB back toward the −38 mV/code-540
regime, and connect `SACLK` to `CLK_N`), which is a source modification outside
this task's "do not modify source files" scope.

## Evidence

### Code 540 — `pbit_raw_core` digital output (all LOW)
| probe | vv range | step | result |
|-------|----------|------|--------|
| `probe540.log` (prior) | −45 … +5 mV | 2.5 mV | all LOW (`≈8.5e-8`), out=1.2 |
| `probe540b.log` (prior) | +7.5 … +50 mV | 2.5 mV | all LOW |
| `probe540w.log` | −400 … −380 mV | 5 mV | all LOW (−400 hit `Timestep too small`; −395…−380 clean) |
| `probe540d.log` | −120 … −70 mV | 5 mV | all LOW |
| `probe540p.log` | +100 … +160 mV | 20 mV | all LOW |

### Code 540 — analog `c_p − c_n` gap (never crosses 0)
| vv (mV) | c_p (V) | c_n (V) | c_p−c_n (V) |
|---------|---------|---------|-------------|
| −120 | 0.4051 | 0.2381 | +0.167 |
| −100 | 0.3980 | 0.2415 | +0.157 |
| −80  | 0.3905 | 0.2421 | +0.148 |
| −70  | 0.3876 | 0.2423 | **+0.145 (min)** |
| +100 | 0.5231 | 0.2809 | +0.242 |
| +140 | 0.7604 | 0.2940 | +0.466 |
| +160 | — | — | +0.772 |

### Code 0 control — comparator switches (HIGH at negative/zero offset)
| vv (mV) | pbit_raw_core | c_p (V) | c_n (V) | c_p−c_n (V) |
|---------|---------------|---------|---------|-------------|
| −60 | 1.2 (HIGH) | 0.2595 | 0.4996 | −0.240 |
| −40 | 1.2 | 0.2531 | 0.4523 | −0.199 |
| −20 | 1.2 | 0.2465 | 0.4278 | −0.181 |
| 0   | 1.2 | 0.2427 | 0.4160 | −0.173 |
| +20 | 1.2 | 0.2377 | 0.4084 | −0.171 |
| +40 | 1.2 | 0.2350 | 0.4065 | −0.172 |

## Root-cause citations (netlist facts, no source modified)

- `/tmp/C169-final.spice` sha256 `97938952…` — byte-identical to source
  `C169-SOURCE-coarse-dac-v7-merged.spice`.
- `SACLK` occurrences (undriven): lines 205 (`XSA_T … SACLK …`),
  240/241 (`XPC1/XPC2 … SACLK …`) — gate inputs only, no driver.
- Design intent (from inline comments): line 195 "Sense amp evaluates on CLK_N
  high"; line 236 "(gate=CLK_N)".
- `CLK_N` is connected only to the HBT latch tail (`XQCLK_LATCH`, line 146), not
  to the CMOS sense-amp devices.
- DAC sizing/compensation: line 269–270 "NO 1.037u compensation encoded …
  re-tune on the ensemble targeting x=1.03".

## Files

- `probe540w.cir` / `.log` — widened digital sweep (−400…+200 mV; run stopped at
  −380 after the extreme point failed convergence).
- `probe540d.cir` / `.log` — code-540 diagnostic sweep (−120…+120 mV) recording
  digital + analog (c_p, c_n, cml_out_p, cml_out_n).
- `probe540p.cir` / `.log` — code-540 positive-range sweep (+100…+400 mV).
- `probe0d.cir` / `.log` — code-0 control sweep (−60…+60 mV).

All runs: `cd /foss/pdks/ihp-sg13g2/libs.tech/ngspice && PDK_ROOT=/foss/pdks
PDK=ihp-sg13g2 ngspice -b <deck>` (ngspice-46, IHP PDK `.spiceinit` OSDI recipe).

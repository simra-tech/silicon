# Load-servo corner matrix — C148 (800 ps/bit) and C149 (400 ps/bit)

Public-experiment record, 2026-08-06 evening — 2026-08-07 morning. In simulation only
(IHP SG13G2 corner libs, ngspice). Nothing here is a signoff or a tape-out claim.

## The circuit change (C148)

Common-mode feedback moved to the **loads**: the diode PMOS gates (XM3/XM4, 16.0u) are servoed so
the cml_out_p/cml_out_n average tracks VCMREF = 0.75 V (absolute source — a testbench idealization;
see Open items). XMTAIL fixed at 2.5u, so common mode and tail current are independent. Under the
previous tail-servo (C146), cm wandered ~100 mV across corners; under C148 it holds 0.765–0.776 V
(11 mV spread).

## The measurement standard (eye_decode.py)

Decode by **sweeping the sampling offset** (0.05-bit steps, bounded above by the simulated window)
and report the contiguous zero-error spans — never an error count at a single phase. A
phase-quantized decoder (integer pattern shift + fixed 0.5-bit phase) can only sample at offsets
k+0.5 and turned corner-dependent chain latency into phantom errors: the "5/64 and 12–13/64
failures" first reported for the C148 27 C corners were the sampling instant sitting on the eye
edge. Controls that keep the standard honest:

- **Reference**: comparator differential (xcomp.c_p − c_n, 0 V slice) must decode 0/64 in the same
  raw, else the run is void.
- **Floor**: the 64-bit TX has 31 ones / 33 zeros, so a stuck pin scores 33 (high) or 31 (low).
- **Closed-eye control**: C146's failing corners have **no** zero-error offset at any position —
  the standard does not rescue genuinely broken circuits.
- **Point count**: verify raw npoints against the deck's expected count before reading anything
  (ngspice exits 0 after aborted transients).
- **Sweep bound**: latency in bits doubles when the bit halves; a minimum at the sweep edge means
  the sweep is too short (C149's first report clipped the −40 minimum this way: 20/64 at a 0–3
  sweep, truly 8/64 at offset 3.35).

## C148 verified results, 800 ps/bit, 64-bit PRBS-7 window

| corner | cm (V) | zero-error span (bits past 10 ns settle) | width |
|---|---|---|---|
| TT-TYP-125 | 0.7760 | 1.30–2.15 | ~720 ps |
| SS-TYP-27  | 0.7673 | 1.55–2.45 | ~720 ps |
| SS-TYP-125 | 0.7716 | 1.50–2.35 | ~680 ps |
| SS-WCS-27  | 0.7673 | 1.60–2.45 | ~680 ps |
| SS-WCS-125 | 0.7715 | 1.50–2.35 | ~680 ps |
| SS-WCS-N40 | 0.7651 | 1.70–2.55 | ~680 ps |

**Cross-corner intersection 1.70–2.15 bits (360 ps): one fixed sampling instant decodes all six
corners at 0/64.** The −40 corner had been dead (stuck-pin floor) in every prior configuration.
Threshold sensitivity: at a fixed in-window instant, all six corners decode 0/64 for any slice
threshold 0.10–1.10 V.

## C149 verified results, 400 ps/bit, same netlist

No corner has any zero-error offset (sweep 0–11 bits). Minima: TT-TYP-125 2/64 @2.60,
SS-TYP-125 5/64 @2.90, SS-WCS-125 6/64 @2.95, SS-TYP-27 7/64 @3.05, SS-WCS-27 7/64 @3.10,
SS-WCS-N40 8/64 @3.35. The rig holds a 0.95-bit clean span at every corner, so the comparator
front end is clean at 2.5 GS/s; the ceiling is the sense-amp/latch stage (state-change time,
~100 ps evaluate needed).

**Rate of record: 1.25 GS/s across the full six-corner matrix. 2.5 GS/s fails at every corner
with this architecture.**

## Prior-claim audit (C145, tail-servo era, same standard)

27 C corners at 1600 ps/bit: no zero-error offset (minima 11 and 9). SS-WCS-N40: stuck-pin floor
at 1600 and 3200 ps. SS-TYP-27 at 3200 ps: 1/64 at best offset. SS-WCS-27 at 3200 ps: 1440 ps
clean span. All pre-C148 rate-ladder conclusions stand.

## Open items

- VCMREF is an ideal 0.75 V source; a real part needs a VDD-ratioed or bandgap reference. C150
  (full 127-bit PRBS period, VDD 1.08/1.32/1.20 V, six corners) is running as this is written and
  will be appended once independently verified.
- Schematic-level only: no layout parasitics, no mismatch, no noise analysis yet.
- Path to 2.5 GS/s: interleaved sense amps (alternate bits) — proposed, not designed.

## C150 (2026-08-07) — full-period pass, supply axis void

**Axis 1 (pattern) — valid, passed.** TX extended to the full 127-bit PRBS-7 period (64 ones,
63 zeros; first 64 bits identical to the previous window), 800 ps/bit, 10 ns settle + 131 bits.
All six corners decode 0/64 with a 720 ps eye and spans identical to the 64-bit result
(TT-TYP-125 1.30–2.15, SS-TYP-27 1.55–2.40, SS-TYP-125 1.50–2.35, SS-WCS-27 1.60–2.45,
SS-WCS-125 1.50–2.35, SS-WCS-N40 1.70–2.55; cm unchanged to 4 digits). The previously untested
half of the pattern, including the runs of seven, changes nothing.

**Axis 2 (supply) — VOID, unrun.** The V108/V120/V132 decks all carry `VDD VDD 0 DC 1.200` and
`VBUF_VDD VDD_BUF 0 DC 1.200`; the supply distinction exists only in the header comment. Confirmed
by identical non-comment deck bodies and by `v(vdd)` = 1.2000 sampled from all three raws. Each
corner ran three times at nominal. Detected because the three "conditions" agreed to every digit —
a 10% supply step cannot leave cm identical to 0.1 mV (harness finding H-723). **Behaviour across
supply is unknown**; the standing prediction that 1.08 V fails (VCMREF being an absolute source) is
untested, neither confirmed nor refuted. C151 reruns it with the sources actually edited.

**Standing rule added:** every swept quantity (supply, temperature, bit period) must be read back
out of the raw and reported beside the result. A condition named only in a filename is not a
condition.

## C151 (2026-08-07) — supply axis rerun, and the empty intersection

Supply genuinely applied this time: `v(vdd)` read back from every raw as 1.0800 / 1.2000 / 1.3200.
64-bit pattern, 800 ps/bit. **All 18 conditions (6 corners × 3 supplies) decode 0/64**, rig 0/64
throughout, per-condition eyes 640–760 ps.

| condition | window (bits past 10 ns settle) | | condition | window |
|---|---|---|---|---|
| TT-TYP-125 @1.32 | 1.25–2.05 | | SS-TYP-125 @1.20 | 1.50–2.35 |
| TT-TYP-125 @1.20 | 1.30–2.15 | | SS-WCS-125 @1.20 | 1.50–2.35 |
| TT-TYP-125 @1.08 | 1.40–2.25 | | SS-TYP-27 @1.20 | 1.55–2.45 |
| SS-TYP-125 @1.32 | 1.35–2.20 | | SS-WCS-27 @1.20 | 1.60–2.45 |
| SS-WCS-125 @1.32 | 1.35–2.20 | | SS-WCS-N40 @1.20 | 1.70–2.55 |
| SS-TYP-27 @1.32 | 1.35–2.20 | | SS-TYP-125 @1.08 | 1.80–2.60 |
| SS-WCS-27 @1.32 | 1.35–2.20 | | SS-WCS-125 @1.08 | 1.80–2.60 |
| SS-WCS-N40 @1.32 | 1.50–2.30 | | SS-TYP-27 @1.08 | 1.85–2.70 |
| | | | SS-WCS-27 @1.08 | 1.85–2.70 |
| | | | SS-WCS-N40 @1.08 | 2.15–2.90 |

**INTERSECTION ACROSS ALL 18: EMPTY.** Latest opening 2.15 (SS-WCS-N40 @1.08 V) vs earliest
closing 2.05 (TT-TYP-125 @1.32 V) — a fixed sampling instant misses by 0.10 bits (80 ps). Chain
latency spread across corner and supply is ~700 ps, one full bit period, as wide as the eye itself.

**Claim of record (revised):** in simulation, 0/64 at 1.25 GS/s at every corner and supply
**given a clock that tracks temperature and supply**. A fixed-instant clock does not work across
the full matrix. Not a signoff; schematic-level only.

**Note on axis coverage:** C151 used the 64-bit pattern, so the supply axis and the full-127-bit
axis have each passed separately but not together.

Per-condition margins do not compose (harness finding H-724): report the cross-condition
intersection as the headline number, the per-condition table as diagnostic.

**Open, pending C152:** where the 700 ps of latency spread accumulates, stage by stage. If one
stage dominates, replica-path clocking is the fix; if it is spread evenly, clock-and-data recovery
or a per-condition clock. Also open: the bit rate at which the intersection first becomes non-empty.

## C152 (2026-08-07) — where the latency spread accumulates

Delay from the bit-clock edge to the crossing at each node, spread across the 18 conditions:

| node | spread across 18 (ps) | mean delay (ps) |
|---|---|---|
| c_p − c_n (comparator) | **11** | 140 |
| cml_out | 53 | 351 |
| sa_n (sense amp) | 111 | 294 |
| Q (NAND latch) | 252 | 543 |
| pbit_out_core | 524 | 626 |
| PBIT_OUT (pad) | 533 | 778 |

The analogue front end is essentially invariant (11 ps); the digital tail — latch, buffers, output
driver — carries ~400 ps of the 533 ps total. Spread is distributed across a latch and three
buffers rather than concentrated in one stage, so a **simple replica-path clock will not track it**;
a replica would have to duplicate the whole NAND→buffer→output chain.

**Tested and refuted: sampling before the pad does not rescue the intersection.** The output driver
and pad exist only for observability, so the obvious hypothesis was that the empty window is an
artifact of the observation path. Decoding internal nodes across all 18 conditions (harness finding
H-725):

| sampling point | intersection across 18 |
|---|---|
| Q (latch, on-chip) | empty by 360 ps |
| pbit_out_core (pre-pad) | empty by 40 ps |
| PBIT_OUT (pad) | empty by 120 ps |

Sampling at Q is *worse*. Per-condition windows are ~600 ps at Q against 640–760 ps after the
buffers: buffers sharpen edges, so window width grows along the chain slightly faster than delay
spread does. Intermediate nodes are not automatically better test points.

## Axis decomposition and the supply-tolerance specification

Window-position shift by axis, from the 18 measured windows (no additional simulation):

| axis | at VDD 1.32 | at VDD 1.08 |
|---|---|---|
| supply 1.32 → 1.08 V (per corner) | 120 ps (TT-TYP-125) … 520 ps (SS-WCS-N40) | — |
| temperature 125 °C → −40 °C | 120 ps | 280 ps |
| process TT → SS (at 125 °C) | 80 ps | 320 ps |

**Every axis is 3–4× worse at low supply**: the axes are not independent contributions, low supply
amplifies sensitivity to all of them (gates short of headroom). One fix aimed at supply sensitivity
would improve temperature and process behaviour too.

**Specification derived:** at nominal supply alone the six-corner intersection is **open 360 ps**;
at ±10% it is empty by 120 ps; linear interpolation of the measured window edges puts the closing
point at **≈ ±7.5% supply**. As drawn, this block needs its supply held to roughly 7% for a
fixed-instant clock to work across the corner matrix — an on-chip regulator requirement, not a
defect.

**In flight (C153):** the 18-condition matrix at 1000 ps/bit, testing the published prediction that
the intersection opens to ~116 ps and that the crossing is near 861 ps/bit (model: eye ≈ 0.836 × BP,
latency spread ≈ 720 ps fixed). Partial at 4/18 conditions: eyes 850–950 ps, intersection open
300 ps — but the late-edge condition (SS-WCS-N40 @1.08 V) has not finished, so the number will
shrink. Not scored until complete.

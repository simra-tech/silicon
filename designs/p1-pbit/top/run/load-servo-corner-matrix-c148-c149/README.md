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

## C153 (2026-08-07) — 1000 ps/bit: the first composable result

All 18 conditions (6 corners × 1.08/1.20/1.32 V), 127-bit PRBS-7, 1000 ps/bit. Rig 0/127 and
output 0/127 at every condition; per-condition eyes 850–950 ps.

**INTERSECTION OPEN 150 ps** — late open SS-WCS-N40 @1.08 V at 1.65 bits, early close
TT-TYP-125 @1.32 V at 1.80 bits. A single fixed sampling instant decodes the full pattern at every
corner, over 165 °C, with the supply ±10%.

**Prediction scored.** Published before the runs existed, from the 800 ps/bit windows alone
(eye ≈ 0.836 × BP, latency spread ≈ 720 ps fixed): +116 ps. Measured: **+150 ps**, an error of
34 ps on a quantity that moved 270 ps between the two rates. The model's assumptions were both
slightly wrong in opposite directions — the spread shrank to 650 ps rather than staying fixed (part
of it is tied to the decision schedule, not propagation), while the eye grew to ~0.90 × BP — and the
errors largely cancelled. Predicted crossing 861 ps/bit; interpolating the two measured
intersections (−120 ps at 800, +150 ps at 1000) puts it at **≈889 ps/bit**.

### Claim of record (2026-08-07, supersedes all earlier rate claims)

> In simulation: 0/127 errors from a **single fixed sampling instant** across six process/temperature
> corners × three supplies (±10%), full PRBS-7 period, at **1.0 GS/s**, with 150 ps of shared
> margin. Fixed-clock operation fails above ≈1.12 GS/s; per-condition operation reaches 1.25 GS/s
> but does not compose.

Still schematic-level: no layout parasitics, no device mismatch, no noise analysis, VCMREF an ideal
source. Not a signoff, not a tape-out claim.

**Next (C154):** strengthen the digital tail (NAND latch + three buffer stages, which carry ~400 ps
of the 533 ps spread), rerun the 18-condition matrix at 800 ps/bit, target making 1.25 GS/s
composable.

## Derived design trade-off — supply regulation vs achievable fixed-clock rate

From the measured window edges at 800 and 1000 ps/bit (linear interpolation of edges in VDD; no
additional simulation):

| supply tolerance | shared margin @800 ps | @1000 ps | max fixed-clock rate |
|---|---|---|---|
| ±0% (perfect) | +360 ps | +550 ps | >1.25 GS/s |
| ±2.5% | +240 ps | +450 ps | >1.25 GS/s |
| ±5% | +120 ps | +350 ps | >1.25 GS/s |
| ±7.5% | 0 ps | +250 ps | ≈1.25 GS/s (boundary) |
| ±10% | −120 ps | +150 ps | 1.13 GS/s (889 ps/bit) |

**Sampling-instant specification.** At ±10% supply and 1000 ps/bit: sample at **1.725 bits past the
settle reference, ±75 ps**. At nominal supply and 800 ps/bit: 1.925 bits, ±180 ps. That tolerance is
the whole budget for clock jitter, distribution skew, and edge-placement error — and none of
mismatch, extracted parasitics or noise has been charged against it yet.

**Reading:** the rate is not a property of the circuit alone. Behind a dedicated on-chip regulator
(±5% or better) the 1.25 GS/s rate is composable; on a raw ±10% supply the fixed-clock ceiling is
1.13 GS/s. Quote the trade, not a single number.

## Output-chain taper: C154 / C155 / C156 (2026-08-07)

The chain is Q → XB1 → XB2 → XM7/8 (PBIT_RAW tap) → XM9/10 (block output) → XISO1 → XISO2 → 210 fF
pad load. The last two stages live in a **separate include** (`*-ISOBUF-PBIT_OUT.spice`), so the
chain crosses a file boundary. Chain delay is set by the ratio between neighbouring stages; as
drawn those ratios are 4.94, 1.15, 1.00, 1.00, 8.94, 2.86 — three stages amplifying nothing and one
overloaded ~9×. Delay proxy (Σ of 1+fanout): 25.9 τ.

| run | change | intersection @800 ps/bit | start spread |
|---|---|---|---|
| C148 | baseline | −120 ps | 720 ps |
| C154 | every device ×2 | **0 ps** (exactly) | 680 ps |
| C155 | retaper, comparator block only | **−160 ps** | 760 ps |
| C156 | retaper both files, equal 2.29× | running | — |

**C154** should have been a no-op — uniform scaling doubles drive and load together — and recovered
120 ps *because the scaling stopped at the block boundary*: exactly one ratio changed (XM9/10 driving
an unscaled XISO1, 1.0 → 0.5).

**C155** set the three in-block ratios to 3.53/4.0/4.0 — textbook — and was **worse by 160 ps**,
because the two unreachable ratios became 0.10 and 8.94. Predicted in advance from the delay proxy
(29.4 τ vs 25.9, "≈14% slower, −80 to −100 ps"); measured every condition 40–160 ps later. Direction
and scale correct, magnitude understated. See harness finding H-727: partial optimisation across an
interface is worse than none, because the quantity optimised belongs to the *pair*.

**C156** (in flight) applies one equal ratio of 2.29 across all six stages, both files:

| stage | as drawn (µm, P+N) | C156 |
|---|---|---|
| XB1 | 0.85 | 0.85 (unchanged) |
| XB2 | 4.20 | 1.95 |
| XM7/8 | 4.83 | 4.47 |
| XM9/10 | 4.83 | 10.25 |
| XISO1 | 4.83 | 23.50 |
| XISO2 | 43.20 | 53.86 (w=15.71/11.22 with **m=2**) |

Build verified against the netlists: all six ratios = 2.29, delay proxy 19.8 τ (−24%).
**Prediction on record:** spread ~760 → ~520 ps, intersection ≈ +160 ps, which would make 1.25 GS/s
composable. Not scored until all 18 conditions land.

**Note — stage count kept at six.** An earlier recommendation to remove two stages was withdrawn:
XM7/8 feeds the separate PBIT_RAW output pin, so deleting it changes the block's I/O, and each stage
inverts so only an even number may be removed. Six equal stages give −24% delay against −31% for
four; 7% is a cheap price for leaving the interface alone.

**Open — unmodelled load:** PBIT_RAW is connected to nothing in these testbenches while PBIT_OUT
carries 210 fF. On a real part it would drive a comparable pad, so the stage feeding it is
under-loaded here and today's timing is optimistic by an unquantified amount.

## Randomness campaign, 2026-08-08 (C157–C162): offset, noise, bias, correlation

The timing work above says whether the part moves bits correctly. This section is the first evidence
about whether the bits are **unpredictable**, which is what the part is for.

### Measured

| quantity | value | method |
|---|---|---|
| input-referred offset, σ | **11.79 mV** (mean −0.19, 90th pct \|offset\| 19.12) | MC mismatch, N=200, track-phase DC sweep; 1/200 failed the validity gate, excluded |
| offset attribution | **11.5 mV** sense-amp/latch/buffer chain, **2.7 mV** CML stage | second MC population with the CML held matched |
| trim efficacy | 1.002 mV input-referred per mV trim differential; range ±60 mV (5σ) | trim sweep at the operating point |
| trim resolution | 0.20 mV per step as drawn; 0.05 mV with 2 extra DAC bits | fine-trim bench |
| noise at comparator, σ_n | **3.246 mV rms** | `.noise`, band later characterised by `.ac` |
| noise band | −3 dB 15.8 MHz … 5.62 GHz, peak \|H\| 14.8 V/V @0.32 GHz, NEBW 8.0 GHz | `.ac` sweep |
| serial correlation ρ (800 ps) | **−0.0033** (independently reproduced: −0.004) | analytic from the `.ac` transfer, dense linear grid |

**Consistency check (independent, both chairs):** implied input density S = 6.12e-18 V²/Hz = 4kTR
with R = 278 Ω at 125 °C — a physical source resistance. √(S·NEBW·|H|²) = 3.253 mV against the
measured 3.246.

### Conclusions

- **Bias, not error rate, is the binding constraint.** Against the 121 mV test differential the
  offset is 10σ of headroom and harmless. Against σ_n = 3.25 mV — the correct yardstick, since in
  service the input is noise centred on zero — an *untrimmed* part gives P(one) ≈ 100%: dead-biased,
  not merely skewed. **Trim is mandatory.**
- **Trim resolution, not range, is the specification.** Required residual is σ_n/40 = **0.081 mV**
  for <1% imbalance. As drawn (0.20 mV) gives 2.45% — 2.5× outside. With 0.05 mV steps: 0.6% —
  inside, min-entropy 0.983 bits/bit.
- **Serial correlation is not a defect.** ρ ≈ −0.003 → P(repeat) ≈ 49.9%, indistinguishable from a
  fair coin. An earlier ρ = 0.102 was a log-grid aliasing artefact (see H-730) and is retracted,
  along with the "correlation dominates" conclusion built on it.
- **One-time calibration cannot work, by arithmetic rather than measurement.** The 0.081 mV budget is
  0.69% of the 11.8 mV offset; a part drifting 1% of its own offset yields 1.45% bias, 5% yields
  7.2%. Any plausible tempco over 165 °C is tens of percent — 30–70× over budget. Three attempts to
  measure the drift factor all failed (probe fighting the CMFB loop; forced-bias deck giving a
  non-physical 375× gain span; unseedable RNG preventing per-part tracking), and none of them matter.
- **The answer is a background servo**, not a tighter component: count the output ones/zeros and
  servo the trim to hold the ratio at ½. Sizing: N = 10,000 bits resolves 1% at 2σ (32,768 at 3σ),
  giving an 8–26 µs window against a 20–50 ms drift time at 1 °C/s — three orders of margin. It also
  absorbs ageing and supply drift, which no factory calibration can.

### Open

- **Servo hazards (raised, not yet analysed):** a loop that forces the ratio to ½ will do so even if
  the noise source dies, so **health monitoring must be independent of the servo** — repetition
  counts and raw pre-trim balance, not the corrected ratio. And the loop imprints a slow negative
  correlation at its own window scale; that must be shown to sit below the measurement floor.
- Metastability rate never calculated — and this circuit deliberately operates in the small-input
  regime other designs treat as the dangerous tail, so it is a first-order quantity here.
- No layout parasitics, no post-layout re-verification. Nothing fabricated.

## Trim architecture: C164–C166 (2026-08-09)

The randomness campaign specified a 0.05 mV input-referred trim step. Building it took four attempts,
each failing for a different and instructive reason. All measured in the working deck, arrival-gated.

| attempt | mechanism | worst step | range | verdict |
|---|---|---|---|---|
| C164 | extra DAC bits, independently referenced | 0.728 mV @125 °C | 121.6 → 3.9 mV | **96× step variation** across corners |
| C165 | ratiometric: trim pairs on the CML tail | 0.742 mV @−40 °C | 325.9 → 12.7 mV | 26× variation, range still collapses, **sign reverses** |
| — | fine trim by load imbalance | — | — | **not manufacturable**: 0.19% of 838 Ω = 1.6 Ω, needs a 434 kΩ tap or is swamped by switch R_on |
| C166 | **dithered LSB** | effective 0.00625 mV | unchanged | **works** |

**Why C164 failed:** the trim was referenced to an absolute quantity while the thing it corrects
scales with the stage's own bias, so the two drift apart. *Any correction referenced to something
absolute, when the thing corrected is not, will separate from it* — the third time this principle
decided an outcome (see also the CMFB loop and the one-time-calibration analysis).

**Why C165 fell short of its prediction:** the ratiometric arithmetic — input-referred step =
ΔI/g_m, and g_m = I_tail/V_T for a bipolar pair, so ΔI = k·I_tail gives step = k·V_T with only a
1.71× spread over −40…125 °C — is correct, but assumes the trim devices *share the tail as a
controlled fraction*. Measured, they sat at V_be ≈ 1.16 V, hard on and outside that regime. **The
arithmetic was right about a circuit that was not built.**

**Why the load-ratio idea died:** (ΔR/R)·V_T is exactly the right relation and depends on no bias
point at all, but at an 838 Ω load a 0.19% imbalance is 1.6 Ω — two orders below what an rppd tap or
a switch can resolve. Sound requirement, unmanufacturable at this impedance.

**C166, the solution — buy the resolution in digital:** keep the 0.2 mV physical LSB that *is*
buildable and toggle it with probability p from a 5-bit dither register. Effective offset = p·LSB,
resolution set by the register rather than by any physical dimension: **0.00625 mV effective step,
32× finer than the LSB**, from logic the servo already requires.

- Mean bias at p = 0.25: Φ(0.05/3.25) = 50.61% → **0.61%**, inside the 1% target.
- Steady-state residual (half p-step, 0.0031 mV): **0.038%** bias — 26× inside target.
  *(Reported as 0.055% by the DE; independently recomputed as 0.038%. Same order, does not change
  the conclusion, recorded for accuracy.)*
- It works because the servo already averages 32,768 bits — anything toggling faster than that
  window is seen only as its average, so the fine resolution is real from the loop's point of view.

**Requirement, not a detail — the dither must be RANDOM, not periodic.** A regular toggle puts a tone
at the dither rate into the output, precisely the structure certification tests hunt for. Quantified:
the dither's threshold jitter is LSB·√(p(1−p)) = 0.087 mV at p = 0.25, i.e. 2.7% of σ_n, raising the
effective noise to 3.2512 mV (+0.035%). Being a *random* component added to the threshold, it cannot
reduce per-bit entropy.

## Specification of the three additions (C166–C168, 2026-08-09)

Derived entirely by arithmetic from the measured properties above; **no simulation**. Every number
was computed independently by both chairs; the corrections that resulted are noted inline.

### 1. Offset trim — coarse/fine cascade

| element | value |
|---|---|
| structure | **(C, p)**: effective offset = (C + p) × 0.2 mV |
| coarse code C | ~10 bits, 0.2 mV per code, ±60 mV (±300 codes) — current-steering DAC |
| fine p | 5-bit **dither probability** over one LSB, 1/32 steps = 0.00625 mV effective |
| why dithered | a 0.05 mV physical step is unmanufacturable here (0.19% of 838 Ω = 1.6 Ω); the servo's 32,768-bit averaging converts digital duty-cycle into effective analogue resolution |
| dither requirement | **must be random, not periodic** — a periodic toggle puts a tone at the dither rate into the output. Jitter contributed: 0.087 mV = 2.7% of σ_n, raising effective σ_n to 3.2512 mV (+0.035%), entropy-neutral |

### 2. Bias servo

| element | value |
|---|---|
| window N | 32,768 bits = 26.2 µs at 1.25 GS/s (15-bit counter) |
| measurement σ | √(0.25/N) = 0.276% per window |
| error | e = count − 16,384; b = f − 0.5 |
| update | p ← clamp(p − g·b, 0, 31/32); **p railing steps C by ±1 and re-centres p** — normal tracking behaviour |
| loop gain | **g = 10.2**, giving dimensionless loop gain 0.25 (db/dp = 0.0245). *Originally specified as g = 0.25, which confuses bias-fraction with probability units and would have been 40× too slow — τ = 163 windows instead of 4.* |
| response | τ = 4 windows = 105 µs; 5τ = 0.52 ms, against drift of ~20 ms per 1% at 1 °C/s |
| settled residual | **0.105%** bias — loop-noise-dominated (per-update p noise 0.028 ≈ 0.9 p-step; steady-state wander 1.4 steps). *Not the 0.038% quantization figure: the loop noise dominates it.* |
| start-up | p = 0.5, output gated until one full window has been observed (26 µs) |

### 3. Health monitors — three independent channels

| channel | watches | alarm | why it survives audit |
|---|---|---|---|
| envelope detector | 1.8–2.2 GHz band at the comparator input | 0.34 mV rms (healthy 0.687) | spectral, so it separates thermal noise from clock-harmonic pickup; a 20 dB source loss lands 5× below the alarm |
| repetition count | P(repeat) over raw windows | 3σ = 50.83% (natural 49.9%) | the dither is white per bit, contributing ρ ≈ 0 — invisible to this statistic, as required |
| **coarse-code rail** | C pinned at 0 or 599, 4-window debounce | — | the total correction has run out of authority. *Replaces two rejected designs: a raw pre-trim balance channel (saturates at ~100% ones for every real part — cannot distinguish healthy from dead) and a p-rail alarm (p railing is normal coarse-step behaviour and would fire during ordinary tracking).* |

### Interaction audit (the composition check)

Each subsystem was specified against its own requirement; the audit asked what they do to each
other. Three pairs compatible with margin (dither vs repetition counts: ρ ≈ 0 against a 0.83%
alarm; dither vs envelope band: ~4 µV in-band against a 340 µV alarm, 85×; start-up: output gated
before monitors are asked to judge). **One pair failed** — see the coarse-code-rail row above.

**Three monitoring channels were designed and then found to alarm on the design's own intended
behaviour** (an amplitude detector that could not separate source from pickup; a balance channel
saturated by the imbalance it was meant to survive; an alarm on a control value that rails
routinely). Each was a reasonable design *considered alone*. The recurring lesson — after H-724's
empty intersection — is that **correctness of parts does not compose into correctness of wholes**,
and the check costs arithmetic against a design that does not yet exist.

**Still unbuilt:** none of this is drawn, simulated or laid out. The metastability rate remains
unmeasured (H-731). No layout parasitics anywhere.

### Behavioural verification of the servo — `servo_model.py`

The specification above was derived by arithmetic, with every parameter computed independently by
both chairs. It still contained a **sign error** that made the loop diverge: the correction
(C+p)·LSB *opposes* the offset, so a positive measured bias means more correction is needed, and the
originally specified `p ← p − g·b` applies less. Simulated, it rails within a few windows and sits
at 50% bias permanently. The corrected rule is **`p ← p + g·b`**, and the convention is now stated
explicitly in the spec so the polarity cannot be re-inferred: *correction opposes the offset;
positive b raises the correction.*

Running the model confirms the response time (first window under 1% at **window 23 = 0.6 ms**,
against the predicted 5τ of 0.52 ms) and revises the settled residual to **0.23%** — the analytic
0.105% omits the coarse/fine interaction with loop noise, so the simulated figure is the one of
record. Both remain inside the 1% target.

**Method note:** a sign error in feedback is the most consequential and least visible defect in
control design — every gain, time constant and threshold can be correct while the loop drives into
the rail. It survives inspection because a minus sign reads as a considered choice. Nothing catches
it except letting the design run. Forty lines, minutes to write, against a fabricated part whose
output would be stuck at one value in a block whose entire purpose is unpredictability.

**Final servo parameters after the coverage fix.** The fine control spans **8 coarse codes**
(1.6 mV) with **6-bit** dither, giving an unchanged 0.025 mV effective step and a **2.95×** coverage
margin over the worst measured coarse step. Loop gain rescales with the wider span:
db/dp = 0.194, so **g = 1.29** holds the dimensionless loop gain at 0.25. Acquisition **18 windows
(0.47 ms)**, settled bias **0.25%** (max 0.90%).

*Why 8 codes and not the 4 that satisfied the arithmetic:* the coverage condition is compared
against a worst coarse step of 0.543 mV taken from **C165, a build that was rejected** — the coarse
DAC is not designed yet, so that number is provisional, while coverage failure is permanent and
inescapable for an affected part. **Margin should scale with how well the number is known, not only
with how bad the failure is.** At 4 codes the check passed 0.800 against 0.798, ~1.5% of headroom on
a placeholder. The extra span costs one register bit.

`servo_model.py` now carries `coverage_check(coarse_step_mV)` as a **fail-loud assertion** taking the
coarse step as an input, so the condition is re-tested automatically when the coarse design lands
rather than being remembered by whoever happens to still be here. It also retains a **regression
case for the sign error** — a defect already found must not be able to return silently.

### Single-step correction, acquisition scaling, and the timeout — the last correction round

Both chairs' copies of `servo_model.py` were found to **slew the coarse code** — up to 6 steps in a
single window (mean 5.1 during acquisition) — while both specification and commentary described a
single-step loop. Neither noticed until the models were *instrumented* rather than read: the p update
can reach g·0.5 = 0.645 and each coarse step consumes 1/FINE_CODES = 0.125 of p, so ~5 steps per
window. **A property of the specification had been asserted as a property of the code, by both sides.**

A related error ran alongside it: acquisition was measured against the wrong σ. Two distinct
quantities in this design are both spread parameters — the noise at the comparator (3.25 mV) and the
part-to-part offset distribution (11.8 mV). Scaling a sweep by the first while meaning the second
gives internally consistent numbers about a part that does not exist.

**With single-stepping enforced (verified by instrumentation: max 1 C-step per window), acquisition
is simply the walk:**

| offset | codes | windows | time |
|---|---|---|---|
| 0.5σ (5.9 mV) | 29 | 29 | 0.77 ms |
| 1σ typical (11.8 mV) | 59 | 59 | 1.55 ms |
| 2σ (23.6 mV) | 118 | 118 | 3.09 ms |
| 3σ (35.4 mV) | 177 | 177 | 4.64 ms |
| 4σ (47.2 mV) | 236 | 229 measured | 6.18 ms |

**Consequence, which neither chair had drawn:** the previously agreed 100-window timeout covers
offsets only to 20 mV = 1.69σ, so **~9% of perfectly healthy parts would raise a fault at every
power-up** — the alarm-on-healthy-behaviour failure for the fourth time, this time inside a number
that had been *verified as safe* using acquisition times nobody knew were slewed.

**Timeout raised to 400 windows (10.5 ms)** — and justified by the *architectural* limit rather than
a statistical tail: the coarse code spans ±300 codes, so the longest possible walk is 300 windows
however the offset distribution turns out; anything beyond is uncorrectable and is caught by the
coarse-rail alarm. **400 = full coarse range + ⅓ margin.** A threshold justified by a statistical
tail must be revisited whenever the tail estimate moves — and 11.8 mV rests on one MC campaign with
one gate-failed sample. A threshold justified by the range moves only when the range does.

The two alarms are then complementary rather than overlapping: **the timeout catches a loop that is
walking but slow (something wrong with the loop); the coarse rail catches one out of authority
(something wrong with the part).**

**Slewing is recorded as a deferred optimisation**, not a bug: it acquires in ~55 windows instead of
229, but a coarse control that can accelerate is a second feedback loop and needs its own overshoot
and stability analysis before it is adopted.

## C169 — the coarse DAC, first build: a void measurement, and the check that will catch the next one

The coarse DAC was built to replace the **provisional** 0.543 mV worst-step figure (itself taken from
C165, a rejected build) that the coverage assertion depends on. The first build measured:

| corner | mean step | worst step | sign reversals |
|---|---|---|---|
| tt/typ/27 | −0.817 mV | 258.3 mV | 373 / 599 |
| ss/wcs/−40 | −0.668 mV | 223.5 mV | 428 / 599 |
| tt/typ/125 | −0.256 mV | 79.8 mV | 5 (only **10 of 599** steps nonzero) |

`coverage_check(258.3)` duly failed — the assertion working as designed, hours after being written.

**But all of it is VOID, and the numbers above must not be quoted as data.** Three symptoms had one
cause: the bench decoder read the sweep *voltage* as the code count (missing a ×100 scale), so
`floor(0.64 V / 64) = 0` — the code never advanced. That single fault explains the inverted direction
(mean step negative at every corner), the ~4× oversize implied full scale (−489 mV against a target
of +120), and the two-thirds-of-boundaries reversals. **A binary-weighted DAC can lose monotonicity
only at major carries — nine of them among 599 boundaries — so 373–428 reversals was never a
matching result.**

**Diagnostic that found it:** a coarse sweep every 64 codes, before any further corner work. The
transfer showed two populations — five points moving by hundreds of millivolts, five by microvolts —
which is not a transfer curve.

**Standing check adopted (see harness finding H-733):** *before characterising any converter, sweep
N codes and count the DISTINCT output levels; if it is not ≈N the decode is broken and nothing
downstream means anything.* The tell was already in the data — 10 nonzero steps across 599 codes,
which no 10-bit converter produces — and would have halted the run before two further corner sweeps,
a monotonicity analysis, and the coverage assertion being fed a number that was never real.

**Rebuild direction:** fix the decoder scale, then **thermometer-code the top bits** — unary segments
are monotonic by construction, which removes the failure mode rather than measuring it. The
distinct-levels check runs first, before any corner run or assertion.

**The worst-case coarse step therefore remains unmeasured**, and the coverage margin still rests on
the provisional 0.543 mV. That is the most load-bearing placeholder in the specification.

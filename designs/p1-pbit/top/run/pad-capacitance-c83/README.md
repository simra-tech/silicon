# C83 — analog pad capacitance, extracted because the PDK does not state it

The p-bit output has to leave the die through a pad before a probe can see it, so
the load the output buffer drives is a real number somebody has to know. The
installed IHP SG13G2 kit states a pad-pin capacitance for the **input** pad
(`sg13g2_IOPadIn`, 0.22075 pF, in the `sg13g2_io_typ_1p5V_3p3V_25C` datasheet's
Pin Capacitance table). It states nothing for `sg13g2_IOPadAnalog`, which is the
cell an outward-facing analog signal would use, and the shipped
`sg13g2_bondpad.lib` is an explicit placeholder with no electrical content.

So this package extracts it from the pad cell's own ESD structures.

## Result (independently recounted from the retained raws)

Small-signal capacitance at the `pad` pin, `V2` deck, pad biased at 0 V:

| frequency | C |
| --- | --- |
| 10 MHz | 271.20 fF |
| 100 MHz | 266.03 fF |
| 1 GHz | 209.74 fF |
| 10 GHz | 150.81 fF |

The roll-off is physical, not numerical: the real part of the admittance rises
over the same span, from 0.13 µS to 1.5 mS, which is what a network of diodes,
clamps and a poly resistor looks like. A pure capacitance would be flat in C and
show no such loss trend.

`V3` sweeps the pad's DC bias across the range the circuit actually swings and
reports C at 1 GHz for each:

| pad bias | C at 1 GHz |
| --- | --- |
| 0.0 V | 209.7377 fF |
| 0.3 V | 209.2036 fF |
| 0.6 V | 209.2039 fF |
| 0.9 V | 209.6917 fF |
| 1.2 V | 210.6463 fF |

Total spread 1.44 fF, about 0.7%. **The pad capacitance is effectively bias
independent over the operating range**, which retires the concern that a 0 V
extraction would not represent operating conditions.

The 0.3 V and 0.6 V points print identically at six significant figures. They are
not identical; they differ in the fourth decimal of a femtofarad. Recounting at
full precision was necessary to establish that the sweep was actually stepping,
rather than repeating one condition.

## Method

Drive `pad` with a 1 V AC source, measure the current into the network, and take
`C = imag(-i(vstim)/v(pad)) / (2*pi*f)`.

Before trusting it on an unknown, the method was checked against a known 100 fF
capacitor in a throwaway deck; it returned 1.00000e-13 F at 10 MHz, 100 MHz and
1 GHz.

## What was wrong first, and why it is worth recording

The first version of this deck ran cleanly, exited 0, wrote an empty stderr, and
returned **2.5e-23 F** — roughly ten orders of magnitude too small, and falling
with frequency instead of flat.

Cause: in SPICE the *first letter* of an element name determines its type. The
IO supply rails were written as

    IOVDD IOVDD 0 DC 3.300
    IOVSS IOVSS 0 DC 0.000

which declares two **current** sources — a 3.3 A injection, and a 0 A source
(an open circuit) where a ground reference was intended. The pad's ESD
structures therefore had no return path, and the only admittance left was the
leakage resistors: `i(vstim)` purely real at -3.33e-10 A, flat from 1 MHz to
100 GHz.

`V2` renames those two elements to `VIOVDD` / `VIOVSS` and changes nothing else.
The fix was confirmed by reverting only the rail naming in an independent
reviewer's deck, which collapsed that deck's answer to -1.4e-27 F, and restoring
it, which reproduced 2.09738e-13 F exactly.

An intermediate reviewer figure of ~85 fF was published and then **retracted**:
that reviewer's own diagnostic deck contained the same `I`-prefixed rail defect
it was written to diagnose. Correcting that single line reproduces the result
above to six figures.

## Custody note

`C83-AC-PADCAP-IOPADANALOG-CANDIDATE-ONLY.raw` and `.op.raw` carry the **V1**
basename but contain **V2** data. The correction instruction deliberately changed
only the two rail lines, which left the deck's internal `write` statements
pointing at the V1 filenames, so the corrected run overwrote the void run's raw.
The void run's stdout log survives and is not included here (it belongs to a
retracted result). Later revisions carry their revision in every filename they
write; `V3`'s per-bias raws show that convention.

## Portability

`*-portable.cir` are the exact run decks with the installed PDK root prefix rewritten
to `$PDK_ROOT`. No other byte differs. Set `PDK_ROOT` to an installed IHP SG13G2
tree and run with `ngspice -b`. The exact non-portable source hashes are recorded
in `BINDINGS.json`.

## Limitations

- Small-signal extraction of one pad cell in isolation. It is not the load a
  packaged or probed die presents, which adds probe, cable and routing.
- No bond wire, no probe model, no board.
- Nothing here is a gate result, a bandwidth claim, signoff, or tape-out
  evidence. The P1 gate remains open.

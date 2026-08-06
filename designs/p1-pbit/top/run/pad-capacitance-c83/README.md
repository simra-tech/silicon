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

## Open caveat added 2026-08-05 after publication, updated the same day

A later transient investigation found that `sub!` — the substrate node the PDK pad cell introduces
through the bulk terminal of its `rppd` secondary-protection resistor — is not tied by the decks in
this package, and was observed following the pad signal (0.4247 V to 0.5601 V) rather than sitting at
a quiet reference.

**Correction to the first version of this note:** that note called `sub!` a *global* node. It is not.
ngspice treats it as instance-local unless a `.global` declaration exists, and the installed PDK
contains none. A first attempt to fix this by adding a top-level `Vsub sub! 0 DC 0` was therefore
**inert** — it tied a top-level node nothing connects to, while three separate internal nodes
(`xpad.xnclamp.sub!`, `xpad.xpclamp.sub!`, `xpad.xsecondprot.sub!`) stayed floating. That attempt
produced bit-identical results, which briefly looked like evidence that the substrate did not matter.
It was not evidence; it was a change that did nothing.

Adding `.global sub!` collapses those to a single node which then holds at 0.000000 V. Measured on a
comparable transient metric — buffered output at t = 1.000 ns driving this same pad cell — tying the
substrate properly moves the result by **-0.188 %** (0.385244 V floating to 0.384520 V tied). That is
roughly nineteen times the measurement method's own error bar, so the effect is real, but it is small.

## Caveat closed 2026-08-06 — the re-extraction was run

The extraction has now been repeated with the substrate genuinely tied, and the caveat above is
resolved with numbers rather than withdrawn or left hanging.

Method, in two steps, because a re-extraction that silently differs from the original in some other
way proves nothing:

1. The portable deck in this package was run unmodified. It reproduced the published figures
   **exactly** — 2.711959e-13 / 2.660271e-13 / 2.097377e-13 F — establishing that the comparison
   baseline is this package and not a rebuilt approximation of it.
2. That same deck was then changed by exactly two added lines, `.global sub!` and `VSUB sub! 0 DC 0`,
   and nothing else.

The tie was verified to have taken effect rather than assumed, which is the failure the note above
records: with the saved-variable restriction lifted, the unmodified deck exposes **three** separate
substrate nodes (`xpad.xnclamp.sub!`, `xpad.xpclamp.sub!`, `xpad.xsecondprot.sub!`) and the modified
deck exposes **one** (`v(sub!)`, with `i(vsub)` beside it).

| frequency | published (substrate floating) | substrate tied | change |
|---|---|---|---|
| 10 MHz  | 271.196 fF | 271.646 fF | +0.166 % |
| 100 MHz | 266.027 fF | 266.479 fF | +0.170 % |
| 1 GHz   | 209.738 fF | 210.193 fF | +0.217 % |
| 10 GHz  | 150.813 fF | 151.266 fF | +0.301 % |

The real part of the admittance is unchanged to five significant figures at every point, so the loss
term and the roll-off reading in this package are unaffected.

Artifacts for this re-extraction ship beside the originals:
`C92-AC-PADCAP-SUBTIED-portable.cir` (the deck, `$PDK_ROOT` substituted the same way),
`C92-AC-PADCAP-SUBTIED.raw`, `C92-AC-PADCAP-SUBTIED.op.raw` and the two run logs. Diff the deck
against `C83-V2-AC-PADCAP-IOPADANALOG-CANDIDATE-ONLY-portable.cir` to see that the two added lines
and the output basenames are the only differences.

**Status of the figures above:** confirmed, with a correction smaller than the rounding used to
quote them. Every value moves up by between 0.17 % and 0.30 %, in the same direction, and none of the
conclusions drawn from them changes — in particular the pad still sits inside the 300–400 fF buffer
drive limit recorded under `context` in `FACTS.json`. Readers who want the corrected numbers should
use the right-hand column; readers comparing against the raws in this package should expect the
left-hand one, because those raws were produced with the substrate floating and have not been
replaced.

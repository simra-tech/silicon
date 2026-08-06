# Output path at the slow MOS corner — C101/C103

**Status: a failure, characterised. Not a gate result, not signoff. The P1 gate remains open.**

At the slow MOS corner this design's output path delivers **nothing** — 13 µV at the pad against
773 mV at nominal. It is not a marginal result and it is not temperature-driven. Four candidate
fixes each improved the chain substantially and **none of them rescued the output.**

## The corner data

Full chain — comparator, isolation buffer, lumped 210 fF load — with `cornerMOSlv` moved and
`cornerHBT` held at `hbt_typ`. Max `v(PBIT_OUT)` over the 2.2 ns window:

| corner / temperature | as drawn | 4-stage taper |
|---|---|---|
| `mos_tt` / 27 °C | 0.772905 V | 1.230175 V |
| `mos_tt` / 125 °C | 1.187339 V | — |
| **`mos_ss` / 27 °C** | **0.000013 V** | — |
| **`mos_ss` / 125 °C** | **0.001849 V** | **0.000051 V** |
| `mos_ff` / −40 °C | 1.219988 V | 1.246055 V |

**Temperature is not the cause.** `mos_tt` at 125 °C works *better* than nominal; `mos_ss` at 27 °C
is dead. The slow MOS corner kills it at any temperature, and it kills the tapered buffer exactly as
thoroughly as the one as drawn — so the buffer is not where the problem is.

Reproduced independently by a second implementation (C101, C102), matching to all printed digits.

## Where the signal dies

Node extrema over the window, as-drawn buffer:

| node | `mos_tt` / 27 °C | `mos_ss` / 27 °C | `mos_tt` / 125 °C |
|---|---|---|---|
| `xcomp.cml_out_p` | 0.476 – 0.732 (0.256) | 0.514 – 0.709 (0.195) | 0.440 – 0.772 (0.332) |
| `xcomp.raw_inv` | 0.300 – 0.704 (0.404) | 0.439 – 0.633 (0.194) | 0.207 – 0.762 (0.555) |
| `PBIT_RAW` | 0.338 – 1.205 (0.868) | 0.658 – 1.197 (0.539) | 0.053 – 1.206 (1.153) |
| `pbit_out_core` | −0.017 – 1.164 (1.181) | −0.006 – 0.025 (**0.031**) | −0.020 – 1.222 (1.242) |

The comparator's own decision node is healthy at `mos_ss` — 539 mV of swing. The collapse is across
`xcomp.xm9`/`xm10`, the inverter that reads `PBIT_RAW`.

**The mechanism is level, not drive.** `PBIT_RAW`'s *floor* is 0.658 V at `mos_ss` against 0.338 V
at nominal. The swing is ample; it sits entirely above the trip point of the inverter that has to
read it. Widening `xm9`/`xm10` does not help.

## The root cause: the CML-to-CMOS converter stops amplifying

`XM5`/`XM6` with `XRFB` (`rppd w=1.0u l=18.5u`) wrapped from output to input is a self-biased
inverting amplifier — the standard CML-to-CMOS converter. The feedback resistor holds the inverter
at its own switching threshold so a small differential swing lands where the stage is most
sensitive.

| | input swing | output swing | **gain** |
|---|---|---|---|
| `mos_tt` / 27 °C | 0.256 V | 0.404 V | **1.58** |
| `mos_tt` / 125 °C | 0.332 V | 0.555 V | **1.67** |
| **`mos_ss` / 27 °C** | 0.195 V | 0.194 V | **1.00** |

At the slow corner it has stopped amplifying. Everything downstream is starved from that point.

## Four fixes, all improvements, none sufficient

All at `mos_ss` / 27 °C, as-drawn buffer, lumped 210 fF, each editing only the lines named:

| variant | change | `PBIT_RAW` floor | `pbit_out_core` max | `PBIT_OUT` max |
|---|---|---|---|---|
| baseline | — | 0.658 V | 0.025 V | 0.000013 V |
| `src-gm2` | `XM5`/`XM6` `m=2` | 0.490 V | 0.478 V | 0.000172 V |
| `src-gm4` | `XM5`/`XM6` `m=4` | 0.421 V | 0.788 V | 0.001873 V |
| `src-rfb37` | `XRFB` `l=37.0u` | 0.584 V | 0.113 V | 0.000061 V |
| `src-gm2rfb37` | both | 0.410 V | 0.761 V | 0.001380 V |
| *(nominal, for scale)* | `mos_tt`/27 °C | *0.338 V* | *1.164 V* | *0.773 V* |

The best variant nearly triples the converter's output swing and brings `PBIT_RAW`'s floor most of
the way down. The pad still sees under 2 mV.

**What the failure does instead of going away is move.** Fix the converter and the signal gets
through it, then dies at the next stage. The relationship in that table is smooth and monotone —
push the floor down, the following node's output climbs — which is what *distributed marginality*
looks like, not a single broken component.

## Conclusion

Every stage in this path has slightly less margin than it needs at `mos_ss`, and the shortfalls
compound. This is a **corner-robustness redesign of the output path**, not a device to widen. The
four-stage buffer taper published in `../isobuf-taper-c99-c100/` is a real improvement at `mos_tt`
and `mos_ff` and does not touch this.

## Limitations

- **Partial corner check.** Only `cornerMOSlv` moves; `cornerHBT` stays `hbt_typ`. `.option temp`
  is global, so temperature does reach the HBTs within their typical corner — the isolation is on
  corner selection, not on temperature.
- No mismatch, no statistical spread, no `sf`/`fs` skew corners, no supply variation.
- Lumped 210 fF stands in for the pad. That stand-in was checked against the real pad at `mos_tt`
  and agreed to within 2.4 %; it has **not** been checked at `mos_ss`.
- The four fixes are first-probe values chosen to move the gain, not an optimisation. A larger or
  differently-structured change might succeed where these did not; what the data supports is that
  *these four* do not, and that the failure relocates rather than resolving.
- An earlier reading of this data attributed the break to undersizing — the same fault as the
  buffer's, one stage earlier. That was wrong and is corrected above.

## Files

`src-*.spice` are the four comparator variants; diff each against
`C45-V1-SOURCE-p1_top_hier_v3-...spice` to see the one or two changed lines. `*.cir` are the decks.
`buf-m1.spice` is the buffer as drawn, `buf-taper2.spice` the four-stage taper. Decks are portable:
`$PDK_ROOT` is the installed IHP SG13G2 root and every include is relative to this directory.

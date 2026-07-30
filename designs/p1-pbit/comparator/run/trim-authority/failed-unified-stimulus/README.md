# Retained failure: unified current-steering stimulus

This is the immediately preceding failed attempt at the 670 uA current-steering
experiment. It is retained because the raw files are real and the failure is
instructional; none of its derived trim-authority numbers should be used.

The deck intended to synthesize a 1.0 V common mode with ±0.1 V base offsets
using voltage-controlled sources. Instead, each source multiplied
`V(v_trim_cm) - V(v_trim_diff)` by ±0.5. At the claimed midpoint this drives
approximately +0.5 V and -0.5 V, about **1 V differential**, rather than equal
1.0 V bases. The trim pair is therefore far outside the three stated codes.

The maximum-code command also leaves this parser error in the retained log:

```text
PPerror: syntax error in line segment
   +0.200
```

The raw files reproduce the report that was made from them, but they belong to
the wrong stimulus. That distinction is why the deck, log, and all three raws
remain together here.

The corrected independent-source experiment is in
[`../current-steering-670ua/`](../current-steering-670ua/).

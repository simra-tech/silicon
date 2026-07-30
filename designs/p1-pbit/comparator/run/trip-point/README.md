# The output inverter's trip point is 593.8 mV, not 600 mV — and the difference is definitional

Several pages in this repository reference "the 0.600 V trip point" of the comparator's output
inverter, one of them describing it as *measured*. **0.600 V is `vdd/2`, and the trip point is
not `vdd/2`.** Measured across corners:

| corner | VDD | **V_trip** | as % of VDD | `vdd/2` − V_trip |
| --- | --- | --- | --- | --- |
| typical, 27 °C, `mos_tt` | 1.20 V | **593.83 mV** | 49.49 % | +6.2 mV |
| cold, −40 °C, `mos_ff` | 1.32 V | **656.02 mV** | 49.70 % | +4.0 mV |
| hot, 125 °C, `mos_ss` | 1.14 V | **560.29 mV** | 49.15 % | +9.7 mV |

The inverter is **`XM5`/`XM6`** — `sg13_lv_pmos w=2.83 µm` over `sg13_lv_nmos w=2.0 µm`, both
`l=0.13 µm` — which is the device actually in the chain, not a stand-in. It tracks the supply at
**49.1 … 49.7 %**, never 50 %, so `vdd/2` overstates it at every corner and worst where the
supply is lowest.

## Why the unity-gain point is the right definition here

The trip point is quoted here as the **unity-gain point**: the input voltage at which
V_out = V_in. That is a deliberate choice, not the only possible one — a threshold defined as
"the input at which the output crosses VDD/2" is a different quantity and would give a different
number for any inverter that is not perfectly symmetric.

The unity-gain point is the correct one for this circuit because of what candidate 2 does. The
feedback resistor `XRFB` — `rppd w=1.0 µm l=18.5 µm`, so 260·18.5 + 70 = **4.88 kΩ** — connects
`raw_inv`, the inverter's *output*, back to `cml_out_p`, its *input*. At DC a resistor between
output and input forces V_out = V_in. **The node is therefore driven to the unity-gain point by
construction**, and that point is 593.83 mV at typical.

That is the whole mechanism of the candidate-2 fix, and it means the number the fix self-biases
to is 593.8 mV — not `vdd/2`, and not a value chosen anywhere in the design.

## Consequence for existing claims

Any figure expressed as "*N* mV from the trip point" that used 0.600 V as its reference carries
a **6.2 mV** error at typical. In particular, the statement in
[`../../README.md`](../../README.md) that the feedback self-biases `cml_out_p` to *1.2 mV from
the 0.600 V trip point* is referenced to the wrong number. Recomputed against the measured
593.83 mV, using the `cml_out_p` DC values already recorded on that page:

| | before the fix | **after candidate 2** |
| --- | --- | --- |
| `cml_out_p` DC (measured) | 0.634 V | **0.6012 V** |
| vs the measured 593.83 mV trip | +40.2 mV | **+7.4 mV** |
| vs the 0.600 V figure used previously | +34 mV | +1.2 mV |

**So the headline "1.2 mV from trip" is really 7.4 mV — six times larger.** The conclusion is
unaffected: the fix still moves the node from +40.2 mV to +7.4 mV, a 5.4× improvement, and the
page's own criterion is that the node sit within roughly 100 mV. The margin dwarfs the
correction. What changes is the *impressiveness* of the number, which is worth correcting
precisely because nothing else depends on it.

Nothing here disturbs the counted results. Bit decisions are read from `PBIT_OUT`, which swings
rail to rail, so a 6 mV difference in where the trace is sliced changes no settled bit. It
matters for statements about *bias* — how close the node sits to its decision point — which is
exactly where the 1.2 mV figure lives.

## Where 0.600 V came from

It is not invented. The CACE characterisation in
[`../../../characterisation/`](../../../characterisation/) reports `Vth` with a typical of
0.600 V, and that is a real measurement — but of `ihp_sg13g2_inv.spice`, the demo inverter,
sized `w=1.414 µm` / `w=1.0 µm`. That is the **same W/L ratio** as the chain's inverter
(1.414 against 2.83/2.0 = 1.415), so the two devices genuinely do share a trip point and the
disagreement is not a device difference.

**The 6.2 mV is a difference of definition between two measurements, not an error in either.**
Which is the more instructive outcome: the number was right, the label on it was wrong, and it
was propagated into a context where the other definition was the one that mattered.

## Reproducing

```
ngspice -b tb_vtrip_27c.cir      # DC sweep of the output inverter, 0 … VDD in 1 mV steps
ngspice -b tb_vtrip_-40c.cir
ngspice -b tb_vtrip_125c.cir
python3 find_vtrip.py            # unity-gain crossing, linearly interpolated
```

`$PDK_ROOT` is the IHP SG13G2 PDK root. The sweeps are 1 mV steps, so the interpolated crossings
carry roughly ±0.5 mV of grid resolution — well inside the 6.2 mV effect.

## Files

- [`find_vtrip.py`](find_vtrip.py) — unity-gain crossing from a DC sweep raw file
- [`tb_vtrip_27c.cir`](tb_vtrip_27c.cir), [`tb_vtrip_-40c.cir`](tb_vtrip_-40c.cir),
  [`tb_vtrip_125c.cir`](tb_vtrip_125c.cir) — the three sweeps
- `raw_vtrip_*.raw` — their output, retained so the crossings can be recomputed

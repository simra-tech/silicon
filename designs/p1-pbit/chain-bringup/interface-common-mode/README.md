# The amplifier–comparator interface: an assumption nobody had checked

Every comparator testbench in this project drives the input pair from sources at a
**1.440 V** common mode. That number was never measured — it was chosen, early,
because the trim pair sits there, and then it propagated into every deck.

The first attempt to run the two blocks end to end made it worth checking. It is
not 1.440 V.

## What the amplifier actually delivers

`tb_noise_amp_output_cm.cir` — operating point, `P1_NOISE_AMP` on 2.500 V with both
inputs at 1.440 V:

    v(noise_amp_p) = 2.138631 V
    v(noise_amp_n) = 2.138631 V

**2.139 V**, not 1.440 V. The two sides are equal to seven digits, so there is no
differential offset at the interface; the common mode is simply 699 mV higher than
every comparator deck assumed.

## Whether it matters: it does not

Re-ran the comparator's clocked polarity pair at the amplifier's real output common
mode, changing nothing else.

| | `PBIT_RAW` latch end | `PBIT_RAW` track end | `PBIT_OUT` latch end |
| --- | --- | --- | --- |
| +10 mV at **1.440 V** CM | 1.20001 V | 1.19999 V | −0.9 µV |
| +10 mV at **2.139 V** CM | 1.20001 V | 1.19999 V | −0.9 µV |
| −10 mV at **2.139 V** CM | −14.1 µV | +7.4 µV | 1.20000 V |

Identical to five decimal places, and the polarity flip still works. The input pair
is a CML pair over a current sink: raising both bases together raises the shared
emitter node with them and leaves the collector currents alone. 699 mV of common
mode is absorbed by the tail.

So this is recorded as an assumption **checked and cleared**, not as a defect. The
prediction going in was that a 699 mV interface mismatch would break something —
it does not, and saying so is worth more than quietly deleting the check.

## What this does not establish

The input pair tolerates this common mode at the two levels tested. It does not
follow that there is no upper limit: push the bases high enough and the collectors
must eventually leave the forward-active region, since the collector load holds
`c_p` / `c_n` near 2.1 V on a 2.5 V supply. The margin between 2.139 V and that
limit has **not** been measured, and it is the number to have before the chain is
laid out.

## Reproducing

```
ngspice -b tb_noise_amp_output_cm.cir
ngspice -b tb_comparator_cm2p14_plus10mv.cir
ngspice -b tb_comparator_cm2p14_minus10mv.cir
```

`$PDK_ROOT` is the IHP SG13G2 PDK root. The 1.440 V baseline row comes from
`../../comparator/run/clocked-both-polarities/`.

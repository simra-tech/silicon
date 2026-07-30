# Clocked at 5 GS/s, both input polarities

Two runs of the same deck differing only in which input source is the higher one.
The point of the pair is that a comparator welded to one rail passes the failing
polarity on its own — only the flip distinguishes a fix from a clamp.

| file | what it is |
| --- | --- |
| `p1_comparator_export.spice` | the block netlist, exported from `p1_comparator.sch` by xschem; 42 instances |
| `tb_clocked_plus10mv.cir` | IN_P − IN_N = **+10 mV** (`VAMP_P` 1.445, `VAMP_N` 1.435) |
| `tb_clocked_minus10mv.cir` | IN_P − IN_N = **−10 mV** (sources exchanged) |
| `ngspice_clocked_plus10mv.log` | full ngspice output including the `.measure` results |
| `ngspice_clocked_minus10mv.log` | same, other polarity |

## Reproducing

```
ngspice -b tb_clocked_plus10mv.cir
ngspice -b tb_clocked_minus10mv.cir
```

`$PDK_ROOT` is the IHP SG13G2 PDK root. The two `pre_osdi` lines load the PSP103
MOS modules; without them the HV PMOS mirror devices have no model and the
netlist is rejected as incomplete.

## Why the measurement instants are what they are

`CLK_P` is `PULSE(1.20 0.0 0 20p 20p 80p 200p)` — it *falls* first. So within each
200 ps period `CLK_P` is low from 20 to 100 ps and high from 120 to 200 ps. The
latch pair is gated by `CLK_N` and the track pair by `CLK_P`, which puts

- the **end of the latch phase** at t = 100 ps + 200 ps·n → sampled at **900 ps**
- the **end of the track phase** at t = 200 ps + 200 ps·n → sampled at **1000 ps**

Both are in the fifth clock period, well clear of start-up. The `MAX`/`MIN`
windows are 600 … 1000 ps, two complete periods.

A phase-dependent offset shows up as a difference between those two instants.
There is none: the two columns agree to 20 µV.

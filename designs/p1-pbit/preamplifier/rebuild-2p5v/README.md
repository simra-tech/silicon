# Preamplifier rebuilt on PDK devices at V_CC = 2.5 V

Artefacts behind *The rebuild on real PDK devices* in [`../README.md`](../README.md).

```
p1_noise_amp_clean.spice          the netlist both AC decks include
tb_p1_noise_amp_ac.cir            AC sweep, ideal voltage drive
ngspice_preamp_ac_output.log      its output: 21.285 dB, f3db 19.091 GHz
tb_p1_noise_amp_ac_cascade.cir    the same deck with 1059 ohm source impedance per input
ngspice_cascade_output.log        its output: 20.953 dB, f3db 5.258 GHz
tb_p1_mirror_sweep.cir            tail current against the slave's collector voltage
ngspice_mirror_sweep_output.log   its output
```

The cascade deck differs from the ideal-drive deck by two inserted resistors and nothing else,
so the 3.6× bandwidth difference between the two logs is attributable to source impedance alone.
That is the whole reason it is shipped as a separate file rather than as an edit.

Absolute paths are rewritten — `$PDK_ROOT` for the PDK, `./` for the working directory — so both
decks need `$PDK_ROOT` pointed at an SG13G2 installation before they will run. That substitution
is the only edit; every number is as the simulator produced it.

**Two things these files do not contain.** No corner or temperature variation: all three runs are
`hbt_typ` / `res_typ` / `cap_typ` at the 27 °C default, and none of them sets `.temp`. And no
mismatch — there is no Monte Carlo here. The gain margin to the 20 dB floor is 0.95 dB in the
loaded configuration, and nothing in this directory tests it against process or temperature.

**One fragility worth knowing before you edit the decks.** The midband gain is read as
`gain[100]`, index 100 of `ac dec 20 1k 100g`, which is 100 MHz for that sweep specification and
comfortably above the ~1.6 MHz high-pass corner the 2 pF coupling caps form with the 50 kΩ base
bias. Change the sweep and the index silently means a different frequency.

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
tb_p1_noise_amp_loaded_corners.cir  loaded gain at -40/+27/+125 C with VCC +/-5%
ngspice_loaded_corners.log          its output: 22.95 / 20.95 / 18.12 dB
tb_temperature_only.cir             temperature varied with the supply held at 2.50 V
ngspice_temperature_only.log        its output: 18.63 dB at 125 C
tb_bias_vs_temperature.cir          per-side collector current against temperature
ngspice_bias_vs_temperature.log     its output: 0.8723 / 0.8933 / 0.9243 mA
```

The last three exist to separate causes rather than to add corners. The loaded-corner deck varies supply and
temperature together, so on its own it cannot say which produced the 2.83 dB hot-corner drop; the other two
vary one thing each, and their results add to the bundled one. That is the whole reason they are three files.

The cascade deck differs from the ideal-drive deck by two inserted resistors and nothing else,
so the 3.6× bandwidth difference between the two logs is attributable to source impedance alone.
That is the whole reason it is shipped as a separate file rather than as an edit.

Absolute paths are rewritten — `$PDK_ROOT` for the PDK, `./` for the working directory — so both
decks need `$PDK_ROOT` pointed at an SG13G2 installation before they will run. That substitution
is the only edit; every number is as the simulator produced it.

The process corners are separate decks, because a `.lib` section cannot be switched from inside `.control`:

```
tb_pvt_loaded_typ.cir            hbt_typ / res_typ / cap_typ,  +27 C, 2.500 V
tb_pvt_loaded_cold_bcs.cir       hbt_bcs / res_bcs / cap_bcs,  -40 C, 2.625 V
tb_pvt_loaded_hot_wcs.cir        hbt_wcs / res_wcs / cap_wcs, +125 C, 2.375 V
ngspice_preamp_loaded_corners.log   all three: 20.95 / 24.11 / 17.19 dB
tb_pvt_crossed_hot_bcs.cir       the crossed corners, run to confirm the diagonal
tb_pvt_crossed_cold_wcs.cir        is the true envelope
ngspice_crossed_hot_bcs.log      19.07 dB
ngspice_crossed_cold_wcs.log     22.03 dB
```

**Read `ngspice_preamp_loaded_corners.log` rather than any summary of it.** It contains four lines of
`Error: no such device or model name xamp.xrbias1.r1` — two per altered corner — recording that an attempt to
override the bias resistor from the control block did not take effect. It is kept unedited for exactly that
reason: the log is what caught a summary that reported gains the simulation never produced.

**Still not contained here: mismatch.** There is no Monte Carlo in this directory, so device-to-device
mismatch within a die is untested, and every corner above is a global shift.

**On temperature in the control block.** The corner deck sets temperature with `set temp = 125` inside
`.control` rather than a `.temp` card, which is easy to mistake for a no-op that would leave all three corners
differing only in supply. It is not one in this ngspice: the run prints
`Doing analysis at TEMP = 125.000000` for that block, which is the definitive readout and is preserved in the
committed log. Worth checking rather than assuming if you port these decks.

**One fragility worth knowing before you edit the decks.** The midband gain is read as
`gain[100]`, index 100 of `ac dec 20 1k 100g`, which is 100 MHz for that sweep specification and
comfortably above the ~1.6 MHz high-pass corner the 2 pF coupling caps form with the 50 kΩ base
bias. Change the sweep and the index silently means a different frequency.

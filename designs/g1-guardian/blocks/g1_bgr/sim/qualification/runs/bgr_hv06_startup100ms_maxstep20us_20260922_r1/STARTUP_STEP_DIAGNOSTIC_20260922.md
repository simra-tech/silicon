# One bounded slow-ramp maximum-step diagnostic

Prospective status: **not run**. Both loop24/Qref4 parent535 and lengthened-HV
derivative586 fail numerically near39.269ms of the original100ms/3V ramp,
at Q76_u24, despite solver exit0. Neither reaches the requested300ms endpoint.
Their final saved steps are200µs apart while detector/kick voltages change
rapidly. The passing1ms-ramp derivative uses a2µs nominal transient step.
These observations motivate one controlled maximum-step check; they do not
establish the physical failure mechanism or show timestep sensitivity is the
only cause.

On derivative source
`586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b`,
retain every source/model/initialization/stimulus byte and solver tolerance.
Only change the transient command to explicitly cap the maximum step at20µs:
`tran 0.0002 0.30000000000000004 0 20u uic`.
The300ms endpoint and original200µs output-step argument remain unchanged.
No altered cards, gmin, integration method, startup device sizing or rail ramp.
The prior failed attempts remain failed regardless of this result.

Fresh single run, one CPU6,300s hard watchdog,0.15GiB HOME growth allowance
after a new CPU/RAM/quota/inode gate. Roughly15000minimum steps versus1627
saved rows/15.77s in the passing fast-ramp run suggest order150s, not a runtime
guarantee; nonlinear iterations may differ. Stop on failure with no automatic
step/tolerance/timeout ladder. This test is not a new statistical population.

Require finite complete output, identical strictly increasing main/terminal
time grids, first saved time in(0,2µs], endpoint300ms, and no numerical error
even if exit0. Preserve missing[0,firstsample) coverage. Original endpoint
level gates remain0.9<VREF<1.2V and IPTAT>1µA; export every mapped MOS/HBT
terminal and keep the separate1.6V HBT VCE screen. Model warnings remain
visible, and waveform extrema are sampled observations, not continuous or
initial-interval bounds. A pass is not timestep convergence or full hot/HV
reliability, PVT/MC, physical-fit, new-wiring-PEX or candidate adoption.

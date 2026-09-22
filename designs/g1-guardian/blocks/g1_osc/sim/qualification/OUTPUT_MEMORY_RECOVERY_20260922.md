# OSC output-memory recovery preparation

The retained slow/cold re-enable run
`osc_actual_receiver_slowcold_reenable_20260922_01` failed with ngspice exit1:
251702400 bytes requested versus244678656 bytes reported available. The
three leaves of `osc_synthetic_jitter_20260922_01` also failed this check;
the zero-amplitude leaf requested250650400 versus249135104 bytes. These
are numerical/output-allocation failures, not timeouts or electrical failures.
No complete acceptance waveform exists for those runs.

Both original runners omitted `save`, so ngspice retained all internal-node
vectors before exporting just the required measurements. `run_receiver.py`
now issues `save` for its22 exported vectors. The T2F qualification script
`run_synthetic_jitter.py` issues `save` for its five exported vectors for
either block. Stimuli, timesteps, models, solver tolerances and exported
columns are unchanged. The simulator memory check remains enabled.

The retained ngspice46 source tree's `src/frontend/outitf.c`, function
`OUTpD_memory`, estimates plot allocation from the number of saved vectors.
Its Linux available-memory helper reads `MemFree`, not `MemAvailable` or
the container memory limit. This source diagnosis is consistent with the
observed rejection; it is not proof that increasing a container limit alone
would recover the run. The pinned executable must still be qualified.

Verification status:

| Check | Status |
|---|---|
| Python syntax compilation of modified runners | passed |
| Nominal actual-receiver saved-vector parity against complete anchor | passed |
| T2F zero-amplitude saved-vector parity against complete synthetic anchor | passed |
| OSC synthetic zero-amplitude endpoint with selected vectors | passed |
| Slow/cold OSC re-enable recovery and function checks | passed |
| OSC nonzero-amplitude synthetic recovery | passed at1/5mV |

`osc_receiver_saveparity_20260922_r1` completes the nominal6µs fixture in
46.103645s. `output_save_parity.json` verifies all30597 rows and22 exported
vectors byte-identical to the archived nominal anchor, identical models,
sources and runtime, and exactly the added `save` statement as the deck
difference. Numerical completion and receiver functionality both pass.
Waveform SHA-256 is
`91630ceea463dd217615014ca0688e0101c4692fd8f12092638c5cee9b6f7990`.
This qualifies the output-saving change for this fixture; the failed
synthetic endpoints are recorded separately below.

`t2f_saveparity_20260922_r1` completes the32µs zero-amplitude T2F fixture
in149.495624s. Its90189 rows/five exported vectors are byte-identical to the
retained anchor, including waveform, PWL stimulus, source/model/runtime and
deck-only-save comparison. Waveform SHA-256 is
`c04fdb0b130e0dd9c9fa03796a605e65fe6aa5aa486e9638be4e1df214f28291`.
The period standard deviation remains1.889571302ps; this is the numerical
baseline of the external perturbation fixture, not physical phase noise.

`osc_reenable_save_20260922_r1` completes the full10µs slow/cold,code15
fixture in68.817248s,50394 finite rows and26,709,350 waveform bytes. Both
receiver-function and disable checks pass: all19 checked clock points have
zero rising edges during3.1–4.9µs disable, and all resume in7–9.8µs.
Frequency is5.616956MHz before disable and5.617099MHz after re-enable.
Source/model/runtime identity and the save-only deck change were checked
against the original failed fixture. The previous allocation failure is
retained. Waveform SHA-256 is
`f82dbf010bc08ff8069da098830f6ad0943248b07a8ec401b8af34e990018b7e`.
This is selected nominal-model receiver coverage with estimated assemblyRC
and assumed100fF leaf loads; it does not qualify the full clock tree or
mismatch/PVT populations.

`osc_synthetic_save0_20260922_r1` and
`osc_synthetic_save15_20260922_r1` complete all three20µs endpoints with
133 measured periods each. The simulated period standard deviations are
21.469819ps (0mV),50.580451ps (1mV),209.649028ps (5mV); wall times are
126.151963s,89.575337s,111.585189s. This is finite external OU-perturbation
sensitivity, not physical device phase noise or a jitter-budget pass. Each
directory's descriptive `analysis.json` reports its own amplitude subset as
incomplete relative to the three-amplitude campaign; together these fresh IDs
cover0/1/5mV. The original failed three-leaf directory is retained unchanged.

Recovery procedure used after pinned-image/PDK qualification: run a fresh nominal actual-receiver
fixture with the unchanged default arguments. Compare `receiver.dat` to
`osc_actual_receiver_nominal_20260922_01` only after confirming that run's
fixture arguments, source/model hashes and endpoint. Compare same-host old
and modified save policies if platform differences prevent byte equality;
retain both and report numerical differences explicitly. The original script
is preserved inside each historical run directory. Then recover the failed
re-enable fixture under a fresh run ID, one thread,4GiB allocation,300s
watchdog. Numerical completion and receiver/disable acceptance are distinct.

For synthetic runs, first repeat the completed T2F zero-amplitude fixture
with `--block t2f --rms-mV 0`, retaining its32µs endpoint and saved stimulus.
Then run OSC zero amplitude before the1/5mV leaves. All use fresh IDs and
300s per-leaf watchdogs. Save only requested vectors, inspect actual output
growth after each pilot, and assess quota before expansion. None of these
preparations constitutes physical device-noise or jitter-budget qualification.

# HBT macro built-in self-heating sensitivity

**All24 paired DC sweeps completed** across HBTtyp/bcs/wcs and ambient
−40/27/85/125°C. The unchanged PDK already enables self-heating by default.
A three-case pilot proves default and explicit `selft=1` give identical full
waveforms; `selft=0` produces zero thermal-node rise and changes current.
This is modeled device-local DC heating, not measured or packaged thermal
qualification. Off-region and125°C selfheated points are explicitly screened
against the stated model range.

## Inputs and supported model control

The runner copies the existing detailed AnalogPad/route fixture
`macro_20260921T153803Z_e82d0d1c/tt_27_1.2_3.3.cir` and uses the unchanged flat
macro CPEX `reports/flat-pex-20260921T150414Z_3db2c2ca/ngspice_pex.spice`.
Only the coupon instance's documented `selft` parameter is explicitly set0/1
in separate local copies. No PDK card or pad model is edited. EmitterNx=1,
W0.07um/L0.9um, collector source1V, emitter source0V, core/IO rails1.2/3.3V.
The original base source sweep is0.30–0.85V in1mV steps (551points).
RouteR remains base35.8955ohm, collector90.0117ohm and emitter69.8649ohm,
with the same lumped route capacitors and full pad models.

[Provenance](selfheat_screen_20260922_r1/provenance.json) pins all sources and
model hashes, ngspice46, PDK84374023ee8b4b126bebbba67fcbada0a9c0ff0b and
image `sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0`.
The relevant unchanged VBIC model excerpt is retained. It declares `selft=1`,
`rth=selft*3260*(4/Nx)^0.9` and `cth=1.60e-12*(Nx*0.25)^0.95`.
ForNx1 the nominal Rth is about11.35kK/W. The internal thermal node
`v(x1.xq1.t)` records modeled junction rise inK; it is observed without
changing the four-terminal device interface or adding thermal loads.

The [pilot qualification](selfheat_pilot_20260922_r1/qualification.json) passed
all five checks before the24-case screen. Every leaf has a30s watchdog,
explicit completion marker, finite551-row waveform and separate process status.
No solver failures or timeouts occurred. Full sweeps and current-threshold
interpolated anchors are retained in the [screen manifest](selfheat_screen_20260922_r1/manifest.json).

## Results and limitations

[Summary](selfheat_summary_20260922_r1/summary.json) separates numerical
completion, terminal limit checks and model-range flags. VCE remains below1.6V
in all13,224 points. Peak collector current is below0.979mA (Nx1 model bound
3mA), and the maximum thermal rise is9.3783K at bcs/125°C and external
base0.85V. At27°C typ the top-of-sweep current changes from306.231uA with
heating disabled to322.049uA with heating enabled (+5.17%), with3.47135K rise.
Across the12 paired corner/temperature conditions, top-point current changes
by+2.29…+6.18%. These top points use the same external base voltage; routing
and emitter resistance are allowed to alter intrinsic bias.

At fixed interpolated collector current, nominal27°C typ gives:

| Collector current | Modeled temperature rise | VBE with self-heating | VBE on minus off |
|---|---:|---:|---:|
| 1uA | 0.01136K | 0.665335V | −15.94uV |
| 10uA | 0.11345K | 0.726518V | −134.47uV |
| 100uA | 1.11814K | 0.789994V | −1.0965mV |

These anchors satisfy the screened bias and junction-temperature ranges. The
0.1uA anchor has VBE about0.604V, below the card's stated0.65V validity floor,
and is retained as a diagnostic rather than included as an in-range anchor.
Many lower-voltage Gummel points similarly lie outside that stated bias range.

All three125°C ambient selfheated sweeps put junction temperature above125°C;
maximum is134.378°C. The model computes those values, but the stated
−40…125°C temperature coverage does not establish their accuracy. They remain
explicit temperature-extrapolation diagnostics. This does not turn numerical
completion into qualification. Ambient−40/27/85°C sweeps remain below125°C
junction temperature in this fixture.

The prior pad-inclusive DC sweeps already used default self-heating; the new
work exposes and compares that mechanism rather than newly enabling it.
Electrical self-heating coupling in the VBIC model is distinct from board,
package, neighboring macros, ambient gradients or radiation effects. No such
thermal network is present. Pulsed-readout thermal settling is **not run**
by this DC campaign; a physical pulse-width/calibration procedure remains
necessary before interpreting sub-mV temperature or dose changes.

```sh
G1_CPUS=2 flow/run.sh env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 designs/g1-guardian/blocks/g1_dut/sim/qualification/run_selfheating.py --run-id selfheat_pilot_repeat --mode pilot
G1_CPUS=2 flow/run.sh env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 designs/g1-guardian/blocks/g1_dut/sim/qualification/run_selfheating.py --run-id selfheat_screen_repeat --mode screen --pilot designs/g1-guardian/blocks/g1_dut/sim/qualification/selfheat_pilot_repeat/qualification.json
python3 designs/g1-guardian/blocks/g1_dut/sim/qualification/analyze_selfheating.py --screen designs/g1-guardian/blocks/g1_dut/sim/qualification/selfheat_screen_repeat --output build/scratch/hbt-selfheat-summary-repeat
```

## Subsequent selected thermal-pulse anchors

Four transient leaves (typ27°C andbcs85°C, each selft0/1) completed1us with
0.1ns maximum step, unchanged model cards and the same pad/route/CPEX fixture.
Base source starts at0.65V, rises to0.8V at100ns with10ns edges, holds200ns,
then returns. All10,020 rows per leaf are retained in
[thermal_pulse_20260922_r1/manifest.json](thermal_pulse_20260922_r1/manifest.json).
The [summary and waveform plot](thermal_pulse_summary_20260922_r1/summary.json)
retain paired source hashes; [SVG](thermal_pulse_summary_20260922_r1/thermal_pulse.svg)
and visually checked PNG show modeled current and thermal response.

With self-heating on, typ27°C rises from0.00636K initial bias heating to
1.21177K at the high plateau; bcs85°C rises from0.11785K to4.13585K.
The respective thermal10–90% response times are25.89ns and26.84ns.
These are combined electrical/thermal responses including the10ns source
edge, not isolated Rth*Cth time constants. High-plateau current is108.523uA
versus105.210uA with heating disabled for typ27°C, and388.122uA versus
367.971uA for bcs85°C. Thermal state returns to its initial biased value by
the final900–1000ns window. Disabled controls retain zero thermal-node rise.
Peak junction temperatures are28.212°C and89.136°C; VCE stays below1V.

This establishes a selected model-based pulsed response, replacing the earlier
DC-only “pulsed readout not run” status for these two conditions. Full pulse
width/load/corner qualification, zero-bias startup, package/chip coupling and
measurement accuracy remain **not run**. The pulse begins at0.65V and does not
cross the lower antenna diode's near-zero reverse-bias transition implicated
in separate GATE pad convergence failures; this result cannot qualify pad
startup from0. Low-bias intrinsic VBE can also lie just below the card's0.65V
floor and is not presented as complete bias-range validation.

```sh
G1_CPUS=2 flow/run.sh env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 designs/g1-guardian/blocks/g1_dut/sim/qualification/run_thermal_pulse.py --run-id thermal_pulse_repeat
G1_CPUS=2 flow/run.sh env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 designs/g1-guardian/blocks/g1_dut/sim/qualification/plot_thermal_pulse.py --run designs/g1-guardian/blocks/g1_dut/sim/qualification/thermal_pulse_repeat --output build/scratch/hbt-thermal-pulse-summary-repeat
```

# G1_T2F system check, 2026-09-24: comparator HBTs with EN = 0, start-up after 100 µs at EN = 0

All numbers are **simulated** (ngspice 46, pinned image
`sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2`, IHP SG13G2 PDK
`84374023ee8b4b126bebbba67fcbada0a9c0ff0b`). No model card, netlist or layout changed.

## Fixture

`t2f_sys.py` writes `decks/`. The decks follow `../tb_g1_t2f.spice.tmpl`: the same `.lib` sections, the
tb `.option` line (`gmin=1e-15 abstol=1e-13 reltol=1e-4 vntol=1e-6 method=gear`), `Vload iptat 1.0 V`,
`Cout fout 50 fF`, PTAT mode, and `../.spiceinit`. Unlike the block tb, **both** blocks are post-layout:
`g1_bgr/sim/postlayout/g1_bgr_pex.spice` and `../postlayout/g1_t2f_pex.spice`.

EN is 0 until 100 µs, then rises to 3.3 V in 10 ns. The run stops 100 µs after that, with a 10 ns
maximum step. The control `en1u_*` is identical except that EN rises at 1 µs, as in the block tb.
`.op` is taken with EN = 0.

Corners are tt27 (typ/tt/typ, 27 °C), ss125 (hbt_wcs/mos_ss/res_wcs, 125 °C) and ff-40
(hbt_bcs/mos_ff/res_bcs, −40 °C), all with cap_typ as in the block's `corners` suite.

Extracted-to-schematic HBT map:

| extracted | schematic | collector / base / emitter |
|---|---|---|
| XQ42 | QA1 | ca1 / vth / tail1 |
| XQ45 | QB1 | cb1 / cap1 / tail1 |
| XQ44 | QA2 | ca2 / vth / tail2 |
| XQ43 | QB2 | cb2 / cap2 / tail2 |
| XQ40, XQ41 | dummies | all terminals on vss |

```sh
cd designs/g1-guardian/blocks/g1_t2f/sim/system_checks_20260924
python3 t2f_sys.py gen && python3 t2f_sys.py run --cpus 51,54,56,57   # host; flow/run.sh, 1 pinned CPU per deck
python3 t2f_sys.py diag 56,57                                          # op-only attribution decks
python3 t2f_sys.py analyze                                             # -> summary.json
# single-device decks decks/diag_single_*.cir were run directly: flow/run.sh ngspice -b <deck>
```

Waveforms are in `${BULK}/blockchecks-20260924/t2f/*.dat`. Logs are in `logs/`. The
`Error: no such vector 0` lines in the logs come from printing `v(0)` for the grounded dummies and are
harmless.

## (1) HBT bias with EN = 0 (post-layout `.op`)

| corner | QA1 = QA2: VBE / VCE / VBC / IC | QB1 = QB2: VBE / VCE / VBC / IC | self-heating ΔT of QA |
|---|---|---|---|
| tt27 | 0.720 / 0.839 / −0.119 V / 7.91 µA | −0.317 / 1.014 / −1.331 V / 1.6 fA | 75 mK |
| ss125 | 0.613 / 0.768 / −0.155 V / 9.35 µA | −0.420 / 1.007 / −1.427 V / 0.10 pA | 82 mK |
| ff-40 | 0.792 / 0.887 / −0.095 V / 6.89 µA | −0.246 / 1.022 / −1.267 V / 1.3 fA | 69 mK |

- **What EN = 0 does.** It holds both capacitors discharged, so cap1 and cap2 sit at below 40 nV.
- **The QA transistors carry the tail.** Their bases are on vth = VREF, so they conduct the whole tail
  current.
- **The QB transistors are off.** VBE is −0.25 to −0.42 V and VBC is −1.27 to −1.43 V.
- **The QB collectors are held.** The NMOS cascode and bleeder hold cb1 and cb2 at 1.27–1.43 V.
- **The dummies** are at exactly 0 V.

**Nothing is floating, and no junction is outside the model card**: vbe_max 1.6, vbc_max 5.1,
vce_max 1.6. The QB2 condition is the same one it passes through every half-period in normal
oscillation.

The QA base currents are a real DC load on VREF through the mode switch: 2 × 10.6 nA at tt27, 2 × 35.8 nA
at ss125 and 2 × 2.75 nA at ff-40. At tt27 this lowers VREF from 1.03929 V (BGR alone, same PEX) to
1.03745 V, i.e. −1.8 mV ≈ 21 nA × 88 kΩ. While running, vth averages a further 0.5–1.5 mV lower.

## (2) The NaN / dynamic-gmin message is a model-initialisation artefact

Every deck prints "The temperature limiting function received NaN" once, followed by dynamic gmin stepping.
The stepping completes, and the final operating point is finite and physically consistent. The message
names no device.

| op-only deck | NaN message |
|---|---|
| BGR alone (tt27, ss125, ff-40) | yes |
| T2F alone with ideal pbias/pcasc/vref, EN = 0 and EN = 1 | yes |
| Joint, EN = 1 (all corners) | yes |
| Joint, EN = 0, with `.nodeset` at the solution | yes |
| **One npn13G2, forward-biased like QA2** | **no** (no gmin stepping) |
| **One npn13G2, biased like QB2 with EN = 0** | **yes** |
| **One npn13G2, all terminals grounded (dummy)** | **yes** |

The message therefore comes from any **off** `npn13G2`, whose self-heating (VBIC `selft=1`) thermal node
sits at ~1e-10 K, or at 1e-303 K for the dummy. The same happens with the BGR's nine grounded dummies.
Nothing is specific to EN = 0 or to the T2F. At ss125 there is also a "singular matrix" warning on
`xbgr.xq64`, which is a BGR dummy with all terminals on vss.

It is **not a circuit issue**: no node floats, and no base is open.

## (3) Start-up after 100 µs at EN = 0

| corner | first fout edge after EN | first-period f | settled f (last 50 µs) | within 1 % / 0.1 % after EN | f with EN at 1 µs |
|---|---|---|---|---|---|
| tt27 | 0.272 µs | 1.5497 MHz (+1.5 %) | 1.526986 MHz | 0.92 / 0.92 µs | 1.526986 MHz |
| ss125 | 0.231 µs | 1.8096 MHz (+2.2 %) | 1.770269 MHz | 0.78 / 1.35 µs | 1.770269 MHz |
| ff-40 | 0.311 µs | 1.3722 MHz (+1.0 %) | 1.359073 MHz | 1.04 / 1.04 µs | 1.359073 MHz |

There are no fout edges while EN = 0, and the 100 µs hold leaves no memory. The tt27 frequency is
1.527 MHz with both blocks extracted. That is −1.0 % against the README post-layout 1.5418 MHz, which used
a schematic BGR, and −4.6 % against the schematic 1.6003 MHz.

## Status

| Check | Status |
|---|---|
| HBT bias at EN = 0, 3 corners, within model voltage range, no floating node | passed |
| NaN/gmin message attributed | passed: an off-device VBIC self-heating initialisation artefact, not a circuit issue |
| Clean start after 100 µs EN = 0, 3 corners | passed: settles to 1 % within 1.04 µs (no acceptance limit was specified) |
| REF mode, supply ramps with EN = 0, 3.0/3.6 V, mismatch, SENSE in the same deck | not run |

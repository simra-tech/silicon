# Remaining DVBE common-routing cuts and resistor body applicability

This is a separate diagnostic continuation of the frozen supply candidate
`e3ecfc6208fcae71c6b2f4223b7db3900677acfe30987b50ba6365c720297feb`.
Canonical source586, all1036 devices, all device models, nine external pins,
native placement and the420×354µm footprint remain held. The existing
conditional nominal error is **−13.550411565mV**, not accepted or resolved.

## Saved-data result

`map_saved.py` binds all42640 positive edges,33420 node voltages and3355
source points; every component has exactly one of55 source-net owners.
It reproduces the saved total metal dissipation. It does not infer complete
edge support polygons from the endpoint boxes.

The DVBE common route carries approximately93.22µA. Two-cut transitions
around local(193,137.2),(203,137.2),(203,18.46) each contain9Ω cut elements
carrying approximately46µA apiece and losing approximately0.42mV. These are
Via2/3/4 in common routing, not native contact or intrinsic VBIC resistance.
The M2 stem near x193 between y137.35 and172.08 loses0.950mV. The widened
M3 collector halves still lose1.118/1.180mV; a wider0.8µm collector previously
failed actual foreign-metal clearance and is not silently retried.

The earlier pbias/pcasc bypass reduced local drop but gained less than0.4µV
of VREF. The larger voltage differences on those nets do not establish a
useful VREF correction; that already tested branch is not repeated.

## Prospective finite geometry screen

Keep every old polygon/cut. Screen one upper parallel common DVBE bridge
at y141µm with eight Via2 cuts near x193 and eight Via3/Via4 cuts near x203.
Local M2/M4 landings are0.72×1.56µm; an M3 bridge and short M5 extension
connect them. At the lower x203/y18.46 transition, screen six-cut Via3/Via4
arrays with1.14×0.72µm landing rectangles. Exact coordinates are in the
source ledger; the geometry may fail and no passing result is presumed.

Before candidate generation require all55 source-probe bindings, no foreign
metal or cut capture,250nm foreign-metal clearance,55nm enclosure,220nm
cut spacing, no partial old-cut overlap,5nm grid and the held footprint.
The screen writes no GDS. A passing local screen still requires full-parent
foreign/fill context, source/native-plus-overlay XOR, all terminal ownership,
seven star cuts, stock main/maximal DRC and strict source LVS before adoption.
Any conditional OP must first reproduce the held zero-R source/OP/2842
parameters/3885 raw fields; all positive edges and model terms remain.

## Separate399BN boundary question

The model's substrate control terminal is not a physical nearest-metal pin.
The [pinned public R3CMC source](https://raw.githubusercontent.com/IHP-GmbH/IHP-Open-PDK/84374023ee8b4b126bebbba67fcbada0a9c0ff0b/ihp-sg13g2/libs.tech/verilog-a/r3_cmc/r3_cmc.va)
uses its two substrate-to-internal-end voltages in the body-current function.
Zero DC substrate current therefore does not prove substrate-voltage
independence. The geometry screen also saves exact installed patched source
and wrapper bytes for an independent runtime-applicability check.

No substrate spreading network, measured electrode reference plane or
validated transfer from the399 bodies to the metal return is established.
Imposing a small NC voltage in a separate unchanged-card test could measure
conditional sensitivity, but cannot establish that transfer or qualify the
physical substrate. No contact/junction resistance is added or subtracted,
and no card is changed to obtain agreement.

| Check | Status |
|---|---|
| Saved-edge/source ownership and power reproduction | Passed |
| Resolution of13.55mV conditional VREF deficit | Failed; still present |
| New local cut/landing screen | Not run |
| New geometry, full-parent checks, stock DRC/LVS | Not run |
| New zero-R/positive-R OP | Not run |
| Exact installed BN branch applicability | Not run; capture prepared |
| Physical399BN potential/reference-plane qualification | Not run/unresolved |
| Source/model/deck mutation or fabricated measurement | Not applicable |

## Successor geometry disposition

The table above records the initial prospective state. The y141 upper bridge
failed actual VBE/VD2 capture. Moving it to y143 passed local checks and the
32-new-cut candidate passed stock main/maximal DRC and strict LVS, but the
complete b417 parent exposed220nm spacing to fill versus the prospective250nm.
That candidate and its failures remain separate.

The next candidate uses six upper cuts per transition, reducing upper landing
height from1.56 to1.14µm without moving its y143 center. Lower arrays remain
unchanged; four existing lower cuts are retained rather than duplicated.
Candidate `f4d14755511ec73220c3afdcd211ee6547e0eb025d4615a30a4919c7d0e819c7`
has26 new cuts. Local native/source/55-net/seven-star checks and stock
main/maximal DRC plus strict LVS passed. Its full-parent clearance rerun and
conditional electrical controls remain pending. One prelaunch resource gate
failed53<56 and launched no solver; a later fresh gate passed. No tolerance,
model, source parameter or physical rule was changed.

## Current-parent and model controls

The26-cut candidate passed the complete current-digital rerouted parent
`9a52cc71122df8fcc56bbd3ec3e0842958e1f7eec0f73c64ed21a8e2c7ea1805`:
all55 BGR source nets distinct, no foreign-metal/cut capture or250nm
proximity on seven changed layers, and exact local parent-plus-overlay XOR.
No fill was removed and the candidate has not been integrated. The held
complete-parent check took102.827s; standalone stock main/maximal zero took
44.530s and strict32-combined-device/24-net/9-pin comparison took6.748s.

All336 MOS source junction parameters, both complete positive-metal network
scenarios, independent network audits and source reconstruction passed.
Each network retains42678 positive edges and33433 contracted nodes with
all1036 compact-model devices and329 historical capacitors. Only exact-zero
connectivity is contracted; a positive edge within one contracted group is
retained in the inventory rather than silently discarded.

The restricted installed-model DC branch proof passed with four rejecting
negative controls. The15 rhigh and384 rppd wrappers do not override the
zero isa/isp defaults: their stationary NC branch current is zero. This
permits model-only DC current accounting, **not** a physical substrate
attachment claim. NC voltage still affects resistor body current. AC and
transient capacitive substrate currents are outside this stationary proof.

The first zero-OP runtime preflight failed because the supplied image token
omitted its required `sha256:` prefix; simulation was **not run**. The exact
manifest identity is used by a separately recorded successor; the script,
source and deck remain unchanged. Earlier short-window resource deferrals
remain failed. New launchers use a fixed30-second turnover-aware observation
under the unchanged60% policy and shared allocation, never a lower floor.
Zero/nominal OP outcome remains **not run** pending those controls; physical
BN reference planes, new capacitance coverage and adoption remain **not run**.

## Final recorded outcome (supersedes the prospective status above)

The complete results are in [REPORT.md](REPORT.md). Exact zero-R OP **passed**:
2842 model parameters,3885 raw fields and original OP waveform bytes match.
The single matched KPEX nominal leaf completed in488.190s and **passed** its
numerical/source/finite-point gates. Simulated conditional VREF is1.044307806083V,
an improvement of12.397999083mV relative to the held supply parent; residual
against original zero-R is−1.152412482mV, **not qualified or accepted**.
The exact maximum-principle check **failed** by1.221245327e−15V and is retained
without a tolerance waiver. Full1036 stationary current accounting completed;
the maximum nonreference KCL residual is1.049755e−13A. Full physical BN/contact
reference-plane qualification, new capacitance coverage, PVT/startup/MC,
LEF nonlinear OP and fullchip adoption remain **not run**. Model/rule/source
mutation and measured-silicon claims are **not applicable** to this diagnostic.

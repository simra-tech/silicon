# Shared-source junction applicability: conditional equations, not qualification

Read-only inspection is complete; unconditional electrical equivalence is **not established**. This does not change the qualified schematic, PSP cards, stock extraction or any golden reference. Independent native-array geometry/default mapping passed; the ten earlier stock-written per-node A/P annotations still failed. A strict stock MOS `Match` is not a junction-parameter certificate.

Evidence is [psp-junction-source-equations-20260922-r1.json](psp-junction-source-equations-20260922-r1.json), produced by [inspect_psp_junction_equations.py](inspect_psp_junction_equations.py) under the pinned runtime/PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`. It records exact source/model/OSDI hashes and line-numbered excerpts. Source PSP103/JUNCAP version is103.8.2/200.6.2. No ngspice, source rebuild or new extraction ran. Matching the inspected Verilog-A source to the existing compiled OSDI by a reproducible rebuild is **not run**; binary hashes alone are not that proof.

## What the source equations support

In `PSP103_module.include` lines1667 and1778, source junction current and charge are sums of bottom-area, STI-edge and gate-edge terms:

`I = AB·j_bottom + LS·j_STI + LG·j_gate`

`Q = AB·q_bottom + LS·q_STI + LG·q_gate`

The terminal contributions include the model multiplicity. Thus, when the component functions, temperature, actual internal junction voltage and all other state/limiting conditions are identical, equal aggregate **AB, LS and LG**, with multiplicity accounted for, imply equal sums. This is a conditional algebraic statement, not a finding that those conditions hold for our shared-source layout.

The actual non-RF HV cards select SWGEO=1, SWJUNCAP=3 and SWJUNEXP=0. Module lines860–889 map the supplied geometry per finger to `AB=AS/NF`, `LS=PS/NF−WE`, `LG=WE`, followed by clipping. Therefore equal AS/PS alone are insufficient without effective gate-edge width and finger/multiplicity accounting. Gate-edge and STI coefficients are separate; they cannot be replaced by an undifferentiated total perimeter.

JUNCAP initialization also computes area/edge-dependent forward-current limiting voltages from `IMAX/(component saturation-current density × component geometry)` (macro lines155–178). A repartition can change these limits. Equality outside a proven common operating/limiting regime is not established by the displayed linear sums.

## Four mismatch inputs and internal voltages

| Input | Direct junction-geometry consequence in the inspected cards | Other consequence |
|---|---|---|
| Random PSP W | Yes. `WE=max(W/NF+delWOD−2·WOT,1nm)` enters LG and subtracts from LS. Wrapper default AS/PS are computed from nominal wrapper w, not this random instance W. | Changes channel behavior and therefore potentially internal bias. |
| Random PSP L | The direct WE length term is zero here: WVARO/WVARL/WVARW are all zero. No direct L term appears in the selected AB/LS/LG mapping at fixed other inputs. | Changes channel behavior; fixed internal voltage is not guaranteed. |
| DELVTO | The inspected direct use shifts channel flat-band/threshold potential, not AB/LS/LG. | Can change branch current and internal bias. |
| FACTUO | The inspected direct use scales channel mobility, not AB/LS/LG. | Can change branch current and internal bias. |

These statements distinguish direct geometry mapping from circuit feedback; they do not assert zero total electrical effect for any random input. The mismatch source is SHA-256 `75c30f6975aad4cfe95af7c80fcea142ab0df6c9d7667c09120c7d0c9b814801`; nominal wrapper/model hashes are recorded in the JSON.

Both **non-RF** HV models used at rfmode0 have nonzero `RJUNSO=RJUNDO=5000·l/w`, plus nonzero body/well terms. Do not substitute the separate RF model's rfmode-multiplied expressions and infer that these resistances vanish at rfmode0. PSP evaluates junction voltage between internal SI/BS or DI/BD nodes (module lines1040–1047), and connects BS/BD through junction/body/well resistances (lines1722 onward). Equal external source/bulk nodes therefore do not prove equal internal junction voltages. The source/drain external sheet-resistance card values RSH/RSHD=0 do not remove the separate bulk/junction network.

## Disposition and next evidence

Shared-source adjacent-gate A/P allocation remains useful geometric bookkeeping, not a per-device model-applicability pass. Preserve the independent whole-array control as the physically direct default mapping. Preserve all stock annotation failures; no change to source A/P, deck parameter flags, ng conversion or model defaults is justified by this review.

A source-preserving mapped-parasitic flow could retain all canonical logical MOS instances and their mismatch/default parameters, adding only independently mapped interconnect parasitics. That is a prospective method, **not implemented or qualified**. It requires explicit gate/drain/source/bulk mapping, shared-diffusion ownership and no-double-counting rules, device/intrinsic-capacitance exclusion, internal-body-network treatment, exact source fingerprints, independent-array controls and operating-point/dynamic comparisons with frozen tolerances. It must not copy averaged extraction parameters into the golden source. Full shared-source dynamic/mismatch applicability, source-to-OSDI rebuild equivalence and adoption remain **not run**.

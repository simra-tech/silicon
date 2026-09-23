# R100 physical PEX boundary audit

This is a saved-artifact audit of the isolated R100 SENSE macro. It changes no
geometry, model, extraction deck or electrical source. The pinned runtime is
IHP SG13G2 `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`, KLayout 0.30.9,
KLayout-PEX 0.3.12. The native macro GDS SHA-256 is
`450a49062d17f65be1046736c2ebeff219b4c4d4b22fac0998940c158741a637`.

Run `python3 audit_saved_boundary.py --self-test`, then
`python3 audit_saved_boundary.py --field "$BULK_ROOT/sense-comp45-rz100-field-extract-20260923-r1" --native "$BULK_ROOT/sense-comp45-rz100-native-build-20260923-r1" --output summary.json`
from this directory after the project's fresh resource gate. The checker
requires the saved source/GDS/capacitance hashes, all 978 unique finite
positive pairs, exact binary64 roundtrips, 844 source pairs, and 134 distinct
source-to-VSUBS pairs. The duplicate-pair rejection control and saved audit
passed. `summary.json` records raw VSUBS capacitance sum 3258.0707077091083
fF, maximum 596.4581626263293 fF. These are extraction values with an
**unbound** terminal, not VSS loads or accepted circuit elements.

| Term | Supported reference plane in pinned source | Remaining boundary |
|---|---|---|
| VSUBS | KLayout-PEX `tech_info.py` defines a virtual substrate layer named `VSUBS`; `rcx25/netlist_expander.py` creates a separate `VSUBS` net. Raw CC lists one term for each of the 134 source nets. | No evidence binds that virtual net to physical VSS, a tap, a package return, or a compact-model substrate terminal. All 134 remain excluded from electrical insertion. |
| CMIM | PDK LVS `cap_derivations.lvs` derives top from MIM/topmetal1 and bottom from MIM/metal5; `cap_connections.lvs` connects those to their metal routes. PDK `capacitors_mod.lib` says top/bottom plate parasitics are included by parasitic-C extraction. | This saved run used blackbox CC. Its 844 inserted pairs do not prove complete MIM plate fields or separation from intrinsic model capacitance. No subtraction or zero assignment is supported. |
| Taps/contacts | Native layer inventory contains nwell, pwell, ntap and ptap geometry. | `cont_drw` remains an unnamed extracted layer (1111.7824 µm²). No saved field result assigns all tap/contact polygons and compact-model reference planes. |
| Finite wire resistance | KLayout-PEX `rcx25/r/r_extractor.py` supports metal-layer resistance from the technology data. | The saved command used CC mode and asserted no extracted resistances. This path has **not run** for the R100 macro, so there is no numeric resistance or complete distributed-terminal claim. |

Pinned file SHA-256s: `tech_info.py`
`42cf89175c0eaf21008aec2819a2abc654af65da016f156b04c7202c1fb9a8d3`,
`rcx25/netlist_expander.py`
`e3e2ba6bb4fb20d82f2d15879b9a30c66dc826bb09acaf0cf039bfb33223a42f`,
`rcx25/r/r_extractor.py`
`288373949c8875a0c96c09f0541d8aed335f14e0e348e23afe8bd58543bb4f11`,
`cap_derivations.lvs`
`f07126c303aab780de391dd1c39dd073ea6fd4123165f1c7bcac71d08da9c310`,
`cap_connections.lvs`
`d9ddc6a3cedb507dcd1d1de12e304b1d69e1690762c8ca3790fc88250ff6b3a`,
`capacitors_mod.lib`
`94b569e695fd8a223a5a49a5b5a6b0d8a62408820bf0c2ed9dbcb0a8ab7d957e`.

Complete physical PEX: **failed/unresolved**. The next defensible step is a
pinned full-mode extraction with explicit MIM plate and tap ownership checks,
then an independently audited node mapping that keeps VSUBS distinct until its
physical reference is proven. This audit supplies no electrical acceptance,
full-chip/fill context, or circuit adoption.

The V06 standalone ideal-reference DC grid is a separate completed source
test; it does not establish the physical substrate return. V18 requires
implemented supply/return geometry, switching currents and package context
for analog/digital VSS coupling and current margin. Those checks are **not
run** here; assigning VSUBS to VSS would bypass that required evidence.

## Full-device RC probe

`probe_rc_boundary.py` used the same source and native-preserving extraction
view, pinned technology and engine, with the supported `RC` mode and device
blackboxing disabled. Exact wrapper inverses and unchanged input/tool/model
hashes passed. The engine **failed** after 37.889447 s in
`rcx25/c/sidewall_and_fringe_extractor.py:383` with `KeyError: '<TODO>'` while
looking up a layer-pair overlap-capacitance specification. No technology value
was substituted and no geometry was omitted to bypass this failure.

The full-device inventory now exposes `cmim_top`, `metal5_cap`, `mim_via` and
contact-derived layers. That inventory is not completed field extraction:
`cont_drw` remains unnamed, and no complete RC result or electrical acceptance
was produced. The failed run is retained as
`sense-rz100-full-rc-probe-20260923-r1` under the configured bulk root.

`probe_r_boundary.py` made a separate resistance-only attempt. It **failed**
after 23.430023 s in `rcx25/extraction_reporter.py:332` with `KeyError: 27`
when looking up a via's bottom-conductor layer in the resistance-request
technology table. Input/tool/model hashes remained unchanged. The log also
retains missing-layer warnings for CMIM bottom terminals; these are not waived.
The run is retained as `sense-rz100-full-r-probe-20260923-r1`. No completed
resistance network was produced or inserted into an electrical netlist.

Neither attempt replaces the failed full-RC check, establishes missing
capacitances, binds VSUBS, or establishes compact-model reference planes.
Independent repair/qualification of the extraction technology and reporting
boundary is **not run**. Full physical PEX and affected electrical acceptance
remain unresolved.

## Saved resistance-request audit

`audit_r_request.py` rebuilds only the native request from the saved full-device
LVS database; it does not run the numerical resistance engine or alter the
technology. Three positive/rejection controls and an exact protobuf roundtrip
passed. The request contains ten conductors and ten vias, but its reference
integrity check **failed**: via ID 29 (`TopVia1`, extracted layer `mim_via`)
references bottom conductor ID 27, which is absent. Its top conductor ID 23
is `TopMetal1`. This invalid request exists before the reporter and numerical
engine run. Suppressing the reporting exception would not supply the missing
conductor definition.

The retained request and technology table are in
`sense-rz100-r-request-audit-20260923-r2`. Its parent LVS database SHA-256 is
`b7fecbfb03453bba2dc8cf687eef50f4be07b2f8e75062089ce15852c26dc214`;
the unchanged technology SHA-256 is
`6ece2ac73930696f77b257d14fcf9d29d9e02451e7df99c72239746c18369a92`.
The original technology JSON contains no literal `<TODO>` string; the full-RC
exception concerns a derived layer name. The first audit wrapper failed
because argument validation had already created the output directory. That
failed source and receipt are retained; the fresh second audit corrects only
directory-creation order. No geometry or extraction-technology correction has
been adopted.

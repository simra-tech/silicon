# Blackboxed native-CMIM R-only boundary check

The native 7 × 7 µm CMIM coupon was run once through stock pinned KPEX 2.5D
R mode with device blackboxing enabled. `probe_blackbox_r.py` is a hash-checked
derivative of the existing full-device coupon probe: it changes only the KPEX
`--blackbox` argument and the matching extraction-context boolean. The
coupon GDS/CDL, pinned technology, PDK models and rule decks are unchanged.
The one-CPU resource gate passed; the bounded tool completed in 7.50 s.

Strict LVS still matched the original two-pin CDL device, `C1 top bottom
cap_cmim w=7u l=7u m=1`. The R request named one `cap_cmim` device and both
source nets. It contained TopMetal1 and Metal5_n_cap conductor entries, but
no via entries, no device-terminal landing records, and no pin landing
records. The installed extractor explicitly warned that it could not find a
layer for either `mim_top` on `top` or `mim_btm` on `bottom`. The resulting
network contained **zero resistors** and zero capacitors. The saved request
audit checks those fields directly from the report database.

Blackboxing therefore avoids the full-device coupon's dangling-conductor
exception, but this coupon does **not** demonstrate external wire/via R
connected to native device terminals. It also omits intrinsic CMIM plate R.
The successful process exit is only a tool-path result, not terminal-bound
parasitic qualification; it must not be substituted for full macro PEX or
for the original failed full-device extraction. A different coupon with
explicit external wires and supported terminal-layer mapping would be needed
to prove any separable external-R path. No electrical adoption is claimed.

That follow-up coupon has now been built without changing the 49 µm² MIM
polygon or 25 native MIM-via shapes. Two 2-µm-wide × 10-µm-long drawn access
stubs were added: Metal5 to the left and TopMetal1 to the right. Native
capacitor source CDL was held exactly. The initial wire/remote-label version
passed stock maximal DRC (zero violations) and strict LVS, but the pinned
KPEX technology requires datatype-2 pin polygons as well as datatype-25
labels. Its R request consequently had no external port landings.

A separately saved second version added the documented datatype-2 remote
pin polygons on the two wires. It again passed stock maximal DRC (zero
violations) and strict LVS. The blackboxed R request then contained one
remote `top` pin on TopMetal1 and one remote `bottom` pin on Metal5, with
the correct two source nets and one native `cap_cmim` device. It still had
**zero CMIM device-terminal landings, zero vias and zero resistors**. The
engine warned that it could not assign a layer to `mim_top` or `mim_btm`.
The resistor result therefore has only one accessible port per net and
cannot establish the known-geometry access-wire resistance to the device.

This is not a mere spelling alias. In the pinned LVS deck, `mim_top` and
`mim_btm` are terminals on the computed `cmim_top`/`cmim_btm` layers;
`cmim_top` derives from MIM drawing, `cmim_btm` from its overlap with
Metal5, and the top reaches TopMetal1 through `mim_via`. Installed KPEX
`lvsdb_extractor.py` explicitly skips computed capacitor layers when
`blackbox_devices=true` (lines 173–179), then cannot map either native
terminal (lines 403–407). On the pin-qualified wired coupon, the MIM
drawing is 49 µm², while the full drawn Metal5 and TopMetal1 regions are
87.24 and 59.69 µm²; their XOR against MIM drawing is 38.24 and 27.91 µm².
The request has no via entry. Mapping a plate terminal straight to either
external metal would therefore change geometry and silently omit the
native connection/via boundary. No exact geometry-and-terminal equivalence
for a project-local alias is established. An adapter was **not** inserted.
Positive terminal-bound R and the corresponding swapped/missing-terminal
negative controls are **not run** because there is no supported positive
representation to control. Full-device R remains separately failed; this
blackboxed result remains partial and unqualified.

The pin-qualified coupon is saved locally as
`sense-mim-access-coupon-20260923-r2` (GDS SHA-256
`0317d7648ed2b74eec9107a40c958c791c3d3dbbdc97c121eab42d93f4f71bf1`);
its blackboxed R request/result and machine-readable audit are under
`sense-rz100-access-pins-blackbox-r-20260923-r1`. The earlier label-only
control remains at `sense-mim-access-coupon-20260923-r1` and
`sense-rz100-access-blackbox-r-20260923-r1`.

A read-only composition audit of the saved KPEX LVS database proves the
exact device-terminal regions: `mim_top` on net `top` is computed
`cmim_top` layer 104, and `mim_btm` on net `bottom` is computed
`cmim_btm` layer 105. Both are the same 49 µm² MIM footprint, not aliases
of the external conductors. In the wired coupon, `metal5_n_cap` contains
38.24 µm² outside that footprint and has **zero area overlap** with the
bottom device terminal. `topmetal1_con` has 59.69 µm² total and overlaps
the top footprint by 40.39 µm², but the pinned LVS topology connects the
top plate to it only through the 4.41 µm² `mim_via` region. Overlap is not
an electrical short across the MIM dielectric.

The pinned native ngspice `cap_cmim` model already contains a 55 mΩ
series resistor on its PLUS side and a `cmim_core` capacitor. At nominal
7 × 7 µm and the pinned typical `cap_carea_norm=1.5 fF/µm²`, its intrinsic
core capacitance is 74.62 fF including the model's 40 aF/µm perimeter
term. The model expressly assigns top/bottom plate parasitic capacitance
to parasitic extraction; it does not state that its lumped 55 mΩ includes
the MIM via or external access-metal resistance. Its port reference-plane
ownership cannot safely be inferred from that number.

Installed KPEX R extraction treats device-terminal regions as polygon
ports keyed by the exact layer ID, while its numerical conductor/via table
has only the external layers and no blackboxed `mim_via`. Merely restoring
terminal metadata on computed layers 104/105 cannot make a route through
that table. Relabelling those ports as external TopMetal1/Metal5 would
bypass the native via/plate connection and, on the bottom, map onto a
disjoint conductive region. It could omit or double-count resistance
relative to the model's 55 mΩ. Consequently a representation-only adapter
is **not currently justified**. An upstream interface must define the
physical terminal reference planes and model/extraction ownership, then
provide the missing supported material/via mapping before positive and
negative coupon controls are meaningful. No local adapter or engine rerun
was made. The hash-checked composition audit is saved as
`terminal_composition_v5.json` beside the pin-qualified R request.

The unchanged source and report are saved under the local results root as
`sense-rz100-minimim-blackbox-r-20260923-r1`; its `audit.json` is the
machine-readable boundary finding. The bounded-tool receipt is under the
private verification directory. These local evidence locations are not
portable dependencies.

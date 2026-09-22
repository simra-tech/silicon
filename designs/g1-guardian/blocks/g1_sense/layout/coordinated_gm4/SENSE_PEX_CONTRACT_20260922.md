# Source-preserving SENSE parasitic diagnostic contract

This is preparation for an **unfilled isolated-candidate diagnostic**, not
adoption or final full-chip extraction. The stock-passing native candidate is
SHA256 `6609a77884a0009924422bf9871ea699e2393c8988412e1b000057cf3448beda`;
the electrical source remains
`baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877`.
Its58 logical MOS,98 resistors and3 MIM devices must remain source-defined.
The51 failed stock-written asymmetric A/P annotations are not imported into a
new electrical source. Model cards and all rule decks remain unchanged.

## Geometry and extraction gate

Create a separate flat, uniquely named extraction view. Every native/conductive
and mask polygon layer must have zero XOR to the stock-passing candidate after
save/reload; only pin annotations and hierarchy may differ. Keep MIM36/0 and
Vmim129/0: no manual MIM deletion or inferred replacement. Every source net label
must lie on its proven connected metal component, all source nets must have
distinct labels, and all original835 channels/893 strips/98R/3MIM must survive.
The original production-candidate interface remains nine pins; the extraction
view's internal diagnostic labels do not change it.

Use the unchanged pinned KLayout-PEX0.3.12 native `--blackbox true` option for the
first one-thread2.5D `--mode CC` pilot. Its installed source excludes computed
resistor/capacitor device regions and retains those native devices in the
expanded netlist. It also disables copying device cells into the capacitance
geometry. This is source-code evidence of intended behavior, not yet measured
coverage or proof that all primitive parasitics are excluded appropriately.
The actual nonempty/excluded layer inventory and output devices must be audited.
Preserve the historical default-whitebox MIM `<TODO>` failure; do not rerun that
known failure or automatically fall back to deleted MIM geometry.

After a fresh global resource gate, the first KPEX child is bounded at180 seconds
plus5-second process-group cleanup, CPU6/thread1, with1GiB forecast/output
acceptance on the dedicated external results filesystem. Source/view/reference,
installed tool implementation/technology/deck hashes are bound before and after.
Missing output, nonfinite/negative capacitance, unidentified source nets,
unsupported-layer warnings, timeout or a nonzero exit fails the corresponding
gate. Extractor completion alone is not source-mapping or model acceptance.
Resistance extraction, fill/density and final whole-chip RC are not run here.

## Electrical mapping gate, not yet run

Only independently identified external parasitic elements may augment the exact
source. Do not convert the stock-extracted MOS/R/C records into the golden
devices, substitute stock averaged A/P, drop ng or resize the main69×23µm MIM to
the baseline23×23µm value. All source device identities and parameter strings
must be retained; any auxiliary ports exposing internal OTA nodes require an
explicit bijective map and a zero-parasitic same-source equivalence control.
Every parasitic node must map to a proven source net, substrate, or a separately
identified floating physical conductor. Unknown nodes do not silently become
ground. Floating-node reduction needs its own charge-conservation/finite-matrix
gate; no unreviewed deletion or capacitance fitting is permitted.

The geometry audit supports source-default **allocation**, not intrinsic PSP
ownership for shared physical junctions. Pinned equations establish I/Q
additivity only at common internal bias/model/temperature/limiting state. The
actual non-RF cards retain junction/body series resistance; random effective
width changes junction edge terms, and channel mismatch can change internal
voltages. Common external terminal voltage therefore does not close this gate.

Remaining evidence needed for an engineering applicability decision is a
source-card-preserving split-versus-independent junction control over actual
source/body voltages, temperatures and qualified mismatch perturbations, with
prospective current/charge error bounds tied to the SENSE error budget. It must
separate blackbox/extraction attribution error from physical shared-junction
modeling. No such electrical comparison, tolerance waiver, compiled-model
rebuild proof or adoption is asserted by this contract. The independent-array
native control remains valid evidence; sacrificing matching to adopt it would
be a separate consequential design decision.

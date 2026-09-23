# SENSE native MIM extraction-boundary control

The native geometry/type preparation passed, but the required external-field
coverage gate **failed**. No capacitance extraction or electrical simulation
ran in this control. This is not a simulated zero capacitance or an observed
numerical omission. No model cards, rule decks or canonical geometry changed.

## Built against

| Item | Identity and establishment |
|---|---|
| PDK | IHP SG13G2 commit84374023ee8b4b126bebbba67fcbada0a9c0ff0b; live COMMIT and file hashes |
| Image | ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2; immutable runtime check |
| Magic | 8.3.678; actual version/banner and unchanged technology-load check |
| Required Magic | 8.3.617; exact technology file, not its older README requirement |
| KLayout | 0.30.9; live module assertion |
| Source | baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877 |
| Native macro GDS | 8060e30ac14a1c4aeb1cf62204c9e95d9a68dbad3d73412fbb34c6a33be8b4f7 |
| Preserved buffer GDS | 320df90ee046c73b628005da9384c80fbd21a715a39b0e8b96b10923726fc500 |

The technology-load warning about Tcl/RLIMIT_NOFILE is retained. Its list
of unsupported non-electrical types is also retained; none occurs in this
isolated MIM drawing. This does not waive those types for a full macro.

## Authoritative ownership and unresolved scope

The pinned model explicitly says, “top/bottom plate parasitic capacitance
is included by parasiticC extraction!” The model retains intrinsic
area/perimeter C and55mOhm series R. Its stale adjacent Metal3 comment is
not used as native layer identity. [Pinned capacitor model](https://raw.githubusercontent.com/IHP-GmbH/IHP-Open-PDK/84374023ee8b4b126bebbba67fcbada0a9c0ff0b/ihp-sg13g2/libs.tech/ngspice/models/capacitors_mod.lib)

For the selected23x23um source device, intrinsic C at27C is
`529*cap_carea +92*40e-18 F`, times the existing mismatch scale. Its
perimeter contribution is3.68fF. The unchanged55mOhm series element remains
inside the compact model. No alternative internal-node attachment is made.

The normal Magic ngspice() variant separately extracts a cap_cmim primitive;
the1500aF/um2 and40aF/um intrinsic field coefficients occur in its LVS-only
variant. That separate LVS estimate is797.18fF, not a substitute for the
selected model corner or a measured capacitance. [Pinned extraction deck](https://raw.githubusercontent.com/IHP-GmbH/IHP-Open-PDK/84374023ee8b4b126bebbba67fcbada0a9c0ff0b/ihp-sg13g2/libs.tech/magic/ihp-sg13g2-extract.tech)

## Exact native control

The actual `cmim` cell from the preserved buffer was isolated, not
regenerated. Its translated drawing was proved a subset of native r8.
The complete134-source-net graph passed with no opens/shorts, binding
TOP/TM1 to XBUF/cz and BOTTOM/M5 to vped. Source XCC remains23x23um,
m=1,mm_ok=1;324 native Vmim cuts are each.42um square.

View A contains only the exact native drawing. View B adds passive P/N
route extensions and two separate foreign witnesses. Their exact shape
ledger and original/inverse saved-view checks are exported. The P/N
extensions would test retention of routing coupling on the same logical
netpair as the compact capacitor, not whole-netpair deletion.

| View | GDS SHA256 |
|---|---|
| A | 06936e73b0aac3856836e1c725567e31d17f2f765e400f990bdad4398cfa7e27 |
| B | c9ded509c3973fa9307336315dcb1d9597d9cb4879e33ff36176aa7e4a5b2a22 |

## Concrete coverage failure

The native plate area is529um2; native TOP TM1 covers514.3824um2, leaving
an exposed14.6176um2 rim. The B foreign TM2 witness covers that rim, with
no intervening conductor above it. The bottom M5 cannot shield this
above-rim interaction.

Imported Magic areas independently agree: mimcap20.0464um2 plus
mimcapcontact508.9536um2 gives529um2. The contact image plus explicit
metal6 area5.4288um2 gives514.3824um2. Contact-area abstraction is not the
same as324 physical cut polygons; full mask-output/contact inverse remains
**not run**.

The pinned TM2 rules489–496 cover allm5/allm6, not the bare cap1 rim.
The aliases in the technology file375–376 do not add bare mimcap to those
metal groups. Explicit mimcap field references are selected lower-layer
fringe interactions and LVS-only intrinsic terms; no normal cap1-to-TM2
field rule was identified. This fails the prospectively required static
coverage gate. [Pinned technology aliases](https://raw.githubusercontent.com/IHP-GmbH/IHP-Open-PDK/84374023ee8b4b126bebbba67fcbada0a9c0ff0b/ihp-sg13g2/libs.tech/magic/ihp-sg13g2.tech)

No numerical extraction was launched after the failure. Whether the engine
would ignore the rim or couple through it to another net was not tested.
No missing capacitance magnitude or complete-field error bound is claimed.

## Checks and retained evidence

| Check | Status |
|---|---|
| Binary/version/unchanged technology load | passed;1.063s wrapper |
| Exact native/source134-net ownership | passed |
| Native A/B saved drawing and type import | passed;3.143s wrapper |
| Required exposed TOP field-rule coverage | **failed** |
| Full imported cut-mask inverse | not run |
| Numerical field extraction and AC | not run; stopped at coverage gate |
| Complete PEX/model attachment/adoption | not run / not qualified |

The preparation wrapper's exit0 means artifact generation completed; its
summary explicitly records the failed field gate. Exact commands, scripts,
raw/portable hashes and output logs are in the adjacent evidence export.
Path substitutions are declared; GDS files are byte-exact. No field105
artifact is repackaged or changed; its18 context failures remain independent.

This fixture is suitable for an authoritative upstream boundary
clarification. A corrected upstream deck or another supported device-owned
method would need explicit version/method review and new validation.
Changing existing rules, inventing a missing term or subtracting an entire
global-netpair is not an accepted remedy. MOS body/gate/junction and
resistor head/BN reference planes remain separately unresolved.

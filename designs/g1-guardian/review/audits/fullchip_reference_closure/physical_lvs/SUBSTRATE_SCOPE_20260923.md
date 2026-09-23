# IO substrate scope: not an assembly omission; source intent unresolved

The current fullchip assembler retained the entire pinned IO CDL byte-for-byte.
That library contains no `.GLOBAL` directive; none was dropped during assembly.
The installed `.spi` and `.spice` views also contain no such directive and are
byte-identical (`1d53ab7df431b717ef5aff43e1117c0224681d5cc84886da37a319280ee958d6`).
This is evidence about the delivered source, not permission to infer missing
global semantics or edit its device parameters.

## Pinned reader controls

Three isolated two-instance controls use the unchanged stock reader and
three-terminal RPPD records. Without a global declaration, the two `SUB!`
nodes remain separate. With explicit `.GLOBAL sub!`, they become one node.
Declaring only `.GLOBAL other!` leaves both `SUB!` nodes separate. All device
parameters remain identical in these controls. Their successful run completed
in 5.601 seconds. The initial invalid two-terminal RPPD fixture failed before
this control and is retained separately.

This agrees with SPICE's documented distinction between local subcircuit
nodes and nodes explicitly declared global; the name suffix alone is not an
established contract for these readers. See the official
[ngspice manual, sections 2.5–2.6](https://ngspice.sourceforge.io/docs/ngspice-43-manual.pdf).
No additional ngspice electrical simulation was run for this reader study.

## Actual reachable source and native terminals

The source-faithful prefix-only tap adapter exposes 386 reachable PTAP1
occurrences: 151 TIE terminals at VSS and 235 at IOVSS, with **243 distinct
WELL nodes** after literal hierarchical source expansion. All original A/P
and terminal statements remain unchanged. The unadapted source reader failed
to recognize these original X-prefix tap records.

The parent-connected native extraction, after unchanged stock simplification,
contains two PTAP1 devices. Independent pad-geometry probes bind their actual
terminal nets as follows:

| Native tap | TIE | WELL | A (µm²) | P (µm) |
|---|---|---|---:|---:|
| `$5` | VSS | VSS | 978.9156 | 6603.096000000001 |
| `$4` | IOVSS | VSS | 234246.6522999997 | 64107.90800000007 |

These native numbers are observations, **not replacement golden parameters**.
IOVSS and VSS remain distinct physical metal nets. A proposed `.GLOBAL sub!`
would only make the source's SUB! nodes common; it would not by itself prove
that this new common node is identical to the source's VSS node. Explicit
body/reference-plane and tap-model intent remains unresolved.

## Public generator evidence and its limit

The pinned IO README distinguishes generator-derived views from an externally
contributed CDL, then records later IO/CDL regeneration in June 2026. It does
not supply a substrate-global include contract. See the
[pinned IO README](https://github.com/IHP-GmbH/IHP-Open-PDK/blob/84374023ee8b4b126bebbba67fcbada0a9c0ff0b/ihp-sg13g2/libs.ref/sg13g2_io/doc/README.md).

The referenced generator version 0.0.4 explicitly adds `sub!` **layout labels**
to p-type guard rings and n-type DC-diode structures. Those are labels added
without an electrical net assignment; this is not an explicit global-source
declaration. See
[generator substrate-label implementation](https://gitlab.com/Chips4Makers/c4m-pdk-ihpsg13g2/-/raw/v0.0.4/c4m/pdk/ihpsg13g2/_io_compliance.py).
The generator evidence therefore supports substrate annotation intent, but
does not authorize changing this delivered CDL's electrical connectivity.

| Check | Status |
|---|---|
| Complete original IO chunk retained | Passed |
| Exact pinned reader scope controls | Passed; first fixture failure retained |
| All 386 source tap occurrences accounted for | Passed |
| Native TIE/WELL mapping to physically distinct pad nets | Passed |
| Common-substrate source intent / A/P model applicability | Not run / unresolved |
| Fullchip strict LVS | Failed; original and adapter diagnostics retained |
| Global source declaration, VSS equivalence or model change adopted | Not run |
| Statistical seed / analog simulation in this study | Not applicable / not run |

Required next authority is an explicit, independently justified source-body
contract, or upstream clarification of the delivered CDL/model intent. No
layout-derived A/P replacement, whole-net subtraction, implicit layout join,
or short between the two ground metal domains is a justified remedy here.

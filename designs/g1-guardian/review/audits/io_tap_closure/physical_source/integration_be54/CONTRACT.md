# Analog-pair full-chip comparison successor

This isolated verification view binds full-parent GDS `be54644ebfffdc85bf4ed136966a31e60f374290b9ba7bd179753aa0b038d307`.
It does not transfer the earlier `4cffddc5` comparison result to changed geometry.

The reference changes exactly the main SENSE OTA resistor length from 6.2 to
62 µm and compensation capacitor width from 69 to 45 µm. Its complete SENSE
body matches the independently qualified standalone reference `8a9c92bd` after
top-name projection. All other full-chip source bytes, terminals, models,
386 reachable tap records, current digital source, and 22 external pins remain
unchanged. The reversible syntax-only tap-reader projection is separate.

| Check | Initial disposition |
| --- | --- |
| Exact two-passive source delta and inverse | Passed |
| Wrong-value / omitted-device negative controls | Passed |
| Full-native-context local tap junction equality | Passed |
| Unchanged stock native deep LVS | Running; no result claimed |
| Saved primitive, binary64 parameter and terminal-graph identity | Not run |
| Native TM2 coverage and 24 pad rectangles → 22 actual extracted nets | Not run |
| Unprojected strict saved comparison | Not run |
| Fresh three-dummy native 12-terminal proof | Not run |
| Exact three-dummy comparison projection and negative controls | Not run |
| Projected strict saved comparison | Not run |
| Electrical tap-R applicability / sequencing qualification | Not run |
| Adoption or tape-out approval | Not run |
| Rule/model tuning or random seed | Not applicable |

The engine uses pinned KLayout 0.30.9 and PDK
`84374023ee8b4b126bebbba67fcbada0a9c0ff0b`, with unchanged stock decks.
Native extraction is bounded to 900 seconds, its independent parser to
60 seconds, and the enclosing job to 990 seconds. One CPU, a 16 GiB memory
reservation (not enforced by the rootless runtime), 2 GiB expected bulk output,
and a fresh coordinated CPU/RAM/storage gate precede launch.

Subsequent saved-data controls preserve every electrical net/device/parameter
and change only tool-generated external-pin metadata, using the independently
observed pad conductors. No name-forced net joins or comparison tolerances are
allowed. The unprojected result must be retained. Only the previously proven
three all-VDD dummy MOS records may be removed from a separate comparison
clone after a fresh actual-geometry terminal proof; electrical sources and
native device polygons remain intact. A projected pass is labelled with this
scope and does not relabel the original stock failure.

Source-bound full-parent physical checks are coordinated separately. Complete
PEX, tap resistance physics, and electrical applicability are not established
by device-aware LVS.

## First native-run outcome

The declared 900-second engine watchdog expired after 900.255 seconds
(916.468 seconds enclosing runtime). No LVS database was saved and no engine
match/mismatch result was produced. This attempt is **failed**, not a completed
electrical mismatch diagnosis. Exact input/rule parity and the output bound
passed; saved-graph, pad-interface and dummy comparison checks remain **not
run**. The last engine-log stage was layout RF MOS mapping. A bounded read-only
hierarchy/log/code inventory is the next diagnostic; no automatic watchdog
extension or deck change is authorized by this result.

Read-only hierarchy accounting subsequently passed: old/new reachable cells
293/294, expanded instances 331,797/331,798, expanded shapes
4,899,239/4,896,746, depth four in both. There is no geometry hierarchy-size
explosion. The current SENSE child names are unique and have no cross-macro
users; the prior assembly used hashed aliases for those children.

Separate unchanged native SENSE unit controls using the full-chip stock
default switches completed with actual engine matches in 7.738 and 6.893
seconds (old/current). Both have the same three resulting circuit names and
class parameter schemas, with no duplicate circuit names. Thus the changed
R/C values or default series-resistor setting alone do not reproduce the
full-context slowdown. These unit results do not establish full-chip LVS.

An explicitly diagnostic 600-second run is authorized on a copied stock rule
tree. Only tagged logging statements are added to RF mapping: class-index
entry/exit, circuit progress, sparse device progress, and purge entry/exit.
Removing those lines must reproduce the original file byte-for-byte; installed
rules remain unchanged. No result from that instrumented run receives
acceptance credit.

The profiler reached its 600-second watchdog. Class-index construction and
all circuit/device loops completed in approximately one second; `purge_devices`
also returned. The following `target_netlist.purge` call did not return before
the watchdog. No database was produced. Installed rules and inputs stayed
exact. This diagnostic localizes the hotspot; it is not a completed LVS result.

The next authorized representation control moves only the added BGR child's
33 objects (26 via cuts and seven metal landings) into their identical root
positions. It must preserve all other cell definitions, root objects, texts,
source bytes and the die, show complete affected-layer XOR equality, and
reverse the saved projection to all original definitions. It does not flatten
any device, IO or SENSE hierarchy. The candidate is based on the subsequent
`9f7bb2ed` one-fill repair and needs its own extraction result.

The representation control passed its complete XOR/inverse proof, producing
`dcca5f47`. Its subsequent unchanged-stock LVS also reached the original
900-second watchdog without a database. Thus removing that routing-only child
did not resolve the observed slowdown; this is a retained failed hypothesis.

The next diagnostic adds only an output checkpoint immediately after the
original `purge_devices` and before the original `purge`. It must retain every
stock operation and restore original copied-deck bytes when tagged capture and
logging lines are removed. A small native-DSL capture/readback control precedes
full extraction. The capture is diagnostic evidence, not LVS acceptance. The
new R100 SENSE candidate and its separate one-resistor source update are not
substituted into this dcca/R62 diagnostic.

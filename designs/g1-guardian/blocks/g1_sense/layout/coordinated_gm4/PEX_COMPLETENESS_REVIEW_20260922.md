# SENSE PEX completeness and supported-method review

The unfilled SENSE candidate remains stock-DRC/LVS passing and **unadopted**.
Recovered capacitance data are **incomplete**, not qualified CPEX. No model,
rule deck, installed tool, canonical schematic or candidate GDS was changed.
Final fill is reserved for the coordinated whole-chip flow.

## Built against

| Input | Exact identity / establishment |
| --- | --- |
| IHP SG13G2 public PDK | `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`, container COMMIT plus card/deck hashes |
| KLayout | 0.30.9, runtime Python version |
| KLayout-PEX | 0.3.12, installed-package version and implementation hashes |
| Container | `sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2`, flow identity gate |
| Source | `baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877` |
| Unfilled candidate | `6609a77884a0009924422bf9871ea699e2393c8988412e1b000057cf3448beda` |
| Extraction-only view | `cb9617c97ae522596c5d4aaa7ee91f65e59b418a14d1095e5e0514d4e8c7e010`, native polygons XOR0 |

## Completed checks and retained failures

| Check | Status / scope |
| --- | --- |
| Native blackbox2.5D CLI pilot | **failed** after108.884s: native MIM writer requests nonexistent parameter `C` |
| Exact engine-data recovery | **passed**116.554s; existing LVSDB reused, no repeated LVS;958binary64 capacitors |
| Recovery parity | **passed** all958 values reproduce original0.001fF-rounded CSV; exact binary64/hex round-trip |
| Original132-probe completeness claim | **failed**: both buffer CZ nets were omitted from the physical probe inventory |
| Independent source-derived134-net graph | **passed**101top+33OTAinternal nets, additional8native R/C terminal probes |
| Exact958-capacitor source attribution | **passed**134source nets+explicitly unbound extractor substrate; no circuit generated |
| Finite symmetric charge matrix | **passed**, maximum row residual6.71419238e−28F |
| Blackbox physical completeness | **failed**, MIM interiors and tap contacts omitted |
| Native7×7MIM3D CLI control | **failed**SIGSEGV during post-processing; solver itself completed51.33s, command73.481s |
| Saved3D mesh/solver audit | **passed scoped method coverage**, no solver rerun; not a converged SENSE extraction |
| Computed-layer partition audit | **passed diagnostic**, demonstrates a stock3D geometry-query alias |
| Intrinsic PSP shared-junction applicability | **not qualified**; prior native allocation evidence and51failed stock A/P annotations remain distinct |
| Source-preserving complete CPEX, wire R, electrical equivalence, final filled RC | **not run** |

The CLI CSV and RDB categories round capacitance values. Exact data were not
persisted by the failed writer, so recovery called the unchanged supported
`KpexCLI.run_kpex_2_5d_engine` API using the saved LVSDB and `None` for both CSV
and expanded-SPICE output paths. The engine result was then serialized directly.
No native MOS/R/C record was substituted into the electrical source. The original
failed command remains failed.

Earlier diagnostic failures are retained: extraction-view r1 lazy Region
emptiness disagreement (subsequent materialized XOR0); coverage r1's ISENSE
witness inside excluded plate material;134-net audit setup r3 omitted top ports
from its counting set, r4 used uppercase stock resistor parameter names;3D
setup r1 omitted the explicit boolean required by `--geo_check`. None was
reclassified as a passing run or hidden by a tolerance change.

## Correction:132 probes were not the complete source net set

The independent source enumeration yields134unique physical source nets, not132.
The earlier MOS/body/bank probe graph lacked `XBUF/cz` and `XREF/cz`, although
strict LVS separately checked the native RZ/CC devices and connections.
The new audit adds both1×6.2µm resistor-head and23×23µm capacitor-plate probes
from the saved native buffer geometry and frozen instance transforms. Each CZ
resistor head and capacitor top lands on the same physical component, distinct
from the resistor's `out1` end and capacitor's output/bottom. Cross-checks find
exactly one source-sized native resistor and capacitor per buffer with those
same extracted terminal memberships: `$192` for XBUF and `$193` for XREF.
This is geometry and source evidence, not a guessed anonymous-node name.

The corrected134-net audit passes without changing the source, GDS, labels,
stock database or rules. All958raw capacitances are attributed to that complete
set plus `VSUBS`. `VSUBS` is explicitly left unbound: it is the extractor's
synthetic substrate conductor, not automatically simulation node0 or source VSS.

## Actual omitted geometry

| Region | Native whitebox area | Native blackbox area |
| --- | ---: | ---: |
| Metal5 under the3MIM plates | 2645µm² | 0 |
| MIM top metal | 2645µm² | 0 |
| Vmim | 285.768µm² | 0 |
| Tap contacts outside the poly/nSD/pSD typed contact sets | 558.1824µm² | 0 |

All558.1824µm² of missing raw contact material lies in actual ntap/ptap regions;
the missing area outside taps is exactly zero. Thus the `cont_drw` warning is
not merely a duplicate-layer warning. Electrical importance and a complete
supported tap-contact representation have not been established.

The pinned `capacitors_mod.lib` has only a two-terminal intrinsic `cap_cmim`
with55mΩ series resistance and a temperature-dependent capacitance model. Its
comments explicitly assign top/bottom plate parasitics to extraction. The
missing bottom-to-substrate coupling cannot be absorbed into, or waived by,
that intrinsic model.

## Small supported3D control and its limits

An unchanged native7×7µm cmim coupon was run with the supported whitebox
FasterCap path, all installed dielectrics and default0.05 solver tolerance.
The saved geometry check reported no errors. The solver converged to a last
relative matrix change0.0244779, then stock netlist post-processing crashed.
The saved matrix gives bottom↔substrate entries1.35960/1.37331fF before any
reciprocity averaging. Saved triangles show49µm² of MIM top underside and the
native67.24µm² bottom metal. Those findings establish actual missing-coupling
coverage in this small method control, not accuracy over SENSE/PVT/fill.
The matrix has only stock console print precision; parsing does not create
additional solver precision. No whitebox capacitance was adopted.

A distinct geometry-query problem is demonstrated, not inferred solely from
the matrix. The stock context retains separate computed regions by name but
`FasterCapInputBuilder` retrieves them through their common GDS67/0 pair.
Both `metal5_cap` and `metal5_n_cap` queries therefore return the entire Metal5
union. The saved coupon's MIM-dielectric-facing bottom surface spans67.24µm²,
not just the49µm² intended computed capacitor region.

Independent partition checks on the actual source layouts pass:

| Case | M5cap | M5noncap | Sum / native M5 | Intersection / native XOR |
| --- | ---: | ---: | ---: | ---: |
| Full SENSE | 2645 | 1010.1748 | 3655.1748µm² | 0 / 0 |
|7×7coupon |49 |18.24 |67.24µm² |0 /0 |

The raw computed M5cap equals native Metal5 intersect native MIM exactly.
Thus a **generic geometry-adapter repair is feasible**: select the exact
`KLayoutExtractedLayerInfo.lvs_layer_name` first for computed-layer queries,
preserve its net properties, and use canonical GDS grouping only for canonical
layer requests. A future repair must enforce those partition/XOR gates, all
per-net memberships, and unchanged process dimensions/permittivities. It would
be new extraction software requiring review and control checks; no such adapter
or tool/technology patch was implemented in this inspection.

## Intrinsic/extrinsic composition remains the technical blocker

The installed3D `NetlistExpander` whitebox branch removes **all native devices**
before creating a full net-pair capacitance network. That is not a
source-preserving CPEX path. Blackbox retains native devices but removes their
geometry, causing the demonstrated extrinsic omissions.

Inspection found no supported primitive-aware intrinsic/extrinsic decomposition:
the3D builder accepts conductors by net, region, height and material; it unions
them by net and generates surfaces keyed by net/material. The solver/parser
returns a net-conductor Maxwell matrix. It does not preserve a native-device
versus routing/fringe contribution to a same-net-pair matrix entry. The2.5D API
does retain layer/net overlap and sidewall categories before summarization, but
not a native-model intrinsic/fringe ownership partition; the prior unsupported
whitebox MIM path remains failed.

Consequently, replacing the canonical temperature/mismatch-aware MIM with the
whitebox linear pair, appending that whole pair, deleting all same-pair coupling,
or subtracting a chosen golden capacitance is not justified. Repairing the
computed geometry alias alone does not solve this composition problem.
Complete source-preserving MIM PEX needs a justified extractor/model boundary
with native-plate versus extrinsic/routing attribution, or a separately reviewed
method whose completeness and model composition can be demonstrated. No such
boundary is supplied by the inspected pinned APIs. Full-macro3D is **not run**.

## Substrate and intrinsic junction boundaries

The3D builder creates a virtual substrate slab under the expanded layout box,
independent of named circuit nets, and removes enlarged diffusion regions from
it. The stock expander later shorts its generated VSUBS/FC_GND nodes to a new
GND node; this is software behavior, not proof of the chip's finite ground-return
network. The mapped raw data therefore retains an explicitly unbound substrate
identity until the physical/electrical substrate-reference contract is reviewed.

The earlier PSP source-equation review still applies: junction current/charge
are additive in geometry coefficients only for common **internal** junction
bias/model/temperature/limiting conditions. The pinned non-RF model retains
series junction/body resistance, and mismatch can change effective geometry
and internal voltages. Correct source-default native A/P allocation and strict
LVS do not alone prove shared-junction model applicability. No new simulation,
model-card modification, extracted-A/P fitting or applicability waiver occurred
in this software-method inspection.

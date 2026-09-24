# Folded soft-input-pair physical milestone

Status: scoped physical checks passed; **not adopted**. This record describes
computed layout verification, not hardware measurement or electrical population
qualification.

## Built against

| Component | Identity | How established |
| --- | --- | --- |
| IHP SG13G2 open PDK | `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` | Frozen run bindings and saved stock-check summaries |
| KLayout | 0.30.9 | Runtime version recorded by the density/antenna runner |
| Runtime image manifest | `sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0` | Pinned flow provenance |
| Runtime image configuration | `sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2` | Explicit launcher image identity; distinct from manifest |
| Rules | Stock PDK main, maximal, density, antenna and LVS | Saved input/rule-held checks; no rule modifications |

## Exact candidate and scope

The external artifact inventory in [evidence.json](evidence.json) pins the original
parent, canonical CDL, candidate GDS/CDL, comparison reference, generators and
saved reports by SHA-256. Candidate GDS is
`60730627d24e1fb6b880138edc3e50fdd7c14624bb2dfbbc631e084b7415eca1`;
canonical candidate CDL is
`984f82ddddf256f7077efc614850e15238ac910f6782c5f6d09140da88027f73`.

Only the soft comparator input NMOS pair changes from W12/L0.34 to W24/L0.68
micrometres: four 6-micrometre fingers per transistor, unchanged W/L, fourfold
gate area. This is **not** the hard regenerative-pair change.
The isolated parent keeps the 1414-micrometre die, original instances, non-target
cells, root geometry, fill and external macro pins. The independent geometry
audit checks those invariants. The necessary local soft-output q feed moves
2.8 micrometres; the local soft VSS label follows its moved ring. No parent input
or central VSS feed was rerouted.

## Completed checks and retained failures

| Check | Status | Saved result |
| --- | --- | --- |
| Independent non-target/soft-cell/q-feed geometry audit | passed | Exact preserved context and bounded target delta |
| Stock main DRC | passed | 0 markers; completed main stage 487.47 s |
| Original combined main/maximal invocation | failed | External timeout, return code 124 at 1151.67 s; original record retained |
| Separate maximal-only DRC | passed | 0 markers; 987.33 s wrapper |
| Stock density | passed | 0 markers; 55.18 s |
| Stock antenna | passed | 0 markers; 153.60 s |
| Stock-reader comparison-reference roundtrip | passed | 76,059 primitives and 22 pins |
| Projected strict full-parent LVS | passed | 11 checks; 61,684 combined devices, 31,173 nets and 22 pins |
| Native junction/geometry inventory | passed | Both folded input devices independently identified |
| Canonical, unprojected full-parent LVS | **not run** | Three all-VDD IO-pad PMOS purge discrepancy remains |
| New native CPEX and loaded-field electrical checks | **not run** | No extracted-field acceptance inferred |
| Electrical population qualification / source adoption | **not run** | No earlier schematic population credit transferred |
| Final integrated acceptance / hardware measurement | **not run** | This is a scoped physical milestone |

The maximal-only run reused the completed main report; it did not rerun main or
erase the combined timeout. The first invocation requested the stock default
128 threads but was constrained to one CPU and observed with one thread;
the successor requested one thread explicitly. Geometry-preparation API/layer
alias failures and the first cell-ID-based observer failure remain in their
original attempt records; the successful semantic geometry audit does not
relabel those attempts.

The LVS reference removes exactly three previously identified all-VDD IO-pad
PMOS devices to match stock-reader purge behavior. That reversible
**comparison-only** projection is not the canonical circuit definition and does
not establish unprojected LVS.

## Junction and mismatch boundary

Each native soft input transistor has four gates of 6 by 0.68 micrometres
(total channel area 16.32 square micrometres). Five diffusion strips have areas
2.04/2.28/2.28/2.28/2.04 square micrometres and perimeters
12.68/12.76/12.76/12.76/12.68 micrometres.

After normalizing the stock source/drain-symmetric labeling to circuit ownership,
the routed XP/XQ drain owns strips 0/2/4: AD=6.36 square micrometres,
PD=38.12 micrometres. The TAIL source owns strips 1/3:
AS=4.56 square micrometres, PS=25.52 micrometres.
The stock combined-device averages AS=AD=5.46 and PS=PD=31.82 are not substituted
for those independently routed values.

A schematic ng=1/default-junction transistor is not thereby equivalent to this
folded device. The ng=4/explicit-junction source-local diagnostic, its primitive
ownership, mismatch mapping and own calibration require separate electrical
qualification. This milestone neither inherits prior codes nor assumes
independent random draws for individual fingers. Stored intrinsic charge and
complete extracted-field modeling are not established.

## Reproduction and provenance limits

`${BULK}` denotes an operator-supplied external artifact root,
`${PDK}` the pinned public PDK, `${REPO}` this repository and
`${TOOLS}` the external frozen helper bundle. Original saved JSON/logs remain
untouched. The inventory hashes and byte lengths refer to those originals.
Only path locations were sanitized in derived commands; numerical options and
result values are unchanged. Administrative ownership metadata is omitted.

The helper sources are hash-bound external inputs, **not included here**.
Consequently this is an evidence/command inventory, not a self-contained public
reproduction package. Restore the exact hashed helper bundle and its pinned
dependencies before executing its commands; do not substitute a similarly named
script. Bulk GDS, reports and unchanged ancestors are not copied into this record.

Preparation command forms (output locations must be fresh):
```sh
python3 ${TOOLS}/prepare_soft_inputpair4_folded_native_r1.py --output ${BULK}/soft-inputpair4-folded-native-20260924-r1
python3 ${TOOLS}/prepare_soft_inputpair4_parent_r3.py --output ${BULK}/soft-inputpair4-parent-20260924-r3
```

Exact location-normalized stock DRC/LVS argv and the maximal-only wrapper command
are in `evidence.json`. The LVS command consumes the separately proved comparison
reference, never the canonical source as if they were interchangeable.
The density/antenna independent saved audit is bound by original SHA-256
`9c3350e7e6c4520262b537748189c3bcbf37dc51cd1daa5643ab37194a1eac4c`.

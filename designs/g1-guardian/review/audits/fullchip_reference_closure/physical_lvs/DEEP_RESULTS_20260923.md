# Current fullchip deep LVS: failed, localized evidence retained

The unchanged stock **deep** comparison of the current routed/sealed native
chip failed. It completed in 124.758 seconds; its wrapper returned zero, but
the actual engine explicitly reported that the netlists do not match. The
saved cross-reference contains 20 reachable circuit pairs on each side:
3 `Match`, 14 `NoMatch`, and 3 `Skipped`. No skipped parent or
`MatchWithWarning` is accepted as a pass.

## Exact inputs and scope

| Input | SHA256 / identity |
|---|---|
| Sealed native GDS | `3a24f4d76b3d91141d09515e498383ec36bec4f5bbcffbb7a53456f82259c0e9` |
| Original source, top-name-only interface | `f4ce6848bd7dd179d2ef4cbd8a4ea6bf9788bcfa1ff4b93fabae8bf18b6378f9` |
| Actual saved LVS database | `1c8f3f91b8be00e0fbbdf4c2a40734fb5f8fe8b0388b1780768699e1a2afcbcf` |
| Actual engine log | `e1e14cd9e4378f29db70f1b285a924bc11fe5402afbc06233ed274a2d186c2a8` |
| PDK / KLayout | `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` / 0.30.9 |

The current source covers the separately audited 4,904-instance source graph.
Post-alignment/simplification expanded device counts are 61,516 layout and
61,237 reference; these are observations, not equality to unsimplified source
counts or proof that an omitted device is harmless. No source, model, rule,
native geometry or physical port was altered by this comparison.

## Parser failures are separate from real LVS failure

The initial preflight attempt did not launch extraction: it mistakenly bound
the portable reference export to the original reference hash. A separate
correction uses the original source and proves that the portable view differs
by exactly one path-comment projection. Both attempts remain retained.

The first saved-result parser then incorrectly treated the uppercased SPICE
reference top as absent and expected the disabled ignore-port switch to print
literal `false`. In the pinned Ruby deck, `false || nil` prints blank while
entering the explicit strict comparison branch. Revision 3 resolves only
unique case-folded top names and requires the actual strict/missing-port
enforcement messages. It confirms both original reference-top existence and
the exact 22 reference pins. The engine mismatch and saved failed pairs are
unchanged. An intervening parser regex error and a later malformed test-log
newline fixture are preserved as failures, not silently overwritten results.

Revision 4 additionally requires unique unrelaxed option values and observed
mode equality. Its corrected test set passes 25 saved-positive/negative
controls: actual same-name/child-alias matches, wrong wiring/top, parameter
warnings, missing reports, nonzero exit, contradictory results, case-fold
collision, ignored ports, implicit joins and wrong/duplicate/missing modes.
These controls validate the result harness, not the failing chip.

## Specific current native/source discrepancies

The 14 failed children are the nine Clamp variants N15N15D, N20N0D, N2N2D,
N43N43D4R, N8N8D, P15N15D, P20N0D, P2N2D, P8N8D; DCNDiode, DCPDiode,
LevelUpInv, RCClampInverter and SecondaryProtection. Every current failed
cell has zero polygon XOR to the pinned stock cell across every layer.

- **Parent-connected fingers:** all 31 duplicated-name clamp/diode terminal
  groups map, by their actual child pin IDs, to a single physical parent
  cluster in every current instance. This is not an implicit name-based join.
  For example, eight distinct N15N15D `pad` nets all connect to parent cluster
  20; their widths sum to the source's 66 µm. Other width sums retain ordinary
  binary64 summation differences rather than inventing an exact numeric pass.
  These facts support a separate documented flat-mode diagnostic, not a deep
  comparison waiver.
- **Tap binding:** the held source retains 63 original `X... ptap1/ntap1`
  records in 41 library cells. The unchanged stock reader does not bind these
  X-prefix records as tap primitives. The source records exist, but their
  empty unresolved subcircuits disappear before comparison. A separate
  syntax-only adapter changes unique identifiers/prefixes, with exact reverse
  reconstruction and byte-identical node/model/parameter suffixes. It does
  not change source A/P to match extraction or cure the known A/P conflict.
- **Resistor recognition:** SecondaryProtection lacks PolyRes 128/0, so its
  source W=1 µm/L=2 µm series resistor is absent from the extracted child and
  `core,pad` merge. Earlier unchanged-deck unit evidence already localized the
  marking-layer remedy. See the separate
  [recognition proposal](POLYRES_REMEDY_PROPOSAL_20260923.md); it is not adopted.
- **Diode dimensions:** two native DC-diode devices each have A=35.0028 µm²,
  P=58.08 µm, m=1; the source has A=35.003 µm², P=58.08 µm, m=2. Effective
  areas are 70.0056 versus 70.006 µm². This discrepancy is reported, not
  adjusted or independently waived.
- **Top pins:** the saved layout top lists 71 internal-name pins while the
  source has 22 external pins. Independent coordinator inspection found the
  expected 22 labels already in the actual native hierarchy. Thus adding
  labels or deleting internal annotations is not justified by this result.
  The pinned `make_top_level_pins` API and hierarchy representation require
  separate diagnosis; electrical connectivity proofs do not substitute for
  matching the actual extracted source interface.

The comparator, passive conditioner and DAC child pairs match. The chip top,
GateLevelUpInv and LevelDown are skipped. Consequently this run establishes
no fullchip device equivalence, even though separate metal-only terminal
audits passed.

| Check | Status |
|---|---|
| Exact native/source/deck/runtime binding and bounded execution | Passed |
| Actual deep strict engine comparison | Failed |
| All saved reachable circuit pairs accounted for | Passed, 20 per side |
| Exact source-top pin set | Passed, 22 |
| Extracted layout-top pin set | Failed, 71 internal-name pins |
| Current 14 failing IO cells equal stock polygon geometry | Passed |
| Actual parent joining of all 31 duplicate terminal groups | Passed |
| Parser failure-propagation controls | Passed; prior harness failures retained |
| Source-derived tap syntax adapter preparation | Passed; not adopted |
| Original IO tap A/P applicability and full IO LVS | Failed / unresolved |
| New recognition-layer derivative or electrical/ESD qualification | Not run |
| Stochastic seed | Not applicable |

The distinct flat-mode experiment has its own
[prospective contract](FLAT_DIAGNOSTIC_CONTRACT_20260923.md) and result receipt;
this report does not claim its outcome or replace the failed deep result.

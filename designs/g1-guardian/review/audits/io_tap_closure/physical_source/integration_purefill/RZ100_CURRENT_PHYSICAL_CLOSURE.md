# Current hard/R100 full-chip physical checks — 2026-09-23

This is a bounded physical-verification result, not electrical or tape-out
adoption. The exact checked GDS is `port_text_candidate.gds`, SHA-256
`3e3634389aff5126d0f55f6814466ad179f6d1280e9152c62a07ab5ea3d105bf`.
The IHP SG13G2 PDK commit is `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`;
KLayout is 0.30.9. Stock rule decks, model cards, device parameters,
acceptance tolerances, and strict missing-port handling were not changed.

| Check on this exact GDS | Status | Evidence SHA-256 |
| --- | --- | --- |
| Stock deep LVS, strict top ports | passed | saved analysis `21087fccfe5567a32057a81640a8cc1f8020f5baad23509c950fe90c3cc9be64`; LVS DB `85da9080314fba5e7b8bebee040f4802cb8843d0823d84bf3be2fe04e3c4a4ab` |
| Stock density | passed, zero markers | summary `010d79cc34e6f43dea20a5696557a5b6d2bbe71c39da4cd9af899d6899ee2e50` |
| Stock main DRC | passed, zero markers | summary `2ccab0278d681639066369015ab8c20e8124606d6cdada87570419cbce509d1c` |
| Stock maximal DRC | passed, zero markers | summary `488d56dc340a5fc558339001d49d7975c0c88f9c536d018b4850ed72c4618295` |
| Stock antenna | passed, zero markers | summary `0c26c6db309a589b146f794aba905baed6808498855bed82b9e72b157474ee1e` |
| Successor 24-opening/22-net bondmap | passed | summary `8b7b1e37a25e1f0e2d691a52030ae854a4da2372ba2f3cc3526dfcafcf58722b` |
| Full-chip PEX, current IR/EM, post-integration electrical adoption | not run | — |

The strict stock LVS engine reported “Netlists match,” zero warnings and zero
errors, with `flag_missing_ports` enabled. The saved comparison has exactly
61,684 matched devices, 31,173 matched nets, and the 22 specified external
pins; one extracted `rppd w=1u l=100u` RZ100 device is present. The reference
is a primitive-flat, stock-reader/writer roundtrip of the current full-chip
source, SHA-256 `784358b6e8955b14a7ef9445d5fd1faa41f0ad988c3d30bdd8bd37fcd4e66433`.
Its independent roundtrip proof is
`5d87c17cd6b3f69205be5a1feebd4abd3fa6744a7587f95e43ebfd533bf46008`.
The comparison-only source removes exactly three proved source-only,
VDD-to-VDD dummy PMOS devices; no other source primitive, parameter, net, or
external pin is omitted. The native-terminal proof is
`d9be7112004e2bed148da9ff63f74c4f0375ed42c0109bca5e1f87c0af9224aa`.
This scope does **not** turn the unprojected canonical-source LVS into a pass.

The maintained fill keepout stage is [keepout_rz_fill.py](keepout_rz_fill.py).
It accepts an explicit input, pins the qualified pure-fill input SHA-256
`6b9c5878a81a0ac4d3f68d3d8dbb5fa1927442675606aa6bd46a14d6552def51`,
asserts 0.001 µm DBU and the current RZ100 marker/instance location, rejects
nonpolygon fill objects, and requires exactly 20 active-fill and 19 poly-fill
deletions in the narrow resistor window. Its output GDS SHA-256 is
`5d121548bb9406f8229fdca7e7e26c1c3e6581ad1b0745f8a2cfce4615af8684`;
the independent exact geometry proof is
`396c2f5f9aed2dbba607f63dff7feb9b59979aa2a4ca235c9f4b340901a81a71`.
Regeneration from the pinned input produced 6,712,041 identical GDS records
except the 281 creation-date payloads; no other record differed (proof
`7ab55cde047a2193f1593983537a4f0d011260babfbc798b6911e0ce00874d9a`).
A changed R100 or fill input must be requalified; the script will not silently
apply this keepout to a different GDS.

The strict-port representation stage is [normalize_rz_port_text.py](normalize_rz_port_text.py):
it promotes the exact 22 existing pad-conductor labels to the root and
suppresses 86 net-mapped internal annotation occurrences responsible for 81
synthetic top pins. It uses 38 instance-local clones so unrelated uses of
repeated standard cells retain their labels. The independent serialized-GDS
proof made by [prove_rz_port_text.py](prove_rz_port_text.py) has result SHA-256
`75f2f46c552c79804568729ddef675f08636211ec737b55b3935cde2903e91af`,
establishes unchanged reachable nontext shape records and instance transforms,
arrays, and properties; therefore flattened nontext geometry is identical.
The parameterized stage reproduced 6,719,503 GDS records, differing only in
307 creation-date payloads (proof
`4f30a3f3aed7ab941802f8a48294a5a01d0e52285176cbdba603443b62ed7d32`).

The original keepout GDS without root-text normalization still has a **failed**
strict stock deep LVS despite a matching saved primitive graph. A separate
stock flat extraction **timed out** before comparison. Both remain retained
as failures; neither is reclassified as a pass. The exact checked GDS and
large reports are held in bulk storage by the artifact identifiers above,
not duplicated in this repository.

The first text-candidate main and maximal DRC launches were **failed before
rule execution**: their direct child-mode invocation omitted the parent
wrapper's report-directory creation. Those `r1` launch logs remain retained;
the `r2` parent-mode runs in the table are separate, fresh-gated stock checks.

The successor [current_rz_bindings.py](current_rz_bindings.py) preserves the
earlier bindings and keeps the canonical `94e50a2a…` circuit source distinct
from the comparison-only flat reference. The maintained
[build_current_rz_candidate.py](build_current_rz_candidate.py) selection
manifest binds the pure-fill → keepout → port-text stage hashes, independent
date-only regeneration proofs, strict stock result, four physical reports,
and [successor bondmap](../../../../../padframe/bondmap_candidate_20260923_r2.csv)
without regenerating geometry in that invocation (manifest SHA-256
`173f0c572958788da39032ee4fc9dc2baa9cd912da3fa72b7b14f24b09b4d9b2`).
The new map changes only the candidate GDS SHA relative to the earlier 24-row
candidate map; [validate_current_rz_bondmap.py](validate_current_rz_bondmap.py)
independently verified all 24 actual opening geometries and pad-centre
extracted net clusters against the 22 strict LVS top pins. It did not change
bonding names, sides, openings, die outline, or circuit interfaces.

[run_current_rz_stock_lvs.py](run_current_rz_stock_lvs.py) is the successor
strict-port stock runner. Its existing-evidence validation passed (summary
SHA-256 `1fb72a13b7c3dab6c81c907d1d951ddda8cdebde4017de4c2fb2b31cf052967f`);
its new-engine execution mode is **not run**. The separate direct stock run in
the table is the actual LVS result. Earlier bindings, source, GDS, map, and
failure evidence were not overwritten.

The wrapper verifies the pinned stock LVS rule tree (53 files) and full
physical rule tree (131 non-bytecode files) before execution and after any new
engine run. One transient generated `.pyc` cache in the older physical-summary
inventory is excluded; no source or rule file is excluded. It requires a
single CPU0 affinity and a fresh coordinated resource gate with 16 GiB RAM
and 2 GiB bulk reserve. Pure negative controls rejected an altered rule hash,
multiple CPUs, a wrong CPU, and a CPU absent from the ledger (summary SHA-256
`195bbecc15320c2980c771c8ebaed6253ee0aca1da9d8b1db163cdd46891e5c0`).

The recorded stages are individually reproducible with fresh output names.
`G1_RESULTS_ROOT` denotes the dedicated bulk artifact root and `D` denotes
`designs/g1-guardian/review/audits/io_tap_closure/physical_source/integration_purefill`:

```sh
flow/run.sh python3 "$D/flatten_current_fill.py" --output "$G1_RESULTS_ROOT/<fresh-purefill>"
flow/run.sh python3 "$D/keepout_rz_fill.py" --input "$G1_RESULTS_ROOT/current-purefill-flat-20260923-r1/pure_fill_flattened.gds" --output "$G1_RESULTS_ROOT/<fresh-keepout>"
flow/run.sh python3 "$D/normalize_rz_port_text.py" --input "$G1_RESULTS_ROOT/current-purefill-rz-keepout-20260923-r2/rz_fill_keepout.gds" --paths "$G1_RESULTS_ROOT/current-purefill-rz-pin-paths-20260923-r3.json" --ports "$G1_RESULTS_ROOT/current-purefill-rz-keepout-port-overlap-20260923-r1.json" --reach "$G1_RESULTS_ROOT/current-purefill-rz-keepout-port-reach-20260923-r1.json" --gds "$G1_RESULTS_ROOT/<fresh-port-text>/port_text_candidate.gds" --proof "$G1_RESULTS_ROOT/<fresh-port-text>/transformation.json"
```

Each stage requires the pinned input/proof and a fresh resource gate. The
keepout and port-text regenerated GDS streams were independently compared
record-for-record against the checked artifacts, allowing only GDS creation
timestamps. The comparison-only reference was made by the stock-reader
[flatten_rz_reference.rb](flatten_rz_reference.rb) from the exact three-dummy
projection, not by changing the canonical circuit source. The successor
build script validates and selects already qualified stage artifacts; it does
not regenerate them.

A single-command geometry regeneration is implemented by
[rebuild_current_rz_candidate.py](rebuild_current_rz_candidate.py). With a
fresh resource gate, one allocated CPU and owner CPU permission, run it inside
`flow/run.sh`:

```sh
G1_CPUSET=0 G1_CPUS=1 G1_RESULTS_ROOT="$G1_RESULTS_ROOT" flow/run.sh python3 "$D/rebuild_current_rz_candidate.py" --input-root "$G1_RESULTS_ROOT" --output-root "$G1_RESULTS_ROOT/<fresh-rz-rebuild>" --resource-gate "$RESOURCE_GATE"
```

The 2026-09-23 CPU0 execution **passed**. Its `rebuild_summary.json` SHA-256 is
`0a5ba14312812c7ff496f50cd0da865affe8c698c2668eac42a30c4f4af7bc91`;
the fresh resource-gate SHA-256 is
`ccd8c72f2bb30dd0ebaa0dcde7d7e2aaa4483ff283eb6656e1f8ced3671e5618`.
Reproduced purefill, keepout and text GDS SHA-256 values are respectively
`667ba195d107acc8f6edd9717ed5b48581db3e6a7c04980b0e336e83ac3dd48a`,
`8ec608c97cc1338fa1a6fe6116b7782c0cd1114cec71a68625f021a7c20a89b1`,
and `485ba56fefada62ec8bec20343f57e210b6ce3dd8b9909a0cb4ae980488a0cc5`.
The three streams have respectively 6,712,236, 6,712,041, and 6,719,503
records; every nondate record is byte-exact against the accepted artifact.
Only GDS creation timestamps differ (281, 281, and 307 date records).
The independent text proof retained all nontext geometry, 22 external names
and 86 exact internal text removals. LVS, DRC, density, antenna, PEX, IR, EM
and electrical adoption were **not run** by this command.

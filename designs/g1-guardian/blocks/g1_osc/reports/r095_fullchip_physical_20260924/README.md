# R0.95 full-chip physical verification

The isolated candidate passed four stock physical checks and strict LVS against
its independently justified comparison-only source. This is not production
adoption, electrical qualification, or an unprojected canonical LVS pass.

| Check | Status | Evidence |
| --- | --- | --- |
| Main DRC | passed | 0 markers; 435.49 s |
| Maximal DRC | passed | 0 markers; 697.29 s |
| Density | passed | 0 markers; 53.96 s; native EdgeSeal boundary |
| Antenna | passed | 0 markers; 169.65 s |
| Three native all-VDD pad-device terminal proofs | passed | independent source, geometry, and terminal graph |
| Comparison-source flatten round-trip | passed | 76,059 devices, 31,906 nets, 22 pins |
| Projected-reference strict stock deep LVS | passed | 11 checks; 61,684 devices, 31,173 nets, 22 pins |
| Previous canonical source/layout comparison | failed | retained stock-purge discrepancy; not reclassified |
| New candidate unprojected canonical LVS | not run | projected result is not a substitute |
| Affected electrical populations and full-chip extracted simulation | not run to completion | separate campaign acceptance required |
| Hardware measurement | not applicable | simulation/layout-only checkpoint |

Three physically present pad PMOS devices have all four terminals tied to VDD.
The stock target extraction purges these devices while the canonical source
retains them. The comparison source removes exactly those three devices, with
an exact reversible source proof and independent native-terminal proof. No
PDK rule deck or model card was modified; missing-port checks remain strict.

The new GDS SHA256 is
`18b897feb06b7a02508ea8734d40845d69bcb515955368daba9dd1938a1949c9`.
Canonical CDL remains separately bound to
`126acd51cae404f55e9a3470d521d0d90f5115e668fbf393ac48c492e4507333`.
The saved LVS database SHA256 is
`07ec16320f4b2e7e17c8bcf34a48d2bc433d41176738f4a74188567d2f930575`.

## Built against

| Component | Identity and establishment |
| --- | --- |
| IHP SG13G2 public PDK | `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`; runtime COMMIT and unchanged rule-tree checks |
| KLayout | 0.30.9; pinned runtime and executed native proof/parser |
| Image config | `ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2` |
| Image amd64 manifest | `5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0` |
| ngspice / xschem / LibreLane / CACE | not applicable to these physical checks |

## Reproduction and provenance

`checks.json` preserves the executed commands, original report hashes, input
identities, switch settings, results, and exclusions. `${BULK}` and `${REPO}`
replace local paths; their expansion must identify the hash-matched artifacts
and this repository. Portable report bytes differ from the original receipts.
Retained bulk reports and the GDS/database are not duplicated in Git.

Use the unchanged DRC and auxiliary-check helpers named in those commands.
The comparison pipeline uses `project_osc_r095_fullchip_dummies.py`,
`prove_osc_r095_fullchip_dummies.py`, `flatten_osc_r095_reference.rb`, and
`run_osc_r095_fullchip_stock_lvs.py`. Runtime and fresh resource checks precede
execution. Seven no-engine negative/binding controls passed for the LVS wrapper.
The executed wrapper hash is recorded in the LVS result; its provenance-only
amendment preceded launch and was reviewed. No failed engine was relabelled.

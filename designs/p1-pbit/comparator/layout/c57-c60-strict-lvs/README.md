# Comparator physical checkpoint C57/C60

This directory preserves a **seven-device comparator-core physical checkpoint**, not
the complete P1 comparator and not the full chip. The frozen layout contains two
`npn13G2v` decision devices, two `npn13G2` load-switch devices, two `rppd`
resistors, one `ptap1` substrate tie, and nine top-level signal or supply ports.

## Verified results

| Check | Exact scope | Result |
| --- | --- | --- |
| DRC | Installed IHP SG13G2 KLayout **main** table, deep mode, C57 GDS | zero report items |
| LVS | Installed IHP SG13G2 KLayout deck, strict top-port mode, C57 GDS versus C60 SPICE | netlists match |

The LVS cross-reference pairs **9/9 ports, 10/10 nets and 7/7 devices**. The
native run enabled `flag_missing_ports`; no ignore-port or implicit-net option was
used. `verify.py` checks the retained hashes, recounts the empty DRC `<items>`
element, confirms the native strict-match statements, checks the source structure,
and recounts the final LVS cross-reference pairs.

The two text logs are path-sanitized publication copies: the private workspace
prefix was replaced with `$DESIGN_ROOT`. Their native pre-sanitization hashes were
`5d332134...` / `f30e1a73...` for DRC and `95cd790b...` / `f9891155...` for LVS.
The result databases, GDS, source, plan and extracted netlist are byte-identical to
the independently reviewed artifacts.

## What this does not establish

- This is not the complete comparator: trim, output buffering, clock distribution,
  pads and the rest of the P1 hierarchy are absent.
- No PEX or post-layout simulation has run, so parasitic-aware 5 GS/s behavior,
  power, noise, kickback and timing remain open.
- Density/fill, antenna, top-level assembly, PVT, mismatch and yield are not closed
  by these two checks.
- This is not a signoff or tape-out-ready claim. No human has signed it off.

## Contents

```
C57-SUBSTRATE-TIE-M1B-REPAIR.gds  frozen hierarchical layout
C57-manifest.json                  geometry and lineage manifest
drc/                               main-table report database and logs
lvs/C60-nine-port-lvs.spice        strict LVS reference
lvs/C60-first-lvs-plan.md          exact runnable command and scope
lvs/c60-extracted.cir              extracted seven-device netlist
lvs/c60-lvs.lvsdb                  native comparison cross-reference
lvs/*.log                          path-sanitized native logs
SHA256SUMS                         publication identities
verify.py                          fail-closed evidence recount
```

Run `python3 verify.py` and `sha256sum -c SHA256SUMS` from this directory to
verify the retained package without requiring the PDK.
To rerun LVS, follow the relative-path command in `lvs/C60-first-lvs-plan.md` from
an SG13G2 environment and adapt the two package-relative input paths.

# C60 — First-LVS plan (SOURCE/PLAN ONLY, UNRUN)

Status: plan only. No LVS/extraction/DRC/PEX/simulation executed; no KLayout run, no
helpers, checks, GDS/layout edits, AGENTS, skills or memory edits. PROVISIONAL; no
P1/signoff claim.

## 1. Bound identities

| role | path (relative to project root) | identity |
|---|---|---|
| Layout (top under test) | `C51-layout/C57-SUBSTRATE-TIE-M1B-REPAIR.gds` | `e8be3e0ee88df96c…` (0-item C57 DRC, `48caf2e7…`) |
| Schematic (this package) | `C60-nine-port-lvs.spice` | (hash in report) |
| Schematic authority | `C45-V1-SOURCE-…no-bleed-wrapped-damp35-ls-hbtv-nx4el5.spice` | `102f2a9d…` (lines 130–133, 172, 191–195) |
| Substrate/extraction contract | `C55-substrate-extraction-contract.md` | `47be9a21…` (V3) |
| Installed LVS runset | `libs.tech/klayout/tech/lvs/sg13g2.lvs` | `e01bcb1e…` |
| Reference diagnostic (independent, matched) | source `3297b718…`; lvsdb `604c7e8d…`; log `867c7b94…`; stdout `3d515020…` | C59-V2 finding: X-prefixed PDK instances are unresolved subcircuits; Q/R + we/le normalization matches |

## 2. Representation/parameter normalization (proven by byte-diff vs C59-V2)

The only changes from `C59-nine-port-lvs-v2.spice` are:
1. **Device prefixes** `X…` → `Q…` (npn13G2v/npn13G2 BJT class) and `R…` (rppd/ptap1
   resistor class) — the reader treats X-prefixed PDK instances as unresolved
   subcircuits (C59-V2 empty-schematic-side finding).
2. **Explicit reader-recognized geometry** added: npn13G2v `we=0.12u le=5.0u`,
   npn13G2 `we=0.07u le=0.9u`; `Nx`/`m` retained; rppd `w=1.0u l=3.85u m=1 b=0`;
   ptap1 `w=2.0u l=2.0u`. The `mm_ok=1` and `R={…}` model extras are dropped
   (models/extras are out of scope).
3. **Port order** set to the EXACT extracted order (from `evidence/c59-extracted.cir`):
   `LS_N LS_P NOISE_AMP_N NOISE_AMP_P VCC_HBT VSS c_n c_p e_track` (nine ports).
4. **sub! bulk is the internal common node `nbulk`** (not a port).

Topology, the seven devices, and the strict nine-port comparison are unchanged.

## 3. Frozen command (ONE, for the later authorized run — NOT executed here)

```
install -d -m 0755 evidence
KLAYOUT_PATH=/foss/pdks/ihp-sg13g2/libs.tech/klayout klayout -b \
  -r /foss/pdks/ihp-sg13g2/libs.tech/klayout/tech/lvs/sg13g2.lvs \
  -rd input=$(pwd)/C51-layout/C57-SUBSTRATE-TIE-M1B-REPAIR.gds \
  -rd topcell=C57_SUBSTRATE_TIE_M1B_REPAIR \
  -rd schematic=$(pwd)/C60-nine-port-lvs.spice \
  -rd report=$(pwd)/evidence/c60-lvs.lvsdb \
  -rd target_netlist=$(pwd)/evidence/c60-extracted.cir \
  -rd log=$(pwd)/evidence/c60-lvs.log \
  -rd run_mode=deep \
  -rd top_lvl_pins=true \
  > $(pwd)/evidence/c60-lvs.stdout.log 2>&1
```

Named preserved outputs (fresh c60-*; no existing artifacts): report
`evidence/c60-lvs.lvsdb`, extracted netlist `evidence/c60-extracted.cir`, log
`evidence/c60-lvs.log`, stdout `evidence/c60-lvs.stdout.log`.

## 4. Strict ports and retained defaults

- **No `ignore_top_ports_mismatch`** — the schematic's nine top-level ports (extracted
  order; the sub! bulk is internal and common) must match the extracted top pins.
- **No implicit nets** — `$implicit_nets` not passed. **No `layout_netlist`**,
  **no `net_only`**. Retained defaults: simplify, series resistors, parallel resistors.

## 5. Target

Target: **no unexpected mismatch** between the extracted netlist and the
`C60-nine-port-lvs.spice` schematic — the seven devices, the nine top-level ports, the
nine named metal nets and the internal common `sub!` bulk all resolve. Any reported
difference must be an explicitly declared expectation (none currently known).

## 6. Discipline

Package only: exactly `C60-nine-port-lvs.spice` + `C60-first-lvs-plan.md`; STOP unrun.
No KLayout run, no helpers, checks, LVS/extraction/DRC/PEX/simulation, GDS/layout edits,
AGENTS, skills or memory edits. PROVISIONAL; no P1/signoff claim.

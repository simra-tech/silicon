# R1 pad ring and package

Status 2026-10-21. This file describes the R1 ring of record, revision b: 1600 x 1600 um, built by block `r1_padring`
([`../blocks/r1_padring/README.md`](../blocks/r1_padring/README.md), section "Revision b (1600 um)").
The ring has an empty core. The ring GDS is a reference for chip assembly. It is not a tape-out file.

Ring GDS: run `ring-20261021-b`, file `r1_padring_1600.gds`, SHA-256
`40514b4f4ff7888ac0ca95329470e47c8c93c1b3efc7fec1bee2f646b8dbac19`, top cell `r1_padring`,
1600 x 1600 um. The file is in the bulk results root (`<G1_RESULTS_ROOT>/r1_padring/ring-20261021-b/`, 47 MB), not in the tree.

The 1414 um ring (revision a, run `ring-20261020-a`, SHA-256 `3a477ab4534834cd8e551d6f3d1e3be5ed90a7851957fb505564c868a8eee0f0`)
is superseded. Its files stay in the tree as the record. Its pad centres are in the last section of this file.
The pin map is unchanged. The pitch of the 24 pads is now 140 um (was 112 um). Pad centres are 101 um from the die edge.

## Pin map (copy of specification section 3)

The pin map is `../specification/R1_TOP_LEVEL_SPECIFICATION.md` section 3. This table is a copy.
Die pads 1-6 are on the south side, 7-12 east, 13-18 north, 19-24 west (same convention as G1).
The net names in the GDS labels and in the netlist replace "/" with "_".
The names are `MA_SCLK`, `SLO_SDO` and `EN_STO_IN`.

| Die pad | Net | IO cell | Side | Pad centre x (um) | Pad centre y (um) | QFN24 lead |
| ---: | --- | --- | --- | ---: | ---: | ---: |
| 1 | `VDD` | `sg13g2_IOPadVdd` | south | 450 | 101 | 1 |
| 2 | `VSS` | `sg13g2_IOPadVss` | south | 590 | 101 | 2 |
| 3 | `IOVDD` | `sg13g2_IOPadIOVdd` | south | 730 | 101 | 3 |
| 4 | `IOVSS` | `sg13g2_IOPadIOVss` | south | 870 | 101 | 4 |
| 5 | `VSS` | `sg13g2_IOPadVss` | south | 1010 | 101 | 5 |
| 6 | `IOVSS` | `sg13g2_IOPadIOVss` | south | 1150 | 101 | 6 |
| 7 | `VDDA` | `sg13g2_IOPadAnalog` | east | 1499 | 450 | 7 |
| 8 | `ISA_P` | `sg13g2_IOPadAnalog` | east | 1499 | 590 | 8 |
| 9 | `ISA_N` | `sg13g2_IOPadAnalog` | east | 1499 | 730 | 9 |
| 10 | `ISB_P` | `sg13g2_IOPadAnalog` | east | 1499 | 870 | 10 |
| 11 | `ISB_N` | `sg13g2_IOPadAnalog` | east | 1499 | 1010 | 11 |
| 12 | `FAULT_N` | `sg13g2_IOPadOut4mA` | east | 1499 | 1150 | 12 |
| 13 | `GATE_A` | `sg13g2_IOPadOut30mA` | north | 450 | 1499 | 18 |
| 14 | `GATE_B` | `sg13g2_IOPadOut30mA` | north | 590 | 1499 | 17 |
| 15 | `GATE_C` | `sg13g2_IOPadOut30mA` | north | 730 | 1499 | 16 |
| 16 | `CS_N` | `sg13g2_IOPadIn` | north | 870 | 1499 | 15 |
| 17 | `MA` / `SCLK` (`MA_SCLK`) | `sg13g2_IOPadIn` | north | 1010 | 1499 | 14 |
| 18 | `SLO` / `SDO` (`SLO_SDO`) | `sg13g2_IOPadOut4mA` (`sg13g2_IOPadTriOut4mA` if bused) | north | 1150 | 1499 | 13 |
| 19 | `SDI` | `sg13g2_IOPadIn` | west | 101 | 450 | 24 |
| 20 | `EN` / `STO_IN` (`EN_STO_IN`) | `sg13g2_IOPadIn` | west | 101 | 590 | 23 |
| 21 | `SIN_P` | `sg13g2_IOPadAnalog` | west | 101 | 730 | 22 |
| 22 | `SIN_N` | `sg13g2_IOPadAnalog` | west | 101 | 870 | 21 |
| 23 | `COS_P` | `sg13g2_IOPadAnalog` | west | 101 | 1010 | 20 |
| 24 | `COS_N` | `sg13g2_IOPadAnalog` | west | 101 | 1150 | 19 |

Pad centre = centre of the 65.8 um passivation opening and of the 70 x 70 um TopMetal2 bondpad
(measured, `../blocks/r1_padring/reports/bondmap/verify_bondmap_r1_1600.json`: 24 openings, 24 rows, all pass).
The ring GDS carries a TopMetal2 label (134/25) on the first pad of each net.
This gives 22 labels for 24 pads: the second `VSS` pad (5) and the second `IOVSS` pad (6) have none.
G1 r4 has the same 22 labels. The cell `new_signal_routes` carries a label on every one of the 24 pads.

`VDDA` (pad 7) uses a bare `sg13g2_IOPadAnalog`. The board ties the `VDDA` lead to the `IOVDD` rail
(G1 rule D14). An analog pad has a 587 ohm series resistor (`padres`) on the core side. The core side
terminal without the resistor is `padbare` in the G1 LEF views (`designs/g1-guardian/blocks/g1_padring/ip/sg13g2_io_padbare/`).
The ring GDS does not change. This block does not use the LEF views.

## Side drawing (GDS view, lower-left die corner at the origin)

Pad numbers and nets. The IO row is 180 um deep on each side. The bondpads sit between the IO row and the die edge.

```
                         north (pads 13-18, left to right)
          13        14        15        16        17          18
        GATE_A    GATE_B    GATE_C     CS_N    MA_SCLK     SLO_SDO
      +-----------------------------------------------------------+
  24  |                                                           | 12
COS_N |                                                           | FAULT_N
  23  |                                                           | 11
COS_P |                                                           | ISB_N
  22  |                                                           | 10
SIN_N |                       core window                         | ISB_P
  21  |                       (empty)                             |  9
SIN_P |                                                           | ISA_N
  20  |                                                           |  8
EN_   |                                                           | ISA_P
STO_IN|                                                           |  7
  19  |                                                           | VDDA
SDI   |                                                           |
      +-----------------------------------------------------------+
         1        2        3        4        5        6
        VDD      VSS     IOVDD    IOVSS     VSS     IOVSS
                         south (pads 1-6, left to right)

west (pads 19-24, bottom to top)                east (pads 7-12, bottom to top)
```

Pad pitch is 140 um. The first pad centre on each side is at 450 um, then 590, 730, 870, 1010, 1150. The six pads are centred on the side.
The pad centres are 101 um from the die edge (south, west) or 1499 um (north, east).

## Package and bond plan

The package is a QFN24 (4 x 4 mm body, 0.5 mm lead pitch, six leads per side, exposed paddle).
The bond plan rule is inherited from G1 (`../../g1-guardian/padframe/BONDPLAN_20260925.md`, owner decision 2026-09-25):

1. Bond each die pad to the lead directly opposite it.
2. No two wires cross.
3. Number the leads counter-clockwise, lead 1 at the top of the left side, next to the top-left corner (pin-1 mark).
4. The die is centred on the paddle and rotated 90 degrees clockwise from the GDS view.
   The GDS south edge (pads 1-6) faces leads 1-6, east faces 7-12, north faces 13-18, west faces 19-24.
5. Pads 1-12 bond to leads 1-12. Pads 13-24 bond to the leads in reversed order: pad n goes to lead 31 - n.
6. The exposed paddle is `VSS`. Leads 2 and 5 (`VSS`) and leads 4 and 6 (`IOVSS`) tie to the same board ground.

The generator is [`bondplan_r1.py`](bondplan_r1.py) (copy of the G1 generator, adapted: the expected GDS hash is a required argument; `-rd die_um=1600` sets the die size, default 1414).
It reads the 24 passivation openings and the labels from the ring GDS and derives the lead for each pad.
Result: 0 wire crossings. The alternative "pad n to lead n" has 30 crossings (geometric calculation in the generator, same as G1).
The wire lengths are nominal estimates from a nominal package drawing. They are not measured values.

| File | Content | SHA-256 |
| --- | --- | --- |
| [`bondmap_src_r1_1600.csv`](bondmap_src_r1_1600.csv) | input rows: pad, net, side, opening centre and size | `3643b3d40a5c9cdb622ea75e173651145d9488ef7a66757bff97b8ded0fe523a` |
| [`bondmap_r1_1600_ring.csv`](bondmap_r1_1600_ring.csv) | bond map bound to the ring GDS hash, with `qfn24_lead` and `lead_side` | `a281113af4ff621d36dbf17a855b77286e3c1af811013d8166cebe4cdae7af73` |
| [`bondplan_r1_1600.svg`](bondplan_r1_1600.svg) | bond plan drawing (top view) | `351007d82159637103f7d9490ad8475f5fac1a83d983e709680036ad95c09147` |
| [`bondplan_r1_1600.json`](bondplan_r1_1600.json) | generator summary, wire lengths | `c45b39e451f4599f4e0afb5df1e3d34b4c714bbd99d3263e7f8144661a0ef9ea` |

The bond map is `ring_reference` status. It is bound to the ring GDS of this block, not to a chip of record.
When the core is placed, the chip GDS has a new hash. Run the generator again on the chip GDS.

## Checks of the bond plan

| Check | Status | Evidence |
| --- | --- | --- |
| Bond map rows against the ring GDS (24 openings, size, TopMetal2 enclosure, dfpad, labels, die size, hash) | passed | `../blocks/r1_padring/reports/bondmap/verify_bondmap_r1_1600.json` (`all_ok: true`) |
| Wire crossings for pad-to-opposite-lead | passed, 0 crossings | `bondplan_r1_1600.json` |
| Bonding diagram accepted by a packaging service | not run | |
| Wire lengths against a real package drawing | not run | the lengths are nominal estimates |
| Pad RC and package parasitics | not run | |

## Superseded: 1414 um ring (revision a, run `ring-20261020-a`)

The files `bondmap_src_r1.csv`, `bondmap_r1_ring.csv`, `bondplan_r1.svg` and `bondplan_r1.json` belong to this ring.
They stay in the tree as the record. Pad pitch 112 um. Pad centres:

| Die pads | Side | Pad centres (um) |
| --- | --- | --- |
| 1-6 | south | x = 395, 507, 619, 731, 843, 955; y = 101 |
| 7-12 | east | x = 1313; y = 395, 507, 619, 731, 843, 955 |
| 13-18 | north | x = 395, 507, 619, 731, 843, 955; y = 1313 |
| 19-24 | west | x = 101; y = 395, 507, 619, 731, 843, 955 |

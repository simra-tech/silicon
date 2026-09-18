# G1 pad ring and package

## Ring geometry

| Item | Value | Source |
| --- | --- | --- |
| Die outline | 1000 × 1000 µm | area allocation |
| Sealring | PDK `sealring` PCell, inner 950 × 950 µm | PDK |
| IO cell size | 80 × 180 µm (`sg13g2_IOPad*`) | `sg13g2_io.lef` |
| Corner cell | 180 × 180 µm (`sg13g2_Corner`) | `sg13g2_io.lef` |
| Cells per side | 6, at 80 µm pitch, plus fillers | design |
| Ring extent per side | 180 + 6 × 80 + 180 = 840 µm; about 110 µm of `sg13g2_Filler*` per side | derived |
| Core window | about 590 × 590 µm inside the ring | derived |
| Bondpad | the IO cell's own bondpad, TopMetal2 | PDK |

The ring is generated with the LibreLane chip flow for SG13G2 (pad placement by
side, `sg13g2_Corner`, filler insertion). Analog cores are placed as macros.

## Package

QFN24, 4 × 4 mm body, 0.5 mm lead pitch, six leads per side, matching six
pads per side on the die. Die thickness 200 µm. Die attach conductive and the
exposed paddle bonded to a board pad so the substrate return is a defined node
rather than a floating one.

Bonding diagram: pad *n* on side *s* to the lead directly opposite, no
crossings. Pad numbering follows the pin map in the specification.

## Pin map

See the specification, section "Pin map". Twenty-four pins: four IO-ring
supplies, three extra supply pads, two Kelvin sense inputs, gate drive, fault
flag, enable, trip-set, three-wire serial, temperature output, reference output,
three canary-transistor pins and three HBT pins.

## Checks

| Check | Status |
| --- | --- |
| Ring assembled, DRC on ring alone | not run |
| Full-chip DRC incl. precheck rules | not run |
| Density and fill | not run |
| Antenna | not run |
| Bonding diagram accepted by packaging service | not run |

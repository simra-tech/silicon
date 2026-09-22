# Isolated BGR586 physical implementation gates

No production geometry is replaced. Source586ffb58, not its535 parent, is the
implementation target. All1,036 source devices, exact W/L/fingers, HBT geometry,
resistor dimensions and source/body nets must survive physical implementation.
Nominal/one-draw numerical results do not qualify new geometry.

First run the unchanged original generator in a fresh isolated directory. Pin
generator `dee7f8fa5ab94165946e342625ed72c00e6a174592bb47a0af9f9054b8ce171e`,
delivered filled GDS `4f83cc0830a97b61fda66113cc3768db54e762fc210b2f798d3dd035db30afeb`,
and original LEF `e00ab99d81bce2c02388a1e933af5e819dd0188f2045f13f943209d059907246`.
The original filler adds datatype22 geometry and removes layer50/23 and67/23
temporary/no-fill markers. Classify precisely those differences; require every
other nontext layer XOR0, exact text inventory and exact LEF bytes. This is a
generator-reproduction control, not source-device fidelity, DRC/LVS or fill
qualification. No original fill script is executed and no original file written.

One CPU6,180-second generator bound,0.05GiB expected output after fresh resource
gate. KLayout0.30.9 and IHP84374023 required. Stop on failure, no automaticretry.
Next gates are separate: native586 footprint refresh against r4coordinates,
small source-bound contact/well/guard prototypes, stock checks and independent
source-to-physical device inventory, then complete placement/routing/feeds/fill.
No source/PDK rule or model modifications; no broad affected MC until reviewed
geometry gates. Proposed2µm reservations are not a waiver of actual well rules.

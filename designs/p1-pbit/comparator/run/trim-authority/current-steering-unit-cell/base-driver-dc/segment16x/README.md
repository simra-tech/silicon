# Loaded 16x steering-segment DC evidence

This 27 C, typical-corner experiment scales the loaded one-unit steering cell
to the weight of one proposed thermometer-coded MSB segment. The NMOS sink uses
`m=16` and each steering HBT uses `Nx=16`, while the corrected nominal
100/20 kohm passive base network, ideal 0.96 V reference, ideal complementary
logic sources, and 2.1 V collector sources remain unchanged.

The two raw rows exchange the steering state symmetrically:

| quantity | value |
| --- | ---: |
| sensed NMOS sink current | 12.206470300 uA |
| requested target | 12.199408 uA |
| error relative to requested target | +0.057891% |
| NMOS drain voltage | 0.342566246 V |
| active / inactive loaded base voltage | 1.000582470 / 0.799622848 V |
| loaded base differential | 200.959622 mV |
| loaded base common mode | 0.900102659 V |
| active / inactive HBT base current | 29.552810 / 0.028628 nA |
| selected / unselected collector current | 12.229873600 / 0.006205677 uA |
| selected share of collector sum | 99.949284% |
| selected collector current per HBT emitter | 0.764367100 uA |
| positive source-delivery power | 8.218930 uW |

Positive source-delivery power is `-sum(Vsource * Isource)` over the two actual
logic-source voltages and the 0.96 V reference. The zero-volt sense and
collector sources are not included.

For the proposed 6-bit thermometer-MSB plus 4-bit binary-LSB mapping, the
architecture arithmetic is 63 weight-16 cells plus four cells weighted 1, 2,
4, and 8: **67 independently steerable cells and 1023 effective units**. The
earlier report of 78 steerable cells is retracted. Physical primitive counts
remain layout-dependent because SPICE `m` and `Nx` multipliers may expand.

This isolated static experiment does not establish the physical 0.96 V
reference, a dynamic CMOS driver, the intermediate binary weights, assembled
array code transfer, mismatch, settling, corners, layout, architecture
selection, a gate disposition, or signoff.

## Reproducing

From this directory, with `PDK_ROOT` set to the IHP SG13G2 PDK root:

```sh
ngspice -b tb_segment16x_dc.cir > log_segment16x_dc.log
```

The retained log contains two completed one-row analyses and no error, fatal,
abort, or NaN message. The published deck differs from the executed deck only
by replacing machine-specific model and output paths with `$PDK_ROOT` and
repository-relative paths.

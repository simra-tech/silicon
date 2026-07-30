# Loaded binary-weight cell DC evidence

This 27 C, typical-corner package measures the three intermediate physical
weights in the proposed segmented trim DAC. For each weight, the NMOS sink
multiplier and both HBT emitter counts scale together while the corrected
nominal 100/20 kohm base network, ideal 0.96 V reference, ideal complementary
logic sources, and 2.1 V collector sources remain fixed.

Each row below is identical after reversing the two retained steering states:

| weight | target current | sensed current | target error | sensed current / unit | NMOS VDS | loaded base differential | selected collector share | selected current / emitter | source-delivery power |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2 | 1.524926 uA | 1.525238570 uA | +0.020497% | 0.762619285 uA | 0.342143970 V | 200.533005 mV | 99.947703% | 0.764085525 uA | 8.244804 uW |
| 4 | 3.049852 uA | 3.050642300 uA | +0.025913% | 0.762660575 uA | 0.342205311 V | 200.594083 mV | 99.948252% | 0.764124183 uA | 8.241099 uW |
| 8 | 6.099704 uA | 6.101938360 uA | +0.036631% | 0.762742295 uA | 0.342326340 V | 200.716101 mV | 99.948706% | 0.764204901 uA | 8.233699 uW |

Every raw row retains the actual 0 V / 1.2 V logic-source voltages. Positive
source-delivery power is `-sum(Vsource * Isource)` over those two actual logic
voltages and the 0.96 V reference.

## Artifact identity correction

The generated `tb_weights2_4_8_dc.cir` called a master deck in the original
report is byte-identical to the weight-2 deck and cannot reproduce weights 4
or 8. The exact executed `tb_w2_dc.cir`, `tb_w4_dc.cir`, and `tb_w8_dc.cir`
were present on disk and are all retained here. The duplicate non-master deck
is intentionally omitted.

This nominal static experiment does not establish assembled-array code
transfer, mismatch, switching behavior, settling, corners, a physical 0.96 V
reference, a dynamic CMOS driver, layout, architecture selection, a gate
disposition, or signoff.

## Reproducing

From this directory, with `PDK_ROOT` set to the IHP SG13G2 PDK root:

```sh
ngspice -b tb_w2_dc.cir > log_w2_dc.log
ngspice -b tb_w4_dc.cir > log_w4_dc.log
ngspice -b tb_w8_dc.cir > log_w8_dc.log
```

The retained combined log contains all six completed one-row analyses and no
error, fatal, abort, or NaN message. Each published deck differs from its
executed deck only by replacing machine-specific model and output paths with
`$PDK_ROOT` and repository-relative paths.

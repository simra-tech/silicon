# Custom CML divide-by-2 candidate V2

This directory contains the first source-backed transistor-level seed for the standalone
divide-by-2 front stage proposed in
[`architecture/custom-cml-div2/`](../../architecture/custom-cml-div2/).

## Result boundary

The candidate is a master/slave CML latch pair with complementary clock steering and inverted
slave-output feedback. It retains the model and device-parameter tails from Top V3 comparator
lines 130–150 as provisional seed values and copies the process substrate tap from line 174.

An independent static audit found:

- 43 unique elements and zero duplicate names;
- 42 of 42 copied master/slave model-plus-parameter tails matching the source;
- one substrate tap matching Top V3 line 174 after its instance name;
- direct `DIV2_P` and `DIV2_N` emitter-follower outputs, with no invented alias resistors; and
- valid text with no tab or unexpected control bytes.

The source candidate SHA-256 is
`64226d8548e664d3a26247817926b1f5bfc5a0cf0552d342861b21c03ef78652`.
The retained Top V3 source netlist SHA-256 is
`b8ac82719ffcd365b91fbd7c997b45d9d422e684077fe82f05a691cb7dcbd4ca`.

These are connectivity and provenance facts only. The copied values remain `PROVISIONAL_SEED`;
the choice to duplicate the master and slave PTAT bias networks is a
`PROVISIONAL_ARCHITECTURE_DECISION`. Bias adequacy, headroom, power, startup, output loading,
PVT behavior, divider function, and frequency capability remain unknown.

## Pin contract

```text
.subckt p1_cml_div2_front DIV2_P DIV2_N CLK_P CLK_N VCC_HBT VSS
```

`CLK_P/N` are differential clock inputs, `DIV2_P/N` are differential internal outputs,
`VCC_HBT` is the 2.5 V HBT supply, and `VSS` is the ground-domain port. The substrate node
`sub!` is connected to `VSS` through the retained `ptap1` element; it is not an ideal short.

## History and evidence

Candidate V1 SHA-256
`12177cd5141a8ccfe26c84fc4851420365f72a64129c885efdaf9c90bf867503`
is rejected. It omitted the substrate tap, added two unproven 1 mΩ output aliases, misstated a
drawn resistor length as resistance, and overstated unrun testbench conditions.

The current nominal operating-point package is
[`run/custom-cml-div2-op-v2/`](../../run/custom-cml-div2-op-v2/). It contains a complete deck,
log, raw file, and path-sanitized OpenADA envelope. That run is thermally warned and remains
engineering-unknown; it does not establish divider operation.

A separate [`selft=0` A/B diagnostic`](../../run/custom-cml-div2-op-selft0-v1/) removes the
warning but shifts the operating point materially. It is retained as diagnostic evidence only
and does not replace this physical-model candidate or its warned result.

Signoff and tape-out readiness are not claimed.

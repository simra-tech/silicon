# Shared-input junction observation: mapping recovered, applicability open

The first representative room OP run completed in119.097s, but its original
full-output byte gate **failed**. Saving all internal vectors changed the
default OP scale from clk0 to vdda3.3. All23078 original printed parameter and
legacy values, and all17 nonscale physical output values, remained exact.
That attribution does not waive the original failed gate.

An initial read-only interpretation of raw internal names also **failed**.
For example, raw `#si` was approximately3.3V while the external source was
1.503V and the pinned source resistance was zero. The initially generated
interpretation is retained and superseded, not silently corrected. Its script
was not snapshotted before correction; a later reconstruction did not recover
the original hash and is explicitly marked non-byte-exact. The corrected
analysis and raw data retain exact hashes.

## Source-derived internal mapping

The pinned OSDI descriptor inventory passed in7.706s without model setup or
evaluation. An earlier0.3-version assumption failed safely before descriptor
access; the installed models use0.4 with a352-byte descriptor. The native
loader supports that compatible prefix. RSE/RDE are zero for all six inputs;
the other five collapse-controlled resistances are positive.

For this collapse pattern, the simulator assigns compact-node labels using
the original descriptor ordering. Reconstructing that mapping gives:

| Physical node | Saved vector suffix |
|---|---|
| SI / DI | Actual external S / D terminal |
| BP | `#si` |
| BI | `#di` |
| BS | `#bp` |
| BD | `#bi` |
| Noise-flow unknown | `#bs` |

The source-derived mapping agrees with independent native channel-voltage
metadata for all six devices at its six-significant-digit print precision.
This is not a direct observation of the live simulator's mapping array.
The behavior follows the [ngspice46 collapse/setup implementation](https://raw.githubusercontent.com/imr/ngspice/ngspice-46/src/osdi/osdisetup.c),
with descriptor layout and compatible loading established by its
[OSDI header](https://raw.githubusercontent.com/imr/ngspice/ngspice-46/src/osdi/osdi.h)
and [native loader](https://raw.githubusercontent.com/imr/ngspice/ngspice-46/src/osdi/osdiregistry.c).

The reconstructed room SI−BS voltages are approximately−1.796841406V for
the main input pair,−0.986931628V for XBUF, and−0.959053385V for XREF.
Within-pair differences are approximately8fV,3.75pV and5.18pV respectively.
They are at numerical/export resolution, not proof of exact equality or a
guaranteed bound. Raw ASCII uses15-digit values; no additional precision is
claimed. A first mapping analysis used an incorrect hierarchical spelling
for external vped and failed before export; that failure is retained.

## Open gates

Corrected room replay **passed** in113.071s with all three original output
files byte-exact and all23078 original printed values exact. It explicitly
selected the original clk output scale; original source/model/solver stayed
held. Its929 warnings (928 resistor voltage-limit messages and one temperature
limiting NaN warning) remain inventoried against the reference, not hidden.
The raw physical values and reconstructed room biases are unchanged.
First hot observation **failed** at the120.021s child limit while printing
the optional vector inventory, after original OP/data export. A new bounded
output-only recovery omits that listing but retains full raw inventory and
the same120s bound. That recovery **passed** in119.678s with all23078 original
printed values exact and all three original waveform files byte-exact. Hot
SI−BS biases were−1.838757523V,−0.997856631V and−0.969903173V for main,
buffer and reference pairs; their within-pair deltas were2.63pV,12.49pV and
4.60pV. They are representative observations, not full-corner bounds.

A separate one-PMOS control retained canonical W384µm/L2µm/ng64/m1/mm_ok1
and unchanged cards. Its four realized W/L/DELVTO/FACTUO parameters stayed
exact across three OP points. Equal-bias repetition produced identical raw
bytes and metadata; changing only the external body source from3.3V to3.0V
changed SI−BS by0.299999999787V and native cjs by4.395922%. The predeclared
1nV/1ppm equal-bias and0.29V/1% negative-bias gates passed. This is a
necessary-condition/mapping control with a separate tiny-circuit random
realization, not a full-population or shared-layout equivalence proof.

Junction charge observations remain **not run**. Native displayed capacitance is
not charge. Actual shared-junction applicability remains **not qualified**;
no canonical source, model, A/P, layout or solver equation was modified.

This diagnostic does not close the independent primitive-owned MIM extrinsic
PEX blocker or waive the51 stock junction-annotation failures.

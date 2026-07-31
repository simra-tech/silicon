# Model-valid full-array code 1023 at the 900 uA scale

This package preserves the opposite endpoint to the
[900 uA code-0 diagnostic](../900ua-code0/README.md): one 27 °C,
typical-model DC run of the full 67-cell current-steering array connected to
comparator candidate 2. The two decks are byte-identical except for 268 logic
value flips and five experiment-identity/output lines. Both retain the
corrected 2.25 µm shared sink width and the model-valid `2x8` thermometer-HBT
representation.

Two parallel `Nx=8` devices are not model-equivalent to one extrapolated
`Nx=16` device. These are model-domain diagnostics, not selected
implementation or replacement-candidate measurements.

## Result

The native ngspice process exited 0 after 9.85 seconds. An independent recount
of the retained raw file gives 1,201 rows by 28 columns, with all 33,628 values
finite. All 14 repeated sweep-coordinate columns are identical. The input
coordinate and collector differential are strictly increasing, and there is
exactly one collector zero crossing.

Linear interpolation across that crossing gives:

| quantity | value |
| --- | ---: |
| input zero crossing | **+47.831624406 mV** |
| VCC-HBT branch-current magnitude | 3.129363009 mA |
| collector common mode | 2.092283044 V |
| `XT01` trim P / N | 1.000630458 / 0.799622911 V |
| `XB8` trim P / N | 1.000362802 / 0.799622639 V |
| `XB4` trim P / N | 1.000228640 / 0.799622502 V |
| `XB2` trim P / N | 1.000161468 / 0.799622432 V |
| `XB1` trim P / N | 1.000127866 / 0.799622397 V |

The corresponding code-0 crossing is -47.829911704 mV. The two-endpoint span
is **95.661536110 mV**, with an arithmetic midpoint of
**+0.000856351 mV**. This is a direct nominal endpoint comparison, not a
linearity, mismatch, yield, tolerance, or specification result.

The code-1023 native log contains no thermal-NaN, heat-sink, dynamic-gmin,
true-gmin, source-stepping, transient-operating-point, parser-error, abort, or
fatal line. The code-0 log does contain the temperature-limiter NaN/heat-sink
event and dynamic-gmin recovery. That code-state diagnostic asymmetry is
retained rather than averaged away: the code-1023 log is warning-free, but the
paired full-array engineering status remains **UNKNOWN** because the code-0
warning is unresolved. Specification status is **NOT EVALUATED**.

Exit status 0 and a warning-free endpoint are not an engineering pass.

## Artifact identity

| artifact | bytes | SHA-256 |
| --- | ---: | --- |
| native executed deck | 18,643 | `2044397d7d840080da193068b3bc27453db4bf3bb9e8a49c8e9b2c95e329fd20` |
| public sanitized deck | 18,466 | `8915de1f008606d131562961aabbdc92149855cb315a0910219169d60a2b5472` |
| `log_full_array_code1023_modelvalid_2x8_900ua.log` | 9,033 | `8a28e49f3b4648df597132f519e16458214522248837bdde90092eb6407b923a` |
| `raw_modelvalid_2x8_900ua_code1023.txt` | 539,249 | `a3897c5d10a1c8f969be5f590e79c9a1ee3fd892b475bc6d1eeda69d7fe4017b` |

The log and raw file are byte-identical to the executed artifacts. The public
deck differs from the native deck only by replacing machine-specific model,
include, OSDI, and output paths.

## Reproducing

From this directory, resolve the PDK placeholder into a temporary deck and use
the IHP ngspice startup configuration:

```sh
IHP_ROOT=/path/to/ihp-sg13g2
PDK_ROOT="$IHP_ROOT" envsubst '$PDK_ROOT' \
  < tb_full_array_code1023_modelvalid_2x8_900ua.cir > resolved.cir
PDK_ROOT="$(dirname "$IHP_ROOT")" \
PDK=ihp-sg13g2 \
SPICE_USERINIT_DIR="$IHP_ROOT/libs.tech/ngspice" \
  ngspice -b resolved.cir > rerun.log 2>&1
```

Run this in a fresh copy if the retained raw evidence must remain untouched.

This package does not establish a valid self-heating-on full-array
measurement, full code-range behavior, DNL, mismatch, monotonicity yield,
dynamic switching, settling, process-voltage-temperature coverage, layout, an
engineering gate disposition, signoff, or tape-out readiness.

# Model-valid full-array code 0 at the 900 uA scale

This package preserves one 27 °C, typical-model DC diagnostic of the full
67-cell current-steering array connected to comparator candidate 2. It starts
from the retained model-valid `2x8` thermometer-HBT code-0 deck and changes
only the shared weighted-cell and thermometer-cell NMOS sink width from
2.00 µm to the corrected 2.25 µm 900 uA candidate width. The public deck also
replaces machine-specific model, include, OSDI, and output paths.

Two parallel `Nx=8` devices are not model-equivalent to one extrapolated
`Nx=16` device. This remains a model-domain diagnostic, not a selected
implementation or replacement-candidate measurement.

## Result

The native ngspice process exited 0 after 11.63 seconds. An independent recount
of the retained raw file gives 1,201 rows by 28 columns, with all 33,628 values
finite. All 14 repeated sweep-coordinate columns are identical, the input
coordinate increases strictly from -60 mV to +60 mV in 0.1 mV steps, and the
collector differential is monotonic with exactly one zero crossing.

Linear interpolation across that crossing gives:

| quantity | value |
| --- | ---: |
| input zero crossing | **-47.829911704 mV** |
| VCC-HBT branch-current magnitude | 3.129363000 mA |
| collector common mode | 2.092283043 V |
| `XT01` trim P / N | 0.799622911 / 1.000630456 V |
| `XB8` trim P / N | 0.799622639 / 1.000362802 V |
| `XB4` trim P / N | 0.799622502 / 1.000228636 V |
| `XB2` trim P / N | 0.799622432 / 1.000161473 V |
| `XB1` trim P / N | 0.799622397 / 1.000127865 V |

The retained 780 uA model-valid baseline crosses at -40.866795 mV. The present
crossing is therefore 6.963116704 mV more negative. Its raw file is bytewise
distinct from the baseline raw (`d3259ccf...`). This is a direct comparison
between two nominal code-0 diagnostics, not a specification or linearity
result.

The native log contains one temperature-limiter NaN event represented by the
NaN line and its heat-sink guidance line. It also records one dynamic-gmin
start and one completion, with no failed recovery, parser error, abort, or
simulation-failure token. Consequently:

- process execution: completed;
- retained numeric dataset: finite and structurally consistent;
- engineering status: **UNKNOWN** because the self-heating warning recurs;
- specification status: **NOT EVALUATED**.

Exit status 0 is not an engineering pass.

## Artifact identity

| artifact | bytes | SHA-256 |
| --- | ---: | --- |
| native executed deck | 18,621 | `5a391a7292b48994f61d276bae88b6fe0ef892c813186f08f3e68da56452aca0` |
| public sanitized deck | 18,444 | `34becf3f9a93784dc3fc2453683ba16f963ceffe3530668a7d977e560e058936` |
| `log_full_array_code0_modelvalid_2x8_900ua.log` | 9,061 | `52243e0d1a29d768836017af1aeddf68d91506f3bca379e034e8f465bc2cb87b` |
| `raw_modelvalid_2x8_900ua_code0.txt` | 539,249 | `20e5a833da9cdd42ce3332d7bc0a260196705b2ec739c9ac25d11cff0b1bd15e` |

The log and raw file are byte-identical to the executed artifacts. The public
deck differs from the exact native deck only in the allowlisted path
substitutions described above.

## Reproducing

From this directory, resolve the PDK placeholder into a temporary deck and use
the IHP ngspice startup configuration:

```sh
IHP_ROOT=/path/to/ihp-sg13g2
PDK_ROOT="$IHP_ROOT" envsubst '$PDK_ROOT' \
  < tb_full_array_code0_modelvalid_2x8_900ua.cir > resolved.cir
PDK_ROOT="$(dirname "$IHP_ROOT")" \
PDK=ihp-sg13g2 \
SPICE_USERINIT_DIR="$IHP_ROOT/libs.tech/ngspice" \
  ngspice -b resolved.cir > rerun.log 2>&1
```

Run this in a fresh copy if the retained raw evidence must remain untouched.

This package does not establish a valid self-heating-on full-array
measurement, full code-range behavior, mismatch, DNL, monotonicity yield,
dynamic switching, settling, process-voltage-temperature coverage, layout, an
engineering gate disposition, signoff, or tape-out readiness.

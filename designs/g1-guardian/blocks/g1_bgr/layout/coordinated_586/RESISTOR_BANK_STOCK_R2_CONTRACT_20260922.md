# Resistor-bank landing r2: stock gate

Exactly one fresh stock DRC and strict LVS pair on GDS
`4019838faa0efb2b5038e69f9652c6e52eb60ab070ac964f2d39f72af29e0d17`.
The source and CDL are unchanged from r1. The saved-view revision audit passed:
only the implicated M3 landing pads were shortened, every other layer and all
text are unchanged, and all Via2/Via3 cuts retain 55 nm M3 enclosure.
The original 73 M3.b failures and passing r1 LVS remain preserved.

Reuse the exact r1 stock runner with only declared input/output revision,
GDS identity, and contract substitutions. CPU6, 180 seconds per child with
five-second kill grace, total output allowance 0.15 GiB. A fresh host resource
gate is required. The immutable source, native-device ledger, track/cut ledger,
CDL and original runner are prerequisites. Save the derived runner and its
hash, and bind both revision manifests and the landing audit before and after.

DRC requires zero markers and successful completion; LVS requires explicit
success and all strict cross-reference statuses Match. Both checks run even
if DRC fails, as in the declared r1 diagnostic. Wrapper exit status must match
the final summary. No source or PDK changes, automatic retry, density, antenna,
PEX, current/temperature qualification or full-bank adoption. These latter
checks are **not run**; simulation seed is **not applicable**.

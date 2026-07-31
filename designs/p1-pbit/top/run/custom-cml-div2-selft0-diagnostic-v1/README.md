# Custom CML divide-by-2 thermally simplified diagnostic V1

This package preserves one controlled comparison against the physical
self-heating Candidate V5 transient. It sets `selft=0` on every one of the 26
`npn13G2` instances and changes nothing else in the candidate.

This is a thermally simplified diagnostic, not a replacement design candidate.
Candidate V5 and its native thermal diagnostics remain the physical source of
record in the adjacent
`custom-cml-div2-tran-integrated-sinks-v1` package.

## Controlled change

Candidate SHA-256
`16ce04d7b3112a26e4b28e8fbe379e9bbb9882ba99ce408961e6b0e2429e0a46`
is 5,662 bytes and 94 lines. Direct comparison with Candidate V5 SHA-256
`689d4beedfce278f0c13cf0e79a25b87ba8a12d25b9459e51dfbfde041cd3db7`
finds exactly 26 changed physical line positions. Each change appends one
`selft=0` override to an existing HBT instance. Removing those suffixes
restores Candidate V5 byte-for-byte.

The private executed deck SHA-256
`21476a37993b026cfe3dce4f8b0b1cb8ce1af9173b071e2c1a15ebf50ee550c7`
differs from the physical V5 deck at four line positions: title comment line
1, include comment line 12, include target line 13, and raw target line 36.
The public deck changes only the PDK root to `$PDK_ROOT`.

## Retained execution evidence

OpenADA 0.4.0 legacy control mode invoked ngspice 46 once and retained:

- native log SHA-256
  `341e4d0bcd10fa7d06689b2bd25e59bf6bff15bfb8fbd0c8722f206bc98cb493`;
- binary raw SHA-256
  `cf6067c37593907e3f86e7b17354b9d0229603f5924d63326ed0ab8aa29bad17`;
- 429 real variables by 2,284 points from 0 through 4 ns; and
- 979,836 finite raw scalars and no non-finite raw scalar.

The native log contains neither thermal diagnostic retained by Candidate V5.
All 26 saved HBT `.t` vectors contain 1,141 post-2 ns points, and every stored
scalar is zero. `THERMAL-NODE-COMPARISON.tsv` records those populations beside
the physical V5 populations without assigning a physical unit to `.t`.

OpenADA's `engineering.status: pass` means its requested evidence envelope is
structurally complete. It is not a project engineering disposition.

## Waveform comparison

`WAVEFORM-COMPARISON.tsv` is an independent parse of both frozen binary raws
from 2 ns through 4 ns. Each of the four differential signals has ten zero
crossings in both runs.

For `div2_p-div2_n`, the thermally simplified run has:

- mean adjacent crossing interval `199.999953898074580 ps`;
- mean two-crossing period `399.999907861493739 ps`; and
- inferred full-cycle frequency `2.500000575865796 GHz`.

The physical V5 comparison is retained in the same table, and
`OUTPUT-CROSSINGS.tsv` carries all ten interpolated timestamps from each raw.
The output swing changes between the two conditions, so the simplified result
is not substituted for the physical waveform.

The absence of the two messages under the one controlled `selft=0` condition
is evidence that their appearance is sensitive to the enabled self-heating
path. It does not establish the physical meaning of the internal `.t` scalar,
does not clear the Candidate V5 messages, and does not authorize a circuit
change.

## Thermal-terminal source authority

`THERMAL-TERMINAL-AUTHORITY.tsv` preserves 13 physical lines from the
hash-identified IHP HBT model. The model's `npn13G2_5t` wrapper exposes a fifth
terminal that its line-147 comment names `temperature output`. The
four-terminal `npn13G2` wrapper used by Candidate V5 instead connects the core
device's fifth terminal to an internal node named `t`.

`THERMAL-SOURCE-SEARCH-INVENTORY.tsv` enumerates the four local sources
searched for an explicit semantic definition. Within that bounded inventory,
none establishes the physical unit of the temperature output or whether it is
absolute temperature versus temperature rise. The authority table therefore
preserves model topology and exact source language without assigning either
unresolved meaning to the saved `.t` vectors.

`NGSPICE-WARNING-AUTHORITY.tsv` separately binds the two native warning
literals to compiled ngspice 46 executable SHA-256 `6aacaca8...`. Their exact
byte offsets are `0x6d5c8a` and `0x6d5cc0`, separated by one newline byte and
six NUL bytes. `NGSPICE-WARNING-SEARCH-INVENTORY.tsv` records the bounded local
search: the text occurs in compiled ngspice binaries and retained tool
evidence, but not in the searched PDK tree. No matching installed C or header
source was found in the bounded local search. Binary strings do not reveal the
emitting C function, trigger condition, or HBT instance, so all three remain
unresolved.

The warning inventory uses `$NGSPICE_ROOT`, `$PDK_ROOT`,
`$SYSTEM_NGSPICE_LIB_ROOT`, and `$LOCAL_TOOL_EVIDENCE_ROOT` as publication
labels for the four private search roots. No file from those roots is included
in this package.

The official ngspice 46 source tarball closes part of that binary-only gap.
`NGSPICE46-SOURCE-PACKAGE.tsv` records its release identity without republishing
the archive. `NGSPICE46-WARNING-CALLPATH-AUTHORITY.tsv` binds 15 exact physical
lines to tarball SHA-256 `a0d1699a...`. `DEVlimitlog` emits the warning when
either its current or stored temperature-change input is NaN, assigns the
current input to zero, sets its check flag, and suppresses later prints after
the first emission. The source therefore supports at most one print per
process, not one print in every process.

`NGSPICE46-DEVLIMITLOG-CALLER-LINE-MAP.tsv` contains 25 byte-verified source
lines covering all five executable call sites: diode, VDMOS, VBIC, HICUM2, and
the OSDI callback. In the VBIC loader, the call is inside the self-heating
guard and passes `Vrth`, stored `VBICvrth`, a limit of 100, and `ichk6`. Neither
the warning function nor that call prints an instance identity or establishes
which upstream calculation first produced NaN.

## Files

| File | Purpose |
| --- | --- |
| `p1_cml_div2_front_integrated_sinks_selft0_diagnostic.spice` | exact thermally simplified diagnostic candidate |
| `V5-SELFT0-DIAGNOSTIC.diff` | complete Candidate V5-to-diagnostic delta |
| `tb_p1_cml_div2_front_tran_v5_selft0_diagnostic.public.cir` | path-sanitized executable deck |
| `evidence/tb_p1_cml_div2_front_tran_v5_selft0_diagnostic.log` | complete native ngspice log |
| `raw_tb_p1_cml_div2_front_tran_v5_selft0_diagnostic.raw` | complete native binary raw plot |
| `openada-result.public.json` | path-sanitized OpenADA execution envelope |
| `evidence/tb_p1_cml_div2_front_tran_v5_selft0_diagnostic.openada-control.public.sp` | path-sanitized generated control script |
| `RAW-SUMMARY.tsv` | independently checked raw-envelope identity |
| `WAVEFORM-COMPARISON.tsv` | full-precision physical-versus-simplified waveform metrics |
| `OUTPUT-CROSSINGS.tsv` | all terminal-output zero-crossing timestamps |
| `THERMAL-NODE-COMPARISON.tsv` | `.t` vector populations and native message counts |
| `THERMAL-TERMINAL-AUTHORITY.tsv` | path-sanitized exact model-line authority map |
| `THERMAL-SOURCE-SEARCH-INVENTORY.tsv` | path-sanitized bounded source-search inventory |
| `NGSPICE-WARNING-AUTHORITY.tsv` | path-sanitized exact compiled-warning byte authority |
| `NGSPICE-WARNING-SEARCH-INVENTORY.tsv` | path-sanitized bounded warning-string search inventory |
| `NGSPICE46-SOURCE-PACKAGE.tsv` | official source release URL, size, and SHA-256 identity |
| `NGSPICE46-WARNING-CALLPATH-AUTHORITY.tsv` | official-source warning behavior and VBIC call authority |
| `NGSPICE46-DEVLIMITLOG-CALLER-LINE-MAP.tsv` | exact source lines for all five limiter call sites |
| `SOURCE-IDENTITIES.tsv` | private and public artifact identities |
| `PUBLISHED-HASHES.sha256` | hashes of every published technical file |

## Reproduction

Set `PDK_ROOT` to the `ihp-sg13g2` PDK root and run from this directory:

```sh
ngspice -i -n -o reproduced.log \
  tb_p1_cml_div2_front_tran_v5_selft0_diagnostic.public.cir
```

Move the retained raw first if it must not be overwritten. Compare a
reproduction by circuit identity, plot metadata, vector names, numeric payload
and native message inventory; binary timestamps may differ.

Project engineering status remains **unknown**. No signoff or tape-out
readiness is claimed.

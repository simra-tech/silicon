# Analog-pair LVS diagnosis checkpoint

The native full-chip LVS gate remains **failed**. This checkpoint records
completed source controls and a diagnostic localization, not tape-out acceptance.
All runs use the pinned IHP revision `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`
and KLayout 0.30.9. Installed model cards and verification rules are unchanged.

| Check | Status | Scope/result |
| --- | --- | --- |
| C45/R62 full-source splice | passed | Two declared SENSE passive changes, inverse source restoration and all 386 taps held |
| R100 full-source splice | passed | Only main-OTA resistor length 62→100 µm; all other source bytes held |
| Hard-comparator full-source splice | passed | Separate hard clone; two regeneration devices W/L 3/0.13→6/0.26 µm; soft path held |
| Native be54 LVS | failed | 900-second watchdog; no completed database |
| Logging-only copied-deck diagnosis | failed | 600-second watchdog; original purge entry localized, no acceptance credit |
| Added BGR overlay hierarchy projection | passed | Exactly 33 objects: 26 cuts and seven landings; whole-layer XOR and inverse exact |
| Native dcca LVS after that projection | failed | 900-second watchdog; the projection did not resolve the stall |
| Pre-purge diagnostic capture | passed | Complete immutable snapshot and binary64 sidecar captured; diagnostic deliberately interrupted afterwards |
| Initial snapshot/float/ID recovery controls | failed | Original incomplete virtual-write, decimal-rounding and ID-compaction failures retained |
| Final copied-snapshot recovery | passed | 293 circuits, 3,286 direct devices, 20,967 parameters; complete identity and negative controls |
| One fill-circuit copied purge | passed | 2.269 seconds, diagnostic only |
| Whole copied-netlist purge | passed | 89.778 seconds, diagnostic only |
| R100/hard-source native full-chip LVS | not run | Source preparation is not physical comparison |
| Pure-fill native LVS | not run | Separate representation-preparation experiment excluded from this checkpoint |
| Tap physical resistance qualification | not run | Symbol arithmetic/model-execution controls are not substrate characterization |
| Random seed | not applicable | Deterministic geometry and source controls |

The captured native L2N is 132,717,253 bytes, SHA256
`f7b561fb32e7d320a3c1b1485be678c3f28074f9055c922cebd65e8fa0118809`.
Its binary64 sidecar is 1,325,835 bytes, SHA256
`53ee3a86d296c99ec15073f92eb1a9aa254ddaed9d33d082dc52ccac9ca52919`.
The large raw snapshot remains retained separately; the export lists original
hashes, exact reproduction sources, normalized reports and deliberate omissions.

Recovery did not overwrite by ordinal device ID. The writer retained six
LevelDown IDs after a removed dummy, while the reader compacted them. A complete
document/class/name/terminal/parameter-token bijection and swapped, missing,
duplicate, terminal and token negative controls precede any parameter restoration.
The final copy restores every captured parameter bit exactly and keeps all net,
pin and terminal incidences unchanged. The original text serialization still
loses binary64 precision in 3,876 parameters; that failure is not waived.

The pinned writer uses 12-significant-digit parameter text. Its reader's decimal
conversion can differ from Python's binary64 conversion even for the same token.
The control therefore verifies the actual pinned formatter token before restoring
the exact captured bits on a **diagnostic copy only**. See the pinned
[writer](https://raw.githubusercontent.com/KLayout/klayout/v0.30.9/src/db/db/dbLayoutToNetlistWriter.cc)
and [decimal parser](https://raw.githubusercontent.com/KLayout/klayout/v0.30.9/src/tl/tl/tlString.cc).

Large passive-fill fanout is a plausible representation cost, but it is not
established as the cause: copied whole-netlist purge completed in 89.778 seconds.
Live extraction state/order remains an unresolved hypothesis. The native
[purge implementation](https://raw.githubusercontent.com/KLayout/klayout/v0.30.9/src/db/db/dbNetlist.cc)
and [circuit pin removal](https://raw.githubusercontent.com/KLayout/klayout/v0.30.9/src/db/db/dbCircuit.cc)
inform the next geometry-identical representation experiment. No fill deletion,
device omission, rule skip, tolerance change or acceptance-policy change follows
from these timings.

Source-reference identities (SHA256):

| Variant | Electrical/source CDL | Stock-reader CDL |
| --- | --- | --- |
| C45/R62 | `ac740690d87f2c1b27ecfa803aba8b11541da617e39e2e7f131aa90fa930fb2e` | `35b4b45b11427e327bc8a2cd145c27c70c102d00dd388a0199a0d19a96695f51` |
| C45/R100 | `5b0b4a2b284c7ee2578d0ae55cf8f9fe0646b2a4739f24d1f1edd9e7ab4320c4` | `6dceb11fbea85e5020b434fd027a306e506a4130daa44613b483b63b70d2830f` |
| R100/hard clone | `be00e66f12309bb26f16165860271936ee3f8eb74bc84c3fa56e1ee3295ccd90` | `94e50a2a7f0646282f4499831bcfe03a2cf8871fbc33a7549b6e8f94fded207b` |

# Pin-metadata harness failure and isolated recovery

The first physical-interface arm failed with signal 11 after 52.853 seconds
inside KLayout's pin-assignment routine. Electrical graph/binary64 checks had
passed, but those checks did not validate reciprocal net-to-pin metadata.
The failed run is retained; no comparison result was produced.

The pinned API's `remove_pin` removes the pin object without disconnecting its
net entry. Calling `disconnect_pin` first is required for this operation. This
was a diagnostic-harness lifecycle error, not evidence that the design passed
or that the electrical graph was wrong. The relevant unmodified implementation
is [KLayout 0.30.9 Circuit::remove_pin](https://github.com/KLayout/klayout/blob/v0.30.9/src/db/db/dbCircuit.cc#L326).

Small independent controls isolate the mechanism:

| Case | Result |
|---|---|
| Fresh two-pin identical circuit | Passed |
| Sparse IDs, old entries only on unpromoted internal node | Passed; does not reproduce failure |
| Sparse IDs with wrong wiring | Passed expected strict rejection |
| Old entries on newly promoted external node | Failed, signal −11; 72 reciprocal entries instead of one |
| Disconnect before removal, same sparse IDs | Passed; exactly one entry on each external net |
| Fresh-ID equivalent circuit | Passed |
| Fresh-ID wrong wiring | Passed expected strict rejection |

Thus sparse numeric IDs alone were not the cause. The initial Python-control
accessor error and both non-reproducing preliminary test sets remain retained.
The recovery preserves the original electrical API objects. It disconnects
metadata before removing it and checks the entire bidirectional pin relation
before projection, after projection, after reverse restoration, and finally.
Every electrical net/device/binary64/terminal fingerprint must still agree.

The recovery fixture is hash-bound by
`048708774b10584925c6423b81c76382b108648fd2597e838a9fc15103c7233f`.
It supplies harness evidence only. Original and tap-adapted full comparison
arms retain their own outcomes; this report makes no fullchip LVS claim.

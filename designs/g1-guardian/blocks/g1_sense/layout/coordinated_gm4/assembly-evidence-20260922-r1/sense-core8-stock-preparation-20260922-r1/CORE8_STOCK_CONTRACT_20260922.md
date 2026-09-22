# Eight-device core stock gate

Independent saved-polygon audit passed400 channels/408 diffusion strips,
eight source-exact W/L/ng/default-junction attributions and13 electrical nets.
Pair centroids coincide at115,59.25um. Source-native polygons,5nm grid,
230x164um bounds and thirteen remaining native-device obstacles passed.
This is not the full21-device main OTA or full SENSE macro.

GDS SHA256 b7f1e3c68b18e81617c992ee3f1001c309070e5b50fb20c96cd80ce4dc0b90db;
reference manifest3311ec4c72310a8057a0504b68c4405d52d57562f96c41780e924f61177c5149;
complete eight-device CDL fb5326d73b1f05543781f4f21c818a6823e0a879a7098389d1bfc560a2b9e8b8.

One unchanged stock deep DRC, density disabled, one CPU7,180s plus5s kill grace.
Only after DRC passes, one unchanged stock deep strict LVS under the same bound.
Fresh resource assessment for this at-most0.10GiB batch;4GiB RAM reservation
only. No model/deck/source/geometry changes. Require zero markers and every
LVS cross-reference Match, explicit match text, zero process exit, unchanged
input/deck hashes and bounded output. Missing or malformed results fail closed.
Retain any failure; no automatic retry, reroute or broader PEX.

Density/antenna, intrinsic shared-junction equivalence, mismatch, full-main
and full-SENSE routing/fit, extracted electrical checks, current/IR and adoption
are **not run**. Seed **not applicable**. The builder's prospective geometric
junction allocation is not a waiver for the separate model-applicability issue.

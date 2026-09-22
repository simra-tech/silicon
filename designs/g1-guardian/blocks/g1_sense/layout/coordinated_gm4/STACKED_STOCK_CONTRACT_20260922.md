# Isolated stacked64 r2 stock gate

The r2 guard correction passes in-memory and independent saved-GDS channel,
terminal, 5nm grid, W/L/ng, adjacent-gate A/P allocation, centroid and bbox
checks. No saved layer is modified during this gate. GDS is
`8818ee050f60243b34b8985f9630ed3d9704351d9874ef656a7202bba8290bf3`;
source remains `baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877`.
All19 other native devices have zero same-layer overlap and zero200nm expanded
overlap with this pair. Their future guards/contacts/routes are not included.

After a fresh0.05GiB resource gate, run exactly one stock deep DRC, then strict
LVS only if DRC passes. CPU7;180seconds per child plus5seconds kill grace;
50MiB phase bound checked after each child. DRC includes stock hard/recommended,
grid and angle checks but not density, with one worker. Require zero markers
and return0. LVS requires return0, explicit success and all strict Match
statuses, never MatchWithWarning. Keep source/CDL/GDS/manifests and stock decks
byte-exact before/after. Missing reports or unknown status fail closed.

CDL contains exactly the two unchanged source MOS; the existing converter drops
ng/mm_ok, so those properties rely on separate saved-native checks, not LVS.
Stock A/P annotations and intrinsic shared-junction applicability remain
separate. Density, antenna, whole-main/SENSE routing, PEX, dynamic/mismatch,
current/IR and adoption are **not run**. Seed **not applicable**. Preserve r1
channel failure; no source/card/deck changes or automatic revision/retry.

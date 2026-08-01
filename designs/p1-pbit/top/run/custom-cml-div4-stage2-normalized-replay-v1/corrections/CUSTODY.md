# Normalized replay custody history

This record separates reproducible circuit evidence from defects in the
versioned package creation record.

## Runtime package

The source/deck package contains 8 files and is identified by original sealed
manifest SHA-256 `d84ffa0bf2a35ab3ec983cc0a38fe988f2621f2805de17faa2f78f439999f0f0`.
The runtime contains 13 files and is identified by original sealed manifest
SHA-256 `61a781fe8cca4f9942f7b2ea27c13d264a84703b90e8e52ce4bd6f7212cc74a6`.

The runtime executed ngspice once, with no simulator retry. Its outer command,
however, recursively removed the versioned package root before creating it and
did not first bind or prove root absence. Prior content absence is therefore
unproved. No deletion loss is asserted. The correction note, inventory, and
manifest have original SHA-256 identities `ab5a8a24311dc98dd7d535f6efbf3dc2cb66fb962cd5aac52bc95ef4eafe14eb`,
`a653b7b084cbcdd4e345388b15441657ac715455e17337593d0a3b2c394f5d1e`,
and `a5309b934a9d8b3480c505f2a4a0053ebbf880037c8ff2d9dc415121b2ab84d9`.

## Waveform-analysis package

The final V1 fact table and manifest have original SHA-256 identities
`1428b09171bfd79bc63ea6aabc6070b71cae38e807f284fb0ebeed0d1b273255`
and `17ca97abdf9087a459b9639cef8f1656db1c82e07d514a94e0a5b2f771b5f88f`.
The V1 report's no-retry and no-pre-clear claims do not describe the complete
creation chain:

1. The first parser/self-check pipeline ended with six self-check failures.
2. The second pipeline inventoried the task-owned draft by names and count,
   recursively removed it, and ended with four self-check failures.
3. The third pipeline inventoried and recursively removed that draft, then
   completed with zero self-check failures.

The failed draft names/counts remain in the private creation record; their
bytes and hashes were not retained. No simulation or raw file was rerun during
these analysis retries.

The V2 correction correctly described that chronology, but bound visible
message content rather than the separate command-bearing record. Its note,
inventory, and manifest identities are `ee53a6ed8b6d5602e7de5797fd72a475ac05808e2cbca435e27d378c190a2f79`,
`15af60e078948d566fc704c324292c67a554becd8017feadeadd806c0f860969`,
and `ffd78b1201b0c83f9f7bea20cafbe5ccff901475eceeee8039ac6842169a17b8`.

V3 bound the command-bearing records correctly. Its note, inventory, and
manifest identities are `ab2bbc13275fc516fbf2f25c2124c672bdd59fa015a755f8e93ce09572a48deb`,
`009492920392d2b82f95642ed0ca2cb9cf1a9465800c2fee12ba7d7f4ae53318`,
and `c53c9f077ad615d3674867508ccd17d35dc88d28debb85253e6643bfcba77d70`.
Its substantive bindings survived independent review, but its self-description
did not: the final V3 followed an earlier sealed draft, an external check with
three presentation failures, an inventory by names/count, a recursive
pre-clear, and regeneration.

The authorized V4 record was required to validate all bytes before directory
creation and to stop without retry on any failure. Four wording checks failed
in memory. The generator exited before creating a V4 directory, a read-only
recount found the directory absent and the sealed V1/V2/V3 file counts still
6/3/3, and no retry occurred. A curated public-safe failure record is retained
alongside this note.

## Disposition

V4 is a preserved execution-record failure, not a circuit failure. The V1
fact table is used only after `VERIFY-PUBLIC-NORMALIZED.py` independently
reconstructs all 49 rows from the raw. No correction artifact is presented as
proof of causality, compatibility, a specification, signoff, or tape-out
readiness.

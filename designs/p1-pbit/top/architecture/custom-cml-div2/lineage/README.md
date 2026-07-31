# Comparator latch lineage for the custom CML divide-by-2

This directory records the static audit used to decide whether the existing Top V3 comparator
track/latch can seed a standalone CML divide-by-2 implementation.

The accepted V4 record reproduces all 21 device lines from
`designs/p1-pbit/top/source-backed-v3/p1_top_hier.spice` lines 130–150 exactly. An independent
comparison found 21 unique source lines, zero mismatches, valid UTF-8, zero tab bytes, and zero
other unexpected control bytes. The retained source netlist SHA-256 is
`b8ac82719ffcd365b91fbd7c997b45d9d422e684077fe82f05a691cb7dcbd4ca`.

## Record dispositions

| Record | Source SHA-256 | Disposition | Reason |
| --- | --- | --- | --- |
| V1 | `786ccc71224fd002c9bb68dad2d777d448a8f521280e8d141a970a38becacecc` | Rejected | Parsed rows dropped explicit source tokens and inserted defaults not present in the netlist. |
| V2 | `2ff7cd4fbf8eaa74ac2953d02a91917f1966fa230c6c6b4f373e10d8a49c7bbe` | Rejected | The literal rows were exact, but one authority entry conflated requirements with architecture. |
| V3 | `4d2615de0093bded59629831c4a85616833c22364bd15d54cd14cc9978fede5a` | Rejected | Three `\text{C}` temperature expressions were changed into tab bytes followed by `ext{C}`. |
| [`current-v4/`](current-v4/) | `944a4aa0a147ef1a1898b6119f1ba41f91cacf271cff19531adea33210a914c1` | Current | Exact literals and authority categories are preserved without control-byte corruption. |

The Principal Engineer retained the audited structure and literal device parameters only as a
provisional first implementation seed. This is not evidence of divide-by-2 function, 5 GHz
capability, output swing or common mode, startup, load drive, PVT operation, power, or sizing
adequacy. The audit contains no circuit, testbench, simulation, electrical pass, signoff result,
or tape-out-readiness claim.

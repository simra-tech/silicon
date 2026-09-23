# XM14 local feeder field diagnostic

The pilot **failed the frozen 1% context-convergence gate**. All four
source-bound ordinary-metal extractions, complete physical-component
accounting and eight independent AC comparisons passed. This is not
complete PEX, a qualified circuit delta, or adoption of the feeder remedy.

The prospective scope is recorded in
[the unchanged freeze](SENSE_FEED_FIELD_PILOT_FREEZE_20260923.md).
Original r8 `8060e30a...`, isolated four-feeder candidate `4b8a82d4...` and
canonical source `baab6183...` remained fixed. Only the 20 um-long middle
of XOTA/XM14 was tested. Both 24 and 48 um transverse windows contained
zero floating fill and zero MIM/Vmim, verified independently at preparation.
Each clipped conductor component was bound to its full-source net and
independently checked against the saved clip and extracted label aliases.

## Results

All values below are extracted from the unchanged stock serialized
ordinary-metal capacitor graph, in fF. P groups source-proven `vdd` pieces;
N groups source-proven `XOTA/pc1` pieces. Pieces within each group are held
at equal diagnostic potential outside the clip; all other drawing nets
and VSUBS are grounded. This does not establish finite-R terminal attachment.

| Layout/context | P-ground | N-ground | Mutual P/N |
|---|---:|---:|---:|
| Original / 24 um | 6.54685440 | 5.51173332 | 0.19793886 |
| Original / 48 um | 9.52860932 | 7.33896350 | 0.74702486 |
| Candidate / 24 um | 7.52502080 | 5.60870292 | 0.34521200 |
| Candidate / 48 um | 10.50677572 | 7.41310200 | 0.89429800 |

All nine frozen metrics failed for each layout: every 2-by-2 matrix entry,
P-ground, N-ground, mutual, differential-energy and common-mode-energy C.
Original relative context changes range from 24.90% to 73.50%; candidate
changes range from 24.34% to 61.40%. There were no zero denominators in
these results. The wider window includes additional portions of the same
P/N source nets as well as other context nets; the absolute grouped field
therefore changes with that boundary. This observation does not waive the
prospective convergence test or establish a different acceptance criterion.

Candidate minus original mutual C is +0.14727314 fF in both windows;
P-ground delta is +0.97816640 fF, and N-ground delta is +0.09696960 /
+0.07413850 fF at 24 / 48 um. These signed differences are descriptive only:
agreement of a selected delta cannot replace the failed complete-matrix
gate. No capacitor was inserted into a compact-model circuit.

| Check | Disposition |
|---|---|
| Eighteen synthetic/parser/rejection controls, host and pinned runtime | Passed |
| Four saved clip XOR/source/net/component/fill/MIM checks | Passed |
| Four bounded native exports and stock CC extractions | Passed |
| Eight finite independent AC comparisons, original 1e-25 F tolerance | Passed |
| Complete matrix charge conservation | Passed |
| Floating-fill Schur solve | Not applicable: zero fill/internal floating block |
| Original 1% context gate, 18 metrics | Failed, all 18 retained |
| Other feeder sites, whole strip or fullchip context | Not run |
| Primitive electrode field / MIM deembedding / finite-R model composition | Not qualified |
| Electrical circuit delta, current/IR/EM acceptance, adoption | Not run |

The wrapper completed in 26.630 s, native pilot body in 17.856 s; observed
combined clip/pilot files were 711,153 bytes. Every child completed inside
its frozen 30 s native-export / 120 s CC / 30 s AC bound. There was no
timeout recovery, criterion change or automatic expansion.

## Reproduction and retained evidence

The portable evidence directory `evidence/feed-field-20260923-r1/` retains
exact input clips, provenance, raw SPICE capacitor graphs, matrices,
synthetic controls, all eight AC decks/logs, stage receipts and failed
aggregate summary. Text path prefixes are made portable; binary input
clips remain byte-exact. Large backend scratch databases are omitted
with hashes and sizes recorded, not represented as rerun or passed checks.

Run `prepare_sense_feed_field_inventory.py`, then
`prepare_sense_feed_field_clips.py`, then `run_sense_feed_field_pilot.py`
with the CLI arguments in the retained receipts after resolving `${REPO}`,
`${BULK}` and `${RECEIPTS}`. The runner rechecks all source hashes and
reruns the eighteen controls before extraction. It exits nonzero for the
retained context failure.

| Built against | Identity / evidence |
|---|---|
| IHP SG13G2 PDK | `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`, checked from pinned COMMIT |
| Runtime image | `sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2` |
| KLayout | 0.30.9, runtime assertion and stock logs |
| ngspice | 46, pinned runtime and AC logs |
| KPEX | Pinned installed package; exact rule-file hashes and command lines in pilot summary |

The earlier model-boundary failures remain unchanged: source NGCON2 versus
the separate one-ended-gate baseline, 51 stock A/P annotation differences,
shared-input junction applicability, 171 unresolved body/BN/MIM/port
attachments, and unsupported complete MIM extrinsic deembedding. The
dual-ended-gate prototype was not combined into this feeder candidate.
Neither a chosen point contact nor assumed equipotential body is introduced.

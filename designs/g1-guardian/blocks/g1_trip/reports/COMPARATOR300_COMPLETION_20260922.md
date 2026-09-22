# Comparator 300-sample completion — simulated

All 300 distinct seeds 62001–62300 completed their 25/−40/125°C cases:
900 numerical cases, with all 32 observed parameters frozen per sample and
no source/model/runtime identity failures. All 900 cases contain locally
nonmonotonic staircase decisions. Their finite ambiguity intervals are not
unique offsets; maximum width is 0.500 mV. No standalone offset acceptance
limit is allocated, and no joint-chain yield is inferred.

This remains the frozen rev1 comparator-cell PEX fixture at 0.75 V common mode,
with ideal symmetric 1 kΩ/1 pF sources, 401 sampled staircase decisions,
SPARSE/TIGHT-TRAP and 0.2 ns maximum step. It does not represent the loaded
25 kΩ conditioner/DAC interface. The raw comparator source SHA256 is
`a87027a83145a84df0337a97d65c87cdbfd1fc6f4ff8f4c209ba4b40499ceab9`.
The pinned ngspice 46 image and IHP PDK commit
`84374023ee8b4b126bebbba67fcbada0a9c0ff0b`, model hashes, exact commands and
per-leaf source identities are retained in portable provenance.

The [complete analysis](resume-server-20260922/comparator300-ambiguity-analysis.json)
retains all 20 parent campaigns and all temperature ambiguity envelopes.
The [full evidence audit](resume-server-20260922/comparator300-evidence-audit.json)
passed exact seed coverage, sample contracts, raw source identity and
source/model/runtime checks. It verified compressed-wave hashes for 878
individual leaves; the remaining 22 cases are literal previously completed
original cases. Original multi-temperature timeouts, including seeds 62007
and 62008, remain retained and are not reclassified by this completion.

The newest 200 seeds added eight completed parents and 600 completed leaves.
All 608 compact portable exports preserve logical repository-relative run IDs,
summaries, runner snapshots, source/tool/PDK identities and artifact hashes.
Bulk waveforms remain separately retained, not copied into the public report.
Mean retained individual-leaf size is 9,801,301 bytes; maximum is 9,910,153
bytes. Exact decoded parity is documented by the immutable archival receipts;
this final audit rechecks compressed hashes, not a newly inferred byte parity.

Median three-temperature sample numerical time is 252.162 s. Numerical
completion is **passed**; unique-offset acceptance is **not applicable**;
loaded-chain statistical qualification and physical adoption are **not run**
by this campaign.

Reproduce the aggregation from `blocks/g1_trip/sim` using
`analyze_cmp_qualification.py` on the 20 campaigns listed in the analysis,
then `audit_cmp_campaigns.py --campaigns <same IDs> --seed-start 62001
--seed-stop 62301 --raw-source-sha256 <hash above> --output <fresh JSON>`.
These readers do not launch simulation or discard historical failures.

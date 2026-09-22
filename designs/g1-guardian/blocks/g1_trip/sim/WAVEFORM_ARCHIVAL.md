# Lossless waveform archival

New joint-kickback and comparator qualification runs can opt into gzip archival:

```
flow/run.sh env G1_ARCHIVE_NEW_WAVES=1 python3 run_joint_calibration.py ...
flow/run.sh env G1_ARCHIVE_NEW_WAVES=1 python3 run_cmp_partition_campaign.py ...
```

The flag is inherited by child leaf runners. It does not change netlists,
numerical settings, saved vectors, samples or acceptance limits. Archival is
disabled by default. Existing run directories are never scanned or compressed.
Each runner creates a fresh run directory and archives only its own waveforms
after saving and interpreting the solver result. Partial saved waveforms from
failed attempts are retained with their original incomplete status.

For each `*.dat`, `wave_archive.py` writes `*.dat.gz` at gzip level6, verifies
the decompressed SHA256 and byte length, then records both raw/gzip hashes,
lengths and the archiver hash in `*.dat.archive.json`. Compressed data and the
receipt are flushed before removing the redundant plain representation. The
original bytes can be restored exactly by decompression. Compression errors
before that removal leave the plain file intact; partial compressed files must
not be treated as valid archives. Neither source snapshots nor logs are removed.

`compare_host_replay.py`, `compare_joint_solver.py` and
`compare_cmp_partition.py` and `analyze_joint_waveforms.py` accept either plain
data or a verified archive. A
missing plain file without its valid receipt/archive is an error. Host parity
uses the uncompressed waveform hash, preserving its strict full-output check.
Joint and partitioned-comparator campaign resumption consumes unchanged JSON
summaries and source snapshots. Other ad hoc readers that directly open `.dat`
must use `open_wave`/`resolve_wave` or explicitly restore the original bytes.

Verification command:

```
python3 -m unittest test_host_replay.py test_dac_chunks.py test_joint_calibration.py
```

26focused tests passed with Python3.6.8 on22September2026 (including
`test_result_directory.py`), including lossless parity of
a temporary copy of a completed joint trace, default-disabled behavior, corrupt
archive rejection, exactly unchanged joint-waveform characterization, and
original preservation on simulated compression failure.
This validates archival behavior, not circuit performance or a new simulation.

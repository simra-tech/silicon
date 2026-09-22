# Simulated actual-BGR DAC125°C all-code completion

Seed51001 now has an explicitly audited full256code125°C DC transfer.
[Coverage audit](resume-server-20260922/dac-hot256-explicit-coverage-20260922-a.json)
joins43completed four-code leaves0–171 from the preserved failed fullhot parent
with42fresh two-code leaves172–255. Every code occurs exactly once. All85leaves
match the actualBGR/SENSE/TRIP circuit, source/model/tool identity and31observed
end parameters; code0/127/255 printed operating points exactly match the saved
125°C phase of `dac-actualbgr-reset-klu-pilot-20260922-a`.

| Simulated metric | Soft | Hard |
|---|---:|---:|
| Numerical full256 completion | passed | passed |
| Strict monotonicity | passed | passed |
| Minimum step |1.830mV|1.837mV|
| Minimum endpoint DNL |−0.023735LSB|−0.018750LSB|
| Maximum absolute endpoint INL |0.101246LSB|0.095250LSB|

No standalone INL limit is allocated. Full256 temperature-return transfer,
dynamic settling and statistical all-code ensemble are **not run**.
The nominal25°C256transfer is a separate completed pilot, not an unrecorded
return sweep. Parameters are recorded after each code list, not before/after
every code. No stronger instrumentation or physical-yield claim is made.

The original `dac-chunks256-hot-tight-pilot-20260922-a` remains
**failed/incomplete**. Its c172 watchdog saved172–174 but no175row or final
parameter vector. All three partial rows are excluded from accepted coverage;
their printed values match the new complete leaves as a diagnostic. The audit
does not alias, overwrite or relabel that failed attempt.

The fresh continuation command inside the pinned runtime was:

```sh
python3 run_dac_chunks.py --run-id dac-hot-tail-two-20260922-a \
  --image-id sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0 \
  --seed 51001 --temps 125 --chunk-size 2 --workers 4 \
  --code-start 172 --code-stop 256 --tight
```

Four independent one-thread ngspice46 processes, unchanged120s leaf watchdog,
KLU and tight settings were used. Full exact commands and hash inventories are
in the exported parent/42leaf provenance. PDK revision is
`84374023ee8b4b126bebbba67fcbada0a9c0ff0b`; models were unchanged.

Selected completed leaves total4866.14core-seconds; the failed c172 adds120.02s,
with earlier qualification costs retained separately. The42two-code leaves
total1208.70core-seconds. Extrapolating only that tail's mean to128two-code leaves
gives3683.65core-seconds per fresh fullhot sample; code-dependent cost and prior
watchdogs mean this is not a worst-case or statistical-ensemble guarantee.
Maximum observed two-code retained leaf size is970,925bytes;128such leaves
project118.53MiB before parent metadata. Bulk evidence remains retained, with
portable summaries, exact runner/provenance copies and full hash inventories.

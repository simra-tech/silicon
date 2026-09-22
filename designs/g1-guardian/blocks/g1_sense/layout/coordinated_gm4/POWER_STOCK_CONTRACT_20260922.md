# Isolated SENSE power-routing gate

The candidate is a separate revision of the checked, unfilled r5 macro. The
canonical source, 58 MOS W/L/ng and native junction geometry, 98 resistors,
three MIM capacitors, matching centroids and seven signal ports are held.
Only added routing and the two declared power-port locations/layers change.
The source SHA is baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877.

Before stock checks, require the independent saved-geometry/source audit,
134-net graph bijection, exact source-derived CDL hash, 5 nm grid and
385 × 240 µm reservation. Use the unchanged pinned PDK decks and tools.
Run one no-density stock DRC and, only after zero markers, one strict
hierarchical LVS with nine external pins and no series-resistor reduction.
Each child is bounded to 180 seconds and the retained output to 50 MiB,
as in the frozen full-SENSE stock runner. Require zero return codes, actual
reports/databases, strict comparisons, and unchanged pre/post bindings.
Any failure is retained; subsequent conditional checks are not run.

The via-only graph audit is separate: enumerate actual physical cuts,
one-cut-open connectivity and per-terminal cut capacity. Metal-width/current
distribution is not implied by a summed via capacity. The exploratory total
macro design envelope is 2 mA at 50% engineering utilization, using published
105 °C / 11-year limits only. Actual branch allocations, current crowding,
pulse qualification, 125 °C lifetime and complete PEX remain independent.

Stock LVS does not validate ng or native model junction applicability. Keep
the 51 failed prior stock A/P annotations and shared-junction model question
explicit. No source/model/deck tuning, geometry adoption, final fill or full
PEX is authorized by a passing result here.

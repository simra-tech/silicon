# SENSE input route resistance: copied DC anchor

All **27 OP points completed** for the baseline SENSE schematic at TT/typ, 3.3 V and 27°C, with geometry-estimated padbare input route resistances scaled by 0, 1 and 2. The zero-resistance control exactly matches all seven printed vectors from the original nine-point corner fixture. The nominal estimated route model reduces gain below the **19.9 V/V** follow-up criterion and increases common-mode conversion. This is a demonstrated model sensitivity; these resistances are geometric estimates, not extracted parasitics or measured silicon values.

| R scale | P / N branch Ω | Gain at CM=0, shunt0→50mV | 25mV output at CM=0 V | Change from zeroR mV | Output span CM−0.1→+0.3 at25mV mV |
|---|---:|---:|---:|---:|---:|
| 0 | 0 / 0 | 19.98798 | 1.49893 | 0 | 0.060 |
| 1 | 77.6671 / 138.2311 | 19.71696 | 1.48646 | −12.47 | 2.340 |
| 2 | 155.3342 / 276.4622 | 19.45338 | 1.47432 | −24.61 | 4.570 |

At scale1 the core sees 24.376 mV for an external25mV differential input at zero common mode. The scale1 common-mode output span is approximately0.119mV input referred using its actual DC gain. A fixed gain/offset calibration at one common mode does not remove this common-mode dependence. The scale2 case is an explicit sensitivity, **not** a guaranteed upper bound.

The [route audit](SENSE_ROUTE_FILL_20260922.md) separates P wire37.6671Ω / N wire98.2311Ω from40Ω via contribution in each branch (two single Via3 instances,20Ω each from the nominal technology model). The fixture inserts these branches between the ideal external Kelvin input sources and the first two SENSE terminals, leaving the original supply/return/reference/PTAT and output load unchanged. There is **no587Ω secondary-pad resistor** in series: the assembled design uses padbare connectivity. Pad capacitance, fill coupling, route temperature/process variation, actual BGR bias and dynamic kickback are not qualified by these OP runs.

[Raw results](sense-input-route-anchor-20260922-r1/summary.json), [analysis](sense-input-route-anchor-20260922-r1/analysis.json), source hashes and exact per-run decks/logs are retained. The original fixture uses printed six-significant-digit values; derived gain and small nonlinearity differences have corresponding rounding limits. No original source or delivered geometry was edited.

Reproduce in a fresh output directory from repository root:

```sh
G1_CPUS=1 flow/run.sh python3 designs/g1-guardian/review/audits/run_sense_input_route_anchor.py --output designs/g1-guardian/review/audits/sense-input-route-anchor-NEW
python3 designs/g1-guardian/review/audits/analyze_sense_input_route.py designs/g1-guardian/review/audits/sense-input-route-anchor-NEW
```

An isolated physical routing remedy is now justified: wider paths, better balanced resistance, legal via arrays, and rerun connectivity/stock DRC/electrical checks. It remains separate from the unadopted OTA sizing candidate; transistor sizing alone cannot remove input-divider ratio loss caused by external series resistance.

## Matched branch allocation anchor

A further27 copied OP points completed at20,35 and40Ω in **each** branch. AtCM0 the gains are19.94792,19.91788 and19.90808; every tested common mode passes the19.9 follow-up criterion. [Raw results](sense-input-route-matched-20260922-r1/summary.json) and [gain checks](sense-input-route-matched-20260922-r1/gain_analysis.json) are retained. Local extrapolation suggests a matched ceiling near44Ω; that ceiling itself was not simulated and is not a PVT limit. An approximately20Ω balanced target provides nominal margin. The original40Ω via-only estimate leaves little wire budget near the criterion, motivating legal via arrays as well as wider wires.

```sh
G1_CPUS=1 flow/run.sh python3 designs/g1-guardian/review/audits/run_sense_input_route_anchor.py --output designs/g1-guardian/review/audits/sense-input-route-matched-NEW --matched-ohms 20,35,40
```

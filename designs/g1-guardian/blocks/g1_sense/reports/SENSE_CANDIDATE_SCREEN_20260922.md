# Isolated gm4 / compensation3 screen

Status: **passed declared standalone screen; not adopted**. All numbers below
are simulated, not measured. This is not joint-chain trim yield or physical
qualification. The source remains an isolated run snapshot.

The main OTA input pair is scaled4, the selected main matching group is scaled4
linearly (16× area), and compensation area is scaled3. Reference and pedestal
buffer sizes remain unchanged. The exact candidate source SHA-256 is
`baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877`.
Its logical source is `sim/qualification/mc-gm4-comp3-smoke20-b1-20260922-a/sense_substrate_tied.spice`.
An [exact portable source copy](resume-server-20260922/gm4comp3-qualified-source.spice)
has the same hash; it is a qualification artifact, not an adopted netlist.

## Evidence

| Check | Result | Scope |
|---|---|---|
| Original seeds41001–41100 | passed100/100 numerical,3600OP | Every sample retained; no selected-seed replacement |
| Sample identity | passed | Same candidate/model/runtime across8runs;51observed parameters frozen over25/−40/125/25°C |
| Return25°C | passed | Exact equality of saved printed OP rows |
| Frozen continuous-correction residual | passed; worst498µV | Seed41039,125°C,trueCM+0.3V,zero shunt; only2µV below500µV limit |
| Gain screening | passed100/100 | 19.9–20.1 declared screen |
| Loaded AC bandwidth | passed selected3.3/3.6V | 2.574/2.676MHz; not allPVT |
| Selected Tian loop screens | passed7/7 | Conditional phase margin61.160–69.163°; DC-equivalent injection, ideal bias/passive load |
| Joint actual-BGR/digital-code calibration | not run to completion | Separate three-sample pilots underway; no result implied here |
| Candidate layout/DRC/LVS/PEX | not run | No physical adoption |
| Measurement | not run | No silicon sample |

The nominal25°C/CM0/shunt25mV correction is frozen before testing other points.
The historical fixture parameter is SENSE_N, not average common mode:
21of27endpoint points/sample are inside the specified average-CM range;
6outside-CM diagnostics remain separately reported. Both sets passed this screen.

The2µV worst-case margin is not a robustness claim. Uncalibrated population
sigma is0.7473mV. An offline ideal-DAC calculation still clips the hard code254
for46/100samples; it omits actual BGR/DAC/comparator mismatch and is not measured
or joint-chain yield. There is no claim that these larger devices fix code reach.

Loaded nominal input-noise PSD integrated1Hz–2MHz changes from60.03µVrms baseline
to36.64µVrms candidate. Output noise divided by nominal20 through10MHz changes
79.12→44.45µVrms, while frequency-dependent input-referred PSD integral changes
108.71→112.25µVrms. No standalone noise limit is allocated; these are distinct
quantities, not a blanket broadband improvement claim.

## Reproduction and retention

[Full100 analysis](resume-server-20260922/gm4comp3-screen100-analysis.json) and
[frozen-screen audit](resume-server-20260922/gm4comp3-screen100-audit.json) identify
all8input runs, exact hashes and every physical sample. Each run's directory in
`resume-server-20260922/` contains exact command arguments, runner snapshot,
source/model/tool identities, summaries and a SHA-256 artifact inventory.
Bulk evidence is retained by repository-relative logical run ID; no private
machine storage path is part of this record.

Built against IHP SG13G2 commit`84374023ee8b4b126bebbba67fcbada0a9c0ff0b`,
ngspice46, pinned image manifest
`sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0`;
observed version output and model hashes are in each provenance file.

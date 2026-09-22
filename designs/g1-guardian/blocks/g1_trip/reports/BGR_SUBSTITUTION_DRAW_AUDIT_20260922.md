# BGR substitution: room OP realization gate — simulated

The room operating-point comparison passed all8,670 declared non-BGR
mismatch-parameter checks, with exact ordered keys and string values.
This qualifies a controlled reference-substitution preparation; no substitution
transient or new calibration is established by this OP result.

| Check | Result |
|---|---|
| Original baseline numeric/query completion | passed,14.213 s |
| Candidate numeric/query completion | passed,19.266 s |
| Non-BGR MOS parameters:1,290 devices×4 | all5,160 exact |
| Non-BGR resistor parameters:1,168 devices×3 | all3,504 exact |
| Six CMIM mismatch scales | all6 present, finite and exact |
| Original24 SENSE/TRIP legacy anchors | exact in both |
| Original three BGR legacy anchors | exact in baseline; explicitly changed in candidate |
| Candidate2,842 BGR nominal parameters | all exact versus retained nominal manifest |
| Model/PDK/runtime and non-BGR source identity | exact |

Seed71002 and the complete room25°C fixture prefix remain unchanged, including
3.3/1.2 V rails,24.5 mV shunt, codes136/154, declared5 MHz clock, loads and
body connections. No transient command exists in either OP audit. SENSE source
is `baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877`;
grounded TRIP copy is `f49e17db24fc85f4f62aab3cc98dce996d027567417ad80cfea13d11609ba2e1`.
Only BGR source bytes change from archived mismatch-enabled
`944aaf94b9a005718abd0ebd92956acc99e8cb7a23ec8556d406736f4e8ef6f9` to nominal
`586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b`.
The pinned image/PDK/model hashes and original/reference-manifest hashes are
live-checked before each leaf and retained in portable provenance.

The replacement has336 MOS,399 resistor and301 HBT instances. Its literal
source has no `mm_ok` overrides; the unchanged pinned mismatch wrappers default
to zero. This was verified by all2,842 observed nominal values, not inferred
merely from using the same seed. The altered device count was not assumed to
preserve random-draw order: the independent full non-BGR inventories establish
the observed equality.

The original27 anchors split into24 non-BGR and3 BGR parameters. The BGR
changes are XM34 `delvto` −0.726465 mV→0, XR16 `nsmm_rsh` −1.166311→0,
and XQ56 area factor1.157897→1. They must not be presented as unchanged.
The old BGR full inventory contains242 parameters, versus2,842 new parameters.

## Capacitor/query provenance and scope

Each CMIM query addresses its actual inner `C1[scale]`:
`xs.xota.xcc`, `xs.xbuf.xcc`, `xs.xref.xcc`, `xt.xcond.xch`, `xt.xchs`,
and `xt.xchh`. In pinned `capacitors_mod_mismatch.lib`, SHA256
`ed188acac7c5830656ef218871f99b2ace021e37b332ea9adaf505eed3d9d937`,
the `cap_cmim` wrapper connects random `cap_carea_mm` to that scale using
`1+(cap_carea_mm-1)/sqrt(l*w*1e12)`. All six query names were available;
no nominal-capacitance fallback or omitted capacitor was accepted.

Distinct ordered groups are retained as `LEGACY27`, `NON_BGR_ALL` and
`BGR_ALL`. Quiet9-node outputs and all warnings are serialized. There were
39 baseline and32 candidate warning lines, including OSDI voltage-limit
warnings; numeric completion is not a model-validity or reliability pass.

Quiet VREF changes1.015614334→1.045458934 V, IPTAT pin voltage
0.751378319→0.757515447 V, ISENSE1.479770399→1.508232944 V, and hardDAC
0.784316046→0.807377942 V. IPTAT pin voltage is not output current. The
nominal reference level changes as well as its expected temperature behavior;
old-code results cannot establish new calibration accuracy.

## Reproduction and retained evidence

A separate originalhot125°C prerequisite,
`joint-bgr586-drawaudit-baseline-hot-20260922-a`, completed in17.535 s.
All27 original anchors and all8,670 queries passed; its full inventory also
equals the room inventory, with a separate hot result retained rather than
assuming temperature invariance. All113 warning lines are retained.
This does not by itself qualify a new-BGR hot transient.

Run IDs are `joint-bgr586-drawaudit-baseline-room-20260922-a` and
`joint-bgr586-drawaudit-candidate-room-20260922-a`. From `blocks/g1_trip/sim`,
prepare with `prepare_bgr_substitution_draw_audit.py`; execute each using
`run_bgr_substitution_draw_audit.py --run-id <id> --image-id <pinned-manifest>
--timeout-s 120`, baseline first, stopping on baseline failure. Compare with
`compare_bgr_substitution_draw_audits.py --baseline <id> --candidate <id>
--output <fresh-json>`.

The [full parity report](resume-server-20260922/joint-bgr586-room-full-draw-parity.json)
has no non-BGR differences. Both portable-run exports retain the complete
parameter order/value groups, source/runtime bindings, literal deck differences,
runner snapshots and artifact hashes. Five focused OP-query tests passed,
including missing-capacitor, nonfinite-value and reordered-query rejection.

Source-substitution transient acceptance, new calibration, BGR mismatch
population, joint MC, new-geometry PEX and candidate adoption are **not run**
as part of this OP gate. Earlier hot electrical failures remain unchanged.
The inherited [SENSE physical-fidelity gate](../../g1_sense/layout/coordinated_gm4/README.md)
is failed; this is an existing-model-level comparison, not physical qualification.

The subsequent [controlled transient report](BGR_SUBSTITUTION_TRANSIENT_20260922.md)
records room completion and the separate hot watchdog failure. Those later
results do not change the scope or acceptance of this OP-only gate.

# Native PSP junction charge-difference observation

The three bounded controls **passed** for one ideal-biased, unchanged
canonical PMOS. This establishes a signed native BS-side **charge-difference
observation method**, not absolute charge or shared-layout equivalence.

The existing physically reconstructed BS/BI identities, native RJUNS and
MULT=m×NF=64 give junction dynamic current from BS KCL after subtracting the
known simulator rshunt and native static `ijs`. Its integral is compared with
an independent integration of native `cjs` against actual SI−BS voltage.
Neither the compact model nor any internal-node electrical connection changes.

| Control | Simulated result |
|---|---:|
| Initial static KCL absolute residual |1.62e−17A |
| Zero-amplitude maximum absolute charge change |2.83e−25C |
|0.3V body-ramp peak charge change,0.05ns maximum step |15.1188848fC |
| Fine-step return-cycle residual |9.97e−20C |
| Fine native-current versus capacitance integral maximum difference |3.33e−18C |
|0.1ns versus0.05ns complete-trace maximum difference |2.75e−18C,0.01818% |

The prospective gates were static KCL≤1e−15A, zero-ramp charge≤1e−20C,
and return-cycle/integral/timestep differences≤max(1e−20C,0.1% of peak).
The fine trace is linearly interpolated onto coarse times for the declared
timestep comparison; raw time-grid equality is not claimed. All four realized
W/L/DELVTO/FACTUO values remain exact across cases and points. Native dynamic
`ijs` and `cjs` availability passed; the three logs contain no warnings.
Runs completed inside30s child bounds, approximately8–9s including container
startup. No timeout escalation or large-circuit transient was used.

The instance retains W384µm/L2µm/ng64/m1/mm_ok1 and the pinned PSP/card hashes.
Its independent tiny-circuit random draw is **not** the full-population SENSE
realization. The ideal external body ramps3.3→3.0→3.3V with fixed source,
gate and drain. The result says nothing yet about a physical shared junction's
ownership, matching, actual six-device waveforms, silicon truth or complete
extrinsic PEX. Those applicability gates remain **not run / not qualified**.

Reproduce the three declared `run_junction_charge_control.py` cases, analyze
each using `analyze_junction_charge_control.py`, and run
`compare_junction_charge_steps.py`. Sources, solver settings, gate values and
model hashes are frozen in each generated contract. The earlier proposal
remains a historical not-run proposal; this separate result records execution.

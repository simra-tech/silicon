# Delivered SENSE routing and nearby fill

The delivered bare-pad-to-SENSE input routes are unequal: the nominal geometric resistance sums are **77.6671 Ω on P and 138.2311 Ω on N**, a 60.564 Ω difference. Estimated route-to-ground capacitance is 6.7227 fF versus 17.5170 fF. These are actual-route geometry plus technology-LEF estimates, **not extracted electrical RC**. Macro-internal parasitics and pad devices are separate.

The DEF endpoints explicitly connect `pad08_sense_p/padbare` and `pad09_sense_n/padbare` to the respective SENSE input. The stock AnalogPad's approximately 587 Ω secondary protection branch is **not in series with these bare-pad input paths**. The VREF connection through `padres` has a different topology. A prior conversational comparison to a series 587 Ω SENSE pad resistance was incorrect and was corrected before fixture adoption.

| Delivered net | Length (µm) | Wire-only R estimate (Ω) | Via R estimate (Ω) | Total route R sum (Ω) | Ground C estimate (fF) |
|---|---:|---:|---:|---:|---:|
| `i_core.sense_p` | 73.14 | 37.6671 | 40 | 77.6671 | 6.7227 |
| `i_core.sense_n` | 190.74 | 98.2311 | 40 | 138.2311 | 17.5170 |
| `i_core.isense` | 306.76 | 157.9814 | 40 | 197.9814 | 28.1579 |
| `i_core.vref_buf` | 246.70 | 127.0505 | 40 | 167.0505 | 22.6458 |

Each route has two single-cut Via3_XY instances; the unchanged nominal technology LEF declares 20 Ω per via. Wire resistance uses segment length divided by sampled actual GDS width and nominal sheet resistance. Ground capacitance uses the existing LEF area/edge coefficients. Geometry audit centerline coverage passed for all four nets. Width samples and segments are retained in `sense-route-geometry-20260922-r1.json`. Route sums include physical pin access/stubs; exact current-path spreading/corner resistance was not extracted.

## Nearby fill is present and asymmetric

`sense-route-nearfill-20260922-r1.json` independently queries delivered GDS datatype-22 fill in the route layer and its two neighboring metal layers. It uses route corridors at median sampled width, records projected overlap, and expands them by 1/2/5/10/20 µm to quantify proximity. Reported nearest distance is axis-aligned expansion until area overlap, not a three-dimensional dielectric distance or a DRC minimum-spacing measurement.

For the M4 sections, same-layer fill first overlaps the expanded N corridor at 0.501 µm, versus 1.501 µm for P. M3 fill projected onto those M4 corridors overlaps 16.8 µm² for N versus 3.2 µm² for P; M5 fill projection overlaps 19.472 µm² versus 3.796 µm². No same-layer zero-distance fill/route overlap was found in these selected corridors. Layer projection does not imply physical connectivity.

These differences establish that fill cannot be presumed absent or symmetric in the assembled input route. They do **not** determine coupling capacitance: floating/connected fill status and a validated electrostatic extraction are not available from this query. The nominal LEF ground-C estimate must not be relabeled as fill coupling or added twice. Actual aggressor connectivity, coupling, shielding and error remain **not run**.

## Concrete isolated fixture insertion

In the completed top fixture, preserve Rkp/Rkn and pad instances XPSP/XPSN at `sense_p`/`sense_n`. Insert route resistance between each bare-pad node and a new macro-input node; change only the first two XSENSE terminals:

```spice
Rroute_p sense_p sense_p_core 77.6671
Rroute_n sense_n sense_n_core 138.2311
Croute_p_pad sense_p 0 3.36136812f
Croute_p_core sense_p_core 0 3.36136812f
Croute_n_pad sense_n 0 8.75850252f
Croute_n_core sense_n_core 0 8.75850252f
* XSENSE sense_p_core sense_n_core <all remaining original pins unchanged>
```

This is a declared pi approximation. Scale 0/1/2 for no added RC, nominal geometry estimate, and deliberately stressed R/C is a useful diagnostic set; 2× is **not a physically qualified upper bound**. Unknown floating-fill/aggressor coupling prevents a rigorous conservative capacitance bound. A new SENSE physical candidate must repeat these audits after rerouting; this evidence applies only to the delivered baseline.

Reproduce using the pinned container and unused output names:

```sh
G1_CPUS=1 flow/run.sh python3 designs/g1-guardian/review/audits/audit_external_routes.py designs/g1-guardian/review/audits/sense-route-geometry-new.json --nets i_core.sense_p,i_core.sense_n,i_core.isense,i_core.vref_buf
G1_CPUS=1 flow/run.sh python3 designs/g1-guardian/review/audits/audit_near_fill.py --output designs/g1-guardian/review/audits/sense-route-nearfill-new.json
```

The near-fill helper consumes the retained canonical r1 route audit, with input hashes recorded. KLayout 0.30.9, unchanged delivered GDS hash `38c1d6d13bbfee4ed0e3c01477742c3d2d28317d9215d9e5bd9a35551285ae59`. No geometry, model card or rule deck changed. Electrical response to the proposed insertion is **not run in this audit**.

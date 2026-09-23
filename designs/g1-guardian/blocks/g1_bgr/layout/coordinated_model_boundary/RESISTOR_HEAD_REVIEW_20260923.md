# Resistor-head boundary and remaining external routing

The metal mesh includes native Metal1 resistor heads, **not** the contact cuts,
salicided/unsalicided poly heads or resistor body. It is therefore more than
external routing alone, but does not explicitly duplicate the specified
contact/poly-end material resistance. Exact lateral Metal1 model de-embedding
remains unestablished; no resistance or model parameter was removed.

## Pinned physical/model evidence

This is a read-only continuation of [the native terminal audit](BOUNDARY_REVIEW_20260923.md),
using PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` and the already qualified
conditional saved OPs, not new analog runs.

- `libs.doc/doc/SG13G2_os_process_spec.pdf`, SHA256
  `974d505886ee62932a50c52c22fbc290db4a70d8a7ce129c0ca8d7934aee160e`,
  Rev. 1.2 pages 10–12: Rsil/Rppd/Rhigh metal-to-body terms are 4.5/35/80,
  with Rppd/Rhigh explicitly in ohm-um and measurement condition A.ae.
- Page 24 A.ae identifies salicide-to-GatPoly contact resistance and gives
  `RRES = 2*RCONT/Ncontacts + 2*RC2POLY/W + RPOLY`. It distinguishes W-plug,
  salicide-to-GatPoly and unsalicided stripe contributions, and restricts the
  formula to equal-width salicided/unsalicided regions. It does not identify
  a lateral Metal1 cut surface or establish application to an arbitrary head.
- `resistors_mod.lib`, SHA256
  `7c77da0c0419c8a332550da3f934f530262bd452734090db827b68ff88d09c43`,
  uses `c1=c2=1`, `rc=rz`, `postsim=0`; our rhigh/rppd end terms are
  160/35 ohm per end. The Rsil wrapper has `rzspec=rqrc=4.5e-6`; the same
  `rqrc/w` appears in the disabled postsim subtraction for Rppd/Rhigh.
  This does not authorize subtracting a Metal1 mesh resistance.
- Pinned `rppd_code.py` lines 225–290 draws separate GatPoly contact areas,
  contact bars/cuts, then Metal1 and its coincident published pin rectangle.
  The prior audit proves all 798 resistor point injections are at native M1
  head centers. The positive-metal engine includes only M1–M5/Via1–Via4;
  it has no Cont, GatPoly or generic contact-resistance contribution.

## Saved nonlinear OP attribution

`audit_resistor_head_bound.py` matches every one of 42,615 positive edges to
the raw saved network, retains all edges and exact resistances, binds all
input hashes before/after, checks 55 source-net components, and reproduces
the existing OP total metal power. All edges touching M1 are placed in a
conservative bucket: it includes every resistor head, **plus** other native
M1, other M1 routing and Via1. No square-counting support polygon is inferred
from endpoint coordinates and no geometric edge is deleted.

| Conditional scenario | Total metal power | All M1-touching upper bucket | Outside M1 heads by layer |
| --- | ---: | ---: | ---: |
| KPEX resistance table | 11.8268 uW | 0.57984% | 99.42016% |
| LEF resistance table | 15.0116 uW | 0.92334% | 99.07666% |

These are simulated power fractions at the existing conditional nonlinear
OP, **not VREF sensitivities or bounds on VREF error**. They do not prove the
same fractions of the earlier 37–47 mV VREF shift. Nevertheless the dominant
metal dissipation cannot be attributed to native M1 resistor heads.

Largest outside-head power nets are VSS, VDD, pcasc, pbias, vb2 and dvbe.
The saved source-terminal voltage spreads are VDD 6.634/8.268 mV,
VSS 8.341/12.228 mV, vb2 14.580/18.600 mV, pbias 14.447/18.469 mV and
pcasc 17.843/22.274 mV (KPEX/LEF respectively). These include all saved
source-bound injection points, not merely the single edges below.
Concrete large-drop route edges, coordinates in local BGR micrometers:

| Net/layer | Endpoint centers | KPEX R | KPEX drop | LEF drop |
| --- | --- | ---: | ---: | ---: |
| vb2 / M3 | (64.95,52.46) to (355.65,52.46) | 85.184 ohm | 3.549 mV | 3.968 mV |
| pbias / M3 | (281.21,138.60) to (411.74,138.60) | 38.2888 ohm | 3.320 mV | 3.732 mV |
| pcasc / M3 | (282.21,139.20) to (412.49,139.20) | 38.2155 ohm | 3.313 mV | 3.724 mV |
| vb2 / M3 | (285.21,141.00) to (414.74,141.00) | 37.9955 ohm | 3.294 mV | 3.703 mV |
| dvbe / M5 | (203.00,137.05) to (203.00,18.67) | 34.7248 ohm | 3.015 mV | 3.389 mV |

These identify candidate conductors for clearance-checked widening/bypass,
not a proved permissible geometry change. Native/source/pins remain held;
any remedy needs actual shape inspection, DRC/LVS and a separately labelled
same-boundary electrical comparison. Higher-layer routing diagnosis need
not wait for a calibrated native M1 head plane.

| Check | Status |
| --- | --- |
| Saved-edge/source-net/hash/finite-power attribution | Passed |
| Pinned A.ae material distinction | Passed, with equal-width applicability restriction |
| Exact calibrated lateral M1 de-embedding boundary | Failed to establish |
| New analog simulation or geometric remedy | Not run |
| VREF sensitivity attribution to head/routing partition | Not run |
| Model subtraction, canonical adoption, changed source or cards | Not applicable; none performed |

The initial PDF text search found no match because the label is line-broken;
page-specific extraction subsequently established the wording above. The
container lacks `pdftotext`; host `pdftotext` read the pinned PDF stream.
Neither diagnostic altered any PDK file.

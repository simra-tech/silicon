# West VDDA extension candidate

Actual frozen merged native source SHA256
`4e034eda528d4bfa3c00accf1f619fe0569b07471b6bece6697466eb9877a87e`
and the separately checked LS overlay
`576cdf8f417a52456bdf60fe65c1f2516cab174ad0a449258b6617dbbcc3a60d`
define the screening context. All primitives, native polygons, source models,
pin annotations, existing feeds and PDN landings stay unchanged.

The first screen failed actual GATE VSS M4-stack and SENSE VSS TM2-flyover
intersections. No candidate GDS was saved. The failed report and source remain
preserved. The second proposed geometry routes GATE's new M4 bridge at y603
instead of600. LS and GATE join a2.2 µm TM2 west rail at x783. The rail changes
to2.2 µm TM1 between y712.5 and731.5, crossing below the existing SENSE VSS
TM2 flyover without any cut at the crossing. It returns to TM2 at y731.5,
then turns at x814 to join the shared same-VDDA routing at y726.

Prospective targets are0.3 mA total LS and2 mA GATE,2.3 mA west-branch
aggregate. These are exploratory geometry assumptions, not qualified operating
bounds. The shared pad target remains10 mA total, not10 mA per branch.
SENSE's narrow M3 leaf is not the series aggregate path. All46 new cut-loss
cases, saved flat native/domain preservation, stock checks and actual final
signal-route context are required. Native internal contact/current distribution,
temperature, PVT, complete field PEX, IR/EM and adoption remain not run.

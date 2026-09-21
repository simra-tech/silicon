# Test: does the PDK filler honour <layer>/23 no-fill shapes placed at chip level?
# Take the previous dry run's pre-fill GDS (after sealring), add no-fill rectangles
# on all fill-relevant layers over the g1_sense macro footprint, run filler.py,
# and count fill shapes (datatype 22) inside vs outside that rectangle.
import pya, sys
src, dst = globals()["src"], globals()["dst"]
ly = pya.Layout(); ly.read(src)
top = ly.cell("g1_chip_top")
# g1_sense at (733,440)-(985.16,629.25) um
box = pya.Box(733000, 440000, 985160, 629250)
for l in (1, 5, 8, 10, 30, 50, 67, 126, 134):
    li = ly.layer(l, 23)
    top.shapes(li).insert(box)
ly.write(dst)
print("no-fill rectangles added on", [f"{l}/23" for l in (1,5,8,10,30,50,67,126,134)], "over", box.to_s())

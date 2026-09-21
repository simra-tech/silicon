# fill_g1_bgr.sh step 1 (KLayout batch): prepare the unfilled macro GDS for the PDK filler.
#   klayout -b -r fill_pre.py -rd src=<unfilled gds> -rd dst=<prefill gds>
# The PDK fill macros fill only inside EdgeSeal.holes (layer 39/0), so a temporary EdgeSeal ring is drawn around the
# macro whose hole is the macro area inset by FILL_INSET; Metal4 and Metal5 get a temporary no-fill rectangle over the
# whole macro (the macro carries no Metal4/5 and the chip-level filler fills those layers over it after routing).
# fill_post.py removes both again.
import pya
FILL_INSET = 1.0     # um: block fill stays this far inside the macro boundary
src, dst = globals()['src'], globals()['dst']
ly = pya.Layout()
ly.read(src)
top = ly.top_cell()
bb = top.bbox()
dbu = ly.dbu
inset = int(round(FILL_INSET / dbu))
ring = pya.Polygon(bb.enlarged(int(round(5.0 / dbu)), int(round(5.0 / dbu))))
ring.insert_hole(bb.enlarged(-inset, -inset))
top.shapes(ly.layer(39, 0)).insert(ring)
for lay in ((50, 23), (67, 23)):
    top.shapes(ly.layer(*lay)).insert(bb)
ly.write(dst)
print('fill_pre: %s -> %s, fill window %s um' % (src, dst, bb.enlarged(-inset, -inset).to_dtype(dbu)))

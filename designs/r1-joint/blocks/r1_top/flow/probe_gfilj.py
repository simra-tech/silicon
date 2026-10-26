# Debug GFil.j marks: which GatPoly filler shapes sit at the marks. klayout -b -r probe_gfilj.py -rd g=<gds>
import pya
ly=pya.Layout(); ly.read(g); top=ly.cell('r1_top'); dbu=ly.dbu
li_a,li_p=ly.layer(1,22),ly.layer(5,22)
act=pya.Region(top.begin_shapes_rec(li_a)); poly=pya.Region(top.begin_shapes_rec(li_p))
m=act.enclosed_check(poly,180)
print('marks',m.count())
n=0
for ep in m.each():
    print(ep.to_s(), 'dist', ep.distance())
    n+=1
    if n>=4: break
tp=pya.Region(top.shapes(li_p)); print('top-cell direct 5/22 shapes',tp.count())
for inst in top.each_inst():
    pass
ep=next(m.each()); bx=pya.Region(ep.bbox().enlarged(500))
print('poly near first mark (hier):',(poly&bx).count(),' top direct:',(tp&bx).count())
cells=set()
it=top.begin_shapes_rec_touching(li_p,ep.bbox().enlarged(500)); 
for i in it: cells.add(i.cell().name)
print(cells)

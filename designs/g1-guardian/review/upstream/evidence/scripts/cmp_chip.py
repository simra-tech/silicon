import pya, json
c=pya.Layout(); c.read("/work/designs/g1-guardian/blocks/g1_padring/layout/g1_chip_top_1414.gds")
d=pya.Layout(); d.read("io_dev_4fd47c5e.gds")
o=pya.Layout(); o.read("io_8437402.gds")
def li(l,a,b):
  i=l.find_layer(a,b); return i
res={}
# cells in chip that carry direct 128/0 shapes
pr=li(c,128,0)
cells=[x for x in c.each_cell() if pr is not None and not x.shapes(pr).is_empty()]
res["chip_cells_with_direct_128_0"]={x.name:[x.shapes(pr).size(), pya.Region(x.shapes(pr)).area()*1e-6] for x in cells}
# match each against upstream-dev cells of same geometry: compare all layers of chip cell vs candidate stock cells
def allreg(l,cell):
  m={}
  for i in l.layer_indexes():
    info=l.get_info(i); r=pya.Region(cell.shapes(i))
    if not r.is_empty(): m[(info.layer,info.datatype)]=r
  return m
out={}
for x in cells:
  mc=allreg(c,x); best=None
  for stock in ["sg13g2_SecondaryProtection","sg13g2_RCClampResistor"]:
    for tag,l in (("dev",d),("pinned",o)):
      ms=allreg(l,l.cell(stock)); diff={}
      for k in set(mc)|set(ms):
        r=(mc.get(k,pya.Region())^ms.get(k,pya.Region()))
        if not r.is_empty(): diff[f"{k[0]}/{k[1]}"]=[r.count(),round(r.area()*1e-6,4)]
      out.setdefault(x.name,{})[f"{stock}@{tag}"]=diff or "identical"
res["direct_xor_vs_stock"]=out
# which parents instantiate them
res["parents"]={x.name:sorted({c.cell(p).name for p in x.each_parent_cell()}) for x in cells}
print(json.dumps(res,indent=1)); open("chip_vs_dev.json","w").write(json.dumps(res,indent=1))

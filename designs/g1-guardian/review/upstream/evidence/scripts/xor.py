import pya, json
a=pya.Layout(); a.read("io_8437402.gds")
b=pya.Layout(); b.read("io_dev_4fd47c5e.gds")
out={"dbu":[a.dbu,b.dbu]}
na={c.name for c in a.each_cell()}; nb={c.name for c in b.each_cell()}
out["only_old"]=sorted(na-nb); out["only_new"]=sorted(nb-na)
def lmap(l): return {(i.layer,i.datatype):li for li,i in ((li,l.get_info(li)) for li in l.layer_indexes())}
la,lb=lmap(a),lmap(b)
# per-cell direct-shape + instance comparison
changed={}
for n in sorted(na&nb):
  ca=a.cell(n); cb=b.cell(n); diffs=[]
  for k in sorted(set(la)|set(lb)):
    ra=pya.Region(ca.shapes(la[k])) if k in la else pya.Region()
    rb=pya.Region(cb.shapes(lb[k])) if k in lb else pya.Region()
    x=ra^rb
    if not x.is_empty(): diffs.append([f"{k[0]}/{k[1]}",x.count(),x.area()*a.dbu*a.dbu])
    ta=sorted(s.text.to_s() for s in ca.shapes(la[k]).each() if s.is_text()) if k in la else []
    tb=sorted(s.text.to_s() for s in cb.shapes(lb[k]).each() if s.is_text()) if k in lb else []
    if ta!=tb: diffs.append([f"{k[0]}/{k[1]} text",len(ta),len(tb)])
  ia=sorted((a.cell(i.cell_index).name,i.trans.to_s(),i.size()) for i in ca.each_inst())
  ib=sorted((b.cell(i.cell_index).name,i.trans.to_s(),i.size()) for i in cb.each_inst())
  if ia!=ib: diffs.append(["instances",len(ia),len(ib)])
  if diffs: changed[n]=diffs
out["changed_cells_direct"]=changed
# flat XOR for requested top cells
flat={}
for n in ["sg13g2_IOPadAnalog","sg13g2_IOPadIn","sg13g2_IOPadOut30mA","sg13g2_IOPadVdd","sg13g2_IOPadIOVdd","sg13g2_IOPadVss","sg13g2_IOPadIOVss","sg13g2_Filler200","sg13g2_SecondaryProtection","sg13g2_RCClampResistor","sg13g2_Corner"]:
  if n not in na or n not in nb: flat[n]="missing"; continue
  r={}
  for k in sorted(set(la)|set(lb)):
    ra=pya.Region(a.cell(n).begin_shapes_rec(la[k])) if k in la else pya.Region()
    rb=pya.Region(b.cell(n).begin_shapes_rec(lb[k])) if k in lb else pya.Region()
    x=ra^rb
    if not x.is_empty(): r[f"{k[0]}/{k[1]}"]=[x.count(),round(x.area()*a.dbu*a.dbu,4)]
  flat[n]=r or "identical"
out["flat_xor"]=flat
print(json.dumps(out,indent=1))
open("xor_result.json","w").write(json.dumps(out,indent=1))

# KLayout batch script: prove that two GDS files hold the same geometry, cell by cell.
# The top cell may carry a different name (a=oldtop, b=newtop); every other cell must match by name.
# Compares, per cell and per layer/datatype, the sorted list of shapes (boxes, polygons, paths, texts
# with properties), and the sorted list of instances (target cell name, transformation, array).
# Usage: klayout -b -r compare_gds.py -rd a=<ref.gds> -rd b=<new.gds> -rd oldtop=<n> -rd newtop=<n> -rd out=<json>
import json, hashlib, pya

def load(p):
    ly = pya.Layout(); ly.read(p); return ly

def cell_sig(ly, c, rename):
    lay = {}
    for li in ly.layer_indexes():
        sh = c.shapes(li)
        if sh.is_empty(): continue
        info = ly.get_info(li)
        items = sorted("%s|%s" % (s.to_s(), s.property_values() if hasattr(s, "property_values") else s.prop_id) for s in sh.each())
        lay["%d/%d" % (info.layer, info.datatype)] = (len(items), hashlib.sha256("\n".join(items).encode()).hexdigest())
    insts = sorted("%s|%s|%s" % (rename(ly.cell(i.cell_index).name), i.cplx_trans.to_s(), (i.a.to_s(), i.b.to_s(), i.na, i.nb) if i.is_regular_array() else "") for i in c.each_inst())
    return lay, (len(insts), hashlib.sha256("\n".join(insts).encode()).hexdigest())

A = load(a); B = load(b)
ra = lambda n: newtop if n == oldtop else n
rb = lambda n: n
res = {"a_cells": A.cells(), "b_cells": B.cells(), "dbu_a": A.dbu, "dbu_b": B.dbu,
       "a_tops": [c.name for c in A.top_cells()], "b_tops": [c.name for c in B.top_cells()],
       "a_bbox_um": A.top_cells()[0].dbbox().to_s(), "b_bbox_um": B.top_cells()[0].dbbox().to_s()}
names_a = sorted(ra(c.name) for c in A.each_cell()); names_b = sorted(c.name for c in B.each_cell())
res["cell_names_equal_modulo_top_rename"] = names_a == names_b
diff_cells = []; n_layers = 0; n_shapes = 0; n_insts = 0
for c in A.each_cell():
    nb = ra(c.name)
    cb = B.cell(nb) if B.has_cell(nb) else None
    if cb is None: diff_cells.append(nb + ":missing"); continue
    la, ia = cell_sig(A, c, ra); lb, ib = cell_sig(B, cb, rb)
    if la != lb or ia != ib: diff_cells.append(nb)
    n_layers += len(la); n_shapes += sum(v[0] for v in la.values()); n_insts += ia[0]
res["cells_compared"] = A.cells(); res["cell_layer_pairs_compared"] = n_layers
res["shapes_compared"] = n_shapes; res["instances_compared"] = n_insts
res["differing_cells"] = diff_cells
res["identical_geometry"] = res["cell_names_equal_modulo_top_rename"] and not diff_cells and A.dbu == B.dbu
open(out, "w").write(json.dumps(res, indent=1) + "\n")
print(json.dumps(res, indent=1))

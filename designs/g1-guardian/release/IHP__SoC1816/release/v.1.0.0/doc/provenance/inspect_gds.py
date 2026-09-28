# KLayout batch script: read-only inspection of a GDS for the IHP Open-Silicon-MPW checklist.
# Usage: klayout -b -r inspect_gds.py -rd gds=<file> -rd out=<json> [-rd newtop=<name>]
import json, pya

ZERO_LAYERS = [(1,0),(5,0),(6,0),(7,0),(8,0),(9,0),(10,0),(14,0),(19,0),(20,0),(27,0),(29,0),(30,0),(31,0),(32,0),(36,0),(44,0),(49,0),(50,0),(66,0),(67,0),(72,0),(73,0),(74,0),(75,0),(77,0),(83,0),(84,0),(125,0),(126,0),(128,0),(129,0),(132,0),(133,0),(134,0),(146,0)]

ly = pya.Layout()
ly.read(gds)
res = {"file": gds.split("/")[-1]}
tops = [c.name for c in ly.top_cells()]
res["top_cells"] = tops
top = ly.top_cells()[0]
b = top.dbbox()
res["dbu_um"] = ly.dbu
res["bbox_um"] = [b.left, b.bottom, b.right, b.top]
res["cell_count"] = ly.cells()
res["layer_count"] = len([li for li in ly.layer_indexes() if not all(ly.cell(ci).shapes(li).is_empty() for ci in range(ly.cells()))])
res["libname"] = ly.meta_info_value("libname") if hasattr(ly, "meta_info_value") else None
res["layout_properties"] = str(ly.prop_id) if hasattr(ly, "prop_id") else None
res["has_pcell_or_lib_context"] = any(c.is_pcell_variant() or c.is_library_cell() for c in ly.each_cell())
if "newtop" in globals():
    res["name_collision_" + newtop] = ly.has_cell(newtop)
zl_paths = 0; npaths = 0; max_pts = 0; big_polys = 0; zero_area = {}; props = 0
layer_info = {li: (ly.get_info(li).layer, ly.get_info(li).datatype) for li in ly.layer_indexes()}
for c in ly.each_cell():
    for li in ly.layer_indexes():
        for s in c.shapes(li).each():
            if s.prop_id != 0: props += 1
            if s.is_path():
                npaths += 1
                p = s.path
                if p.num_points() < 2 or p.length() == 0: zl_paths += 1
            if s.is_polygon() or s.is_simple_polygon():
                n = s.polygon.num_points() if s.is_polygon() else s.simple_polygon.num_points()
                max_pts = max(max_pts, n)
                if n > 8000: big_polys += 1
            if layer_info[li] in ZERO_LAYERS:
                z = False
                if s.is_box(): z = s.box.width() == 0 or s.box.height() == 0
                elif s.is_path(): z = s.path.width == 0 or s.path.polygon().area() == 0
                elif s.is_polygon(): z = s.polygon.area() == 0
                elif s.is_simple_polygon(): z = s.simple_polygon.area() == 0
                if z:
                    k = "%d/%d" % layer_info[li]; zero_area[k] = zero_area.get(k, 0) + 1
    for inst in c.each_inst():
        if inst.prop_id != 0: props += 1
res["paths"] = npaths
res["zero_length_paths"] = zl_paths
res["max_polygon_points"] = max_pts
res["polygons_over_8000_points"] = big_polys
res["zero_area_shapes_on_ihp_zero_py_layers"] = zero_area
res["shapes_or_instances_with_properties"] = props
res["texts_63_0_top"] = [s.text.string for s in top.shapes(ly.layer(63,0)).each() if s.is_text()]
open(out, "w").write(json.dumps(res, indent=1) + "\n")
print(json.dumps(res, indent=1))

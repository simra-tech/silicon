# Build the R1 pad ring (empty core) from the G1 r4 ring cells.
#   klayout -b -r flow/build_ring.py -rd src=<g1 r4 gds> -rd out=<ring gds> -rd report=<json>
# What is taken from G1 r4 (SHA-256 225d0b53...): the design-local IO cell copies (PolyRes 128/0),
# corners, IO fillers, bondpad cell, the 5 um outward bondpad bridge (cell bondpad_outward_5um_retained_metal),
# the 24 TopMetal2 pad squares/pins/labels (cell new_signal_routes, filtered to the pad zone), the seal ring and
# the registration texts (top cell), and the core power ring (TM1/TM2). Everything else (macros, standard cells,
# core routing, VDDA grid, old fill) is dropped. The IO cell type of each slot follows the R1 pin map.
import pya, json, hashlib, sys
DBU = 0.001
ly = pya.Layout(); ly.read(src)
T = ly.top_cell()
assert abs(ly.dbu - DBU) < 1e-12

PINS = [  # pad, net label, IO cell type, G1 cell suffix
 (1,'VDD','Vdd'),(2,'VSS','Vss'),(3,'IOVDD','IOVdd'),(4,'IOVSS','IOVss'),(5,'VSS','Vss'),(6,'IOVSS','IOVss'),
 (7,'VDDA','Analog'),(8,'ISA_P','Analog'),(9,'ISA_N','Analog'),(10,'ISB_P','Analog'),(11,'ISB_N','Analog'),
 (12,'FAULT_N','Out4mA'),(13,'GATE_A','Out30mA'),(14,'GATE_B','Out30mA'),(15,'GATE_C','Out30mA'),
 (16,'CS_N','In'),(17,'MA_SCLK','In'),(18,'SLO_SDO','Out4mA'),(19,'SDI','In'),(20,'EN_STO_IN','In'),
 (21,'SIN_P','Analog'),(22,'SIN_N','Analog'),(23,'COS_P','Analog'),(24,'COS_N','Analog')]
PREFIX = 'retained_fullchip_sg13g2_IOPad'
def slot(tr):
    x, y = tr.disp.x, tr.disp.y
    if y == 141000 and 355000 <= x <= 915000: return 1 + (x-355000)//112000
    if x == 1273000 and 355000 <= y <= 915000: return 7 + (y-355000)//112000
    if y == 1273000 and 355000 <= x <= 915000: return 13 + (x-355000)//112000
    if x == 141000 and 355000 <= y <= 915000: return 19 + (y-355000)//112000
    return None
cell_by_name = {c.name: c for c in ly.each_cell()}
want = {p[0]: p for p in PINS}
rep = {'src': src, 'removed_insts': {}, 'kept_insts': {}, 'slots': {}}
newinsts = []
for inst in list(T.each_inst()):
    n = inst.cell.name
    if n.startswith(PREFIX):
        s = slot(inst.trans)
        assert s is not None, (n, inst.trans.to_s())
        tgt = cell_by_name[PREFIX + want[s][2]]
        newinsts.append((s, pya.CellInstArray(tgt.cell_index(), inst.trans), n))
        inst.delete()
    elif n.startswith('retained_fullchip_sg13g2_Corner') or n.startswith('retained_fullchip_sg13g2_Filler') \
         or n.startswith('retained_fullchip_bondpad') or n in ('new_signal_routes', 'bondpad_outward_5um_retained_metal'):
        rep['kept_insts'][n] = rep['kept_insts'].get(n, 0) + 1
    else:
        rep['removed_insts'][n] = rep['removed_insts'].get(n, 0) + 1
        inst.delete()
for s, arr, old in newinsts:
    T.insert(arr)
    rep['slots'][s] = {'net': want[s][1], 'cell': PREFIX + want[s][2], 'g1_cell': old}
assert len(newinsts) == 24 and sorted(rep['slots']) == list(range(1, 25))

# --- top direct shapes: keep seal ring, registration texts, core ring (+ its vias), drop the rest
L = lambda l, d: ly.layer(l, d)
um = lambda v: int(round(v / DBU))
TM1R = [(324.82,321,339.82,1093),(344.82,321,361.8,1093),(1054.42,321,1069.42,1093),(1074.42,321,1089.42,1093),
        (1054.42,347.16,1069.42,1066.3),(344.82,347.16,359.82,1066.3),(1074.42,327.16,1089.42,1086.3),(324.82,327.16,339.82,1086.3)]
TM2R = [(344.82,1051.3,1069.42,1066.3),(344.82,347.16,1069.42,362.16),(328,1071.3,1086,1086.3),(328,327.16,1086,342.16)]
rbox = lambda t: pya.Box(um(t[0]), um(t[1]), um(t[2]), um(t[3]))
tm1 = pya.Region([rbox(t) for t in TM1R]).merged(); tm2 = pya.Region([rbox(t) for t in TM2R]).merged()
tm12 = tm1 & tm2
kept = {}; dropped = {}
for li in list(ly.layer_indexes()):
    info = ly.get_info(li); key = '%d/%d' % (info.layer, info.datatype)
    sh = T.shapes(li)
    for s in list(sh.each()):
        if s.is_text():
            if key == '63/0': kept[key] = kept.get(key, 0) + 1; continue
            sh.erase(s); dropped[key+'t'] = dropped.get(key+'t', 0) + 1; continue
        b = s.bbox(); keep = False
        if b.width() >= um(1300) and b.height() >= um(1300): keep = True          # seal ring, one shape per layer
        elif key == '126/0': keep = any(rbox(t) == b for t in TM1R)
        elif key == '134/0': keep = any(rbox(t) == b for t in TM2R)
        elif key == '133/0': keep = (pya.Region(b) - tm12).is_empty()
        elif key == '125/0': keep = False   # TopVia1 of the ring: G1 strapped the ring down to Metal5; not in the empty core
        if keep: kept[key] = kept.get(key, 0) + 1
        else: sh.erase(s); dropped[key] = dropped.get(key, 0) + 1
rep['top_kept'] = kept; rep['top_dropped'] = dropped

# --- pad labels in top: one label per net (first pad of a duplicated net), as in G1 r4
core = pya.Box(um(321), um(321), um(1093), um(1093))
pad_xy = lambda n: ({1:(0,0)}, None)
def centre(n):
    i = (n-1) % 6
    if n <= 6: return (395+112*i, 101)
    if n <= 12: return (1313, 395+112*i)
    if n <= 18: return (395+112*i, 1313)
    return (101, 395+112*i)
seen = set(); lbl = T.shapes(L(134, 25))
for n, net, _ in PINS:
    if net in seen: continue
    seen.add(net); x, y = centre(n)
    lbl.insert(pya.Text(net, pya.Trans(um(x), um(y))))
rep['top_labels'] = len(seen)

# --- new_signal_routes: keep pad-zone TopMetal2 square/pin/label and the prBoundary
nsr = cell_by_name['new_signal_routes']
nk = {}; nd = {}
for li in list(ly.layer_indexes()):
    info = ly.get_info(li); key = '%d/%d' % (info.layer, info.datatype)
    sh = nsr.shapes(li)
    for s in list(sh.each()):
        if s.is_text():
            sh.erase(s); continue                      # labels re-inserted below
        b = s.bbox()
        keep = (key in ('134/0', '134/2') and not b.overlaps(core)) or key == '189/4'
        if keep: nk[key] = nk.get(key, 0) + 1
        else: sh.erase(s); nd[key] = nd.get(key, 0) + 1
for n, net, _ in PINS:
    x, y = centre(n); nsr.shapes(L(134, 25)).insert(pya.Text(net, pya.Trans(um(x), um(y))))
# instances inside new_signal_routes (vias of the dropped routes) are removed
ninst = 0
for inst in list(nsr.each_inst()): inst.delete(); ninst += 1
rep['nsr_kept'] = nk; rep['nsr_dropped'] = nd; rep['nsr_insts_deleted'] = ninst

# --- prune orphan cells
for _ in range(20):
    orphans = [c for c in ly.each_cell() if c.cell_index() != T.cell_index() and c.parent_cells() == 0]
    if not orphans: break
    for c in orphans: ly.delete_cell(c.cell_index())
T.name = 'r1_padring'
rep['cells'] = ly.cells(); rep['top'] = T.name; rep['bbox_um'] = [T.bbox().p1.x*DBU, T.bbox().p1.y*DBU, T.bbox().p2.x*DBU, T.bbox().p2.y*DBU]
opt = pya.SaveLayoutOptions(); opt.format = 'GDS2'; opt.gds2_write_timestamps = False; opt.gds2_write_cell_properties = False
ly.write(out, opt)
rep['out'] = out; rep['out_sha256'] = hashlib.sha256(open(out, 'rb').read()).hexdigest()
json.dump(rep, open(report, 'w'), indent=1, sort_keys=True, default=str)
print(json.dumps({k: rep[k] for k in ('top_kept','top_dropped','nsr_kept','nsr_dropped','removed_insts','kept_insts','cells','out_sha256','bbox_um')}, indent=1, default=str))

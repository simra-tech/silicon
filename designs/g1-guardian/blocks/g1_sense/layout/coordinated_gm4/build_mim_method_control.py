#!/usr/bin/env python3
"""One exact native seven-micron MIM method coupon; no design mutation."""
import argparse
import json
import os
from pathlib import Path
from build_native_prototypes import lib, pya, snapshot, sha
from export_sense_kpex_api import materialize


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert os.sched_getaffinity(0) == {7} and pya.__version__ == '0.30.9'
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output/'builder_snapshot.py').write_bytes(Path(__file__).read_bytes())
    ly = pya.Layout()
    ly.dbu = .001
    cell = ly.create_cell('sense_mim_method_control')
    draw = lib.Draw(ly, cell)
    draw.pcell('cmim', dict(Calculate='C', w='7u', l='7u'), 5., 5.)
    initial = {ly.get_info(index).to_s(): materialize(pya.Region(cell.begin_shapes_rec(index))) for index in ly.layer_indexes()}
    assert snapshot(cell,36).area() == 49_000_000
    for layer, label in ((67,'bottom'), (126,'top')):
        point = pya.Point(6000,6000)
        assert not materialize(snapshot(cell,layer) & pya.Region(pya.Box(5999,5999,6001,6001))).is_empty()
        cell.shapes(ly.layer(layer,25)).insert(pya.Text(label,pya.Trans(point)))
    gds = args.output/'sense_mim_method_control.gds'
    ly.write(str(gds))
    saved = pya.Layout()
    saved.read(str(gds))
    restored = saved.cell(cell.name)
    for index in saved.layer_indexes():
        info = saved.get_info(index)
        if info.datatype in (2,25):
            continue
        assert materialize(initial.get(info.to_s(),pya.Region()) ^ materialize(pya.Region(restored.begin_shapes_rec(index)))).is_empty()
    cdl = args.output/'sense_mim_method_control.cdl'
    cdl.write_text('* Native PCell method-control declaration; not extracted golden\n.subckt sense_mim_method_control top bottom\nC1 top bottom cap_cmim w=7u l=7u m=1\n.ends sense_mim_method_control\n')
    result = dict(status='passed native coupon geometry preparation', GDS_sha256=sha(gds), CDL_sha256=sha(cdl),
                  script_sha256=sha(Path(__file__)), native_MIM_area_um2=49., native_polygon_XOR_um2=0.,
                  declared_W_L_um=[7.,7.], PEX='not run', production_mutation=False,
                  scope='Method coverage only; no SENSE adoption, model/deck edits or intrinsic capacitance fitting')
    (args.output/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()

"""Lease-required standalone preparation/readback; no DRC/LVS execution here."""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from soft_inputpair4_folded_native_r1 import ROOT, GENERATOR, build_standalone

SOURCE=ROOT/'designs/g1-guardian/blocks/g1_trip/sim/qualification/joint586-softinputpair4-r100-roomcal-s73133-20260924-r3/trip.spice'
SOURCE_SHA='ceda15f71151cb79907137f496a8f256bef97a612ad1cfa3a6f86cf6faebb655'
TOP='g1_cmp_soft_inputpair4_folded_r1'
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def cdl(source):
    sys.path.insert(0,str(GENERATOR.parent))
    from lvs_netlist import convert
    block,=re.findall(r'(?ms)^\.subckt g1_cmp inp inn clk q qb vdd vss\n.*?^\.ends\n',source)
    for name in ['XM1','XM2']:
        line,=re.findall(r'(?m)^'+name+r' .+$',block)
        assert 'w=24u l=0.68u ng=1 m=1 mm_ok=1' in line
    changed=block.replace('.subckt g1_cmp ','.subckt '+TOP+' ')
    result='\n'.join(convert(changed.splitlines(True)))+'\n'
    assert result.count('w=24u l=0.68u m=1')==2
    assert result.splitlines()[0]=='.subckt '+TOP+' inp inn clk q qb vdd vss'
    return result


def main():
    import pya
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);args=ap.parse_args()
    assert sha(SOURCE)==SOURCE_SHA
    out=Path(args.output);assert out.is_absolute() and not out.exists()
    report=build_standalone(out)
    (out/'standalone.cdl').write_text(cdl(SOURCE.read_text()))
    a=pya.Layout();a.read(str(out/'standalone.gds'));top=a.top_cell()
    assert top.name==TOP and len(list(a.top_cells()))==1
    expected={'inp','inn','clk','q','qb','vdd','vss'}
    labels={s.text.string for i in a.layer_indexes() for s in top.shapes(i).each() if s.is_text()}
    assert expected.issubset(labels),(expected-labels)
    top.write(str(out/'readback.gds'))
    b=pya.Layout();b.read(str(out/'readback.gds'));other=b.top_cell()
    assert top.bbox()==other.bbox()
    for i in a.layer_indexes():
        j=b.find_layer(a.get_info(i));assert j is not None
        assert (pya.Region(top.begin_shapes_rec(i))^pya.Region(other.begin_shapes_rec(j))).is_empty()
        assert sorted(s.text.to_s() for s in top.shapes(i).each() if s.is_text())==sorted(s.text.to_s() for s in other.shapes(j).each() if s.is_text())
    report.update(source_sha256=SOURCE_SHA,cdl_sha256=sha(out/'standalone.cdl'),
                  readback_shapes_texts_exact=True,readback_sha256=sha(out/'readback.gds'),
                  source_converter_sha256=sha(GENERATOR.parent/'lvs_netlist.py'),
                  preparation_status='passed standalone generation/source/readback; stock DRC/LVS not run')
    (out/'readback.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))


if __name__=='__main__': main()

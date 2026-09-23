#!/usr/bin/env python3
"""Audit a saved native R extraction request without changing its technology."""
import argparse,hashlib,importlib.metadata,json,os
from pathlib import Path
from google.protobuf.json_format import MessageToDict
import klayout.db as kdb
from klayout_pex.env import Env
from klayout_pex.kpex_cli import KpexCLI
from klayout_pex.tech_info import TechInfo
from klayout_pex.klayout.lvsdb_extractor import KLayoutExtractionContext
from klayout_pex.rcx25.r.r_extractor import RExtractor,pb_RExtractorTech

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def dangling(conductors,vias):
    assert len(conductors)==len(set(conductors))
    return [dict(via=v,endpoint=end,conductor=c) for v,ends in vias for end,c in ends if c not in conductors]

def controls():
    assert dangling([1,2],[(3,[('bottom',1),('top',2)])])==[]
    assert dangling([1],[(3,[('bottom',1),('top',27)])])==[dict(via=3,endpoint='top',conductor=27)]
    try:dangling([1,1],[])
    except AssertionError:pass
    else:raise AssertionError('duplicate conductor IDs escaped')

def main():
    p=argparse.ArgumentParser()
    for key in ['view','reference','source','output']:p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();assert os.sched_getaffinity(0)=={6} and not a.output.exists()
    assert kdb.__version__=='0.30.9' and importlib.metadata.version('klayout-pex')=='0.3.12'
    assert sha(a.source)=='bb933fdabf3fd8a5117bf47f33cd40657caf78ef424e6a9bfddda0f11190d782'
    old=a.output.parent/'sense-rz100-full-r-probe-20260923-r1'
    dbpath=old/'engine/g1_sense_pex_view__g1_sense_physical/g1_sense_physical.lvsdb.gz'
    assert sha(dbpath)=='b7fecbfb03453bba2dc8cf687eef50f4be07b2f8e75062089ce15852c26dc214'
    previous=json.loads((old/'summary.json').read_text())
    assert previous['inputs_tools_cards_unchanged'] and previous['error']=='KeyError(27)'
    controls()
    # KpexCLI.validate_args creates the output ancestors itself. Reserve the
    # unique diagnostic directory before calling it, not afterwards.
    a.output.mkdir(parents=True)
    (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    args=KpexCLI.parse_args(['--pdk','ihp-sg13g2','--threads','1','--2.5D','--mode','R',
        '--blackbox','false','--gds',str(a.view/'g1_sense_pex_view.gds'),'--cell','g1_sense_physical',
        '--schematic',str(a.reference/'g1_sense_physical.cdl'),'--out_dir',str(a.output/'unused-engine')],Env.from_os_environ())
    KpexCLI.validate_args(args)
    techpath=Path(args.tech_pbjson_path);assert sha(techpath)==previous['technology_sha256']=='6ece2ac73930696f77b257d14fcf9d29d9e02451e7df99c72239746c18369a92'
    tech=TechInfo.from_json(str(techpath),dielectric_filter=args.dielectric_filter)
    db=kdb.LayoutVsSchematic();db.read(str(dbpath))
    context=KLayoutExtractionContext.prepare_extraction(db,'g1_sense_physical',tech,False)
    extractor=RExtractor(pex_context=context,
        substrate_algorithm=pb_RExtractorTech.Algorithm.ALGORITHM_SQUARE_COUNTING,
        wire_algorithm=pb_RExtractorTech.Algorithm.ALGORITHM_SQUARE_COUNTING,
        delaunay_b=.5,delaunay_amax=0,via_merge_distance=0,skip_simplify=True)
    request=extractor.prepare_request()
    conductors=[c.layer.id for c in request.tech.conductors]
    vias=[(v.layer.id,[('bottom',v.bottom_conductor.id),('top',v.top_conductor.id)]) for v in request.tech.vias]
    missing=dangling(conductors,vias)
    payload=request.SerializeToString(deterministic=True)
    (a.output/'request.pb').write_bytes(payload)
    restored=type(request)();restored.ParseFromString(payload);assert restored==request
    (a.output/'request_technology.json').write_text(json.dumps(MessageToDict(request.tech,preserving_proto_field_name=True),indent=2)+'\n')
    (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    result=dict(status='completed native request-schema diagnostic',controls='passed',
        saved_LVSDB_sha256=sha(dbpath),technology_sha256=sha(techpath),
        request_sha256=sha(a.output/'request.pb'),protobuf_roundtrip_exact=True,
        conductor_count=len(conductors),via_count=len(vias),dangling_conductor_references=missing,
        request_schema='failed' if missing else 'passed',
        TODO_technology_lines=[dict(line=i+1,text=t.strip()) for i,t in enumerate(techpath.read_text().splitlines()) if '<TODO>' in t],
        numerical_resistance_extraction='not run',full_PEX='not qualified',
        source_geometry_technology_changes='none')
    assert sha(dbpath)==previous.get('saved_LVSDB_sha256', 'b7fecbfb03453bba2dc8cf687eef50f4be07b2f8e75062089ce15852c26dc214')
    assert sha(techpath)==previous['technology_sha256']
    (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))

if __name__=='__main__':main()

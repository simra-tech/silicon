#!/usr/bin/env python3
"""Exact three-segment M3 dogleg repair; no rerouting or stock-DRC waiver."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import time
from check_closed_macro_odb import sha,quote
from check_fullchip_def_odb import observation,OPENROAD

STATUS='passed exact three-segment g_shared_bare spacing repair; stock checks not run'
OLD=(
 '      NEW Metal3 ( 404160 359940 ) ( * 360360 )\n',
 '      NEW Metal3 ( 404160 360360 ) ( 415680 * )\n',
 '      NEW Metal3 ( 415680 359940 ) ( * 360360 )\n')
NEW=tuple(s.replace('360360','360480') for s in OLD)
NET_HEADER='    - g_shared_bare ( pad19_g_shared padbare ) ( i_core.u_dose G_SHARED ) + USE SIGNAL\n'
SERIALIZED_HEADER='    - g_shared_bare ( i_core.u_dose G_SHARED ) ( pad19_g_shared padbare ) + USE SIGNAL\n'


def wire_only_patch(original,block):
    assert block.startswith(NET_HEADER) and block.count(NET_HEADER)==1
    wire=block.replace(NET_HEADER,'    - g_shared_bare + USE SIGNAL\n',1)
    return '\n'.join(original.splitlines()[:5])+'\nNETS 1 ;\n'+wire+'END NETS\nEND DESIGN\n'


def expected_serialization(original):
    changed,_=transform(original)
    assert changed.count(NET_HEADER)==1 and SERIALIZED_HEADER not in changed
    # The pinned FLOORPLAN reader reverses this net's iteration order even
    # with no connection statements. Only this exact two-pin permutation is
    # permitted; sorted complete terminal observations must also match.
    return changed.replace(NET_HEADER,SERIALIZED_HEADER,1)


def transform(text):
    match=re.search(r'^    - g_shared_bare \(.*?;\n',text,re.M|re.S)
    assert match and text.count('    - g_shared_bare (')==1
    block=match.group();changed=block
    for old,new in zip(OLD,NEW):
        assert text.count(old)==block.count(old)==1 and new not in text
        changed=changed.replace(old,new)
    result=text[:match.start()]+changed+text[match.end():]
    inverse=result
    for old,new in zip(OLD,NEW):inverse=inverse.replace(new,old)
    assert inverse==text
    assert 'UNITS DISTANCE MICRONS 1000 ;\n' in text
    return result,changed


def validate_patch(folder):
    meta=json.loads((folder/'analysis.json').read_text())
    assert meta['status']==STATUS and meta['exact_DEF_delta']=='passed'
    assert meta['instances_and_terminal_connectivity_held']=='passed'
    parent=Path(meta['parent_route'])
    assert sha(parent/'analysis.json')==meta['parent_metadata_sha256']
    old=json.loads((parent/'analysis.json').read_text())
    assert old['status']=='passed isolated detailed-route candidate with zero router markers'
    assert sha(parent/'detailed.odb')==old['detailed.odb_sha256']==meta['parent_ODB_sha256']
    assert sha(parent/'detailed.def')==old['detailed.def_sha256']==meta['parent_DEF_sha256']
    assert (folder/'detailed.def').read_text()==expected_serialization((parent/'detailed.def').read_text())
    assert all(sha(folder/name)==meta[name+'_sha256'] for name in ['detailed.def','detailed.odb'])
    return parent,old


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--route',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert not a.output.exists() and len(os.sched_getaffinity(0))==1
    source=a.route/'detailed.odb';deffile=a.route/'detailed.def';parent=json.loads((a.route/'analysis.json').read_text())
    assert parent['status']=='passed isolated detailed-route candidate with zero router markers'
    assert sha(source)==parent['detailed.odb_sha256']=='4623e83f84bc59cc6905434cc2bb0a58795f83181677e97ce8347582e28eabb5'
    assert sha(deffile)==parent['detailed.def_sha256']=='a3ab1794039b6469c7fe610837f8e9cff788ce8c9c484f438404be6398dc1269'
    assert sha(OPENROAD)=='a20f82ef703596ff75e8ddba7a89c8447f62c5113dcb9d8be8740eb229a44ddc'
    original=deffile.read_text();_,block=transform(original);expected=expected_serialization(original)
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    patch=a.output/'one_net.def'
    patch.write_text(wire_only_patch(original,block))
    lines=['set_thread_count 1','read_db '+quote(source),'write_def '+quote(a.output/'baseline.def')]
    lines+=observation(a.output/'before.tsv')
    lines+=['read_def -floorplan_initialize '+quote(patch),'write_def '+quote(a.output/'detailed.def'),'write_db '+quote(a.output/'detailed.odb')]
    lines+=observation(a.output/'after.tsv')
    lines+=['puts "EXACT_GSHARED_ROUTE_REPAIR_COMPLETE"']
    script=a.output/'route.tcl';script.write_text('\n'.join(lines)+'\n')
    command=['timeout','--kill-after=5','90',str(OPENROAD),'-exit',str(script)]
    inputs={str(f):sha(f) for f in [source,deffile,a.route/'analysis.json',OPENROAD,Path(__file__)]}
    result=dict(status='running',parent_route=str(a.route),parent_metadata_sha256=sha(a.route/'analysis.json'),
                parent_ODB_sha256=sha(source),parent_DEF_sha256=sha(deffile),inputs=inputs,command=command,
                changed_net='g_shared_bare',centerline_shift_dbu=120,old_horizontal_clearance_um=.5,new_horizontal_clearance_um=.62,
                declared_serialization_only_difference='Exact two existing g_shared_bare terminal records reverse order; no terminal membership change permitted. Independently compare all sorted instance/terminal observations.',
                stock_rule='M3.f requires0.6um for this10.2um-wide blocker and>10um parallel run',
                not_run=['Fresh stock DRC/maximal/density/antenna','Actual GDS geometric delta and full connectivity','New RCX/STA','Adoption'],
                source_reference='OpenROAD definReader registers NETS in FLOORPLAN mode, not INCREMENTAL; definNet updates existing net wires. https://github.com/The-OpenROAD-Project/OpenROAD/blob/master/src/odb/src/defin/definReader.cpp ; pinned actual behavior must satisfy exact roundtrip below',
                prior_attempt='Incremental reader ignored NETS; FLOORPLAN updated wires but reconnected pins in reverse order. Both failed exact-delta gates retained. This successor omits connection statements from the tiny patch, keeping all existing connections and their serialized order; exact full DEF and terminal observation gates still required.')
    start=time.monotonic()
    try:
        with (a.output/'tool.log').open('x') as log:run=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
        result.update(returncode=run.returncode,wall_s=time.monotonic()-start)
        log=(a.output/'tool.log').read_text()
        assert run.returncode==0 and 'EXACT_GSHARED_ROUTE_REPAIR_COMPLETE' in log and '[ERROR' not in log
        assert (a.output/'baseline.def').read_text()==original,'Original DB/DEF roundtrip changed'
        assert (a.output/'detailed.def').read_text()==expected,'Unexpected DEF change beyond exact three-segment repair'
        assert sorted((a.output/'before.tsv').read_text().splitlines())==sorted((a.output/'after.tsv').read_text().splitlines())
        assert all(sha(Path(f))==h for f,h in inputs.items())
        result.update(status=STATUS,exact_DEF_delta='passed',instances_and_terminal_connectivity_held='passed')
        result.update({n+'_sha256':sha(a.output/n) for n in ['detailed.odb','detailed.def']})
    except Exception as error:
        result.update(status='failed exact route-repair gate',error=repr(error));raise
    finally:
        (a.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result,indent=2))


if __name__=='__main__':main()

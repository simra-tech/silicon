#!/usr/bin/env python3
"""Source-derived CDL sidecars for frozen prototype GDS; never extraction-to-golden."""
import argparse,hashlib,json,re,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from spice2cdl import convert

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--prototype',type=Path,required=True);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists();manifest=json.loads((a.prototype/'manifest.json').read_text())
    assert manifest['status']=='passed scoped native/terminal gate' and sha(a.source)==manifest['source_sha256']
    assert sha(a.prototype/'native_prototypes.gds')==manifest['GDS_sha256']
    text=a.source.read_text();blocks={name:re.search(r'(?ms)^\.subckt '+name+r' .*?^\.ends',text).group(0) for name in ('g1_ota','g1_ota_main_candidate')}
    a.output.mkdir(parents=True);records=[]
    for row in manifest['cells']:
        name=row['cell'];sub='g1_ota_main_candidate' if name.endswith('64') else 'g1_ota'
        lookup={line.split()[0]:line for line in blocks[sub].splitlines() if line.startswith('X')}
        if name=='bias_n2':chosen=[('XMB2',['d','g','vss','vss'])];pins='d g vss'
        elif name=='bias_p4':chosen=[('XMB5',['d','g','vdd','vdd'])];pins='d g vdd vss'
        else:chosen=[('XM1',['fn','inn','tail','vdd']),('XM2',['fp','inp','tail','vdd'])];pins='inp inn fn fp tail vdd vss'
        lines=[];mapping=[]
        for device,nodes in chosen:
            words=lookup[device].split();new=' '.join([words[0]]+nodes+words[5:]);lines.append(new);mapping.append(dict(source_line=lookup[device],prototype_line=new,source_subcircuit=sub))
        source_view=['.subckt '+name+' '+pins]+lines+['.ends '+name]
        cdl='* Source-derived prototype reference; ng audit is separate. No explicit taps fitted.\n'+'\n'.join(convert(source_view))+'\n'
        out=a.output/(name+'.cdl');out.write_text(cdl)
        records.append(dict(cell=name,cdl_sha256=sha(out),source_mapping=mapping,dropped_parameters=['ng','mm_ok'],
                            not_certified_by_LVS=['ng','AS/AD/PS/PD source-default applicability']))
    result={'status':'prepared source-derived references','source_sha256':sha(a.source),'prototype_manifest_sha256':sha(a.prototype/'manifest.json'),
            'GDS_sha256':manifest['GDS_sha256'],'script_sha256':sha(Path(__file__)),'converter_sha256':sha(Path(__file__).resolve().parent.parent/'spice2cdl.py'),
            'references':records,'extracted_netlist_used':False,'tap_device_reference':'none; any resulting tap mismatch is failed, not waived'}
    (a.output/'manifest.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'references':len(records)},indent=2))
if __name__=='__main__':main()

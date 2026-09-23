#!/usr/bin/env python3
"""Read pinned model files from an existing container; execute no container process."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import tarfile

HERE=Path(__file__).resolve().parent
GM4=HERE.parents[2]/'blocks/g1_sense/layout/coordinated_gm4'
IMAGE='sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2'


def digest(raw):return hashlib.sha256(raw).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--container',required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert re.fullmatch('[0-9a-f]{12,64}',a.container) and not a.output.exists()
    info=json.loads(subprocess.check_output(['podman','inspect',a.container]))[0]
    assert info['Image']==IMAGE or 'sha256:'+info['Image']==IMAGE
    old=json.loads((GM4/'psp-junction-source-equations-20260922-r1.json').read_text())
    def read(relative):
        raw=subprocess.check_output(['podman','cp',a.container+':/foss/pdks/ihp-sg13g2/'+relative,'-'])
        with tarfile.open(fileobj=io.BytesIO(raw))as archive:
            files=[r for r in archive.getmembers()if r.isfile()];assert len(files)==1
            content=archive.extractfile(files[0]).read()
        return content
    assert read('COMMIT').decode().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    paths=['libs.tech/ngspice/models/sg13g2_moshv_mod.lib',
           'libs.tech/ngspice/models/sg13g2_moshv_mod_mismatch.lib',
           'libs.tech/ngspice/models/sg13g2_moshv_parm.lib',
           'libs.tech/verilog-a/psp103/psp103.va',
           'libs.tech/verilog-a/psp103/PSP103_module.include',
           'libs.tech/verilog-a/psp103/PSP103_scaling.include',
           'libs.tech/verilog-a/psp103/PSP103_macrodefs.include',
           'libs.tech/verilog-a/psp103/PSP103_parlist.include']
    records={};texts={}
    for path in paths:
        raw=read(path);assert digest(raw)==old['file_hashes'][path],path
        texts[path]=raw.decode()
        records[path]=dict(sha256=digest(raw),bytes=len(raw),prior_pinned_hash_exact=True)
    patterns={
        'psp103.va':r'\b(module|inout|electrical)\b',
        'PSP103_module.include':r'\b(module|inout|electrical)\b|CollapsableR\(|RSE_i\s*=|RDE_i\s*=|RG_i\s*=|NF_i\s*=|NGCON|XGW|I\((?:GP|DI|SI|BS|BD),',
        'PSP103_macrodefs.include':r'CollapsableR|MULT_i.*\(G\)|MULT_i.*SN',
        'PSP103_parlist.include':r'\b(?:RGO|RSHG|RINT|RVPOLY|XGW|XGWE|NGCON|RG|RSE|RDE)\b',
        'PSP103_scaling.include':r'\b(?:RG_i|RSE_i|RDE_i|RG_p|RSE_p|RDE_p|NGCON_i|NF_i)\s*=|RSHG|RGO|RSHD|RSH_i|XGW',
        'sg13g2_moshv_mod.lib':r'^\.subckt|Nsg13_hv_[np]mos d g s b|nf=|ngcon=|rfmode ==',
        'sg13g2_moshv_mod_mismatch.lib':r'^\.subckt|Nsg13_hv_[np]mos d g s b|nf=|ngcon=|delvto=|factuo=|\+ w=|\+ l='}
    excerpts={}
    for path,text in texts.items():
        pat=patterns.get(Path(path).name)
        if pat:excerpts[path]=[dict(line=i,text=line)for i,line in enumerate(text.splitlines(),1)if re.search(pat,line)]
    models={};name=None
    wanted={'rshg','rgo','rsh','rshd','rjunso','rjundo','rbulko','rwello','swgeo','swnqs','xgw','ngcon'}
    for i,line in enumerate(texts[paths[2]].splitlines(),1):
        if line.startswith('.model '):name=line.split()[1];models[name]={}
        if name:
            for key,value in re.findall(r'(\w+)\s*=\s*(\x27[^\x27]*\x27|\S+)',line):
                if key.lower()in wanted:models[name][key.lower()]=dict(value=value,line=i)
    result=dict(status='passed pinned read-only terminal semantics inspection; distributed attachment not qualified',
        PDK_commit='84374023ee8b4b126bebbba67fcbada0a9c0ff0b',image_config_sha256=IMAGE,
        script_sha256=digest(Path(__file__).read_bytes()),files=records,excerpts=excerpts,models=models,
        no_container_process_executed=True,no_source_or_geometry_modified=True,
        not_run=['Executable/source rebuild equivalence','Distributed attachment simulation','Physical model applicability'])
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],models=models,sha256=digest(a.output.read_bytes())),indent=2))


if __name__=='__main__':main()

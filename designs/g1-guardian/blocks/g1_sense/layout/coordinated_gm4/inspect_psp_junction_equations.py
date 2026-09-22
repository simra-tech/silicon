#!/usr/bin/env python3
"""Read-only pinned source-equation evidence, not a model-equivalence test."""
import argparse,hashlib,json,os,re
from pathlib import Path

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists() and os.sched_getaffinity(0)=={7}
    root=Path('/foss/pdks/ihp-sg13g2');assert (root/'COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    directory=root/'libs.tech/verilog-a/psp103'
    files=sorted(directory.glob('*.include'))+sorted(directory.glob('*.va'))
    modelroot=root/'libs.tech/ngspice/models';files += [modelroot/name for name in ('sg13g2_moshv_mod.lib','sg13g2_moshv_mod_mismatch.lib','sg13g2_moshv_parm.lib')]
    files += sorted((root/'libs.tech/ngspice/osdi').glob('psp103*.osdi'))
    hashes={str(path.relative_to(root)):sha(path) for path in files}
    assert hashes['libs.tech/ngspice/models/sg13g2_moshv_mod.lib']=='58ce3084c253f2d3753c3b95386e8f4b81dcadfed4f4503dce56862a556c3328'
    queries={
        'PSP103_module.include':[r'AS_i\s*=',r'PS_i\s*=',r'W_i\s*=',r'jww\s*=',r'jwcorr\s*=',r'ABS_i\s*=',r'LSS_i\s*=',r'LGS_i\s*=',r'ABSOURCE_i\s*=',r'LSSOURCE_i\s*=',r'LGSOURCE_i\s*=',r'ijun_s\s*= ABSOURCE',r'qjun_s\s*=\s*ABSOURCE',r'Vjun_s\s*=',r'I\(BS, SI\)',r'CollapsableR\(.*(?:juns|well|bulk)',r'MULT_i\s*='],
        'PSP103_scaling.include':[r'^iL\s*=',r'^delWOD\s*=',r'^WE\s*=',r'RJUNS_p\s*=',r'RJUNS_i\s*=',r'RWELL_p\s*=',r'RBULK_p\s*=',r'FACTUO_i\s*=',r'DELVTO_i\s*='],
        'PSP103_macrodefs.include':[r'DELVTO_i',r'FACTUO_i',r'MULT_i\s*='],
        'JUNCAP200_macrodefs.include':[r'vmaxbot\s*=',r'vmaxsti\s*=',r'vmaxgat\s*=',r'VMAX\s*=',r'Vjun > VMAX',r'AB_i \*',r'LS_i \*',r'LG_i \*']}
    excerpts={}
    for filename,patterns in queries.items():
        lines=(directory/filename).read_text().splitlines();excerpts[filename]=[dict(line=i,text=line) for i,line in enumerate(lines,1) if any(re.search(pattern,line) for pattern in patterns)]
    models={};lines=(modelroot/'sg13g2_moshv_parm.lib').read_text().splitlines();current=None
    wanted={'swgeo','swjuncap','swjunasym','swjunexp','wvaro','wvarl','wvarw','wot','rjunso','rjundo','rbulko','rwello','rsh','rshd','imax'}
    for number,line in enumerate(lines,1):
        if line.startswith('.model '):current=line.split()[1];models[current]=dict(declaration=line,line=number,parameters={})
        if current:
            for name,value in re.findall(r'(\w+)\s*=\s*(\x27[^\x27]*\x27|\S+)',line):
                if name.lower() in wanted:models[current]['parameters'][name.lower()]=dict(value=value,line=number)
    mismatch=(modelroot/'sg13g2_moshv_mod_mismatch.lib').read_text().splitlines()
    stochastic=[dict(line=i,text=line) for i,line in enumerate(mismatch,1) if re.search(r'\+\s+(?:w|l|delvto|factuo|as|ps|nf)\s*=',line)]
    result=dict(status='completed read-only source-equation inspection; applicability not qualified',PDK_commit=(root/'COMMIT').read_text().strip(),
                script_sha256=sha(Path(__file__)),file_hashes=hashes,source_excerpts=excerpts,model_parameters=models,mismatch_instance_lines=stochastic,
                executable_source_rebuild_binding='not run; OSDI hashes recorded, no assertion that inspected source was rebuilt into these binaries',
                simulation='not run',GDS_saved=False,cards_modified=False,unconditional_shared_junction_equivalence='not established')
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'models':models},indent=2))
if __name__=='__main__':main()

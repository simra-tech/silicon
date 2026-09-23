#!/usr/bin/env python3
"""Read-only binary/version/unchanged-technology preflight, no geometry import."""
import argparse, hashlib, json, os, re, shutil, subprocess, time
from pathlib import Path

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists() and list(os.sched_getaffinity(0))==[6]
    a.output.mkdir(parents=True)
    pdk=Path('/foss/pdks/ihp-sg13g2');tech=pdk/'libs.tech/magic/ihp-sg13g2.tech'
    assert (pdk/'COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    assert sha(tech)=='0a0e1666da3fa38d7faefe340576102ddc558727a3f6f7f666e92f50a1dc568d'
    paths={str(q):sha(q) for q in tech.parent.rglob('*') if q.is_file()}
    executable=shutil.which('magic');start=time.monotonic()
    result=dict(status='running',CPU=6,executable=executable,source_sha256=sha(Path(__file__)),
        required_version='8.3.617',pdk_files=paths,steps=[],not_run=['Geometry import','Extraction','Backend adoption'])
    def save():
        result['wall_s']=time.monotonic()-start
        (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    def call(name,command,limit):
        row=dict(name=name,command=command,timeout_s=limit);result['steps'].append(row);save()
        try:
            proc=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=limit)
            text=proc.stdout.decode(errors='replace');row.update(returncode=proc.returncode,status='completed')
        except subprocess.TimeoutExpired as exc:
            text=(exc.stdout or b'').decode(errors='replace');row.update(status='timeout');raise
        finally:
            if 'text' in locals():
                (a.output/(name+'.log')).write_text(text);row['log_sha256']=sha(a.output/(name+'.log'))
            save()
        assert proc.returncode==0,(name,proc.returncode)
        return text
    try:
        assert executable,'Magic executable missing'
        binary=Path(executable).resolve();result['resolved_executable']=str(binary);result['executable_sha256']=sha(binary)
        text=call('version',[executable,'--version'],10)
        versions=re.findall(r'(?<!\d)(8\.\d+\.\d+)(?!\d)',text);assert versions,text
        result['version']=versions[0]
        assert tuple(map(int,versions[0].split('.'))) >= (8,3,617),'Installed Magic below unchanged tech requirement'
        script=Path(__file__).with_suffix('.tcl');result['tcl_sha256']=sha(script)
        text=call('technology_load',[executable,'-dnull','-noconsole','-rcfile',str(tech.parent/'ihp-sg13g2.magicrc'),str(script)],30)
        result['error_lines']=[s for s in text.splitlines() if re.search(r'(?i)(^|\b)(error|fatal|invalid command|unknown command|could not|cannot load|requires magic)\b',s)]
        assert not result['error_lines'],result['error_lines']
        assert 'IDENTITY_TECH=ihp-sg13g2' in text and 'IDENTITY_COMPLETE=1' in text
        assert 'ngspice()' in text
        assert all(sha(Path(q))==digest for q,digest in paths.items())
        result['status']='passed binary/version/unchanged technology load only'
    except Exception as exc:
        result.update(status='failed Magic identity preflight',error=repr(exc));raise
    finally:
        save();print(json.dumps({k:v for k,v in result.items() if k!='pdk_files'},indent=2))

if __name__=='__main__':main()

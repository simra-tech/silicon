#!/usr/bin/env python3
"""Bounded native-blackbox CC pilot; no electrical/source-model adoption."""
import argparse,datetime,hashlib,importlib.metadata,json,math,os,re,signal,subprocess,time
from pathlib import Path
import klayout_pex,pya

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def value(s):
    match=re.fullmatch(r'([-+\d.eE]+)([afpnumk]?)',s);assert match,s
    return float(match[1])*dict(a=1e-18,f=1e-15,p=1e-12,n=1e-9,u=1e-6,m=1e-3,k=1e3).get(match[2],1.)
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in('view','reference','output','resource-gate'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();assert not a.output.exists() and os.sched_getaffinity(0)=={6} and pya.__version__=='0.30.9' and importlib.metadata.version('klayout-pex')=='0.3.12'
    gate=json.loads(a.resource_gate.read_text());assert gate['status']=='passed' and gate['external_allocation']['expected_growth_gib']>=1 and 0<=(datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(gate['utc'])).total_seconds()<1800
    m=json.loads((a.view/'manifest.json').read_text());ref=json.loads((a.reference/'manifest.json').read_text());assert m['status']=='passed extraction-only flat label view' and m['native_MIM_layers_retained'] and m['candidate_GDS_sha256']==ref['GDS_sha256']
    here=Path(__file__).resolve().parent;source=here.parents[1]/'reports/resume-server-20260922/gm4comp3-qualified-source.spice';assert sha(source)==m['source_sha256']=='baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877'
    gds=a.view/'g1_sense_pex_view.gds';cdl=a.reference/'g1_sense_physical.cdl';assert sha(gds)==m['GDS_sha256'] and sha(cdl)==ref['CDL_sha256'];bindings={f:sha(f)for f in(source,gds,cdl,a.view/'manifest.json',a.reference/'manifest.json')}
    pkg=Path(klayout_pex.__file__).parent;pdk=Path('/foss/pdks/ihp-sg13g2');assert(pdk/'COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    toolfiles={f:sha(f)for f in pkg.rglob('*')if f.is_file()and f.suffix in('.py','.json','.lvs','.lylvs','.rb')};cards={f:sha(f)for f in(pdk/'libs.tech/ngspice/models').rglob('*.lib')};assert toolfiles and cards
    a.output.mkdir(parents=True);(a.output/'runner_snapshot.py').write_bytes(Path(__file__).read_bytes());(a.output/'contract.md').write_bytes((here/'SENSE_PEX_CONTRACT_20260922.md').read_bytes())
    spice=a.output/'g1_sense_blackbox_cc.spice';cmd=['kpex','--pdk','ihp-sg13g2','--threads','1','--2.5D','--mode','CC','--blackbox','true','--cache-lvs','false','--gds',str(gds.resolve()),'--cell','g1_sense_physical','--schematic',str(cdl.resolve()),'--out_dir',str((a.output/'kpex').resolve()),'--out_spice',str(spice.resolve())]
    result=dict(status='running',command=cmd,source_sha256=sha(source),GDS_sha256=sha(gds),candidate_GDS_sha256=m['candidate_GDS_sha256'],CDL_sha256=sha(cdl),view_manifest_sha256=sha(a.view/'manifest.json'),script_sha256=sha(Path(__file__)),tool='KLayout-PEX0.3.12/KLayout0.30.9',tool_hashes={str(f.relative_to(pkg)):h for f,h in toolfiles.items()},card_hashes={str(f.relative_to(pdk)):h for f,h in cards.items()},timeout_s=180,max_output_bytes=2**30,threads=1,blackbox=True,mode='CC',source_mapping='not run',electrical_equivalence='not run',fill='not run',resistance='not run',adoption='not run')
    report=a.output/'summary.json';report.write_text(json.dumps(result,indent=2)+'\n');start=time.monotonic();interrupted=[];old={s:signal.signal(s,lambda signum,frame:interrupted.append(signum))for s in(signal.SIGINT,signal.SIGTERM)};reason=None
    with(a.output/'kpex.log').open('x')as log:
        proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1'))
        try:
            while proc.poll()is None:
                growth=sum(f.stat().st_size for f in a.output.rglob('*')if f.is_file());elapsed=time.monotonic()-start
                if interrupted or elapsed>=180 or growth>2**30:
                    reason='interrupted'if interrupted else('timeout'if elapsed>=180 else'output_limit');os.killpg(proc.pid,signal.SIGTERM)
                    try:proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait()
                    break
                result.update(wall_s=elapsed,output_bytes=growth);report.write_text(json.dumps(result,indent=2)+'\n')
                try:proc.wait(timeout=1)
                except subprocess.TimeoutExpired:pass
        finally:
            if proc.poll()is None:os.killpg(proc.pid,signal.SIGKILL);proc.wait();reason=reason or'runner_error'
            for s,handler in old.items():signal.signal(s,handler)
    logtext=(a.output/'kpex.log').read_text(errors='replace');issues=re.findall(r'(?im)^.*(?:No .*cap specified|<TODO>|Traceback|unsupported|Unable to find info about extracted).*$' ,logtext)
    caps=[];parse_error=None
    if spice.exists():
        try:
            lines=[]
            for line in spice.read_text().splitlines():
                if line.startswith('+'):lines[-1]+=' '+line[1:]
                else:lines.append(line)
            for line in lines:
                if re.match(r'^Cext_',line,re.I):
                    words=line.split();cap=value(words[3]);assert math.isfinite(cap)and cap>=0 and words[1]!=words[2];caps.append(dict(name=words[0],nodes=words[1:3],C_F=cap))
        except Exception as exc:parse_error=repr(exc)
    result.update(status='passed bounded raw CC extraction; semantic mapping not run'if reason is None and proc.returncode==0 and caps and not issues and parse_error is None else'failed bounded CC diagnostic',termination_reason=reason,returncode=proc.returncode,wall_s=time.monotonic()-start,output_bytes=sum(f.stat().st_size for f in a.output.rglob('*')if f.is_file()),unsupported_or_missing_layer_messages=issues,cap_parse_error=parse_error,parasitic_cap_count=len(caps),parasitic_node_count=len({n for row in caps for n in row['nodes']}),SPICE_sha256=sha(spice)if spice.exists()else None,log_sha256=sha(a.output/'kpex.log'),inputs_unchanged=all(sha(f)==h for f,h in bindings.items()),tool_files_unchanged=all(sha(f)==h for f,h in toolfiles.items()),model_cards_unchanged=all(sha(f)==h for f,h in cards.items()))
    if not all(result[k]for k in('inputs_unchanged','tool_files_unchanged','model_cards_unchanged')):result['status']='failed changed bound inputs'
    report.write_text(json.dumps(result,indent=2)+'\n');(a.output/'raw_capacitors.json').write_text(json.dumps(caps,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in('tool_hashes','card_hashes','command','unsupported_or_missing_layer_messages')},indent=2));raise SystemExit(0 if result['status'].startswith('passed')else 1)
if __name__=='__main__':main()

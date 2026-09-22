#!/usr/bin/env python3
"""Unmodified complete source OTA reference; only subcircuit boundary renamed."""
import argparse,hashlib,json,re,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from spice2cdl import convert

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--buffer',type=Path,required=True);p.add_argument('--saved-audit',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    source=Path(__file__).resolve().parents[2]/'reports/resume-server-20260922/gm4comp3-qualified-source.spice';assert sha(source)=='baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877'
    m=json.loads((a.buffer/'manifest.json').read_text());audit=json.loads(a.saved_audit.read_text());gds=a.buffer/'g1_ota_source_faithful.gds'
    assert sha(gds)==m['GDS_sha256']==audit['GDS_sha256']=='320df90ee046c73b628005da9384c80fbd21a715a39b0e8b96b10923726fc500'
    assert audit['status']=='passed saved-buffer source/native/terminal audit'
    original=re.search(r'(?ms)^\.subckt g1_ota .*?^\.ends[^\n]*',source.read_text()).group(0)
    lines=original.splitlines();lines[0]=lines[0].replace('.subckt g1_ota ','.subckt g1_ota_source_faithful ',1);lines[-1]='.ends g1_ota_source_faithful'
    devices=[line for line in lines if line.startswith('X')];assert len(devices)==21
    a.output.mkdir(parents=True);view=a.output/'source_reference.spice';view.write_text('\n'.join(lines)+'\n')
    cdl=a.output/'g1_ota_source_faithful.cdl';cdl.write_text('* Exact complete source OTA; source ng and junction audits remain separate.\n'+'\n'.join(convert(lines))+'\n')
    result=dict(status='prepared exact source reference',source_sha256=sha(source),source_subcircuit='g1_ota',GDS_sha256=sha(gds),
                original_subcircuit_sha256=hashlib.sha256(original.encode()).hexdigest(),source_view_sha256=sha(view),CDL_sha256=sha(cdl),
                manifest_sha256=sha(a.buffer/'manifest.json'),saved_audit_sha256=sha(a.saved_audit),script_sha256=sha(Path(__file__)),
                converter_sha256=sha(Path(__file__).resolve().parent.parent/'spice2cdl.py'),exact_source_device_lines=devices,
                conversions=['Rename subcircuit boundary only','Stock converter X primitives to M/R/C','ng and mm_ok dropped','RZ sub! to vss per canonical convention'],
                source_or_model_parameters_fitted=False,extracted_netlist_used=False,stock_checks='not run',tap_devices='none added to reference')
    (a.output/'manifest.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'CDL_sha256':sha(cdl)}))
if __name__=='__main__':main()

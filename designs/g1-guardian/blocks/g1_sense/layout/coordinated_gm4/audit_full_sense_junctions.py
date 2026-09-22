#!/usr/bin/env python3
"""Read-only stock/native junction attribution; strict LVS is not A/P acceptance."""
import argparse,hashlib,json,os,re
from pathlib import Path
import pya
from audit_junction_defaults import default

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in('stock','reference','output'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();assert not a.output.exists() and len(os.sched_getaffinity(0))==1 and pya.__version__=='0.30.9'
    source=Path(__file__).resolve().parents[2]/'reports/resume-server-20260922/gm4comp3-qualified-source.spice';assert sha(source)=='baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877'
    summary=json.loads((a.stock/'summary.json').read_text());ref=json.loads((a.reference/'manifest.json').read_text());assert summary['status']=='passed' and summary['GDS_sha256']==ref['GDS_sha256'] and ref['source_sha256']==sha(source)
    specs={}
    for block in re.findall(r'(?ms)^\.subckt .*?^\.ends[^\n]*',source.read_text()):
        name=block.split()[1];specs[name]={s.split()[0][1:].upper():s for s in block.splitlines()if ' sg13_hv_'in s}
    assert [len(specs[n])for n in('g1_sense','g1_ota','g1_ota_main_candidate')]==[1,19,19]
    path=a.stock/'lvs/g1_sense_physical.lvsdb';original=sha(path);db=pya.LayoutVsSchematic();db.read(str(path));xref=db.xref();rows=[];classes=[]
    for cls in db.netlist().each_device_class():
        if cls.name not in('sg13_hv_nmos','sg13_hv_pmos'):continue
        fields={q.name:q.is_primary for q in cls.parameter_definitions()};assert fields=={'L':True,'W':True,'AS':False,'AD':False,'PS':False,'PD':False,'rfmode':True};classes.append(dict(model=cls.name,fields=fields,ng_present=False))
    assert len(classes)==2
    for cp in xref.each_circuit_pair():
        assert cp.status()==pya.NetlistCrossReference.Match
        circuit=cp.second().name.lower();key='g1_sense'if circuit=='g1_sense_physical'else circuit;assert key in specs
        netmap={}
        for pair in xref.each_net_pair(cp):
            assert pair.status()==pya.NetlistCrossReference.Match;netmap[pair.first().name]=pair.second().name.lower()
        for pair in xref.each_device_pair(cp):
            assert pair.status()==pya.NetlistCrossReference.Match;name=pair.second().name.upper()
            if name not in specs[key]:continue
            line=specs[key][name];words=line.split();params=dict(re.findall(r'(\w+)=([^\s]+)',line));expected=default(float(params['w'].rstrip('u')),int(params['ng']));device=pair.first()
            terminals={term.name.upper():netmap[device.net_for_terminal(term.name).name]for term in device.device_class().terminal_definitions()}
            assert terminals['G']==words[2].lower() and terminals['B']==words[4].lower() and {terminals['S'],terminals['D']}=={words[1].lower(),words[3].lower()}
            values={n:device.parameter(n)for n in('AS','AD','PS','PD')};by_net={terminals['S']:(values['AS'],values['PS']),terminals['D']:(values['AD'],values['PD'])}
            actual=dict(as_um2=by_net[words[3].lower()][0],ps_um=by_net[words[3].lower()][1],ad_um2=by_net[words[1].lower()][0],pd_um=by_net[words[1].lower()][1]);delta={k:actual[k]-expected[k]for k in expected}
            prefixes=['XOTA/']if key=='g1_ota_main_candidate'else(['XBUF/','XREF/']if key=='g1_ota'else[''])
            for prefix in prefixes:
                identity=prefix+'X'+name;native=next(d for d in ref['devices']if d['device']==identity);assert native['source_line']==line and native['expected_default']==expected
                rows.append(dict(device=identity,source_cell=key,source_line=line,stock_device_id=device.id(),stock_terminals_source_names=terminals,stock_fields=values,source_node_actual=actual,source_default=expected,native_junction_allocation=ref['adjacent_gate_allocation'][identity],delta_stock_minus_source_default=delta,status='passed'if all(abs(v)<1e-8 for v in delta.values())else'failed'))
    assert len(rows)==58 and len({r['device']for r in rows})==58 and sha(path)==original and sha(source)==summary['source_sha256']
    counts={status:sum(r['status']==status for r in rows)for status in('passed','failed')}
    result=dict(status='passed complete read-only stock attribution audit',per_node_junction_status='failed'if counts['failed']else'passed',source_sha256=sha(source),stock_database_sha256=original,stock_summary_sha256=sha(a.stock/'summary.json'),reference_manifest_sha256=sha(a.reference/'manifest.json'),script_sha256=sha(Path(__file__)),counts=counts,rows=rows,stock_classes=classes,scope='Actual 58 source-instance records; shared buffer definition is expanded to XBUF and XREF. Strict LVS only compares L/W/rfmode. Native default-allocation geometry is independent of the failed stock per-node annotation. No source/card/deck/database edits, no extracted-to-golden tuning.',intrinsic_shared_junction_model_applicability='not run',source_preserving_parasitic_mapping='not run')
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in('rows','stock_classes')},indent=2))
if __name__=='__main__':main()

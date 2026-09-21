#!/usr/bin/env python3
"""Hash retained power/IR inputs and reports; distinguish evidence coverage."""
import hashlib,json,re
from pathlib import Path
R=Path(__file__).resolve().parents[4];B=R/'designs/g1-guardian/blocks';rows=[];files={}
def read(p):
    files[str(p.relative_to(R))]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size};return p.read_text()
for block,tag,sta,ir in [('g1_ctrl','run7','56-openroad-stapostpnr','57-openroad-irdropreport'),('g1_padring','assembly-1350','54-openroad-stapostpnr','55-openroad-irdropreport')]:
    run=B/block/'flow/runs'/tag;data={'block':block,'run':tag,'power_W':{},'IR':{}}
    for corner in ['nom_typ_1p20V_25C','nom_fast_1p32V_m40C','nom_slow_1p08V_125C']:
        report=read(run/sta/corner/'power.rpt');groups={}
        for line in report.splitlines():
            if re.match(r'^(Sequential|Combinational|Clock|Macro|Pad|Total)\s',line):
                v=line.split();groups[v[0]]=dict(zip(['internal','switching','leakage','total'],map(float,v[1:5])))
        data['power_W'][corner]=groups
    for step in [sta,ir]:
        for name in ['COMMANDS','config.json']:read(run/step/name)
        state=json.loads(read(run/step/'state_in.json'))
        for key in ['nl','pnl','odb','def','sdc','spef']:
            value=state.get(key)
            for item in (value.values() if isinstance(value,dict) else [value]):
                if isinstance(item,str) and item.startswith('/work/'):
                    p=R/item.removeprefix('/work/')
                    if p.exists():files[str(p.relative_to(R))]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
    log=read(run/sta/'nom_typ_1p20V_25C/sta.log')
    data['blackbox_modules']=sorted(set(re.findall(r'module (\w+) not found',log)))
    data['macro_netlist_lines']=[line for line in log.splitlines() if 'Reading macro netlist' in line or "Reading 'i_core.u_digital' parasitics" in line]
    irlog=read(run/ir/'openroad-irdropreport.log');report=read(run/ir/'irdrop.rpt');metrics=json.loads(read(run/ir/'or_metrics_out.json'))
    for section in report.split('########## IR report #################')[1:]:
        fields=dict(re.findall(r'^([\w ]+)\s*:\s*([^\n]+)',section,re.M));net=fields['Net              '].strip()
        data['IR'][net]={k.strip():v.strip() for k,v in fields.items()}
        data['IR'][net]['exact_worst_drop_V']=metrics[f'design_powergrid__drop__worst__net:{net}__corner:nom_typ_1p20V_25C']
    data['activity_trace_matches']=[line for line in (log+'\n'+irlog).splitlines() if re.search(r'\b(read_vcd|read_saif|set_power_activity)\b',line)]
    data['activity_qualification']='No activity annotation found in retained STA/IR logs; vectorless estimate; numerical engine defaults not established'
    for pattern in ['final/gds/*.gds','final/def/*.def','final/nl/*.v','final/pnl/*.v','final/spef/nom/*.spef']:
        for p in run.glob(pattern):files[str(p.relative_to(R))]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
    rows.append(data)
for relative in ['g1_ctrl/layout/g1_digital.nl.v','g1_ctrl/layout/g1_digital.nom.spef','g1_ctrl/layout/lib/g1_digital__nom_typ_1p20V_25C.lib','g1_ctrl/flow/g1_digital.sdc','g1_ctrl/layout/g1_digital_top.sdc','g1_padring/flow/g1_chip_top.sdc','g1_padring/flow/runs/assembly-1350/22-openroad-generatepdn/analog_straps.log','g1_padring/flow/runs/assembly-1350/51-openroad-fillinsertion/g1_chip_top.nl.v','g1_padring/flow/runs/assembly-1350/53-openroad-rcx/nom/g1_chip_top.nom.spef']:
    read(B/relative)
lib=(B/'g1_ctrl/layout/lib/g1_digital__nom_typ_1p20V_25C.lib').read_text()
result={'scope':'Read-only retained-report audit. No new power, activity or IR simulation.', 'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'runs':rows,'digital_abstract_power_groups':{k:len(re.findall(r'\b'+k+r'\s*\(',lib)) for k in ['internal_power','leakage_power','cell_leakage_power']},'artifact_hashes':files,'checks':{'whole_chip_power_below_10mW':'not run','activity_annotated_power':'not run','loaded_VDDA_IR':'not run','loaded_IOVDD_IOVSS_IR':'not run','assembly_full_macro_load_IR':'not run'}}
out=R/'designs/g1-guardian/review/audits/power-evidence-20260921.json';out.write_text(json.dumps(result,indent=2)+'\n');print(out.relative_to(R))

#!/usr/bin/env python3
"""PREPARATION-ONLY strict one-target capacitor reduction, no pilot acceptance yet."""
import argparse,hashlib,json,math,re
from pathlib import Path
import numpy as np
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--clip',type=Path,required=True);p.add_argument('--pex',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
provenance=json.loads((a.clip/'provenance.json').read_text());label_groups={row['label']:row['group'] for row in provenance['labels']};label_groups['VSUBS']='grounded_context';results={};a.output.mkdir()
for variant in ('no_fill','actual_fill'):
    path=a.pex/variant/'kpex/clip__sense_fill_clip/sense_fill_clip_k25d_pex_netlist.spice';statements=[]
    for line in path.read_text().splitlines():
        line=line.strip()
        if not line or line.startswith('*'):continue
        if line.startswith('+'):assert statements;statements[-1]+=' '+line[1:].strip()
        else:statements.append(line)
    caps=[];names=set()
    for line in statements:
        fields=line.split()
        if not fields[0].lower().startswith('c'):continue
        assert len(fields)==4 and fields[0].lower() not in names;names.add(fields[0].lower())
        match=re.fullmatch(r'([\d.eE+\-]+)([afpnu]?)',fields[3]);assert match
        value=float(match[1])*{'a':1e-18,'f':1e-15,'p':1e-12,'n':1e-9,'u':1e-6,'':1}[match[2]];assert math.isfinite(value) and value>0
        assert fields[1]!=fields[2];caps.append((fields[1],fields[2],value))
    assert caps;nodes=sorted({name for left,right,value in caps for name in (left,right)});groups={}
    emitted_labels={label for node in nodes for label in node.split('|')}
    assert {label for label,group in label_groups.items() if group=='target'}<=emitted_labels,'missing target component after extraction'
    for node in nodes:
        labels=node.split('|');assert all(label in label_groups for label in labels),(node,'unidentified extractednode')
        classes={label_groups[label] for label in labels}
        assert not ('target' in classes and ('grounded_context' in classes or 'fill' in classes)),(node,'inconsistent physicaltarget classification')
        groups[node]='target' if classes=={'target'} else 'grounded_context' if 'grounded_context' in classes else 'fill'
    target=[node for node in nodes if groups[node]=='target'];fill=[node for node in nodes if groups[node]=='fill'];assert target
    index={node:i for i,node in enumerate(nodes)};matrix=np.zeros((len(nodes),len(nodes)))
    for left,right,value in caps:
        i,j=index[left],index[right];matrix[i,i]+=value;matrix[j,j]+=value;matrix[i,j]-=value;matrix[j,i]-=value
    assert np.max(abs(matrix.sum(axis=1)))<1e-27
    ti=[index[node] for node in target];fi=[index[node] for node in fill];record={'target_extracted_components':target,'node_groups':groups,'capacitors':len(caps),'modes':{}}
    for mode in ('grounded_fill','floating_fill'):
        reduced=matrix[np.ix_(ti,ti)];residual=0
        if mode=='floating_fill' and fi:
            ff=matrix[np.ix_(fi,fi)];fp=matrix[np.ix_(fi,ti)];transfer=np.linalg.solve(ff,-fp);reduced=reduced+matrix[np.ix_(ti,fi)]@transfer;residual=float(np.max(abs(ff@transfer+fp)))
        assert math.isfinite(residual) and residual<=1e-25,'Schur charge residual exceeded frozen limit'
        ones=np.ones(len(ti));ceff=float(ones@reduced@ones);assert math.isfinite(ceff) and ceff>0
        record['modes'][mode]={'target_ground_equivalent_fF':ceff*1e15,'floating_charge_residual_F':residual}
        deck=['* Declared idealoutsideequipotential target pieces; othercontexts ground.']
        for i,(left,right,value) in enumerate(caps):
            def convert(node):return 'P' if groups[node]=='target' else '0' if groups[node]=='grounded_context' or mode=='grounded_fill' else 'F'+str(index[node])
            left,right=convert(left),convert(right)
            if left!=right:deck.append('C%d %s %s %.17g'%(i,left,right,value))
        deck+=['VP P 0 DC 0 AC 1','.control','set numdgt=17','ac lin 1 1Meg 1Meg','let ceff = -imag(i(VP))/(2*pi*1e6)','print ceff','echo LOCAL_CAP_AC_END','quit','.endc','.end']
        (a.output/(variant+'_'+mode+'.cir')).write_text('\n'.join(deck)+'\n')
    results[variant]=record
(a.output/'summary.json').write_text(json.dumps({'status':'matrixreduction complete; ngspiceACcomparison NOTRUN','clip_provenance_sha256':hashlib.sha256((a.clip/'provenance.json').read_bytes()).hexdigest(),'results':results,
    'scope':'One-target local load under explicitlyidealoutsideconnections forprovenmetalnet pieces, groundedcontext andtwofillconditions. Not actual signal/activity/circuit acceptance, currentmargin, convergence orwholeRC.'},indent=2)+'\n')

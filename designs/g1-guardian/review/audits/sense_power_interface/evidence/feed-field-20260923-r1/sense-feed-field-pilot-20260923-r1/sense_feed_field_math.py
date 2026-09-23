"""Strict source-group capacitor accounting for the frozen zero-fill pilot."""
import math
import re


def parse_caps(text):
    statements=[]
    for raw in text.splitlines():
        line=raw.strip()
        if not line or line.startswith('*'):continue
        if line.startswith('+'):
            if not statements:raise ValueError('orphan continuation')
            statements[-1]+=' '+line[1:].strip()
        else:statements.append(line)
    caps=[];names=set()
    for line in statements:
        fields=line.split();kind=fields[0][0].lower()
        if kind=='.':continue
        if kind!='c':raise ValueError('non-capacitor element in ordinary-metal CC graph: '+line)
        if len(fields)!=4 or fields[0].lower() in names:raise ValueError('malformed/duplicate capacitor')
        names.add(fields[0].lower())
        match=re.fullmatch(r'([\d.eE+\-]+)([afpnu]?)',fields[3])
        if match is None:raise ValueError('unsupported capacitor value')
        value=float(match[1])*{'a':1e-18,'f':1e-15,'p':1e-12,'n':1e-9,'u':1e-6,'':1}[match[2]]
        if not math.isfinite(value) or value<=0 or fields[1]==fields[2]:raise ValueError('nonpositive/nonfinite/self capacitor')
        caps.append((fields[1],fields[2],value))
    if not caps:raise ValueError('empty capacitor graph')
    return caps


def reduce_caps(caps, provenance):
    assert provenance['fill_count']==provenance['MIM_Vmim_count']==0
    labels={r['label']:r for r in provenance['labels']};assert len(labels)==len(provenance['labels'])
    expected={frozenset(row['labels']):row for row in provenance['components']}
    assert sum(len(k) for k in expected)==len(labels)
    nodes=sorted({node for a,b,c in caps for node in (a,b)});groups={};sources={};seen=set();components=set()
    for node in nodes:
        aliases=node.split('|');assert len(aliases)==len(set(aliases))
        if aliases==['VSUBS']:
            groups[node]='context';sources[node]='VSUBS';continue
        assert all(name in labels for name in aliases),('Unidentified extracted label',node)
        key=frozenset(aliases);assert key in expected,('Physical component aliases differ from saved clip',node)
        assert key not in components;components.add(key);seen.update(aliases)
        source_names={labels[name]['source_net'] for name in aliases};assert len(source_names)==1
        source=next(iter(source_names));assert source==expected[key]['source_net']
        classes={labels[name]['group'] for name in aliases};assert len(classes)==1
        groups[node]=next(iter(classes));sources[node]=source
    assert seen==set(labels) and components==set(expected),'Missing native conductor component'
    assert set(groups.values())=={'P','N','context'} and 'VSUBS' in nodes
    index={node:i for i,node in enumerate(nodes)};matrix=[[0. for _ in nodes] for _ in nodes]
    contributions={'P_ground':[],'N_ground':[],'mutual':[]};source_caps={}
    for a,b,c in caps:
        assert math.isfinite(c) and c>0 and a!=b
        i,j=index[a],index[b];matrix[i][i]+=c;matrix[j][j]+=c;matrix[i][j]-=c;matrix[j][i]-=c
        ga,gb=groups[a],groups[b]
        if ga!=gb:
            key='mutual' if {ga,gb}=={'P','N'} else 'P_ground' if 'P' in (ga,gb) else 'N_ground'
            contributions[key].append(c)
        sa,sb=sources[a],sources[b]
        if sa!=sb:source_caps.setdefault(tuple(sorted((sa,sb))),[]).append(c)
    residual=max(abs(math.fsum(row)) for row in matrix);assert math.isfinite(residual) and residual<1e-27
    gp,gn,mut=(math.fsum(contributions[k]) for k in ('P_ground','N_ground','mutual'))
    reduced=[[gp+mut,-mut],[-mut,gn+mut]]
    assert all(math.isfinite(x) for row in reduced for x in row)
    assert reduced[0][0]>0 and reduced[1][1]>0 and gp*gn+mut*(gp+gn)>0
    return dict(matrix_F=reduced,P_ground_F=gp,N_ground_F=gn,mutual_F=mut,
        differential_energy_F=.25*(gp+gn)+mut,common_mode_energy_F=gp+gn,
        raw_nodes=nodes,raw_matrix_F=matrix,node_groups=groups,node_source_nets=sources,
        source_net_pair_capacitors_F=[dict(nets=list(key),C_F=math.fsum(values)) for key,values in sorted(source_caps.items())],
        row_sum_residual_F=residual,floating_charge_residual_F=0.,
        Schur='not applicable: frozen pilot has no fill/internal floating block',
        physical_components_accounted=len(components),capacitors=len(caps))


def ac_deck(caps, groups, drive):
    assert drive in ('P','N')
    deck=['* Frozen ordinary-metal capacitor graph; ideal outside P/N grouping, other context grounded.']
    for i,(a,b,c) in enumerate(caps):
        x='0' if groups[a]=='context' else groups[a];y='0' if groups[b]=='context' else groups[b]
        if x!=y:deck.append('C%d %s %s %.17g'%(i,x,y,c))
    deck += ['VP P 0 DC 0 AC '+str(int(drive=='P')),'VN N 0 DC 0 AC '+str(int(drive=='N')),
        '.control','set numdgt=17','ac lin 1 1Meg 1Meg','let cp = -imag(i(VP))/(2*pi*1e6)',
        'let cn = -imag(i(VN))/(2*pi*1e6)','print cp cn','echo SENSE_FEED_AC_END','quit','.endc','.end']
    return '\n'.join(deck)+'\n'


def ac_check(log, returncode, expected):
    fatal=bool(re.search(r'(?im)^\s*(?:fatal(?: error)?|error)\b|syntax error|segmentation fault|doAnalyses:.*failed|timestep too small',log))
    observed={}
    for name in ('cp','cn'):
        matches=re.findall(r'^'+name+r'\s*=\s*([-+\deE.]+)\s*$',log,re.M)
        if len(matches)!=1:return dict(status='failed',reason='missing or duplicate exact AC vector',fatal_log=fatal)
        observed[name]=float(matches[0])
    finite=all(math.isfinite(v) for v in observed.values()) and all(math.isfinite(v) for v in expected)
    error=max(abs(observed[n]-expected[i]) for i,n in enumerate(('cp','cn'))) if finite else float('inf')
    passed=returncode==0 and not fatal and log.count('SENSE_FEED_AC_END')==1 and finite and error<1e-25
    return dict(status='passed' if passed else 'failed',observed_F={k:v if math.isfinite(v) else None for k,v in observed.items()},expected_F=expected,
        max_abs_error_F=error if finite else None,tolerance_F=1e-25,fatal_log=fatal,finite=finite)


def context_check(small,large):
    fields=['P_ground_F','N_ground_F','mutual_F','differential_energy_F','common_mode_energy_F']
    rows=[]
    metrics=[(key,small[key],large[key]) for key in fields]
    metrics += [('matrix_%d_%d'%(i,j),small['matrix_F'][i][j],large['matrix_F'][i][j]) for i in range(2) for j in range(2)]
    for key,a,b in metrics:
        assert math.isfinite(a) and math.isfinite(b)
        relative=None if b==0 else abs(a-b)/abs(b)
        rows.append(dict(metric=key,small_F=a,large_F=b,relative_error=relative,
            status='passed' if relative is not None and relative<=.01 else 'failed',
            reason='zero denominator' if relative is None else 'unchanged 1% criterion'))
    return dict(status='passed' if all(r['status']=='passed' for r in rows) else 'failed',metrics=rows,tolerance=.01)

#!/usr/bin/env python3
"""Nominal sheet-R network from actual DEF top-metal PDN; not signoff PEX/IR."""
import collections,hashlib,json,re
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import splu
from scipy.sparse.csgraph import dijkstra,connected_components
import pya
R=Path(__file__).resolve().parents[4];B=R/'designs/g1-guardian/blocks/g1_padring';P=Path('/foss/pdks/ihp-sg13g2');out=R/'designs/g1-guardian/review/audits/supply-mesh-20260921';out.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
deffile=B/'flow/runs/assembly-1350/final/def/g1_chip_top.def';gds=B/'layout/g1_chip_top.gds';tech=P/'libs.ref/sg13g2_stdcell/lef/sg13g2_tech.lef'
d=deffile.read_text();units=int(re.search(r'UNITS DISTANCE MICRONS (\d+)',d)[1]);t=tech.read_text();sheet={};cut={}
for name,body in re.findall(r'^LAYER (\w+)\n(.*?)^END \1\s*$',t,re.M|re.S):
    body=re.sub(r'#.*','',body)
    if m:=re.search(r'RESISTANCE RPERSQ ([\d.]+)',body):sheet[name]=float(m[1])
    elif m:=re.search(r'RESISTANCE ([\d.]+)',body):cut[name]=float(m[1])
via_defs={}
for name,body in re.findall(r'^\s*- (\S+) (.*?) ;',re.search(r'^VIAS \d+ ;(.*?)^END VIAS',d,re.M|re.S)[1],re.M|re.S):
    m=re.search(r'LAYERS (\w+) (\w+) (\w+)',body);n=re.search(r'ROWCOL (\d+) (\d+)',body)
    if m and n:via_defs[name]={'layers':list(m.groups()),'cuts':int(n[1])*int(n[2]),'R_ohm':cut[m[2]]/(int(n[1])*int(n[2]))}
log=(B/'flow/runs/assembly-1350/22-openroad-generatepdn/analog_straps.log').read_text();terminals=collections.defaultdict(list)
for name,net,x,y in re.findall(r'analog_straps: (\S+) \((\w+)\): stack on the bar at \(([\d.]+), ([\d.]+)\)',log):terminals[net].append({'name':name,'point_um':[float(x),float(y)],'access':'Metal3 bar stack'})
for name,net,layer,x1,x2,y,x in re.findall(r'analog_straps: (\S+) \((\w+)\): jog on (\w+) x ([\d.]+)\.\.([\d.]+) at y=([\d.]+), stack at x=([\d.]+)',log):terminals[net].append({'name':name,'point_um':[float(x),float(y)],'access':layer+' jog','jog_extent_um':[float(x1),float(x2)]})
ly=pya.Layout();ly.read(str(gds));top=ly.cell('g1_chip_top');regions={n:pya.Region(top.begin_shapes_rec(ly.layer(gl,0))).merged() for n,gl in [('TopMetal1',126),('TopMetal2',134)]}
special=re.search(r'^SPECIALNETS \d+ ;(.*?)^END SPECIALNETS',d,re.M|re.S)[1];nets={e.split()[0]:e for e in re.findall(r'^\s*- (.*?) ;',special,re.M|re.S)}
source={'VDDA':('TopMetal1',946.02,389.34),'VDD':('TopMetal2',395.,354.66),'VSS':('TopMetal2',507.,334.66)};result={'scope':'Nominal centerline resistor approximation for routed TopMetal1/2 grid only. Source interfaces exclude pad internals, bond/package/board and regulator; macro interiors excluded. No loaded full-chip IR signoff.','inputs':{str(p.relative_to(R)) if p.is_relative_to(R) else str(p):sha(p) for p in [gds,deffile,tech]},'pdk_commit':(P/'COMMIT').read_text().strip(),'sheet_ohm_per_square':sheet,'via_ohm_per_cut':cut,'source_interfaces':source,'networks':{},'script_sha256':sha(Path(__file__))}
for net in ['VDDA','VDD','VSS']:
    segments=[];vias=[];all_vias=[]
    for route in re.split(r'(?:\+ ROUTED|\bNEW)\s+',nets[net])[1:]:
        header=route.split();layer=header[0];width=int(header[1])/units;matches=list(re.finditer(r'\(\s*([\d*-]+)\s+([\d*-]+)(?:\s+[\d-]+)?\s*\)',route));pts=[]
        for m in matches:pts.append(tuple(pts[-1][i] if m[i+1]=='*' else int(m[i+1])/units for i in (0,1)))
        if matches:
            tail=route[matches[-1].end():].strip().split();name=tail[0] if tail else ''
            if name in via_defs:
                v={'name':name,'point':pts[-1],**via_defs[name]};all_vias.append(v)
                if v['layers'][0]=='TopMetal1' and v['layers'][2]=='TopMetal2':vias.append(v)
        if layer not in regions or width<=0:continue
        for a,b in zip(pts,pts[1:]):
            if a==b:continue
            assert a[0]==b[0] or a[1]==b[1]
            shape=pya.Region(pya.DPath([pya.DPoint(*a),pya.DPoint(*b)],width).to_itype(ly.dbu))
            segments.append({'layer':layer,'a':a,'b':b,'width':width,'gds_full_width_coverage':(shape-regions[layer]).is_empty()})
    points=collections.defaultdict(set)
    for s in segments:points[s['layer']].update([s['a'],s['b']])
    for v in vias:
        for layer in ['TopMetal1','TopMetal2']:points[layer].add(v['point'])
    points[source[net][0]].add(source[net][1:])
    for term in terminals[net]:points['TopMetal1'].add(tuple(term['point_um']))
    def on(s,p):return min(s['a'][0],s['b'][0])-1e-6<=p[0]<=max(s['a'][0],s['b'][0])+1e-6 and min(s['a'][1],s['b'][1])-1e-6<=p[1]<=max(s['a'][1],s['b'][1])+1e-6
    # Same-layer centerline crossings and collinear endpoints split resistor edges.
    for i,s in enumerate(segments):
        for q in segments[i+1:]:
            if s['layer']!=q['layer']:continue
            if s['a'][0]==s['b'][0] and q['a'][1]==q['b'][1]:p=(s['a'][0],q['a'][1])
            elif s['a'][1]==s['b'][1] and q['a'][0]==q['b'][0]:p=(q['a'][0],s['a'][1])
            else:continue
            if on(s,p) and on(q,p):points[s['layer']].add(p)
    nodes={};edges={}
    def node(layer,p):
        key=(layer,round(p[0],6),round(p[1],6))
        if key not in nodes:nodes[key]=len(nodes)
        return nodes[key]
    def edge(a,b,res):
        if a==b:return
        pair=tuple(sorted([a,b]));edges[pair]=min(edges.get(pair,float('inf')),res) # overlapping duplicate geometry is not parallel metal
    for s in segments:
        pp=sorted(p for p in points[s['layer']] if on(s,p))
        for a,b in zip(pp,pp[1:]):edge(node(s['layer'],a),node(s['layer'],b),sheet[s['layer']]*(abs(a[0]-b[0])+abs(a[1]-b[1]))/s['width'])
    disconnected_vias=[]
    for v in vias:
        if not all(any(s['layer']==layer and on(s,v['point']) for s in segments) for layer in ['TopMetal1','TopMetal2']):disconnected_vias.append(v);continue
        edge(node('TopMetal1',v['point']),node('TopMetal2',v['point']),v['R_ohm'])
    src=node(source[net][0],source[net][1:]);rr=[];cc=[];vv=[]
    for (i,j),r in edges.items():rr += [i,j];cc += [j,i];vv += [r,r]
    graph=coo_matrix((vv,(rr,cc)),shape=(len(nodes),len(nodes))).tocsr();_,labels=connected_components(graph);keep=[i for i in range(len(nodes)) if labels[i]==labels[src] and i!=src];index={old:new for new,old in enumerate(keep)};ri=[];ci=[];va=[]
    for (i,j),r in edges.items():
        if labels[i]!=labels[src]:continue
        g=1/r
        for v in [i,j]:
            if v!=src:ri.append(index[v]);ci.append(index[v]);va.append(g)
        if i!=src and j!=src:
            ri.extend([index[i],index[j]]);ci.extend([index[j],index[i]]);va.extend([-g,-g])
    G=coo_matrix((va,(ri,ci)),shape=(len(keep),len(keep))).tocsc();solve=splu(G);short=dijkstra(graph,indices=src);terminal_rows=[]
    for term in terminals[net]:
        key=('TopMetal1',*term['point_um']);idx=nodes.get(key);row=dict(term)
        if idx is None or labels[idx]!=labels[src]:row.update(status='not run',reason='Centerline approximation does not connect this terminal')
        else:
            b=np.zeros(len(keep));b[index[idx]]=1;v=solve.solve(b)
            stack=[via for via in all_vias if via['point']==tuple(term['point_um']) and via['layers'][2]!='TopMetal2'];unique={via['name']:via for via in stack}
            row.update(status='passed',mesh_effective_R_ohm=float(v[index[idx]]),mesh_shortest_path_R_ohm=float(short[idx]),stack_R_ohm=sum(x['R_ohm'] for x in unique.values()),stack_vias=list(unique.values()),linear_residual_max=float(np.max(abs(G@v-b))))
            if 'jog_extent_um' in term:
                length=term['jog_extent_um'][1]-term['jog_extent_um'][0];layer=term['access'].split()[0]
                width=.5 if layer=='Metal2' else None
                row['jog_full_length_um']=length;row['jog_R_assuming_0p5um_width_ohm']=sheet[layer]*length/width if width else None
        terminal_rows.append(row)
    result['networks'][net]={'segments':segments,'grid_nodes':len(nodes),'grid_edges':len(edges),'source_connected_nodes':len(keep)+1,'omitted_vias_not_on_both_centerlines':disconnected_vias,'full_width_GDS_coverage_passed':all(s['gds_full_width_coverage'] for s in segments),'terminals':terminal_rows}
(out/'mesh.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({net:{'coverage':v['full_width_GDS_coverage_passed'],'omitted_vias':len(v['omitted_vias_not_on_both_centerlines']),'terminals':[{k:t.get(k) for k in ['name','status','mesh_effective_R_ohm','mesh_shortest_path_R_ohm','stack_R_ohm']} for t in v['terminals']]} for net,v in result['networks'].items()},indent=2))

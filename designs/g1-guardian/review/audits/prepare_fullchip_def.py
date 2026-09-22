#!/usr/bin/env python3
"""Prepare isolated unrouted full-chip DEF; preserve every original terminal.

This is routing input, not a completed layout. Original routes are deliberately
excluded from the derived view after moving instances; the source is untouched.
"""
import argparse
import collections
import hashlib
import json
import math
import os
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
DESIGN = HERE.parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def section(text, name):
    match = re.search(r'^'+name+r' (\d+) ;\n(.*?)^END '+name+r'\n', text, re.M | re.S)
    assert match, name
    rows = re.findall(r'^\s+- (.*?);', match[2], re.M | re.S)
    assert len(rows) == int(match[1]), name
    return match, rows


def overlap(a, b):
    return min(a[2], b[2]) > max(a[0], b[0]) and min(a[3], b[3]) > max(a[1], b[1])


def dbbox(values):
    return [round(v*1000) for v in values]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--placement', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0)) == 1
    a.output.mkdir(parents=True)
    (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    source = DESIGN/'blocks/g1_padring/flow/runs/assembly-1350/final/def/g1_chip_top.def'
    assert sha(source) == '948e720bd27b58f5b2b200c65d4c18483444937b77633a75504778c13b32297b'
    packfile = HERE/'coordinated-bbox-pack-20260922-r4.json'
    pack = json.loads(packfile.read_text())
    meta = json.loads((a.placement/'analysis.json').read_text())
    assert sha(packfile) == meta['pack_sha256']
    assert meta['status'] == 'passed source-preserving core placement'
    text = source.read_text()
    _, original = section(text, 'COMPONENTS')
    assert len(original) == 4884
    comps = {}
    for row in original:
        fields = row.split()
        match = re.search(r'\+ (?:FIXED|PLACED) \( (\d+) (\d+) \) (\w+)', row)
        assert match and fields[0] not in comps
        comps[fields[0]] = dict(master=fields[1], xy=[int(match[1]), int(match[2])], orient=match[3], raw=row)
    decap_lookup = {}; local_pins = {}
    for row in meta['decaps']:
        key = (row['cell'], tuple(row['pins']['VDD']['original_dbu']), tuple(row['pins']['VSS']['original_dbu']))
        assert key not in decap_lookup
        decap_lookup[key] = row
        pins = {name: tuple(pin['local_dbu']) for name,pin in row['pins'].items()}
        assert row['cell'] not in local_pins or local_pins[row['cell']] == pins
        local_pins[row['cell']] = pins
    targets = {m['name']: m for m in pack['macros']}
    macro_lookup = {(m['source_cell'], m['original_transform']): m for m in meta['macros']}
    # The saved native placement, not enumeration assumptions, binds all three LSs.
    macro_lookup[('g1_bgr', 'r0 645000,862000')] = targets['g1_bgr_candidate']
    macro_lookup[('g1_sense', 'r0 733000,440000')] = targets['g1_sense_candidate']
    assert len(macro_lookup) == 12
    pdk = Path('/foss/pdks/ihp-sg13g2')
    assert (pdk/'COMMIT').read_text().strip() == '84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    stdlef = pdk/'libs.ref/sg13g2_stdcell/lef/sg13g2_stdcell.lef'
    sizes = {}
    for name, body in re.findall(r'^MACRO (\S+)\n(.*?)^END \1$', stdlef.read_text(), re.M | re.S):
        s = re.search(r'\bSIZE ([\d.]+) BY ([\d.]+) ;', body)
        if s:
            sizes[name] = [round(float(v)*1000) for v in s.groups()]
    # Reconstruct the original greedy capacity slots, then reserve the exact
    # first4662 used by the proven native placement. No decap is removed.
    obstacles = [[b[0]-3000,b[1]-3000,b[2]+3000,b[3]+3000] for b in [dbbox(m['bbox_um']) for m in pack['macros']]]
    obstacles += [dbbox(c['bbox_um']) for c in pack['port_corridors']]
    obstacles += [dbbox(b) for b in pack['PDN_access_lane_reservations_um']]
    slots = []
    for row in range(203):
        y = 324000+row*3780
        if y+3780 > 1087000:
            break
        site = 0
        while site < 1600:
            x = 327360+site*480
            b = [x,y,x+3360,y+3780]
            if b[2] > 1087000:
                break
            blocked = [o for o in obstacles if overlap(b,o)]
            if blocked:
                site = max(site+1, math.ceil((max(o[2] for o in blocked)-327360)/480))
            else:
                slots.append(dict(row=row, site=site, bbox=b, orient='FS' if row%2 else 'N'))
                site += 7
    assert len(slots) == pack['available_decap8_sites']
    for expected, row in zip(slots, pack['decap_placements']):
        assert expected['row'] == row['row'] and expected['site'] == row['site']
    # Keep narrow native glue cells contiguous on each row. Giving every small
    # cell a full decap8 slot creates artificial sub-minimum NWell gaps.
    free_runs=[]
    for slot in slots[4662:]:
        x,y,right,top=slot['bbox']
        if free_runs and free_runs[-1]['row']==slot['row'] and free_runs[-1]['right']==x:
            free_runs[-1]['right']=right
        else:
            free_runs.append(dict(row=slot['row'],x=x,y=y,right=right,orient=slot['orient']))
    changes = []; counts = collections.Counter(); seen_decaps = set(); seen_macros = set()
    for name, comp in comps.items():
        master = comp['master']; x,y = comp['xy']; old = [x,y,comp['orient']]
        if master.startswith('sg13g2_decap_'):
            assert comp['orient'] in ('N','FS')
            w,h = sizes[master]
            def native_pin(name):
                px,py = local_pins[master][name]
                return (x+px,y+(py if comp['orient']=='N' else h-py))
            vdd = native_pin('VDD'); vss = native_pin('VSS')
            key = (master,vdd,vss); row = decap_lookup[key]
            assert row['index'] not in seen_decaps
            seen_decaps.add(row['index'])
            box = dbbox(row['intended_LEF_bbox_um'])
            comp.update(xy=box[:2],orient='FS' if row['orientation']=='MX' else 'N')
            kind = 'retained_decap'
        elif master.startswith('g1_'):
            assert comp['orient'] == 'N'
            key = (master,'r0 %d,%d'%(x,y)); target = macro_lookup[key]
            assert key not in seen_macros
            seen_macros.add(key)
            box = dbbox(target['bbox_um'])
            orientation = targets[target['name']]['orientation']
            comp.update(xy=box[:2],orient='W' if orientation=='R90' else 'N')
            kind = 'retained_macro'
        elif name.startswith(('IO_', 'pad')):
            comp['xy'] = [x+(64000 if x>=1029000 else 0), y+(64000 if y>=1029000 else 0)]
            kind = 'retained_IO'
        else:
            assert master in ('sg13g2_tiehi','sg13g2_antennanp','sg13g2_fill_1','sg13g2_fill_2'),master
            w,h = sizes[master]
            assert w<=3360 and h==3780
            run=next(run for run in free_runs if run['right']-run['x']>=w)
            comp.update(xy=[run['x'],run['y']],orient=run['orient'])
            run['x']+=w
            kind = 'retained_glue'
        counts[kind] += 1
        changes.append(dict(instance=name,master=master,old=old,new=comp['xy']+[comp['orient']],kind=kind))
    assert counts == dict(retained_decap=4662,retained_macro=12,retained_IO=144,retained_glue=66)
    assert len(seen_decaps)==4662 and len(seen_macros)==12
    # Extend each IO side by exactly64um using unmodified native filler masters.
    added = []
    for side,orient in [('SOUTH','N'),('NORTH','FS'),('EAST','W'),('WEST','FW')]:
        offset = 1029000
        for i,width in enumerate([20000,20000,20000,2000,2000]):
            name = 'IO_EXPAND_'+side+'_'+str(i)
            master = 'sg13g2_Filler4000' if width==20000 else 'sg13g2_Filler400'
            xy = ([offset,141000 if side=='SOUTH' else 1093000] if side in ('SOUTH','NORTH')
                  else [141000 if side=='WEST' else 1093000,offset])
            assert name not in comps
            comps[name] = dict(master=master,xy=xy,orient=orient)
            added.append(dict(instance=name,master=master,xy=xy,orient=orient,width_dbu=width))
            offset += width
        assert offset == 1093000
    output_components = ['    - '+name+' '+v['master']+' + FIXED ( %d %d ) %s ;'%(*v['xy'],v['orient']) for name,v in comps.items()]
    cmatch,_ = section(text,'COMPONENTS')
    text = text[:cmatch.start()]+'COMPONENTS %d ;\n'%len(comps)+'\n'.join(output_components)+'\nEND COMPONENTS\n'+text[cmatch.end():]
    connectivity = {}
    for kind in ['SPECIALNETS','NETS']:
        match, rows = section(text,kind); newrows=[]; fingerprints={}
        for row in rows:
            name = row.split()[0]
            head = re.split(r'\+ (?:ROUTED|FIXED|COVER)\b',row,maxsplit=1)[0].strip()
            assert not re.search(r'\b(?:NEW|RECT|SHAPE)\b',head)
            terminals = re.findall(r'\(\s*(\S+)\s+(\S+)\s*\)',head)
            fingerprints[name] = terminals
            if kind=='SPECIALNETS' and name in ('VDD','VSS','IOVDD','IOVSS'):
                pin = dict(VDD='vdd',VSS='vss',IOVDD='iovdd',IOVSS='iovss')[name]
                addition = ' '.join('( '+r['instance']+' '+pin+' )' for r in added)
                head = re.sub(r'\s+\+ USE', ' '+addition+' + USE',head,count=1)
                assert len(re.findall(r'\(\s*(\S+)\s+(\S+)\s*\)',head))==len(terminals)+20
            newrows.append('    - '+head+' ;')
        connectivity[kind] = fingerprints
        text = text[:match.start()]+kind+' %d ;\n'%len(rows)+'\n'.join(newrows)+'\nEND '+kind+'\n'+text[match.end():]
    pmatch,_ = section(text,'PINS')
    pins = re.sub(r'\+ FIXED \( (\d+) (\d+) \)',lambda m:'+ FIXED ( %d %d )'%(int(m[1])+(64000 if int(m[1])>=1029000 else 0),int(m[2])+(64000 if int(m[2])>=1029000 else 0)),pmatch[0])
    text = text[:pmatch.start()]+pins+text[pmatch.end():]
    text = text.replace('DIEAREA ( 0 0 ) ( 1350000 1350000 ) ;','DIEAREA ( 0 0 ) ( 1414000 1414000 ) ;')
    # Old fragmented rows/routes are not valid at the new placement. Explicit
    # site rows cover only qualified capacity slots; all current cells fixed.
    text = re.sub(r'^ROW .*\n','',text,flags=re.M)
    rowtext = '\n'.join('ROW G1_SLOT_%d CoreSite %d %d %s DO 7 BY 1 STEP 480 0 ;'%(i,*s['bbox'][:2],s['orient'])for i,s in enumerate(slots))+'\n'
    text = text.replace('TRACKS X 480',rowtext+'TRACKS X 480',1)
    text = re.sub(r'^(TRACKS [XY] (\d+) DO )\d+( STEP (\d+) LAYER \w+ ;)',lambda m:m[1]+str((1414000-int(m[2]))//int(m[4])+1)+m[3],text,flags=re.M)
    text = re.sub(r'^(GCELLGRID [XY] 0 DO )\d+( STEP 7200 ;)',r'\g<1>197\2',text,flags=re.M)
    assert not re.search(r'\+ (?:ROUTED|COVER)\b|\bNEW Metal',text)
    assert len(section(text,'COMPONENTS')[1])==4904
    for kind in ['SPECIALNETS','NETS']:
        for row in section(text,kind)[1]:
            name = row.split()[0]; terminals = re.findall(r'\(\s*(\S+)\s+(\S+)\s*\)',row)
            old = connectivity[kind][name]
            assert terminals[:len(old)]==old, (kind,name)
            assert all(t[0] in comps or t[0] in ('PIN','*') for t in terminals)
    dest = a.output/'g1_chip_top_unrouted.def';dest.write_text(text)
    (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    result = dict(status='passed source-preserving unrouted DEF preparation',DEF_sha256=sha(dest),source_DEF_sha256=sha(source),
                  script_sha256=sha(Path(__file__)),pack_sha256=sha(packfile),placement_metadata_sha256=sha(a.placement/'analysis.json'),
                  stdcell_LEF_sha256=sha(stdlef),components=len(comps),retained_counts=dict(counts),added_native_IO_fillers=added,
                  changes=changes,original_connectivity=connectivity,original_terminal_sequence_retained='passed',
                  not_run=['OpenROAD import and instance/pin roundtrip','native IO/glue GDS integration and stock checks',
                           'PDN and signal routing','fullchip LVS/PEX/DRC/density/antenna/STA/currentIR','electrical adoption'])
    (a.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items()if k not in ('changes','original_connectivity')},indent=2))


if __name__ == '__main__':
    main()

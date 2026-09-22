#!/usr/bin/env python3
"""Read-only physical net/plate/contact coverage of the frozen saved LVSDB."""
import argparse
import copy
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import time

import klayout.db as kdb
from google.protobuf.json_format import MessageToDict
from klayout_pex.env import Env
from klayout_pex.kpex_cli import KpexCLI
from klayout_pex.klayout.lvsdb_extractor import KLayoutExtractionContext
from klayout_pex.tech_info import TechInfo
from export_sense_kpex_api import materialize, sha
from build_source_faithful_buffer import full_nets


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('lvsdb', 'view', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    assert os.sched_getaffinity(0) == {7} and kdb.__version__ == '0.30.9'
    original = sha(args.lvsdb)
    assert original == '95e8683146bc38ecf9a78e3fde3fe8541c9a888707a77c378b816c9136a1af67'
    manifest = json.loads((args.view / 'manifest.json').read_text())
    assert sha(args.view / 'g1_sense_pex_view.gds') == manifest['GDS_sha256']
    source=Path(__file__).resolve().parents[2]/'reports/resume-server-20260922/gm4comp3-qualified-source.spice'
    assert sha(source)==manifest['source_sha256']=='baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877'
    blocks={block.split()[1]:block.splitlines() for block in re.findall(r'(?ms)^\.subckt .*?^\.ends[^\n]*',source.read_text())}
    def native_nodes(line):
        words=line.split()
        if not words or not words[0].startswith('X'):return []
        return words[1:5] if 'sg13_hv_' in line else words[1:4] if 'rppd' in line else words[1:3] if 'cap_cmim' in line else []
    top_nodes={node for line in blocks['g1_sense'] for node in native_nodes(line)}
    top_nodes.update(blocks['g1_sense'][0].split()[2:])
    expected=set(top_nodes)
    for line in blocks['g1_sense']:
        words=line.split()
        if words and words[-1] in ('g1_ota','g1_ota_main_candidate'):
            definition=blocks[words[-1]];ports=dict(zip(definition[0].split()[2:],words[1:-1]))
            nodes={node for item in definition for node in native_nodes(item)}
            expected.update(ports.get(node,words[0]+'/'+node) for node in nodes)
    assert len(top_nodes)==101 and len(expected)==134
    old_names={row['source_net'] for row in manifest['labels']}
    assert expected-old_names=={'XBUF/cz','XREF/cz'} and old_names<=expected
    # Independent native resistor-head and MIM-plate geometry, translated from
    # the frozen buffer. No extracted-name-based assignment of these new nets.
    buffer_path=Path(__file__).with_name('source-faithful-buffer-20260922-r2')/'g1_ota_source_faithful.gds'
    assert sha(buffer_path)=='320df90ee046c73b628005da9384c80fbd21a715a39b0e8b96b10923726fc500'
    buf_layout=kdb.Layout();buf_layout.read(str(buffer_path));buf=buf_layout.top_cell()
    rb=materialize(kdb.Region(buf.begin_shapes_rec(buf_layout.layer(128,0)))).bbox()
    cb=materialize(kdb.Region(buf.begin_shapes_rec(buf_layout.layer(36,0)))).bbox()
    assert (rb.width(),rb.height())==(1000,6200) and (cb.width(),cb.height())==(23000,23000)
    physical=kdb.Layout();physical.read(str(args.view/'g1_sense_pex_view.gds'));physical_top=physical.top_cell()
    complete_probes=copy.deepcopy(manifest['terminal_audit']['probes']);added=[]
    for instance,dx,out in [('XBUF',15.5,'vped'),('XREF',135.5,'vref_buf')]:
        dy=185.8
        for device,terminal,net,layer,x,y in [
            ('XRZ','end0',instance+'/out1',8,rb.center().x*.001,rb.bottom*.001-.28),
            ('XRZ','end1',instance+'/cz',8,rb.center().x*.001,rb.top*.001+.28),
            ('XCC','top',instance+'/cz',126,cb.left*.001+1,cb.bottom*.001+1),
            ('XCC','bottom',out,67,cb.left*.001+1,cb.bottom*.001+1)]:
            added.append(dict(device=instance+'/'+device,terminal=terminal,net=net,layer=layer,point_um=[x+dx,y+dy]))
    complete_probes.extend(added)
    graph=full_nets(physical_top,complete_probes)
    assert graph['status']=='passed' and {row['net'] for row in graph['probes']}==expected
    labels=copy.deepcopy(manifest['labels'])
    for net in sorted(expected-old_names):
        probe=next(row for row in graph['probes'] if row['net']==net and row['terminal']=='end1')
        labels.append(dict(source_net=net,pex_label=None,layer=probe['layer'],point_um=probe['point_um'],
                           witness_device=probe['device'],witness_terminal=probe['terminal'],
                           original_physical_net=probe['physical_net']))
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / 'script_snapshot.py').write_bytes(Path(__file__).read_bytes())
    cli_args = KpexCLI.parse_args(['--pdk', 'ihp-sg13g2', '--threads', '1', '--2.5D', '--mode', 'CC',
                                   '--lvsdb', str(args.lvsdb), '--out_dir', str(args.output / 'api')], Env.from_os_environ())
    KpexCLI.validate_args(cli_args)
    cli = KpexCLI()
    tech = TechInfo.from_json(cli_args.tech_pbjson_path, dielectric_filter=cli_args.dielectric_filter)
    db = cli.create_lvsdb(cli_args)
    contexts = {name: KLayoutExtractionContext.prepare_extraction(db, cli_args.effective_cell_name, tech, blackbox)
                for name, blackbox in (('blackbox', True), ('whitebox', False))}
    raw = {db.layer_name(index): materialize(db.layer_by_index(index)) for index in db.layer_indexes()}
    all_layers = {}
    for name, context in contexts.items():
        all_layers[name] = {layer.lvs_layer_name: materialize(layer.region)
                            for layers in context.extracted_layers.values() for layer in layers.source_layers}
    inventory = []
    for name in sorted(set(all_layers['blackbox']) | set(all_layers['whitebox'])):
        before = all_layers['whitebox'].get(name, kdb.Region())
        after = all_layers['blackbox'].get(name, kdb.Region())
        info = tech.computed_layer_info_by_name.get(name)
        inventory.append(dict(name=name, whitebox_um2=before.area()*1e-6, blackbox_um2=after.area()*1e-6,
                              excluded_um2=materialize(before-after).area()*1e-6,
                              technology=MessageToDict(info) if info else None))
    context = contexts['blackbox']
    circuit = db.netlist().circuit_by_name(cli_args.effective_cell_name)
    # Build explicit property-bound metal polygons. No textual net-name guess.
    polys = {}
    for pair, layers in context.extracted_layers.items():
        if pair not in {(row['layer'], 0) for row in labels}:
            continue
        polys[pair] = []
        for layer in layers.source_layers:
            iterator, transform = layer.region.begin_shapes_rec()
            while not iterator.at_end():
                shape = iterator.shape()
                polys[pair].append((shape.property('net'), transform * iterator.trans() * shape.polygon))
                iterator.next()
    def hits_at(layer, point_um):
        point = kdb.DPoint(*point_um).to_itype(.001)
        witness = kdb.Region(kdb.Box(point.x-1, point.y-1, point.x+1, point.y+1))
        return sorted({net for net, polygon in polys.get((layer, 0), [])
                       if not materialize(kdb.Region(polygon) & witness).is_empty()})
    mapping = []
    for label in labels:
        hits = hits_at(label['layer'], label['point_um'])
        original_hits = list(hits)
        alternate = None
        if not hits:
            for probe in manifest['terminal_audit']['probes']:
                if probe['net'] != label['source_net']:
                    continue
                layer = 8 if probe['layer'] == 501 else probe['layer']
                proposed = hits_at(layer, probe['point_um'])
                if len(proposed) == 1:
                    hits = proposed
                    alternate = dict(layer=layer, point_um=probe['point_um'], device=probe['device'],
                                     terminal=probe['terminal'], original_physical_net=probe['physical_net'])
                    assert alternate['original_physical_net'] == label['original_physical_net']
                    break
        mapping.append(dict(**label, original_witness_hits=original_hits, alternate_connected_witness=alternate,
                            extracted_nets=hits, status='passed' if len(hits) == 1 else 'failed'))
    mapping_pass = all(row['status'] == 'passed' for row in mapping)
    mapping_pass &= len({row['extracted_nets'][0] for row in mapping if row['extracted_nets']}) == len(mapping)
    native_terminals=[]
    for instance,output in [('XBUF','vped'),('XREF','vref_buf')]:
        cz=next(row['extracted_nets'][0] for row in mapping if row['source_net']==instance+'/cz')
        out1=next(row['extracted_nets'][0] for row in mapping if row['source_net']==instance+'/out1')
        matches={'R':[],'C':[]}
        for dev in circuit.each_device():
            cls=dev.device_class();terms={t.name:dev.net_for_terminal(t.name).expanded_name() for t in cls.terminal_definitions()}
            if cls.name=='cap_cmim' and set(terms.values())=={cz,output}:
                assert dev.parameter('w')==23 and dev.parameter('l')==23
                matches['C'].append(dict(id=dev.id(),terminals=terms,w=23,l=23))
            if cls.name=='rppd' and set(terms.values())=={cz,out1,'vss'}:
                assert abs(dev.parameter('w')-1)<1e-10 and abs(dev.parameter('l')-6.2)<1e-10
                matches['R'].append(dict(id=dev.id(),terminals=terms,w=1,l=6.2))
        assert all(len(rows)==1 for rows in matches.values()),matches
        native_terminals.append(dict(instance=instance,CZ_extracted=cz,matches=matches))
    contact = raw.get('cont_drw', kdb.Region())
    typed = kdb.Region()
    for name in ('cont_poly_con', 'cont_nsd_con', 'cont_psd_con'):
        typed += all_layers['blackbox'].get(name, kdb.Region())
    missing = materialize(contact - typed)
    taps = raw.get('ptap', kdb.Region()) + raw.get('ntap', kdb.Region())
    in_taps = materialize(missing & taps)
    result = dict(status='passed read-only coverage audit', script_sha256=sha(Path(__file__)),
                  LVSDB_sha256=original, view_manifest_sha256=sha(args.view/'manifest.json'),
                  technology_sha256=sha(Path(cli_args.tech_pbjson_path)),
                  source_net_mapping_status='passed' if mapping_pass else 'failed', mapping=mapping,
                  source_net_count=len(expected),source_top_net_count=len(top_nodes),source_nets=sorted(expected),
                  original_probe_net_count=132,original_complete_source_net_claim='failed; omitted two buffer CZ nets',
                  added_native_RC_probes=added,complete_physical_graph=graph,
                  native_RC_extracted_terminal_crosscheck=native_terminals,
                  layer_inventory=inventory,
                  contact=dict(raw_um2=contact.area()*1e-6, typed_um2=materialize(typed).area()*1e-6,
                               missing_um2=missing.area()*1e-6, missing_in_taps_um2=in_taps.area()*1e-6,
                               missing_outside_taps_um2=materialize(missing-taps).area()*1e-6),
                  process_stack=MessageToDict(tech.tech.process_stack),
                  layer_definitions=[MessageToDict(layer) for layer in tech.tech.layers],
                  tool_availability={name: bool(shutil.which(name)) for name in ('FasterCap', 'fastercap', 'fastcap')},
                  no_extraction_launched=True, no_geometry_written=True, completeness='not qualified')
    assert sha(args.lvsdb) == original
    (args.output/'summary.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('mapping','layer_inventory','process_stack','layer_definitions')}, indent=2))


if __name__ == '__main__':
    main()

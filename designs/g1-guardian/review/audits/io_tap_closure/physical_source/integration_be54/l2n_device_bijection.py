#!/usr/bin/env python3
"""Decode native L2N document IDs independently of reader allocation IDs."""
import collections
import json
import math
import shlex
import struct


def atom(text):
    out=shlex.split(text);assert len(out)==1,text
    return out[0]


def document_devices(path):
    abstracts={};circuits={};circuit=None;device=None
    with path.open() as stream:
        for line in stream:
            if line.startswith('device('):
                items=shlex.split(line[len('device('):].strip())
                assert len(items)==2,items
                assert items[0] not in abstracts;abstracts[items[0]]=items[1]
            if line.startswith('circuit('):
                circuit=atom(line[len('circuit('):].strip());assert circuit not in circuits
                circuits[circuit]=[]
            elif circuit is not None and line==')\n':
                assert device is None;circuit=None
            elif circuit is not None and line.startswith(' device('):
                assert device is None
                items=shlex.split(line[len(' device('):].strip());assert len(items)==2
                device=dict(id=int(items[0]),model=abstracts.get(items[1],items[1]),name='',parameters={},terminals={})
            elif device is not None:
                if line==' )\n':
                    circuits[circuit].append(device);device=None
                elif line.startswith('  name('):device['name']=atom(line[len('  name('):].strip()[:-1])
                elif line.startswith('  param('):
                    items=shlex.split(line[len('  param('):].strip()[:-1]);assert len(items)==2
                    assert items[0] not in device['parameters'];device['parameters'][items[0]]=float(items[1])
                elif line.startswith('  terminal('):
                    items=shlex.split(line[len('  terminal('):].strip()[:-1]);assert len(items) in (1,2)
                    assert items[0] not in device['terminals'];device['terminals'][items[0]]=None if len(items)==1 else int(items[1])
    assert circuit is None and device is None
    return circuits


def actual_device(d):
    return dict(id=d.id(),model=d.device_class().name,name=d.name,
        parameters={p.name:d.parameter(p.name) for p in d.device_class().parameter_definitions()},
        terminals={t.name:None if d.net_for_terminal(t.name) is None else d.net_for_terminal(t.name).cluster_id
            for t in d.device_class().terminal_definitions()})


def check_record(doc,actual):
    assert doc['model']==actual['model'] and doc['name']==actual['name']
    assert doc['terminals']==actual['terminals']
    assert set(doc['parameters'])==set(actual['parameters'])
    assert all(struct.pack('>d',v)==struct.pack('>d',actual['parameters'][p]) for p,v in doc['parameters'].items())


def bind(snapshot,nl,rows,output):
    docs=document_devices(snapshot);actual={c.name:[actual_device(d) for d in c.each_device()] for c in nl.each_circuit()}
    assert set(docs)==set(actual)
    grouped=collections.defaultdict(dict)
    for cn,di,dn,cl,pn,h in rows:
        identity=(cn,di,dn,cl);assert pn not in grouped[identity];grouped[identity][pn]=h
    mapping={};ledger=[];negative_swap=None
    for cn,records in docs.items():
        decoded=actual[cn];assert len(records)==len(decoded)
        assert len({r['id'] for r in records})==len(records)
        assert len({r['id'] for r in decoded})==len(decoded)
        for index,(doc,current) in enumerate(zip(records,decoded)):
            check_record(doc,current)
            old=(cn,doc['id'],doc['name'],doc['model']);new=(cn,current['id'],current['name'],current['model'])
            assert old in grouped and old not in mapping and set(grouped[old])==set(doc['parameters'])
            for pn,h in grouped[old].items():
                precise=struct.unpack('>d',bytes.fromhex(h))[0];assert math.isfinite(precise)
                # Native writer's documented/observed 12-significant-digit
                # representation; this is a serialization check, not tolerance.
                assert float(format(precise,'.12g'))==doc['parameters'][pn],(old,pn)
            mapping[old]=new
            if old!=new:ledger.append(dict(circuit=cn,document_device_id=doc['id'],reader_device_id=current['id'],
                model=doc['model'],name=doc['name'],terminals=doc['terminals']))
            if negative_swap is None:
                for other in decoded[index+1:]:
                    if other['model']==current['model'] and (other['terminals']!=current['terminals'] or other['parameters']!=current['parameters']):
                        rejected=False
                        try:check_record(doc,other)
                        except AssertionError:rejected=True
                        assert rejected;negative_swap=dict(circuit=cn,document_id=doc['id'],wrong_reader_id=other['id']);break
    assert set(mapping)==set(grouped) and len(set(mapping.values()))==len(mapping)
    assert negative_swap is not None
    remapped=[list(mapping[tuple(r[:4])])+r[4:] for r in rows]
    assert len(remapped)==len(rows) and len({tuple(r[:5]) for r in remapped})==len(rows)
    # Missing/duplicate device identities must not meet the complete bijection.
    assert len(mapping)-1!=len(grouped)
    duplicate=list(mapping.values());duplicate[-1]=duplicate[0]
    assert len(set(duplicate))!=len(grouped)
    (output/'document_reader_bijection.json').write_text(json.dumps(dict(
        status='passed complete document-to-reader device bijection; lookup keys only',
        circuits=len(docs),devices=len(mapping),parameters=len(rows),renamed_ids=ledger,
        all_document_parameter_tokens_and_terminal_net_ids_exact=True,
        all_sidecar_values_match_native_12digit_encoding=True,negative_swapped_record_rejected=negative_swap,
        negative_missing_and_duplicate_identity_rejected=True,
        live_net_ids_and_device_ids_unchanged=True),indent=2)+'\n')
    return remapped

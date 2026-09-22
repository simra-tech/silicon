#!/usr/bin/env python3
"""Synthetic exact-identity, property, hierarchy and negative adapter controls."""
import argparse
import hashlib
import json
import os
from pathlib import Path
from types import SimpleNamespace
import klayout.db as kdb
from computed_layer_geometry_adapter import ExactComputedLayerBuilder


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert not a.output.exists() and os.sched_getaffinity(0)=={6}
    layer=kdb.Region();layer.enable_properties()
    layer.insert(kdb.PolygonWithProperties(kdb.Polygon(kdb.Box(0,0,10,10)),{'net':'A','owner':11}))
    layer.insert(kdb.PolygonWithProperties(kdb.Polygon(kdb.Box(20,0,30,10)),{'net':'B','owner':12}))
    other=kdb.Region(kdb.Box(40,0,50,10))
    source=SimpleNamespace(source_layers=[SimpleNamespace(lvs_layer_name='part_a',region=layer),
                                         SimpleNamespace(lvs_layer_name='part_b',region=other)])
    obj=object.__new__(ExactComputedLayerBuilder)
    obj.tech_info=SimpleNamespace(gds_pair_for_computed_layer_name={'part_a':(1,0),'part_b':(1,0),'absent':(1,0)})
    obj.pex_context=SimpleNamespace(extracted_layers={(1,0):source})
    got=obj.shapes_of_layer('part_a');assert got.area()==200 and len(list(got.each()))==2
    bynet=obj.shapes_of_net('part_a','A');poly,=list(bynet.each())
    assert poly.area()==100 and poly.property('net')=='A' and poly.property('owner')==11
    assert obj.shapes_of_net('part_a','unknown').is_empty()
    assert obj.shapes_of_layer('absent') is None
    assert obj.shapes_of_net('absent','A') is None
    # Caller mutation must not change original backing region or sibling identity.
    got.clear();assert layer.area()==200 and obj.shapes_of_layer('part_b').area()==100
    source.source_layers.append(SimpleNamespace(lvs_layer_name='part_a',region=other))
    try:obj.shapes_of_layer('part_a')
    except AssertionError:duplicate_refused=True
    else:duplicate_refused=False
    assert duplicate_refused
    result=dict(status='passed',controls=['same-GDS distinct computed identity','net membership','all arbitrary properties retained',
                'unknown net empty','absent computed layer no GDS fallback','absent computed net no GDS fallback',
                'caller region mutation isolated','sibling identity held','ambiguous duplicate identity fails closed'],
                script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                adapter_sha256=hashlib.sha256(Path(__file__).with_name('computed_layer_geometry_adapter.py').read_bytes()).hexdigest(),
                geometry_only=True,no_solver=True)
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()

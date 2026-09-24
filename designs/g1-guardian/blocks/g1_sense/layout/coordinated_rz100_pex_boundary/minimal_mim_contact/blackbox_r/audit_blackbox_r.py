#!/usr/bin/env python3
"""Audit saved blackboxed native-CMIM R request, terminal binding and omissions."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def child(parent, name):
    matches = [c for c in parent.findall('./categories/category') if c.findtext('name') == name]
    assert len(matches) == 1, (name, len(matches))
    return matches[0]


def names(category):
    return [c.findtext('name') for c in category.findall('./categories/category')]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run', type=Path, required=True)
    p.add_argument('--receipt-log', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists()
    summary = json.loads((a.run / 'summary.json').read_text())
    assert summary['status'] == 'completed raw coupon extraction'
    assert summary['blackbox_devices'] and summary['inputs_unchanged']
    assert summary['mode'] == 'R' and summary['resistor_count'] == 0
    assert summary['capacitor_count'] == 0 and summary['unknown_layers'] == []
    report = a.run / 'native_report.rdb.gz'
    tree = ET.fromstring(gzip.decompress(report.read_bytes()))
    root = child(tree, '[R] Extraction Request')
    technology = child(root, '[R] Extraction Tech')
    conductors = names(child(technology, 'Conductors'))
    vias = names(child(technology, 'Vias'))
    devices = names(child(root, 'Devices'))
    assert devices == ['$1: cap_cmim']
    device_terminals = names(child(child(root, 'Devices'), devices[0]).find('./categories/category[name="Terminals"]'))
    # On this coupon, both source nets exist, but the blackboxed R request
    # contains no device-terminal landing records for either net.
    networks = child(root, 'Network Extraction Request')
    net_names = names(networks)
    assert net_names == ['Net top', 'Net bottom']
    per_net = {}
    for net in net_names:
        item = child(networks, net)
        per_net[net] = dict(pins=names(child(item, 'Pins')),
                            device_terminals=names(child(item, 'Device Terminals')),
                            layer_regions=names(child(item, 'Layer Regions')))
    extracted = child(child(tree, '[R] Extraction Result'), 'Networks')
    result_names = names(extracted)
    assert result_names == net_names
    log = a.receipt_log.read_text()
    assert 'Could not find a layer for device $1' in log
    assert 'terminal mim_top' in log and 'terminal mim_btm' in log
    result = dict(status='passed saved-request audit; blackbox R not terminal-qualified',
                  summary_sha256=sha(a.run / 'summary.json'),
                  report_sha256=sha(report), receipt_log_sha256=sha(a.receipt_log),
                  source_cdl_sha256=summary['CDL_sha256'],
                  source_gds_sha256=summary['GDS_sha256'],
                  blackbox_devices=True, source_device=devices,
                  request_conductors=conductors, request_vias=vias,
                  source_device_terminal_records=device_terminals,
                  net_request=per_net, extracted_networks=result_names,
                  extracted_resistor_count=0,
                  missing_terminal_layer_warnings=['mim_top on top', 'mim_btm on bottom'],
                  external_wire_via_R='not demonstrated by this coupon',
                  intrinsic_plate_R='not extracted',
                  full_macro_PEX='not qualified', electrical_adoption='not run')
    a.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ['status', 'request_conductors',
        'request_vias', 'source_device_terminal_records', 'net_request',
        'extracted_resistor_count']}))


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Read pinned OSDI 0.4 compatible-prefix descriptors without model evaluation."""
import argparse
import ctypes as C
import hashlib
import json
import os
from pathlib import Path


class Node(C.Structure):
    _fields_=[('name',C.c_char_p),('units',C.c_char_p),('residual_units',C.c_char_p),
              ('resist_residual_off',C.c_uint32),('react_residual_off',C.c_uint32),
              ('resist_limit_rhs_off',C.c_uint32),('react_limit_rhs_off',C.c_uint32),('is_flow',C.c_bool)]


class Pair(C.Structure):
    _fields_=[('node_1',C.c_uint32),('node_2',C.c_uint32)]


class DescriptorPrefix(C.Structure):
    _fields_=[('name',C.c_char_p),('num_nodes',C.c_uint32),('num_terminals',C.c_uint32),
              ('nodes',C.POINTER(Node)),('num_jacobian_entries',C.c_uint32),('jacobian_entries',C.c_void_p),
              ('num_collapsible',C.c_uint32),('collapsible',C.POINTER(Pair)),('collapsed_offset',C.c_uint32)]


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert not a.output.exists() and os.sched_getaffinity(0)=={7}
    root=Path('/foss/pdks/ihp-sg13g2')
    pins=json.loads(Path(__file__).with_name('psp-junction-source-equations-20260922-r1.json').read_text())
    rows=[]
    for rel,digest in pins['file_hashes'].items():
        if not rel.endswith('.osdi'):continue
        path=root/rel;assert hashlib.sha256(path.read_bytes()).hexdigest()==digest
        lib=C.CDLL(str(path));major=C.c_uint32.in_dll(lib,'OSDI_VERSION_MAJOR').value
        minor=C.c_uint32.in_dll(lib,'OSDI_VERSION_MINOR').value
        count=C.c_uint32.in_dll(lib,'OSDI_NUM_DESCRIPTORS').value
        assert (major,minor,count)==(0,4,1),(major,minor,count)
        descriptor_size=C.c_uint32.in_dll(lib,'OSDI_DESCRIPTOR_SIZE').value
        assert descriptor_size>=C.sizeof(DescriptorPrefix)
        d=DescriptorPrefix.in_dll(lib,'OSDI_DESCRIPTORS')
        assert 4<=d.num_nodes<=64 and d.num_terminals==4 and d.num_collapsible<64
        names=[d.nodes[i].name.decode() for i in range(d.num_nodes)]
        pairs=[{'from_index':d.collapsible[i].node_1,'to_index':d.collapsible[i].node_2,
                'from_name':names[d.collapsible[i].node_1],
                'to_name':'0' if d.collapsible[i].node_2==2**32-1 else names[d.collapsible[i].node_2]}
               for i in range(d.num_collapsible)]
        rows.append(dict(path=rel,sha256=digest,descriptor_name=d.name.decode(),
                         OSDI_version=[major,minor],descriptor_size=descriptor_size,nodes=names,collapsible=pairs))
    result=dict(status='passed read-only descriptor inventory; actual collapse flags not yet proved',
                source_header='https://raw.githubusercontent.com/imr/ngspice/ngspice-46/src/osdi/osdi.h',
                compatibility_loader='https://raw.githubusercontent.com/imr/ngspice/ngspice-46/src/osdi/osdiregistry.c',
                script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),descriptors=rows,
                model_setup='not run',model_evaluation='not run',internal_voltage_identity='not qualified')
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()

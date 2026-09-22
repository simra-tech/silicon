#!/usr/bin/env python3
"""Apply only source-declared analog pad aliases to saved physical observations."""
import argparse
import collections
import json
from pathlib import Path
import re
from hashlib import sha256

ROOT=Path(__file__).resolve().parents[4]


def sha(path):return sha256(path.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--observations',type=Path,required=True)
    p.add_argument('--prepared',type=Path,required=True)
    p.add_argument('--odb-check',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert not a.output.exists()
    observed=json.loads(a.observations.read_text());prepared=json.loads(a.prepared.read_text())
    odb=json.loads((a.odb_check/'analysis.json').read_text())
    assert sha(a.odb_check/'analysis.json')==observed['LEF_binding_sha256']
    assert prepared['DEF_sha256']==odb['source_DEF_sha256']
    verilog=ROOT/'designs/g1-guardian/blocks/g1_padring/ip/sg13g2_io_padbare/verilog/sg13g2_io.v'
    body,=re.findall(r'module sg13g2_IOPadAnalog\s*\(.*?\);(.*?)endmodule',verilog.read_text(),re.S)
    assert body.count('assign pad = padbare;')==body.count('assign padbare = pad;')==1
    components={r['instance']:r['master']for r in prepared['changes']}
    logical={}
    for line in (a.odb_check/'roundtrip.tsv').read_text().splitlines():
        fields=line.split('\t')
        if fields[0]=='CONN' and fields[2]!='PIN':
            key=tuple(fields[2:]);assert key not in logical;logical[key]=fields[1]
    observations={(r['instance'],r['pin']):r for r in observed['observations']}
    assert len(observations)==observed['terminal_observations']
    parents={name:name for name in logical.values()}
    def canonical(name):
        while parents[name]!=name:name=parents[name]
        return name
    aliases=[]
    for instance,master in components.items():
        if master!='sg13g2_IOPadAnalog':continue
        if (instance,'pad')not in logical or(instance,'padbare')not in logical:continue
        left=logical[instance,'pad'];right=logical[instance,'padbare']
        # Aliases come from the unchanged library assignment, not from which
        # observed shorts happen to occur. Verify both actual native terminals.
        lp=observations[instance,'pad']['clusters'];rp=observations[instance,'padbare']['clusters']
        assert len(lp)==len(rp)==1 and lp==rp,(instance,lp,rp)
        if left!=right:
            parents[canonical(right)]=canonical(left)
            aliases.append(dict(instance=instance,master=master,logical_nets=[left,right],actual_component=lp[0]))
    assert len(aliases)==8
    unexpected=[];expected=[]
    for merge in observed['unexpected_net_merges']:
        if len({canonical(name)for name in merge['logical_nets']})==1:expected.append(merge)
        else:unexpected.append(merge)
    passed=not observed['errors'] and not observed['signal_splits'] and not unexpected
    result=dict(status='passed source-aliased signal terminal connectivity'if passed else'failed source-aliased signal terminal connectivity',
                observation_sha256=sha(a.observations),source_GDS_sha256=observed['GDS_sha256'],
                prepared_sha256=sha(a.prepared),library_Verilog_sha256=sha(verilog),script_sha256=sha(Path(__file__)),
                aliases=aliases,source_expected_merges=expected,unexpected_merges=unexpected,
                original_raw_status=observed['status'],terminal_observations=observed['terminal_observations'],
                signal_splits=observed['signal_splits'],errors=observed['errors'],
                supply_components={k:v for k,v in observed['split_components'].items()if k in ('VDD','VSS','VDDA','IOVDD','IOVSS')},
                not_run=['full PDN connectivity','external BTerm physical binding','device-aware fullchip LVS',
                         'PEX and electrical adoption'],not_applicable=['padres aliasing or label-based physical joining'])
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
    raise SystemExit(0 if passed else 1)


if __name__=='__main__':main()

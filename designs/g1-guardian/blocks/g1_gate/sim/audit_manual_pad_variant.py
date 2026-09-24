#!/usr/bin/env python3
"""Independent R-token-only inverse for conditional pad sensitivities, not physical bounds."""
import hashlib,json,re
from decimal import Decimal,localcontext
from pathlib import Path

PARENT='c46e32249a04ed75d25d5f2b4f0b79304c25f7d85ce7628ee5a65b1734f43256'
VARIANTS={1:'b332d78f89653d03f8e9afe0865ddace98a06709fca093a22430bcd4d5fed854',
          2:'25a4317632da2ce5a06a76592922232b0864a57dac58fe4bee07931e55717efe'}

def digest(raw):return hashlib.sha256(raw).hexdigest()

def inverse(candidate,edits,count):
    lines=candidate.decode().splitlines(True);indices=[]
    for e in edits:
        i=e['line']-1;assert i not in indices;indices.append(i)
        assert lines[i]==e['after'] and e['after']!=e['before']
        a,n=re.subn(r'(?i)\bR=\S+','R=DECLARED',e['after'])
        b,m=re.subn(r'(?i)\bR=\S+','R=DECLARED',e['before'])
        assert n==m==1 and a==b,'Change outside one explicit R token'
        lines[i]=e['before']
    assert len(indices)==count
    return ''.join(lines).encode()

def audit(pad,summary,original_proof,factor):
    raw=pad.read_bytes();proof=json.loads(summary.read_text());old=json.loads(original_proof.read_text())
    assert factor in VARIANTS and digest(raw)==VARIANTS[factor]
    assert proof['parent_SPI_sha256']==old['candidate_sha256']==PARENT
    assert old['status'].startswith('passed source-only') and old['original_parameter_and_tap_R_preservation'] and old['exact_original_library_prefix']
    assert all(r['wrong_bulk_rejected'] and r['missing_bulk_terminal_rejected'] for r in old['flattened_controls'])
    variant,=[r for r in proof['variants'] if r['perimeter_factor']==factor]
    assert variant['sha256']==VARIANTS[factor] and variant['expanded_tap_edits']==386
    assert all(variant['controls'].values()) and variant['all_non_tap_params_nodes_models_held'] and variant['original_library_prefix_held']
    restored=inverse(raw,variant['local_edits'],42);assert digest(restored)==PARENT
    assert len(proof['local_mapping'])==42 and len(proof['fullchip386_occurrence_mapping'])==386
    byline={r['source_line']:r for r in proof['local_mapping']};assert len(byline)==42
    for e in variant['local_edits']:
        row=byline[e['line']]
        with localcontext() as c:
            c.prec=50
            expected=format(Decimal(980)/(Decimal(row['A_um2'])+factor*Decimal(row['P_um'])),'.18E')
        token,=re.findall(r'(?i)\bR=(\S+)',e['after']);assert token==expected==row['R_ohm'][str(factor)]
    return dict(status='passed exact declared conditional R-only inverse',factor=factor,pad_sha256=VARIANTS[factor],
        parent_sha256=PARENT,summary_sha256=digest(summary.read_bytes()),original_proof_sha256=digest(original_proof.read_bytes()),
        local_R_changes=42,fullchip_declared_occurrences=386,
        scope='Verified native A/P arithmetic sensitivity only. Neither coefficient is a validated physical bound or substrate spreading model. No original-R electrical acceptance transfer.')

#!/usr/bin/env python3
"""One isolated, source-defined main-MIM width candidate; no old qualification inheritance."""
import argparse
from decimal import Decimal, localcontext
import json
import math
import os
from pathlib import Path
import subprocess
import numpy as np
from run_loaded_followthrough import get_reference, adverse_deck, errors
from run_loaded_ac_audit import make_deck, source_probe, observations, OBS
from run_loaded_noise_audit import (TRIP, IMAGE, MANIFEST, sha, read_group,
                                   quiet_values, warning_inventory, table, run_bounded)
from analyze_loaded_ac_audit import crossings, controls

CAP_QUERY='@c.xs.xota.xcc.c1[scale]'
OLD='XCC cz out cap_cmim w=69u l=23u m=1 mm_ok=1'
NEW='XCC cz out cap_cmim w=50u l=23u m=1 mm_ok=1'
RZ_OLD='XRZ out1 cz vss rppd w=1u l=6.2u m=1 b=0 mm_ok=1'


def candidate_source(original,rz_length_um='6.2'):
    assert original.count(OLD)==1 and NEW not in original
    changed=original.replace(OLD,NEW)
    assert changed.replace(NEW,OLD)==original
    assert rz_length_um in ['6.2','24.8']
    if rz_length_um!='6.2':
        prefix,main=changed.split('.subckt g1_ota_main_candidate ',1)
        replacement=RZ_OLD.replace('l=6.2u','l='+rz_length_um+'u')
        assert main.count(RZ_OLD)==1 and replacement not in main
        updated=main.replace(RZ_OLD,replacement)
        assert updated.replace(replacement,RZ_OLD)==main
        changed=prefix+'.subckt g1_ota_main_candidate '+updated
    return changed


def scale_interval(old,new):
    """Outward binary64 interval for the pinned native expression.

    Old decimal-only failure is retained. Inverting the old rounded `1+t`
    requires a rounding enclosure; decimal print uncertainty alone is not an
    enclosure of the underlying t. Each native operation is bounded outward
    by its neighboring binary64 value. No simulator tolerance changes.
    """
    down=lambda x:float(np.nextafter(float(x),-np.inf))
    up=lambda x:float(np.nextafter(float(x),np.inf))
    def outward(values):return [down(min(values)),up(max(values))]
    def multiply(a,b):return outward([x*y for x in a for y in b])
    def divide(a,b):
        assert b[0]>0
        return outward([x/y for x in a for y in b])
    def root_area(width):
        # Mantissa-times-suffix parsing followed by the explicit source order.
        l=outward([23.*1e-6]);w=outward([float(width)*1e-6])
        area=multiply(multiply(l,w),[1e12,1e12])
        return outward([math.sqrt(x) for x in area])
    with localcontext() as context:
        context.prec=60
        a,b=Decimal(old),Decimal(new)
        da=Decimal(10)**a.as_tuple().exponent/2
        db=Decimal(10)**b.as_tuple().exponent/2
        factor=(Decimal(69)/Decimal(50)).sqrt()
        decimal_only=[1+(a-da-1)*factor,1+(a+da-1)*factor]
        original_print=[str(a-da),str(a+da)]
        observed_print=[str(b-db),str(b+db)]
        old_export=outward([float(a-da),float(a+da)])
        observed=outward([float(b-db),float(b+db)])
        # Enclose pre-rounding input of the old final addition, then undo the
        # division. The same area-independent native random deviation is used.
        old_t=outward([down(old_export[0])-1,up(old_export[1])-1])
        deviation=multiply(outward(old_t),root_area(69))
        assert .5 < 1+deviation[0] <= 1+deviation[1] < 2
        new_t=divide(deviation,root_area(50))
        predicted=outward([1+new_t[0],1+new_t[1]])
        passed=max(predicted[0],observed[0])<=min(predicted[1],observed[1])
        return dict(status='passed' if passed else 'failed',
            old_printed=old,new_printed=new,area_ratio='69/50',
            exact_formula='new_scale=1+(old_scale-1)*sqrt(69/50)',
            native_expression='1+(cap_carea_mm-1)/sqrt(l*w*1e12)',
            old_decimal_print_interval=original_print,new_decimal_print_interval=observed_print,
            prior_decimal_only_prediction=[str(x) for x in decimal_only],
            old_root_area_interval=root_area(69),new_root_area_interval=root_area(50),
            held_random_deviation_enclosure=deviation,
            predicted_binary64_interval=predicted,observed_binary64_interval=observed,
            rounding_basis='Outward nextafter at each binary64 operation and inverse old addition/division; half-last-decimal print interval. No fitted absolute/relative tolerance.',
            numerical_options_changed=False)


def parameter_gate(log,groups,expected):
    rows=[]
    for when in ['BEFORE','AFTER']:
        rows.append(read_group(log,'NON_BGR_'+when,groups['NON_BGR'])+
                    read_group(log,'BGR_'+when,groups['BGR']))
    assert rows[0]==rows[1] and len(rows[0])==11512
    unchanged=[r for r in expected if r[0]!=CAP_QUERY]
    assert len(unchanged)==11511
    assert [r for r in rows[0] if r[0]!=CAP_QUERY]==unchanged
    relation=scale_interval(dict(expected)[CAP_QUERY],dict(rows[0])[CAP_QUERY])
    assert relation['status']=='passed', relation
    legacy=read_group(log,'LEGACY27_AFTER',groups['LEGACY27'])
    assert legacy==[[q,dict(expected)[q]] for q in groups['LEGACY27']]
    return dict(unchanged11511_exact=True,candidate11512_before_after_exact=True,
                legacy27_exact=True,changed_cap_scale=relation,parameters=rows[0])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--case',choices=['slow','fast','nominal'],required=True)
    p.add_argument('--rz-length-um',choices=['6.2','24.8'],default='6.2')
    p.add_argument('--mode',choices=['differential','tian_voltage','tian_current'],required=True)
    p.add_argument('--baseline',type=Path)
    p.add_argument('--baseline-proof',type=Path)
    p.add_argument('--original-differential',type=Path)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--prepare-only',action='store_true')
    a=p.parse_args();assert not a.output.exists()
    if not a.prepare_only:assert os.sched_getaffinity(0)=={1}
    run,ref,prep,expected,old_op=get_reference('adverse',a.case) if a.case!='nominal' else get_reference('settling','rise')
    original=(ref/'sense.spice').read_text(); candidate=candidate_source(original,a.rz_length_um)
    a.output.mkdir(parents=True)
    (a.output/'candidate.spice').write_text(candidate)
    (a.output/'runner.py').write_bytes(Path(__file__).read_bytes())
    source_path=a.output/'candidate.spice'
    if a.mode.startswith('tian_'):
        source_path=a.output/'probe.spice';source_path.write_text(source_probe(candidate))
    if a.case!='nominal':
        deck=adverse_deck((ref/'population_transient.cir').read_text(),a.output,a.mode,run,prep['groups'])
    else:
        deck=make_deck((ref/'population_transient.cir').read_text(),a.output,a.mode,prep['groups'])
    if a.mode=='differential':
        old='.include qualification/'+run+'/sense.spice'
        assert deck.count(old)==1
        deck=deck.replace(old,'.include '+str(source_path))
    differential_anchor=None
    if a.case=='nominal' and a.mode=='differential':
        assert a.original_differential
        differential_anchor=json.loads((a.original_differential/'summary.json').read_text())
        anchor_contract=json.loads((a.original_differential/'contract.json').read_text())
        assert differential_anchor['status']=='passed source/OP/AC leaf'
        assert differential_anchor['mode']=='differential' and differential_anchor['full11512_and27_exact']
        assert anchor_contract['source_hashes']==prep['source_hashes']
        original_include='.include qualification/'+run+'/sense.spice'
        restored_prefix=deck.split('.control\n')[0].replace('.include '+str(source_path),original_include)
        assert restored_prefix==(a.original_differential/'probe.cir').read_text().split('.control\n')[0]
    baseline=None
    baseline_proof=None
    if a.mode.startswith('tian_'):
        assert a.baseline
        baseline_proof=a.baseline_proof or a.baseline/'summary.json'
        baseline=json.loads(baseline_proof.read_text())
        assert baseline['status']=='passed candidate source/finite leaf'
        assert baseline['mode']=='differential' and baseline['case']==a.case
        assert sha(a.baseline/'candidate.spice')==sha(a.output/'candidate.spice')
        if a.baseline_proof:
            assert baseline['reanalysis_only']
            assert all(sha(a.baseline/n)==h for n,h in baseline['original_failed_leaf_bindings'].items())
    contract=dict(case=a.case,mode=a.mode,reference_run=run,
        original_source_sha256=sha(ref/'sense.spice'),candidate_source_sha256=sha(a.output/'candidate.spice'),
        other_source_hashes={n:h for n,h in prep['source_hashes'].items() if n!='sense.spice'},
        source_inverse_exact=True,changes=[dict(old=OLD,new=NEW)]+([dict(old=RZ_OLD,new=RZ_OLD.replace('l=6.2u','l='+a.rz_length_um+'u'),scope='main OTA only')] if a.rz_length_um!='6.2' else []),
        main_MIM_area_um2=dict(original=1587,candidate=1150,delta=-437),
        main_RZ_body_area_um2=dict(original=6.2,candidate=float(a.rz_length_um),delta=float(a.rz_length_um)-6.2),
        baseline_summary_sha256=sha(baseline_proof) if baseline else None,
        original_differential_summary_sha256=sha(a.original_differential/'summary.json') if differential_anchor else None,
        unchanged11511_plus27_exact_required=True,candidate11512_before_after_exact_required=True,
        intentional_model_scale='Native mismatch area law; held random realization checked with decimal-print and outward binary64 operation intervals. All other recorded model fingerprints exact; changed resistor dimensions are not an unchanged circuit.',
        criteria=dict(gain_V_per_V=[19.9,20.1],BW_Hz_min=2e6,PM_deg_min=60,GM_dB_min=10,
                      probe_DC_V_max=1e-6,probe_DC_A_max=1e-9),
        watchdog_s=120,scope='Isolated source candidate only; no production, old MC, native geometry, field model or PEX qualification inherited.')
    (a.output/'contract.json').write_text(json.dumps(contract,indent=2)+'\n')
    (a.output/'probe.cir').write_text(deck)
    if a.prepare_only:print(json.dumps(contract,indent=2));return
    pd=Path('/foss/pdks/ihp-sg13g2')
    runtime=dict(image_id_observed_by_host=MANIFEST,pdk_commit=(pd/'COMMIT').read_text().strip(),
        ngspice_version=subprocess.check_output(['ngspice','--version'],text=True),
        model_sha256={str(f.relative_to(pd)):sha(f) for f in (pd/'libs.tech/ngspice/models').rglob('*') if f.is_file()},solver='sparse')
    assert runtime==prep['expected_runtime_identity']
    (a.output/'provenance.json').write_text(json.dumps(dict(runtime_identity=runtime,
        OCI_config_digest=IMAGE,OCI_manifest_digest=MANIFEST,runtime_exact=True),indent=2)+'\n')
    with (a.output/'run.log').open('x') as log:
        state=run_bounded(['ngspice','-b',str(a.output/'probe.cir')],log,a.output/'run.json',120,cwd=TRIP,interval_s=1)
    text=(a.output/'run.log').read_text()
    result=dict(status='failed',case=a.case,mode=a.mode,runtime=state,
                errors=errors(text),warnings=warning_inventory(text))
    try:
        assert state['status']=='completed' and state['returncode']==0 and not result['errors']
        assert ('LOADED_FOLLOWTHROUGH_END' if a.case!='nominal' else 'LOADED_AC_END') in text
        assert all(sha(ref/n)==h for n,h in prep['source_hashes'].items())
        assert sha(a.output/'candidate.spice')==contract['candidate_source_sha256']
        result['parameter_gate']=parameter_gate(text,prep['groups'],expected)
        op=quiet_values(text);obs=observations(text)
        result.update(quiet_op_V=op,operating_point=obs,original9OP_exact=op==old_op,
                      original9OP_abs_delta_V={n:abs(op[n]-old_op[n]) for n in op})
        if a.mode=='differential':
            anchor_op=differential_anchor['quiet_op_V'] if differential_anchor else old_op
            result['same_topology_original9OP_exact']=op==anchor_op
            assert op==anchor_op, 'Passive candidate DC must match its exact original differential topology'
            if differential_anchor:
                result['same_topology_original_supply_current_exact']=all(obs[n]==differential_anchor['operating_point'][n] for n in ['i(vdda)','i(vdd)'])
                assert result['same_topology_original_supply_current_exact']
        else:
            delta={n:abs(obs[n]-baseline['operating_point'][n]) for n in OBS}
            result['probe_DC_abs_delta']=delta
            assert max(abs(op[n]-baseline['quiet_op_V'][n]) for n in op)<=1e-6
            assert all(d<=(1e-9 if n.startswith('i(') else 1e-6) for n,d in delta.items())
        header=['frequency','ac_re','ac_im'] if a.mode=='differential' else ['frequency','ir','ii','vr','vi']
        wave=table(a.output/'ac.dat',header);assert wave.shape==(901,len(header))
        if a.mode=='differential':
            basis=table(a.output/'input_basis.dat',['frequency','p_re','p_im','n_re','n_im'])
            assert np.array_equal(basis[:,0],wave[:,0])
            assert np.max(abs(basis[:,1:]-np.array([.5,0,-.5,0])))<=1e-12
            controls();mag=abs(wave[:,1]+1j*wave[:,2]);db=20*np.log10(mag)
            bw=crossings(wave[:,0],db,db[0]-3.010299956639812)
            result.update(gain_1Hz_V_per_V=float(mag[0]),
                gain_status='passed' if 19.9<=mag[0]<=20.1 else 'failed',
                halfpower_downcrossings_Hz=[q[2] for q in bw],
                bandwidth_status='passed' if bw and bw[0][2]>=2e6 else 'failed')
        result['status']='passed candidate source/finite leaf'
    except (AssertionError,ValueError,KeyError,IndexError,OSError) as exc:
        result['analysis_error']=repr(exc)
    (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['warnings','parameter_gate']},indent=2))
    raise SystemExit(0 if result['status'].startswith('passed') else 1)


if __name__=='__main__':main()

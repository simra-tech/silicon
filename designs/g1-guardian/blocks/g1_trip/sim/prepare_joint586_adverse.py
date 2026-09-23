#!/usr/bin/env python3
"""Prepare, never launch, required joint corner/rail/true-common-mode controls."""
import argparse
import difflib
import json
from pathlib import Path
import re
from prepare_joint586_population import make_control, disabled_source, sha
from run_joint586_calibration import REFERENCE, SIM, ROOT

CORNERS = {'slow': ('ss','wcs','wcs','wcs'), 'fast': ('ff','bcs','bcs','bcs')}
SEEDS = {'slow':(77001,77002), 'fast':(78001,78002)}
CASES = [('enabled',0,True,[25]),('repeat',0,True,[25]),('changed',1,True,[25]),
         ('disabled',0,False,[25]),('disabledchanged',1,False,[25]),('return',0,True,[25,125,-40,25])]
# Calibration stays at original unbalanced input SHN=0, not silently moved to
# true zero common mode. All following conditions reuse its frozen codes.
CONDITIONS = [('room_legacy',25,3.3,1.2,None),('cold_legacy',-40,3.3,1.2,None),
    ('hot_legacy',125,3.3,1.2,None),('low_cold_cm0',-40,3.,1.08,0.),
    ('low_hot_cm0',125,3.,1.08,0.),('high_cold_cm0',-40,3.6,1.32,0.),
    ('high_hot_cm0',125,3.6,1.32,0.),('room_cm_low',25,3.3,1.2,-.1),
    ('room_cm_zero',25,3.3,1.2,0.),('room_cm_high',25,3.3,1.2,.3)]


def replace_once(text,old,new):
    assert text.count(old)==1, old
    return text.replace(old,new)


def transform_fixture(deck,corner,vdda,vdd,common_mode,shunt=.025):
    """Explicit library/rail/input changes only; control queries remain intact."""
    assert corner in ['typ']+list(CORNERS)
    assert (vdda,vdd) in [(3.3,1.2),(3.,1.08),(3.6,1.32)]
    assert common_mode in [None,-.1,0.,.3] and 0<=shunt<=.05
    original=deck
    changes=[]
    def change(old,new):
        nonlocal deck
        deck=replace_once(deck,old,new)
        if old!=new:changes.append((old,new))
    if corner!='typ':
        mos,res,cap,hbt=CORNERS[corner]
        for name,old,new in [('MOSlv','mos_tt','mos_'+mos),('MOShv','mos_tt','mos_'+mos),
                ('RES','res_typ','res_'+res),('CAP','cap_typ','cap_'+cap),('HBT','hbt_typ','hbt_'+hbt)]:
            prefix='.lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/corner'+name+'.lib '
            change(prefix+old+'_mismatch\n',prefix+new+'_mismatch\n')
    change('.param VDDA=3.3 VDD=1.2 VREF=1.04\n',
        '.param VDDA=%.12g VDD=%.12g VREF=1.04\n'%(vdda,vdd))
    for line in original.splitlines(True):
        if re.fullmatch(r'V[sh][0-7] [sh][0-7] 0 dc 1\.2\n',line):
            change(line,line.replace('dc 1.2','dc %.12g'%vdd))
    change('Vclk clk 0 pulse(0 1.2 20n 0.2n 0.2n 100n 200n)\n',
        'Vclk clk 0 pulse(0 %.12g 20n 0.2n 0.2n 100n 200n)\n'%vdd)
    old,=re.findall(r'^Vsh shp 0 dc .+\n',deck,re.M)
    if common_mode is None:
        change(old,'Vsh shp 0 dc '+format(shunt,'.17g')+'\n')
    else:
        change(old,'Vsh shp 0 dc '+format(common_mode+shunt/2,'.17g')+'\n'
            +'Vshn shn 0 dc '+format(common_mode-shunt/2,'.17g')+'\n')
        change('XS shp 0 vref iptat isense vped vref_buf vdda 0 g1_sense\n',
            'XS shp shn vref iptat isense vped vref_buf vdda 0 g1_sense\n')
    inverse=deck
    for old,new in reversed(changes):inverse=replace_once(inverse,new,old)
    assert inverse==original
    if '.control\n' in original:
        assert deck.split('.control\n')[1]==original.split('.control\n')[1]
    return deck,changes


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--campaign-id',required=True)
    args=parser.parse_args()
    assert re.fullmatch('[a-z0-9-]+',args.campaign_id)
    out=SIM/'qualification'/args.campaign_id
    assert not out.exists()
    reference=SIM/'qualification'/REFERENCE
    prep=json.loads((reference/'preparation.json').read_text())
    old=(reference/'population_transient.cir').read_text()
    auditpath=SIM/'qualification/joint586-transient-full-audit-20260922.json'
    audit=json.loads(auditpath.read_text())
    assert audit['status']=='passed strict transient controls'
    assert all(audit['strict_checks'].values())
    assert all(sha(reference/name)==digest for name,digest in prep['source_hashes'].items())
    out.mkdir()
    bindings={str(p.relative_to(ROOT)):sha(p) for p in [auditpath,reference/'preparation.json',
        reference/'population_transient.cir',reference/'population_inventory.json']+
        [reference/n for n in prep['source_hashes']]}
    rows=[]
    for corner in CORNERS:
        for label,index,enabled,temps in CASES:
            run_id=args.campaign_id+'-'+corner+'-'+label
            local=out/(corner+'-'+label)
            local.mkdir()
            seed=SEEDS[corner][index]
            for name in prep['source_hashes']:
                source=(reference/name).read_text()
                (local/name).write_text(source if enabled else disabled_source(source))
            # Only output/include paths differ beyond the declared body/OP
            # transformation. No simulator is invoked by this preparation.
            logical=args.campaign_id+'/'+local.name
            body=old.split('.control\n')[0].replace(REFERENCE,logical)
            changed,changes=transform_fixture(body,corner,3.3,1.2,None)
            op=changed+make_control(logical,seed,temps,prep['groups'])
            (local/'population_op.cir').write_text(op)
            (local/'declared_body_difference.diff').write_text(''.join(difflib.unified_diff(
                body.splitlines(True),changed.splitlines(True),fromfile='qualifiedTypicalBody',tofile=corner+'Body')))
            rows.append(dict(corner=corner,label=label,seed=seed,enabled=enabled,temperatures_C=temps,
                deck=str((local/'population_op.cir').relative_to(ROOT)),deck_sha256=sha(local/'population_op.cir'),
                source_hashes={name:sha(local/name) for name in prep['source_hashes']},
                maximum_wall_s=300 if len(temps)==1 else 1200,status='not run'))
    # Exact examples bind the forthcoming transient fixtures before a runner
    # exists; only body changes shown, no new sampling policy is introduced.
    examples=[]
    for corner in CORNERS:
        for label,temp,vdda,vdd,cm in CONDITIONS:
            transformed,changes=transform_fixture(old,corner,vdda,vdd,cm)
            transformed=replace_once(transformed,'.temp 25.0\n','.temp '+str(float(temp))+'\n')
            path=out/(corner+'-'+label+'-transient.diff')
            path.write_text(''.join(difflib.unified_diff(old.splitlines(True),transformed.splitlines(True),
                fromfile='qualifiedTypicalTransient',tofile=corner+'-'+label)))
            examples.append(dict(corner=corner,condition=label,diff=str(path.relative_to(ROOT)),sha256=sha(path)))
    first20=json.loads((SIM/'qualification/joint586-first20-audit-20260922.json').read_text())
    hours=first20['total_completed_leaf_core_seconds']/3600/20
    packet=dict(status='prepared only; exact-diff review and own harness qualification required',
        canonical_source_hashes=prep['source_hashes'],source_nominal_BGR_sha256='586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b',
        physical_scope=prep['physical_scope'],live_bindings_sha256=bindings,inventory_sha256=prep['inventory_sha256'],
        full_parameter_count=11512,legacy_parameter_count=27,randomized_source_instances=3500,
        groups=prep['groups'],expected_runtime_identity=prep['expected_runtime_identity'],op_controls=rows,
        transient_examples=examples,process_sections=CORNERS,
        qualification='Eachcorner six OP controls enabled/repeat/changed/disabled/disabledchanged/25-125-minus40-25 return; exact11512+27, distinct3500 primitives byBGR/nonBGR groups, exactdisabled/repeat/return OP wave. Then samecorner transient repeat,changed,disabled pair,cold,hot,return withfull11512+27 and18finitecolumns,1.02us/5MHz/1200sperphase; exactwave failures remainfailures. Rail/commonmode perturbations require beforeafter and samecorner same-seed inventory parity before population.',
        population_seeds={'slow':list(range(77101,77131)),'fast':list(range(78101,78131))},
        population_conditions=[dict(label=l,temperature_C=t,VDDA_V=a,VDD_V=d,true_common_mode_V=c,
            input_policy='original SHN0/SHPshunt, mean=shunt/2' if c is None else 'SHP=CM+shunt/2,SHN=CM-shunt/2') for l,t,a,d,c in CONDITIONS],
        calibration='Samecorner25C3.3/1.2 originalSHN0 interior25mV binarycalibration. Originalsignedcorrection,rounding,saturation,independentcodepolicy,nominalhard204 unchanged. Freeze resultingcodes for all10conditions; fouroriginalguards plus two24.5/25.5mVresidualleaves percondition. No recalibration at rail/CM/temp.',
        sampling='Originalfixed0.6V clock-crossing and decision thresholds retained,20nsafteractualedge,late3cycles and legacyfixedtimes mustagree. Clock/codeHIGH amplitudes track actualVDD; no hidden half-rail normalization or thresholdwaiver.',
        screening_scope='Selected slow and fast global corners only, not exhaustiveMOSxRxHBT Cartesian. Fulljoint30adverse/trueCM currentlynotrun; priorstandaloneSENSE/T2F grids do not substitute. Crossed extremeCM withcold/hot/supply remainsrequiredselected deterministic sensitivity, not implicitlycovered by roomCMensemble.',
        remaining_selected_deterministic_conditions=[dict(temperature_C=t,VDDA_V=a,VDD_V=d,true_common_mode_V=c)
            for t in [-40,125] for a,d in [(3.,1.08),(3.3,1.2),(3.6,1.32)] for c in [-.1,.3]],
        progression='Ownqualification then firstsample completeindependentaudit,20smoke then30predeclaredselectedcornercharacterization. Preserveallnumerical/electricalfails, no seeds dropped or replaced. No firstcohortlaunch bythispreparer.',
        forecast=dict(measured_typical28leaf_cpu_hours_per_sample=hours,nominal_leaf_count=28,
            projected_corner_leaf_count_per_sample=70,projected_cpu_hours_per_corner30=hours*70/28*30,
            projected_two_corner_cpu_hours=hours*70/28*60,projected_bulk_GiB=.23*70/28*60,
            maximum_original1200s_leaf_cpu_hours_two_corners=70*60*1200/3600,
            required_additional_deterministic_leaves_bothcorners=12*6*2,
            projected_deterministic_cpu_hours=hours/28*12*6*2,
            caveat='Typical measured extrapolation only; adversecornerqualification mustreplace withmeasuredthroughput. Includes10expectedcalibrationleaves; actualbinarypath/failurecount retained. Qualification controls and futurephysicalPEX reruns additional.'))
    (out/'contract.json').write_text(json.dumps(packet,indent=2)+'\n')
    print(json.dumps(dict(contract=str((out/'contract.json').relative_to(ROOT)),sha256=sha(out/'contract.json'),forecast=packet['forecast']),indent=2))


if __name__=='__main__':main()

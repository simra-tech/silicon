#!/usr/bin/env python3
"""Bounded actual-chain calibration pilot: independent comparator brackets and saturation.
Each probe is a fresh archived simulator process with same seed/device order;
observed sampled parameters must match exactly. Not a shortcut around V14 monotonicity.
"""
import argparse,datetime,json,math,subprocess,sys
from pathlib import Path
from result_directory import allocate_run
SIM=Path(__file__).resolve().parent
class PauseRequested(Exception): pass

def analysis_arguments(args):
 """Discard run-label/watchdog replay metadata only; numerical arguments stay exact."""
 result=[];index=0
 while index<len(args):
  if args[index] in ['--run-id','--timeout-s','--replay-reference']:index+=2
  else:result.append(args[index]);index+=1
 return result


def calibration_codes(brackets, known_shunt=.025, candidate=False, hard_nominal_code=None):
 """Nearest integer correction, then signed-byte and unsigned-DAC saturation."""
 nominal_cal=(.25+known_shunt*3975/1.04) if candidate else known_shunt*5300/1.04
 raw_delta={k:math.floor(sum(pair)/2-nominal_cal+.5) for k,pair in brackets.items()}
 delta={k:max(-128,min(127,v)) for k,v in raw_delta.items()}
 nominal={'soft':115,'hard':191} if candidate else {'soft':153,'hard':254}
 if hard_nominal_code is not None:
  if candidate or not 0<=hard_nominal_code<=255: raise ValueError('Explicit hard setting requires baseline mapping and unsigned DAC code')
  nominal['hard']=hard_nominal_code
 raw_code={k:nominal[k]+delta[k] for k in brackets}
 code={k:max(0,min(255,v)) for k,v in raw_code.items()}
 return {'raw_independent_correction_codes':raw_delta,'signed_correction_codes':delta,'corrected_codes':code,'clipped':{k:raw_code[k]!=code[k] or raw_delta[k]!=delta[k] for k in brackets}}

def main():
 p=argparse.ArgumentParser();p.add_argument('--run-id',required=True);p.add_argument('--image-id',required=True);p.add_argument('--seeds',default='71001');p.add_argument('--guards',action='store_true');p.add_argument('--solver',choices=['sparse','klu'],default='sparse');p.add_argument('--temperatures',default='25,-40,125');p.add_argument('--headroom-candidate',action='store_true');p.add_argument('--sense-candidate');p.add_argument('--hard-nominal-code',type=int,help='Isolated baseline setting with both hard guards inside0–50mV; canonical default unchanged');p.add_argument('--resume',action='store_true');p.add_argument('--leaf-timeout-s',type=float,default=600);p.add_argument('--reuse-map',type=Path,help='Explicit identical-analysis references; each alias requires fresh exact-deck/source/model preflight');p.add_argument('--recovery-map',type=Path);p.add_argument('--rebuild-only',action='store_true',help='Replay preserved leaf summaries; never launch simulation');a=p.parse_args()
 if not 0<a.leaf_timeout_s<=600: raise ValueError('Joint watchdog must be positive and at most600s')
 guard_points=[(.027,{'soft':False,'hard':False}),(.033,{'soft':True,'hard':False}),(.045,{'soft':True,'hard':False}),(.055,{'soft':True,'hard':True})]
 if a.hard_nominal_code is not None:
  hard_target=a.hard_nominal_code*1.04/5300
  if a.headroom_candidate or not 0<=a.hard_nominal_code<=255 or not .033<.9*hard_target<1.1*hard_target<=.05: raise ValueError('Explicit hard setting must preserve soft/hard band ordering and0–50mV range')
  guard_points[2:]=[(.9*hard_target,{'soft':True,'hard':False}),(1.1*hard_target,{'soft':True,'hard':True})]
 reuse_map=json.loads(a.reuse_map.read_text()) if a.reuse_map else {}
 recovery_map=json.loads(a.recovery_map.read_text()) if a.recovery_map else {}
 if recovery_map and not a.resume: raise ValueError('Recovery map requires explicit --resume')
 out=SIM/'qualification'/a.run_id
 if a.resume:
  if not out.is_dir(): raise ValueError('Resume campaign does not exist')
  stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
  if (out/'summary.json').exists(): (out/f'summary.before-resume.{stamp}.json').write_text((out/'summary.json').read_text())
  (out/f'resume_driver.{stamp}.py').write_text(Path(__file__).read_text())
  (out/f'resume_configuration.{stamp}.json').write_text(json.dumps({'arguments':sys.argv[1:],'new_leaf_timeout_s':a.leaf_timeout_s,'scope':'Existing cached attempts and their original bounds retained; only new leaf analyses use this bound'},indent=2)+'\n')
  if recovery_map: (out/f'recovery_map.{stamp}.json').write_text(json.dumps(recovery_map,indent=2)+'\n')
 else:
  if a.rebuild_only: raise ValueError('--rebuild-only requires --resume')
  out=allocate_run(SIM,a.run_id);(out/'driver.py').write_text(Path(__file__).read_text())
 if not a.resume: (out/'provenance.json').write_text(json.dumps({'arguments':sys.argv[1:],'new_leaf_timeout_s':a.leaf_timeout_s,'scope':'BGR flagged PEX, actual SENSE bias/refbuffer, full schematic TRIP transistor switches and comparators; ideal supply sources, no pads/RTL. TightGear0.2ns,0.52usprobe. Per-probe watchdog recorded by new_leaf_timeout_s; no failed sample omission. Full code monotonicity remains separate V14 requirement.'},indent=2)+'\n')
 if reuse_map:(out/'reuse_map.json').write_text(json.dumps(reuse_map,indent=2)+'\n')
 samples=[]
 for seed in map(int,a.seeds.split(',')):
  sample={'seed':seed,'status':'running','calibration_Vsh_V':.025,'specified_shunt_range_V':[0,.05],'hard_full_robust_band_status':'not applicable at nominal50mV: upper guard55mV exceeds specified SENSE range','probes':[],'bracket_status':'not run','guards_status':'not run'};samples.append(sample);fp=None;index=0
  sample['guard_definitions']=[{'shunt_V':v,'expected':e} for v,e in guard_points]
  sample['hard_nominal_code']=a.hard_nominal_code if a.hard_nominal_code is not None else (191 if a.headroom_candidate else 254)
  if a.hard_nominal_code is not None: sample['hard_full_robust_band_status']='both guards inside specified range; acceptance determined by frozen checks'
  def persist():(out/'summary.json').write_text(json.dumps(samples,indent=2)+'\n')
  def probe(codes,shunt=.025,temp=25):
   nonlocal index,fp
   leaf=f'{a.run_id}-s{seed}-p{index:02d}';index+=1
   cmd=[sys.executable,str(SIM/'run_kickback_qualification.py'),'--run-id',leaf,'--image-id',a.image_id,'--seed',str(seed),'--actual-bgr','--soft-code',str(codes['soft']),'--hard-code',str(codes['hard']),'--shunt-value',str(shunt),'--temperature',str(temp),'--offsets-mv=0','--tstop-us','.52','--maxstep-ns','.2','--tight','--gear']
   if a.solver!='sparse':cmd += ['--solver',a.solver]
   if a.headroom_candidate:cmd.append('--headroom-candidate')
   if a.sense_candidate:cmd += ['--sense-candidate',a.sense_candidate]
   cmd += ['--timeout-s',str(a.leaf_timeout_s)]
   if leaf in reuse_map and leaf in recovery_map:raise ValueError('Reuse and recovery aliases must be disjoint')
   reused=leaf in reuse_map
   evidence_leaf=reuse_map.get(leaf,recovery_map.get(leaf,leaf))
   leafdir=SIM/'qualification'/evidence_leaf
   if reused:
    target=SIM/'qualification'/leaf
    if not target.exists():
     if a.rebuild_only or (out/'PAUSE_REQUESTED').exists():raise PauseRequested(leaf)
     rc=subprocess.run(cmd+['--replay-reference',evidence_leaf,'--prepare-only'],cwd=SIM).returncode
     if rc:raise RuntimeError('Reuse preflight failed '+leaf)
    comparison=json.loads((target/'same_deck_replay.json').read_text())
    if comparison.get('status')!='passed' or comparison['reference_run']!=evidence_leaf:raise RuntimeError('Invalid reuse preflight '+leaf)
    if json.loads((leafdir/'summary.json').read_text())[0]['solver_status']!='passed':raise RuntimeError('Cannot reuse incomplete analysis '+leaf)
   elif evidence_leaf!=leaf:
    comparison=json.loads((leafdir/'same_deck_replay.json').read_text())
    if comparison.get('status')!='passed' or comparison['reference_run']!=leaf: raise RuntimeError('Unqualified recovery alias '+leaf)
    if json.loads((leafdir/'summary.json').read_text())[0]['solver_status']!='passed': raise RuntimeError('Recovery alias has no completed solver result '+leaf)
   if (a.resume or reused) and leafdir.exists():
    if not (leafdir/'summary.json').exists(): raise RuntimeError(f'Incomplete existing leaf {leaf}: preserve it and diagnose before resume')
    provenance=json.loads((leafdir/'provenance.json').read_text())
    if evidence_leaf==leaf:
     if analysis_arguments(provenance['runner_arguments']) != analysis_arguments(cmd[2:]): raise RuntimeError(f'Cached leaf analysis arguments differ: {leaf}')
    elif analysis_arguments(provenance['runner_arguments'])!=analysis_arguments(cmd[2:]): raise RuntimeError(f'Recovery analysis arguments differ: {leaf}')
    rc=0
   else:
    if a.rebuild_only or (out/'PAUSE_REQUESTED').exists():
     persist();(out/'resume_checkpoint.json').write_text(json.dumps({'status':'paused before new leaf','next_leaf':leaf,'next_command':cmd[2:],'sample_seed':seed,'completed_probes_this_sample':len(sample['probes'])},indent=2)+'\n')
     raise PauseRequested(leaf)
    rc=subprocess.run(cmd,cwd=SIM).returncode
   entry={'run':leaf,'evidence_run':evidence_leaf,'recovery_alias':evidence_leaf!=leaf and not reused,'reused_analysis':reused,'codes':codes.copy(),'shunt_V':shunt,'temp_C':temp,'range_scope':'within specified SENSE range' if 0<=shunt<=.05 else 'outside specified SENSE range diagnostic','runner_returncode':rc,'status':'failed'};sample['probes'].append(entry)
   path=leafdir/'summary.json'
   if rc==0 and path.exists():
    r=json.loads(path.read_text())[0];entry['solver_status']=r['solver_status'];entry['watchdog_status']=r.get('watchdog_status');entry['wall_s']=r['wall_s'];entry['fingerprints']=r['fingerprints']
    if r['solver_status']=='passed' and len(r['fingerprints'])==27:
     if fp is None:fp=r['fingerprints']
     entry['physical_sample_fingerprint_matches']=r['fingerprints']==fp
     values=r['both_sampled_output_V'];entry['sampled_outputs_V']=values
     decisions={key:all(v>.6 for v in vals) if all(v>.6 for v in vals) or all(v<.6 for v in vals) else None for key,vals in values.items()}
     entry['decisions']=decisions
     if entry['physical_sample_fingerprint_matches'] and all(v is not None for v in decisions.values()):entry['status']='passed'
   persist();return entry
  lo=probe({'soft':0,'hard':0});hi=probe({'soft':255,'hard':255})
  if any(e['status']!='passed' for e in [lo,hi]):sample.update(status='failed',bracket_status='not run to completion (probe failed)');persist();continue
  if not all(lo['decisions'][k] and not hi['decisions'][k] for k in ['soft','hard']):sample.update(status='failed',bracket_status='failed endpoint bracketing');persist();continue
  lows={'soft':0,'hard':0};highs={'soft':255,'hard':255};failed=False
  while max(highs[k]-lows[k] for k in lows)>1:
   mid={k:(lows[k]+highs[k])//2 for k in lows};r=probe(mid)
   if r['status']!='passed':failed=True;break
   for k in lows:
    if highs[k]-lows[k]>1:
     if r['decisions'][k]:lows[k]=mid[k]
     else:highs[k]=mid[k]
  if failed:sample.update(status='failed',bracket_status='not run to completion (probe failed)');persist();continue
  monotonic=True
  for k in lows:
   rows=sorted((e['codes'][k],e['decisions'][k]) for e in sample['probes'])
   monotonic &= all(a>=b for (_,a),(_,b) in zip(rows,rows[1:]))
  sample['brackets']={k:[lows[k],highs[k]] for k in lows};sample['bracket_status']='passed selected probes' if monotonic else 'failed sampled monotonicity'
  sample.update(calibration_codes(sample['brackets'],candidate=a.headroom_candidate,hard_nominal_code=a.hard_nominal_code));codes=sample['corrected_codes'];sample['status']='completed calibration pilot' if monotonic else 'failed'
  sample['qualification_limit']='Only probed-code monotonicity established; V14 full-code statistical monotonicity and actual threshold residual not implied.';persist()
  if a.guards and monotonic:
   guards=[]
   for temp in map(float,a.temperatures.split(',')):
    for shunt,expect in guard_points:
     r=probe(codes,shunt,temp);guards.append({'probe':r['run'],'expected':expect,'range_scope':r['range_scope'],'status':'passed' if r['status']=='passed' and r['decisions']==expect else 'failed'})
   sample['guards']=guards;sample['guards_status']='passed' if all(x['status']=='passed' for x in guards) else 'failed';persist()
   residual=[];cal_codes={k:math.floor(sum(sample['brackets'][k])/2+.5) for k in codes}
   for temp in map(float,a.temperatures.split(',')):
    for shunt,expected in [(.0245,False),(.0255,True)]:
     r=probe(cal_codes,shunt,temp);residual.append({'probe':r['run'],'fixed_calibration_codes':cal_codes,'expected_both_high':expected,'status':'passed' if r['status']=='passed' and all(v==expected for v in r['decisions'].values()) else 'failed'})
   sample['residual_half_mV_checks']=residual;sample['residual_half_mV_status']='passed' if all(x['status']=='passed' for x in residual) else 'failed';persist()
if __name__=='__main__':
 try: main()
 except PauseRequested as e: print('PAUSED before',e,flush=True)

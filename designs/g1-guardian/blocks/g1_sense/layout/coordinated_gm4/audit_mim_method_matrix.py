#!/usr/bin/env python3
"""Recover completed coupon solver evidence after stock postprocessor crash."""
import argparse
import json
import math
from pathlib import Path
import re
from export_sense_kpex_api import sha
from klayout_pex.fastercap.fastercap_runner import fastercap_parse_capacitance_matrix


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();assert not args.output.exists()
    summary=json.loads((args.run/'summary.json').read_text())
    assert summary['returncode']==-11 and summary['termination_reason'] is None and summary['all_inputs_tools_cards_unchanged']
    log=(args.run/'kpex.log').read_text()
    assert 'No errors found' in log and 'FasterCap succeeded after' in log
    assert log.index('FasterCap succeeded after') < log.index('Removing whiteboxed device')
    logs=list(args.run.rglob('*_FasterCap_Output.txt'));assert len(logs)==1
    matrix=fastercap_parse_capacitance_matrix(logs[0]);assert matrix.conductor_names==['g1_VSUBS','g2_bottom','g3_top']
    rows=matrix.rows;assert all(math.isfinite(v) for row in rows for v in row)
    assert all(rows[i][i]>0 for i in range(3)) and all(rows[i][j]<0 for i in range(3)for j in range(3)if i!=j)
    mesh_files=list(args.run.rglob('*.geo'));areas={}
    for net,z in [('bottom',4.96),('bottom',5.45),('top',5.49)]:
        key=f'{net}@z{z}';area=0.;triangles=0
        for path in mesh_files:
            if f'_net={net}.geo'not in path.name:continue
            for line in path.read_text().splitlines():
                words=line.split()
                if not words or words[0]!='T':continue
                coords=list(map(float,words[2:11]));assert len(coords)==9
                pts=[coords[i:i+3]for i in (0,3,6)]
                if not all(abs(point[2]-z)<1e-8 for point in pts):continue
                area+=abs(sum(pts[i][0]*pts[(i+1)%3][1]-pts[(i+1)%3][0]*pts[i][1]for i in range(3)))/2
                triangles+=1
        areas[key]=dict(projected_area_um2=area,triangles=triangles)
    assert abs(areas['top@z5.49']['projected_area_um2']-49)<1e-8
    assert abs(areas['bottom@z4.96']['projected_area_um2']-67.24)<1e-8
    assert abs(areas['bottom@z5.45']['projected_area_um2']-67.24)<1e-8
    diffs=[float(value)for value in re.findall(r'Weighted Frobenius norm of the difference between capacitance \(auto option\): ([\d.eE+-]+)',logs[0].read_text())]
    assert diffs and diffs[-1]<.05
    result=dict(status='passed saved solver/plate coverage control; extraction completeness not qualified',
                original_command_status='failed SIGSEGV after successful solver; preserved',
                no_solver_rerun=True,script_sha256=sha(Path(__file__)),run_summary_sha256=sha(args.run/'summary.json'),
                solver_log_sha256=sha(logs[0]),mesh_hashes={path.name:sha(path)for path in mesh_files},
                conductor_names=matrix.conductor_names,matrix_F=rows,raw_bottom_substrate_fF=[-rows[0][1]*1e15,-rows[1][0]*1e15],
                last_solver_relative_Frobenius_delta=diffs[-1],requested_solver_tolerance=.05,
                reciprocity_relative_by_pair={f'{i},{j}':abs(rows[i][j]-rows[j][i])/max(abs(rows[i][j]),abs(rows[j][i]))for i in range(3)for j in range(i+1,3)},
                plate_surface_inventory=areas,small_coupon_native_MIM_area_um2=49.,
                dielectric_scope_issue='Stock computed metal5_n_cap and metal5_cap share GDS67/0; FasterCapInputBuilder resolves both through the merged GDS-pair context. The saved ismim-facing bottom surface covers full67.24um2 rather than49um2 MIM interior. This is recorded, not silently corrected or electrically waived.',
                precision='Stock printed matrix values; binary64 parsing cannot recover extra solver digits',
                full_macro_context_convergence='not run',intrinsic_extrinsic_separation='not run',
                tap_contact_coverage='not run',electrical_adoption='not run')
    args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='mesh_hashes'},indent=2))


if __name__=='__main__':main()

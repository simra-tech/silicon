#!/usr/bin/env python3
"""Run pinned FasterCap on the native CMIM coupon and retain its raw matrix."""
import argparse
import hashlib
import importlib.metadata
import json
import math
import os
import re
import shutil
from pathlib import Path

import klayout.db as kdb
from klayout_pex.env import Env
from klayout_pex.fastercap.fastercap_runner import run_fastercap, fastercap_parse_capacitance_matrix
from klayout_pex.kpex_cli import KpexCLI
from klayout_pex.klayout.lvsdb_extractor import KLayoutExtractionContext
from klayout_pex.tech_info import TechInfo


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_iterations(path):
    lines = path.read_text().splitlines()
    matrices = []
    for i, line in enumerate(lines):
        if line.strip() != 'Capacitance matrix is:':
            continue
        match = re.fullmatch(r'Dimension (\d+) x (\d+)', lines[i + 1].strip())
        assert match and match.group(1) == match.group(2)
        size = int(match.group(1))
        rows = []
        names = []
        for raw in lines[i + 2:i + 2 + size]:
            cells = raw.split()
            names.append(cells[0])
            rows.append([float(x) / 1e6 for x in cells[1:]])
        assert len(rows) == size and all(len(row) == size for row in rows)
        assert all(math.isfinite(x) for row in rows for x in row)
        matrices.append(dict(names=names, matrix_F=rows))
    return matrices


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--coupon', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--tolerance', type=float, choices=[0.05, 0.01], default=0.05)
    p.add_argument('--stream-stdout', action='store_true')
    p.add_argument('--pty-stdout', action='store_true')
    p.add_argument('--galerkin', action='store_true')
    a = p.parse_args()
    assert os.sched_getaffinity(0) == {1} and not a.output.exists()
    assert kdb.__version__ == '0.30.9'
    assert importlib.metadata.version('klayout-pex') == '0.3.12'
    assert Path('/foss/pdks/ihp-sg13g2/COMMIT').read_text().strip() == '84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    meta = json.loads((a.coupon / 'manifest.json').read_text())
    gds = a.coupon / 'sense_mim_method_control.gds'
    cdl = a.coupon / 'sense_mim_method_control.cdl'
    assert meta['status'] == 'passed native coupon geometry preparation'
    assert sha(gds) == meta['GDS_sha256'] == '546c3e33d3894fb4c0d54c623a0cd2ac261cbf074a44d210240921c86194fd20'
    assert sha(cdl) == meta['CDL_sha256'] == 'bcc32a78962430e46e7269518c645681c3233e24337e87142e714c7fe85aa974'
    args = KpexCLI.parse_args(['--pdk', 'ihp-sg13g2', '--threads', '1', '--fastercap',
        '--tolerance', str(a.tolerance), *(['--galerkin'] if a.galerkin else []),
        '--blackbox', 'false', '--cache-lvs', 'false', '--geo_check', 'true',
        '--gds', str(gds), '--cell', 'sense_mim_method_control',
        '--schematic', str(cdl), '--out_dir', str(a.output / 'engine')], Env.from_os_environ())
    KpexCLI.validate_args(args)
    techpath = Path(args.tech_pbjson_path)
    resolved = shutil.which(args.fastercap_exe_path)
    assert resolved
    binary = Path(resolved)
    assert sha(techpath) == '6ece2ac73930696f77b257d14fcf9d29d9e02451e7df99c72239746c18369a92'
    assert sha(binary) == 'ca21992c038685cb0885ae8b2488f2a6a3ca7d2b2ed1ff2c996978bcdd4e7dcf'
    stream_wrapper = Path(__file__).with_name('stream_fastercap.sh')
    pty_wrapper = Path(__file__).with_name('pty_fastercap.py')
    assert not (a.stream_stdout and a.pty_stdout)
    if a.stream_stdout:
        assert stream_wrapper.is_file() and os.access(stream_wrapper, os.X_OK)
    if a.pty_stdout:
        assert pty_wrapper.is_file() and os.access(pty_wrapper, os.X_OK)
    a.output.mkdir(parents=True, exist_ok=True)
    (a.output / 'source.py').write_bytes(Path(__file__).read_bytes())
    result = dict(status='running', coupon_GDS_sha256=sha(gds), coupon_CDL_sha256=sha(cdl),
                  technology_sha256=sha(techpath), FasterCap_binary_sha256=sha(binary),
                  KLayout_PEX_version='0.3.12', max_threads=1,
                  args=dict(tolerance=args.fastercap_tolerance, d_coeff=args.fastercap_d_coeff,
                            mesh=args.fastercap_mesh_refinement_value,
                            dielectric_filter='all', blackbox=False,
                            galerkin=args.fastercap_galerkin_scheme),
                  source_model_technology_changes='none', electrical_adoption='not run')
    result['stdout_adapter'] = (dict(mode='PTY', wrapper_sha256=sha(pty_wrapper))
                                if a.pty_stdout else
                                dict(mode='stdbuf -oL -eL', wrapper_sha256=sha(stream_wrapper))
                                if a.stream_stdout else 'none')
    def save():
        (a.output / 'summary.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    save()
    try:
        cli = KpexCLI()
        tech = TechInfo.from_json(str(techpath), dielectric_filter=args.dielectric_filter)
        db = cli.create_lvsdb(args)
        context = KLayoutExtractionContext.prepare_extraction(db, 'sense_mim_method_control', tech, False)
        result['unknown_layers'] = [q.lvs_layer_name for q in context.unnamed_layers]
        lst = Path(cli.build_fastercap_input(args, context, tech))
        result['input_list_sha256'] = sha(lst)
        geo = sorted(lst.parent.glob('*.geo'))
        result['geometry_files'] = [dict(name=q.name, sha256=sha(q), bytes=q.stat().st_size)
                                    for q in geo]
        assert any('outside=ismim_net=bottom' in q.name for q in geo)
        assert any('outside=ismim_net=top' in q.name for q in geo)
        save()
        log = a.output / 'FasterCap_Output.txt'
        run_fastercap(exe_path=str(pty_wrapper if a.pty_stdout else
                                   stream_wrapper if a.stream_stdout else binary),
            lst_file_path=str(lst), log_path=str(log),
            tolerance=args.fastercap_tolerance, d_coeff=args.fastercap_d_coeff,
            mesh_refinement_value=args.fastercap_mesh_refinement_value,
            ooc_condition=args.fastercap_ooc_condition,
            auto_preconditioner=args.fastercap_auto_preconditioner,
            galerkin_scheme=args.fastercap_galerkin_scheme,
            jacobi_preconditioner=args.fastercap_jacobi_preconditioner)
        matrix = fastercap_parse_capacitance_matrix(str(log))
        iterations = parse_iterations(log)
        assert iterations and iterations[-1]['names'] == matrix.conductor_names
        assert iterations[-1]['matrix_F'] == matrix.rows
        (a.output / 'raw_matrices.json').write_text(json.dumps(iterations, indent=2) + '\n')
        result.update(status='completed raw FasterCap coupon only; convergence audit pending',
                      solver_log_sha256=sha(log), iteration_count=len(iterations),
                      conductor_names=matrix.conductor_names, raw_matrix_F=matrix.rows,
                      raw_matrices_sha256=sha(a.output / 'raw_matrices.json'))
    except Exception as exc:
        result.update(status='failed raw FasterCap coupon', error=repr(exc))
    finally:
        result['inputs_unchanged'] = (sha(gds) == meta['GDS_sha256'] and
                                      sha(cdl) == meta['CDL_sha256'] and
                                      sha(techpath) == result['technology_sha256'] and
                                      sha(binary) == result['FasterCap_binary_sha256'])
        save()
    print(json.dumps({k: result.get(k) for k in ['status', 'error', 'iteration_count',
                                               'conductor_names', 'raw_matrix_F']}))
    raise SystemExit(1 if result['status'].startswith('failed') else 0)


if __name__ == '__main__':
    main()

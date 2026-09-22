"""Allocate a fresh run locally or via an ignored link to reserved result storage."""
import os
import fcntl
from pathlib import Path
import re
import subprocess


def allocate_run(sim, run_id):
    sim = Path(sim)
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', run_id):
        raise ValueError('Run ID must be a single safe path component')
    local = sim / 'qualification' / run_id
    if os.path.lexists(str(local)):
        raise FileExistsError('Run ID already exists: ' + str(local))
    result_root = os.environ.get('G1_RESULTS_ROOT')
    if not result_root:
        local.mkdir(parents=True, exist_ok=False)
        return local
    external = Path(result_root)
    if not external.is_absolute() or not external.is_dir():
        raise ValueError('G1_RESULTS_ROOT must be an existing absolute reserved directory')
    repository = sim.parents[4]
    relative = str(local.relative_to(repository))
    # Only this exact generated path is excluded, never a broad campaign glob.
    git = ['git', '-c', 'safe.directory=' + str(repository)]
    exclude_path = Path(subprocess.check_output(git + ['rev-parse', '--git-path', 'info/exclude'], cwd=repository, universal_newlines=True).strip())
    if not exclude_path.is_absolute():
        exclude_path = repository / exclude_path
    exclude_path.parent.mkdir(parents=True, exist_ok=True)
    with exclude_path.open('a+') as exclude:
        fcntl.flock(exclude, fcntl.LOCK_EX)
        exclude.seek(0)
        previous = exclude.read()
        entry = '/' + relative
        if entry not in previous.splitlines():
            exclude.write(('\n' if previous and not previous.endswith('\n') else '') + entry + '\n')
            exclude.flush()
            os.fsync(exclude.fileno())
        ignored = subprocess.run(git + ['check-ignore', '--quiet', relative], cwd=repository).returncode
        if ignored != 0:
            raise ValueError('External run link is not ignored by Git: ' + relative)
    block = external / sim.parent.name
    block.mkdir(exist_ok=True)
    destination = block / run_id
    destination.mkdir(exist_ok=False)
    local.parent.mkdir(parents=True, exist_ok=True)
    local.symlink_to(destination, target_is_directory=True)
    # Keep the lexical /work path: relative_to(SIM), source includes and replay
    # normalization must not depend on the external host storage location.
    return local

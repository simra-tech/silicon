"""Pure fail-closed rule-hash and CPU/resource-gate checks for stock LVS."""
from datetime import datetime,timezone
from pathlib import Path
import hashlib

REQUIRED_CHECKS=('cpu_budget_positive','quota_growth_and_reserve','inodes_available',
                 'ram_available','coordinated_CPU_reservations_fit',
                 'external_allocation_growth','external_inodes')

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def rule_tree(pdk,relative):
    directory=Path(pdk)/relative
    assert directory.is_dir()
    return {str(p.relative_to(pdk)):digest(p) for p in directory.rglob('*') if p.is_file()}
def rule_files(hashes):
    """Exclude only generated Python bytecode, never a source/rule file."""
    return {k:v for k,v in hashes.items() if '/__pycache__/' not in k and not k.endswith('.pyc')}
def require_rules(expected,observed):
    assert isinstance(expected,dict) and expected and expected==observed,'stock rule tree changed'
    return True
def require_bound_hashes(expected):
    assert expected and all(digest(path)==sha for path,sha in expected.items()),'bound file changed'
    return True
def require_affinity(gate,affinity,required_cpu,now=None):
    now=now or datetime.now(timezone.utc)
    assert len(affinity)==1 and set(affinity)=={required_cpu},'invalid single-CPU affinity'
    assert gate['status']=='passed' and all(gate['checks'].get(k) is True for k in REQUIRED_CHECKS),'resource gate failed'
    utc=gate['utc'];assert utc.endswith('Z') or utc.endswith('+00:00')
    stamp=datetime.strptime(utc.replace('Z','').split('+')[0].split('.')[0],'%Y-%m-%dT%H:%M:%S').replace(tzinfo=timezone.utc)
    assert 0<=(now-stamp).total_seconds()<=150,'resource gate stale'
    assert gate['sample_seconds']>=30 and gate['reserve_gib']>=16
    assert gate['external_allocation']['reserve_gib']>=2
    assert required_cpu in gate['coordinated_allocation']['cpus'],'CPU absent from coordinated ledger'
    return True

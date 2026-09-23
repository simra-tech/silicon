#!/usr/bin/env python3
"""Bounded native full-device RC extraction; not model-composition acceptance."""
import hashlib,json,os,sys
from pathlib import Path

def main():
    assert os.sched_getaffinity(0)=={6}
    source=Path(sys.argv[sys.argv.index('--source')+1])
    reference=Path(sys.argv[sys.argv.index('--reference')+1])
    assert hashlib.sha256(source.read_bytes()).hexdigest()=='bb933fdabf3fd8a5117bf47f33cd40657caf78ef424e6a9bfddda0f11190d782'
    assert json.loads((reference/'manifest.json').read_text())['GDS_sha256']=='450a49062d17f65be1046736c2ebeff219b4c4d4b22fac0998940c158741a637'
    parent=Path(__file__).resolve().parent.parent/'coordinated_comp45_rz62'
    original_path=parent/'extract_affected_field_cc.py'
    original=original_path.read_text()
    assert hashlib.sha256(original.encode()).hexdigest()=='12b4a0611b1ea88ae2cf3bdd22bb7701ed4b28c074252f152ee179fb725707d7'
    changes=[
        ('os.sched_getaffinity(0)=={1}','os.sched_getaffinity(0)=={6}'),
        ("'--mode','CC'","'--mode','RC'"),
        ("'--blackbox','true'","'--blackbox','false'"),
        ('args.effective_cell_name,tech,True)','args.effective_cell_name,tech,False)'),
        ("complete_field_coverage='FAILED: native blackbox MIM/tap omissions retained'",
         "complete_field_coverage='NOT QUALIFIED: full-device geometry and reference planes require independent audit'"),
        ("numerical_engine='unchanged native2.5D CC, original reporter; no SPICE/CSV writer'",
         "numerical_engine='unchanged native2.5D RC, full-device mode, original reporter; no SPICE/CSV writer'"),
        ('assert rows and not summary.resistances',
         "assert rows\n        resistors=[]\n        for key,value in sorted(summary.resistances.items()):\n            value=float(value);assert math.isfinite(value) and value>=0\n            resistors.append(dict(net1=key.net1,net2=key.net2,resistance_ohm=value,resistance_hex=value.hex()))\n        rp=a.output/'exact_resistances.json';rp.write_text(json.dumps(resistors,indent=2,allow_nan=False)+'\\n')\n        result.update(resistor_count=len(resistors),resistor_sha256=sha(rp),resistance_acceptance='not qualified')"),
        ("status='passed raw native CC only; completefield FAILED'",
         "status='completed raw native RC diagnostic; completefield NOT QUALIFIED'"),
        ("status='failed raw CC diagnostic'","status='failed raw RC diagnostic'")]
    derived=original
    for old,new in changes:
        assert derived.count(old)==1,old
        derived=derived.replace(old,new)
    restored=derived
    for old,new in reversed(changes):
        assert restored.count(new)==1
        restored=restored.replace(new,old)
    assert restored==original
    compile(derived,'derived_rc_probe.py','exec')
    output=Path(sys.argv[sys.argv.index('--output')+1])
    adapter=output.with_name(output.name+'-adapter');assert not adapter.exists() and not output.exists()
    adapter.mkdir(parents=True)
    (adapter/'derived.py').write_text(derived)
    (adapter/'adapter.py').write_bytes(Path(__file__).read_bytes())
    (adapter/'contract.json').write_text(json.dumps(dict(status='prepared diagnostic only',
        exact_inverse=True,changes=changes,original_sha256=hashlib.sha256(original.encode()).hexdigest(),
        derived_sha256=hashlib.sha256(derived.encode()).hexdigest(),
        source_sha256='bb933fdabf3fd8a5117bf47f33cd40657caf78ef424e6a9bfddda0f11190d782',
        native_GDS_sha256='450a49062d17f65be1046736c2ebeff219b4c4d4b22fac0998940c158741a637',
        model_composition='not run; no VSUBS binding or intrinsic capacitance subtraction'),indent=2)+'\n')
    sys.path.insert(0,str(parent))
    namespace=dict(__file__=str(adapter/'derived.py'),__name__='rc_boundary_probe')
    exec(compile(derived,str(adapter/'derived.py'),'exec'),namespace)
    namespace['main']()

if __name__=='__main__':main()

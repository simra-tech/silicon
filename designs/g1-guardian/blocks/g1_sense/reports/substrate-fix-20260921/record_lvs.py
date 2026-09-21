import hashlib,json
from pathlib import Path
p=Path('/foss/pdks/ihp-sg13g2')
out=Path('reports/substrate-fix-20260921')
record={'command':'G1_WORKDIR=designs/g1-guardian/blocks/g1_sense flow/run.sh python3 /foss/pdks/ihp-sg13g2/libs.tech/klayout/tech/lvs/run_lvs.py --layout=layout/g1_sense_filled.gds --netlist=reports/substrate-fix-20260921/g1_sense.cdl --run_dir=reports/substrate-fix-20260921/lvs --topcell=g1_sense --run_mode=deep --no_series_res','pdk_commit':(p/'COMMIT').read_text().strip(),'image_id_observed':'sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0','klayout_version':'0.30.9 (runner log)','solver_exit':0,'status':'passed','drc_status':'not run; geometry unchanged','deck_hashes':{str(f.relative_to(p)):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'libs.tech/klayout/tech/lvs').rglob('*') if f.is_file()}}
(out/'lvs_provenance.json').write_text(json.dumps(record,indent=2)+'\n')

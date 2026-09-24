#!/usr/bin/env python3
"""One of three remaining required four-site cohorts; unchanged qualified logic."""
import argparse
import hashlib
from pathlib import Path
import sys

p=argparse.ArgumentParser(add_help=False);p.add_argument('--cohort',type=int,choices=[2,3,4],required=True)
a,rest=p.parse_known_args();sys.argv=[sys.argv[0]]+rest
stages={2:[('iptat_lower',7),('iptat_corner',8),('iptat_upper',9),('vref_neighbor',16)],
        3:[('vref_lower',11),('vref_left',12),('vref_upper',13),('vref_trip',14)],
        4:[('vref_corner',15),('vref_midleft',17),('vref_midright',18),('vdda_feed',20)]}[a.cohort]
path=Path(__file__).with_name('run_local_via_cohort1.py')
assert hashlib.sha256(path.read_bytes()).hexdigest()=='8beda294b6d202b03956acd71d6dd2db535f1499ad2df2b67651c883d1cb0393'
text=path.read_text()
old="[('gate_route',0),('gate_output',1),('clock_receiver',5),('iptat_sense',6)]"
assert text.count(old)==1;text=text.replace(old,repr(stages))
assert text.count("'stage_ids':[0,1,5,6]")==1
text=text.replace("'stage_ids':[0,1,5,6]","'stage_ids':"+repr([n for _,n in stages]))
assert text.count('prepare_local_via_cohort1_clip.py')==2
text=text.replace('prepare_local_via_cohort1_clip.py','prepare_local_via_remaining_clip.py')
text=text.replace('cohort1 four','cohort%d four'%a.cohort)
text=text.replace('stages0/1/5/6 only','stages'+','.join(str(n) for _,n in stages)+' only')
needle="(out/'contract.json').write_text(json.dumps(contract,indent=2)+'\\n')"
assert text.count(needle)==1
text=text.replace(needle,needle+"\n(out/'derived_runner.py').write_text(DERIVED_SOURCE)\n")
exec(compile(text,str(path),'exec'),dict(__file__=__file__,__name__='remaining_via_cohort',DERIVED_SOURCE=text))

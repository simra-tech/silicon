"""Exact two-device soft-only reference delta on latest canonical OSC parent."""
import hashlib,os,re
from pathlib import Path
SOURCE=Path(os.environ['G1_RESULTS_ROOT'])/'osc-r095-physical-20260924-r1/fullchip_r095_candidate.cdl'
SOURCE_SHA='126acd51cae404f55e9a3470d521d0d90f5115e668fbf393ac48c492e4507333'
NEW='g1_cmp_soft_inputpair4_folded_r1'
def transform(text):
    assert hashlib.sha256(text.encode()).hexdigest()==SOURCE_SHA
    block,=re.findall(r'(?ms)^\.subckt g1_cmp inp inn clk q qb vdd vss\n.*?^\.ends\n',text)
    changed=block
    edits=[]
    for device,nodes in [('MM1','xp inp tail'),('MM2','xq inn tail')]:
        before=device+' '+nodes+' vss sg13_lv_nmos w=12u l=0.34u m=1'
        after=before.replace('w=12u l=0.34u','w=24u l=0.68u')
        assert changed.count(before+'\n')==1;changed=changed.replace(before,after);edits.append((before,after))
    changed=changed.replace('.subckt g1_cmp ','.subckt '+NEW+' ')
    before='XCS icmp vth_soft clk cmp_soft cmp_soft_n VDD VSS g1_cmp\n'
    after=before.replace(' g1_cmp\n',' '+NEW+'\n')
    assert text.count(before)==1
    result=text.replace(block,changed).replace(before,after)
    inverse=result.replace(after,before).replace('.subckt '+NEW+' ','.subckt g1_cmp ')
    for old,new in edits:inverse=inverse.replace(new,old)
    assert inverse==text
    hard,=re.findall(r'(?ms)^\.subckt g1_cmp_regenpair4 .*?^\.ends\n',text)
    assert hard in result
    return result

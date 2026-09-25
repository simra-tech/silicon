import os
SIM=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sys,glob,os,re
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from gen import *
L=os.path.join(SIM,'logs')
H='| %s | Status | trip_d (µs) | GATE < 1 V (µs) | GATE < 0.33 V (µs) | Cause | VDDA (µA) | Wall (s) | Log |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- |'
def emit(title,items):
    print(H%title)
    for label,case,log in items:
        print('| %s | '%label+' | '.join(row(case,info(log)))+' |')
    print()

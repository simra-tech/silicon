#!/usr/bin/env python3
"""R2: four-cut narrow risers; defer obstructed vb2 escape. No GDS write."""
import screen_bias_bypass as base


def ledger():
    rows=[]
    def rect(layer,net,box,role):
        rows.append(dict(layer=layer,net=net,bbox_dbu=box,role=role))
    for net,left,right,port_y,y in (
        ('pbias',281210,411740,138600,156000),
        ('pcasc',282210,412490,139200,159000)):
        rect('M5',net,[left-150,y-1000,right+150,y+1000],'bias_parallel_bypass')
        for x in (left,right):
            rect('M4',net,[x-150,port_y-150,x+150,y+780],'same_net_narrow_riser')
            for layer in ('M4','M5'):
                rect(layer,net,[x-150,y-780,x+150,y+780],'four_Via4_landing')
            for dy in (-630,-210,210,630):
                rect('Via4',net,[x-95,y+dy-95,x+95,y+dy+95],'four_redundant_Via4')
    return rows


if __name__=='__main__':
    base.ledger=ledger
    base.__file__=__file__
    base.main()

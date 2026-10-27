"""layout-B diagnosis: plot the net boxes of dev/net_dump.py (host python, matplotlib). plot_nets.py <json> <png> [layers] [x0,y0,x1,y1]"""
import json, sys
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
d = json.load(open(sys.argv[1])); out = sys.argv[2]
lays = sys.argv[3].split(',') if len(sys.argv) > 3 else ['8', '10', '30', '50', '67', '126']
win = [float(v) for v in sys.argv[4].split(',')] if len(sys.argv) > 4 else None
col = {'gnd': 'tab:blue', 'vss': 'tab:blue', 'vdd': 'tab:red', 'vdda': 'tab:pink', 'vref': 'tab:green', 'vrefl': 'tab:olive',
       'top_p': 'tab:purple', 'top_n': 'tab:orange', 'lsb_p': 'tab:brown', 'lsb_n': 'tab:gray'}
fig, ax = plt.subplots(figsize=(22, 12))
for net, L in d.items():
    for ln, bxs in L.items():
        LM = {'l10': '8', 'l12': '10', 'l14': '30', 'l16': '50', 'l18': '67', 'l20': '126'}   # lvsdb derived metal layers (deck order)
        if LM.get(ln.split(':')[0], ln.split(':')[-1].split('/')[0]) not in lays:
            continue
        for b in bxs:
            ax.add_patch(Rectangle((b[0], b[1]), b[2] - b[0], b[3] - b[1], color=col.get(net, 'k'), alpha=0.5, lw=0))
ax.set_aspect('equal'); ax.autoscale()
if win:
    ax.set_xlim(win[0], win[2]); ax.set_ylim(win[1], win[3])
ax.legend(handles=[Rectangle((0, 0), 1, 1, color=col.get(n, 'k')) for n in d], labels=list(d), loc='upper right')
ax.set_title('%s layers %s' % (sys.argv[1].split('/')[-1], ','.join(lays)))
fig.savefig(out, dpi=80, bbox_inches='tight')

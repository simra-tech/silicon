#!/usr/bin/env python3
"""Collect the final-GDS STA runs into results.json and the markdown tables of the README.
Usage: summarize.py <bulk final dir> <out dir>   (python 3.6)"""
import sys, os, re, json, glob, collections
B, O = sys.argv[1], sys.argv[2]
REF = {  # r3 sign-off (bulk digital-eco-r3cand2-20260926/sta/main; blocks/g1_padring/reports/signoff-1414r3-20260926/macro/*.tsv)
    'macro_r3signoff': dict(fast=(29.0439, 0.1141), typ=(28.8211, 0.1948), slow=(28.4466, 0.3375)),
    'chip_merged_r3signoff_1350routes': dict(fast=(27.9884, 0.1141), typ=(27.2483, 0.1948), slow=(25.7036, 0.3375)),
}
def rd(p):
    try: return open(p).read()
    except IOError: return ''
def groups(txt):
    g = {}
    for m in re.finditer(r'(min_delay/hold|max_delay/setup) group (\S+)\s*\n.*?\n-+\n(\S+).*?(-?[\d.]+) \((MET|VIOLATED)\)', txt, re.S):
        g['%s:%s' % ('hold' if m.group(1).startswith('min') else 'setup', m.group(2))] = dict(endpoint=m.group(3), slack=float(m.group(4)))
    return g
def drv(txt):
    out = collections.defaultdict(list); sec = None
    for ln in txt.splitlines():
        s = ln.strip()
        if s in ('max slew', 'max capacitance', 'max fanout'): sec = s; continue
        m = re.match(r'(\S+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+) \(VIOLATED\)', s)
        if m and sec: out[sec].append(dict(pin=m.group(1), limit=float(m.group(2)), value=float(m.group(3)), slack=float(m.group(4))))
    return out
def unannot(txt):
    m = re.search(r'Found (\d+) unannotated drivers', txt); n = int(m.group(1)) if m else 0
    names = [l.strip() for l in txt.split('partially')[0].splitlines()[1:] if l.startswith(' ')]
    pm = re.search(r'Found (\d+) partially unannotated', txt)
    return dict(count=n, partial=int(pm.group(1)) if pm else 0, clkload=sum(1 for x in names if 'clkload' in x),
                other=[x for x in names if 'clkload' not in x])
def latency(txt):
    res = {}
    for m in re.finditer(r'Clock (\S+)\n(.*?)(?=\nClock |\Z)', txt, re.S):
        lat = [(float(a), float(b)) for a, b in re.findall(r'\s([\d.]+)\s+([\d.]+) latency', m.group(2))]
        sk = [float(x) for x in re.findall(r'\s([\d.]+) skew', m.group(2))]
        if lat: res[m.group(1)] = dict(min=min(x[0] for x in lat), max=max(x[1] for x in lat), skew_max=max(sk) if sk else None)
    return res
def slews(txt):
    r = {}
    for m in re.finditer(r'^(\S+) \^ ([\d.]+):([\d.]+) v ([\d.]+):([\d.]+)', txt, re.M):
        r[m.group(1)] = dict(rise=float(m.group(3)), fall=float(m.group(5)))
    return r
def unconstrained(txt):
    m = re.search(r'Warning: There (?:are|is) (\d+) unconstrained endpoints?', txt); return int(m.group(1)) if m else 0
runs = {}
for d in sorted(glob.glob(os.path.join(B, '*-*'))):
    if not os.path.isdir(d): continue
    tag, corner = os.path.basename(d).rsplit('-', 1)
    s = dict(l.split('\t', 1) for l in rd(os.path.join(d, 'summary.tsv')).splitlines() if '\t' in l)
    log = rd(os.path.join(d, 'sta.log'))
    runs.setdefault(tag, {})[corner] = dict(
        complete='STA_FINAL_COMPLETE' in log,
        worst_setup_ns=float(s['worst_setup_ns']) if 'worst_setup_ns' in s else None,
        worst_hold_ns=float(s['worst_hold_ns']) if 'worst_hold_ns' in s else None,
        tns_setup=s.get('tns_setup_ns'), tns_hold=s.get('tns_hold_ns'),
        registers={k[10:]: v for k, v in s.items() if k.startswith('registers_')},
        groups=groups(rd(os.path.join(d, 'groups_end.rpt'))),
        setup_violations=len(re.findall(r'VIOLATED', rd(os.path.join(d, 'setup_violators.rpt')))),
        hold_violations=len(re.findall(r'VIOLATED', rd(os.path.join(d, 'hold_violators.rpt')))),
        drv={k: v for k, v in drv(rd(os.path.join(d, 'drv_violators.rpt'))).items()},
        annotation=unannot(rd(os.path.join(d, 'annotation.rpt'))),
        clock_latency=latency(rd(os.path.join(d, 'clock_latency.rpt'))),
        key_slews=slews(rd(os.path.join(d, 'slews_key_pins.rpt'))),
        unconstrained=unconstrained(rd(os.path.join(d, 'coverage.rpt'))),
        warnings=sorted(set(re.findall(r'^(Warning \d+|Error \d+)', log, re.M))))
json.dump(dict(reference=REF, runs=runs), open(os.path.join(O, 'results.json'), 'w'), indent=1, sort_keys=True)
# ---- markdown
M = []
C = ('fast', 'typ', 'slow')
M.append('| Case | Corner | Worst setup (ns) | Worst hold (ns) | Setup / hold viol. | Setup SCLK / osc_clk / async | Hold SCLK / osc_clk / async | Registers SCLK / osc_clk | Max slew / cap / fanout flags | Unannotated (clkload / other / partial) |')
M.append('| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |')
for tag in sorted(runs):
    for c in C:
        r = runs[tag].get(c)
        if not r: M.append('| %s | %s | not run | | | | | | | |' % (tag, c)); continue
        g = r['groups']; gs = lambda k: '%.3f' % g[k]['slack'] if k in g else '-'
        sclk = 'sclk' if tag == 'macro' else 'SCLK'
        M.append('| %s | %s | %.3f | %+.3f | %d / %d | %s / %s / %s | %s / %s / %s | %s / %s | %d / %d / %d | %d / %d / %d |' % (
            tag, c, r['worst_setup_ns'], r['worst_hold_ns'], r['setup_violations'], r['hold_violations'],
            gs('setup:' + sclk), gs('setup:osc_clk'), gs('setup:asynchronous'), gs('hold:' + sclk), gs('hold:osc_clk'), gs('hold:asynchronous'),
            r['registers'].get(sclk, '-'), r['registers'].get('osc_clk', '-'),
            len(r['drv'].get('max slew', [])), len(r['drv'].get('max capacitance', [])), len(r['drv'].get('max fanout', [])),
            r['annotation']['clkload'], len(r['annotation']['other']), r['annotation']['partial']))
# key pin slews (ns, max of the max-corner rise/fall), chip_p2p and chip_p2p_oscedge
M += ['', '| Pin | ' + ' | '.join('%s %s' % (t, c) for t in ('chip_p2p', 'chip_p2p_oscedge') for c in C) + ' |', '| --- |' + ' --- |' * 6]
pins = sorted(set(p for t in ('chip_p2p',) for c in C for p in runs.get(t, {}).get(c, {}).get('key_slews', {})))
for p in pins:
    row = []
    for t in ('chip_p2p', 'chip_p2p_oscedge'):
        for c in C:
            k = runs.get(t, {}).get(c, {}).get('key_slews', {}).get(p)
            row.append('%.3f / %.3f' % (k['rise'], k['fall']) if k else '-')
    M.append('| `%s` | %s |' % (p, ' | '.join(row)))
M += ['', '| Clock | ' + ' | '.join('%s %s' % (t, c) for t in ('chip_p2p', 'chip_p2p_oscedge') for c in C) + ' |', '| --- |' + ' --- |' * 6]
for clk in ('SCLK', 'osc_clk'):
    row = []
    for t in ('chip_p2p', 'chip_p2p_oscedge'):
        for c in C:
            k = runs.get(t, {}).get(c, {}).get('clock_latency', {}).get(clk)
            row.append('%.3f-%.3f (skew %.3f)' % (k['min'], k['max'], k['skew_max']) if k else '-')
    M.append('| %s | %s |' % (clk, ' | '.join(row)))
open(os.path.join(O, 'tables.md'), 'w').write('\n'.join(M) + '\n')
print('\n'.join(M))
# ---- per-net table of the digital top-level nets (chip_p2p), from top_net_pins.tsv and the SPEF report
import csv
spef = json.load(open(os.path.join(os.path.dirname(B.rstrip('/')), 'rc_r4', 'top_p2p.json')))['nets']
ANALOG = {'D_ELT', 'D_STD', 'G_SHARED', 'HBT_B', 'HBT_C', 'HBT_E', 'SENSE_N', 'SENSE_P', 'VREF', 'TRIP_SET', 'i_core_vref', 'i_core_trip_set'}
tab = collections.OrderedDict()
for c in C:
    p = os.path.join(B, 'chip_p2p-%s' % c, 'top_net_pins.tsv')
    if not os.path.exists(p): continue
    for row in csv.DictReader(open(p), delimiter='\t'):
        net = row['net']
        if net in ANALOG: continue
        e = tab.setdefault(net, dict(driver=None, cells=set(), load_slew={}, cap={}))
        cap = max(float(x) for x in row['net_total_cap_pf'].replace('e-', 'E').split('-') if x) if row['net_total_cap_pf'] else None
        e['cap'][c] = cap
        sl = [float(x) for x in (row['slew_rise_ns'], row['slew_fall_ns']) if x not in ('', 'INF', '-INF')]
        if row['direction'] == 'output' or (row['direction'] == 'bidirect' and net in ('SDO', 'FAULT_N', 'GATE', 'TEMP_OUT')):
            e['driver'] = '%s (%s)' % (row['pin'], row['cell'])
        else:
            e['cells'].add(row['cell'])
            if sl: e['load_slew'][c] = max(e['load_slew'].get(c, 0), max(sl))
N = ['', '| Net | Driver | R to the far pin (ohm) | Route C incl. fragments (fF) | Net C with pins, slow (fF) | Worst load slew fast / typ / slow (ns) | Loads |', '| --- | --- | --- | --- | --- | --- | --- |']
for net, e in sorted(tab.items()):
    s = spef.get(net, {}); rr = s.get('R_to_pin_ohm') or {}
    N.append('| `%s` | %s | %s | %s | %s | %s | %s |' % (net, ('`%s`' % e['driver']) if e['driver'] else 'port', '%.0f' % max(rr.values()) if rr else '-',
             '%.1f' % s['C_total_fF'] if s else '-', '%.1f' % (e['cap']['slow'] * 1000) if e['cap'].get('slow') is not None else '-',
             ' / '.join('%.3f' % e['load_slew'][c] if c in e['load_slew'] else '-' for c in C), ', '.join(sorted(e['cells']))))
open(os.path.join(O, 'net_table.md'), 'w').write('\n'.join(N) + '\n')
print('\n'.join(N))

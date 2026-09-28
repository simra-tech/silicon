#!/usr/bin/env python3
"""Collect the IR/EM run of record into the small tracked result files of this directory.
Usage: summarize.py <B = ${BULK}/postsub-20260928/irem> <this directory>"""
import csv, collections, glob, json, os, re, sys
B, OUT = sys.argv[1], sys.argv[2]
NETS = ['VDD', 'VSS', 'VDDA', 'IOVDD', 'IOVSS', 'GATE', 'SENSE_P', 'SENSE_N', 'VREF', 'i_core_vref']
BLOCKS = {'Xi_core_u_digital': 'G1_CTRL digital macro', 'Xi_core_u_osc': 'G1_OSC', 'Xi_core_u_trip': 'G1_TRIP', 'Xi_core_u_t2f': 'G1_T2F',
          'Xi_core_u_gate': 'G1_GATE', 'Xi_core_u_bgr': 'G1_BGR', 'Xi_core_u_sense': 'G1_SENSE', 'Xi_core_u_ls_en': 'g1_ls_up (en)',
          'Xi_core_u_ls_mode': 'g1_ls_up (mode)', 'Xi_core_u_ls_r4': 'g1_ls_up (r4)', 'Xi_core_u_dose': 'G1_DOSE', 'Xi_core_u_dut': 'G1_DUT'}
def rel(p): return p.replace(B, '${BULK}/postsub-20260928/irem')
S = {}
for net in NETS:
    for tech in ('typ', 'worst'):
        S[(net, tech)] = json.load(open('%s/solve/%s_%s_summary.json' % (B, net, tech)))
# ---- IR per sink group
with open(os.path.join(OUT, 'ir_drop_by_pin.csv'), 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['net', 'case', 'tech', 'sink_group', 'block', 'load_mA', 'max_drop_mV', 'mean_drop_mV'])
    for (net, tech), s in sorted(S.items()):
        for case, c in s['cases'].items():
            for g, d in sorted(c['ir'].items()):
                if 'max_drop_mV' not in d: w.writerow([net, case, tech, g, BLOCKS.get(g, 'IO cell'), '', d.get('status'), '']); continue
                w.writerow([net, case, tech, g, BLOCKS.get(g, 'IO cell'), '%.4g' % (d['load_A'] * 1e3), '%.3f' % d['max_drop_mV'], '%.3f' % d['mean_drop_mV']])
# ---- EM rows (pitch 1.0): utilisation >= 0.10, plus the top 15 of every net/tech/case
rows = []
for f in sorted(glob.glob('%s/solve/*_em.csv' % B)):
    rs = list(csv.DictReader(open(f)))
    rows += [r for r in rs if float(r['utilisation']) >= 0.10 or int(r['rank']) <= 15]
cols = list(rows[0].keys())
with open(os.path.join(OUT, 'em_segments.csv'), 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
# per net / tech / case / origin / layer maximum (all kept rows of solve/, utilisation >= 0.01 or top 40)
mx = {}
for f in sorted(glob.glob('%s/solve/*_em.csv' % B)):
    for r in csv.DictReader(open(f)):
        k = (r['net'], r['tech'], r['case'], r['origin'], r['kind'], r['layer'])
        if k not in mx or float(r['utilisation']) > float(mx[k]['utilisation']): mx[k] = r
with open(os.path.join(OUT, 'em_max_by_layer.csv'), 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['net', 'tech', 'case', 'origin', 'kind', 'layer', 'max_utilisation', 'I_mA', 'limit', 'box'])
    for k in sorted(mx): r = mx[k]; w.writerow(list(k) + [r['utilisation'], r['I_mA'], r['limit'], r['box']])
over = [r for r in rows if float(r['utilisation']) > 0.5]
with open(os.path.join(OUT, 'em_over_50pct.csv'), 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(sorted(over, key=lambda r: -float(r['utilisation'])))
# ---- per net summary
summ = {}
for (net, tech), s in sorted(S.items()):
    for case, c in s['cases'].items():
        summ['%s/%s/%s' % (net, tech, case)] = dict(total_A=c['total_A'], max_node_drop_mV=round(c['max_node_drop_mV'], 3),
            em_max_by_origin={k: round(v, 4) for k, v in c['em_max_by_origin'].items()}, ngspice_ok=c['ngspice_ok'],
            scipy_max_abs_diff_V=c['scipy_max_abs_diff_V'])
    summ['%s/%s/mesh' % (net, tech)] = dict(cells=s['cells'], links=s['links'], via_arrays=s['via_arrays'], pads=s['pads'],
            islands=s['islands'], open_sinks=s['open_sinks'], dangling_cuts=s['dangling_cuts'], sheet_and_via_ohm=s['sheet_and_via_ohm'])
json.dump(summ, open(os.path.join(OUT, 'solve_summary.json'), 'w'), indent=1)
# ---- convergence (typ, trip_worst)
with open(os.path.join(OUT, 'mesh_convergence.csv'), 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['net', 'pitch_um', 'cells', 'max_node_drop_mV', 'em_route_wire', 'em_route_via', 'em_io_wire', 'em_io_via'])
    for net in NETS:
        for p, d in (('5.0', 'pitch_5.0'), ('2.5', 'pitch_2.5'), ('1.0', 'solve'), ('0.5', 'pitch_0.5')):
            if not os.path.exists('%s/%s/%s_typ_summary.json' % (B, d, net)): continue
            s = json.load(open('%s/%s/%s_typ_summary.json' % (B, d, net))); c = s['cases']['trip_worst']; e = c['em_max_by_origin']
            w.writerow([net, p, s['cells'], '%.3f' % c['max_node_drop_mV']] + ['%.4f' % e.get(k, 0) for k in ('route:wire', 'route:via', 'io:wire', 'io:via')])
# ---- cross-check
xr = []
for net in ('VDD', 'VSS', 'VDDA', 'GATE', 'SENSE_P', 'SENSE_N', 'i_core_vref'):
    ms = json.load(open('%s/xcheck/mesh/%s_typ_summary.json' % (B, net)))
    sq = '%s/xcheck/rnet_sq_%s.json' % (B, net); te = '%s/xcheck/rnet_tes_%s.json' % (B, net)
    rs = json.load(open(sq))['R_eff_ohm'] if os.path.exists(sq) else {}
    rt = json.load(open(te))['R_eff_ohm'] if os.path.exists(te) else {}
    for case, c in ms['cases'].items():
        g = case[2:]; d = c['ir'][g]
        xr.append([net, g, '%.3f' % d['mean_drop_mV'], '%.3f' % d['max_drop_mV'], '%.3f' % rs[g] if rs.get(g) else 'not run' if not rs else 'n/a',
                   '%.3f' % rt[g] if rt.get(g) else 'not run', '%+.1f' % (100 * (rs[g] - d['mean_drop_mV']) / d['mean_drop_mV']) if rs.get(g) else ''])
with open(os.path.join(OUT, 'crosscheck_reff.csv'), 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['net', 'sink_group', 'mesh_R_mean_ohm', 'mesh_R_max_ohm', 'klayout_pex_squarecounting_ohm', 'klayout_pex_tesselation_ohm', 'sq_vs_mesh_pct'])
    w.writerows(xr)
# ---- PSM macro
psm = {}
WID = {'Metal1': 0.44, 'TopMetal1': 2.2, 'TopMetal2': 2.2}
CUTS = {('Metal1', 'Metal2'): ('Via1', 5, 0.4), ('Metal2', 'Metal3'): ('Via2', 5, 0.4), ('Metal3', 'Metal4'): ('Via3', 5, 0.4),
        ('Metal4', 'Metal5'): ('Via4', 5, 0.4), ('Metal5', 'TopMetal1'): ('TopVia1', 2, 1.4), ('TopMetal1', 'TopMetal2'): ('TopVia2', 1, 10.0)}
JM = {'Metal1': 1.0, 'TopMetal1': 15.0, 'TopMetal2': 16.0}
for tag in ('stock_typ', 'stock_worst', 'chipfed_typ', 'chipfed_worst', 'chipfedtm1_typ', 'chipfedtm1_worst'):
    log = open('%s/psm/%s/psm.log' % (B, tag)).read()
    d = dict(total_power_W=float(re.search(r'^Total\s+\S+\s+\S+\s+\S+\s+(\S+)', log, re.M).group(1)))
    for m in re.finditer(r'Net\s+:\s+(\S+)\n(?:(?!Net).*\n)*?Average IR drop\s*:\s*(\S+) V\nWorstcase IR drop:\s*(\S+) V', log):
        d['%s_avg_ir_mV' % m.group(1)] = 1e3 * float(m.group(2)); d['%s_worst_ir_mV' % m.group(1)] = 1e3 * float(m.group(3))
    for net in ('VDD', 'VSS'):
        mx = collections.defaultdict(float)
        for r in list(csv.reader(open('%s/psm/%s/psm_em_%s.csv' % (B, tag, net))))[1:]:
            mx[(r[0], r[3])] = max(mx[(r[0], r[3])], abs(float(r[6])))
        em = {}
        for (l0, l1), i in sorted(mx.items()):
            imA = i * 1e3
            if l0 == l1:
                if l0 in WID: em[l0] = dict(max_mA=round(imA, 5), width_um=WID[l0], J_mA_per_um=round(imA / WID[l0], 5), utilisation=round(imA / WID[l0] / JM[l0], 5))
            elif (l0, l1) in CUTS:
                v, n, lim = CUTS[(l0, l1)]
                em[v] = dict(max_mA=round(imA, 5), cuts=n, per_cut_mA=round(imA / n, 5), utilisation=round(imA / n / lim, 5))
        d['em_' + net] = em
    psm[tag] = d
json.dump(psm, open(os.path.join(OUT, 'psm_macro.json'), 'w'), indent=1)
os.system('cp %s/loads/all_loads.json %s/loads.json' % (B, OUT))
geo = json.load(open('%s/geom/geometry_summary.json' % B)); geo['input'] = rel(geo['input'])
json.dump(geo, open(os.path.join(OUT, 'geometry_summary.json'), 'w'), indent=1)
print('rows', len(rows), 'over50', len(over), 'xcheck', len(xr))

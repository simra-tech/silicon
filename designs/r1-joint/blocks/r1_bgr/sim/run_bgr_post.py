#!/usr/bin/env python3
"""r1_bgr pre- vs post-layout runner (T7 layout track). Runs inside the pinned container:

  flow/run.sh python3 run_bgr_post.py <run-id> <pex-run-id>

<pex-run-id> is the directory <G1_RESULTS_ROOT>/r1_bgr/<pex-run-id>/ written by layout/pex_build.py
(r1_bgr_pex.spice = full RC, r1_bgr_pex_c.spice = layout devices + C with the wiring R shorted).
Reuses the decks and reducers of run_bgr.py (same testbench template, loads, options and corner names).
Views: sch = schematic/r1_bgr.spice (netlist of record), dev = layout devices + C (wiring R shorted), rc = full RC.
Checks: op (tt/27 C/3.3 V; port voltages for the IR drops), temp (tt, -40..125 C, 3.3 V), startup (10 us ramp to 3.0 V at
tt/27 C and ss/-40 C), stb (core loop, pbias gate cut, tt/27 C/3.3 V and ss/125 C/3.0 V).
Writes <G1_RESULTS_ROOT>/r1_bgr/<run-id>/ (decks, logs, data, summary.json) and results/<run-id>.json.
"""
import hashlib
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import run_bgr as B  # noqa: E402

ROOT = os.environ['G1_RESULTS_ROOT']
runid, pexid = sys.argv[1], sys.argv[2]
rundir = os.path.join(ROOT, 'r1_bgr', runid)
os.makedirs(rundir, exist_ok=False)
PEXD = os.path.join(ROOT, 'r1_bgr', pexid)
SCH = os.path.join(HERE, '..', 'schematic', 'r1_bgr.spice')
VIEWS = {'sch': SCH, 'dev': os.path.join(PEXD, 'r1_bgr_pex_c.spice'), 'rc': os.path.join(PEXD, 'r1_bgr_pex.spice')}


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


assert sha(SCH) == B.NETLIST_SHA
summary = dict(run_id=runid, pex_run=pexid, started=time.strftime('%Y-%m-%dT%H:%M:%S'),
               netlists={k: dict(path=('<G1_RESULTS_ROOT>/r1_bgr/%s/%s' % (pexid, os.path.basename(v)) if k != 'sch'
                                       else 'designs/r1-joint/blocks/r1_bgr/schematic/r1_bgr.spice'), sha256=sha(v))
                         for k, v in VIEWS.items()})
TT = ('hbt_typ', 'mos_tt', 'res_typ')
items, meta = [], []

# --- op with all node voltages (IR drops)
CTL_OPW = """.control
set filetype=ascii
option temp=27
op
let idd = -i(vdd)
let iptat = i(vload)
print v(vref) v(dvbe) v(vbe) idd iptat
write @@OUT@@.raw all
.endc
"""
for v in ('sch', 'rc'):
    out = os.path.join(rundir, 'op_%s' % v)
    open(out + '.cir', 'w').write(B.deck('op', VIEWS[v], *TT, 3.3, CTL_OPW.replace('@@OUT@@', out)))
    items.append((out + '.cir', out + '.log'))
    meta.append(('op', v, out))
# --- temperature sweep at tt
for v in ('sch', 'dev', 'rc'):
    out = os.path.join(rundir, 'temp_%s' % v)
    open(out + '.cir', 'w').write(B.deck('temp', VIEWS[v], *TT, 3.3, B.CTL_TEMP.replace('@@OUT@@', out)))
    items.append((out + '.cir', out + '.log'))
    meta.append(('temp', v, out))
# --- start-up, 10 us ramp to 3.0 V
SU = [('tt27', 'hbt_typ', 'mos_tt', 'res_typ', 27), ('ss_m40', 'hbt_wcs', 'mos_ss', 'res_wcs', -40)]
for v in ('sch', 'rc'):
    for name, h, m, r, t in SU:
        out = os.path.join(rundir, 'su_%s_%s' % (name, v))
        ctl = B.CTL_START
        for k, val in dict(TEMP=t, TRAMP=10e-6, VDD=3.0, TEND=1e-3, TSTEP=0.2e-6, OUT=out, V99='1.0').items():
            ctl = ctl.replace('@@%s@@' % k, str(val))
        d = B.deck('startup', VIEWS[v], h, m, r, 3.0, ctl).replace('Vdd vdd 0 dc 3.0', 'Vdd vdd 0 dc 3.0 pwl(0 0 1 3.0)')
        open(out + '.cir', 'w').write(d)
        items.append((out + '.cir', out + '.log'))
        meta.append(('su', v, name, h, m, r, t, out))
# --- core loop gain, pbias gate cut


def cut_pbias(text, view):
    """move the gates of the PMOS mirror devices (gate on pbias) to pbias_rx; add the Tian probe before .ends"""
    out, moved = [], 0
    for l in text.splitlines():
        t = l.split()
        if view == 'sch':
            ok = t and t[0].startswith('XMP') and not t[0].startswith('XMPI') and len(t) > 2 and t[2] == 'pbias'
        else:
            ok = t and t[0].startswith('XM') and 'sg13_hv_pmos' in t and len(t) > 2 and t[2] == 'pbias'
        if ok:
            t[2] = 'pbias_rx'
            moved += 1
            l = ' '.join(t)
        if l.strip() == '.ends':
            out.append('Vprobe pbias pbias_rx dc 0 ac {vinj}')
            out.append('Iprobe 0 pbias dc 0 ac {iinj}')
        out.append(l)
    return '\n'.join(out) + '\n', moved


STB = [('tt27_3v3', 'hbt_typ', 'mos_tt', 'res_typ', 27, 3.3), ('ss125_3v0', 'hbt_wcs', 'mos_ss', 'res_wcs', 125, 3.0)]
moved = {}
for v in ('sch', 'rc'):
    ptxt, moved[v] = cut_pbias(open(VIEWS[v]).read(), v)
    pn = os.path.join(rundir, 'stb_net_%s.spice' % v)
    open(pn, 'w').write(ptxt)
    for cname, h, m, r, t, vd in STB:
        out = os.path.join(rundir, 'stb_%s_%s' % (cname, v))
        ctl = B.CTL_STB.replace('@@NET@@', 'pbias').replace('@@OUT@@', out)
        dk = B.deck('stb', pn, h, m, r, vd, ctl).replace('.global sub!', '.global sub!\n.param vinj=1 iinj=0\n.temp %g' % t)
        open(out + '.cir', 'w').write(dk)
        items.append((out + '.cir', out + '.log'))
        meta.append(('stb', v, cname, t, vd, out))
summary['stb_moved_gates'] = moved

t0 = time.time()
res = B.run_all(items)
summary['wall_s'] = round(time.time() - t0, 1)


def logval(path, key):
    for l in open(path, errors='replace'):
        s = l.strip()
        if s.startswith(key + ' ') or s.startswith(key + '='):
            try:
                return float(s.split('=')[1].split()[0])
            except Exception:
                pass
    return None


def read_raw(path):
    """ASCII raw file of an op: {vector name: value}"""
    names, vals, mode = [], [], None
    for l in open(path, errors='replace'):
        if l.startswith('Variables:'):
            mode = 'var'
            continue
        if l.startswith('Values:'):
            mode = 'val'
            continue
        if mode == 'var':
            f = l.split()
            if len(f) >= 2:
                names.append(f[1])
        elif mode == 'val':
            for x in l.split():
                try:
                    vals.append(float(x))
                except ValueError:
                    pass
    vals = vals[1:] if len(vals) == len(names) + 1 else vals
    return dict(zip(names, vals))


rows = dict(op={}, temp={}, startup=[], stb=[])
for mt, (path, rc, dt) in zip(meta, res):
    if mt[0] == 'op':
        _, v, out = mt
        r = dict(rc=rc, seconds=round(dt, 1))
        for k in ('v(vref)', 'v(dvbe)', 'v(vbe)', 'idd', 'iptat'):
            r[k] = logval(out + '.log', k)
        try:
            raw = read_raw(out + '.raw')
            r['n_vectors'] = len(raw)
            if v == 'rc':
                pick = {k: x for k, x in raw.items() if k.startswith('v(xbgr.') and ('__' in k)}
                json.dump(pick, open(out + '_ports.json', 'w'))
                r['port_voltages_file'] = os.path.basename(out) + '_ports.json'
        except Exception as e:
            r['raw_error'] = str(e)
        rows['op'][v] = r
    elif mt[0] == 'temp':
        _, v, out = mt
        r = dict(rc=rc, seconds=round(dt, 1))
        try:
            d = B.readdat(out + '.dat')
            T = d[list(d)[0]]
            vv = d['v(vref)']
            r.update(vref27=B.val_at(T, vv, 27), vref_m40=B.val_at(T, vv, -40), vref125=B.val_at(T, vv, 125), tc_box=B.tcbox(T, vv),
                     iptat27_uA=B.val_at(T, d['iptat'], 27) * 1e6, idd27_uA=B.val_at(T, d['idd'], 27) * 1e6,
                     idd_max_uA=max(d['idd']) * 1e6, dvbe27_mV=B.val_at(T, d['v(dvbe)'], 27) * 1e3)
        except Exception as e:
            r['error'] = str(e)
        rows['temp'][v] = r
    elif mt[0] == 'su':
        _, v, name, h, m, r_, t, out = mt
        row = dict(view=v, case=name, hbt=h, mos=m, res=r_, temp=t, ramp='10us', rc=rc, seconds=round(dt, 1))
        for k in ('vref_end', 'iptat_end', 't_99', 'vref_max'):
            row[k] = logval(out + '.log', k)
        try:
            d = B.readdat(out + '.dat')
            tt = d[list(d)[0]]
            vv = d['v(vref)']
            ve = vv[-1]
            tset = None
            for i in range(len(vv) - 1, -1, -1):
                if abs(vv[i] - ve) > 0.01 * ve:
                    tset = tt[i + 1] if i + 1 < len(tt) else tt[i]
                    break
            row['t_settle_1pct'] = tset
            row['ok'] = bool(0.95 < ve < 1.15 and abs(row.get('iptat_end') or 0) > 1e-6)
        except Exception as e:
            row['error'] = str(e)
            row['ok'] = False
        rows['startup'].append(row)
    else:
        _, v, cname, t, vd, out = mt
        row = dict(view=v, case=cname, temp=t, vdd=vd, rc=rc, seconds=round(dt, 1))
        try:
            c = B.read_cols(out + '.dat')
            row.update(B.curve_margins(c[0], c[1], c[2]))
            row['pass_pm60'] = True if row['pm_deg'] is None else row['pm_deg'] >= 60
            row['pass_gm10'] = True if row['gm_db'] is None else row['gm_db'] >= 10
            row['vref_op'] = logval(out + '.log', 'v(vref)')
        except Exception as e:
            row['error'] = str(e)
        rows['stb'].append(row)
summary['rows'] = rows
os.makedirs(os.path.join(HERE, 'results'), exist_ok=True)
json.dump(summary, open(os.path.join(HERE, 'results', runid + '.json'), 'w'), indent=1)
json.dump(summary, open(os.path.join(rundir, 'summary.json'), 'w'), indent=1)
print(json.dumps(dict(op=rows['op'], temp=rows['temp']), indent=1)[:4000])
for r in rows['startup'] + rows['stb']:
    print({k: r.get(k) for k in ('view', 'case', 'rc', 'seconds', 'vref_end', 't_settle_1pct', 'vref_max', 'ok', 'pm_deg', 'gm_db', 'f_unity', 'error')})

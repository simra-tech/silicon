#!/usr/bin/env python3
"""Print a compact summary of results/<run-id>.json (host or container, Python >= 3.6)."""
import json, math, sys

GAINS = ['x1', 'x2', 'x4', 'x8', 'x16', 'x32']
LSB = 2.4 / 4096

def main(rid):
    res = json.load(open('results/%s.json' % rid))
    for j in res:
        print('== %s rc=%s %ss %s' % (j['name'], j['rc'], j['seconds'], ('ERR ' + '; '.join(j['errors'][:2])) if j['errors'] else ''))
        for r in j['rows']:
            t = r['tag']
            if t == 'ACROW' and isinstance(r.get('fs3'), str):
                print('  ACROW with failed measure: %s' % r)
            elif t == 'ACROW':
                print('  mc%-2d %-4s g=%7.3f/%7.3f f3=%.3f/%.3f MHz pk=%.2f dB ph100k=%.2f/%.2f deg dph=%.3f df3=%.2f%%' % (
                    r['mc'], GAINS[int(r['code'])], 10 ** (r['gs0'] / 20), 10 ** (r['gc0'] / 20), r['fs3'] / 1e6, r['fc3'] / 1e6,
                    max(r['pks'], r['pkc']), r['ps100'], r['pc100'], r['ps100'] - r['pc100'], 100 * (r['fs3'] / r['fc3'] - 1)))
            elif t == 'OPROW' and r.get('mc', 0) == 0:
                print('  op %-4s ocm=%.4f/%.4f o1cm=%.4f idd=%.3f mA' % (GAINS[int(r['code'])], r['ocms'], r['ocmc'], r['o1cm'], r['idd'] * 1e3))
            elif t == 'NZROW':
                print('  %-4s gain=%.3f out=%.1f uV (%.2f LSB) in=%.1f uV  in@1k/10k/100k/1M = %.0f/%.0f/%.0f/%.0f nV/rtHz' % (
                    GAINS[int(r['code'])], r['gain'], r['onoise_rms'] * 1e6, r['onoise_rms'] / LSB, r['in_rms'] * 1e6,
                    r['in1k'] * 1e9, r['in10k'] * 1e9, r['in100k'] * 1e9, r['in1m'] * 1e9))
            elif t == 'THDROW':
                print('  THD %.4f %% (%.1f dB)' % (r['thd_percent'], 20 * math.log10(r['thd_percent'] / 100)))
            elif t == 'TRROW':
                print('  %-4s diff pk %.4f/%.4f V, sin out+ %.3f..%.3f V, out- %.3f..%.3f V, ocm %.4f, CM pp out/stage1 %.2g/%.2g V' % (
                    GAINS[int(r['code'])], r['smax'], r['smin'], r['splo'], r['sphi'], r['snlo'], r['snhi'],
                    r.get('ocm', float('nan')), r.get('ocmpp', float('nan')), r.get('o1cmpp', float('nan'))))
            else:
                print('  ' + ' '.join('%s=%s' % (k, ('%.4g' % v) if isinstance(v, float) else v) for k, v in r.items()))

if __name__ == '__main__':
    main(sys.argv[1])

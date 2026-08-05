#!/usr/bin/env python3
"""C80-V4 fail-closed verifier (relative paths only; run from this directory).
Scans ALL 12 files (including this one) for forbidden literals built at runtime
from noncontiguous pieces, so no forbidden text appears in this source."""
import hashlib, json, math, re, struct, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
fails = []
def check(cond, msg):
    print(('PASS' if cond else 'FAIL'), msg)
    if not cond:
        fails.append(msg)

def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()

def norm(s):
    return re.sub(r'\s+', ' ', s).lower()

# Forbidden fragments, assembled at runtime from noncontiguous pieces so their
# literal text is absent from this file (the package-wide scan includes it).
WSP = '/vol' + 'ume/us' + 'er'      # workspace prefix
HOME = '/hom' + 'e/'                # home prefix
PEM = 'BEGIN PRI' + 'VATE KEY'      # private-key header
RP = 'raw' + ' prompt'              # raw-prompt marker
REA = 'chain-of' + '-thought'       # reasoning marker
RMK = 'system-' + 'reminder'        # injected-instruction marker

# 0. package-wide literal scan: EVERY file including verify.py
ALL = [f for f in os.listdir('.') if os.path.isfile(f)]
for f in sorted(ALL):
    text = open(f, 'r', errors='replace').read()
    check(WSP not in text, f'no workspace-prefix literal in {f}')
    check(HOME not in text, f'no home-prefix literal in {f}')
    check(PEM not in text, f'no private-key header in {f}')
    check(not re.search(r'sim-[0-9a-f]{32,}', text), f'no long sim-ID in {f}')
    check(not re.search(r'sk-[A-Za-z0-9]{20,}', text), f'no credential-like token in {f}')
    low = text.lower()
    check(RP not in low and REA not in low and RMK not in low,
          f'no prompt/reasoning markers in {f}')

# 1. exact file set (the 12 files)
required = {
    'C45-V1-SOURCE-p1_top_hier_v3-no-bleed-wrapped-damp35-ls-hbtv-nx4el5.spice',
    'C75-V1-SOURCE-p1_hybrid.spice',
    'C76-V1-AC-TRACKPHASE-HYBRID-CANDIDATE-ONLY.cir',
    'c76-V1-AC-TRACKPHASE-HYBRID-CANDIDATE-ONLY.op.raw',
    'c76-V1-AC-TRACKPHASE-HYBRID-CANDIDATE-ONLY.raw',
    'c76-V1-run.log', 'c76-V1-run.stdout.log',
    'README.md', 'FACTS.json', 'BINDINGS.json', 'verify.py', 'SHA256SUMS'}
present = {f for f in os.listdir('.') if os.path.isfile(f)}
check(present == required, f'exact file set ({len(present)} present, expected {len(required)})')

# 2. BINDINGS.json loads and matches the file hashes
b = json.load(open('BINDINGS.json'))
for name, h in b['files'].items():
    check(sha(name) == h, f'BINDINGS file hash {name}')

# 3. SHA256SUMS covers the other 11 files with matching hashes
sums = {}
for line in open('SHA256SUMS'):
    parts = line.split()
    if len(parts) == 2:
        sums[parts[1]] = parts[0]
check(set(sums) == required - {'SHA256SUMS'}, 'SHA256SUMS covers the other 11 files')
for name, h in sums.items():
    check(h == sha(name), f'SHA256SUMS hash {name}')

# 4. deck: the portable deck hash + the two local include operands (the native
#    deck hash 3beb35b7 is bound as PROVENANCE ONLY — no reconstruction)
check(sha('C76-V1-AC-TRACKPHASE-HYBRID-CANDIDATE-ONLY.cir') ==
      b['provenance']['portable_deck_646ca890'], 'portable deck hash 646ca890')
deck = open('C76-V1-AC-TRACKPHASE-HYBRID-CANDIDATE-ONLY.cir').read()
inc = re.findall(r'^\.include (\S+)$', deck, re.M)
check(inc == ['C45-V1-SOURCE-p1_top_hier_v3-no-bleed-wrapped-damp35-ls-hbtv-nx4el5.spice',
              'C75-V1-SOURCE-p1_hybrid.spice'],
      f'deck include operands are exactly the two local basenames ({inc})')
check('/' not in ' '.join(inc), 'include operands contain no path separators')

# 5. C45 derivative scope: noncomment electrical-line hash equals the bound value
def noncomment_hash(p):
    lines = [l for l in open(p).read().splitlines() if not l.lstrip().startswith('*')]
    return hashlib.sha256(('\n'.join(lines) + '\n').encode()).hexdigest()
check(noncomment_hash('C45-V1-SOURCE-p1_top_hier_v3-no-bleed-wrapped-damp35-ls-hbtv-nx4el5.spice') ==
      b['provenance']['c45_noncomment_electrical_line_hash'],
      'C45 noncomment electrical-line hash equals the bound value (scrub touched only comments)')
check(b['provenance']['c45_original_executed_source_102f2a9d'].startswith('102f2a9d'),
      'C45 original executed-source hash bound as provenance (102f2a9d)')

# 6. raw dimensions/payload/finiteness/monotonicity
def parse_raw(p):
    data = open(p, 'rb').read()
    hdr = data[:data.find(b'Binary:')].decode('latin1')
    nv = int(re.search(r'No\. Variables:\s*(\d+)', hdr).group(1))
    np_ = int(re.search(r'No\. Points:\s*(\d+)', hdr).group(1))
    flags = re.search(r'Flags:\s*(\S+)', hdr).group(1)
    vnames = re.findall(r'^\t\d+\t(\S+)\t', hdr, re.M)
    off = data.find(b'Binary:') + 8
    comp = 2 if flags == 'complex' else 1
    payload = np_ * nv * comp * 8
    check(len(data) - off == payload, f'{p} payload byte-exact ({len(data)-off} == {payload})')
    vals = struct.unpack(f'<{np_*nv*comp}d', data[off:])
    check(all(math.isfinite(v) for v in vals), f'{p} all values finite')
    return nv, np_, flags, vnames, vals
onv, onp, oflags, ovn, oval = parse_raw('c76-V1-AC-TRACKPHASE-HYBRID-CANDIDATE-ONLY.op.raw')
check(onv == 20 and onp == 1 and oflags == 'real', 'OP raw 20x1 real')
anv, anp, aflags, avn, aval = parse_raw('c76-V1-AC-TRACKPHASE-HYBRID-CANDIDATE-ONLY.raw')
check(anv == 21 and anp == 201 and aflags == 'complex', 'AC raw 21x201 complex')
freq = [aval[(p*anv)*2] for p in range(anp)]
check(all(freq[i] < freq[i+1] for i in range(anp-1)), 'AC frequency monotone')

# 7. the 40 scalar values: recount from the AC raw (log-f interpolation) vs
#    FACTS.json; magnitude and phase counted SEPARATELY (20 mag + 20 ph = 40)
facts = json.load(open('FACTS.json'))
i = {n: k for k, n in enumerate(avn)}
def col(k): return [complex(aval[(p*anv+k)*2], aval[(p*anv+k)*2+1]) for p in range(anp)]
probes = facts['probe_frequencies_hz']
fkeys = ['10m', '100m', '1g', '2g5', '5g']
ok = 0
for name in ('ga', 'gb', 'load', 'ydm'):
    for fk, f in zip(fkeys, probes):
        j = max(q for q in range(anp-1) if freq[q] <= f)
        lf = math.log10
        w = (lf(f)-lf(freq[j]))/(lf(freq[j+1])-lf(freq[j]))
        def v(n):
            c = col(i[n]); return c[j] + w*(c[j+1]-c[j])
        if name == 'ga':
            val = (v('v(noise_amp_pa)')-v('v(noise_amp_na)')) / (v('v(raw_noise_pa)')-v('v(raw_noise_na)'))
        elif name == 'gb':
            val = (v('v(xhyb.ls_p)')-v('v(xhyb.ls_n)')) / (v('v(raw_noise_pb)')-v('v(raw_noise_nb)'))
        elif name == 'load':
            val = (v('v(noise_amp_pb)')-v('v(noise_amp_nb)')) / (v('v(noise_amp_pa)')-v('v(noise_amp_na)'))
        else:
            val = ((v('i(vbase_pb)')-v('i(vbase_nb)'))/2) / (v('v(ls_base_pb)')-v('v(ls_base_nb)'))
        mg, ph = abs(val), math.atan2(val.imag, val.real)
        exp_m = facts['scalars_40'][f'{name}_mag_{fk}']
        exp_p = facts['scalars_40'][f'{name}_ph_{fk}']
        ok += int(abs(mg-exp_m)/abs(exp_m) < 2e-4) + int(abs(ph-exp_p) < 2e-4)
check(ok == 40, f'40 scalar values (20 mag + 20 ph of the four complex responses) recounted from raw match FACTS.json ({ok}/40)')

# 8. warning counts (literal)
logtext = open('c76-V1-run.log').read()
wc = facts['warning_counts']
got = {
    'warning_tokens': len(re.findall(r'warning', logtext, re.I)),
    'warning_lines': sum(1 for l in open('c76-V1-run.log') if re.search(r'warning', l, re.I)),
    'complete_vmax_phrases': len(re.findall(r'voltage is greater than specified by vmax', logtext)),
    'complete_nxampa_tokens': len(re.findall(r'n\.xampa\.[a-z0-9_]+\.nr1', logtext)),
    'truncated_prefix_tokens': len(re.findall(r'^\.x[a-z0-9_]+\.nr1', logtext, re.M)),
    'thermal_nan_notices': len(re.findall(r'temperature limiting function received nan', logtext, re.I)),
    'errors': len(re.findall(r'error|failed!|no such|unable|fatal', logtext, re.I))}
check(got == wc, f'warning counts match FACTS.json ({got})')

# 9. cautious claims in README + FACTS — whitespace-normalized (wrap-insensitive)
readme_n = norm(open('README.md').read())
for phrase in ['provisional', 'ac-experiment-only', 'never native pex',
               'no bandwidth decision', 'p1 open', 'not "content-identical"',
               'not "header-only"', 'path-scrubbed derivative']:
    check(norm(phrase) in readme_n, f'README contains cautious claim: {phrase!r}')
check(facts['claims_scope']['provisional'] and facts['claims_scope']['ac_experiment_only']
      and facts['claims_scope']['never_native_pex'] and facts['claims_scope']['no_bandwidth_gate']
      and facts['claims_scope']['no_pex_pass_signoff_claim'] and facts['claims_scope']['p1_open'],
      'FACTS claims scope flags all set')
check(facts['derivative_scope']['c45_path_scrubbed'] and
      facts['derivative_scope']['c45_noncomment_electrical_line_hash'] ==
      b['provenance']['c45_noncomment_electrical_line_hash'],
      'FACTS derivative scope consistent (C45 path-scrubbed derivative)')

print()
if fails:
    print(f'RESULT: FAIL ({len(fails)} failing checks)')
    sys.exit(1)
print('RESULT: PASS')


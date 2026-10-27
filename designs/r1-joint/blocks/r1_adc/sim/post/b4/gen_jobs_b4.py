#!/usr/bin/env python3
"""Layout B4 campaign job files (sim/post/run_qpost.sh format). Reads the slice reference / ground port tokens of
Xslice_a / Xslice_b in r1_adc_lay_pr of the merged B4 netlist, then writes:
  jobs_b4_103.txt  INL ramp half a (tt, ideal VREF 1.045 V)
  jobs_b4_104.txt  INL ramp half b
  jobs_b4_105.txt  OP tt / base netlist / R2-4 tt; OP ss125 / base / R2-4 ss125; mux tt, ss125, ffm40; first conversion
                   tt and ss125; supply-R what-if mux tt (IR-drop share)
usage (repo root): python3 designs/r1-joint/blocks/r1_adc/sim/post/b4/gen_jobs_b4.py <tag>   (tag b4 -> netlist mb4)"""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
POST = os.path.dirname(HERE)
tag = sys.argv[1]
NL = 'sim/post/r1_adc_post_rc_m%s.spice' % tag
src = open(os.path.join(POST, os.path.basename(NL))).read().split('\n')
inpr = False
ports = {}
for ln in src:
    if ln.startswith('.subckt r1_adc_lay_pr '):
        inpr = True
    elif ln.startswith('.ends'):
        inpr = False
    elif inpr and re.match(r'Xslice_[ab] ', ln):
        t = ln.split()
        ports[t[0][-1]] = dict(vref=[x for x in t if re.match(r'vref__p\d+$', x)], vrefl=[x for x in t if re.match(r'vrefl__p\d+$', x)],
                               vss=[x for x in t if re.match(r'vss__p\d+$', x)])
assert set(ports) == {'a', 'b'}, ports
probe = ' '.join('v(xadc.xl.%s)' % x for s in 'ab' for k in ('vref', 'vrefl') for x in ports[s][k]) + \
        ' v(xadc.xl.%s) v(xadc.xl.%s) v(xadc.xl.xslice_a.lsb_p)' % (ports['a']['vss'][0], ports['b']['vss'][0])
mid = lambda s: ports[s]['vref'][len(ports[s]['vref']) // 2]
save = 'v(xadc.xl.%s) v(xadc.xl.%s) v(xadc.xl.%s) v(xadc.xl.%s)' % (mid('a'), mid('b'), ports['a']['vrefl'][0], ports['b']['vrefl'][0])
json.dump(dict(ports=ports, probe=probe, save=save, va_vb='v(xadc.xl.%s),v(xadc.xl.%s)' % (mid('a'), mid('b')),
               vla_vlb='v(xadc.xl.%s),v(xadc.xl.%s)' % (ports['a']['vrefl'][0], ports['b']['vrefl'][0])),
          open(os.path.join(HERE, 'ports_%s.json' % tag), 'w'), indent=1)
R = 'python3 sim/post/run_post.py'
L = 'layout B4'
SS = '--corner mos_ss --temp 125 --vdd 1.08'
FF = '--corner mos_ff --temp -40 --vdd 1.32'
p = 'post%s' % tag
def ref_block(cn, cflag):
    sp = 'sim/post/r1_adc_post_rc_m%s_sp_%s.spice' % (tag, cn)
    return [
        '%s --id %s-op-%s-rc --cpu @CPU@ --deck points --core lay --netlist %s --solver sparse --ref lay %s --points sim/r5/points/ref10.json --op-only --probe-extra "%s" --question "post-layout RC (%s): operating point %s with all slice reference port nodes" --disposition "post-layout op (RC, %s)"' % (R, p, cn, NL, cflag, probe, L, cn, L),
        'python3 sim/post/make_sp_netlist.py %s %s %s-op-%s-rc --per-port' % (NL, sp, p, cn),
        '%s --id %s-op-%s-sp --cpu @CPU@ --deck points --core lay --netlist %s --solver sparse --ref lay %s --points sim/r5/points/ref10.json --op-only --probe-extra "%s" --question "R2-4 base netlist check %s (%s): slice reference ports forced at the buffer-OP values" --disposition "diagnosis"' % (R, p, cn, sp, cflag, probe, cn, L),
        '%s --id %s-ref-%s-rc --cpu @CPU@ --deck points --core lay --netlist %s --solver sparse --ref lay %s --points sim/r5/points/ref10.json --save full --save-extra "%s" --question "post-layout RC (%s): R2-4 reference settling %s, slice-port reference nodes saved" --disposition "post-layout value (R2-4 %s, RC, %s)"' % (R, p, cn, NL, cflag, save, L, cn, cn, L),
        '%s --id %s-ref-%s-sp --cpu @CPU@ --deck points --core lay --netlist %s --solver sparse --ref lay %s --points sim/r5/points/ref10.json --save full --question "post-layout RC (%s): R2-4 base run %s, ideal DC sources at each slice reference port" --disposition "post-layout R2-4 base (RC, slice-port ideal, %s)"' % (R, p, cn, sp, cflag, L, cn, L)]
j105 = ['# %s, CPU 105: R2-4 tt and ss125, mux tt / ss125 / ffm40, first conversion tt / ss125, supply-R what-if (IR-drop share)' % L]
j105 += ref_block('tt', '')
j105 += ref_block('ss125', SS)
for cn, cf in (('tt', ''), ('ss125', SS), ('ffm40', FF)):
    j105.append('%s --id %s-isa-%s-rc --cpu @CPU@ --deck isa --core lay --netlist %s --solver sparse --ref lay %s --question "post-layout RC (%s, merged, sparse): mux sequence %s, 33 ns hold pulse, buffer + bandgap model; gain, offset, full scale, IDD, output word timing" --disposition "post-layout value (mux %s, RC, %s)"' % (R, p, cn, NL, cf, L, cn, cn, L))
j105.append('%s --id %s-fc-tt-rc --cpu @CPU@ --deck points --core lay --ref lay-ideal --vref 1.045 --netlist %s --solver sparse --points sim/r5/points/fixtt.json --timing r1_adc_timing_r5_n0_cq_pre33.inc --question "post-layout RC (%s): first conversion with the 33 ns hold pulse, tt, 0 V in frames 0 and 1" --disposition "post-layout value (first conversion tt, %s)"' % (R, p, NL, L, L))
j105.append('%s --id %s-fc-ss125-rc --cpu @CPU@ --deck points --core lay --ref lay-ideal --vref 1.045 --netlist %s --solver sparse %s --points sim/post/points/ffb.json --timing r1_adc_timing_r5_n0_cq_vdd108_pre33.inc --question "post-layout RC (%s): first conversion with the 33 ns hold pulse, ss/125 C/1.08 V, -0.80 V (sim/post/points/ffb.json)" --disposition "post-layout value (first conversion ss125, %s)"' % (R, p, NL, SS, L, L))
dn = 'sim/post/b4/r1_adc_post_rc_m%s_rsup001.spice' % tag
j105.append('python3 sim/post/make_diag_netlist.py %s %s --r-scale gnd,vdd,vss,vdda:0.01' % (NL, dn))
j105.append('%s --id %s-diag-isa-tt-rsup001 --cpu @CPU@ --deck isa --core lay --netlist %s --solver sparse --ref lay --question "diagnosis (%s): mux tt with the supply and ground wiring R (gnd, vdd, vss, vdda) scaled by 0.01; IR-drop share of IDD and gain" --disposition "diagnosis"' % (R, p, dn, L))
open(os.path.join(POST, 'jobs_%s_105.txt' % tag), 'w').write('\n'.join(j105) + '\n')
for cpu, half in (('103', 'a'), ('104', 'b')):
    open(os.path.join(POST, 'jobs_%s_%s.txt' % (tag, cpu)), 'w').write(
        '# %s, CPU %s: INL ramp half %s\n%s --id %s-inl%s-tt-rc --cpu @CPU@ --deck points --core lay --ref lay-ideal --vref 1.045 --netlist %s --solver sparse --points sim/r5/points/inlramp5%s.json --question "post-layout RC (%s): reduced INL ramp half %s (sim/r5/points/inlramp5%s.json), tt, ideal VREF 1.045 V" --disposition "post-layout value (INL bow tt, %s)"\n'
        % (L, cpu, half, R, p, half, NL, half, L, half, half, L))
print(json.dumps(ports))

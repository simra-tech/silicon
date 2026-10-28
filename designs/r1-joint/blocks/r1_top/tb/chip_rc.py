"""Sixth budget, chip view (`run_tb.py --chip-rc`): the top-level routing RC of try g (track T11, run pex-20261029-g3,
fast variant, subckt r1_top_rc) inserted between the block pins of the deck netlist r1_chip.sp.

Method:
1. The wrapper r1_top_pex of the RC file gives, per CDL instance, the RC port node of every pin (u_<inst>__<pin>,
   io_<pad>__<pin>), in CDL pin order.
2. Each block, pad and ctrl pin of the deck is moved from its deck net to its RC port node: by position where the
   deck pin list equals the CDL one (pads, analog blocks), by name for r1_adc (the CDL has 4 more pins) and for the
   ctrl wrapper r1_ctrl_top_tb (CTRL_MAP below; testbench pins stay on their deck nets).
3. The RC instance Xrc is added. Its top ports are the pad and supply nets of the deck (same names).
4. A deck net that is not an RC top port is tied by a 0 V source to the RC node of its first moved pin, so that
   the testbench parts on that net (stubs, MODEL sources, loads, probes) stay connected there.
5. A non-supply pin that the deck ties to a supply net (deviations D11 T2F enable at VSS, r1_gate gate_en at VDD)
   keeps that tie (deck deviation kept).
"""
import re

SUPPLIES = {'VDD', 'VSS', 'VDDA', 'IOVDD', 'IOVSS'}
SUPPLY_PINS = {'vdd', 'vss', 'vdda', 'vdd12', 'iovdd', 'iovss'}
# deck ctrl wrapper pin (r1_ctrl_top_tb, after the "p_" prefix) -> CDL r1_ctrl_top pin
CTRL_MAP = {'osc_clk': 'clk', 'por_n': 'por_n', 'cs_n_p2c': 'cs_n', 'ma_sclk_p2c': 'ma_sclk', 'sdi_p2c': 'sdi',
            'en_sto_in_p2c': 'en_pad', 'cmp_oc_a': 'cmp_0', 'cmp_neg_a': 'cmp_1', 'cmp_oc_b': 'cmp_2',
            'cmp_neg_b': 'cmp_3', 't2f_fout': 't2f_clk', 'adc_valid_a': 'adc_valid_a', 'adc_valid_b': 'adc_valid_b',
            'slo_sdo_c2p': 'slo_sdo', 'fault_n_c2p': 'fault_n', 'pwm_a': 'gate_a', 'pwm_b': 'gate_b',
            'pwm_c': 'gate_c', 'adc_hold': 'adc_hold', 'is_smp': 'is_smp', 'adc_start': 'adc_start',
            'adc_sel': 'adc_sel', 't2f_en': 't2f_en', 't2f_mode': 't2f_mode', 'bias_en': 'bias_en',
            'cur_trk': 'cur_trk', 'vdd': 'vdd', 'vss': 'vss'}
for _k in range(14):
    CTRL_MAP['adc_raw_a%d' % _k] = 'adc_raw_a_%d' % _k
    CTRL_MAP['adc_raw_b%d' % _k] = 'adc_raw_b_%d' % _k
for _k in range(32):
    CTRL_MAP['tap_p%d' % _k] = 'tap_p_%d' % _k
    CTRL_MAP['tap_n%d' % _k] = 'tap_n_%d' % _k
for _k in range(5):
    CTRL_MAP['osc_trim%d' % _k] = 'osc_trim_%d' % _k
for _k in range(4):
    CTRL_MAP['pga_c%d' % _k] = 'pga_c_%d' % _k


def _join(txt):
    out = []
    for l in txt.splitlines():
        if l.startswith('+') and out:
            out[-1] += ' ' + l[1:]
        else:
            out.append(l)
    return out


def load_rc(path):
    L = open(path).read().splitlines()
    i = [k for k, l in enumerate(L) if l.startswith('.subckt r1_top_pex')][0]
    inst, xrc = {}, None
    for l in L[i + 1:]:
        if l.startswith('.ends'):
            break
        t = l.split()
        if t[0] == 'Xrc':
            xrc = ' '.join(x for x in t if not x.startswith('ictrl_p')) + ' ictrl_p=0'
            continue
        inst[t[0][1:].lower()] = (t[1:-1], t[-1])
    return inst, xrc


def chip_rc_pass(chip, rc_path, ctrl_pins):
    """chip: deck r1_chip text; ctrl_pins: pin names of r1_ctrl_top_tb (with the p_ prefix). Returns text, report."""
    inst, xrc = load_rc(rc_path)
    lines = _join(chip)
    first = {}            # deck net -> RC node of its first moved pin
    moved, kept, out = 0, [], []
    for l in lines:
        if not l.startswith('X'):
            out.append(l)
            continue
        t = l.split()
        name = t[0][1:].lower()
        key = 'io_' + name[2:] if name.startswith('p_') else name
        nets, cell = t[1:-1], t[-1]
        if key == 'u_ctrl':
            cdl = {n.split('__', 1)[1]: n for n in inst['u_ctrl'][0]}
            pins = [p[2:] if p.startswith('p_') else p for p in ctrl_pins]
            nodes = [cdl.get(CTRL_MAP.get(p, ''), None) for p in pins]
        elif key in inst:
            cdl_nodes = inst[key][0]
            if key == 'u_adc':
                cdl_nodes = [n for n in cdl_nodes if not n.endswith('_nc')]
            if len(cdl_nodes) != len(nets):
                kept.append('%s: pin count %d against %d, not moved' % (name, len(nets), len(cdl_nodes)))
                out.append(l)
                continue
            nodes = list(cdl_nodes)
        else:
            out.append(l)
            continue
        new = []
        for net, node in zip(nets, nodes):
            pin = node.split('__', 1)[1] if node else ''
            if node is None or (net in SUPPLIES and pin.lower() not in SUPPLY_PINS):
                new.append(net)
                continue
            new.append(node)
            moved += 1
            if net not in SUPPLIES and not re.fullmatch(r'[A-Z_]+', net or '') and net not in first:
                first[net] = node
        out.append(' '.join([t[0]] + new + [cell]))
    out.append('* ---------------- chip view: top-level routing RC of try g (r1_top_rc, fast variant) ----------------')
    out.append(xrc)
    for net, node in sorted(first.items()):
        out.append('Vchip_%s %s %s 0' % (re.sub(r'\W', '_', net), net, node))
    rep = {'pins_moved': moved, 'nets_tied': len(first), 'not_moved': kept}
    return '\n'.join(out) + '\n', rep

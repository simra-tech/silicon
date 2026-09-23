#!/usr/bin/env python3
"""One explicitly nonphysical TI FET damping sensitivity, never acceptance."""
import argparse
import hashlib
import json
from pathlib import Path

MODEL_SHA = 'c5572438f1a79c8e9f48cfcf5a8d152daafdad8e8ec26ac30f807f0211edf2df'
DECK_SHA = '961a294a2e90795066860acaa3aaabf166d337f6caf30dbc38d6def590303296'
EDITS = {
    'RDP10': ('RDP   4  7\t 0.19e-3', 'RDP   4  7\t 1.9e-3'),
    'LDD10': ('LDD   1  4\t 0.05E-9', 'LDD   1  4\t 0.5E-9'),
}
OLD_INCLUDE = '.incpslt /work/build/g1_gate/vendor/CSD16340Q3.lib'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--original-model', type=Path, required=True)
    p.add_argument('--baseline-deck', type=Path, required=True)
    p.add_argument('--element', choices=sorted(EDITS), required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists()
    model = a.original_model.read_bytes()
    deck = a.baseline_deck.read_bytes()
    assert sha(model) == MODEL_SHA and sha(deck) == DECK_SHA
    model_text, deck_text = model.decode(), deck.decode()
    OLD, NEW = EDITS[a.element]
    assert model_text.count(OLD) == 1 and deck_text.count(OLD_INCLUDE) == 1
    altered_model = model_text.replace(OLD, NEW)
    altered_deck = deck_text.replace(OLD_INCLUDE,
        '.incpslt ' + str(a.output / 'vendor_variant.lib'))
    assert altered_model.replace(NEW, OLD) == model_text
    assert altered_deck.replace('.incpslt ' + str(a.output / 'vendor_variant.lib'),
                                OLD_INCLUDE) == deck_text
    a.output.mkdir(parents=True)
    (a.output / 'vendor_variant.lib').write_text(altered_model)
    (a.output / 'fixture.cir').write_text(altered_deck)
    (a.output / '.spiceinit').write_bytes((a.baseline_deck.parent / '.spiceinit').read_bytes())
    result = dict(status='prepared diagnostic only; source intentionally changed',
                  original_model_sha256=MODEL_SHA, variant_model_sha256=sha(altered_model.encode()),
                  baseline_deck_sha256=DECK_SHA, variant_deck_sha256=sha(altered_deck.encode()),
                  single_model_edit=dict(element=a.element, old=OLD, new=NEW,
                                         inverse_exact=True),
                  include_path_only_edit=True, solver_options_unchanged=True,
                  stimulus_unchanged=True, stop_s=16e-6, timeout_s=120,
                  physical_parameter_claim='none; 10x element is numerical sensitivity',
                  electrical_acceptance='not run')
    (a.output / 'contract.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()

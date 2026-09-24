#!/usr/bin/env python3
"""Pure saved-artifact corruption controls for the new-CPEX PVT auditor."""
import json
import shutil
import tempfile
from pathlib import Path

import audit_trim_newpex_pvt as audit


def main():
    source = audit.HERE/'runs/osc_r095_remaining48_20260922_r1'
    old = json.loads((source/'manifest.json').read_text())
    row = next(item for item in old['cases'] if item['name'] == 'ff_bcs_bcs_1.32_-40_c15')
    row = dict(row, tuple_index=3, waveform_sha256=audit.sha(source/(row['name']+'.dat')))
    template = (audit.HERE.parent/'postlayout/tb_osc_pex.cir').read_text()
    with tempfile.TemporaryDirectory() as directory:
        folder = Path(directory)
        for suffix in ('.cir','.dat','.log'):
            shutil.copy(source/(row['name']+suffix), folder/(row['name']+suffix))
        passed = audit.audit_case(folder,row,3,15,template)
        assert passed['status'] == 'passed', passed['checks']
        wave = folder/(row['name']+'.dat')
        wave.write_bytes(wave.read_bytes().replace(b'0.000000',b'NaN',1))
        corrupt_wave = audit.audit_case(folder,row,3,15,template)
        assert corrupt_wave['status'] == 'failed' and not corrupt_wave['checks']['wave_hash']
        shutil.copy(source/(row['name']+'.dat'),wave)
        log = folder/(row['name']+'.log')
        log.write_text(log.read_text()+'\nError: injected corruption\n')
        corrupt_log = audit.audit_case(folder,row,3,15,template)
        assert corrupt_log['status'] == 'failed' and not corrupt_log['checks']['log_clean']
        shutil.copy(source/(row['name']+'.log'),log)
        deck = folder/(row['name']+'.cir')
        deck.write_text(deck.read_text().replace('tran 0.2n 6.0u','tran 0.2n 5.9u'))
        corrupt_deck = audit.audit_case(folder,row,3,15,template)
        assert corrupt_deck['status'] == 'failed' and not corrupt_deck['checks']['source_deck_exact']
    print('PASS 4 pure saved-artifact controls')


if __name__ == '__main__':
    main()

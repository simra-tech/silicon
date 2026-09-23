"""Fail-closed successor bindings for the RZ100/current physical candidate.

The prior current/projection bindings are intentionally not mutated.
"""
import hashlib
import os
from pathlib import Path

ORIGINAL_SOURCE=('trip-hard-full-reference-20260923-r1/physical_taps_reader.cdl',
 '94e50a2a7f0646282f4499831bcfe03a2cf8871fbc33a7549b6e8f94fded207b')
PUREFILL=('current-purefill-flat-20260923-r1/pure_fill_flattened.gds',
 '6b9c5878a81a0ac4d3f68d3d8dbb5fa1927442675606aa6bd46a14d6552def51')
PUREFILL_PROOF=('current-purefill-flat-20260923-r1/analysis.json',
 '7131ac72e1c06e473e3da26ef3edf08c75d8c512eae1edb40b53008392cf0e2f')
KEEPOUT=('current-purefill-rz-keepout-20260923-r2/rz_fill_keepout.gds',
 '5d121548bb9406f8229fdca7e7e26c1c3e6581ad1b0745f8a2cfce4615af8684')
KEEPOUT_PROOF=('current-purefill-rz-keepout-proof-20260923-r1.json',
 '396c2f5f9aed2dbba607f63dff7feb9b59979aa2a4ca235c9f4b340901a81a71')
PIN_PATHS=('current-purefill-rz-pin-paths-20260923-r3.json',
 '2956b2812aa9bdc6069d0a8f6100ab41ea22b751712f5b1ed2e872a5b48c04c8')
PORT_OVERLAP=('current-purefill-rz-keepout-port-overlap-20260923-r1.json',
 '34df779541b88ae8afa464e469a1b600977c8f351a84aa93fd9d89e1973851d6')
PORT_REACH=('current-purefill-rz-keepout-port-reach-20260923-r1.json',
 '57f481f98230a6261536d7c9533f8755b4d85d3c166278b604f4cb70c6b47fa0')
CANDIDATE=('current-purefill-rz-port-text-20260923-r3/port_text_candidate.gds',
 '3e3634389aff5126d0f55f6814466ad179f6d1280e9152c62a07ab5ea3d105bf')
TRANSFORMATION=('current-purefill-rz-port-text-20260923-r3/transformation.json',
 'dffbcc62bf72ceb90c6a32221ef915c98546497668aa089c6cd5d10b166571f8')
IDENTITY_PROOF=('current-purefill-rz-port-text-20260923-r3/identity_proof_repro_script.json',
 '75f2f46c552c79804568729ddef675f08636211ec737b55b3935cde2903e91af')
KEEPOUT_RECORD_PROOF=('current-purefill-rz-keepout-repro-20260923-r2/record_identity.json',
 '7ab55cde047a2193f1593983537a4f0d011260babfbc798b6911e0ce00874d9a')
TEXT_RECORD_PROOF=('current-purefill-rz-port-text-repro-20260923-r1/record_identity.json',
 '4f30a3f3aed7ab941802f8a48294a5a01d0e52285176cbdba603443b62ed7d32')
DUMMY_PROOF=('current-purefill-rz-keepout-dummy-proof-20260923-r2/summary.json',
 'd9be7112004e2bed148da9ff63f74c4f0375ed42c0109bca5e1f87c0af9224aa')
FLAT_REFERENCE=('current-purefill-rz-keepout-flat-reference-20260923-r5/physical_AP_three_dummy_flat_reference.cdl',
 '784358b6e8955b14a7ef9445d5fd1faa41f0ad988c3d30bdd8bd37fcd4e66433')
FLAT_REFERENCE_PROOF=('current-purefill-rz-keepout-flat-reference-20260923-r5/summary.json',
 '5d87c17cd6b3f69205be5a1feebd4abd3fa6744a7587f95e43ebfd533bf46008')
STRICT_ANALYSIS=('current-purefill-rz-port-text-deep-stock-20260923-r1/strict_analysis.json',
 '21087fccfe5567a32057a81640a8cc1f8020f5baad23509c950fe90c3cc9be64')
STOCK_LVS_RULE_BASELINE=('current-purefill-native-lvs-20260923-r1/summary.json',
 '26d9175fc2d74b4d13c18156b1412607905022a4c65288ff25b3cc646982dcc7')
STRICT_DB=('current-purefill-rz-port-text-deep-stock-20260923-r1/port_text_candidate.lvsdb',
 '85da9080314fba5e7b8bebee040f4802cb8843d0823d84bf3be2fe04e3c4a4ab')
STRICT_PARSER=('current-purefill-native-lvs-20260923-r1/parser.py',
 'e53c46f698af2825e8a3a127bfe8b04d5ed5e4783ba45ec49b5ef63f0f04c361')
EXPECTED_PINS=('current-purefill-native-lvs-20260923-r1/expected_source_pins.json',
 '46fa499631e3a74096b27c94f997ab30c83db6cfcc7e7971ed3fb5223c446c77')
BOND_VALIDATION=('current-rz-bondmap-validation-20260923-r1/summary.json',
 '8b7b1e37a25e1f0e2d691a52030ae854a4da2372ba2f3cc3526dfcafcf58722b')
PHYSICAL={
 'density':('rz-port-text-stock-density-20260923-r1/summary.json','010d79cc34e6f43dea20a5696557a5b6d2bbe71c39da4cd9af899d6899ee2e50'),
 'main':('rz-port-text-stock-main-20260923-r2/summary.json','2ccab0278d681639066369015ab8c20e8124606d6cdada87570419cbce509d1c'),
 'maximal':('rz-port-text-stock-maximal-20260923-r2/summary.json','488d56dc340a5fc558339001d49d7975c0c88f9c536d018b4850ed72c4618295'),
 'antenna':('rz-port-text-stock-antenna-20260923-r1/summary.json','0c26c6db309a589b146f794aba905baed6808498855bed82b9e72b157474ee1e')}

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def root():
    p=Path(os.environ['G1_RESULTS_ROOT'])
    assert p.is_absolute() and p.is_dir() and p!=Path('/')
    return p
def bound(spec):
    relative,digest=spec;assert len(digest)==64 and not Path(relative).is_absolute()
    p=root()/relative;assert sha(p)==digest,(relative,'hash mismatch')
    return p

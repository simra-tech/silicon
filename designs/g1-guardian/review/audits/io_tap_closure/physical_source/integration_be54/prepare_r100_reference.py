#!/usr/bin/env python3
"""Source-only successor: exactly one main-OTA RZ length, 62 to 100 um."""
import hashlib
from pathlib import Path

base=Path(__file__).resolve().with_name('prepare_reference.py')
assert hashlib.sha256(base.read_bytes()).hexdigest()=='dab3ee8674667fbf49a97e055c0ed05073840e0f9cf531f3c4287a800503d79b'
code=base.read_text()
pairs=[
 ('analog-pair-integration-20260923-r1/analog_pair_native.gds','sense-r100-integration-20260923-r2/sense_replaced_native.gds'),
 ('be54644ebfffdc85bf4ed136966a31e60f374290b9ba7bd179753aa0b038d307','f43fd1c11d23fb9df59c8ab3bc9a01b7be929cdbf2d4b6d1775ceefd9a577c89'),
 ('80575bbd6a51044a287bb091c6888a02acdb4fb096d95dc201278dcc7e74fab3','90b472d62757f55b587ac9b42a6f671a058b73175185eb2dac8a9cce24e1ecf8'),
 ('passed isolated analog-pair hierarchy replacement','passed isolated SENSE-only native hierarchy replacement'),
 ('sense-comp45-native-reference-20260923-r3','sense-comp45-rz100-native-reference-20260923-r1'),
 ('8a9c92bd68f75d94fb3a08b95d7082d2a24e2dfd0827e9ba06e1ee84637cef5c','696b43fd94787bdff34a4b8dfac2b1e67a765740053880e752b58a9ba5664fc5'),
 ('io-physical-ap-source-20260923-r2','analog-pair-reference-20260923-r1'),
 ('796a724df08e1da81bbb43e6b54399e6ac338ff33db6a56535f8a89f91f24abf','ac740690d87f2c1b27ecfa803aba8b11541da617e39e2e7f131aa90fa930fb2e'),
 ('d39ce8512f167545ab2818582bd1e51e88f6402ff810dcf3368cd7d277ddb4d4','35b4b45b11427e327bc8a2cd145c27c70c102d00dd388a0199a0d19a96695f51'),
 ('len(differences)==2','len(differences)==1'),
 ('passed exact two-passive current-fullchip source update; native LVS not run','passed exact R62 to R100 current-fullchip source update; native LVS not run'),
]
for old,new in pairs:
    assert code.count(old)==1,(old,code.count(old))
    code=code.replace(old,new)
# Simultaneously move the old/new R length tokens, retaining byte proof and
# independently frozen literal standalone SENSE-body equality. CCC is a no-op
# anchor here: the flattened diff gate below permits only the single resistor.
code=code.replace('62u','100u').replace('6.2u','62u').replace('69u','45u')
old="assert (path.endswith('/XOTA/RRZ') and delta=={'l':('62u','100u')}) or (path.endswith('/XOTA/CCC') and delta=={'w':('45u','45u')}),(path,delta)"
assert code.count(old)==1
code=code.replace(old,"assert path.endswith('/XOTA/RRZ') and delta=={'l':('62u','100u')},(path,delta)")
exec(compile(code,str(base),'exec'),globals())

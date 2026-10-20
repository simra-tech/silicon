#!/usr/bin/env python3
"""Write layout/r1_padring_ref.lef: abstract of the R1 ring for chip assembly (die, 24 bondpad pins on TopMetal2,
core power ring and core window as obstructions). Generated from the pin map and the coordinates in
../padframe/README.md; the bondpad TopMetal2 square is 70 x 70 um centred on the pad centre."""
import sys
PINS = [(1,'VDD'),(2,'VSS'),(3,'IOVDD'),(4,'IOVSS'),(5,'VSS'),(6,'IOVSS'),(7,'VDDA'),(8,'ISA_P'),(9,'ISA_N'),(10,'ISB_P'),(11,'ISB_N'),
 (12,'FAULT_N'),(13,'GATE_A'),(14,'GATE_B'),(15,'GATE_C'),(16,'CS_N'),(17,'MA_SCLK'),(18,'SLO_SDO'),(19,'SDI'),(20,'EN_STO_IN'),
 (21,'SIN_P'),(22,'SIN_N'),(23,'COS_P'),(24,'COS_N')]
USE = {'VDD':'POWER','VDDA':'POWER','IOVDD':'POWER','VSS':'GROUND','IOVSS':'GROUND'}
def centre(n):
    i = (n-1) % 6
    if n <= 6: return (395+112*i, 101)
    if n <= 12: return (1313, 395+112*i)
    if n <= 18: return (395+112*i, 1313)
    return (101, 395+112*i)
TM1R = [(324.82,321,339.82,1093),(344.82,321,361.8,1093),(1054.42,321,1069.42,1093),(1074.42,321,1089.42,1093),
        (1054.42,347.16,1069.42,1066.3),(344.82,347.16,359.82,1066.3),(1074.42,327.16,1089.42,1086.3),(324.82,327.16,339.82,1086.3)]
TM2R = [(344.82,1051.3,1069.42,1066.3),(344.82,347.16,1069.42,362.16),(328,1071.3,1086,1086.3),(328,327.16,1086,342.16)]
o = ['VERSION 5.8 ;', 'BUSBITCHARS "[]" ;', 'DIVIDERCHAR "/" ;', '',
     '# R1 pad ring reference abstract (empty core). Units um. Pins: bondpad TopMetal2 squares (70 x 70 um).',
     '# Core window and ring: see README. Obstructions: core power ring (TopMetal1 / TopMetal2).', '',
     'MACRO r1_padring', '  CLASS BLOCK ;', '  ORIGIN 0 0 ;', '  FOREIGN r1_padring 0 0 ;', '  SIZE 1414 BY 1414 ;', '  SYMMETRY X Y ;']
nets = []
for _, n in PINS:
    if n not in nets: nets.append(n)
for net in nets:
    o += ['  PIN %s' % net, '    DIRECTION INOUT ;', '    USE %s ;' % USE.get(net, 'SIGNAL'), '    PORT', '      LAYER TopMetal2 ;']
    for n, m in PINS:
        if m == net:
            x, y = centre(n); o.append('        RECT %.3f %.3f %.3f %.3f ;' % (x-35, y-35, x+35, y+35))
    o += ['    END', '  END %s' % net]
o += ['  OBS', '    LAYER TopMetal1 ;'] + ['      RECT %.3f %.3f %.3f %.3f ;' % t for t in TM1R] + ['    LAYER TopMetal2 ;'] + ['      RECT %.3f %.3f %.3f %.3f ;' % t for t in TM2R] + ['  END', 'END r1_padring', '', 'END LIBRARY', '']
open(sys.argv[1], 'w').write('\n'.join(o))

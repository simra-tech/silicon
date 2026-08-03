# C01 CORRECTION RECORD

Date: 2026-08-03. PE-reviewed corrections to the C01 probe deliverables.
No simulation, no design edit, no cleanup, and no prior-file mutation was
performed for this record; only this file was written.

## Corrections (CONFIRMED by PE review)

1. C01-CROSSING-TABLE.tsv contains 50 data rows plus one header row, not
   51 data rows as stated in the run report.
2. The project root contains the preserved, unmanifested toolcheck/ subtree
   (fixture/probe decks, logs, raws). The root is therefore not an exact
   8-file closure; the artifact manifest covers only the 8 listed files.
3. The saved MOS vectors i(@n.<path>.nsg13_lv_nmos[ids]) are channel drain
   currents, not gate/displacement currents. Their ratio to the follower
   currents therefore cannot exclude dynamic capacitive loading of the
   divider/CMOS interface.

## Classification status

PROVISIONAL (PE): the 0.395 divider attenuation and the GP/GN levels are
measured facts, but headroom and the drive-versus-loading cause remain
AMBIGUOUS. The earlier C01-CLASSIFICATION.md "DRIVE/HEADROOM" label is
superseded by this determination; no signoff/pass/tape-out claim is made
anywhere.

## Intact original hashes (unchanged by C01 or by this record)

- sealed V8 transient deck : 1d668a3be99eb365c23cad1c09c1f4e58db96626d03132c324fa6970c2de11e8
- sealed V8 interface      : 68b1bc654f4449e63958f7dd0e82154aa54f8d3fd39725ec1dc74834876053b2
- sealed V8 baseline raw   : dbab1bd80ddaed8c3bee8f0c5ca816ac192fb687a7c31e841c1de46a7f68906c
- ngspice binary           : 6aacaca88f656e5e19074ac070fb410bf6cc437df1de88ec28d50a24c6239a1b
- C01 deck (additive)      : 09cb1b8ce26b0ef60ee89a4258344635b2c0bfbc4d96fd72e3ff1f76e081c51f
- C01 raw (89 vars)        : 5ebd09ff96dc6aabe3b20fda571f6bb0baa2db38573c712d7344a0575e9ce176

## Signoff

NOT CLAIMED. The dynamic-deficit cause remains open; the private/public
package derivations and any portable derivative are built by the Principal
Engineer, not this session.

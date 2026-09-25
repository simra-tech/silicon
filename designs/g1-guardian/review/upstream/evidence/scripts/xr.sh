for arm in pinneddeck_devgds_pinnedcdl devdeck_devgds_devcdl; do for c in sg13g2_IOPadAnalog sg13g2_IOPadIn sg13g2_IOPadVdd sg13g2_Filler200; do
 db=$(ls runs/$arm/$c/*.lvsdb | head -1); echo "=== $arm $c"; klayout -b -r xref_summary.py -rd db=$db | head -30; done; done

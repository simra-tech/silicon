W=${W:?set W to a scratch directory holding the inputs}
for c in sg13g2_IOPadAnalog sg13g2_IOPadIn sg13g2_IOPadVdd sg13g2_IOPadOut30mA sg13g2_Filler200; do
python3 $W/devpdk/ihp-sg13g2/libs.tech/klayout/tech/lvs/run_lvs.py --layout $W/io_dev_4fd47c5e.gds --netlist $W/io_dev_globalsub.cdl --topcell $c --run_mode flat --top_lvl_pins --run_dir $W/runs/devdeck_devgds_globalsub/$c > $W/runs/devdeck_devgds_globalsub_$c.log 2>&1
db=$(ls $W/runs/devdeck_devgds_globalsub/$c/*.lvsdb|head -1); echo "=== $c"; klayout -b -r $W/xref_summary.py -rd db=$db | head -25
done

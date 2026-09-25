W=${W:?set W to a scratch directory holding the inputs}
python3 $W/devpdk/ihp-sg13g2/libs.tech/klayout/tech/lvs/run_lvs.py --layout /work/designs/g1-guardian/blocks/g1_padring/layout/g1_chip_top_1414.gds --netlist /work/designs/g1-guardian/blocks/g1_padring/netlist/g1_chip_top_1414.cdl --topcell g1_chip_top --run_mode deep --top_lvl_pins --spice_comments --run_dir $W/runs/chip_devdeck_canonical > $W/runs/chip_devdeck_canonical.log 2>&1
db=$(ls $W/runs/chip_devdeck_canonical/*.lvsdb | head -1); klayout -b -r $W/xref_summary.py -rd db=$db > $W/runs/chip_devdeck_canonical_xref.txt 2>&1

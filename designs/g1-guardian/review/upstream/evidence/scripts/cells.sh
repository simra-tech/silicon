#!/bin/sh
# arm: pinned deck, dev GDS, pinned CDL ; arm2: dev deck, dev GDS, dev CDL
P=/foss/pdks/ihp-sg13g2
W=${W:?set W to a scratch directory holding the inputs}
for c in sg13g2_IOPadAnalog sg13g2_IOPadIn sg13g2_IOPadVdd sg13g2_Filler200; do

  python3 $W/devpdk/ihp-sg13g2/libs.tech/klayout/tech/lvs/run_lvs.py --layout $W/io_dev_4fd47c5e.gds --netlist $W/devpdk/ihp-sg13g2/libs.ref/sg13g2_io/cdl/sg13g2_io.cdl --topcell $c --run_mode flat --top_lvl_pins --run_dir $W/runs/devdeck_devgds_devcdl/$c > $W/runs/devdeck_devgds_devcdl_$c.log 2>&1
done

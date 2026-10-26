T=/foss/pdks/ihp-sg13g2/libs.tech/klayout/tech/drc/rule_decks
sed -n 2960,3010p $T/sg13g2_maximal.drc
grep -n "output(\"MIM\.\|output(\"TV1\|output(\"TM1\.\|output(\"Slt.g\|output(\"Slt.h\|output(\"M5\.\|output(\"V4" $T/sg13g2_maximal.drc
grep -rn "output(\"MIM\|output(\"Slt\|output(\"TM1" $T/beol/*.drc | head -30
ls $T/beol $T/feol

T=/foss/pdks/ihp-sg13g2/libs.tech/klayout/tech/drc
ls $T $T/rule_decks 2>/dev/null | head -40
grep -rn "MIM\.\|Mim\.\|TV1\.\|TM1\.[a-d]\|Slt\.\(a\|b\|c\)\.\(M5\|TM1\)" $T/rule_decks/*.drc 2>/dev/null | grep -i "rule\|check\|output" | head -60

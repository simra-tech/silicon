#!/usr/bin/env bash
# One strobe-train run: run_kick_train.sh <netlist> <tag> <mos corner> <VDD> <TEMP> <soft|hard> <outdir> [underdrive LSB, default 1] [tstop, default 4.25u] [hard code, default 254] [soft code, default 153]
# (from designs/g1-guardian/blocks/g1_trip/sim; analyse with postlayout/kick_train.py)
set -eu
NET=$1; TAG=$2; MOS=$3; VDD=$4; TEMP=$5; COND=$6; OUT=$7; UD=${8:-1}; TSTOP=${9:-4.25u}; HC=${10:-254}; SC=${11:-153}
name="kick_${TAG}_${MOS}_${VDD}V_${TEMP}C_${COND}"
[ "$HC" = 254 ] || name="${name%_*}_h${HC}_${COND}"
[ "$SC" = 153 ] || name="${name%_*}_s${SC}_${COND}"
[ "$UD" = 1 ] || name="${name%_*}_ud${UD}_${COND}"
BITS=""
for b in 0 1 2 3 4 5 6 7; do
  BITS="$BITS -e s/@@S$b@@/$( [ $(( (SC >> b) & 1 )) = 1 ] && echo {VDD} || echo 0 )/ -e s/@@H$b@@/$( [ $(( (HC >> b) & 1 )) = 1 ] && echo {VDD} || echo 0 )/"
done
mkdir -p "$OUT"
sed -e "s#@@NET@@#$NET#" -e "s/@@MOS@@/$MOS/g" -e "s/@@VDD@@/$VDD/" -e "s/@@TEMP@@/$TEMP/" -e "s/@@COND@@/$COND/g" -e "s/@@UD@@/$UD/g" -e "s/@@TSTOP@@/$TSTOP/" -e "s/@@HCODE@@/$HC/g" -e "s/@@SCODE@@/$SC/g" $BITS \
    -e "s#@@OUT@@#$OUT/$name.dat#" postlayout/tb_trip_kick_train.cir > "$OUT/$name.cir"
ngspice -b "$OUT/$name.cir" > "$OUT/$name.log" 2>&1
grep "^DC" "$OUT/$name.log"

. "$(dirname "$0")/common.sh"
for v in 3.3 3.0 3.6; do
  ofs postb7-ofs 103 tt mos_tt 27 1.2 "" $v
  ofs postb7-ofs 103 ss125 mos_ss 125 1.08 _vdd108 $v
  ofs postb7-ofs 103 ffm40 mos_ff -40 1.32 _vdd132 $v
done
echo chain103a done

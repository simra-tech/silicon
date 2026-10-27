. "$(dirname "$0")/common.sh"
gl b6-ms-ref-tt-buf-s4 103 ref_tt_buf 10800 "R2-4 buffer run tt, gate-level SAR, first 4 ref10 slots, layout B6 netlist"
gl b6-ms-fc-ffm40 103 fc_ffm40 7200 "first conversion ff / -40 C / 1.32 V, 0 V, gate-level SAR, layout B6 (first conversion, output window at ff)"
beh postb6-win1024-tt-rc 103 --deck points --ref lay-ideal --vref 1.045 --points sim/post/points/winb4_1024.json --question "post-layout RC (layout B6): static window at code 1024, tt, ideal VREF 1.045 V, B4 window centres" --disposition "post-layout value (static window tt, layout B6)"
echo chain103 done

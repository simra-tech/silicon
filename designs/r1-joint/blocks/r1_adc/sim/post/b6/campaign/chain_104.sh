. "$(dirname "$0")/common.sh"
gl b6-ms-ref-tt-base-s4 104 ref_tt_base 10800 "R2-4 base run tt (slice reference ports ideal), gate-level SAR, first 4 ref10 slots, layout B6"
beh postb6-win2048-tt-rc 104 --deck points --ref lay-ideal --vref 1.045 --points sim/post/points/winb4_2048.json --question "post-layout RC (layout B6): static window at code 2048, tt, ideal VREF 1.045 V, B4 window centres" --disposition "post-layout value (static window tt, layout B6)"
beh postb6-win3072-tt-rc 104 --deck points --ref lay-ideal --vref 1.045 --points sim/post/points/winb4_3072.json --question "post-layout RC (layout B6): static window at code 3072, tt, ideal VREF 1.045 V, B4 window centres" --disposition "post-layout value (static window tt, layout B6)"
echo chain104 done

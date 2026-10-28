. "$(dirname "$0")/common.sh"
# B8 (dev1 extraction): gate-level SAR first conversion at ff / -40 C / 1.32 V: first conversion, bit-exact, output window.
# Limit: B7 measured 0.0083 us per wall minute (b7-ms-fc-ffm40), 1.86 us -> 13 450 s, + 25 % = 16 800 s.
python3 sim/post/b6/run_b6.py --id b8-ms-fc-ffm40 --cpu 103 --deck sim/post/b8/decks/fc_ffm40.cir --timeout 16800 \
  --question "first conversion, bit-exact and output window at ff / -40 C / 1.32 V, gate-level SAR, layout B8 extraction (pex-b8-dev1), both frames; limit from the B7 rate plus 25 %" || echo "FAILED b8-ms-fc-ffm40"
echo chain103a done

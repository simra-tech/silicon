. "$(dirname "$0")/common.sh"
# D25 decoupling calibration: ideal C at the slice reference ports of the B7 (= B6) extraction, tt buffer run
DISP="diagnostic only (decoupling sizing, ideal capacitors)"
d23 postb8-cal-c100-tt-buf 105 tt sim/post/b8/cal_mb6_c100_100.spice "D25 sizing: R2-4 D23 proxy, tt buffer run, B7 extraction + ideal 100 pF on vref and 100 pF on vrefl per slice at the slice ports"
echo chain105a done

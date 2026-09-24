# Hysteresis interface remedy review — not implemented

Keep HYS disabled for the supervised feasibility demo, with static threshold
and offset configuration while energized. This review proposes verification
contracts, not a selected or qualified RTL change. No production source changed
and no additional analog simulation ran for this review.

## Observed failure and actual RTL cause

The [loaded pilot](HYS_FEEDBACK_PILOT_20260922.md) passed 29 scoped mechanism
checks but failed the existing post-code-change settling interval of at least
1 µs. The 128→127 carry occurred 100 ns before the next soft evaluation; the
127→128 carry occurred **on the soft evaluation edge, with zero delay**. Three
startup decisions were unclassified. Large-margin correct decisions do not
qualify either carry for general operation.

In `g1_trip_timer.v`, `soft_armed` is combinationally `soft_cnt != 0` and directly
selects the subtraction feeding the physical DAC output. `soft_cnt` updates on
every positive oscillator edge. In `g1_digital_top.v`, the comparator divider
also toggles on those edges. Thus either phase can receive a code change; no
DAC holding register, settle counter or decision-valid token exists. The two
input synchronization flops filter asynchronous inputs but do not establish
that the analog threshold was settled when a decision was made.

The current `soft_mask` is unsuitable as a drop-in settling mask: it clears
the accumulator and decay prescaler. Reusing it would discard previously
accumulated fault time and can make repeated update events restart the timer.
`trip_soft` also reads the synchronized level separately from the accumulator
update; freezing only the counter would still allow an invalid level to trip
when the retained count is already at the limit.

Reviewed source SHA256 identities:

| Source in `g1_ctrl/rtl/` | SHA256 |
| --- | --- |
| `g1_trip_timer.v` | `094527d2ccbdfad792d4c2e4d1a602c50051ed1e1c8d1789e4946a44e37af850` |
| `g1_digital_top.v` | `42430b79ddf649d832993aca1cf3c8a548afc97383c59a793cf70b972c8256ac` |
| `g1_sync2.v` | `c14906d7d9256a771cd8fdc0ab14ba291131e151d24bf06b951b6bc693ad8ef2` |

## Options and timing consequences

| Option | What it establishes | Cost or unresolved issue |
| --- | --- | --- |
| HYS off, configuration under independent load inhibit | No autonomous DAC updates during the demo | Does not demonstrate hysteresis; startup and static-path qualification remain separate |
| Register the desired code and commit only on a chosen clock phase | Removes uncontrolled combinational code-update scheduling; allows explicit bit-skew constraints | At 5 MHz, one comparator period is only 200 ns and opposite phase only 100 ns: phase selection alone cannot satisfy 1 µs |
| Registered code plus settling/decision-valid state; freeze soft accumulation while invalid | Can prevent consumption of decisions made with an unsettled DAC, if validity tracks the actual evaluation through synchronization | Continuous-fault trip time lengthens by invalid intervals; intermittent-fault accounting and decay semantics change |
| Keep counting the last valid level during settling | Retains a continuous-high count in the special persistent-fault case | A fault that clears can be overcounted; a new fault after a valid low can be missed; not equivalent to current timing semantics |
| Defer a requested DAC update until the load is inhibited | Allows the existing 1 µs requirement to be observed without live code transients | Autonomous hysteresis is effectively unavailable during energized operation; software cannot pause the existing automatic output path |
| Shorter analog settling contract | Might permit a smaller validity gap if independently established | Not established by this pilot; needs near-threshold, skew, loading, PVT and mismatch evidence, including the same-edge return carry |

Do not stop or gate the shared `cmp_clk` as a soft-only remedy: its falling edge
also clocks the hard comparator, and the timer's `hard_sample = ~cmp_clk`
assumes the existing phase cadence. Slowing the oscillator instead also changes
all timer units and hard response. A separate soft comparator clock or a second
pre-settled threshold bank would be a larger analog/interface change, not a
minimal RTL remedy considered here.

## Bounded candidate for a later digital-only experiment

If active HYS remains a requirement, first review a separate candidate with
registered physical DAC codes and an explicit soft-valid state, without
changing the shared clock. Suggested state sequence:

`valid → commit code/invalidate → wait settled age → qualifying evaluation →
synchronizer/consumer latency → valid`

The contract must satisfy all of the following before implementation:

1. Invalidate at the commit event, including when it coincides with comparator
   evaluation. Evaluate age from the latest physical bit arrival, not merely
   the RTL assignment. Atomic RTL vectors do not prove simultaneous routed
   transitions. Base-code, HYS mode/step and shared-offset writes also require
   a defined update policy; retain static configuration for the first candidate.
2. Derive the settle-cycle count from a verified maximum oscillator frequency:
   `N / f_max >= 1 µs + maximum DAC-delivery skew/delay + timing margin`.
   Ten nominal 100 ns cycles are not a worst-case guarantee. Actual delay and
   clock bounds remain not run for this proposed implementation.
3. Permit a decision only from a soft rising edge after that age. Propagate an
   evaluation-valid token with the decision; do not simply unmask after a
   timer expires while the synchronizer still holds an older invalid decision.
   Current two-flop nonblocking updates and the timer's read of the previous
   synchronized value add consumer latency that must be checked edge by edge.
4. Freeze the accumulator and decay phase while invalid, and gate `trip_soft`
   on the same validity definition. This is a proposed semantic choice, not
   equivalent behavior. Preserve count rather than clear it; choose explicitly
   whether pending opposite updates are coalesced or deferred. Bound repeated
   changes so validity cannot be postponed forever.
5. Specify the changed continuous-fault bound. For one update, extra detection
   delay includes the invalid interval, the wait to a qualifying comparator
   edge, and its synchronization/consumer delay. Multiple updates add gaps;
   changing from wall-clock fault accumulation to valid-sample accumulation
   requires a specification change. Do not retain an unqualified "exactly the
   window" claim. Test SOFT_TIME=0 separately; it can trip before a settling
   mask would be triggered by the first nonzero count.
6. Preserve hard clock cadence, synchronized hard samples, HARD_N filtering,
   force-trip and external-latch adoption; never suppress a hard trip as an
   incidental consequence of soft settling. Software status should distinguish
   requested code from physical code and invalid time if they can differ.

## Hard-path independence is also analog

Static hard code does not isolate the hard comparator from a soft-DAC update.
Both DACs load the same buffered reference, and the loaded return carry moved
that node over a simulated 0.88100–1.07677 V range in the declared window.
The pilot's 12 guarded hard decisions passed, but hard trip filtering and FAST
were disabled. This does not prove hard-path immunity near its threshold or
fast-latch pulse immunity. A soft-only digital validity mask cannot suppress a
physical transient entering the asynchronous fast latch. Any eventual remedy
must preserve hard detection while qualifying this shared-node disturbance;
otherwise live HYS cannot be claimed independent of the hard protection path.

## Required verification, before adoption

| Check | Current status |
| --- | --- |
| Source/timing review and identification of zero-delay carry | passed, read-only source review plus retained simulated pilot |
| Existing 1 µs interface interval for both carries | failed, retained; this review does not repair it |
| New RTL implementation, synthesis/STA and equivalence outside the intended change | not run |
| Digital test: both comparator phases, same-edge commit, stale synchronized HIGH/LOW, valid-token alignment and no invalid trip | not run |
| Digital test: uninterrupted fault at SOFT_TIME 0/1/default/max, exact new latency bound, count/decay preservation and intermittent pulses | not run |
| Digital test: repeated requests/cancellation, all decay modes, clear/reset/inrush/retry, counter saturation and no validity starvation | not run |
| Digital test: HYS 1/2, zero/255 clipping, signed offset, all major carries and physical-code readback | not run |
| Hard independence: exact clock/sample sequence, HARD_N 0/1/default/max, simultaneous soft update/hard fault and force/external-trip priority | not run |
| Analog co-simulation: actual DAC bit skew, both carry directions, near-threshold faults/clears, reference recovery, all soft/hard decisions and fast-latch waveform | not run |
| Model/source/seed parity, PVT/mismatch ensemble and extracted-route verification of an eventual candidate | not run |
| New layout/DRC/LVS change in this review | not applicable; no physical implementation changed |

The next step is agreement on the altered timing semantics and bounded digital
test contract, not another analog run. Demo HYS remains disabled.

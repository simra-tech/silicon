# Output-pad result classification

The runner previously set its overall status to passed after numerical
completion, before checking the output clock. A failed output-function check
or later analysis exception could therefore coexist with a misleading overall
pass. The corrected runner records numerical completion separately and
requires the existing output-function check and completed analysis to pass.
Timeouts remain not run to completion. No circuit, model, stimulus, solver
option, or functional threshold was changed.

Verification on 2026-09-23, Python 3.6.8:

~~~sh
python3 -m unittest discover \
  -s designs/g1-guardian/blocks/g1_t2f/sim/qualification \
  -p test_output_pad_status.py -v
~~~

Eight synthetic metadata controls **passed**: complete success, functional
failure, missing functional result, analysis exception, nonzero solver exit,
numerical failure, timeout, and an empty record. Whitespace checking passed.
These are software tests, not analog simulations. New analog runs and hardware
checks are **not run** for this classification change; circuit-change
qualification is **not applicable**.

Existing saved manifests and waveforms were not rewritten or reclassified.
The prior native TEMP_OUT pad and pad-replay numerical failures remain failed;
the separate core-route control is not a pad qualification.

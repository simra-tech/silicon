"""Bind independently testable recovery implementation without altering prepared inputs."""
import json
from pathlib import Path
from run_586_nearendpoint_recovery import HERE,ROOT,sha

def main():
    packet=HERE/'t2f586-nearendpoint-recovery-contract-20260923-b.json'
    output=HERE/'t2f586-nearendpoint-recovery-implementation-20260923-a.json';assert not output.exists()
    import run_586_calibration_sample,run_586_population_control,run_586_source_control,run_bgr_substitution_draw_audit,run_nominal_clock_probe,analyze_bgr_substitution_outcomes,wave_archive
    files=[Path(m.__file__).resolve() for m in [run_586_calibration_sample,run_586_population_control,run_586_source_control,run_bgr_substitution_draw_audit,run_nominal_clock_probe,analyze_bgr_substitution_outcomes,wave_archive]]
    files += [Path(__file__).resolve(),HERE/'run_586_nearendpoint_recovery.py',HERE/'test_586_nearendpoint_recovery.py']
    result=dict(status='implementation prepared; no launch lease',preparation_packet=str(packet.relative_to(ROOT)),preparation_packet_sha256=sha(packet),implementation_bindings_sha256={str(p.relative_to(ROOT)):sha(p) for p in files},scope='One separate900s attempt for each of exactly fivepreparedcases, no retryloop/automaticpopulationcontinuation. RequiresROOTfuturelease and resourcegate.')
    output.write_text(json.dumps(result,indent=2)+'\n');print(output.relative_to(ROOT),sha(output))

if __name__=='__main__':main()

#!/usr/bin/env python3
"""Bind temperature implementation without changing prepared fixture packets."""
import json
from pathlib import Path
from prepare_586_klu_temperature_coverage import HERE,ROOT,sha


def main():
    packet=HERE/'t2f586-klu-temperature-coverage-20260923-a.json';out=HERE/'t2f586-klu-temperature-implementation-20260923-a.json';assert not out.exists()
    assert sha(packet)=='4beafcca416e8e0ff12ca8bffe3e9ae9bb7f2985dd7e7a921fc53419259fa042'
    paths=[Path(__file__).resolve(),HERE/'run_586_klu_temperature.py',HERE/'prepare_586_klu_temperature_coverage.py']
    import run_586_population_control,run_586_source_control,run_nominal_clock_probe,run_bgr_substitution_draw_audit,analyze_bgr_substitution_outcomes,wave_archive
    paths += [Path(m.__file__).resolve() for m in [run_586_population_control,run_586_source_control,run_nominal_clock_probe,run_bgr_substitution_draw_audit,analyze_bgr_substitution_outcomes,wave_archive]]
    result=dict(status='implementation bound; no fixture changed and no launch',preparation_packet=str(packet.relative_to(ROOT)),preparation_packet_sha256=sha(packet),
        implementation_bindings_sha256={str(p.relative_to(ROOT)):sha(p) for p in paths},
        authority='Only separately allocated bounded successful-temperature controls may launch; return launch requires its own resource and scope disposition. No population/solver adoption.')
    out.write_text(json.dumps(result,indent=2)+'\n');print(out.relative_to(ROOT),sha(out))


if __name__=='__main__':main()

"""Exact one-thread CPU ownership assertion, independent of electrical inputs."""
import os


def verify_cpu(cpu):
    assert cpu in [1,6], 'Only explicitly coordinated compensation CPU slots are supported'
    observed=os.sched_getaffinity(0)
    assert observed=={cpu}, 'Actual process affinity must equal the one requested CPU'
    return sorted(observed)

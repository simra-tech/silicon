"""Logical owner of an odd (drain) diffusion strip; geometry is not modified."""

def drain_owner(owners, strip):
    assert owners and 0 <= strip <= len(owners) and strip % 2 == 1
    return owners[min(strip, len(owners)-1)]

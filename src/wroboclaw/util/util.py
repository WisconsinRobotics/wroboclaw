from enum import Enum

class BoundaryBehaviour(Enum):
    """Describes some behaviour for clamping a value to an interval."""
    wrap = 0
    clamp = 1

def boundary_clamp(behaviour: BoundaryBehaviour, value: float, lower: float, upper: float) -> float:
    """Clamps a value to an interval using the given boundary behaviour.

    The behaviours are as follows:
    - wrap: Causes values that under- or overflow to wrap around to the other side of the interval.
      Naturally, this means that the interval is closed below and open above.
    - clamp: Causes values that under- or overflow to be rounded to the nearest bound of the interval.
      Naturally, this means that the inverval is closed both above and below.

    Parameters
    ----------
    behaviour : BoundaryBehaviour
        The behaviour to use while clamping.
    value : float
        The value to clamp.
    lower : float
        The lower bound of the clamping interval.
    upper : float
        The upper bound of the clamping interval.

    Returns
    -------
    float
        The clamped value.
    """    
    if behaviour is BoundaryBehaviour.wrap:
        return lower + (value - lower) % (upper - lower)
    elif behaviour is BoundaryBehaviour.clamp:
        return min(max(value, lower), upper)
    else:
        raise ValueError(behaviour)

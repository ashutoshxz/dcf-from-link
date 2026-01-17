
def to_crores(value: float) -> float:
    """Convert absolute INR to crores."""
    return value / 1e7 if value is not None else None

def from_crores(value_crore: float) -> float:
    return value_crore * 1e7 if value_crore is not None else None

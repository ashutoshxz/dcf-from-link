
import pytest
from dcf_valuations.model.dcf import _cost_of_equity

def test_cost_of_equity():
    ke = _cost_of_equity(beta=1.0, rf=0.07, erp=0.055, size_premium=0.0)
    assert 0.12 <= ke <= 0.14

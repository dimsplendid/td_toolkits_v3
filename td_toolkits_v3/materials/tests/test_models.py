import pytest

# Connects our tests with our database
pytestmark = pytest.mark.django_db

from ..models import (
    Vender,
    get_default_vender,
    LiquidCrystal,
)
from .factories import (
    VenderFactory,
    LiquidCrystalFactory
)


def test_vender__str__():
    vender = VenderFactory()
    assert vender.__str__() == vender.name
    assert str(vender) == vender.name

def test_liquid_crystal__str__():
    lc = LiquidCrystalFactory()
    assert lc.__str__() == lc.name
    assert str(lc) == lc.name

def test_get_default_vender():
    vender = get_default_vender()
    assert vender.__str__() == "INX"
    assert str(vender) == "INX"

def test_lc_default_vender():
    lc = LiquidCrystal.objects.create(name='LCT-15-1098')
    assert lc.vender.name == 'INX'
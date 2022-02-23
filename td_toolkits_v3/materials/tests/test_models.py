import pytest

from ..models import (
    Vender,
    get_default_vender,
    LiquidCrystal,
)

# Connects our tests with our database
pytestmark = pytest.mark.django_db

def test_vender__str__():
    vender = Vender.objects.create(name="INX")
    assert vender.__str__() == "INX"
    assert str(vender) == "INX"

def test_liquid_crystal__str__():
    lc = LiquidCrystal.objects.create(name='LCT-19-580')
    assert lc.__str__() == "LCT-19-580"
    assert str(lc) == "LCT-19-580"

def test_get_default_vender():
    vender = get_default_vender()
    assert vender.__str__() == "INX"
    assert str(vender) == "INX"

def test_default_vender():
    lc = LiquidCrystal.objects.create(name='LCT-15-1098')
    assert lc.vender.name == 'INX'
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

@pytest.fixture
def lc():
    return LiquidCrystalFactory()

@pytest.fixture
def lc_real():
    return LiquidCrystal.objects.create(
        name='LCT-15-1098',
        n_e=1.5794,
        n_o=1.4818,
        e_para=3.5,
        e_perp=6.9,
        rotational_viscosity=107,
        k_11=14.7,
        k_33=15.1,
    )


def test_vender__str__():
    vender = VenderFactory()
    assert vender.__str__() == vender.name
    assert str(vender) == vender.name

def test_liquid_crystal__str__(lc):
    assert lc.__str__() == lc.name
    assert str(lc) == lc.name

def test_get_default_vender():
    vender = get_default_vender()
    assert vender.__str__() == "INX"
    assert str(vender) == "INX"

def test_lc_default_vender():
    lc = LiquidCrystal.objects.create(name='LCT-15-1098')
    assert lc.vender.name == 'INX'

def test_lc_get_absolute_url(lc):
    url = lc.get_absolute_url()
    assert url == f'/materials/lcs/{lc.slug}/'

def test_lc_delta_n(lc, lc_real):
    
    assert lc.delta_n is None
    assert lc_real.delta_n == pytest.approx(0.0976)
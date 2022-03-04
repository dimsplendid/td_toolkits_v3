from .factories import (
    VenderFactory,
    LiquidCrystalFactory,
    PolyimideFactory,
    SealFactory,
)
from ..models import (
    Vender,
    get_default_vender,
    LiquidCrystal,
)
import pytest

# Connects our tests with our database
pytestmark = pytest.mark.django_db


@pytest.fixture
def lc():
    return LiquidCrystalFactory()

@pytest.fixture
def lc_real():
    return LiquidCrystal.objects.create(
        name='LCT-15-1098',
        designed_cell_gap=2.8,
        n_e=1.5794,
        n_o=1.4818,
        e_para=3.5,
        e_perp=6.9,
        rotational_viscosity=107,
        k_11=14.7,
        k_33=15.1,
    )

@pytest.fixture
def pi():
    return PolyimideFactory()

@pytest.fixture
def seal():
    return SealFactory()

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
    assert url == f'/materials/lc/{lc.slug}/'


def test_lc_delta_n(lc, lc_real):
    assert lc.delta_n is None
    assert lc_real.delta_n == pytest.approx(0.0976)


def test_lc_delta_e(lc, lc_real):
    assert lc.delta_e is None
    assert lc_real.delta_e == pytest.approx(-3.4)


def test_lc_retardation(lc, lc_real):
    assert lc.retardation is None
    assert lc_real.retardation == lc_real.delta_n \
        * lc_real.designed_cell_gap \
        * 1000

def test_lc_scatter_index(lc, lc_real):
    assert lc.scatter_index is None
    assert lc_real.scatter_index == pytest.approx(0.007208509601712038)

def test_lc_response_index(lc, lc_real):
    assert lc.response_index is None
    assert lc_real.response_index == pytest.approx(14.557823129251702)

def test_lc_vt_index(lc, lc_real):
    assert lc.vt_index is None
    assert lc_real.vt_index == pytest.approx(0.23129251700680276)

def test_pi__str__(pi):
    assert pi.__str__() == pi.name
    assert str(pi) == pi.name

def test_seal__str__(seal):
    assert seal.__str__() == seal.name
    assert str(seal) == seal.name
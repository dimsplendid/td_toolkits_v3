import pytest

from ..models import ProductModelType
from .factories import (
    product_model_type,
    project,
    experiment,
    condition,
    sub,
    chip,
)

pytestmark = pytest.mark.django_db

def test_product_model_type_name_default():
    product = ProductModelType.default()
    assert product.name == '5905'

def test_product_model_type__str__(product_model_type):
    assert product_model_type.__str__() == product_model_type.name
    assert str(product_model_type) == product_model_type.name

def test_project__str__(project):
    assert project.__str__() == project.name
    assert str(project) == project.name

def test_experiment__str__(experiment):
    assert experiment.__str__() == experiment.name
    assert str(experiment) == experiment.name

def test_condition__str__(condition):
    assert condition.__str__() == condition.name
    assert str(condition) == condition.name

def test_sub__str__(sub):
    assert sub.__str__() == sub.name
    assert str(sub) == sub.name

def test_chip__str__(chip):
    assert chip.__str__() == chip.name
    assert str(chip) == chip.name


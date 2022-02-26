import pytest

from ..models import ProductModelType

pytestmark = pytest.mark.django_db

def test_product_model_type_name_default():
    product = ProductModelType.default()
    assert product.name == '5905'
from django.template.defaultfilters import slugify


import factory
import factory.fuzzy
import pytest


from ..models import (
    ProductModelType,
    Sub,
    Chip
)

@pytest.fixture
def product_model_type():
    return ProductModelTypeFactory()

@pytest.fixture
def sub():
    return SubFactory()

@pytest.fixture
def chip():
    return ChipFactory()

class ProductModelTypeFactory(factory.django.DjangoModelFactory):
    name = factory.fuzzy.FuzzyText()
    slug = factory.LazyAttribute(
        lambda obj: slugify(obj.name)
    )

    class Meta:
        model = ProductModelType

class SubFactory(factory.django.DjangoModelFactory):
    name = factory.fuzzy.FuzzyText()
    slug = factory.LazyAttribute(
        lambda obj: slugify(obj.name)
    )
    product_type = factory.SubFactory(ProductModelTypeFactory)

    class Meta:
        model = Sub

class ChipFactory(factory.django.DjangoModelFactory):
    name = factory.fuzzy.FuzzyText()
    slug = factory.LazyAttribute(
        lambda obj: slugify(obj.name)
    )
    sub = factory.SubFactory(SubFactory)

    class Meta:
        model = Chip
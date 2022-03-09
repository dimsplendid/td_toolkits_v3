from pathlib import Path

from django.template.defaultfilters import slugify


import factory
import factory.fuzzy
import pytest

from td_toolkits_v3.materials.tests.factories import (
    LiquidCrystalFactory,
    SealFactory,
    PolyimideFactory,
)

from ..models import (
    ProductModelType,
    Factory,
    Project,
    Experiment,
    Condition,
    Sub,
    Chip,
)


@pytest.fixture
def product_model_type():
    return ProductModelTypeFactory()


@pytest.fixture
def factory_():
    return FactoryFactory()


@pytest.fixture
def project():
    return ProjectFactory()


@pytest.fixture
def experiment():
    return ExperimentFactory()


@pytest.fixture
def condition():
    return ConditionFactory()


@pytest.fixture
def sub():
    return SubFactory()


@pytest.fixture
def chip():
    return ChipFactory()


class ProductModelTypeFactory(factory.django.DjangoModelFactory):
    name = factory.fuzzy.FuzzyText()
    slug = factory.LazyAttribute(lambda obj: slugify(obj.name))

    class Meta:
        model = ProductModelType


class FactoryFactory(factory.django.DjangoModelFactory):
    name = factory.fuzzy.FuzzyText()
    slug = factory.LazyAttribute(lambda obj: slugify(obj.name))
    addr = factory.fuzzy.FuzzyText()
    desc = factory.Faker("paragraph", nb_sentences=3, variable_nb_sentences=True)

    class Meta:
        model = Factory


class ProjectFactory(factory.django.DjangoModelFactory):
    name = factory.fuzzy.FuzzyText()
    code = factory.fuzzy.FuzzyText()

    class Meta:
        model = Project


class ExperimentFactory(factory.django.DjangoModelFactory):
    name = factory.fuzzy.FuzzyText()
    slug = factory.LazyAttribute(lambda obj: slugify(obj.name))
    desc = factory.Faker("paragraph", nb_sentences=3, variable_nb_sentences=True)
    product_type = factory.SubFactory(ProductModelTypeFactory)
    project = factory.SubFactory(ProjectFactory)

    class Meta:
        model = Experiment


class ConditionFactory(factory.django.DjangoModelFactory):
    name = factory.fuzzy.FuzzyText()
    slug = factory.LazyAttribute(lambda obj: slugify(obj.name))
    desc = factory.Faker("paragraph", nb_sentences=3, variable_nb_sentences=True)
    experiment = factory.SubFactory(ExperimentFactory)

    class Meta:
        model = Condition


class SubFactory(factory.django.DjangoModelFactory):
    name = factory.fuzzy.FuzzyText()
    slug = factory.LazyAttribute(lambda obj: slugify(obj.name))
    condition = factory.SubFactory(ConditionFactory)

    class Meta:
        model = Sub


class ChipFactory(factory.django.DjangoModelFactory):
    name = factory.fuzzy.FuzzyText()
    slug = factory.LazyAttribute(lambda obj: slugify(obj.name))
    sub = factory.SubFactory(SubFactory)
    lc = factory.SubFactory(LiquidCrystalFactory)
    pi = factory.SubFactory(PolyimideFactory)
    seal = factory.SubFactory(SealFactory)

    class Meta:
        model = Chip


TEST_DIR = Path(__file__).resolve(strict=True).parent

PRODUCT_TEST_FILE_DIR = TEST_DIR / r"test_files/chip_model_test.xlsx"
MATERIAL_TEST_FILE_DIR = TEST_DIR / r"test_files/material_for_chip_test.xlsx"

from pathlib import Path

from django.template.defaultfilters import slugify


import factory
import factory.fuzzy
import pytest
from td_toolkits_v3.materials.tests.factories import MATERIAL_TEST_FILE_DIR

from td_toolkits_v3.products.tests.factories import (
    PRODUCT_TEST_FILE_DIR,
    ChipFactory
)

from ..models import (
    AxometricsLog,
    RDLCellGap,
)

TEST_DIR = Path(__file__).resolve(strict=True).parent

MATERIAL_TEST_FILE_DIR = TEST_DIR / r'test_files/properties/batch_upload_test.xlsx'
PRODUCT_TEST_FILE_DIR = TEST_DIR / r'test_files/condition/conditions_5905_test.xlsx'
AXO_TEST_FILES_DIR = TEST_DIR / r'test_files/axo/'
RDL_CELL_GAP_TEST_FILE_DIR = TEST_DIR / r'test_files/rdl_cellgap/cell_gap_RDL.xlsx'

@pytest.fixture
def axometrics_log():
    return AxometricsLogFactory()

@pytest.fixture
def rdl_cell_gap():
    return RDLCellGapFactory()

class AxometricsLogFactory(factory.django.DjangoModelFactory):
    chip = factory.SubFactory(ChipFactory)
    measure_point = factory.fuzzy.FuzzyInteger(6)
    x_coord = factory.fuzzy.FuzzyFloat(10)
    y_coord = factory.fuzzy.FuzzyFloat(10)
    cell_gap = factory.fuzzy.FuzzyFloat(2.5, 3.5)
    twist = factory.fuzzy.FuzzyFloat(10)
    top_pretilt = factory.fuzzy.FuzzyFloat(10)
    bottom_pretilt = factory.fuzzy.FuzzyFloat(10)
    rms = factory.fuzzy.FuzzyFloat(10)
    iteration = factory.fuzzy.FuzzyFloat(10)

    class Meta:
        model = AxometricsLog

class RDLCellGapFactory(factory.django.DjangoModelFactory):
    chip = factory.SubFactory(ChipFactory)
    cell_gap = factory.fuzzy.FuzzyFloat(2.5, 3.5)
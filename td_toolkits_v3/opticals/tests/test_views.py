import os
import pytest

from django.urls import reverse


pytestmark = pytest.mark.django_db

from td_toolkits_v3.products.models import Experiment

from .factories import (
    MATERIAL_TEST_FILE_DIR,
    PRODUCT_TEST_FILE_DIR,
    AXO_TEST_FILES_DIR,
)
from ..models import (
    AxometricsLog
)

def test_axo_batch_create_view(client):
    # create material data first
    with open(MATERIAL_TEST_FILE_DIR, 'rb') as fp:
        form_data = {'materials': fp}
        client.post(reverse('materials:upload'),form_data)

    # Product import
    with open(PRODUCT_TEST_FILE_DIR, 'rb') as fp:
        form_data = {'chips': fp}
        client.post(reverse('products:chip_upload'), form_data)

    axo_files = []
    _, _, files = next(os.walk(AXO_TEST_FILES_DIR))
    for file in files:
        fp = open(AXO_TEST_FILES_DIR / file, 'rb')
        axo_files.append(fp)

    form_data = {
        'exp_id': Experiment.objects.last().name,
        'axos': axo_files
    }
    client.post(reverse('opticals:axo_upload'), form_data)
    axo_1 = AxometricsLog.objects.get(
        chip__short_name='1-23',
        measure_point=5,
    )
    axo_2 = AxometricsLog.objects.get(
        chip__short_name='4-11',
        measure_point=1,
    )
    # test all allowed data are imported
    assert AxometricsLog.objects.all().count() == 288
    # test if the import data is correct
    assert axo_1.cell_gap == pytest.approx(2.939389)
    assert axo_2.cell_gap == pytest.approx(3.005118)
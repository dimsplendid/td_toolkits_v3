import os
import pytest

from django.urls import reverse
from pytest_django.asserts import assertContains

pytestmark = pytest.mark.django_db

from td_toolkits_v3.products.models import Experiment
from td_toolkits_v3.products.tests.factories import (
    experiment
)

from .factories import (
    MATERIAL_TEST_FILE_DIR,
    PRODUCT_TEST_FILE_DIR,
    AXO_TEST_FILES_DIR,
    RDL_CELL_GAP_TEST_FILE_DIR,
    TOC_OPT_TEST_FILES_DIR,
)
from ..models import (
    AxometricsLog,
    OpticalLog,
    RDLCellGap
)
from ..views import (
    AxoUploadView,
    RDLCellGapUploadView,
)

def test_axo_upload_view(client):
    # create material data first
    with open(MATERIAL_TEST_FILE_DIR, 'rb') as fp:
        form_data = {'materials': fp}
        client.post(reverse('materials:upload'),form_data)

    # Product import
    with open(PRODUCT_TEST_FILE_DIR, 'rb') as fp:
        form_data = {'chips': fp}
        client.post(reverse('products:chip_upload'), form_data)

    # axo files upload
    axo_files = []
    _, _, files = next(os.walk(AXO_TEST_FILES_DIR))
    for file in files:
        fp = open(AXO_TEST_FILES_DIR / file, 'rb')
        axo_files.append(fp)
    exp_id = Experiment.objects.last().name
    form_data = {
        'exp_id': (exp_id, exp_id),
        'factory': ('T2', 'T2'),
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
    assert AxometricsLog.objects.all().count() == 282
    # test if the import data is correct
    assert axo_1.cell_gap == pytest.approx(2.939389)
    assert axo_2.cell_gap == pytest.approx(3.005118)

def test_rdl_cell_gap_upload_view(client):
    # create material data first
    with open(MATERIAL_TEST_FILE_DIR, 'rb') as fp:
        form_data = {'materials': fp}
        client.post(reverse('materials:upload'),form_data)

    # Product import
    with open(PRODUCT_TEST_FILE_DIR, 'rb') as fp:
        form_data = {'chips': fp}
        client.post(reverse('products:chip_upload'), form_data)

    # Open RDL cell gap
    with open(RDL_CELL_GAP_TEST_FILE_DIR, 'rb') as fp:
        form_data = {
            'exp_id': Experiment.objects.last().name,
            'rdl_cell_gap': fp
        }
        client.post(reverse('opticals:rdl_cell_gap_upload'), form_data)

    rdl_1 = RDLCellGap.objects.get(
        chip__short_name='1-25'
    )
    rdl_2 = RDLCellGap.objects.get(
        chip__name='T19BU001NA03'
    )
    assert rdl_1.cell_gap == pytest.approx(2.914)
    assert rdl_2.cell_gap == pytest.approx(2.719)

def test_rdl_cell_gap_upload_view_content(rf, experiment):
    # Determine the url
    url = reverse('opticals:rdl_cell_gap_upload')
    # Generate a request using the pytest short cut: rf
    # rf: short cut to django.test.RequestFactory
    request = rf.get(url)
    # Pass in the request into the view to get an
    # HTTP response served up by Django
    response = RDLCellGapUploadView.as_view()(request)

    assertContains(response, experiment.name)
    assertContains(response, 'RDL Cell Gap Upload')

def test_toc_opt_upload_view(client):
    # create material data first
    with open(MATERIAL_TEST_FILE_DIR, 'rb') as fp:
        form_data = {'materials': fp}
        client.post(reverse('materials:upload'),form_data)

    # Product import
    with open(PRODUCT_TEST_FILE_DIR, 'rb') as fp:
        form_data = {'chips': fp}
        client.post(reverse('products:chip_upload'), form_data)

    # TOC OPT files upload
    opt_files = []
    _, _, files = next(os.walk(TOC_OPT_TEST_FILES_DIR))
    print('opt upload test files')
    print('-'*20)
    for file in files:
        print(file)
        fp = open(TOC_OPT_TEST_FILES_DIR / file, 'rb')
        opt_files.append(fp)
    exp_id = Experiment.objects.last().name
    form_data = {
        'exp_id': (exp_id, exp_id),
        'factory': ('TOC', 'TOC'),
        'opts': opt_files
    }

    client.post(reverse('opticals:toc_opt_log_upload'), form_data)

    assert OpticalLog.objects.all().count() == 14994
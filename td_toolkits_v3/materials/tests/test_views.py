from django.urls import reverse

import pytest

# Connects our tests with our database
pytestmark = pytest.mark.django_db

from .factories import (
    MATERIAL_TEST_FILE_DIR,
    MATERIAL_TEST_NULL_FILE_DIR,
)
from ..models import (
    LiquidCrystal,
    Polyimide,
    Seal,
)

def test_material_batch_create_view(client):
    """POST request to MaterialBatchCreateView
    for batch create materials data.
    """
    
    with open(MATERIAL_TEST_FILE_DIR, 'rb') as fp:
        form_data = {
            'materials': fp,
        }
        url = reverse('materials:upload')
        client.post(url, form_data)

    lc_name = LiquidCrystal.objects.last().name
    pi_name = Polyimide.objects.last().name
    seal_name = Seal.objects.last().name

    assert lc_name == 'LCT-15-1098'
    assert pi_name == 'RB005'
    assert seal_name == '723K1M'

def test_material_batch_create_null_view(client):
    """Test that upload file do not have data
    """
    with open(MATERIAL_TEST_NULL_FILE_DIR, 'rb') as fp:
        form_data = {
            'materials': fp,
        }
        url = reverse('materials:upload')
        client.post(url, form_data)

    assert LiquidCrystal.objects.all().count() == 0
    assert Polyimide.objects.all().count() == 0
    assert Seal.objects.all().count() == 0

def test_material_batch_create_unique(client):
    """Test duplicate doesn't affect data"""
    LiquidCrystal.objects.create(name='LCT-15-1098')
    Polyimide.objects.create(name='RB005')
    Seal.objects.create(name='723K1M')

    with open(MATERIAL_TEST_FILE_DIR, 'rb') as fp:
        form_data = {
            'materials': fp,
        }
        url = reverse('materials:upload')
        client.post(url, form_data)

    assert LiquidCrystal.objects.all().count() == 1
    assert LiquidCrystal.objects.last().n_e == None
    assert Polyimide.objects.all().count() == 1
    assert Polyimide.objects.last().vender.name == 'INX'
    assert Seal.objects.all().count() == 1
    assert Seal.objects.last().vender.name == 'INX'
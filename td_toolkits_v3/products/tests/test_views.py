from django.urls import reverse

import pytest

pytestmark = pytest.mark.django_db

from .factories import (
    PRODUCT_TEST_FILE_DIR,
    MATERIAL_TEST_FILE_DIR,
)

from ..models import (
    Chip
)

def test_chip_batch_create_view(client, user):
    # Authenticate the user
    client.force_login(user)
    # create material data first
    with open(MATERIAL_TEST_FILE_DIR, 'rb') as fp:
        form_data = {'materials': fp}
        client.post(reverse('materials:upload'),form_data)

    # Product import
    with open(PRODUCT_TEST_FILE_DIR, 'rb') as fp:
        form_data = {
            'chips': fp,
            'fab': ('rdl', 'rdl')
        }
        client.post(reverse('products:chip_upload'), form_data)

    # check all chip is add
    assert Chip.objects.all().count() == 49
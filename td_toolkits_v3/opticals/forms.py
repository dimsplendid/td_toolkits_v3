from django import forms

import pandas as pd

from td_toolkits_v3.products.models import (
    ProductModelType,
    Project,
    Experiment,
    Condition,
    Sub,
    Chip
)
from td_toolkits_v3.materials.models import (
    LiquidCrystal,
    Polyimide,
    Seal,
)
from .models import (
    AxometricsLog,
)


class AxoUploadForm(forms.Form):
    
    exp_id = forms.CharField(
        max_length=255,
        initial=None,
    )
    axos = forms.FileField(widget=forms.FileInput(
            attrs={
                'multiple': True,
                'webkitdirectory': True,
                'directory': True,
            }
    ))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        last_exp = Experiment.objects.last()
        if last_exp is not None:
            last_exp_id = last_exp.name
            self.fields['exp_id'].initial = last_exp_id

    def save(self, request):
        print(request.FILES.getlist('axos'))
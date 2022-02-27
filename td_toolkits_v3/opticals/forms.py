from django import forms

import pandas as pd

from td_toolkits_v3.products.models import Chip
from .models import (
    AxometricsLog,
)

class OpticalsUploadForm(forms.Form):
    chips = forms.FileField(widget=forms.FileInput(
        attrs={
            'accept': '.xlsx'
        }
    ))
    axos = forms.FileField(widget=forms.FileInput(
        attrs={
            'multiple': True,
            'webkitdirectory': True,
            'directory': True,
        }
    ))

    def save(self, request):
        print(self.cleaned_data['chips'])
        print(request.FILES.getlist('axos'))
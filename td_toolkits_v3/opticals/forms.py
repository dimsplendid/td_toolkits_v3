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
        chip_df = pd.read_excel(self.cleaned_data['chips'], sheet_name='Sheet1')
        print(chip_df)

        # print(request.FILES.getlist('axos'))
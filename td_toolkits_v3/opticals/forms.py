from django import forms

import pandas as pd

from .models import (
    AxometricsLog,
)

class OpticalsUploadForm(forms.Form):
    axo = forms.FileField()
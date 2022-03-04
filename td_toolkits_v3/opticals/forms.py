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




# axos = forms.FileField(widget=forms.FileInput(
    #     attrs={
    #         'multiple': True,
    #         'webkitdirectory': True,
    #         'directory': True,
    #     }
    # ))

    # print(request.FILES.getlist('axos'))
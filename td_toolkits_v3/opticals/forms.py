import io
import os
import csv
from re import M
import pandas as pd

from django import forms

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
from td_toolkits_v3.products.tests.factories import experiment
from .models import (
    AxometricsLog,
    RDLCellGap
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
        # Set the last experiment name for the upload axo data
        last_exp = Experiment.objects.last()
        if last_exp is not None:
            last_exp_id = last_exp.name
            self.fields['exp_id'].initial = last_exp_id

    def save(self, request):
        files = request.FILES.getlist('axos')
        experiment = Experiment.objects.get(
            name=str(self.cleaned_data['exp_id']))
        # print(files)

        # the axo location order map to opt measurement point
        points = [5, 3, 1, 6, 4, 2]

        for file in files:
            file_name = str(file).split('.')[0]
            short_names = [s.strip() for s in file_name.split('+')]

            reader = csv.reader(io.StringIO(file.read().decode('utf-8', errors='ignore')))
            data_range = range(28, 28 + len(points)*len(short_names))
            data = [row for idx, row in enumerate(reader) \
                if  idx in data_range]
            row_count = 0
            for short_name in short_names:
                print(short_name)
                # Check if there is chip data, otherwise skip.
                try:
                    chip = Chip.objects.get(
                        short_name=short_name,
                        sub__condition__experiment=experiment
                    )
                except:
                    continue
                print(chip)
                for point in points:
                    AxometricsLog.objects.create(
                        chip=chip,
                        measure_point=point,
                        x_coord=data[row_count][1],
                        y_coord=data[row_count][2],
                        cell_gap=data[row_count][3],
                        top_rubbing_direct=data[row_count][4],
                        twist=data[row_count][5],
                        top_pretilt=data[row_count][6],
                        bottom_pretilt=data[row_count][7],
                        rms=data[row_count][8],
                        iteration=data[row_count][9],
                    )
                    row_count += 1

class RDLCellGapUploadForm(forms.Form):
    exp_id = forms.CharField(
        max_length=255,
        initial=None,
    )
    rdl_cell_gap = forms.FileField(
        widget=forms.FileInput(attrs={
            'accept': '.xlsx'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set the last experiment name for the upload axo data
        last_exp = Experiment.objects.last()
        if last_exp is not None:
            last_exp_id = last_exp.name
            self.fields['exp_id'].initial = last_exp_id

    def save(self):
        rdl_cell_gap = pd.read_excel(
            self.cleaned_data['rdl_cell_gap']
        )
        experiment = Experiment.objects.get(
            name=str(self.cleaned_data['exp_id']))

        for row in rdl_cell_gap.to_dict(orient='records'):
            # Check if there is chip data, otherwise skip.
            try:
                chip = Chip.objects.get(
                    short_name=row['short id'],
                    sub__condition__experiment=experiment
                )
            except:
                continue
            
            RDLCellGap.objects.create(
                chip=chip,
                cell_gap=row['cell gap(um)']
            )




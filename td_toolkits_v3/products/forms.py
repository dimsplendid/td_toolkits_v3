from django import forms
from django.core.cache import cache

import pandas as pd

from td_toolkits_v3.materials.models import(
    LiquidCrystal,
    Polyimide,
    Seal
)
from td_toolkits_v3.products.models import Factory

from .models import (
    Project,
    ProductModelType,
    Experiment,
    Condition,
    Sub,
    Chip
)


class ChipsUploadForm(forms.Form):

    chips = forms.FileField(widget=forms.FileInput(
        attrs={'accept': '.xlsx'}))

    fab = forms.ChoiceField(
        choices=[('rdl', 'RDL')],
        initial='rdl'
    )
    
    def save(self):
        print(self.cleaned_data['chips'])
        chip_df = pd.read_excel(self.cleaned_data['chips'], sheet_name='upload')
        save_log = {
            'file_name': [self.cleaned_data['chips'].name],
            'warning': [],
        }
        df = {}
        for row in chip_df.to_dict(orient='records'):
            if not Chip.objects.filter(
                sub__condition__experiment__project__name=str(row['project']),
                sub__condition__experiment__name=str(row['exp id']),
                name=str(row['id'])
            ).exists():
                project = Project.objects.get_or_create(
                    name=str(row['project']))[0]
                product_type = ProductModelType.objects.get_or_create(
                    name=str(row['platform'])
                )[0]
                experiment = Experiment.objects.get_or_create(
                    name=str(row['exp id']),
                    project=project,
                    product_type=product_type,
                )[0]
                condition = Condition.objects.get_or_create(
                    name=str(row['condition']),
                    experiment=experiment
                )[0]
                try:
                    df[row['condition']][0] += 1
                except KeyError:
                    df[row['condition']] = [1]
                sub = Sub.objects.get_or_create(
                    name=f"{str(row['exp id'])}-{str(row['condition'])}",
                    condition=condition
                )[0]
                # TODO: error handling
                lc = LiquidCrystal.objects.get(name=row['LC'])
                pi = Polyimide.objects.get(name=row['PI'])
                seal = Seal.objects.get(name=row['Seal'])
                Chip.objects.create(
                    name=str(row['id']),
                    short_name=str(row['short id']),
                    sub=sub,
                    lc=lc,
                    pi=pi,
                    seal=seal
                )
            else:
                save_log['warning'].append(
                    f"Chip: {row['id']} already exists"
                )
        
        # Save log to cache
        cache.set('save_log', save_log)
        cache.set('df', pd.DataFrame(df))
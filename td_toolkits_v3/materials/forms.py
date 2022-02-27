from django import forms

import pandas as pd

from .models import (
    Vender,
    LiquidCrystal,
    Polyimide,
    Seal,
)

class MaterialsUploadForm(forms.Form):
    file = forms.FileField(
        help_text='Excel files(.xlsx)',
        widget=forms.FileInput(attrs={'accept': '.xlsx'})
    )

    def save(self):
        lc_df = pd.read_excel(
            self.cleaned_data['file'], sheet_name='LiquidCrystal')
        pi_df = pd.read_excel(
            self.cleaned_data['file'], sheet_name='Polyimide')
        seal_df = pd.read_excel(
            self.cleaned_data['file'], sheet_name='Seal')
        # LC part
        for row in lc_df.to_dict(orient='records'):
            if LiquidCrystal.objects.filter(name=row['Name']):
                continue
            else:
                vender = Vender.objects.get_or_create(name=row['Vender'])[0]
                LiquidCrystal.objects.create(
                    name=row['Name'],
                    vender=vender,
                    designed_cell_gap=row['designed cell gap(um)'],
                    t_ni=row['Tni(°C)'],
                    t_cn=row['Tcn(°C)'],
                    flow_viscosity=row['Flow Viscosity(ν)(mm^2/s)'],
                    rotational_viscosity=row['Rotational Viscosity(γ1)(mPa*s)'],
                    n_e=row['n_e'],
                    n_o=row['n_o'],
                    e_para=row['ε_∥'],
                    e_perp=row['ε_⟂'],
                    k_11=row['K11(pN)'],
                    k_22=row['K22(pN)'],
                    k_33=row['K33(pN)'],
                    density=row['d(g/cm^3)'],
                )

        # PI part
        for row in pi_df.to_dict(orient='records'):
            if Polyimide.objects.filter(name=row['Name']):
                continue
            else:
                vender = Vender.objects.get_or_create(name=row['Vender'])[0]
                Polyimide.objects.create(
                    name=row['Name'],
                    vender=vender,
                )
        # Seal part
        for row in seal_df.to_dict(orient='records'):
            if Seal.objects.filter(name=row['Name']):
                continue
            else:
                vender = Vender.objects.get_or_create(name=row['Vender'])[0]
                Seal.objects.create(
                    name=row['Name'],
                    vender=vender,
                )
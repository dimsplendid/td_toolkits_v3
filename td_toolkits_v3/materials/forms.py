from django import forms

import pandas as pd

from .models import (
    Vender,
    LiquidCrystal,
    Polyimide,
    Seal,
)

class MaterialsUploadForm(forms.Form):
    materials = forms.FileField(
        help_text='Excel file(.xlsx)',
        widget=forms.FileInput(attrs={'accept': '.xlsx'})
    )

    def save(self):
        lc_df = pd.read_excel(
            self.cleaned_data['materials'], sheet_name='LiquidCrystal')
        pi_df = pd.read_excel(
            self.cleaned_data['materials'], sheet_name='Polyimide')
        seal_df = pd.read_excel(
            self.cleaned_data['materials'], sheet_name='Seal')
        # LC part
        for row in lc_df.to_dict(orient='records'):
            if LiquidCrystal.objects.filter(name=row['Name']):
                continue
            else:
                vender = Vender.objects.get_or_create(
                    name=str(row['Vender']))[0]
                LiquidCrystal.objects.create(
                    name=str(row['Name']),
                    vender=vender,
                    designed_cell_gap=float(row['designed cell gap(um)']),
                    t_ni=float(row['Tni(°C)']),
                    t_cn=float(row['Tcn(°C)']),
                    flow_viscosity=float(row['Flow Viscosity(ν)(mm^2/s)']),
                    rotational_viscosity=float(row['Rotational Viscosity(γ1)(mPa*s)']),
                    n_e=float(row['n_e']),
                    n_o=float(row['n_o']),
                    e_para=float(row['ε_∥']),
                    e_perp=float(row['ε_⟂']),
                    k_11=float(row['K11(pN)']),
                    k_22=float(row['K22(pN)']),
                    k_33=float(row['K33(pN)']),
                    density=float(row['d(g/cm^3)']),
                )

        # PI part
        for row in pi_df.to_dict(orient='records'):
            if Polyimide.objects.filter(name=row['Name']):
                continue
            else:
                vender = Vender.objects.get_or_create(
                    name=str(row['Vender']))[0]
                Polyimide.objects.create(
                    name=str(row['Name']),
                    vender=vender,
                )
        # Seal part
        for row in seal_df.to_dict(orient='records'):
            if Seal.objects.filter(name=row['Name']):
                continue
            else:
                vender = Vender.objects.get_or_create(
                    name=str(row['Vender']))[0]
                Seal.objects.create(
                    name=str(row['Name']),
                    vender=vender,
                )

class MaterialsUpdateForm(forms.Form):
    materials = forms.FileField(
        help_text='Excel file(.xlsx)',
        widget=forms.FileInput(attrs={'accept': '.xlsx'})
    )

    def save(self):
        lc_df = pd.read_excel(
            self.cleaned_data['materials'], sheet_name='LiquidCrystal')
        pi_df = pd.read_excel(
            self.cleaned_data['materials'], sheet_name='Polyimide')
        seal_df = pd.read_excel(
            self.cleaned_data['materials'], sheet_name='Seal')
        # LC part
        for row in lc_df.to_dict(orient='records'):
            try:
                lc = LiquidCrystal.objects.get(name=row['Name'])
                vender = Vender.objects.get_or_create(
                    name=str(row['Vender']))[0]
                
                lc.vender=vender
                lc.designed_cell_gap=float(row['designed cell gap(um)'])
                lc.t_ni=float(row['Tni(°C)'])
                lc.t_cn=float(row['Tcn(°C)'])
                lc.flow_viscosity=float(row['Flow Viscosity(ν)(mm^2/s)'])
                lc.rotational_viscosity=float(row['Rotational Viscosity(γ1)(mPa*s)'])
                lc.n_e=float(row['n_e'])
                lc.n_o=float(row['n_o'])
                lc.e_para=float(row['ε_∥'])
                lc.e_perp=float(row['ε_⟂'])
                lc.k_11=float(row['K11(pN)'])
                lc.k_22=float(row['K22(pN)'])
                lc.k_33=float(row['K33(pN)'])
                lc.density=float(row['d(g/cm^3)'])

                lc.save()
                
            except Exception as e: print(e)

        # PI part
        for row in pi_df.to_dict(orient='records'):
            try:
                pi = Polyimide.objects.get(name=row['Name'])
                vender = Vender.objects.get_or_create(
                    name=str(row['Vender']))[0]
                
                pi.name=str(row['Name'])
                pi.vender=vender

                pi.save()
                
            except Exception as e: print(e)

        # Seal part
        for row in seal_df.to_dict(orient='records'):
            try:
                seal = Seal.objects.get(name=row['Name'])
                vender = Vender.objects.get_or_create(
                    name=str(row['Vender']))[0]
                
                seal.name=str(row['Name'])
                seal.vender=vender

                seal.save()
                
            except Exception as e: print(e)

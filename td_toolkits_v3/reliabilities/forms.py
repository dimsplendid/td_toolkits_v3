from django import forms
import pandas as pd

from td_toolkits_v3.materials.models import (
    LiquidCrystal,
    Polyimide,
    Seal,
    Vender,
)

from .models import (
    Adhesion,
    DeltaAngle,
    File,
    LowTemperatureOperation,
    LowTemperatureStorage,
    PressureCookingTest,
    SealWVTR,
    UShapeAC,
    VoltageHoldingRatio,
)

class ReliabilitiesUploadForm(forms.Form):
    reliabilites = forms.FileField(
        help_text='Excel file',
        widget=forms.FileInput(attrs={'accept': '.xlsx'})
    )

    @staticmethod
    def get_configureation(row):
        """
        Simplify the way to get the whole configuration.
        Including deal with create and None value
        
        Parameters
        ----------
        row: list-like array
            The structure should ('', lc, pi, seal, ...)
        """
        if row[1] == 'N.A.':
            lc = None
        else:
            lc, _ = LiquidCrystal.objects.get_or_create(name=row[1])
        if row[2] == 'N.A.':
            pi = None
        else:
            pi, _ = Polyimide.objects.get_or_create(name=row[2])
        if row[3] == 'N.A.':
            seal = None
        else:
            seal, _ = Seal.objects.get_or_create(name=row[3])
        return lc, pi, seal

    def save(self):
        # TODO: This should also have a more elegant way to implment it.
        adhesion_df = pd.read_excel(
            self.cleaned_data['reliabilites'], sheet_name='Adhesion'
        )
        lto_df = pd.read_excel(
            self.cleaned_data['reliabilites'], sheet_name='LTO'
        )
        lts_df = pd.read_excel(
            self.cleaned_data['reliabilites'], sheet_name='LTS'
        )
        pct_df = pd.read_excel(
            self.cleaned_data['reliabilites'], sheet_name='PCT'
        )
        seal_wvtr_df = pd.read_excel(
            self.cleaned_data['reliabilites'], sheet_name='Seal WVTR'
        )
        delta_angle_df = pd.read_excel(
            self.cleaned_data['reliabilites'], sheet_name='Δangle'
        )
        u_shape_ac_df = pd.read_excel(
            self.cleaned_data['reliabilites'], sheet_name='U-Shape AC'
        )
        vhr_df = pd.read_excel(
            self.cleaned_data['reliabilites'], sheet_name='VHR'
        )
        # Store each table
        if len(adhesion_df):
            # TODO: The field would change later
            for _, row in adhesion_df.iterrows():
                lc, pi, seal = self.get_configureation(row)
                vender, _ = Vender.objects.get_or_create(name=row[8])
                file, _ = File.objects.get_or_create(name=row[9])
                if not Adhesion.objects.filter(
                    lc=lc, pi=pi, seal=seal, vender=vender, file_source=file,
                    adhesion_interface=row[5], method=row[6]).exists():
                    Adhesion.objects.create(
                        lc=lc, pi=pi, seal=seal, vender=vender, 
                        file_source=file,
                        adhesion_interface=row[5], 
                        method=row[6], 
                        value=row[4], 
                        peeling=row[7]
                    )

        if len(lto_df):
            for _, row in lto_df.iterrows():
                lc, pi, seal = self.get_configureation(row)
                vender, _ = Vender.objects.get_or_create(name=row[9])
                file, _ = File.objects.get_or_create(name=row[10])
                jar_test_seal, _ = Seal.objects.get_or_create(name=row[7])
                
                if not LowTemperatureOperation.objects.filter(
                    lc=lc, pi=pi, seal=seal, vender=vender, file_source=file,
                    storage_condition=row[5], slv_condition=row[6],
                    jar_test_seal=jar_test_seal,
                    measure_temperature=row[8]).exists():

                    LowTemperatureOperation.objects.create(
                        lc=lc, pi=pi, seal=seal, vender=vender, file_source=file,
                        storage_condition=row[5], slv_condition=row[6],
                        jar_test_seal=jar_test_seal, measure_temperature=row[8],
                        value=LowTemperatureOperation.value_mapping[row[4]])

        if len(lts_df):
            for _, row in lts_df.iterrows():
                lc, pi, seal = self.get_configureation(row)
                vender, _ = Vender.objects.get_or_create(name=row[9])
                file, _ = File.objects.get_or_create(name=row[10])
                jar_test_seal, _ = Seal.objects.get_or_create(name=row[7])
                
                if not LowTemperatureStorage.objects.filter(
                    lc=lc, pi=pi, seal=seal, vender=vender, file_source=file,
                    storage_condition=row[5], slv_condition=row[6],
                    jar_test_seal=jar_test_seal,
                    measure_temperature=row[8]).exists():
                    LowTemperatureStorage.objects.create(
                        lc=lc, pi=pi, seal=seal, vender=vender, 
                        file_source=file,
                        storage_condition=row[5], slv_condition=row[6],
                        jar_test_seal=jar_test_seal, measure_temperature=row[8],
                        value=row[4])

        if len(pct_df):
            for _, row in pct_df.iterrows():
                lc, pi, seal = self.get_configureation(row)
                vender, _ = Vender.objects.get_or_create(name=row[7])
                file, _ = File.objects.get_or_create(name=row[8])
                if not PressureCookingTest.objects.filter(
                    lc=lc, pi=pi, seal=seal, vender=vender, file_source=file,
                    measure_condition=row[5], test_vehical=row[6],
                    ).exists():
                    PressureCookingTest.objects.create(
                        value=row[4], lc=lc, pi=pi, seal=seal, vender=vender, 
                        file_source=file,
                        measure_condition=row[5], test_vehical=row[6],
                    )

        if len(seal_wvtr_df):
            # TODO: The field would change
            for _, row in seal_wvtr_df.iterrows():
                lc, pi, seal = self.get_configureation(row)
                vender, _ = Vender.objects.get_or_create(name=row[8])
                file, _ = File.objects.get_or_create(name=row[9])
                if not SealWVTR.objects.filter(
                    lc=lc, pi=pi, seal=seal, vender=vender, file_source=file,
                    temperature=row[5], humidity=row[6], thickness=row[7]
                    ).exists():
                    SealWVTR.objects.create(
                        value=row[4], lc=lc, pi=pi, seal=seal, vender=vender, 
                        file_source=file,
                        temperature=row[5], humidity=row[6], thickness=row[7])

        if len(delta_angle_df):
            for _, row in delta_angle_df.iterrows():
                lc, pi, seal = self.get_configureation(row)
                vender, _ = Vender.objects.get_or_create(name=row[9])
                file, _ = File.objects.get_or_create(name=row[10])
                if not DeltaAngle.objects.filter(
                    lc=lc, pi=pi, seal=seal, vender=vender, file_source=file,
                    measure_voltage=row[5], measure_freq=row[6], 
                    measure_time=row[7],
                    measure_temperature=row[8]
                ).exists():
                    DeltaAngle.objects.create(
                        value=row[4], lc=lc, pi=pi, seal=seal, vender=vender, 
                        file_source=file,
                        measure_voltage=row[5], 
                        measure_freq=row[6], 
                        measure_time=row[7],
                        measure_temperature=row[8]
                    )

        if len(u_shape_ac_df):
            for _, row in u_shape_ac_df.iterrows():
                lc, pi, seal = self.get_configureation(row)
                vender, _ = Vender.objects.get_or_create(name=row[7])
                file, _ = File.objects.get_or_create(name=row[8])
                if not UShapeAC.objects.filter(
                    lc=lc, pi=pi, seal=seal, vender=vender, file_source=file,
                    time=row[5], temperature=row[6],).exists():
                    UShapeAC.objects.create(
                        value=row[4], lc=lc, pi=pi, seal=seal, vender=vender, 
                        file_source=file,
                        time=row[5], temperature=row[6],)

        if len(vhr_df):
            for _, row in vhr_df.iterrows():
                lc, pi, seal = self.get_configureation(row)
                vender, _ = Vender.objects.get_or_create(name=row[9])
                file, _ = File.objects.get_or_create(name=row[10])
                if not VoltageHoldingRatio.objects.filter(
                    lc=lc, pi=pi, seal=seal, vender=vender, file_source=file,
                    measure_voltage=row[5], measure_freq=row[6], 
                    measure_temperature=row[7],
                    uv_aging=row[8]).exists():
                    VoltageHoldingRatio.objects.create(
                        value=row[4], lc=lc, pi=pi, seal=seal, vender=vender, 
                        file_source=file,
                        measure_voltage=row[5], measure_freq=row[6], 
                        measure_temperature=row[7],
                        uv_aging=row[8]
                    )

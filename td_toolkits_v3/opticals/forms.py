import io
from typing import List, Tuple, Dict, Union, Optional
import csv
from datetime import datetime, timedelta, timezone
import numpy as np
import pandas as pd

from django import forms
from django.http import HttpRequest
from django.core.cache import cache

from td_toolkits_v3.products.models import (
    ProductModelType,
    Project,
    Factory,
    Experiment,
    Condition,
    Sub,
    Chip,
)
from td_toolkits_v3.materials.models import (
    LiquidCrystal,
    Polyimide,
    Seal,
)

from . import models

from .models import (
    Instrument,
    AxometricsLog,
    OpticalSearchProfile,
    RDLCellGap,
    OpticalLog,
    ResponseTimeLog,
    OpticalReference,
    OpticalReference,
    OptFittingModel,
    RTFittingModel,
    BackLightUnit,
    BackLightIntensity,
)
from .tools.utils import (
    OptLoader, 
    OptFitting, # TODO: to be deprecated
    OPTFitting,
    RTFitting,
    MaterialConfiguration,
    OptTableGenerator,
    tr2_score,
)

from td_toolkits_v3.materials.tools.utils import (
    LiquidCrystalPydantic,
)


class AxoUploadForm(forms.Form):

    exp_id = forms.ChoiceField(choices=[("", "")], initial=None)
    factory = forms.ChoiceField(choices=[("", "")], initial=None)

    axos = forms.FileField(
        widget=forms.FileInput(
            attrs={
                "multiple": True,
                "webkitdirectory": True,
                "directory": True,
            }
        )
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set the last experiment name for the upload axo data
        self.fields["exp_id"].choices = list(
            Experiment.objects.all().values_list("name", "name")
        )
        last_exp = Experiment.objects.last()
        if last_exp is not None:
            last_exp_id = last_exp.name
            self.fields["exp_id"].initial = (last_exp_id, last_exp_id)
        Factory.default("T2")
        self.fields["factory"].choices = list(
            Factory.objects.all().values_list("name", "name")
        )
        self.fields["factory"].initial = ("T2", "T2")

    def save(self, request):
        files = request.FILES.getlist("axos")
        experiment = Experiment.objects.get(
            name=str(self.cleaned_data["exp_id"]))
        # print(files)
        factory = Factory.default(self.cleaned_data["factory"])
        instrument = Instrument.default("AXO", factory)

        # the axo location order map to opt measurement point
        # points = [5, 3, 1, 6, 4, 2]
        points = [1, 2, 3, 4, 5, 6]

        save_log = {
            'file_name': [],
            'warning': [],
        }
        
        for file in files:
            file_name = str(file).split(".")[0]
            short_names = [s.strip() for s in file_name.split("+")]

            reader = csv.reader(
                io.StringIO(file.read().decode("utf-8", errors="ignore"))
            )
            data_range = range(28, 28 + len(points) * len(short_names))
            data = [
                list(map(float,row))  for idx, row
                in enumerate(reader) if idx in data_range
            ]
            row_count = 0
            save_log['file_name'].append(file_name)
            for short_name in short_names:
                # print(short_name)
                # Check if there is chip data, otherwise skip.
                try:
                    chip = Chip.objects.get(
                        short_name=short_name, 
                        sub__condition__experiment=experiment
                    )
                except:
                    save_log['warning'].append(
                        f"Chip: {short_name} is not in the database."
                    )
                    continue
                # print(chip)
                for point in points:
                    try:
                        AxometricsLog.objects.get(
                            chip=chip,
                            measure_point=point,
                        )
                        save_log['warning'].append(
                            f"{chip.name}({chip.short_name})"
                            f" at point [{point}] is duplicate, keep the old one"
                        )
                        continue
                    except:
                        if data[row_count][8] > 1:
                            save_log['warning'].append(
                                f"Measurement at {chip.name}({chip.short_name}) "
                                f"of point [{point}] has large RMS({data[row_count][8]}), "
                                f"skip it."
                            )
                            continue
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
                            instrument=instrument,
                        )
                        row_count += 1
        
            cache.set("df", 
                pd.DataFrame.from_records(
                    AxometricsLog.objects.filter(
                        chip__sub__condition__experiment=experiment
                    ).values(
                        'chip__name',
                        'cell_gap',
                        'rms',
                    )
                ).rename(columns={
                    'chip__name': 'ID',
                    'cell_gap': 'Cell Gap',
                    'rms': 'RMS',
                })
            )
            cache.set("save_log", save_log)
        


class RDLCellGapUploadForm(forms.Form):
    exp_id = forms.ChoiceField(choices=[("", "")], initial=None)

    rdl_cell_gap = forms.FileField(
        widget=forms.FileInput(attrs={"accept": ".xlsx"})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set the last experiment name for the upload axo data
        self.fields["exp_id"].choices = list(
            Experiment.objects.all().values_list("name", "name")
        )
        last_exp = Experiment.objects.last()
        if last_exp is not None:
            last_exp_id = last_exp.name
            self.fields["exp_id"].initial = (last_exp_id, last_exp_id)

    def save(self):
        rdl_cell_gap = pd.read_excel(
            self.cleaned_data["rdl_cell_gap"],
            sheet_name='upload',
        )
        # make sure the short id type is str.
        rdl_cell_gap = rdl_cell_gap.astype({'short id': 'str'})
        
        experiment = Experiment.objects.get(
            name=str(self.cleaned_data["exp_id"]))

        factory = Factory.default("Fab1")
        instrument = Instrument.default("RETS", factory)
        save_log = {
            "file_name": [self.cleaned_data['rdl_cell_gap']],
            "warning": [],
        }
        for row in rdl_cell_gap.to_numpy():
            # Check if there is chip data, otherwise skip.
            try:
                chip = Chip.objects.get(
                    short_name=row[0], 
                    sub__condition__experiment=experiment
                )
            except:
                save_log["warning"].append(
                    f"Chip: {row[0]} is not in the database."
                )
                continue
            
            try:
                RDLCellGap.objects.get(
                    chip=chip
                )
                save_log["warning"].append(
                    f"The chip {chip.name}({chip.short_name}) is duplicate, keep the old one"
                )
                continue
            except:
                RDLCellGap.objects.create(
                    chip=chip, cell_gap=row[1], instrument=instrument
                )
        cache.set(
            "df",
            pd.DataFrame.from_records(
                RDLCellGap.objects.filter(
                    chip__sub__condition__experiment=experiment
                ).values(
                    'chip__name',
                    'cell_gap',
                )
            ).rename(columns={
                'chip__name': 'ID',
                'cell_gap': 'Cell Gap',
            })
        )
        cache.set("save_log", save_log)

class AlterRdlCellGapUploadForm(forms.Form):
    exp_id = forms.ChoiceField(
        choices=[("", "")], initial=None 
    )
    
    rdl_cell_gap = forms.FileField(
        widget=forms.FileInput(attrs={"accept": ".xlsx"})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['exp_id'].choices = list(
            Experiment.objects.all().values_list('name', 'name')
        )
        last_exp = Experiment.objects.last()
        if last_exp is not None:
            last_exp_id = last_exp.name
            self.fields['exp_id'].initial = (last_exp_id, last_exp_id)
    
    def save(self):
        rdl_cell_gap = pd.read_excel(
            self.cleaned_data["rdl_cell_gap"],
            sheet_name='upload',
        )
        
        # make sure the short id type is str.
        rdl_cell_gap = rdl_cell_gap.astype({'short id': 'str'})
        
        experiment = Experiment.objects.get(
            name=str(self.cleaned_data["exp_id"])
        )
        
        log = {
            'file_name': [self.cleaned_data['rdl_cell_gap']],
            'warning': [],
        }
        bulk_create_list = []
        bulk_update_list = []
        
        for row in rdl_cell_gap.to_numpy():
            # Check if there is chip data, otherwise skip.
            try:
                chip = Chip.objects.get(
                    short_name=row[0], 
                    sub__condition__experiment=experiment
                )
            except Chip.DoesNotExist:
                log['warning'].append(
                    f"Chip: {row[0]} is not in the database."
                )
                continue
            try:
                rdl_cell_gap = models.AlterRdlCellGap.objects.get(
                    chip=chip,
                    measure_point=row[1],
                )
                log['warning'].append(
                    f"The chip {chip.name}({chip.short_name})[{rdl_cell_gap.measure_point}] is duplicate, overwrite the old one"
                )
                rdl_cell_gap.cell_gap = row[2]
                bulk_update_list.append(rdl_cell_gap)
                
            except:
                bulk_create_list.append(
                    models.AlterRdlCellGap(
                        chip=chip, 
                        measure_point=row[1],
                        cell_gap=row[2], 
                    )
                )
        models.AlterRdlCellGap.objects.bulk_create(bulk_create_list)
        models.AlterRdlCellGap.objects.bulk_update(bulk_update_list, ['cell_gap'])
        cache.set('save_log', log)

class OptUploadForm(forms.Form):
    exp_id = forms.ChoiceField(choices=[("", "")], initial=None)
    factory = forms.ChoiceField(choices=[("", "")], initial=None)
    log_id = forms.ChoiceField(
        choices=[("panel_id", "Panel ID"), ("short_id", "Short ID")], 
        initial=("panel_id", "Panel ID"),
    )
    
    opts = forms.FileField(
        widget=forms.FileInput(
            attrs={
                "multiple": True,
                "webkitdirectory": True,
                "directory": True,
            }
        )
    )
    

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set the last experiment name for the upload axo data
        self.fields["exp_id"].choices = list(
            Experiment.objects.all().values_list("name", "name")
        )
        last_exp = Experiment.objects.last()
        if last_exp is not None:
            last_exp_id = last_exp.name
            self.fields["exp_id"].initial = (last_exp_id, last_exp_id)
        Factory.default("TOC")
        self.fields["factory"].choices = list(
            Factory.objects.all().values_list("name", "name")
        )
        self.fields["factory"].initial = ("TOC", "TOC")

    def save(self, request):
        files = request.FILES.getlist("opts")
        experiment = Experiment.objects.get(
            name=str(self.cleaned_data["exp_id"]))
        # print(files)
        factory = Factory.default(self.cleaned_data["factory"])
        opt_df_list = [pd.DataFrame()]
        
        save_log = {
            "file_name": [file.name for file in files],
            "warning": [],
        }
        
        for file in files:
            if not file.name.endswith('csv'):
                save_log["warning"].append(
                    f"File {file.name} is not a csv file, skip it."
                )
                continue
            # Using pd read csv this time
            tmp_df = pd.read_csv(
                file, encoding="utf-8", encoding_errors="ignore")
            opt_df_list.append(tmp_df)
            
        opt_df = pd.concat(opt_df_list)

        if len(opt_df) == 0:
            save_log["warning"].append("No data found in the file")
            return
        # print(opt_df.head())
        # 0. drop na for chip, date, time
        opt_df = opt_df.dropna(
            subset=[
                opt_df.columns[0],  # Date
                opt_df.columns[1],  # Time
                opt_df.columns[2],  # ID or Short ID
                opt_df.columns[3],  # measure point
                opt_df.columns[6],  # voltage
            ]
        )
        # 1. drop V == 1, the data separate note
        opt_df = opt_df[opt_df.iloc[:, 6] != 1]
        # 2. change Vpp to Vop
        opt_df.iloc[:, 6] = opt_df.iloc[:, 6] / 2
        # 3. transform datetime
        opt_df["datetime"] = [
            datetime.strptime(
                f"{opt_df.iloc[i, 0]} {opt_df.iloc[i, 1]} +0800",
                r"%Y/%m/%d %H:%M:%S %z",
            )
            for i in range(len(opt_df))
        ]

        # 4. drop duplicate (keep newer)
        opt_df = opt_df.sort_values("datetime").drop_duplicates(
            subset=[
                # cause sometime the header maybe different?
                # using the position otherwise.
                opt_df.columns[2],  # ID
                opt_df.columns[3],  # measure point
                opt_df.columns[6],  # voltage
            ],
            keep="last",
        )

        # 5. drop chip that already logged
        if self.cleaned_data["log_id"] == "panel_id":
            chip_could_log = [
                i.name
                for i in Chip.objects.filter(
                    sub__condition__experiment=experiment, opticallog__isnull=True
                ).distinct()
            ]
        elif self.cleaned_data["log_id"] == "short_id":
            chip_could_log = [
                i.short_name
                for i in Chip.objects.filter(
                    sub__condition__experiment=experiment, opticallog__isnull=True
                ).distinct()
            ]
        else:
            raise ValueError("Wrong log id")
        
        origin_opt_df = opt_df
        # cast the id to str
        opt_df.iloc[:, 2] = opt_df.iloc[:, 2].astype("str")
        opt_df = opt_df[opt_df.iloc[:, 2].isin(chip_could_log)]
        
        if len(opt_df) == 0:
            print(origin_opt_df.info())
            save_log["warning"].append("No logable data found in the file")
            cache.set("save_log", save_log)
            return
        
        # 6. modified data type
        opt_df.iloc[:, 3] = opt_df.iloc[:, 3].astype("int")  # measure point
        opt_df.iloc[:, 5] = opt_df.iloc[:, 5].astype("str")  # operator
        opt_df.iloc[:, 6] = opt_df.iloc[:, 6].astype("float")  # voltage
        opt_df.iloc[:, 11] = opt_df.iloc[:, 11].astype("float")  # lc percent
        opt_df.iloc[:, 23] = opt_df.iloc[:, 23].astype("float")  # w_capital_y
        opt_df.iloc[:, 32] = opt_df.iloc[:, 32].astype("float")  # w_x
        opt_df.iloc[:, 33] = opt_df.iloc[:, 33].astype("float")  # w_y
        # 7. batch create for each chip
        logs = []
        instrument = Instrument.default(opt_df.iloc[0, 4], factory)

        for chip_name in opt_df.iloc[:, 2].unique():
            try:
                if self.cleaned_data["log_id"] == "panel_id":
                    chip = Chip.objects.get(
                        name=chip_name, sub__condition__experiment=experiment
                    )
                elif self.cleaned_data["log_id"] == "short_id":
                    chip = Chip.objects.get(
                        short_name=chip_name, sub__condition__experiment=experiment
                    )
                else:
                    raise ValueError("Wrong log id")
            except Chip.DoesNotExist:
                save_log["warning"].append(
                    f"The chip {chip_name} is not found in the experiment"
                )
                continue
                
            tmp_df = opt_df[opt_df.iloc[:, 2] == chip_name]
            if len(tmp_df) == 0:
                continue
            for row in tmp_df.to_numpy():
                logs.append(
                    OpticalLog(
                        chip=chip,
                        measure_point=row[3],
                        measure_time=row[-1],
                        instrument=instrument,
                        operator=row[5],
                        voltage=row[6],
                        lc_percent=row[11],
                        w_capital_y=row[23],
                        w_x=row[32],
                        w_y=row[33],
                    )
                )

        OpticalLog.objects.bulk_create(logs)

        # save the log to cache
        cache.set("save_log", save_log)

class ResponseTimeUploadForm(forms.Form):
    exp_id = forms.ChoiceField(choices=[("", "")], initial=None)
    factory = forms.ChoiceField(choices=[("", "")], initial=None)
    data_type = forms.ChoiceField(choices=(
            ('txt', 'Raw(.txt)'),
            ('xlsx', 'Excel(.xlsx)'),
        ),
        initial='txt'
    )
    log_id = forms.ChoiceField(
        choices=[("panel_id", "Panel ID"), ("short_id", "Short ID")], 
        initial=("panel_id", "Panel ID"),
    )

    rts = forms.FileField(
        widget=forms.FileInput(
            attrs={
                "multiple": True,
                "webkitdirectory": True,
                "directory": True,
            }
        )
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set the last experiment name for the upload axo data
        self.fields["exp_id"].choices = list(
            Experiment.objects.all().values_list("name", "name")
        )
        last_exp = Experiment.objects.last()
        if last_exp is not None:
            last_exp_id = last_exp.name
            self.fields["exp_id"].initial = (last_exp_id, last_exp_id)
        Factory.default("TOC")
        self.fields["factory"].choices = list(
            Factory.objects.all().values_list("name", "name")
        )
        self.fields["factory"].initial = ("TOC", "TOC")

    def save(self, request):
        files = request.FILES.getlist("rts")
        experiment = Experiment.objects.get(
            name=str(self.cleaned_data["exp_id"]))
        print(files)
        factory = Factory.default(self.cleaned_data["factory"])
        data_type = self.cleaned_data['data_type']

        rt_df_list = [pd.DataFrame()]
        
        save_log = {
            "file_name": [file.name for file in files],
            "warning": [],
        }
        for file in files:
            print(file.name)
            if data_type == 'txt':
                if not file.name.endswith('txt'):
                    print(f'skip {file}')
                    continue
                tmp_df = pd.read_table(
                    file, encoding="utf-8", encoding_errors="ignore")
                rt_df_list.append(tmp_df)
            elif data_type == 'xlsx':
                if not file.name.endswith('xlsx'):
                    print(f'skip {file}')
                    continue
                tmp_df = pd.read_excel(file)
                rt_df_list.append(tmp_df)
            else:
                print('Something wrong, I should never touch this place.')
                raise ValueError('wrong data type')
        rt_df = pd.concat(rt_df_list)

        # There are some row are the header, cause they just
        # merge the file directory.
        # Yea, I don't know why ether...
        unwanted_mask = rt_df.iloc[:, 7].astype("str").str.match("[ a-zA-Z]+")
        rt_df = rt_df[~unwanted_mask]
        if len(rt_df) == 0:
            save_log["warning"].append("No logable data found in the files after unwanted mask")
            cache.set("save_log", save_log)
            return

        # modified types
        for col in [3, 7, 17, 19]:
            rt_df.iloc[:, col] = rt_df.iloc[:, col].astype("float")
        # operator should be str
        rt_df.iloc[:, 5] = rt_df.iloc[:, 5].astype("str")
        # id should be str
        rt_df.iloc[:, 2] = rt_df.iloc[:, 2].astype("str")

        print(rt_df.head())
        # 0. drop na for chip, date, time
        rt_df = rt_df.dropna(
            subset=[
                rt_df.columns[0],  # Date
                rt_df.columns[1],  # Time
                rt_df.columns[2],  # ID
                rt_df.columns[3],  # measure point
                rt_df.columns[7],  # voltage
            ]
        )
        # 1. trasform datetime
        if data_type == 'txt':
            rt_df["datetime"] = [
                datetime.strptime(
                    f"{rt_df.iloc[i, 0]} {rt_df.iloc[i, 1]} +0800", 
                    r"%Y/%m/%d %H:%M:%S %z"
                )
                for i in range(len(rt_df))
            ]
        elif data_type == 'xlsx':
            rt_df["datetime"] = [
                datetime.strptime(
                    f"{rt_df.iloc[i, 0]} {rt_df.iloc[i, 1]} +0800", 
                    r"%Y/%m/%d %H:%M:%S %z"
                )
                for i in range(len(rt_df))
            ]
        # 2. drop duplicate(keep newer)
        rt_df = rt_df.sort_values("datetime").drop_duplicates(
            subset=[
                # cause sometime the header maybe different?
                # using the position otherwise.
                rt_df.columns[2],  # ID
                rt_df.columns[3],  # measure point
                rt_df.columns[7],  # voltage
            ],
            keep="last",
        )

        # 3. drop chip that already logged
        if self.cleaned_data["log_id"] == "panel_id":
            chip_could_log = [
                i.name
                for i in Chip.objects.filter(
                    sub__condition__experiment=experiment, 
                    responsetimelog__isnull=True
                ).distinct()
            ]
        elif self.cleaned_data["log_id"] == "short_id":
            chip_could_log = [
                i.short_name
                for i in Chip.objects.filter(
                    sub__condition__experiment=experiment, 
                    responsetimelog__isnull=True
                ).distinct()
            ]
        else:
            raise ValueError("Wrong log id")

        rt_df = rt_df[rt_df.iloc[:, 2].isin(chip_could_log)]
        if len(rt_df) == 0:
            save_log["warning"].append("No logable data found in the files")
            cache.set("save_log", save_log)
            return
        logs = []
        instrument = Instrument.default(rt_df.iloc[0, 4], factory)

        # 4. batch create for each chip
        for chip_name in rt_df.iloc[:, 2].unique():
            if self.cleaned_data["log_id"] == "panel_id":
                chip = Chip.objects.get(
                    name=chip_name, sub__condition__experiment=experiment
                )
            elif self.cleaned_data["log_id"] == "short_id":
                chip = Chip.objects.get(
                    short_name=chip_name, sub__condition__experiment=experiment
                )
            else:
                raise ValueError("Wrong log id")
            chip = chip
            tmp_df = rt_df[rt_df.iloc[:, 2] == chip_name]
            for row in tmp_df.to_numpy():
                logs.append(
                    ResponseTimeLog(
                        chip=chip,
                        measure_point=row[3],
                        measure_time=row[-1],
                        instrument=instrument,
                        operator=row[5],
                        voltage=row[7],
                        time_rise=row[17],
                        time_fall=row[19],
                    )
                )

        ResponseTimeLog.objects.bulk_create(logs)


class CalculateOpticalForm(forms.Form):
    exp_id = forms.ChoiceField(choices=[("", "")], initial=None)
    cell_gap = forms.ChoiceField(
        choices=[('axo', 'AXO'), ('rdl', 'RDL - 1 Point'), ('rdl_alter', 'RDL - 6 Points')],
        initial=('axo', 'AXO'),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set the last experiment name for the upload axo data
        self.fields["exp_id"].choices = list(
            Experiment.objects.all().values_list("name", "name")
        )
        last_exp = Experiment.objects.last()
        if last_exp is not None:
            last_exp_id = last_exp.name
            self.fields["exp_id"].initial = (last_exp_id, last_exp_id)

    def calculate(self, request):

        request.session["message"] = 'Error:'
        data_loader = OptLoader(
            self.cleaned_data['exp_id'],
            self.cleaned_data['cell_gap'],
        )

        opt_df = data_loader.opt
        rt_df = data_loader.rt

        # Check both data have the same kinds of LC
        if not (set(opt_df['LC'].unique()) == set(rt_df['LC'].unique())):
            raise ValueError(
                'The opt and rt has different kinds lc.'
                f"opt_df: {opt_df['LC'].unique()}"
                f"rt_df: {rt_df['LC'].unique()}"
            )
        
        msg = ''
            
        for lc in opt_df['LC'].unique():
            tmp_rt_df = rt_df[rt_df['LC'] == lc]
            tmp_opt_df = opt_df[opt_df['LC'] == lc]
            opt_fitting = OptFitting(lc, tmp_rt_df, tmp_opt_df)
            msg = opt_fitting.save(lc, self.cleaned_data['exp_id'])

        if type(msg) == str:
            request.session["message"] = msg
        else:
            request.session["message"] = (
                'Calculate '
                f'{self.cleaned_data["exp_id"]}'
                ' success.'
            )
        request.session["exp_id"] = self.cleaned_data['exp_id']

class ProductModelTypeForm(forms.ModelForm):
    class Meta:
        model = ProductModelType
        fields = ['name', 'model_name', 'factory']

class OpticalReferenceForm(forms.ModelForm):
    class Meta:
        model = OpticalReference
        fields = [
        'lc',
        'pi',
        'seal',
        'cell_gap',
        'voltage',
        'ito_slit',
        'tft_tech',
        'transmittance',
        'time_rise',
        'time_fall',
        'gray_to_gray',
        'w_x',
        'w_y',
        'contrast_ratio',
    ]

OpticalReferenceFormset = forms.inlineformset_factory(
    ProductModelType, 
    OpticalReference,
    form=OpticalReferenceForm,
)

class FittingBaseForm(forms.Form):
    
    exp_id = forms.ChoiceField(choices=[("", "")], initial=None)
    cell_gap = forms.ChoiceField(
        choices=[('axo', 'AXO'), ('rdl', 'RDL - 1 Point'), ('rdl_alter', 'RDL - 6 Points')],
        initial=('axo', 'AXO'),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set the last experiment name for the upload axo data
        self.fields["exp_id"].choices = list(
            Experiment.objects.all().values_list("name", "name")
        )
        last_exp = Experiment.objects.last()
        if last_exp is not None:
            last_exp_id = last_exp.name
            self.fields["exp_id"].initial = (last_exp_id, last_exp_id)
            
    def calculate(self, request):
        raise NotImplementedError
    
class OptFittingForm(FittingBaseForm):
    
    def calculate(self, request):
        request.session["message"] = 'Error:'
        data_loader = OptLoader(
            self.cleaned_data['exp_id'],
            self.cleaned_data['cell_gap'],
        )

        opt_df = data_loader.opt
        if type(opt_df) == str:
            print(opt_df)
            request.session["message"] = opt_df
            return
        elif type(opt_df) == pd.DataFrame:
            # cast type of opt_df to dataframe
            opt_df = opt_df
        else:
            raise ValueError('Wrong type of opt_df')
            
        opt_df['cfg'] = opt_df['LC'] + ',' + opt_df['PI'] + ',' + opt_df['Seal']

        all_cfg = [
            MaterialConfiguration(*c.split(',')) for c in opt_df.cfg.unique()
        ]
        
        msg = ''
        
        for cfg in all_cfg:
            tmp_opt_df = opt_df[
                  (opt_df['LC']==cfg.lc) 
                & (opt_df['PI']==cfg.pi)
                & (opt_df['Seal']==cfg.seal)
            ]
            opt_fitting = OPTFitting(cfg, tmp_opt_df)
            msg = opt_fitting.save(self.cleaned_data['exp_id'])

        if type(msg) == str:
            request.session["message"] = msg
        else:
            request.session["message"] =( 'Calculate '
                f'{self.cleaned_data["exp_id"]}'
                ' success.')
        request.session["exp_id"] = self.cleaned_data['exp_id']

class RTFittingForm(FittingBaseForm):
    
    def calculate(self, request):
        request.session["message"] = 'Error:'
        data_loader = OptLoader(
            self.cleaned_data['exp_id'],
            self.cleaned_data['cell_gap'],
        )

        rt_df = data_loader.rt
        if type(rt_df) == str:
            print(rt_df)
            request.session["message"] = rt_df
            return
        elif type(rt_df) == pd.DataFrame:
            # cast type of opt_df to dataframe
            rt_df = rt_df
        else:
            raise ValueError('Wrong type of rt_df')
        rt_df['cfg'] = rt_df['LC'] + ',' + rt_df['PI'] + ',' + rt_df['Seal']

        all_cfg = [
            MaterialConfiguration(*c.split(',')) for c in rt_df.cfg.unique()
        ]
        
        msg = ''
        
        for cfg in all_cfg:
            tmp_rt_df = rt_df[
                  (rt_df['LC']==cfg.lc) 
                & (rt_df['PI']==cfg.pi)
                & (rt_df['Seal']==cfg.seal)
            ]
            rt_fitting = RTFitting(cfg, tmp_rt_df)
            msg = rt_fitting.save(self.cleaned_data['exp_id'])

        if type(msg) == str:
            request.session["message"] = msg
        else:
            request.session["message"] =( 'Calculate '
                f'{self.cleaned_data["exp_id"]}'
                ' success.')
        request.session["exp_id"] = self.cleaned_data['exp_id']
        
class ConfigurationForm(forms.Form):
    ...
    
class ExperimentFrom(forms.Form):
    ...
    
class OpticalPhaseTwoForm(forms.Form):
    experiment = forms.ModelChoiceField(
        queryset=Experiment.objects.all().exclude(
            optfittingmodel=None
        )
    )
    
    reference = forms.ModelChoiceField(
        queryset=OpticalReference.objects.all(),
        required=False,
    )
    
    voltage = forms.FloatField(initial=5)
    
    def calc(self, request: HttpRequest):
        experiment: Experiment = self.cleaned_data['experiment']
        reference: OpticalReference = self.cleaned_data['reference']
        voltage: float = self.cleaned_data['voltage']
        # Calculate result
        opt_tr2_result = OptTableGenerator(experiment, voltage=voltage, reference=reference)
        opt_tr2_result.calc()
        # Save result to cookie
        result = {
            k: v.to_json() for
            k, v in opt_tr2_result.tables.items()
        }
        request.session['result'] = result
        
class AdvancedContrastRatioForm(forms.Form):
    experiment = forms.ModelChoiceField(
        queryset=Experiment.objects.all().exclude(
            optfittingmodel=None
        )
    )
    reference = forms.ModelChoiceField(
        queryset=OpticalReference.objects.all(),
        required=False,
    )
    back_light = forms.ModelChoiceField(
        queryset=BackLightUnit.objects.all(),
        required=False,
    )
    
    def calc(self, request: HttpRequest):
        experiment = self.cleaned_data['experiment']
        reference: Optional[OpticalReference] = self.cleaned_data['reference']
        # TODO
        back_light = self.cleaned_data['back_light']
        lcs = LiquidCrystal.objects.filter(
            optfittingmodel__experiment=experiment,
            # optfittingmodel__isnull=False
        ).exclude(ne_exps=None).exclude(no_exps=None)
        # Calculate result
        # Calculate Vop
        
        result = {
            'LC': [],
            'PI': [],
            'Seal': [],
            'ne R2': [],
            'no R2': [],
            'LC%': [],
            'Scatter Index': [],
            'CR Index': [],
            'CR Score': [],
        }
        
        if (reference is None) or (reference.lc not in lcs):
            vop = 5
        else:
            try:
                # If there is RTFiggingModel of ref LC, get
                # Vop from Tr and cell gap
                vop = RTFittingModel.objects.get(
                    lc=reference.lc,
                    experiment=self.cleaned_data['experiment'],
                ).voltage.predict(np.array([[
                    reference.time_rise,
                    reference.lc.designed_cell_gap,
                ]]))[0]
            except:
                vop = 5
        
        # Calculate Transmittance and set Parameter for CR Calculation
        lc_properties = {
            lc.name: LiquidCrystalPydantic(
                d=lc.designed_cell_gap,
                k11=lc.k_11,
                k22=lc.k_22,
                k33=lc.k_33,
                ne_exp=[(n.wavelength, n.value) for n in lc.ne_exps.all()],
                no_exp=[(n.wavelength, n.value) for n in lc.no_exps.all()],
            ) for lc in lcs
        }
        
        for model in OptFittingModel.objects.filter(
            experiment=experiment,
            lc__name__in=lc_properties.keys()
        ):
            result["LC"] += [model.lc.name]
            result["PI"] += [model.pi.name]
            result["Seal"] += [model.seal.name]
            result["ne R2"] += [lc_properties[model.lc.name].refraction_r2['ne']]
            result["no R2"] += [lc_properties[model.lc.name].refraction_r2['no']]
            result["LC%"] += [model.lc_percent.predict([
                [vop, model.lc.designed_cell_gap]
            ])[0]]
            result['Scatter Index'] += [
                lc_properties[model.lc.name].scatter
            ]
        
        result["CR Index"] = (
            np.array(result["LC%"]) / np.array(result["Scatter Index"]) * 10000
        )
        result["CR Score"] = tr2_score(
            result["CR Index"],
            method="min-max",
            formatter=lambda x: np.round(9*x) + 1,
        )
        result = pd.DataFrame(result)
        if (reference is not None) and (reference.lc in lcs):
            result["CR"] = (
                result["CR Index"]
                / result[result['LC']==reference.lc.name]['CR Index'][0]
                * reference.contrast_ratio
            )
        cache.set('result', result)
        
class BackLightUnitUploadForm(forms.Form):
    file = forms.FileField(
        widget=forms.FileInput(
            attrs={"accpet": ".xlsx"}
        )
    )
    name = forms.CharField(max_length=255)
    
    def save(self):
        file = self.cleaned_data['file']
        
        blu_intensity: list[BackLightIntensity] = []
        blu = BackLightUnit.objects.create(
            name=self.cleaned_data['name'],
        )
        for row in pd.read_excel(file).itertuples():
            blu_intensity.append(
                BackLightIntensity(
                    wavelength=row.wavelength,
                    value=row.value,
                    blu=blu,
                )
            )
            
        BackLightIntensity.objects.bulk_create(blu_intensity)
        cache.set('blu', blu)
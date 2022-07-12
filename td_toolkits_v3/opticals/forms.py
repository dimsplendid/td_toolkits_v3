import io
import csv
from datetime import datetime, timedelta, timezone
import pandas as pd

from django import forms
from django.http import HttpRequest

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
)
from .tools.utils import (
    OptLoader, 
    OptFitting, # TODO: to be deprecated
    OPTFitting,
    RTFitting,
    MaterialConfiguration,
    OptTableGenerator
)


class AxoUploadForm(forms.Form):

    exp_id = forms.ChoiceField(choices=("", ""), initial=None)
    factory = forms.ChoiceField(choices=("", ""), initial=None)

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

        for file in files:
            file_name = str(file).split(".")[0]
            short_names = [s.strip() for s in file_name.split("+")]

            reader = csv.reader(
                io.StringIO(file.read().decode("utf-8", errors="ignore"))
            )
            data_range = range(28, 28 + len(points) * len(short_names))
            data = [row for idx, row in enumerate(reader) if idx in data_range]
            row_count = 0
            for short_name in short_names:
                # print(short_name)
                # Check if there is chip data, otherwise skip.
                try:
                    chip = Chip.objects.get(
                        short_name=short_name, 
                        sub__condition__experiment=experiment
                    )
                except:
                    continue
                # print(chip)
                for point in points:
                    try:
                        AxometricsLog.objects.get(
                            chip=chip,
                            measure_point=point,
                        )
                        print(
                            f"{chip.name}({chip.short_name})"
                            + f" at point [{point}] is duplicate"
                        )
                        continue
                    except:
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


class RDLCellGapUploadForm(forms.Form):
    exp_id = forms.ChoiceField(choices=("", ""), initial=None)

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

        for row in rdl_cell_gap.to_numpy():
            # Check if there is chip data, otherwise skip.
            try:
                chip = Chip.objects.get(
                    short_name=row[0], 
                    sub__condition__experiment=experiment
                )
            except:
                continue

            RDLCellGap.objects.create(
                chip=chip, cell_gap=row[1], instrument=instrument
            )


class OptUploadForm(forms.Form):
    exp_id = forms.ChoiceField(choices=("", ""), initial=None)
    factory = forms.ChoiceField(choices=("", ""), initial=None)

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

        opt_df = pd.DataFrame()
        for file in files:
            # Using pd read csv this time
            tmp_df = pd.read_csv(
                file, encoding="utf-8", encoding_errors="ignore")
            opt_df = pd.concat([opt_df, tmp_df])

        if len(opt_df) == 0:
            return
        # print(opt_df.head())
        # 0. drop na for chip, date, time
        opt_df = opt_df.dropna(
            subset=[
                opt_df.columns[0],  # Date
                opt_df.columns[1],  # Time
                opt_df.columns[2],  # ID
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
        chip_could_log = [
            i.name
            for i in Chip.objects.filter(
                sub__condition__experiment=experiment, opticallog__isnull=True
            ).distinct()
        ]

        opt_df = opt_df[opt_df.iloc[:, 2].isin(chip_could_log)]

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
        instrument_id = Instrument.default(opt_df.iloc[0, 4], factory).id

        for chip_name in opt_df.iloc[:, 2].unique():
            chip_id = Chip.objects.get(
                name=chip_name, sub__condition__experiment=experiment
            ).id
            tmp_df = opt_df[opt_df.iloc[:, 2] == chip_name]
            if len(tmp_df) == 0:
                continue
            for row in tmp_df.to_numpy():
                logs.append(
                    OpticalLog(
                        chip_id=chip_id,
                        measure_point=row[3],
                        measure_time=row[-1],
                        instrument_id=instrument_id,
                        operator=row[5],
                        voltage=row[6],
                        lc_percent=row[11],
                        w_capital_y=row[23],
                        w_x=row[32],
                        w_y=row[33],
                    )
                )

        OpticalLog.objects.bulk_create(logs)


class ResponseTimeUploadForm(forms.Form):
    exp_id = forms.ChoiceField(choices=("", ""), initial=None)
    factory = forms.ChoiceField(choices=("", ""), initial=None)
    data_type = forms.ChoiceField(choices=(
            ('txt', 'Raw(.txt)'),
            ('xlsx', 'Excel(.xlsx)'),
        ),
        initial='txt'
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

        rt_df = []
        for file in files:
            print(file.name)
            if data_type == 'txt':
                if not file.name.endswith('txt'):
                    print(f'skip {file}')
                    continue
                tmp_df = pd.read_table(
                    file, encoding="utf-8", encoding_errors="ignore")
                rt_df.append(tmp_df)
            elif data_type == 'xlsx':
                if not file.name.endswith('xlsx'):
                    print(f'skip {file}')
                    continue
                tmp_df = pd.read_excel(file)
                rt_df.append(tmp_df)
            else:
                # raise ValueError('wrong data type')
                print('Something wrong, I should never touch this place.')
        rt_df = pd.concat(rt_df)

        # There are some row are the header, cause they just
        # merge the file directory.
        # Yea, I don't know why ether...
        unwanted_mask = rt_df.iloc[:, 7].astype("str").str.match("[ a-zA-Z]+")
        rt_df = rt_df[~unwanted_mask]
        if len(rt_df) == 0:
            return

        # modified types
        for col in [3, 7, 17, 19]:
            rt_df.iloc[:, col] = rt_df.iloc[:, col].astype("float")
        # operator should store in str
        rt_df.iloc[:, 5] = rt_df.iloc[:, 5].astype("str")

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
                datetime.combine(
                    rt_df.iloc[i, 0], 
                    rt_df.iloc[i, 1], 
                    tzinfo=timezone(timedelta(hours=8))
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
        chip_could_log = [
            i.name
            for i in Chip.objects.filter(
                sub__condition__experiment=experiment, 
                responsetimelog__isnull=True
            ).distinct()
        ]

        rt_df = rt_df[rt_df.iloc[:, 2].isin(chip_could_log)]
        logs = []
        instrument_id = Instrument.default(rt_df.iloc[0, 4], factory).id

        # 4. batch create for each chip
        for chip_name in rt_df.iloc[:, 2].unique():
            chip_id = Chip.objects.get(
                name=chip_name, sub__condition__experiment=experiment
            ).id
            tmp_df = rt_df[rt_df.iloc[:, 2] == chip_name]
            for row in tmp_df.to_numpy():
                logs.append(
                    ResponseTimeLog(
                        chip_id=chip_id,
                        measure_point=row[3],
                        measure_time=row[-1],
                        instrument_id=instrument_id,
                        operator=row[5],
                        voltage=row[7],
                        time_rise=row[17],
                        time_fall=row[19],
                    )
                )

        ResponseTimeLog.objects.bulk_create(logs)


class CalculateOpticalForm(forms.Form):
    exp_id = forms.ChoiceField(choices=("", ""), initial=None)
    cell_gap = forms.ChoiceField(
        choices=[('axo', 'AXO'), ('rdl', 'RDL')],
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
    
    exp_id = forms.ChoiceField(choices=("", ""), initial=None)
    cell_gap = forms.ChoiceField(
        choices=[('axo', 'AXO'), ('rdl', 'RDL')],
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
        raise('Method Not Implement')
    
class OptFittingForm(FittingBaseForm):
    
    def calculate(self, request):
        request.session["message"] = 'Error:'
        data_loader = OptLoader(
            self.cleaned_data['exp_id'],
            self.cleaned_data['cell_gap'],
        )

        opt_df = data_loader.opt
        opt_df['cfg'] = opt_df['LC'] + ',' + opt_df['PI'] + ',' + opt_df['Seal']

        all_cfg = [
            MaterialConfiguration(*c.split(',')) for c in opt_df.cfg.unique()
        ]
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
        rt_df['cfg'] = rt_df['LC'] + ',' + rt_df['PI'] + ',' + rt_df['Seal']

        all_cfg = [
            MaterialConfiguration(*c.split(',')) for c in rt_df.cfg.unique()
        ]
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
        queryset=Experiment.objects.filter(optfittingmodel=True)
    )
    
    reference = forms.ModelChoiceField(
        queryset=OpticalReference.objects.all(),
        required=False,
    )
    
    def calc(self, request: HttpRequest):
        experiment = self.cleaned_data['experiment']
        reference = self.cleaned_data['reference']
        # Calculate result
        opt_tr2_result = OptTableGenerator(experiment, reference=reference)
        opt_tr2_result.calc()
        # Save result to cookie
        result = {
            k: v.to_json() for
            k, v in opt_tr2_result.tables.items()
        }
        request.session['result'] = result
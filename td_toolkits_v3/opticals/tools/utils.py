from __future__ import annotations

from typing import NamedTuple

import numpy as np
import pandas as pd
import plotly.express as px
from plotly.offline import plot
import re
from scipy.interpolate import interp1d
from sklearn import linear_model
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import (
    StandardScaler,
    PolynomialFeatures,
    FunctionTransformer
)
from sklearn.pipeline import Pipeline

from td_toolkits_v3.materials.models import LiquidCrystal, Polyimide, Seal
from td_toolkits_v3.products.models import Experiment
from td_toolkits_v3.opticals.models import (
    AxometricsLog, 
    OpticalLog, 
    OpticalReference, 
    RDLCellGap,
    ResponseTimeLog,
    OpticalsFittingModel,
    OpticalSearchProfile,
    OptFittingModel,
    RTFittingModel,
)

class MaterialConfiguration(NamedTuple):
    lc: str
    pi: str
    seal: str

class CellGapRange(NamedTuple):
    min: float
    max: float

class OptLoader():
    
    def __init__(self, experiment_name: str, cell_gap='axo'):
        """
        Simple Loader to load needed data from database.
        experiment_name: str
            The experiment name to load.
        ref: (str, str), optional, default is None
            The setting of reference product, like ('T2', '6512')
            Should setting ref before using ref loader.
        cell_gap: str, optional, default is 'axo'
            The cell gap method for the opt and rt data.
            There are 'rdl' and 'axo' now.
            And if there are no cell gap data, using None.
        """
        self.experiment_name = experiment_name
        self.cell_gap = cell_gap
        
    def load_by_experiment(self, header, model):
        """
        aux function for loading
        """
        df = pd.DataFrame.from_records(
            model.objects
            .filter(chip__sub__condition__experiment__name=self.experiment_name)
            .values(*header)
        ).rename(
            columns=header
        )
        if len(df) == 0:
            return f'There is no {model.__name__} data in'\
                    + f'experiment {self.experiment_name}'
        return df

    @property
    def axo(self):
        header = {
            "chip__name": "ID",
            "measure_point": "Point",
            "cell_gap": "Cell Gap"
        }
        df = self.load_by_experiment(header, AxometricsLog)
        return df

    @property
    def rdl(self):
        header = {
            "chip__name": "ID",
            "cell_gap": "Cell Gap"
        }
        df = self.load_by_experiment(header, RDLCellGap)
        return df


    # load all need opt data
    @property
    def opt(self):
        """
        Loading Optical data, this would merge the cell gap so that we don't need
        to worry about it later.
        """
        # check parameter
        if self.cell_gap not in ['axo', 'rdl', None]:
            return f'The {self.cell_gap} method is not implement now.'

        # Setting the needed data, and the proper columns name for later use.
        header = {
            "chip__name": "ID",
            "chip__lc__name": "LC",
            "chip__pi__name": "PI",
            "chip__seal__name": "Seal",
            "measure_point": "Point",
            "voltage": "Vop",
            "lc_percent": "LC%",
            "w_x": "Wx",
            "w_y": "Wy",
            "w_capital_y": "WY",
        }
        # Query from database, and transform to pd.dataframe
        df = self.load_by_experiment(header, OpticalLog)
        # check is there opt data
        if type(df) == str:
            return df

        # no cell gap assignment, return raw directly
        if self.cell_gap is None:
            return df

        if self.cell_gap == 'axo':
            axo_df = self.axo
            if type(axo_df) == str:
                return axo_df
            df = pd.merge(df, axo_df, on=['ID', 'Point'], how='inner')
        else:
            rdl_df = self.rdl
            if type(rdl_df) == str:
                return rdl_df
            df = pd.merge(df, rdl_df, on='ID', how='inner')

        if len(df) == 0:
            return 'There are no suitable cell gap in OPT log, '\
                    + 'check the gap data again'

        # calculate T% by LC%
        def max_percent(arr):
            return 100 * arr / max(arr)
        df['T%'] = df.groupby(by=['ID', 'Point'])['LC%'].apply(max_percent)
        return df

    @property
    def rt(self):
        """
        Loading RT data, this would merge the cell_gap so that we don't need to 
        worry about that later.
        """
        # check parameter
        if self.cell_gap not in ['axo', 'rdl', None]:
            return f'The {self.cell_gap} method is not implement now.'

        # Setting the needed data, and the proper columns name for later use.
        header = {
            "chip__name": "ID",
            "chip__lc__name": "LC",
            "chip__pi__name": "PI",
            "chip__seal__name": "Seal",
            "measure_point": "Point",
            "voltage": "Vop",
            "time_rise": "Tr",
            "time_fall": "Tf",
        }
        # Query from database, and transform to pd.dataframe
        df = self.load_by_experiment(header, ResponseTimeLog)
        # check is there opt data
        if type(df) == str:
            return df

        # no cell gap assignment, return raw directly
        if self.cell_gap is None:
            return df

        if self.cell_gap == 'axo':
            axo_df = self.axo
            if type(axo_df) == str:
                return axo_df
            df = pd.merge(df, axo_df, on=['ID', 'Point'], how='inner')
        else:
            rdl_df = self.rdl
            if type(rdl_df) == str:
                return rdl_df
            df = pd.merge(df, rdl_df, on='ID', how='inner')

        if len(df) == 0:
            return 'There are no suitable cell gap in RT log, '\
                    + 'check the gap data again'
        df['RT'] = df['Tr'] + df['Tf']
        return df
    
    
    
class RefOptLoader():

    def __init__(self, ref=None):
        self.__ref = ref

    @property
    def ref(self):
        
        if self.__ref is None:
            print('Should set the (Factory, Product) first.')
            return
        
        factory_name = self.__ref[0]
        type_name = self.__ref[1]
        header = {
            "product_model_type__name": "Product",
            "product_model_type__factory__name": "Factory",
            "lc__name": "LC",
            "cell_gap": "Cell Gap",
            "transmittance": "T%",
            "time_rise": "Tr",
            "time_fall": "Tf",
            "gray_to_gray": "G2G",
            "w_x": "Wx",
            "w_y": "Wy",
            "contrast_ratio": "CR"
        }
        df = pd.DataFrame.from_records(
            OpticalReference.objects
            .filter(
                product_model_type__name=type_name, 
                product_model_type__factory__name=factory_name
            ).values(*header)
        ).rename(
            columns=header
        )
        
        if len(df) == 0:
            return f'There is no {type_name} reference, maybe you can build one.'
        
        return df

    @ref.setter
    def ref(self, ref_product):
        self.__ref = ref_product

class OPTFitting():
    def __init__(
        self,
        name: MaterialConfiguration,
        opt_df: pd.DataFrame, 
        opt_cutoff: int = 3, 
        random_state: int | None = None,
    ) -> None:
        """
        Parameters
        ----------
        name: MaterialConfiguration
            Using the (LC, PI, Seal) name for the identifier of all models.
        opt_df: Pandas.DataFrame
            Fields need contain ('Cell Gap', 'Vop', 'Wx', 'Wy', 'WY', 'T%', 'LC%')
        opt_cutoff: float, optional, default is 3
            Couse opt is variance at low Vop(maybe come from the detection limit)
            We need set a cut of.
        """
        self.name = name

        self.cell_gap_range = CellGapRange(
            opt_df['Cell Gap'].min(), 
            opt_df['Cell Gap'].max(),
        )
        
        self.opt_df = opt_df[opt_df['Vop'] > opt_cutoff]
        self.preprocess()
        
        self.opt_sets = {}
        self.opt_sets['train'], self.opt_sets['test'] = train_test_split(
            self.opt_df,
            test_size=0.1,
            random_state=random_state,
        )

        self.__opt_transformer = None
        self.__wx_model = None
        self.__wy_model = None
        self.__w_capital_y_model = None
        self.__lc_percent_model = None
        self.__transmittance_model = None
        self.__v_percent_model = None

        self.r2 = {}
        
    def preprocess(self):
        
        # 1. remove VT < 10% at 8V
        brokens = self.opt_df['ID'][
            (self.opt_df['Vop']==8)
          & (self.opt_df['LC%']<0.1)
        ].unique()
        
        self.opt_df = self.opt_df[~self.opt_df['ID'].isin(brokens)]

    def calc(self, models=None):
        """
        Calculate all model at once.

        Parameters
        ----------
        models: list[str]
            The list of the models' name
        """
        # get all models, the naming rule is ^([a-z]+_)+model$
        to_be_cal = [s for s in self.__dir__() 
            if re.search('^([a-z]+_)+model$', s)]
        if models is not None:
            to_be_cal = models
        
        for model in to_be_cal:
            # calculate and generate short-cut for predict
            setattr(self, model[:-6], getattr(self, model).predict)
        

    def save(self, experiment_name: str):
        try:
            OptFittingModel.objects.get(
                experiment__name=experiment_name,
                lc__name=self.name.lc,
                pi__name=self.name.pi,
                seal__name=self.name.seal,
            )
            return (
                'There is such model in log, please delete it first '
                'or try to update[TODO]'
            )

        except:
            # calculation first
            self.calc()
            # saving
            experiment = Experiment.objects.get(name=experiment_name)
            lc = LiquidCrystal.objects.get(name=self.name.lc)
            pi = Polyimide.objects.get(name=self.name.pi)
            seal = Seal.objects.get(name=self.name.seal)
            obj = OptFittingModel.objects.create(
                experiment=experiment,
                lc=lc,
                pi=pi,
                seal=seal,
                cell_gap_upper=self.cell_gap_range.max,
                cell_gap_lower=self.cell_gap_range.min,
                w_x=self.wx_model,
                w_y=self.wy_model,
                w_capital_y=self.w_capital_y_model,
                lc_percent=self.lc_percent_model,
                transmittance=self.transmittance_model,
                v_percent=self.v_percent_model,
                r2=self.r2,
            )
            return obj
   
    @staticmethod
    def _opt_transformer_f(x):
        new_x = np.empty(shape=(len(x), 7), dtype=float)
        new_x[:, 0] = 1
        new_x[:, 1] = x[:, 0]
        new_x[:, 2] = x[:, 1]
        new_x[:, 3] = x[:, 0] * x[:, 1]
        new_x[:, 4] = x[:, 0] ** 2
        new_x[:, 5] = x[:, 0] ** 3
        new_x[:, 6] = x[:, 0] ** 4
        return new_x

    @property
    def opt_transformer(self):
        """
        custom opt transform function
        [x0, x1] = [Vop, Cell Gpa]
        [x0, x1] |-> [1, x0, x1, x0*x1, x0**2, x0**3, x0**4]
        """
        if self.__opt_transformer is not None:
            return self.__opt_transformer

        transformer = FunctionTransformer(self._opt_transformer_f)
        self.__opt_transformer = transformer
        return transformer

    def __opt_model(self, y_label, transformer=None):
        """
        generate a model for optical fitting
        data -> Scalar -> Transform(expand features) -> Linear Regression
        """
        if transformer is None:
            transformer = PolynomialFeatures(degree=2)
        model = Pipeline([
            ('Scalar', StandardScaler()),
            ('Custom Transform', transformer),
            ('Linear', linear_model.TheilSenRegressor(fit_intercept=False))
        ])
        x_train = self.opt_sets['train'][['Vop', 'Cell Gap']].to_numpy()
        y_train = self.opt_sets['train'][y_label].to_numpy()
        x_test = self.opt_sets['test'][['Vop', 'Cell Gap']].to_numpy()
        y_test = self.opt_sets['test'][y_label].to_numpy()
        model.fit(x_train, y_train)
        r2_score = model.score(x_test, y_test)
        return model, r2_score

    @property
    def wx_model(self):
        """
        f(Vop, Cell Gap) |-> Wx
        """
        if self.__wx_model is not None:
            return self.__wx_model
        
        self.__wx_model, r2_score = self.__opt_model('Wx')
        self.r2['f(Vop, Cell Gap) |-> Wx'] = r2_score
        return self.__wx_model

    @property
    def wy_model(self):
        """
        f(Vop, Cell Gap) |-> Wy
        """
        if self.__wy_model is not None:
            return self.__wy_model

        self.__wy_model, r2_score = self.__opt_model('Wy')
        self.r2['f(Vop, Cell Gap) |-> Wy'] = r2_score
        return self.__wy_model
    
    @property
    def w_capital_y_model(self):
        """
        f(Vop, Cell Gap) |-> WY
        """
        if self.__w_capital_y_model is None:
            self.__w_capital_y_model, r2_score = self.__opt_model('WY')
            self.r2['f(Vop, Cell Gap) |-> WY'] = r2_score
        
        return self.__w_capital_y_model

    @property
    def lc_percent_model(self):
        """
        f(Vop, Cell Gap) |-> LC%
        """
        if self.__lc_percent_model is not None:
            return self.__lc_percent_model

        self.__lc_percent_model, r2_score = self.__opt_model(
            'LC%', self.opt_transformer)
        self.r2['f(Vop, Cell Gap) |-> LC%'] = r2_score
        return self.__lc_percent_model
    
    @property
    def transmittance_model(self):
        """
        f(Vop, Cell Gap) |-> T%
        """
        if self.__transmittance_model is not None:
            return self.__transmittance_model

        self.__transmittance_model, r2_score = self.__opt_model(
            'T%', self.opt_transformer)
        self.r2['f(Vop, Cell Gap) |-> T%'] = r2_score
        return self.__transmittance_model

    @staticmethod
    def _v_percent_model_tranformer_f(x):
        """
        [x0, x1] = [T%, Cell Gap]
        [x0, x1] |-> [1, x1, exp(x0+10)]
        """
        new_x = np.empty(shape=(len(x), 3), dtype=float)
        new_x[:, 0] = 1
        new_x[:, 1] = x[:, 1]
        new_x[:, 2] = np.exp(x[:, 0]+10)

        return new_x
    
    @property
    def v_percent_model(self):
        """
        f(T%, Cell Gap) |-> Vop
        """
        if self.__v_percent_model is not None:
            return self.__v_percent_model

        # 1. should cut of T% after 100, make f(T%) is a funciton
        opt_df = self.opt_df.copy()
        opt_cut_off_df = []
        for id in opt_df['ID'].unique():
            tmp_df_1 = opt_df[opt_df['ID']==id]
            for point in tmp_df_1['Point'].unique():
                tmp_df_2 = tmp_df_1[tmp_df_1['Point']==point]
                tmp_df_2 = tmp_df_2.iloc[:tmp_df_2['T%'].argmax(),:]
                opt_cut_off_df.append(tmp_df_2)
        opt_cut_off_df = pd.concat(opt_cut_off_df)
        # 2. And we usually inteterstin in the higer T% region
        #    Select 85% for now.
        opt_cut_off_df = opt_cut_off_df[opt_cut_off_df['T%']>85]

        train, test = train_test_split(opt_cut_off_df, test_size=0.1)
        x_train = train[["T%", "Cell Gap"]].to_numpy()
        y_train = train['Vop'].to_numpy()
        x_test = test[['T%', 'Cell Gap']].to_numpy()
        y_test = test['Vop'].to_numpy()

        # 3. Using pipeline the special transformer
        
        model = Pipeline([
            ('Scalar', StandardScaler()),
            ('Custom Transform', FunctionTransformer(
                self._v_percent_model_tranformer_f)),
            ('Linear', linear_model.TheilSenRegressor(fit_intercept=False))
        ])
        model.fit(x_train, y_train)
        self.__v_percent_model = model
        self.r2['f(T%, Cell Gap) |-> Vop'] = model.score(x_test, y_test)
        return model

class RTFitting():
    def __init__(
        self, 
        name: MaterialConfiguration, 
        rt_df: pd.DataFrame, 
        random_state: int | None = None,
    ):
        """
        Parameters
        ----------
        name: str
            Using the LC name for the identifier of all models.
        rt_df: pandas.DataFrame
            Fields need contain ('Cell Gap', 'Vop', 'RT', 'Tr', 'Tf')
        """
        self.name = name
        self.rt_df = rt_df
        self.preprocess()

        self.cell_gap_range = CellGapRange(
            rt_df['Cell Gap'].min(), 
            rt_df['Cell Gap'].max(),
        )
        
        self.rt_sets = {}
        self.rt_sets['train'], self.rt_sets['test'] = train_test_split(
            self.rt_df,
            test_size=0.1,
            random_state=random_state,
        )

        self.__voltage_model = None

        self.__rt_transformer = None
        self.__response_time_model = None
        self.__time_rise_model = None
        self.__time_fall_model = None

        self.r2 = {}
        
    def preprocess(self):
        
        # 1. remove VT < 10% at 8V
        brokens = self.rt_df['ID'][
            (self.rt_df['RT']>150)
          | (self.rt_df['RT']<0)
        ].unique()
        
        self.rt_df = self.rt_df[~self.rt_df['ID'].isin(brokens)]

    def calc(self, models=None):
        """
        Calculate all model at once.

        Parameters
        ----------
        models: list[str]
            The list of the models' name
        """
        # get all models, the naming rule is ^([a-z]+_)+model$
        to_be_cal = [s for s in self.__dir__() 
            if re.search('^([a-z]+_)+model$', s)]
        if models is not None:
            to_be_cal = models
        
        for model in to_be_cal:
            # calculate and generate short-cut for predict
            setattr(self, model[:-6], getattr(self, model).predict)
        

    def save(self, experiment_name: str):
        try:
            RTFittingModel.objects.get(
                experiment__name=experiment_name,
                lc__name=self.name.lc,
                pi__name=self.name.pi,
                seal__name=self.name.seal,
            )
            return 'There is such model in log, please delete it first' \
                 + ' or try to update[TODO]'

        except:
            # calculation first
            self.calc()
            # saving
            experiment = Experiment.objects.get(name=experiment_name)
            lc = LiquidCrystal.objects.get(name=self.name.lc)
            pi = Polyimide.objects.get(name=self.name.pi)
            seal = Seal.objects.get(name=self.name.seal)
            obj = RTFittingModel.objects.create(
                experiment=experiment,
                lc=lc,
                pi=pi,
                seal=seal,
                cell_gap_upper=self.cell_gap_range.max,
                cell_gap_lower=self.cell_gap_range.min,
                voltage=self.voltage_model,
                response_time=self.response_time_model,
                time_rise=self.time_rise_model,
                time_fall=self.time_fall_model,
                r2=self.r2,
            )
            return obj
    @property
    def voltage_model(self):
        """
        f(Tr, cell gap) |-> Vop
        """
        if self.__voltage_model is not None:
            return self.__voltage_model

        model = Pipeline([
            ('Scalar', StandardScaler()),
            ('Poly', PolynomialFeatures(degree=2)),
            ('Linear', linear_model.LinearRegression(fit_intercept=False))
        ])
        x_train = self.rt_sets['train'][['Tr', 'Cell Gap']].to_numpy()
        y_train = self.rt_sets['train']['Vop'].to_numpy()
        x_test = self.rt_sets['test'][['Tr', 'Cell Gap']].to_numpy()
        y_test = self.rt_sets['test']['Vop'].to_numpy()
        model.fit(x_train, y_train)
        self.__voltage_model = model
        self.r2['f(Tr, Cell Gap) |-> Vop'] = model.score(x_test, y_test)
        return model

    @staticmethod
    def _rt_transformer_f(x):
        new_x = np.empty(shape=(len(x), 5), dtype=float)
        new_x[:, 0] = 1
        new_x[:, 1] = x[:, 0]
        new_x[:, 2] = x[:, 1]
        new_x[:, 3] = x[:, 0] * x[:, 1]
        new_x[:, 4] = x[:, 0] ** 2
        return new_x

    @property
    def rt_transformer(self):
        """
        custom rt transform function
        [x0, x1] = [Vop, Cell Gap]
        [x0, x1] |-> [1, x0, x1, x0*x1, x0**2]
        """
        if self.__rt_transformer is not None:
            return self.__rt_transformer

        transformer = FunctionTransformer(self._rt_transformer_f)
        self.__rt_transformer = transformer
        return transformer

    def __rt_model(self, y_label):
        model = Pipeline([
            ('Scalar', StandardScaler()),
            ('Custom Transform', self.rt_transformer),
            ('Linear', linear_model.TheilSenRegressor(fit_intercept=False))
        ])
        x_train = self.rt_sets['train'][['Vop', 'Cell Gap']].to_numpy()
        y_train = self.rt_sets['train'][y_label].to_numpy()
        x_test = self.rt_sets['test'][['Vop', 'Cell Gap']].to_numpy()
        y_test = self.rt_sets['test'][y_label].to_numpy()
        model.fit(x_train, y_train)
        r2_score = model.score(x_test, y_test)
        return model, r2_score

    @property
    def response_time_model(self):
        """
        f(Vop, Cell Gap) |-> RT
        """
        if self.__response_time_model is not None:
            return self.__response_time_model
        
        self.__response_time_model, r2_score = self.__rt_model('RT')
        self.r2['f(Vop, Cell Gap) |-> RT'] = r2_score
        return self.__response_time_model

    @property
    def time_rise_model(self):
        """
        f(Vop, Cell Gap) |-> Tr
        """
        if self.__time_rise_model is not None:
            return self.__time_rise_model
        
        self.__time_rise_model, r2_score = self.__rt_model('Tr')
        self.r2['f(Vop, Cell Gap) |-> Tr'] = r2_score
        return self.__time_rise_model

    @property
    def time_fall_model(self):
        """
        f(Cell Gap) |-> Tf
        """
        if self.__time_fall_model is not None:
            return self.__time_fall_model

        self.__time_fall_model = Pipeline([
            ('Scalar', StandardScaler()),
            ('Linear', linear_model.TheilSenRegressor())
        ])
        
        x_train = self.rt_sets['train'][['Cell Gap']].to_numpy()
        y_train = self.rt_sets['train']['Tf'].to_numpy()
        x_test = self.rt_sets['test'][['Cell Gap']].to_numpy()
        y_test = self.rt_sets['test']['Tf'].to_numpy()
        self.__time_fall_model.fit(x_train, y_train)
        r2_score = self.__time_fall_model.score(x_test, y_test)
        
        self.r2['f(Cell Gap) |-> Tf'] = r2_score
        return self.__time_fall_model

    
class OptFitting():
    # TODO: deprecate and transfer to OPTFitting & RTFitting
    def __init__(self, name, rt_df, opt_df, opt_cutoff=3, random_state=None):
        """
        Parameters
        ----------
        name: str
            Using the LC name for the identifier of all models.
        rt_df: pandas.DataFrame
            Fields need contain ('Cell Gap', 'Vop', 'RT', 'Tr', 'Tf')
        opt_df: Pandas.DataFrame
            Fields need contain ('Cell Gap', 'Vop', 'Wx', 'Wy', 'WY', 'T%', 'LC%')
        opt_cutoff: float, optional, default is 3
            Couse opt is variance at low Vop(maybe come from the detection limit)
            We need set a cut of.
        """
        self.name = name
        self.rt_df = rt_df

        self.cell_gap_range = (rt_df['Cell Gap'].min(), rt_df['Cell Gap'].max())
        
        self.rt_sets = {}
        self.rt_sets['train'], self.rt_sets['test'] = train_test_split(
            self.rt_df,
            test_size=0.1,
            random_state=random_state
        )

        self.opt_df = opt_df[opt_df['Vop'] > opt_cutoff]
        
        self.opt_sets = {}
        self.opt_sets['train'], self.opt_sets['test'] = train_test_split(
            self.opt_df,
            test_size=0.1,
            random_state=random_state
        )

        self.__voltage_model = None

        self.__rt_transformer = None
        self.__response_time_model = None
        self.__time_rise_model = None
        self.__time_fall_model = None

        self.__opt_transformer = None
        self.__wx_model = None
        self.__wy_model = None
        self.__w_capital_y_model = None
        self.__lc_percent_model = None
        self.__transmittance_model = None
        self.__v_percent_model = None

        self.r2 = {}

    def calc(self, models=None):
        """
        Calculate all model at once.

        Parameters
        ----------
        models: list[str]
            The list of the models' name
        """
        # get all models, the naming rule is ^([a-z]+_)+model$
        to_be_cal = [s for s in self.__dir__() 
            if re.search('^([a-z]+_)+model$', s)]
        if models is not None:
            to_be_cal = models
        
        for model in to_be_cal:
            # calculate and generate short-cut for predict
            setattr(self, model[:-6], getattr(self, model).predict)
        

    def save(self, lc_name, experiment_name):
        try:
            OpticalsFittingModel.objects.get(
                experiment__name=experiment_name,
                lc__name=lc_name,
            )
            return 'There is such model in log, please delete it first' \
                 + ' or try to update[TODO]'

        except:
            # calculation first
            self.calc()
            # saving
            experiment = Experiment.objects.get(name=experiment_name)
            lc = LiquidCrystal.objects.get(name=lc_name)
            obj = OpticalsFittingModel.objects.create(
                experiment=experiment,
                lc=lc,
                cell_gap_upper=self.cell_gap_range[1],
                cell_gap_lower=self.cell_gap_range[0],
                voltage=self.voltage_model,
                response_time=self.response_time_model,
                time_rise=self.time_rise_model,
                time_fall=self.time_fall_model,
                w_x=self.wx_model,
                w_y=self.wy_model,
                w_capital_y=self.w_capital_y_model,
                lc_percent=self.lc_percent_model,
                transmittance=self.transmittance_model,
                v_percent=self.v_percent_model,
                r2=self.r2,
            )
            return obj
    @property
    def voltage_model(self):
        """
        f(Tr, cell gap) |-> Vop
        """
        if self.__voltage_model is not None:
            return self.__voltage_model

        model = Pipeline([
            ('Scalar', StandardScaler()),
            ('Poly', PolynomialFeatures(degree=2)),
            ('Linear', linear_model.LinearRegression(fit_intercept=False))
        ])
        x_train = self.rt_sets['train'][['Tr', 'Cell Gap']].to_numpy()
        y_train = self.rt_sets['train']['Vop'].to_numpy()
        x_test = self.rt_sets['test'][['Tr', 'Cell Gap']].to_numpy()
        y_test = self.rt_sets['test']['Vop'].to_numpy()
        model.fit(x_train, y_train)
        self.__voltage_model = model
        self.r2['f(Tr, Cell Gap) |-> Vop'] = model.score(x_test, y_test)
        return model

    @staticmethod
    def _rt_transformer_f(x):
        new_x = np.empty(shape=(len(x), 5), dtype=float)
        new_x[:, 0] = 1
        new_x[:, 1] = x[:, 0]
        new_x[:, 2] = x[:, 1]
        new_x[:, 3] = x[:, 0] * x[:, 1]
        new_x[:, 4] = x[:, 0] ** 2
        return new_x

    @property
    def rt_transformer(self):
        """
        custom rt transform function
        [x0, x1] = [Vop, Cell Gap]
        [x0, x1] |-> [1, x0, x1, x0*x1, x0**2]
        """
        if self.__rt_transformer is not None:
            return self.__rt_transformer

        transformer = FunctionTransformer(self._rt_transformer_f)
        self.__rt_transformer = transformer
        return transformer

    def __rt_model(self, y_label):
        model = Pipeline([
            ('Scalar', StandardScaler()),
            ('Custom Transform', self.rt_transformer),
            ('Linear', linear_model.TheilSenRegressor(fit_intercept=False))
        ])
        x_train = self.rt_sets['train'][['Vop', 'Cell Gap']].to_numpy()
        y_train = self.rt_sets['train'][y_label].to_numpy()
        x_test = self.rt_sets['test'][['Vop', 'Cell Gap']].to_numpy()
        y_test = self.rt_sets['test'][y_label].to_numpy()
        model.fit(x_train, y_train)
        r2_score = model.score(x_test, y_test)
        return model, r2_score

    @property
    def response_time_model(self):
        """
        f(Vop, Cell Gap) |-> RT
        """
        if self.__response_time_model is not None:
            return self.__response_time_model
        
        self.__response_time_model, r2_score = self.__rt_model('RT')
        self.r2['f(Vop, Cell Gap) |-> RT'] = r2_score
        return self.__response_time_model

    @property
    def time_rise_model(self):
        """
        f(Vop, Cell Gap) |-> Tr
        """
        if self.__time_rise_model is not None:
            return self.__time_rise_model
        
        self.__time_rise_model, r2_score = self.__rt_model('Tr')
        self.r2['f(Vop, Cell Gap) |-> Tr'] = r2_score
        return self.__time_rise_model

    @property
    def time_fall_model(self):
        """
        f(Vop, Cell Gap) |-> Tf
        """
        if self.__time_fall_model is not None:
            return self.__time_fall_model

        self.__time_fall_model, r2_score = self.__rt_model('Tf')
        self.r2['f(Vop, Cell Gap) |-> Tf'] = r2_score
        return self.__time_fall_model

    @staticmethod
    def _opt_transformer_f(x):
        new_x = np.empty(shape=(len(x), 7), dtype=float)
        new_x[:, 0] = 1
        new_x[:, 1] = x[:, 0]
        new_x[:, 2] = x[:, 1]
        new_x[:, 3] = x[:, 0] * x[:, 1]
        new_x[:, 4] = x[:, 0] ** 2
        new_x[:, 5] = x[:, 0] ** 3
        new_x[:, 6] = x[:, 0] ** 4
        return new_x

    
    @property
    def opt_transformer(self):
        """
        custom opt transform function
        [x0, x1] = [Vop, Cell Gpa]
        [x0, x1] |-> [1, x0, x1, x0*x1, x0**2, x0**3, x0**4]
        """
        if self.__opt_transformer is not None:
            return self.__opt_transformer

        transformer = FunctionTransformer(self._opt_transformer_f)
        self.__opt_transformer = transformer
        return transformer

    def __opt_model(self, y_label, transformer=None):
        """
        generate a model for optical fitting
        data -> Scalar -> Transform(expand features) -> Linear Regression
        """
        if transformer is None:
            transformer = PolynomialFeatures(degree=2)
        model = Pipeline([
            ('Scalar', StandardScaler()),
            ('Custom Transform', transformer),
            ('Linear', linear_model.TheilSenRegressor(fit_intercept=False))
        ])
        x_train = self.opt_sets['train'][['Vop', 'Cell Gap']].to_numpy()
        y_train = self.opt_sets['train'][y_label].to_numpy()
        x_test = self.opt_sets['test'][['Vop', 'Cell Gap']].to_numpy()
        y_test = self.opt_sets['test'][y_label].to_numpy()
        model.fit(x_train, y_train)
        r2_score = model.score(x_test, y_test)
        return model, r2_score

    @property
    def wx_model(self):
        """
        f(Vop, Cell Gap) |-> Wx
        """
        if self.__wx_model is not None:
            return self.__wx_model
        
        self.__wx_model, r2_score = self.__opt_model('Wx')
        self.r2['f(Vop, Cell Gap) |-> Wx'] = r2_score
        return self.__wx_model

    @property
    def wy_model(self):
        """
        f(Vop, Cell Gap) |-> Wy
        """
        if self.__wy_model is not None:
            return self.__wy_model

        self.__wy_model, r2_score = self.__opt_model('Wy')
        self.r2['f(Vop, Cell Gap) |-> Wy'] = r2_score
        return self.__wy_model
    
    @property
    def w_capital_y_model(self):
        """
        f(Vop, Cell Gap) |-> WY
        """
        if self.__w_capital_y_model is None:
            self.__w_capital_y_model, r2_score = self.__opt_model('WY')
            self.r2['f(Vop, Cell Gap) |-> WY'] = r2_score
        
        return self.__w_capital_y_model

    @property
    def lc_percent_model(self):
        """
        f(Vop, Cell Gap) |-> LC%
        """
        if self.__lc_percent_model is not None:
            return self.__lc_percent_model

        self.__lc_percent_model, r2_score = self.__opt_model(
            'LC%', self.opt_transformer)
        self.r2['f(Vop, Cell Gap) |-> LC%'] = r2_score
        return self.__lc_percent_model
    
    @property
    def transmittance_model(self):
        """
        f(Vop, Cell Gap) |-> T%
        """
        if self.__transmittance_model is not None:
            return self.__transmittance_model

        self.__transmittance_model, r2_score = self.__opt_model(
            'T%', self.opt_transformer)
        self.r2['f(Vop, Cell Gap) |-> T%'] = r2_score
        return self.__transmittance_model

    @staticmethod
    def _v_percent_model_tranformer_f(x):
        """
        [x0, x1] = [T%, Cell Gap]
        [x0, x1] |-> [1, x1, exp(x0+10)]
        """
        new_x = np.empty(shape=(len(x), 3), dtype=float)
        new_x[:, 0] = 1
        new_x[:, 1] = x[:, 1]
        new_x[:, 2] = np.exp(x[:, 0]+10)

        return new_x
    
    @property
    def v_percent_model(self):
        """
        f(T%, Cell Gap) |-> Vop
        """
        if self.__v_percent_model is not None:
            return self.__v_percent_model

        # 1. should cut of T% after 100, make f(T%) is a funciton
        opt_df = self.opt_df.copy()
        opt_cut_off_df = []
        for id in opt_df['ID'].unique():
            tmp_df_1 = opt_df[opt_df['ID']==id]
            for point in tmp_df_1['Point'].unique():
                tmp_df_2 = tmp_df_1[tmp_df_1['Point']==point]
                tmp_df_2 = tmp_df_2.iloc[:tmp_df_2['T%'].argmax(),:]
                opt_cut_off_df.append(tmp_df_2)
        opt_cut_off_df = pd.concat(opt_cut_off_df)
        # 2. And we usually inteterstin in the higer T% region
        #    Select 85% for now.
        opt_cut_off_df = opt_cut_off_df[opt_cut_off_df['T%']>85]

        train, test = train_test_split(opt_cut_off_df, test_size=0.1)
        x_train = train[["T%", "Cell Gap"]].to_numpy()
        y_train = train['Vop'].to_numpy()
        x_test = test[['T%', 'Cell Gap']].to_numpy()
        y_test = test['Vop'].to_numpy()

        # 3. Using pipeline the special transformer
        
        model = Pipeline([
            ('Scalar', StandardScaler()),
            ('Custom Transform', FunctionTransformer(
                self._v_percent_model_tranformer_f)),
            ('Linear', linear_model.TheilSenRegressor(fit_intercept=False))
        ])
        model.fit(x_train, y_train)
        self.__v_percent_model = model
        self.r2['f(T%, Cell Gap) |-> Vop'] = model.score(x_test, y_test)
        return model


class OptResultGenerator():
    # TODO: to be deprecated
    # Need separate this function either
    def __init__(self, lc:str, ref:tuple):
        """
        loading the newest optical model of lc, 
        and calculate some differece base on reference
        lc: str
            The name of liquid crystal, need add first
        ref: tuple(str, str)
            The ref product, encoding in (Factory, Product) like ('T2', '6512')
        """
        self.lc = LiquidCrystal.objects.get(name=lc)
        # TODO: Need re-consider what's the better way to construct result
        self.models = OpticalsFittingModel.objects.filter(
            lc__name=lc
        ).latest('created')
        self.range = (self.models.cell_gap_lower, self.models.cell_gap_upper)
        self.ref_data = RefOptLoader(ref).ref.to_dict('records')[0]
        self.__ref = None

    @property
    def ref(self):
        """
        Generate ref data
        
        Return
        ------
        ref: dict
        """
        if self.__ref is None:
            # add origin data to ref
            self.__ref = self.ref_data
            # get some fitting property of ref
            ref_models = OpticalsFittingModel.objects.filter(
                lc__name=self.ref_data['LC']
            ).latest('created')
            x = [[self.__ref['Tr'], self.__ref['Cell Gap']]]
            # calculate ref vop by the voltage model
            self.__ref['Vop'] = ref_models.voltage.predict(x)[0]
            # CR index to calculate relate CR
            # deduction:
            # CR = (W/W_ref)/(D/D_ref) * CR_ref
            #    = W/D / (W_ref/D_ref) * CR_ref
            #    = W/D * (scatter_index * cell_gap) / T_ref * CR
            #    = W/D * CR_index
            # TODO: maybe use the LC% make more sense?
            x = [[self.__ref['Vop'], self.__ref['Cell Gap']]]
            self.__ref['CR index'] = self.__ref['CR'] \
                                   / float(ref_models.lc_percent.predict(x)) \
                                   * self.__ref['Cell Gap'] \
                                   * LiquidCrystal.objects.get(
                                       name=self.__ref['LC']).scatter_index
            self.__ref['Cell Gap range'] = np.arange(
                round(self.__ref['Cell Gap'])-0.6, # get one more for diff
                round(self.__ref['Cell Gap'])+0.5,
                0.1,
            )

        return self.__ref
    
    @property
    def table(self):
        """
        Generate the table for require ref LC
        TODO: add the choice of V%?
        """
        table ={}
        ref_d = self.ref['Cell Gap']
        target_d = self.ref['Cell Gap range']
        v = self.ref['Vop']
        predict_region = np.array([[v] * len(target_d), target_d]).T

        table['LC'] = self.lc.name
        table['V90'] = self.models.v_percent.predict([[90, ref_d]])[0]
        table['V95'] = self.models.v_percent.predict([[95, ref_d]])[0]
        table['V99'] = self.models.v_percent.predict([[99, ref_d]])[0]
        table['Vop'] = self.ref['Vop']
        table['Cell Gap'] = target_d
        table['Δnd'] = target_d * self.lc.delta_n
        
        # RT part
        table['RT'] = self.models.response_time.predict(predict_region)
        table['Tr'] = self.models.time_rise.predict(predict_region)
        table['Tf'] = self.models.time_fall.predict(predict_region)
        table['G2G'] = self.ref['G2G'] * table['RT'] \
                        / (self.ref['Tr']+self.ref['Tf'])
        # Opt Part
        table['Wx'] = self.models.w_x.predict(predict_region)
        table['ΔWx'] = table['Wx'] - self.ref['Wx']
        table['Wy'] = self.models.w_y.predict(predict_region)
        table['ΔWy'] = table['Wy'] - self.ref['Wy']
        table['WY'] = self.models.w_capital_y.predict(predict_region)
        table['WX'] = table['Wx'] * table['WY'] / table['Wy']
        table['WZ'] = (1-table['Wx']-table['Wy']) * table['WY'] / table['Wy']
        table['T%'] = self.models.transmittance.predict(predict_region)
        table['LC%'] = self.models.lc_percent.predict(predict_region)

        # Eab part
        f_x = self.f(table['WX'], 'Xn')
        f_y = self.f(table['WY'], 'Yn')
        f_z = self.f(table['WZ'], 'Zn')
        table['a*'] = 500 * (f_x-f_y)
        table['b*'] = 200 * (f_y-f_z)
        table['L*'] = 116 * f_y - 16
        table["u'"] = 4 * table['Wx'] / (-2*table['Wx'] + 12*table['Wy'] + 3)
        table["v'"] = 9 * table['Wy'] / (-2*table['Wx'] + 12*table['Wy'] + 3)
        # prepend 0 to keep the length the same, eleminate after tablize
        table['Δa*'] = np.diff(table['a*'], prepend=0)
        table['Δb*'] = np.diff(table['b*'], prepend=0)
        table['ΔL*'] = np.diff(table['L*'], prepend=0)
        # Euclidean distance is the same with L2 norm
        # so numpy.linalg.norm() can get the distance between columns
        # see https://numpy.org/doc/stable/reference/generated/numpy.linalg.norm.html
        table['ΔEab*'] = np.linalg.norm(
            [table['Δa*'], table['Δb*'], table['ΔL*']], 
            axis=0,
        )
        table["Δu'"] = np.diff(table["u'"], prepend=0)
        table["Δv'"] = np.diff(table["v'"], prepend=0)
        table["Δu'v'"] = np.linalg.norm([table["Δu'"], table["Δv'"]], axis=0)

        # CR part
        table['D'] = self.lc.scatter_index * table['Cell Gap']
        table['W'] = table['LC%']
        table['CR'] = table['W']/table['D'] * self.ref['CR index']
        table['ΔCR'] = table['CR'] - self.ref['CR']

        table['Remark'] = ['Interpolation' \
                            if (d > self.range[0] and d < self.range[1]) \
                            else 'Extrapolation' \
                            for d in target_d]
        
        # eliminate the redundant 0-th row, which for calculate diff.
        return pd.DataFrame(table)[1:] 

    @property
    def vt_curve(self):
        """
        generate V-T curve at 3 to 10
        """
        # gennerate a grid from Vop and cell gap range
        v = np.arange(3, 10, 0.1)
        v, d = np.meshgrid(v, self.ref['Cell Gap range'])
        x = list(zip(v.flatten(), d.flatten()))
        t = self.models.transmittance.predict(x)
        df = pd.DataFrame({
            'LC': self.models.lc.name,
            'Cell Gap': d.flatten(),
            'Vop': v.flatten(),
            'T%': t
        })
        return df

    @staticmethod
    def f(x, opt):
        """
        Aux fuction for calculating Eab
        """
        blu = {
            'Xn': 95.04,
            'Yn': 100.,
            'Zn': 108.86
        }
        x_over_blu = x/blu[opt]
        return np.where(
            x_over_blu < 0.008856,
            7.787 * x/blu[opt] + 16/116,
            (x/blu[opt]) ** (1/3)
        )

def tr2_score(column, method='mean', cmp='gt', scale=1., formatter=None):
    """
    Calculate the score base on the data.
    Parameters
    ----------
    column: numpy.array
    method: str, optional, default 'mean'
        'mean': Mean Normalization: score = (x - mean) / stdev
        'min-max': Min-Max Normalization: score = (x - min) / (max - min)
    cmp: str, optional, default 'gt'
        'gt': larger the better
        'lt': smaller the better
    scale: float, optional, default 1
        Scale the score by multiply.
        Scale would after formatter.
    formatter: one parameter function, optional, default None
        Modified final score, like round to integer
    Returns
    -------
    numpy.array
    """
    if method == 'mean':
        # Mean Normalization
        stdev = column.std()
        mean = column.mean()
        if stdev == 0:
            score = np.zeros(len(column))
        else:
            score = (column - mean) / stdev
        if cmp == 'lt':
            score = -score

    if method == 'min-max':
        # Min-Max Normalization
        min = column.min()
        max = column.max()
        if min == max:
            score = np.array([0.5] * len(column))
        else:
            if cmp == 'gt':
                score = (column - min) / (max - min)
            else:
                score = (max - column) / (max - min)

    if formatter:
        score = formatter(score)
    
    score *= scale

    return score

class OptictalsScore():

    def __init__(self, data, profile):
        """
        Parameters
        ----------
        data: pandas.DataFrame
            The result of the Optical Search
        profile: pandas.DataFrame
            The setting of limits. Only using first row
        """
        self.data = data[['LC', 'Cell Gap', 'LC%', 'ΔEab*', 'RT', 'CR', 'Remark']]
        header = {
            'name': 'LC',
            'designed_cell_gap': 'Designed Cell Gap'
        }
        designed_cell_gap = pd.DataFrame.from_records(
            LiquidCrystal.objects.filter(
                name__in = self.data['LC'].unique()
            ).values(
                *header
            )
        ).rename(columns=header)
        self.data = pd.merge(self.data, designed_cell_gap, on='LC', how='left')
        # print(self.data)
        self.constraint = profile.to_dict(orient='records')[0]
        mask = (
            (self.data['LC%']    >  self.constraint['LC%'])
            & (self.data['ΔEab*']  <  self.constraint['ΔEab*'])
            & (self.data['RT']     <  self.constraint['RT'])
            & (self.data['CR']     >  self.constraint['CR'])
            &  (np.abs(self.data['Cell Gap']-self.data['Designed Cell Gap']) < 0.001)
        )
        if self.constraint['Remark'] != OpticalSearchProfile.RemarkChoice.ALL:
            mask = mask & (self.data['Remark'] == self.constraint['Remark'])
        # print((self.data['Cell Gap']-self.data['Designed Cell Gap']))
        self.data = self.data[mask].iloc[:,:-1]
        self.__score = None
        self.__plot = None

    @property
    def score(self):
        if self.__score is None:
            def f(x):
                return np.round(9 * x) + 1
            score_df = self.data[['LC']].copy()
            score_df['LC%'] = tr2_score(
                self.data['LC%'], 
                'min-max', 'gt',self.constraint['w(LC%)'] , f)
            score_df['ΔEab*'] = tr2_score(
                self.data['ΔEab*'], 
                'min-max', 'lt', self.constraint['w(ΔEab*)'], f)
            score_df['RT'] = tr2_score(
                self.data['RT'], 
                'min-max', 'lt', self.constraint['w(RT)'], f)
            score_df['CR'] = tr2_score(
                self.data['CR'], 
                'min-max', 'gt', self.constraint['w(CR)'], f)
            score_df['Sum'] = score_df.iloc[:,1:].sum(axis=1)
            # score_df['Remark'] = self.data['Remark']
            # score_df['Cell Gap'] = self.data['Cell Gap']
            score_df = score_df.sort_values(by='Sum', ascending=False)
            self.__score = score_df

        return self.__score

    @property
    def plot(self):
        if self.__plot is None:
            plot_df = self.score.set_index('LC').stack().reset_index()
            plot_df.columns = ['LC', 'Item', 'Score']
            fig = px.bar(
                plot_df, x='Item', y='Score', color='LC', barmode='group')
            self.__plot = plot(fig, output_type='div')
        
        return self.__plot
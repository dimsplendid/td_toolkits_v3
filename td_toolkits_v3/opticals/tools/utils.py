import numpy as np
import pandas as pd
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

from td_toolkits_v3.materials.models import LiquidCrystal
from td_toolkits_v3.products.models import Experiment
from td_toolkits_v3.opticals.models import (
    AxometricsLog, 
    OpticalLog, 
    OpticalReference, 
    RDLCellGap,
    ResponseTimeLog,
    OpticalsFittingModel,
)

class OptLoader():
    
    def __init__(self, experiment_name: str, ref=None, cell_gap='axo'):
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
        """
        self.experiment_name = experiment_name
        self.ref = ref
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
        if self.cell_gap not in ['axo', 'rdl']:
            return f'The {self.cell_gap} method is not implement now.'

        # Setting the needed data, and the proper columns name for later use.
        header = {
            "chip__name": "ID",
            "chip__lc__name": "LC",
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
        if self.cell_gap not in ['axo', 'rdl']:
            return f'The {self.cell_gap} method is not implement now.'

        # Setting the needed data, and the proper columns name for later use.
        header = {
            "chip__name": "ID",
            "chip__lc__name": "LC",
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
    
    @property
    def ref(self):
        
        if self._ref == None:
            print('Should set the (Factory, Product) first.')
            return
        
        factory_name = self._ref[0]
        type_name = self._ref[1]
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
            "w_y": "Wx",
            "contrast_ratio": "CR"
        }
        df = pd.DataFrame.from_records(
            OpticalReference.objects
            .filter(product_model_type__name=type_name, product_model_type__factory__name=factory_name)
            .values(*header)
        ).rename(
            columns=header
        )
        
        if len(df) == 0:
            return f'There is no {type_name} reference, maybe you can build one.'
        
        return df
    
    @ref.setter
    def ref(self, ref_product):
        self._ref = ref_product


class OptFitting():

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
                 + 'or try to update[TODO]'

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
        if self.__w_capital_y_model is not None:
            return self.__w_capital_y_model
        
        self.__wy_model, r2_score = self.__opt_model('WY')
        self.r2['f(Vop, Cell Gap) |-> WY'] = r2_score
        return self.__wy_model

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
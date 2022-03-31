import numpy as np
import pandas as pd
import plotly.express as px
from plotly.offline import plot
import re
from sympy import construct_domain

from td_toolkits_v3.opticals.tools.utils import tr2_score
from td_toolkits_v3.reliabilities.models import (
    Adhesion,
    DeltaAngle,
    File,
    LowTemperatureOperation,
    LowTemperatureStorage,
    PressureCookingTest,
    ReliabilitySearchProfile,
    SealWVTR,
    UShapeAC,
    VoltageHoldingRatio,
)

class ReliabilityScore():

    def __init__(self, query, profile) -> None:
        self.lc, self.pi, self.seal = query
        self.constraint = profile
        # pattern using for tranform the model name
        self.pattern = re.compile(r'(?<!^)(?=[A-Z])')
        # header using for query and modified field name
        self.header = {
            'lc__name': 'LC',
            'pi__name': 'PI',
            'seal__name': 'Seal',
            'value': 'Value',
            'vender__name': 'Vender',
            'file_source__name': 'file source'
        }
        
        self.__name_map = {}
        # generate all tables
        _ = self.__table(Adhesion, opt=3)
        _ = self.__table(DeltaAngle, opt=6)
        _ = self.__table(UShapeAC, 'u_shape_ac', opt=6, f=np.abs)
        _ = self.__table(VoltageHoldingRatio)
        _ = self.__table(LowTemperatureStorage, opt=4)
        _ = self.__table(PressureCookingTest)
        _ = self.__table(SealWVTR, 'seal_wvtr', opt=1)

        self.__result = None
        self.__plot_df = []
        self.__plot = None

    def __table(self, Model=None, name=None, opt=7, f=None):
        """
        Model: django.db.models.Model
            The RA log model you need
        name: str, default is None
            Alternative name of the model, this name is the attribute
            name of ReliabilitySearchProfile, default would
            generate from the Model name (CapCamel to snake_case)
            eg: MyModel -> my_model
        opt: int, default is 7(all)
            Using binary to represent query lc, pi, seal,
            eg. need all, (lc, pi, seal) = 111 = 7
        f: funcion, default is None
            Transfer the value x to f(x) if needed
        """
        if (Model is None) and (name is None):
            return 'You should at least offer one of Model or name'

        if Model is None:
            return getattr(self, name)
        
        if name is None:
            name = self.pattern.sub('_', Model.__name__).lower()

        if getattr(self, f'table_{name}', None) is None:
            # option early gardian
            if (opt > 7) and (opt < 1):
                return 'no such option, opt need to be 1~7'

            # get the compare condition, should be 'gt' or 'lt'
            cmp = getattr(self.constraint, f'{name}_cmp')
            if cmp not in ['gt', 'lt']:
                return f'Check the profile {name}_cmp, something wrong.'
            # setting query parameter for the model filter
            q = {
                'lc__in': self.lc,
                'pi__in': self.pi,
                'seal__in': self.seal,
                'vender__in': getattr(self.constraint, f'{name}_venders').all(),
                f'value__{cmp}': getattr(self.constraint, name)
            }

            # parse option
            opt = f'{opt:03b}'
            groupby = []
            if opt[0] == '0':
                del q['lc__in']
            else:
                groupby.append('LC')

            if opt[1] == '0':
                del q['pi__in']
            else:
                groupby.append('PI')
            if opt[2] == '0':
                del q['seal__in']
            else:
                groupby.append('Seal')


            df = pd.DataFrame.from_records(
                Model.objects.filter(**q).values(*self.header)
            ).rename(columns=self.header)
            # check the query result
            if len(df) == 0:
                result = {
                    'raw': None,
                    'mean': None,
                }
                setattr(self, f'table_{name}', result)
                return getattr(self, f'table_{name}')
            if f:
                df['Value'] = f(df['Value'])

            self.__name_map[name] = Model.name
            mean_df = df.groupby(
                by=groupby, 
                as_index=False
            ).mean().sort_values(by='Value', ascending=False)
            result = {
                'raw': df,
                'mean': mean_df
            }

            setattr(self, f'table_{name}', result)

        return getattr(self, f'table_{name}')    

    @staticmethod
    def score_f(x):
        return np.round(9 * x) + 1

    @property
    def result(self):
        if self.__result is None:

            # generate all configuration table
            df_lc = pd.DataFrame.from_records(
                self.lc.values('name')
            ).rename(columns={'name': 'LC'})
            df_pi = pd.DataFrame.from_records(
                self.pi.values('name')
            ).rename(columns={'name': 'PI'})
            df_seal = pd.DataFrame.from_records(
                self.seal.values('name')
            ).rename(columns={'name': 'Seal'})
            tmp_df = df_lc.merge(df_pi, how='cross')
            score_df = tmp_df.merge(df_seal, how='cross')
            raw_df = score_df.copy()


            for table in self.__dir__():
                # skip not table attribute
                if not table.startswith('table_'):
                    continue
                # skip None table
                if (mean := getattr(self, table)['mean']) is None:
                    continue
                
                item = table[6:]
                columns = list(mean.columns[:-1])
                score = mean[columns]
                score[item] = tr2_score(
                    mean['Value'], 
                    'min-max', 
                    getattr(self.constraint, f'{item}_cmp'),
                    getattr(self.constraint, f'{item}_weight'),
                    self.score_f
                )
                mean = mean.rename(columns={'Value':item})
                score_df = score_df.merge(score, on=columns, how='left')
                raw_df = raw_df.merge(mean, on=columns, how='left')

            score_df = score_df.fillna(0)
            score_df['Sum'] = score_df.iloc[:, 3:].sum(axis=1)
            score_df = score_df[score_df['Sum']>0]
            score_df = score_df.sort_values('Sum', ascending=False)
            raw_df = raw_df.iloc[score_df.index, :]
            self.__result = {
                'normalized': score_df.rename(columns=self.__name_map),
                'raw': raw_df.rename(columns=self.__name_map),
            }

        return self.__result

    @property
    def plot(self):
        if self.__plot is None:
            pass



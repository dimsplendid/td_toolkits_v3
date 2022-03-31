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
        self.pattern = re.compile(r'(?<!^)(?=[A-Z])')
        self.header = {
            'lc__name': 'LC',
            'pi__name': 'PI',
            'seal__name': 'Seal',
            'value': 'Value',
            'vender__name': 'Vender',
            'file_source__name': 'file source'
        }
        
        # run all models
        _ = self.__table(Adhesion, opt=3)
        _ = self.__table(DeltaAngle, opt=6)
        _ = self.__table(UShapeAC,name='u_shape_ac', opt=6)
        _ = self.__table(VoltageHoldingRatio)
        _ = self.__table(LowTemperatureStorage, opt=4)
        _ = self.__table(PressureCookingTest)
        _ = self.__table(SealWVTR, 'seal_wvtr', opt=1)

        self.__score = None
        self.__plot_df = []
        self.__plot = None

    def __table(self, Model=None, name=None, opt=7):
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
        """
        if (Model is None) and (name is None):
            return 'You should at least offer one of Model or name'

        if Model is None:
            return getattr(self, name)
        
        if name is None:
            name = self.pattern.sub('_', Model.__name__).lower()

        if getattr(self, name, None) is None:
            # parse option
            if (opt > 7) and (opt < 1):
                return 'no such option, opt need to be 1~7'
            cmp = getattr(self.constraint, f'{name}_cmp')
            q = {
                'lc__in': self.lc,
                'pi__in': self.pi,
                'seal__in': self.seal,
                'vender__in': getattr(self.constraint, f'{name}_venders').all(),
                f'value__{cmp}': getattr(self.constraint, name)
            }
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
                setattr(self, f'{name}', result)
                return getattr(self, name)

            mean_df = df.groupby(
                by=groupby, 
                as_index=False
            ).mean().sort_values(by='Value', ascending=False)
            result = {
                'raw': df,
                'mean': mean_df
            }

            setattr(self, f'{name}', result)

        return getattr(self, name)    

    @property
    def score(self):
        if self.__score is None:
            # custome score function
            def f(x):
                return np.round(9 * x) + 1

            def is_good(table):
                return not(table.empty or (table.iloc[:,-1].sum() == 0))

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
            df = tmp_df.merge(df_seal, how='cross')
            df_raw = df.copy()

            # adhesion part
            if self.adhesion:
                adhesion_score = self.adhesion['mean'][['PI', 'Seal']]
                adhesion_score['Adhesion'] = tr2_score(
                    self.adhesion['mean']['Value'],
                    'min-max', 'gt', self.constraint.adhesion_weight, f
                )
                if is_good(adhesion_score):
                    df = df.merge(adhesion_score, on=['PI', 'Seal'], how='left')
            
            # delta angle
            if self.delta_angle:
                delta_angle_score = self.delta_angle['mean'][['LC', 'PI']]
                delta_angle_score['Δ angle'] = tr2_score(
                    self.delta_angle['mean']['Value'],
                    'min-max', 'gt', self.constraint.delta_angle_weight, f
                )
                if is_good(delta_angle_score):
                    df = df.merge(
                        delta_angle_score, on=['LC', 'PI'], how='left')
                
            # U Shape
            if self.ushape_ac:
                ushape_ac_score = self.ushape_ac['mean'][['LC', 'PI']]
                ushape_ac_score['U-Shape AC%'] = tr2_score(
                    self.ushape_ac['mean']['Value'],
                    'min-max', 'gt', self.constraint.u_shape_ac_weight, f
                )
                if is_good(ushape_ac_score):
                    df = df.merge(ushape_ac_score, on=['LC', 'PI'], how='left')
                
            # VHR
            if self.vhr:
                vhr_score = self.vhr['mean'][['LC', 'PI', 'Seal']]
                vhr_score['VHR'] = tr2_score(
                    self.vhr['mean']['Value'],
                    'min-max', 'gt', 
                    self.constraint.voltage_holding_ratio_weight, f
                )
                if is_good(vhr_score):
                    df = df.merge(
                        vhr_score, on=['LC', 'PI', 'Seal'], how='left')
                
            # LTS
            if self.lts:
                lts_score = self.lts['mean'][['LC']]
                lts_score['LTS'] = tr2_score(
                    self.lts['mean']['Value'],
                    'min-max', 'gt', 
                    self.constraint.low_temperature_storage_weight, f
                )
                if is_good(lts_score):
                    df = df.merge(lts_score, on=['LC'], how='left')
                
            # PCT
            if self.pct:
                pct_score = self.pct['mean'][['LC', 'PI', 'Seal']]
                pct_score['PCT'] = tr2_score(
                    self.pct['mean']['Value'],
                    'min-max', 'gt', 
                    self.constraint.pressure_cooking_test_weight, f
                )
                if is_good(pct_score):
                    df = df.merge(
                        pct_score, on=['LC', 'PI', 'Seal'], how='left')
                
            # Seal WVTR
            if self.seal_wvtr:
                seal_wvtr_score = self.seal_wvtr['mean'][['Seal']]
                seal_wvtr_score['Seal WVTR'] = tr2_score(
                    self.seal_wvtr['mean']['Value'],
                    'min-max', 'gt', self.constraint.seal_wvtr_weight, f
                )
                if is_good(seal_wvtr_score):
                    df = df.merge(seal_wvtr_score, on=['Seal'], how='left')
                
            #TODO: These should have more explicit way to implement...

            df = df.fillna(0)
            df['Sum'] = df.iloc[:, 3:].sum(axis=1)
            self.__score = df.sort_values('Sum', ascending=False)

        return self.__score

    @property
    def plot(self):
        if self.__plot is None:
            pass



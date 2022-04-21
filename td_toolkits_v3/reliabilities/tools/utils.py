import numpy as np
import pandas as pd
import plotly.express as px
from plotly.offline import plot
import re
from scipy.interpolate import interp1d

from td_toolkits_v3.opticals.tools.utils import tr2_score, OptLoader
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

def table_shrink(df, step=0.1, ratio=1.5):
    """
    A greedy method to find the max dense part of the sparse table.
    Reduce rows and columns with NaN step by step.

    Only consider number fields.

    The effect is like:
    ⎡1  -1  Na⎤    ⎡1  -1⎤ 
    ⎢         ⎥ -> ⎢     ⎥
    ⎢3   2  Na⎥    ⎣3   2⎦
    ⎢         ⎥
    ⎣Na  2  Na⎦

    
    Parameters
    ----------
    df: pd.DataFrame
        The table to shrink
    step: float, default is 0.1
        The na ratio change for each step, smaller the better, but maybe slower
    ratio: float, default is 1.5
        The shrink speed ratio between row and columns, in mose sceanary,
        we may want keep more columns(feature) than rows(log)
    """
    # The column/raw contain na ratio
    na_ratio = 1

    #  count not number(cnn) columns
    cnn = (df.dtypes != np.number).sum()

    while df.isna().any(None) and (na_ratio > 0):
        na_ratio -= step
        # reduce row by the zero ratio of all columns
        df = df.loc[df.isna().sum(axis=1) / (len(df.columns)-cnn) < na_ratio]
        # reduce column by the zero ratio of all rows
        df = df.loc[:, df.isna().sum(axis=0) / len(df) < (na_ratio*ratio)]
       
    return df

class ReliabilityScore():

    def __init__(self, query, profile: ReliabilitySearchProfile) -> None:
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

        ushape_add = {
            'add_q': {
                'time': 1,
                'temperature': 25
            },
            'add_header': {
                'time': 'Time',
                'temperature': 'Temperature'
            }
        }

        _ = self.__table(UShapeAC, 'u_shape_ac', opt=6, f=np.abs, **ushape_add)

        vhr_add ={
            'add_q': {
                'measure_voltage': 1.,
                'measure_freq': 0.6,
            },
            'add_header': {
                'measure_voltage': 'Measure Voltage',
                'measure_freq': 'Measure Frequency'
            }
        }
        _ = self.__table(VoltageHoldingRatio, **vhr_add)

        lts_add = {
            'add_q': {
                'storage_condition': 'Bulk',
                'measure_temperature': -30,
            },
            'add_header': {
                'storage_condition': 'Storage Cond.',
                'measure_temperature': 'Measure Temp.(°C)',
            }
        }
        _ = self.__table(LowTemperatureStorage, opt=4, **lts_add)
        _ = self.__table(PressureCookingTest)
        _ = self.__table(SealWVTR, 'seal_wvtr', opt=1)

        self.__result = None
        self.__plot_df = []
        self.__plot = None

    def __table(
            self, Model=None, name=None, opt=7, f=None, 
            add_q=None, add_header=None
        ):
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
            # TODO: add condition filter, I think maybe just using 
            # dictionary union(`{**a, **b}`) to q.
            q = {
                'lc__in': self.lc,
                'lc__material_type': self.constraint.material_type,
                'pi__in': self.pi,
                'pi__material_type': self.constraint.material_type,
                'seal__in': self.seal,
                'seal__material_type': self.constraint.material_type,
                'vender__in': getattr(self.constraint, f'{name}_venders').all(),
                f'value__{cmp}': getattr(self.constraint, name)
            }
            if add_q is not None:
                q = {**q, **add_q}

            # parse option
            opt = f'{opt:03b}'
            groupby = []
            if opt[0] == '0':
                del q['lc__in']
                del q['lc__material_type']
            else:
                groupby.append('LC')

            if opt[1] == '0':
                del q['pi__in']
                del q['pi__material_type']
            else:
                groupby.append('PI')
            if opt[2] == '0':
                del q['seal__in']
                del q['seal__material_type']
            else:
                groupby.append('Seal')
            
            header = self.header
            if add_header is not None:
                header = {**self.header, **add_header}

            df = pd.DataFrame.from_records(
                Model.objects.filter(**q).values(*header)
            ).rename(columns=header)
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

            # Store the human readable name
            self.__name_map[name] = Model.name
            # only store configure and value in the mean table
            columns = [v for _, v in self.header.items()]
            mean_df = df[columns].groupby(
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
            raw_df = tmp_df.merge(df_seal, how='cross')

            # 1. construct raw table
            for table in self.__dir__():
                # skip not table attribute
                if not table.startswith('table_'):
                    continue
                # skip None table
                if (mean := getattr(self, table)['mean']) is None:
                    continue
                
                item = table[6:]
                # calculate the score, drop the last column(file source)
                columns = list(mean.columns[:-1])
                mean = mean.rename(columns={'Value':item})
                raw_df = raw_df.merge(mean, on=columns, how='left')

            # 2. shrink the raw_df to get a better table to estimate score
            shrink_df = table_shrink(raw_df)
            score_df = shrink_df.iloc[:,:3].copy()
            for item in shrink_df.columns[3:]:
                score_df[item] = tr2_score(
                    shrink_df[item], 
                    'min-max', 
                    getattr(self.constraint, f'{item}_cmp'),
                    getattr(self.constraint, f'{item}_weight'),
                    self.score_f
                )

            # rename columns to more human readable name
            raw_df = raw_df.rename(columns=self.__name_map)
            shrink_df = shrink_df.rename(columns=self.__name_map)
            score_df.columns = shrink_df.columns

            score_df['Sum'] = score_df.iloc[:, 3:].sum(axis=1)
            score_df = score_df.sort_values('Sum', ascending=False)
            shrink_df = shrink_df.loc[score_df.index, :]
            self.__result = {
                'normalized': score_df,
                'raw': shrink_df,
                'all': raw_df,
            }

        return self.__result

    @property
    def plot(self):
        """
        generate plotly plot and 
        """
        if self.__plot is None:
            df = self.result['normalized'].copy()
            df['Configuration'] = df['LC']+ ', '+df['PI']+ ', '+df['Seal']
            # drop the LC, PI, Seal columns
            # and only show the first 10 logs
            # (If logs are less than 10, keep all)
            df = df.iloc[:10, 3:]
            plot_df = df.set_index('Configuration').stack().reset_index()
            plot_df.columns = ['Configuration', 'Item', 'Score']
            fig = px.bar(
                plot_df, x='Item', y='Score', color='Configuration',
                barmode='group',
            )
            self.__plot = plot(fig, output_type='div')
            return self.__plot

class UShape:
    def __init__(self, experiment_name):
        self.opt_raw = OptLoader(experiment_name, None).opt
        self.__vt_curve = None
        self.__voltage_setting = None

        # TODO: U-Shape Calculate
        self.result_raw = None

    @property
    def vt_curve(self):
        if self.__vt_curve is None:
            df = self.opt_raw.groupby(['ID', 'Point']).apply(
                lambda group: group.iloc[:group['LC%'].argmax()+1]
            ).reset_index(drop=True)
            df['T%'] = df.groupby(['ID', 'Point'])['LC%'].apply(
                lambda group: 100 * group / group.max()
            )
            self.__vt_curve = {'data': df}
            fig = px.scatter(
                self.__vt_curve['data'],
                x='Vop', y='T%', color='LC'
            )
            self.__vt_curve['plot'] = plot(fig, output_type='div')

        return self.__vt_curve

    @property
    def voltage_setting(self):
        if self.__voltage_setting is None:
            # record all f(T) |-> V functons
            result = {
                'ID': [],
                'Point':[],
                'Cond': [],
                'L255': [],
                'L64': [],
                'L128': [],
            }
            for name, group in self.vt_curve['data'].groupby(['ID', 'Point']):
                f = interp1d(group['T%'], group['Vop'], fill_value='extrapolate')
                result['ID'] += [name[0]]
                result['Point'] += [name[1]]
                result['L255'] += [f(self.transmittance_from(255))]
                result['L64'] += [f(self.transmittance_from(64))]
                result['L128'] += [f(self.transmittance_from(128))]
                result['Cond'] += [group['LC'].iloc[0]]
            df = pd.DataFrame(result)
            df.iloc[:, 3:] = df.iloc[:, 3:].astype(float)
            self.__voltage_setting = (
                df.groupby('ID', as_index=False).mean()
                .merge(
                    df[['ID', 'Cond']].drop_duplicates(), on='ID', how='left'
                )
            )

        return self.__voltage_setting

    @staticmethod
    def transmittance_from(gray_level: int, gamma: float=2.2) -> float:
        """
        Transform gray level to transmittance with specific gamma value. 
        Parameters
        formula:(T99 as white state)
            T% = (gray_level / 255)^gamma * 99
        ----------
        gray_level: int
        gamma: float, default is 2.2
        """
        return (gray_level/255)**gamma * 99

# Test main
# Show the difference ratio and the final table of the table shrink
if __name__ == '__main__':
    from td_toolkits_v3.materials.models import (
        LiquidCrystal,
        Polyimide,
        Seal,
    )
    import matplotlib.pyplot as plt

    query = (
        LiquidCrystal.objects.all(),
        Polyimide.objects.all(),
        Seal.objects.all(),
    )

    profile = ReliabilitySearchProfile.objects.get(name='Default')

    ra_score = ReliabilityScore(query, profile)

    ratio_range = np.arange(0.5, 4, 0.1)
    columns_lens = []
    rows_lens = []
    for i in ratio_range:
        df = table_shrink(ra_score.result['all'], ratio=i)
        columns_lens.append(len(df.columns)-3)
        rows_lens.append(len(df))

    # plot the feature lenth change
    fig, ax1 = plt.subplots()
    color = 'tab:red'
    ax1.set_xlabel('ratio')
    ax1.set_ylabel('features', color=color)
    ax1.plot(ratio_range, columns_lens, color=color)
    ax1.tick_params(axis='y', labelcolor=color)

    ax2 = ax1.twinx()

    color = 'tab:blue'
    ax2.set_ylabel('# of logs', color=color)  # we already handled the x-label with ax1
    ax2.plot(ratio_range, rows_lens, color=color)
    ax2.tick_params(axis='y', labelcolor=color)

    fig.tight_layout()  # otherwise the right y-label is slightly clipped
    plt.show()
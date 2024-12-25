from __future__ import annotations
from typing import List, Tuple, Dict, Union, Optional, Callable, NamedTuple
from pydantic import BaseModel

import pandas as pd

from scipy.integrate import quad
from sklearn.metrics import r2_score

from django.db.models import Model

from td_toolkits_v3.materials.models import (
    LiquidCrystal,
    Polyimide,
    Seal,
    Vender,
)

def get_registered_name(header: dict[str, Model] = {
    'LC': LiquidCrystal,
    'PI': Polyimide,
    'Seal': Seal,
    # 'Vender': Vender,
}) -> pd.DataFrame:
    df_list = []
    for item in header:
        df_list.append(pd.DataFrame.from_records(
            header[item].objects.all().values('name', 'vender__name')
        ))
        df_list[-1]['item'] = item
    df = pd.concat(df_list)
    df = df[['item', 'name', 'vender__name']]
    df.columns = ['item', 'name', 'vender']
    return df

class Refraction(NamedTuple):
    l: float
    n: float

class LiquidCrystalPydantic(BaseModel):
    d: float
    k11: float
    k22: float
    k33: float
    
    ne_exp: List[Refraction]
    no_exp: List[Refraction]
    ne: Optional[Callable[[float],float]] = None
    no: Optional[Callable[[float],float]] = None
    blu: Callable[[float],float] = lambda x: 1000
    
    
    
    def __init__(self, *args, **kwargs):
        self.update_forward_refs()
        super().__init__(*args, **kwargs)
        self.ne = self.refraction_2(
            min(self.ne_exp, key=lambda x: x.l),
            max(self.ne_exp, key=lambda x: x.l),
        )
        self.no = self.refraction_2(
            min(self.no_exp, key=lambda x: x.l),
            max(self.no_exp, key=lambda x: x.l),
        )
    
    @property
    def k_avg(self) -> float:
        return (self.k11+self.k22+self.k33) / 3
    
    @staticmethod
    def cauchy_2(A: float, B: float) -> Callable[[float], float]:
        return lambda x: A + B/x**2
    
    def refraction_2(
        self,
        p1: Refraction, 
        p2: Refraction,
    ) -> Callable[[float], float]:
        A = (p1.n*p1.l**2 - p2.n*p2.l**2)/(p1.l**2 - p2.l**2)
        B = (p1.n - p2.n) * p1.l**2 * p2.l**2/(p2.l**2 - p1.l**2)
        return self.cauchy_2(A, B)   
    
    @property
    def refraction_r2(self) -> Dict[str, float]:
        x_ne = [x[0] for x in self.ne_exp]
        y_ne_pred = [self.ne(x) for x in x_ne]
        r2_ne = r2_score(y_ne_pred, [x[1] for x in self.ne_exp])
        
        x_no = [x[0] for x in self.no_exp]
        y_no_pred = [self.no(x) for x in x_no]
        r2_no = r2_score(y_no_pred, [x[1] for x in self.no_exp])
        
        return {
            'ne': r2_ne,
            'no': r2_no,
        }
    
    @property
    def scatter(self):
        return quad(
            lambda x: ((self.ne(x)**2-self.no(x)**2)**2) * self.blu(x),
            380, 780,
            limit=1000,
            epsabs = 1,
        )[0] * self.d / self.k_avg
from __future__ import annotations
from typing import Union, Any
import numpy as np
import pandas as pd
from dataclasses import dataclass, field

@dataclass
class PreprocessingResult:
    data: pd.DataFrame = field(default_factory=pd.DataFrame)
    fail_ids: list[str] = field(default_factory=list)
    
    def __iter__(self):
        return iter((self.data, self.fail_ids))

def is_smooth(
    data: pd.Series[float],
    
):
    ...

def vt_preprocessing(
    data: pd.DataFrame,
    id_key: str = 'ID',
    vop_key: str = 'Vop',
    lc_efficiency_key: str = 'LC%',
    normal_white_vop: float = 4.8,
    lc_efficency_cut_off: float = 0.5,
    other_fail_ids: list[str]|None = None,
) -> PreprocessingResult:
    """
    remove the failure measurement data base on VT curve and recent knowledges
    and reserve other fields.
    
    1. When in normal white voltage(~4.8 V) the panel should turn on, the LC%
       should greater than 0.5.
    2. The VT curve should not vibrate and smooth, that is, it should be filted
       by the high frequency part of Fourier Transform.
    3. And you can also add the failure id list to filtered.
    
    ## Parameters
    data: pandas.DataFrame
        The data to be preprocessed
    vop_key: str = 'Vop'
        The field's name of Vop in data
    lc_efficiency_key: str = 'LC%',
        The field's name of LC% in data
    normal_white_vop: float = 4.8
        The white vop to be cut off
    lc_efficency_cut_off: float = 0.5
        The cut off threshold
    other_fail_ids: list[str]|None = None
        If there are other known fail IDs, you can add here to remove together
    
    ## Returns
    PreprocessingResult
    .data: pandas.DataFrame
        data after preprocessing
    .fail_ids: list[str]
        all the fail IDs
    """
    result = PreprocessingResult()
    result.fail_ids += data[
        (data[vop_key]==normal_white_vop) &
        (data[lc_efficiency_key] < lc_efficency_cut_off)
    ][id_key].unique().tolist() # type: ignore
    
    if other_fail_ids is not None:
        result.fail_ids += other_fail_ids
    
    

    
    return result

def rt_preprocessing():
    pass
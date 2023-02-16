from __future__ import annotations
from typing import Callable
import pandas as pd
from dataclasses import dataclass, field

@dataclass
class PreprocessingResult:
    data: pd.DataFrame = field(default_factory=pd.DataFrame)
    fail_ids: set[str] = field(default_factory=set)
    
    def __iter__(self):
        return iter((self.data, self.fail_ids))

def is_smooth(
    data: pd.Series[float],
    cut_off: float = 0.01,
) -> bool:
    """
    Using the standard deviation of difference to justify the data is smooth 
    or not.
    
    ## Parameters
    data: pd.Series[float]
        the data series to be justify
    cut_off: float = 0.01
        the cut off to judge the smooth data, 
    """
    diff = data.diff()
    std: float = diff.std() # type: ignore
    return (std < cut_off)

def vt_preprocessing(
    data: pd.DataFrame,
    id_key: str = 'ID',
    point_key: str = 'Point',
    vop_key: str = 'Vop',
    lc_efficiency_key: str = 'LC%',
    normal_white_vop: float = 4.8,
    lc_efficency_cut_off: float = 0.5,
    other_fail_ids: list[str] | set[str] | None = None,
    is_smooth_f: Callable[[pd.Series[float]], bool] = is_smooth,
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
    result.fail_ids = result.fail_ids | set(data[
        (data[vop_key]==normal_white_vop) &
        (data[lc_efficiency_key] < lc_efficency_cut_off)
    ][id_key].unique().tolist())                           # type: ignore
    
    tmp_df = data[
        data[vop_key] > normal_white_vop
    ][[id_key, point_key, lc_efficiency_key]].copy()       # type: ignore
    tmp_df['Sample'] = ( 
          tmp_df[id_key].astype(str)                       # type: ignore
        + '-' 
        + tmp_df[point_key].astype(str)                    # type: ignore
    )
    tmp_df: pd.DataFrame = (
        tmp_df[['Sample', lc_efficiency_key]]              # type: ignore
        .groupby('Sample')
        .apply(is_smooth_f)                                # type: ignore
    )
    
    result.fail_ids = result.fail_ids | {
        ele.split('-')[0]                                  # type: ignore
        for ele in                                         # type: ignore
        tmp_df[~tmp_df[lc_efficiency_key]].index.to_list() # type: ignore     
    }
    
    if other_fail_ids is not None:
        result.fail_ids = result.fail_ids | set(other_fail_ids)
    
    result.data = data[~data['ID'].isin(result.fail_ids)]  # type: ignore

    
    return result

def rt_preprocessing():
    pass

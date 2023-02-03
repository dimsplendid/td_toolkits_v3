from __future__ import annotations
import pandas as pd
from dataclasses import dataclass

@dataclass
class PreprocessingResult:
    data: pd.DataFrame
    fail_ids: list[str]
    
    def __iter__(self):
        return iter((self.data, self.fail_ids))

def vt_preprocessing(
    df: pd.DataFrame,
    vop_key: str = 'Vop',
    lc_efficiency_key: str = 'LC%',
    
) -> PreprocessingResult:
    """
    remove the failure measurement data base on VT curve and recent knowledge
    1. 
    2. 
    
    Parameters
    ==========
    
    
    Returns
    =======
    """
    pass

def rt_preprocessing
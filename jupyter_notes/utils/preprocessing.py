from __future__ import annotations
import pandas as pd
from dataclasses import dataclass

@dataclass
class PreprocessingResult:
    data: pd.DataFrame
    fail_ids: list[str]
    
    def __iter__(self):
        return iter((self.data, self.fail_ids))

def vt_fail_drop(
    df: pd.DataFrame,
    vop_key: str = 'Vop',
    lc_efficiency_key: str = 'LC%',
    
) -> PreprocessingResult:
    """
    """
    pass
from __future__ import annotations

import pandas as pd
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
    'Vender': Vender,
}) -> pd.DataFrame:
    df_list = []
    for item in header:
        df_list.append(pd.DataFrame.from_records(
            header[item].objects.all().values('name')
        ))
        df_list[-1]['item'] = item
    df = pd.concat(df_list)
    df = df[['item', 'name']]
    return df
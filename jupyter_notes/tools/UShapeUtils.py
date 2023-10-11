import os
from pathlib import Path
import pandas as pd

def load(
    path: Path
):
    """
    Loading the U-Shape data from given path.
    The raw data structure should be:
    ─┬─ folder[path]
     └─ [short_id_1]_[short_id_2][_err1][_err2]
         ├─ [short_id_1].xlsx
         └─ [short_id_2].xlsx
    """
    list_df = []
    root, folders, _ = next(os.walk(path))
    for folder in folders:
        name_parsers = folder.split("_")
        if len(name_parsers) >= 2:
            short_ids = name_parsers[0:2]
        else:
            short_ids = [name_parsers[0]]
        for short_id in short_ids:
            df = pd.read_excel(
                Path(root)/folder/f"{short_id}.xlsx",
                sheet_name="U數據彙整"
            )
            df = df[df['ΔVcom(W-B)(mV)']!=0]
            df = df.dropna(subset=["ΔVcom(W-B)(mV)"])
            df['Panel ID'] = short_id
            warning = ""
            if "vcom差大於0.03" in folder:
                warning += "vcom差大於0.03 "
            if "vcom大於0.05" in folder:
                warning += "vcom大於0.05"
            df["Warning"] = warning
            df[['Total亮度差(W-B)@系Vcom(%)', 'AC IS亮度差(W-B)(%)', 'DC IS亮度差(W-B)(%)']] *= 100
            list_df.append(df)
    return pd.concat(list_df, ignore_index=True)
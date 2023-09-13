import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from typing import List, Optional

def plot(
    df: pd.DataFrame,
    groupby: Optional[str] = None,
    hover_data: List[str]=[],
):
    fig = px.box(
        df,
        x='LC',
        y='VHR%',
        # points='all',
        hover_data=hover_data,
        color=groupby,
    )
    mean_trace = go.Scatter()

    lcs = df.LC.unique()
    avg = []
    if groupby is None:
        for lc in lcs:
            avg.append(df[df.LC==lc]['VHR%'].mean())

        fig.add_trace(
            go.Scatter(
                x=lcs,
                y=avg,
                text=[f'{x:.1f}' for x in avg],
                mode='markers+text',
                name='mean',
                textposition="bottom center",
                fillcolor='firebrick'
            )
        )
    else:
        ...
    return fig
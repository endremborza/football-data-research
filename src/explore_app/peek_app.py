import re

import dask.dataframe as dd
import plotly.graph_objects as go
import requests
from dask.distributed import Client, get_client
from daskpeeker import (
    Metric,
    Peeker,
    SharedFigure,
    SharedTrace,
    StandaloneFigure,
    Table,
)

from ..network.create_raw_pass_data import chain_len_col, chain_num_col
from .create_figure import get_network_figure
from .export_app_data import (
    app_discrete_cols,
    edge_ends,
    load_entire_app_data,
    loc_cols,
)

pass_dir_cat_col = "pass_direction_cat"


class FootballPeeker(Peeker):
    def get_shared_figures(self):
        return [
            SharedFigure(
                go.Figure(layout=go.Layout(title="Pass Chain Lengths")), chain_len_col
            ),
            SharedFigure(
                go.Figure(layout=go.Layout(title="Pass Directions")), pass_dir_cat_col
            ),
        ]

    def get_report_elems(self, filtered_ddf: dd.DataFrame):

        elems = [Metric(filtered_ddf.shape[0].compute(), "Number of passes")]

        for k, v in (
            filtered_ddf.loc[
                :,
                [
                    "is_success",
                    "target_distance_from_opp_goal",
                    "distance_from_opp_goal",
                    "length",
                    "predicted_success_probability",
                ],
            ]
            .mean()
            .compute()
        ).items():
            elems.append(Metric(round(v, 4), k.replace("_", " ").title()))

        for c in [chain_len_col, pass_dir_cat_col]:
            s = (
                filtered_ddf.loc[:, c]
                .value_counts()
                .compute()
                .sort_index()
                .head(10)
                .pipe(lambda s: s / s.sum())
            )
            elems.append(SharedTrace(go.Bar(x=s.index.tolist(), y=s.tolist()), c))

        elems.append(StandaloneFigure(get_network_figure(filtered_ddf), col_width=12))

        return elems


def get_peeker():
    print("getting peeker")
    try:
        scheduler_address = re.compile("> Scheduler (.*) </").findall(
            requests.get("http://127.0.0.1:8787/info/main/workers.html").content.decode(
                "utf-8"
            )
        )[0]

        client = get_client(scheduler_address)
    except Exception as e:
        print("new client started: ", e)
        client = Client()
    n_part = sum(client.nthreads().values())
    print(client.dashboard_link)

    app_data = load_entire_app_data()
    ddf = dd.from_pandas(app_data, npartitions=n_part).persist()

    cat_filt_cols = app_discrete_cols
    num_filt_cols = [chain_len_col]

    return FootballPeeker(ddf, cat_filt_cols, num_filt_cols)

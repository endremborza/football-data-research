import glob
import os

from functools import reduce

from tqdm.notebook import tqdm
import pandas as pd
import numpy as np

from src.dvc_util import PipelineElement
from src.network.create_raw_pass_data import export_pass_data_pe, load_season_passes

from src.data_loaders import T2Data, reduce_append

app_dir = os.path.join("data", "app-data")


edge_ends = [
    "source_formation_slot",
    "target_formation_slot",
]

loc_cols = ["x", "y", "passendx", "passendy"]

cat_cols = [
    "period",
    "outcometype",
    "event_side",
    "zone",
    "match_standing",
    "match_result",
    "pass_direction_cat",
    "predicted_success_bin",
    "formation_name",
    "team_name",
]

bool_cats = {
    "pass_kind": [
        "throwin",
        "freekicktaken",
        "goalkick",
        "cornertaken",
        "keeperthrow",
    ],
    "pass_style": [
        "cross",
        "layoff",
    ],
}

app_discrete_cols = [*bool_cats.keys(), *cat_cols]


def make_cat_from_bools(cols):
    def f(df):
        def _redf(c1, c2):
            return np.where(df.loc[:, c2].fillna(0).astype(bool), c2, c1)

        return reduce(_redf, ["other", *cols])

    return f


def export_app_data():
    os.makedirs(app_dir, exist_ok=True)
    season_df = T2Data.get_wh_season_df()
    team_names = T2Data.get_wh_team_df().set_index("teamId").loc[:, "name"]

    for season_id in tqdm(season_df["wh_season_id"].tolist()):
        (
            load_season_passes(season_id)
            .assign(
                team_name=lambda df: team_names.reindex(df["teamid"]).values,
                predicted_success_bin=lambda df: pd.cut(
                    df["predicted_success_probability"], [0, 0.25, 0.5, 0.75, 1]
                ).astype(str),
            )
            .assign(**{k: make_cat_from_bools(v) for k, v in bool_cats.items()})
        ).to_parquet(os.path.join(app_dir, f"app-data-{season_id}.parquet"))


def load_season_app_data(season_id: str):
    return pd.read_parquet(os.path.join(app_dir, f"app-data-{season_id}.parquet"))


def load_entire_app_data() -> pd.DataFrame:
    files = glob.glob(os.path.join(app_dir, "app-data-*.parquet"))
    return reduce(reduce_append, files)


export_app_data_pe = PipelineElement(
    name="export_app_data",
    runner=export_app_data,
    output_path=app_dir,
    param_list=["seed"],
    dependency_list=[export_pass_data_pe],
)

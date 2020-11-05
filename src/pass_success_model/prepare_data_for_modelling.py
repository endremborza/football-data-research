from functools import reduce
import glob
import os

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import OneHotEncoder

from ..data_loaders import get_season_events, T2Data, reduce_append
from ..dvc_util import PipelineElement

bool_quals = [
    "longball",
    "headpass",
    "throwin",
    "chipped",
    "cross",
    "cornertaken",
    "freekicktaken",
    "layoff",
    "indirectfreekicktaken",
    "throughball",
    "keeperthrow",
    "goalkick",
]

categ_vals = ["period", "event_side", "pass_direction_cat"]

num_vals = [
    "x",
    "y",
    "passendy",
    "passendx",
    "length",
    "distance_from_opp_goal",
    "distance_from_own_goal",
    "minute",
]

target = "is_success"

model_data_dir = os.path.join("data", "data_for_models")


class AddCodes(BaseEstimator, TransformerMixin):
    def __init__(self, categs):
        self._ohenc = OneHotEncoder(sparse=False)
        self._categs = categs

    def fit(self, df, _=None):
        self._ohenc.fit(df.loc[:, self._categs])
        return self

    def transform(self, df):
        nocat_df = df.drop(self._categs, axis=1)
        return pd.DataFrame(
            np.concatenate(
                [nocat_df.values, self._ohenc.transform(df.loc[:, self._categs])],
                axis=1,
            ),
            columns=[*nocat_df.columns, *self._ohenc.get_feature_names()],
            index=df.index,
        )


def get_pass_direction_category(df):
    try:
        angle = df["angle"]
    except KeyError:
        return np.repeat(np.nan, df.shape[0])
    return np.where(
        (angle < (np.pi * 0.25)) | (angle > (np.pi * 1.75)),
        "forward",
        np.where(
            (angle >= (np.pi * 0.25)) & (angle <= (np.pi * 0.75)),
            "left",
            np.where(
                (angle > (np.pi * 0.75)) & (angle < (np.pi * 1.25)), "backward", "right"
            ),
        ),
    )


def transform_event_data_to_pass_data(event_df: pd.DataFrame) -> pd.DataFrame:
    pass_period_ids = pd.Series(
        {
            "FirstHalf": 1,
            "SecondHalf": 2,
            "FirstPeriodOfExtraTime": 3,
            "SecondPeriodOfExtraTime": 4,
        }
    )

    return (
        event_df.loc[lambda df: df["type"] == "Pass", :]
        .dropna(how="all", axis=1)
        .assign(
            pass_direction_cat=get_pass_direction_category,
            is_success=lambda df: (df["outcometype"] == "Successful").astype(float),
            distance_from_opp_goal=lambda df: (
                (df["x"] - 100) ** 2 + (df["y"] - 50) ** 2
            )
            ** 0.5,
            distance_from_own_goal=lambda df: (df["x"] ** 2 + (df["y"] - 50) ** 2)
            ** 0.5,
            match_period_id=lambda df: pass_period_ids.reindex(df["period"]).values,
        )
    )


def transform_pass_data_to_model_data(pass_df: pd.DataFrame) -> pd.DataFrame:
    return pd.concat(
        [
            pass_df.loc[:, [*num_vals, *categ_vals, target]],
            pass_df.reindex(bool_quals, axis=1).fillna(0),
        ],
        axis=1,
    )


def transform_event_data_to_model_data(event_df: pd.DataFrame) -> pd.DataFrame:
    return transform_event_data_to_pass_data(event_df).pipe(
        transform_pass_data_to_model_data
    )


def write_parts(season_id):
    full_df = transform_event_data_to_model_data(get_season_events(season_id))
    for df_name, df in zip(
        ["x_train", "x_test", "y_train", "y_test"],
        train_test_split(full_df.drop(target, axis=1), full_df.loc[:, [target]]),
    ):
        cat_dir = os.path.join(model_data_dir, df_name)
        os.makedirs(cat_dir, exist_ok=True)
        df.to_parquet(os.path.join(cat_dir, f"passes-{season_id}.parquet"))


def export_all_model_data(wrapper=lambda x: x):
    season_df = T2Data.get_wh_season_df()
    for season_id in wrapper(season_df["wh_season_id"].tolist()):
        try:
            write_parts(season_id)
        except KeyError:
            print(season_id)


def load_all_model_data(data_kind):
    cat_dir = os.path.join(model_data_dir, data_kind)
    return reduce(reduce_append, glob.glob(f"{cat_dir}/*.parquet"))


prep_pass_model_pe = PipelineElement(
    name="prepare_data_for_model",
    runner=export_all_model_data,
    output_path=model_data_dir,
)

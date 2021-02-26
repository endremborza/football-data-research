import glob
import os
from functools import reduce

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder

from ..data_loaders import T2Data, get_season_events, reduce_append, t2_dir
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

categ_vals = ["period", "event_side", "pass_direction_cat", "match_standing"]

num_vals = [
    "x",
    "y",
    "passendy",
    "passendx",
    "length",
    "distance_from_opp_goal",
    "distance_from_own_goal",
    "target_distance_from_opp_goal",
    "target_distance_from_own_goal",
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


def add_match_status_cols(match_df):
    return (
        match_df.assign(
            is_home_goal=lambda df: (df["event_side"] == "home")
            & (df["type"] == "Goal"),
            is_away_goal=lambda df: (df["event_side"] == "away")
            & (df["type"] == "Goal"),
        )
        .assign(
            home_goals=lambda df: df["is_home_goal"].cumsum(),
            away_goals=lambda df: df["is_away_goal"].cumsum(),
        )
        .assign(
            our_goals=lambda df: np.where(
                df["event_side"] == "home", df["home_goals"], df["away_goals"]
            ),
            opp_goals=lambda df: np.where(
                df["event_side"] == "away", df["home_goals"], df["away_goals"]
            ),
        )
        .pipe(
            lambda df: pd.concat(
                [
                    df,
                    df.groupby("event_side")
                    .agg({"our_goals": "last", "opp_goals": "last"})
                    .rename(columns=lambda s: "final_" + s)
                    .reindex(df["event_side"].values)
                    .assign(id=df.index)
                    .set_index("id"),
                ],
                axis=1,
            )
        )
        .assign(
            match_standing=lambda df: np.where(
                df["our_goals"] > df["opp_goals"],
                "winning",
                np.where(df["our_goals"] < df["opp_goals"], "losing", "drawing"),
            ),
            match_result=lambda df: np.where(
                df["final_our_goals"] > df["final_opp_goals"],
                "won",
                np.where(
                    df["final_our_goals"] < df["final_opp_goals"], "lost", "drawn"
                ),
            ),
        )
    )


def pre_filter_extension(season_df):
    return pd.concat(
        [
            add_match_status_cols(match_df)
            for _, match_df in season_df.groupby("wh_match_id")
        ]
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
        event_df.pipe(pre_filter_extension)
        .loc[lambda df: df["type"] == "Pass", :]
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
            target_distance_from_opp_goal=lambda df: (
                (df["passendx"] - 100) ** 2 + (df["passendy"] - 50) ** 2
            )
            ** 0.5,
            target_distance_from_own_goal=lambda df: (
                df["passendx"] ** 2 + (df["passendy"] - 50) ** 2
            )
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
    dependency_list=[t2_dir],
)

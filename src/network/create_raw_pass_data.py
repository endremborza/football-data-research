import glob
import os

from functools import reduce

import numpy as np
import pandas as pd

from src.data_loaders import T2Data, get_season_events, reduce_append
from src.dvc_util import PipelineElement
from src.pass_success_model.run_pass_success_model import (
    run_pass_model_pe,
    load_trained_model,
)
from src.pass_success_model.prepare_data_for_modelling import (
    target,
    transform_event_data_to_pass_data,
    transform_pass_data_to_model_data,
)

pass_dir = os.path.join("data", "pass-data")

x_field_bins = [-1, 33.3, 66.6, 101]
y_field_bins = x_field_bins

MAX_TIME_FOR_CONSEQ = 3

last_pass_col = ["is_success", "target_player", "fullsec"]

conscol = "is_conseq"


def get_seq_lengths(df):
    seq_gb = df.assign(seq_id=(~df.loc[:, conscol]).cumsum()).groupby("seq_id")[conscol]
    return df.assign(
        n_in_chain=seq_gb.transform("cumsum") + df["is_success"],
        chain_len=seq_gb.transform("count"),
    )


def get_chains(gdf):
    return (
        gdf.assign(fullsec=lambda df: df["minute"] * 60 + df["second"])
        .sort_values(["fullsec", "eventid"])
        .pipe(
            lambda df: pd.concat(
                [
                    df,
                    df.loc[:, last_pass_col]
                    .rename(columns=lambda s: f"prev_pass_{s}")
                    .assign(prev_pass_id=lambda df: df.index)
                    .shift(1),
                ],
                axis=1,
            )
        )
        .assign(
            time_since_last_pass=lambda df: (df["fullsec"] - df["prev_pass_fullsec"])
        )
        .assign(
            **{
                conscol: lambda df: (df["time_since_last_pass"] <= MAX_TIME_FOR_CONSEQ)
                & (df["source_player"] == df["prev_pass_target_player"])
                & df["prev_pass_is_success"].astype(bool)
                & df["is_success"].astype(bool)
            }
        )
        .drop(["fullsec", "prev_pass_fullsec"], axis=1)
        .pipe(get_seq_lengths)
        .drop(conscol, axis=1)
    )


def get_melted_formations(match_id, formation_uses_df):
    return (
        formation_uses_df.assign(
            period_id=lambda df: np.where(df["period"] == 16, 1, df["period"])
        )
        .loc[lambda df: df["wh_match_id"] == match_id]
        .rename(columns={"side": "event_side"})
        .melt(
            id_vars=[
                "period_id",
                "start_minute",
                "end_minute",
                "formation_name",
                "event_side",
                "wh_match_id",
            ],
            value_vars=[f"spot_{i}" for i in range(1, 12)],
        )
        .dropna()
        # .assign(variable=lambda df: df["formation_name"] + "-" + df["variable"])
    )


def transform_passes_to_network_base(pass_df):

    model = load_trained_model()
    pass_network_base = pass_df.assign(
        source_field_zone=lambda df: pd.cut(
            df["x"], bins=x_field_bins
        ).cat.codes.astype(str)
        + "-"
        + pd.cut(df["y"], bins=y_field_bins).cat.codes.astype(str),
        target_field_zone=lambda df: pd.cut(
            df["passendx"], bins=x_field_bins
        ).cat.codes.astype(str)
        + "-"
        + pd.cut(df["passendy"], bins=y_field_bins).cat.codes.astype(str),
        source_player=lambda df: df["wh_player_id"],
        target_player=lambda df: np.where(
            df["is_success"], df["player_with_next_touch"], np.nan
        ),
        predicted_success_probability=lambda df: model.predict_proba(
            transform_pass_data_to_model_data(df).drop(target, axis=1)
        )[:, 1],
        predicted_success_bin=lambda df: pd.cut(
            df["predicted_success_probability"], np.linspace(0, 1, 11)
        ),
    )
    return pass_network_base


def _filter_for_past(df):
    return (df["minute"] >= df["start_minute"]) & (
        df["match_period_id"] >= df["period_id"]
    )


def extend_pass_network_base(network_base: pd.DataFrame):
    formation_uses_df = T2Data.get_formation_use_df()
    network_dfs = []
    for match_id, gdf in network_base.groupby("wh_match_id"):
        melted_formations = get_melted_formations(match_id, formation_uses_df)
        network_dfs.append(
            gdf.merge(
                melted_formations.rename(columns={"value": "source_player"}), how="left"
            )
            .loc[_filter_for_past]
            .rename(columns={"variable": "source_formation_slot"})
            .merge(
                melted_formations.rename(columns={"value": "target_player"}),
                how="left",
            )
            .rename(columns={"variable": "target_formation_slot"})
            .loc[_filter_for_past]
            .sort_values(["period", "end_minute"])
            .drop_duplicates(subset=["event_side", "eventid"], keep="first")
            .pipe(
                lambda df: df.assign(
                    **{
                        col: df.loc[:, col].fillna("no_target")
                        for col in df.columns
                        if col.startswith("target_")
                    }
                )
            )
        )
    return pd.concat(network_dfs)


def add_chains(df):
    return pd.concat(
        [
            get_chains(gdf)
            for _, gdf in gdf.groupby(["wh_match_id", "period", "event_side"])
        ]
    )


def create_pass_data(season_id):
    return (
        get_season_events(season_id)
        .pipe(transform_event_data_to_pass_data)
        .pipe(transform_passes_to_network_base)
        .pipe(extend_pass_network_base)
        .pipe(add_chains)
    )


def export_raw_passes(wrapper=lambda x: x):
    os.makedirs(pass_dir, exist_ok=True)
    season_df = T2Data.get_wh_season_df()
    for season_id in wrapper(season_df["wh_season_id"]):
        create_pass_data(season_id).to_parquet(
            os.path.join(pass_dir, f"passes-{season_id}.parquet")
        )


def load_season_passes(season_id: str):
    return pd.read_parquet(os.path.join(pass_dir, f"passes-{season_id}.parquet"))


def load_all_passes() -> pd.DataFrame:
    files = glob.glob(os.path.join(pass_dir, "passes-*.parquet"))
    return reduce(reduce_append, files)


export_pass_data_pe = PipelineElement(
    name="export_raw_pass_data",
    runner=export_raw_passes,
    output_path=pass_dir,
    param_list=["seed"],
    dependency_list=[run_pass_model_pe],
)

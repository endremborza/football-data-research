import glob
import itertools
import os
from functools import reduce

import numpy as np
import pandas as pd

from src.data_loaders import T2Data, get_season_events, reduce_append
from src.dvc_util import PipelineElement
from src.pass_success_model.prepare_data_for_modelling import (
    AddCodes,
    bool_quals,
    num_vals,
    target,
    transform_event_data_to_pass_data,
    transform_pass_data_to_model_data,
)
from src.pass_success_model.run_pass_success_model import (
    load_trained_model,
    run_pass_model_pe,
)

network_dir = os.path.join("data", "networks")


x_field_bins = [-1, 33.3, 66.6, 101]
y_field_bins = x_field_bins

categ_vals = ["period", "pass_direction_cat", "predicted_success_bin"] + [
    side + "_" + var
    for side, var in itertools.product(
        ["source", "target"], ["field_zone", "formation_slot"]
    )
]
network_types = ["field_zone", "player", "formation_slot"]
all_num_vals = num_vals + ["predicted_success_probability"]


def rename_encoded_cols(colname):
    for idx, cat_col in enumerate(categ_vals):
        start_str = f"x{idx}_"
        if colname.startswith(start_str):
            return colname.replace(start_str, f"cat__{cat_col}__")
    return colname


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


def create_aggregate_network(extended_network_base: pd.DataFrame):
    final_dfs = []
    for match_id, gdf in extended_network_base.groupby("wh_match_id"):
        merged_df_transformed = (
            pd.concat(
                [
                    gdf.reindex([*bool_quals, target], axis=1).fillna(0),
                    gdf.loc[:, all_num_vals + categ_vals],
                ],
                axis=1,
            )
            .pipe(AddCodes(categ_vals).fit_transform)
            .assign(total=1)
            .rename(columns=rename_encoded_cols)
        )

        for cat_type in network_types:
            current_endpoints = [f"{s}_{cat_type}" for s in ["source", "target"]]

            final_dfs.append(
                merged_df_transformed.assign(
                    formation=gdf["formation_name"],
                    side=gdf["event_side"],
                    **{endp.split("_")[0]: gdf[endp] for endp in current_endpoints},
                )
                .groupby(["side", "source", "target", "formation"])
                .agg(
                    {
                        **{
                            c: "sum"
                            for c in merged_df_transformed.columns
                            if c not in all_num_vals
                        },
                        **{c: "mean" for c in all_num_vals},
                    }
                )
                .reset_index()
                .assign(wh_match_id=match_id, network_type=cat_type)
            )

    return pd.concat(final_dfs).fillna(0)


def create_season_networks(season_id: str) -> pd.DataFrame:
    return (
        get_season_events(season_id)
        .pipe(transform_event_data_to_pass_data)
        .pipe(transform_passes_to_network_base)
        .pipe(extend_pass_network_base)
        .pipe(create_aggregate_network)
        .assign(
            source=lambda df: df["source"].astype(str),
            target=lambda df: df["target"].astype(str),
        )  # TODO
    )


def export_all_networks(wrapper=lambda x: x):
    os.makedirs(network_dir, exist_ok=True)
    season_df = T2Data.get_wh_season_df()
    for season_id in wrapper(season_df["wh_season_id"]):
        try:
            create_season_networks(season_id).to_parquet(
                os.path.join(network_dir, f"network-{season_id}.parquet")
            )
        except KeyError as e:
            print(season_id, e)


def load_season_network(season_id: str):
    return pd.read_parquet(os.path.join(network_dir, f"network-{season_id}.parquet"))


def load_entire_network() -> pd.DataFrame:
    files = glob.glob(os.path.join(network_dir, f"network-*.parquet"))
    return reduce(reduce_append, files)


create_network_pe = PipelineElement(
    name="create_match_networks",
    runner=export_all_networks,
    output_path=network_dir,
    param_list=["seed"],
    dependency_list=[run_pass_model_pe],
)

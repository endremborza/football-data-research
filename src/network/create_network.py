import glob
import itertools
import os
from functools import reduce

import pandas as pd

from src.data_loaders import T2Data, reduce_append
from src.dvc_util import PipelineElement
from src.pass_success_model.prepare_data_for_modelling import (
    AddCodes,
    bool_quals,
    num_vals,
    target,
)
from .create_raw_pass_data import export_pass_data_pe, load_season_passes

network_dir = os.path.join("data", "networks")

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
        load_season_passes(season_id)
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
        create_season_networks(season_id).to_parquet(
            os.path.join(network_dir, f"network-{season_id}.parquet")
        )


def load_season_network(season_id: str):
    return pd.read_parquet(os.path.join(network_dir, f"network-{season_id}.parquet"))


def load_entire_network() -> pd.DataFrame:
    files = glob.glob(os.path.join(network_dir, "network-*.parquet"))
    return reduce(reduce_append, files)


create_network_pe = PipelineElement(
    name="create_match_networks",
    runner=export_all_networks,
    output_path=network_dir,
    param_list=["seed"],
    dependency_list=[export_pass_data_pe],
)

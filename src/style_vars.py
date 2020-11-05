import glob
import os
from functools import reduce
from operator import truediv

import pandas as pd
import numpy as np

from .data_loaders import T2Data
from .create_network import load_season_network

style_data_dir = os.path.join("data", "style")

cats_for_gini = [
    "source_field_zone",
    "source_formation_slot",
    "target_field_zone",
    "target_formation_slot",
    "predicted_success_bin",
    "pass_direction_cat",
]


def get_gini_for_rows(x):
    return (
        np.abs(x[:, :, np.newaxis] - x[:, np.newaxis]).mean(axis=(-1, -2))
        / x.mean(axis=1)
        / 2
    )


def get_coeffs(df):
    return pd.DataFrame(
        {
            gini_cat: df.loc[
                :,
                df.columns.str.startswith(f"cat__{gini_cat}")
                & ~df.columns.str.endswith("no_target"),
            ].pipe(lambda _df: get_gini_for_rows(_df.values))
            for gini_cat in cats_for_gini
        },
        index=df.index,
    )


def inner_gb(df):
    return df.groupby(["network_type", "edge_end", "side", "wh_match_id"]).sum()


def weighted_average_ginis(edge_end_ginis):

    weighed_cols = ["predicted_success_probability", *cats_for_gini]
    p_weights = edge_end_ginis.pipe(
        lambda df: pd.DataFrame(
            {
                c: np.where(
                    df.reset_index()["edge_end"] == "target",
                    df["is_success"].values,
                    df["total"].values,
                )
                if not c.startswith("target")
                else df["is_success"]
                for c in weighed_cols
            }
        )
    )

    return reduce(
        truediv,
        map(inner_gb, (p_weights * edge_end_ginis.loc[:, weighed_cols], p_weights),),
    ).join(edge_end_ginis.drop(weighed_cols, axis=1).pipe(inner_gb))


def get_edge_end_ginis(network_df):
    return (
        network_df.pipe(
            lambda df: pd.concat(
                [
                    df.rename(columns={"source": "end1", "target": "end2"}).assign(
                        edge_end="source"
                    ),
                    df.rename(columns={"source": "end2", "target": "end1"}).assign(
                        edge_end="target"
                    ),
                ]
            )
        )
        .groupby(
            ["network_type", "edge_end", "wh_match_id", "side", "end1", "formation"]
        )
        .sum()
        .drop("player")
        .assign(
            is_success=lambda df: df["total"]
            - df["cat__target_formation_slot__no_target"],
            predicted_success_probability=lambda df: df["total"]
            * df["predicted_success_probability"],
        )
        .pipe(
            lambda df: pd.concat(
                [
                    df.loc[
                        :, ["total", "is_success", "predicted_success_probability"]
                    ].assign(
                        predicted_success_probability=lambda _df: _df[
                            "predicted_success_probability"
                        ]
                        / _df["total"]
                    ),
                    get_coeffs(df),
                ],
                axis=1,
            )
        )
    )


def get_style_vars(edge_end_ginis: pd.DataFrame):
    return (
        edge_end_ginis.pipe(
            lambda df: weighted_average_ginis(df)
            .join(
                (
                    df.groupby(
                        ["network_type", "edge_end", "side", "wh_match_id", "formation"]
                    )["total"].sum()
                    / df.groupby(["network_type", "edge_end", "side", "wh_match_id"])[
                        "total"
                    ].sum()
                )
                .to_frame()
                .pivot_table(
                    index=["network_type", "edge_end", "side", "wh_match_id"],
                    columns="formation",
                    values="total",
                )
            )
            .fillna(0)
        )
        .assign(rate=lambda df: df["is_success"] / df["total"])
        .reset_index()
        .pipe(
            lambda df: pd.concat(
                [
                    df.assign(perspective="self"),
                    df.assign(
                        perspective="opposition",
                        side=np.where(df["side"] == "home", "away", "home"),
                    ),
                ]
            )
        )
        .pipe(
            lambda df: df.pivot_table(
                index=["wh_match_id", "side"],
                columns=["perspective", "network_type", "edge_end"],
                values=cats_for_gini,
            ).join(
                df.drop(cats_for_gini, axis=1).pivot_table(
                    index=["wh_match_id", "side"], columns="perspective"
                )
            )
        )
    )


def export_all_style(wrapper=lambda x: x):
    os.makedirs(style_data_dir, exist_ok=True)
    season_df = T2Data.get_wh_season_df()
    for season_id in wrapper(season_df["wh_season_id"]):
        try:
            network_df = load_season_network(season_id)
        except OSError:
            continue
        network_df.pipe(get_edge_end_ginis).pipe(get_style_vars).rename(
            columns=lambda x: "___".join(x)
        ).to_parquet(os.path.join(style_data_dir, f"{season_id}.parquet"))


def load_style_df(season_id: str):
    return pd.read_parquet(os.path.join(style_data_dir, f"{season_id}.parquet"))


def load_all_style_data() -> pd.DataFrame:
    return pd.concat(
        [
            pd.read_parquet(f)
            for f in glob.glob(os.path.join(style_data_dir, f"*.parquet"))
        ]
    ).fillna(0)

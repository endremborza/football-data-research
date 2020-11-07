import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from src.dvc_util import PipelineElement
from src.network.create_network import load_entire_network
from src.data_loaders import T2Data
from src.style.create_style_vars import (
    load_all_style_data,
    get_gini_for_rows,
    create_style_data_pe,
)

style_report_dir = os.path.join("reports", "style")

style_pair_renamer = {
    "rate___self": "pass success rate",
    "target_formation_slot___opposition___field_zone___source": "opposition rigidity",
}


def dump_heatmap(us_match_df: pd.DataFrame, style_df: pd.DataFrame):

    rel_matchups = (
        us_match_df.join(style_df)
        .rename(columns=style_pair_renamer)
        .loc[:, ["win", *style_pair_renamer.values()]]
    )
    style_pair_vals = list(style_pair_renamer.values())

    rel_matchups[["win"]].join(
        rel_matchups.loc[:, style_pair_vals].apply(pd.qcut, q=4)
    ).assign(c=1).groupby(style_pair_vals).sum().reset_index().pivot_table(
        index=style_pair_vals[0], columns=style_pair_vals[1], values=["win", "c"]
    ).pipe(
        lambda df: sns.heatmap(
            df["win"] / df["c"],
            annot=(
                "matches: "
                + df["c"].astype(str)
                + "\nwin rate: "
                + (df["win"] / df["c"]).round(2).astype(str)
            ).values,
            fmt="",
        )
    )
    plt.tight_layout()
    plt.savefig(os.path.join(style_report_dir, "heatmap.png"))
    return (
        rel_matchups.groupby("wh_match_id")
        .std()
        .drop("win", axis=1)
        .prod(axis=1)
        .sort_values()
        .index[-4]
    )


def export_style_report():
    plt.rcParams["figure.figsize"] = (14, 14)
    os.makedirs(style_report_dir, exist_ok=True)

    simple_matches = T2Data.get_simplified_wh_matches()
    us_match_df = T2Data.get_unstacked_match_df()
    style_df = load_all_style_data()
    match_id = dump_heatmap(us_match_df, style_df)

    simple_matches.set_index("wh_match_id").loc[[match_id], :].reset_index().to_html(
        os.path.join(style_report_dir, "simple_match_sample.html")
    )

    match_network_df = load_entire_network().loc[
        lambda df: (df["wh_match_id"] == match_id)
        & (df["network_type"] == "field_zone")
    ]

    prefix = "cat__target_formation_slot__"

    df_for_style = (
        match_network_df.loc[
            :,
            lambda df: df.columns.str.startswith(prefix)
            | df.columns.isin(
                ["source", "target", "side", "total", "formation", "is_success"]
            ),
        ]
        .rename(columns=lambda s: s.replace(prefix, "targeted_"))
        .drop("targeted_no_target", axis=1)
        .groupby(["side", "source", "formation"])
        .sum()
        .assign(
            gini=lambda df: df.drop(["total", "is_success"], axis=1).pipe(
                lambda v: get_gini_for_rows(v.values)
            )
        )
    )

    df_for_style.reset_index().to_html(
        os.path.join(style_report_dir, "style_table.html")
    )

    df_for_style.assign(
        prod=lambda df: df[["is_success", "gini"]].prod(axis=1)
    ).groupby("side").sum().assign(
        **{
            "weighted means of ginis --> rigidity": lambda df: df["prod"]
            / df["is_success"].values,
            "pass success rate": lambda df: df["is_success"] / df["total"].values,
        }
    ).iloc[
        :, -2:
    ].reset_index().to_html(
        os.path.join(style_report_dir, "simple_result.html")
    )


report_style_pe = PipelineElement(
    name="report_style",
    runner=export_style_report,
    output_path=style_report_dir,
    param_list=["seed"],
    dependency_list=[create_style_data_pe],
)

import os
import pandas as pd
import seaborn as sns
import statsmodels.api as sm
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
    "source_field_zone___opposition___formation_slot___target": "opposition rigidity",
}
style_pair_vals = list(style_pair_renamer.values())


def _make_fp(fp_str):
    return os.path.join(style_report_dir, fp_str)


class ExportedFiles:
    heatmap = _make_fp("heatmap.png")
    source_example = _make_fp("style_table.html")
    all_ginis = _make_fp("all_ginis.html")
    result_of_sample_match = _make_fp("result_of_sample_match.html")
    style_agged = _make_fp("match_styles.html")

    under_probit = _make_fp("under_probit.html")
    over_probit = _make_fp("over_probit.html")


def get_rel_matchups(us_match_df: pd.DataFrame, style_df: pd.DataFrame):
    return (
        us_match_df.join(style_df)
        .rename(columns=style_pair_renamer)
        .loc[:, ["win", *style_pair_renamer.values()]]
    )


def dump_probit_results(rel_matchups):
    break_q = 0.66
    filenames = {True: ExportedFiles.over_probit, False: ExportedFiles.under_probit}

    for gid, gdf in rel_matchups.groupby(
        rel_matchups[style_pair_vals[0]].pipe(lambda s: s > s.quantile(break_q))
    ):
        html_str = (
            sm.Probit(gdf["win"], gdf[style_pair_vals[1:]].assign(const=1))
            .fit(cov_type="HC1")
            .summary()
            .tables[1]
            .as_html()
        )
        with open(filenames[gid], "w") as fp:
            fp.write(html_str)


def dump_heatmap(rel_matchups: pd.DataFrame):

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
    plt.savefig(ExportedFiles.heatmap)
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
    rel_matchups = get_rel_matchups(us_match_df, style_df)
    match_id = dump_heatmap(rel_matchups)
    dump_probit_results(rel_matchups)

    simple_matches.set_index("wh_match_id").loc[[match_id], :].reset_index().to_html(
        ExportedFiles.result_of_sample_match
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
        .rename(columns=lambda s: s.replace(prefix, ""))
        .drop("unknown_target", axis=1)
        .groupby(["side", "source", "formation"])
        .sum()
        .assign(
            gini=lambda df: df.drop(["total", "is_success"], axis=1).pipe(
                lambda v: get_gini_for_rows(v.values)
            )
        )
    )

    df_for_style.loc[lambda df: df["is_success"] > 13].iloc[[3], :].loc[
        :, lambda df: df.columns.str.startswith("spot")
    ].reset_index("source").reset_index(drop=True).melt(id_vars=["source"]).rename(
        columns={"variable": "target", "value": "successful passes"}
    ).to_html(
        ExportedFiles.source_example
    )

    df_for_style[["is_success", "gini"]].reset_index().to_html(ExportedFiles.all_ginis)

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
        ExportedFiles.style_agged
    )


report_style_pe = PipelineElement(
    name="report_style",
    runner=export_style_report,
    output_path=style_report_dir,
    param_list=["seed"],
    dependency_list=[create_style_data_pe],
)

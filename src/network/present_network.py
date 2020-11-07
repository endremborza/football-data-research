import os

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd

from src.data_loaders import T2Data
from src.dvc_util import PipelineElement
from src.network.create_network import create_network_pe, load_entire_network

network_plot_dir = os.path.join("reports", "network_plots")


def fix_no_target(gdf):
    return pd.concat(
        [
            gdf,
            gdf.loc[lambda df: df["target"] == "no_target"].assign(
                x=lambda df: df["passendx"],
                y=lambda df: df["passendy"],
                source=lambda df: df["target"],
            ),
        ]
    )


def get_pos_dict(nw_df, bg_img):
    return (
        nw_df.pipe(fix_no_target)
        .assign(
            sumx=lambda df: df["x"] * df["total"], sumy=lambda df: df["y"] * df["total"]
        )
        .groupby("source")[["total", "sumx", "sumy"]]
        .sum()
        .pipe(
            lambda df: df[["sumx", "sumy"]]
            / df[["total"]].values
            / 100
            * bg_img.shape[:2][::-1]
        )
        .T.to_dict("list")
    )


def rename_nodes(df, players):
    return df.assign(
        **{
            side: players.reindex(df[side]).pipe(
                lambda s: np.where(s.isna(), df[side], s.values)
            )
            for side in ["source", "target"]
        }
    )


def plot_nw_df(gdf, poses, gid, bg_img):
    graph = nx.from_pandas_edgelist(gdf, edge_attr="total", create_using=nx.DiGraph())
    plt_title = (
        f"{gid[0]} level graph of {gid[2]} team playing in {gid[3]} "
        f"formation from {gid[4]} {gid[6]} {gid[5]} ({gid[-2]})"
    )

    plt_id = "-".join(gid[:4])

    fig, ax = plt.subplots()
    ax.imshow(bg_img)
    nx.draw_networkx(
        graph,
        pos=poses,
        ax=ax,
        font_size=15,
        node_size=1100,
        font_color="w",
        width=gdf["total"].pipe(np.log).values,
        arrowsize=15,
        connectionstyle="arc3,rad=0.1",
    )
    plt.title(plt_title)
    plt.tight_layout()
    plt.savefig(
        os.path.join(network_plot_dir, f"{plt_id}.svg"), bbox_inches=0, transparent=True
    )


def plot_top_networks():
    os.makedirs(network_plot_dir, exist_ok=True)
    bg_img = plt.imread("football-field.jpg")
    fig_h = 9
    plt.rcParams["figure.figsize"] = (fig_h * bg_img.shape[1] / bg_img.shape[0], fig_h)
    plt.rcParams['axes.titlesize'] = 16

    match_df = T2Data.get_simplified_wh_matches()
    network_df = load_entire_network()
    players = (
        T2Data.get_wh_player_df()
        .assign(ind=lambda df: df["playerId"].astype(float).astype(str))
        .set_index("ind")
    )["name"]

    gb_cols = ["network_type", "wh_match_id", "side", "formation"]
    top_networks = (
        network_df.groupby(gb_cols)[["total"]]
        .sum()
        .sort_values("total", ascending=False)
        .reset_index()
        .drop_duplicates(subset=["network_type", "formation"])
        .head(network_df["network_type"].nunique() * 2)
        .drop("total", axis=1)
        .merge(match_df)
        .merge(network_df)
        .pipe(rename_nodes, players)
        .loc[lambda df: df["target"] != "no_target"]
    )

    full_gb_cols = [*gb_cols, *match_df.columns]

    for gid, gdf in top_networks.groupby(full_gb_cols):
        poses = get_pos_dict(gdf, bg_img)
        plot_nw_df(gdf, poses, gid, bg_img)


plot_network_pe = PipelineElement(
    name="plot_networks",
    runner=plot_top_networks,
    output_path=network_plot_dir,
    param_list=["seed"],
    dependency_list=[create_network_pe, "src/network/present_network.py"],
)

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from .export_app_data import edge_ends, loc_cols


def get_network_figure(network_df):

    edge_list = (
        network_df.groupby(edge_ends)
        .agg({c: ["count", "sum", "std"] for c in loc_cols})
        .compute()
    )

    _cols1 = loc_cols[:2]
    _cols2 = loc_cols[2:]

    node_locs = (
        pd.concat(
            [
                edge_list[_cols]
                .groupby(level=i)
                .sum()
                .rename(columns=dict(zip(_cols2, _cols1)))
                for i, _cols in enumerate([_cols1, _cols2])
            ]
        )
        .groupby(level=0)
        .sum()
        .pipe(
            lambda df: {
                k: v.values
                for k, v in (
                    df.loc[:, (slice(None), "sum")]
                    / df.loc[:, (slice(None), "count")].values
                ).iterrows()
            }
        )
    )

    edge_traces = []
    annotations = []

    for (source, target), w in (
        edge_list[(loc_cols[0], "count")]
        .pipe(lambda s: s / s.max() * 4 + 1)
        .iteritems()
    ):
        if source == target:
            continue

        etrace, annot = get_edge_trace_w_annot(source, target, w, node_locs)

        edge_traces.append(etrace)
        annotations.append(annot)

    node_trace = get_node_trace(node_locs, edge_list)

    fig = go.Figure(
        data=[node_trace, *edge_traces],
        layout=go.Layout(
            # title='Pass nw',
            height=800,
            # width=1500,
            titlefont_size=16,
            showlegend=False,
            hovermode="closest",
            margin=dict(b=20, l=5, r=5, t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            annotations=annotations,
        ),
    )

    decorate_fig(fig)

    return fig


def get_edge_trace_w_annot(source, target, w, node_locs):
    x1, y1 = node_locs.get(source)
    x2, y2 = node_locs.get(target)

    dir_vec = np.array([(x2 - x1), (y2 - y1)])
    ort_vec = np.array([-dir_vec[1], dir_vec[0]])
    midpoint = np.array([(x2 + x1), (y2 + y1)]) / 2
    xm, ym = midpoint + ort_vec / np.linalg.norm(dir_vec) * 2

    xma, yma = np.array([xm, ym]) - (dir_vec / np.linalg.norm(dir_vec)) * 2

    return (
        go.Scatter(
            x=[x1, xm, x2],
            y=[y1, ym, y2],
            line=dict(width=w, color="#888"),
            hoverinfo="none",  # str(row),
            mode="lines",
            line_shape="spline",
        ),
        dict(
            ax=xma,
            ay=yma,
            axref="x",
            ayref="y",
            x=xm,
            y=ym,
            xref="x",
            yref="y",
            showarrow=True,
            arrowhead=3,
            arrowsize=1.5,
            arrowwidth=1.5,
            arrowcolor="black",
        ),
    )


def get_node_trace(node_locs, edge_list):
    node_x = []
    node_y = []
    hovertext = []

    for node_name, (x, y) in node_locs.items():
        node_x.append(x)
        node_y.append(y)
        hovertext.append(get_htext(node_name, edge_list))

    return go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers",
        hovertext=hovertext,
        hoverinfo="text",
        text=list(node_locs.keys()),
        marker=dict(
            # showscale=True,
            color=["blue" for n in node_locs.keys()],  # TODO better
            size=20,
            line_width=2,
        ),
    )


def get_htext(n, edge_list):
    htext = f"<b>{n}</b><br><br>"
    for side, head, inder in zip(
        [1, 0], ["out-edges", "in-edges"], [(n, slice(None)), (slice(None), n)]
    ):
        try:
            toadd = [f"<b>{head}:</b><br>"]
            for n2, c in (
                edge_list.loc[inder, (slice(None), "count")]
                .reset_index()
                .iloc[:, [side, 2]]
                .values
            ):
                toadd.append(f"{n2}: {c}<br>")
            htext += "".join(toadd)
        except KeyError:
            pass
    return htext


def decorate_fig(fig):

    fig.update_yaxes(range=[0, 100])
    fig.update_xaxes(range=[0, 100])

    fig.add_layout_image(
        dict(
            source="https://endremborza.github.io/football-data-research/football-field.jpg",
            xref="x",
            yref="y",
            x=0,
            y=100,
            sizex=100,
            sizey=100,
            sizing="stretch",
            opacity=0.5,
            layer="below",
        )
    )

    fig.update_layout(template="plotly_white")

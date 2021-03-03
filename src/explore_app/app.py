"""
Todo:

pretty UX plan

save button + comment

add deselect all button

additional filters:
  - match level / half level data
    - rate of consecutive
  - filter to matches

additional info to graphs:
  - style metrics
  - top triads / diads

some pattern detection in remaining data
  - isolation forest ?

"""

import numpy as np
import pandas as pd


import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go


from .export_app_data import (
    load_entire_app_data,
    loc_cols,
    app_discrete_cols,
    edge_ends,
)


bt_root = "https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/"

external_stylesheets = [
    "https://codepen.io/chriddyp/pen/bWLwgP.css",
    f"{bt_root}css/bootstrap.min.css",
    f"{bt_root}css/bootstrap-theme.min.css",
    "https://use.fontawesome.com/releases/v5.7.2/css/all.css",
]

external_scripts = [f"{bt_root}js/bootstrap.min.js"]


def get_network_figure(network_df):

    edge_list = network_df.groupby(edge_ends).agg(
        {app_discrete_cols[0]: "count", **{c: ["mean", "std"] for c in loc_cols}}
    )

    source_nodes = (
        network_df.groupby(edge_ends[0])[loc_cols[:2]].mean().to_dict("index")
    )
    # target_nodes = (
    #    network_df.groupby(edge_ends[1])[loc_cols[2:]].mean().to_dict("index")
    # )

    _lcols = [edge_ends[0], *loc_cols[:2]]
    _tcols = [edge_ends[1], *loc_cols[2:]]
    node_locs = (
        pd.concat(
            [
                network_df.loc[:, _lcols],
                network_df.loc[:, _tcols].rename(columns=dict(zip(_tcols, _lcols))),
            ]
        )
        .groupby(_lcols[0])
        .mean()
        .pipe(lambda df: {k: v.values for k, v in df.iterrows()})
    )

    edge_traces = []
    annotations = []

    for (source, target), w in (
        edge_list[(app_discrete_cols[0], "count")]
        .pipe(lambda s: s / s.max() * 4 + 1)
        .iteritems()
    ):
        if source == target:
            continue

        etrace, annot = get_edge_trace_w_annot(source, target, w, node_locs)

        edge_traces.append(etrace)
        annotations.append(annot)

    node_trace = get_node_trace(node_locs, source_nodes, edge_list)

    fig = go.Figure(
        data=[node_trace, *edge_traces],
        layout=go.Layout(
            # title='Pass nw',
            height=900,
            width=1500,
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


def get_triads(network_df, top_n=10):
    last_ind = "prev_pass_id"
    chan_ind_col = "n_in_chain"
    triads = (
        network_df.loc[lambda df: df[chan_ind_col] > 1, [*edge_ends, last_ind]]
        .assign(
            root_source=lambda df: network_df.reindex(df.loc[:, last_ind])
            .loc[:, edge_ends[0]]
            .values
        )
        .dropna()
        .drop(last_ind, axis=1)
        .sort_index(axis=1)
    )

    return triads.pipe(_iadagg, triads.columns.tolist()[:3], top_n)


def get_diads(network_df, top_n=10):
    return network_df.loc[lambda df: df["is_success"].astype(bool)].pipe(
        _iadagg, edge_ends, top_n
    )


def _iadagg(df, cols, top_n):
    return (
        df.assign(count=1)
        .groupby(cols)[["count"]]
        .sum()
        .assign(rate=lambda df: df["count"] / df["count"].sum())
        .nlargest(top_n, "count")
    )


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


def get_node_trace(node_locs, source_nodes, edge_list):
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
            color=[
                "blue" if n in source_nodes.keys() else "red" for n in node_locs.keys()
            ],
            size=20,
            line_width=2,
        ),
    )


def _iad_num(x):
    if isinstance(x, float) and x < 1:
        return "{:.2f}%".format(x * 100)
    return x


def get_iad_table(iads):
    rows = [html.Tr([html.Th(c) for c in ["motif", *iads.columns]])]
    for ind, r in iads.iterrows():
        siad = " -> ".join(ind)
        rows.append(html.Tr([html.Td(_iad_num(e)) for e in [siad, *r]]))
    return html.Table(rows)


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


def get_app():
    app_data = load_entire_app_data()

    app = dash.Dash(
        __name__,
        external_stylesheets=external_stylesheets,
        external_scripts=external_scripts,
        # suppress_callback_exceptions=True
    )

    chl_cols = app_data.loc[:, app_discrete_cols].nunique().sort_values().index.tolist()

    chlists = []
    for c in chl_cols:
        vals = app_data[c].drop_duplicates().tolist()

        clear_id = f"clear-{c}"
        chlist_id = f"cat-checklist-{c}"
        chlist = dcc.Checklist(
            id=chlist_id,
            options=[{"label": v, "value": v} for v in sorted(vals)],
            value=vals,
            labelStyle={"margin": 3},
            inputStyle={"margin": 3},
        )
        clear_but = html.Button("Toggle", id=clear_id)

        chlists.append(
            html.Div(
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(
                                    html.H4(c.replace("_", " ").title()),
                                    className="col-md-6",
                                ),
                                html.Div(clear_but, className="col-md-6"),
                            ],
                            className="row",
                        ),
                        chlist,
                        html.Hr(),
                    ],
                ),
                className="col-md-12",
                style={"padding": 7},
            )
        )

        @app.callback(
            Output(chlist_id, "value"),
            Input(clear_id, "n_clicks"),
            State(chlist_id, "options"),
            prevent_initial_call=True,
        )
        def toggle_chl(n, vals):
            if n % 2 == 0:
                return [o["value"] for o in vals]
            else:
                return []

    filter_elems = chlists
    figure_elems = [
        html.Div([dcc.Graph(id="graph-fig-1")], className="row"),
        html.Div(id="cat-bars", className="row"),
        html.Div(id="iads", className="row"),
    ]

    app.layout = html.Div(
        html.Div(
            [
                html.Div(filter_elems, className="col-md-2"),
                html.Div(figure_elems, className="col-md-10"),
            ],
            className="row",
        ),
        style={"padding": 20},
        className="container-fluid",
    )

    @app.callback(
        Output("graph-fig-1", "figure"),
        Output(
            "cat-bars",
            "children",
        ),
        Output(
            "iads",
            "children",
        ),
        *[
            Input(
                f"cat-checklist-{c}",
                "value",
            )
            for c in chl_cols
        ],
    )
    def filt(*chvals):

        import time
        stime = time.time()

        filt_arr = np.array([True] * app_data.shape[0])
        for c, vals in zip(chl_cols, chvals):
            filt_arr &= app_data.loc[:, c].isin(vals)
        filted_df = app_data.loc[filt_arr, :]

        fig = get_network_figure(filted_df)

        bars = []
        for c in chl_cols:
            vcounts = filted_df.loc[:, c].value_counts()
            bars.append(
                dcc.Graph(
                    figure=go.Figure(
                        data=[
                            go.Bar(
                                y=vcounts.index.tolist(),
                                x=vcounts.tolist(),
                                orientation="h",
                            ),
                        ],
                        layout=go.Layout(title=c.replace("_", " ").title()),
                    ),
                    className="col-md-3",
                )
            )

        iads = [
            html.Div(
                [html.H3("Diads"), get_iad_table(get_diads(filted_df))],
                className="col-md-6",
            ),
            html.Div(
                [html.H3("Triads"), get_iad_table(get_triads(filted_df))],
                className="col-md-6",
            ),
        ]

        print("CALCTIME: ", time.time() - stime)

        return fig, html.Div(bars, className="row"), iads

    return app

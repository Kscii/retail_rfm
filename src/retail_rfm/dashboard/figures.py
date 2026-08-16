from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .theme import SEGMENT_COLORS, TOKENS


GRAPH_CONFIG = {
    "displaylogo": False,
    "displayModeBar": False,
    "responsive": True,
    "modeBarButtonsToRemove": ["lasso2d", "select2d"],
}


def _base_layout(figure: go.Figure, height: int = 400, margin: dict | None = None) -> go.Figure:
    figure.update_layout(
        height=height,
        margin=margin or {"l": 48, "r": 24, "t": 35, "b": 46},
        paper_bgcolor=TOKENS["surface"],
        plot_bgcolor=TOKENS["surface"],
        font={"family": TOKENS["font_family"], "color": TOKENS["ink"], "size": 12},
        hoverlabel={"font": {"family": TOKENS["font_family"], "size": 8}, "align": "left"},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "x": 0},
    )
    figure.update_xaxes(showgrid=True, gridcolor="#E8EDF3", zeroline=False)
    figure.update_yaxes(showgrid=True, gridcolor="#E8EDF3", zeroline=False)
    return figure


def overview_share_figure(profiles: pd.DataFrame) -> go.Figure:
    figure = go.Figure()
    for row in profiles.sort_values("segment_order").itertuples():
        figure.add_bar(
            name=row.segment_code,
            y=["Customers", "Observed Net value"],
            x=[row.customer_share * 100, row.net_monetary_share * 100],
            orientation="h",
            marker_color=SEGMENT_COLORS[row.segment_code],
            text=[f"{row.customer_share:.1%}", f"{row.net_monetary_share:.1%}"],
            textposition="inside",
            insidetextanchor="middle",
            hovertemplate=(
                f"<b>{row.segment_code} · {row.segment_name}</b><br>"
                "%{y}: %{x:.2f}%<extra></extra>"
            ),
        )
    figure.update_layout(barmode="stack", barnorm=None)
    figure.update_xaxes(range=[0, 100], ticksuffix="%", title=None)
    figure.update_yaxes(autorange="reversed", title=None)
    return _base_layout(figure, height=315, margin={"l": 128, "r": 18, "t": 45, "b": 42})


def _customer_customdata(frame: pd.DataFrame) -> np.ndarray:
    return np.column_stack(
        [
            frame["customer_id"].astype(str),
            frame["country_display"].astype(str),
            frame["recency"],
            frame["frequency"],
            frame["net_monetary"],
            frame["any_capped_flag"].map({0: "No", 1: "Yes"}),
        ]
    )


CUSTOMER_HOVER = (
    "<b>Customer %{customdata[0]}</b><br>"
    "%{customdata[1]}<br>"
    "Recency: %{customdata[2]} days<br>"
    "Frequency: %{customdata[3]} orders<br>"
    "Observed Net value: £%{customdata[4]:,.2f}<br>"
    "Touches cap: %{customdata[5]}<extra></extra>"
)


def rfm_3d_figure(customers: pd.DataFrame, centroids: pd.DataFrame) -> go.Figure:
    figure = go.Figure()
    for segment_code in ("S1", "S2", "S3", "S4"):
        segment = customers.loc[customers["segment_code"].eq(segment_code)]
        for capped, label, size, opacity in ((0, segment_code, 4, 0.60), (1, f"{segment_code} · capped", 7, 0.92)):
            points = segment.loc[segment["any_capped_flag"].eq(capped)]
            if points.empty:
                continue
            figure.add_trace(
                go.Scatter3d(
                    x=points["scaled_recency"],
                    y=points["scaled_frequency"],
                    z=points["scaled_net_monetary"],
                    mode="markers",
                    name=label,
                    legendgroup=segment_code,
                    showlegend=capped == 0,
                    ids=points["customer_id"].astype(str),
                    customdata=_customer_customdata(points),
                    hovertemplate=CUSTOMER_HOVER,
                    marker={
                        "size": size,
                        "color": SEGMENT_COLORS[segment_code],
                        "opacity": opacity,
                        "line": {
                            "color": TOKENS["cap"] if capped else SEGMENT_COLORS[segment_code],
                            "width": 2 if capped else 0,
                        },
                    },
                )
            )
    selected_segments = set(customers["segment_code"].unique())
    centers = centroids.loc[centroids["segment_code"].isin(selected_segments)]
    figure.add_trace(
        go.Scatter3d(
            x=centers["scaled_recency"],
            y=centers["scaled_frequency"],
            z=centers["scaled_net_monetary"],
            mode="markers+text",
            name="Centroids",
            text=centers["segment_code"],
            textposition="top center",
            hovertemplate=(
                "<b>%{text} centroid</b><br>"
                "Scaled R: %{x:.2f}<br>Scaled capped F: %{y:.2f}<br>"
                "Scaled capped Net M: %{z:.2f}<extra></extra>"
            ),
            marker={"size": 6, "symbol": "diamond", "color": TOKENS["ink"], "line": {"color": "white", "width": 1.5}},
        )
    )
    figure.update_layout(
        height=510,
        margin={"l": 0, "r": 0, "t": 18, "b": 0},
        paper_bgcolor=TOKENS["surface"],
        font={"family": TOKENS["font_family"], "color": TOKENS["ink"]},
        hoverlabel={"font": {"family": TOKENS["font_family"], "size": 8}, "align": "left"},
        legend={"orientation": "h", "x": 0.02, "y": 0.98, "bgcolor": "rgba(255,255,255,.78)"},
        scene={
            "xaxis_title": "Scaled Recency",
            "yaxis_title": "Scaled capped Frequency",
            "zaxis_title": "Scaled capped Net value",
            "bgcolor": "#FFFFFF",
            "xaxis": {"gridcolor": "#E2E8F0", "zerolinecolor": "#94A3B8"},
            "yaxis": {"gridcolor": "#E2E8F0", "zerolinecolor": "#94A3B8"},
            "zaxis": {"gridcolor": "#E2E8F0", "zerolinecolor": "#94A3B8"},
            "camera": {"eye": {"x": 1.45, "y": 1.5, "z": 1.0}},
        },
        uirevision="rfm-camera-v1",
    )
    return figure


SLICE_SPECS = {
    "rf": ("scaled_recency", "scaled_frequency", "Scaled Recency", "Scaled capped Frequency"),
    "rm": ("scaled_recency", "scaled_net_monetary", "Scaled Recency", "Scaled capped Net value"),
    "fm": ("scaled_frequency", "scaled_net_monetary", "Scaled capped Frequency", "Scaled capped Net value"),
}


def rfm_slice_figure(customers: pd.DataFrame, centroids: pd.DataFrame, slice_id: str) -> go.Figure:
    x_column, y_column, x_title, y_title = SLICE_SPECS.get(slice_id, SLICE_SPECS["rf"])
    figure = go.Figure()
    for segment_code in ("S1", "S2", "S3", "S4"):
        points = customers.loc[customers["segment_code"].eq(segment_code)]
        if points.empty:
            continue
        figure.add_scatter(
            x=points[x_column],
            y=points[y_column],
            mode="markers",
            name=segment_code,
            ids=points["customer_id"].astype(str),
            customdata=_customer_customdata(points),
            hovertemplate=CUSTOMER_HOVER,
            marker={"size": 5, "color": SEGMENT_COLORS[segment_code], "opacity": 0.58},
        )
    centers = centroids.loc[centroids["segment_code"].isin(customers["segment_code"].unique())]
    figure.add_scatter(
        x=centers[x_column],
        y=centers[y_column],
        mode="markers+text",
        text=centers["segment_code"],
        textposition="top center",
        name="Centroids",
        marker={"size": 8, "symbol": "diamond", "color": TOKENS["ink"]},
        hovertemplate="<b>%{text} centroid</b><extra></extra>",
    )
    figure.update_xaxes(title=x_title)
    figure.update_yaxes(title=y_title)
    return _base_layout(figure, height=385, margin={"l": 56, "r": 20, "t": 36, "b": 52})


def timeline_figure(timeline: pd.DataFrame, segment_code: str) -> go.Figure:
    colors = np.where(
        timeline["is_cancellation"].eq(1),
        TOKENS["refund"],
        np.where(timeline["invoice_amount"] >= 0, SEGMENT_COLORS[segment_code], TOKENS["muted"]),
    )
    labels = np.where(timeline["is_cancellation"].eq(1), "Cancellation / return", "Purchase / other")
    customdata = np.column_stack(
        [timeline["invoice_no"], timeline["line_count"], labels]
    )
    figure = go.Figure(
        go.Bar(
            x=timeline["invoice_date"],
            y=timeline["invoice_amount"],
            width=4 * 24 * 60 * 60 * 1000,
            marker_color=colors,
            customdata=customdata,
            hovertemplate=(
                "<b>Invoice %{customdata[0]}</b><br>"
                "%{x|%d %b %Y}<br>%{customdata[2]}<br>"
                "Amount: £%{y:,.2f}<br>Lines: %{customdata[1]}<extra></extra>"
            ),
        )
    )
    figure.add_hline(y=0, line_color=TOKENS["ink"], line_width=1)
    figure.update_xaxes(title=None)
    figure.update_yaxes(title="Invoice amount (£)")
    return _base_layout(figure, height=350, margin={"l": 68, "r": 22, "t": 20, "b": 46})


def k_evidence_figure(evidence: pd.DataFrame) -> go.Figure:
    data = evidence.loc[evidence["evidence_type"].eq("k_selection")]
    pivot = data.pivot(index="k", columns="metric_name", values="metric_value").sort_index()
    figure = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=("Elbow / inertia", "Silhouette", "Initialization stability (ARI)", "Smallest cluster"),
        vertical_spacing=0.18,
        horizontal_spacing=0.13,
    )
    specs = (
        ("median_inertia", 1, 1, "Squared distance", 1.0),
        ("median_silhouette_full", 1, 2, "Score", 1.0),
        ("median_pairwise_ari", 2, 1, "Score", 1.0),
        ("median_min_cluster_share", 2, 2, "Share (%)", 100.0),
    )
    for metric, row, column, ylabel, multiplier in specs:
        values = pivot[metric] * multiplier
        figure.add_scatter(
            x=pivot.index,
            y=values,
            mode="lines+markers",
            marker={
                "size": [12 if k == 4 else 7 for k in pivot.index],
                "color": [TOKENS["accent"] if k == 4 else TOKENS["muted"] for k in pivot.index],
            },
            line={"color": TOKENS["muted"], "width": 2},
            showlegend=False,
            hovertemplate="k=%{x}<br>%{y:.3f}<extra></extra>",
            row=row,
            col=column,
        )
        figure.update_yaxes(title_text=ylabel, row=row, col=column)
        figure.update_xaxes(tickmode="linear", dtick=1, row=row, col=column)
    figure.add_hline(y=1, line_dash="dash", line_color=TOKENS["refund"], row=2, col=2)
    figure.update_annotations(font_size=11)
    figure.update_xaxes(tickfont_size=9)
    figure.update_yaxes(tickfont_size=9, title_text=None)
    return _base_layout(figure, height=390, margin={"l": 42, "r": 16, "t": 46, "b": 36})


def preprocessing_figure(evidence: pd.DataFrame) -> go.Figure:
    data = evidence.loc[evidence["evidence_type"].eq("preprocessing")]
    pivot = data.pivot(index="candidate", columns="metric_name", values="metric_value")
    order = ["Standard / k=4", "Robust / k=2", "Log / k=3", "Cap99.5 / k=4"]
    pivot = pivot.reindex(order)
    colors = [TOKENS["muted"], TOKENS["refund"], TOKENS["positive"], TOKENS["accent"]]
    figure = go.Figure(
        go.Bar(
            x=pivot.index,
            y=pivot["min_cluster_share"] * 100,
            marker_color=colors,
            text=[f"{value:.2f}%" for value in pivot["min_cluster_share"] * 100],
            textposition="outside",
            customdata=np.column_stack([pivot["silhouette_full"], pivot["min_cluster_size"]]),
            hovertemplate=(
                "<b>%{x}</b><br>Smallest cluster: %{y:.2f}% (%{customdata[1]:.0f} customers)"
                "<br>Silhouette: %{customdata[0]:.3f}<extra></extra>"
            ),
        )
    )
    figure.add_hline(y=1, line_dash="dash", line_color=TOKENS["refund"], annotation_text="1% check line")
    figure.update_yaxes(title=None, tickfont_size=9)
    figure.update_xaxes(tickfont_size=9)
    return _base_layout(figure, height=170, margin={"l": 38, "r": 12, "t": 22, "b": 58})


def cap_evidence_figure(evidence: pd.DataFrame) -> go.Figure:
    data = evidence.loc[evidence["evidence_type"].eq("cap_sensitivity")]
    pivot = data.pivot(index="candidate", columns="metric_name", values="metric_value")
    order = ["No cap", "99.0%", "99.5%", "99.9%"]
    pivot = pivot.reindex(order)
    figure = make_subplots(specs=[[{"secondary_y": True}]])
    figure.add_scatter(
        x=pivot.index,
        y=pivot["median_silhouette_full"],
        name="Silhouette",
        mode="lines+markers",
        line={"color": TOKENS["accent"], "width": 3},
        marker={"size": 9},
        secondary_y=False,
    )
    figure.add_scatter(
        x=pivot.index,
        y=pivot["median_pairwise_ari"],
        name="Median ARI",
        mode="lines+markers",
        line={"color": TOKENS["positive"], "width": 3},
        marker={"size": 9},
        secondary_y=False,
    )
    figure.add_bar(
        x=pivot.index,
        y=pivot["either_affected"],
        name="Customers capped",
        marker_color=TOKENS["cap"],
        opacity=0.22,
        secondary_y=True,
    )
    figure.update_yaxes(title=None, range=[0, 1.08], tickfont_size=9, secondary_y=False)
    figure.update_yaxes(title=None, tickfont_size=9, secondary_y=True)
    figure.update_xaxes(tickfont_size=9)
    return _base_layout(figure, height=170, margin={"l": 38, "r": 38, "t": 32, "b": 38})

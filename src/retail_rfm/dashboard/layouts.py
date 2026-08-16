from __future__ import annotations

from urllib.parse import urlencode

import numpy as np
from dash import dcc, html

from .figures import (
    GRAPH_CONFIG,
    cap_evidence_figure,
    k_evidence_figure,
    overview_share_figure,
    preprocessing_figure,
    rfm_3d_figure,
    rfm_slice_figure,
    timeline_figure,
)
from .repository import DashboardRepository
from .theme import SEGMENT_COLORS


def _page_heading(eyebrow: str, title: str, lead: str, badge: str) -> html.Div:
    return html.Div(
        [
            html.Div(
                [
                    html.P(eyebrow, className="eyebrow"),
                    html.H1(title, className="page-title"),
                    html.P(lead, className="page-lead"),
                ]
            ),
            html.Div(badge, className="method-badge"),
        ],
        className="page-heading",
    )


def _kpi(label: str, value: str, note: str) -> html.Div:
    return html.Div(
        [html.Div(label, className="kpi-label"), html.Div(value, className="kpi-value"), html.Div(note, className="kpi-note")],
        className="card kpi-card",
    )


def _segment_card(row) -> html.Div:
    return html.Div(
        [
            html.Div(row.segment_code, className="segment-code"),
            html.Div(row.segment_name, className="segment-name"),
            html.Div([html.Span("Customers"), html.Strong(f"{row.customer_share:.2%}")], className="segment-stat"),
            html.Div([html.Span("Observed Net share"), html.Strong(f"{row.net_monetary_share:.2%}")], className="segment-stat"),
            html.Div([html.Span("Median R / F"), html.Strong(f"{row.recency_median:.0f}d / {row.frequency_median:.0f}")], className="segment-stat"),
            html.Div([html.Span("Median Net value"), html.Strong(f"£{row.net_monetary_median:,.0f}")], className="segment-stat"),
            html.P(row.description, className="section-note"),
            html.Div([html.Strong("Test: "), row.strategy_hypothesis], className="hypothesis"),
            html.Div([html.Strong("Future KPI: "), row.future_kpis], className="hypothesis"),
        ],
        className="card segment-card",
        style={"--segment-color": SEGMENT_COLORS[row.segment_code]},
    )


def overview_layout(repository: DashboardRepository) -> html.Main:
    profiles = repository.profiles
    high = profiles.loc[profiles["segment_code"].isin(["S3", "S4"])]
    high_customer_share = float(high["customer_share"].sum())
    high_net_share = float(high["net_monetary_share"].sum())
    return html.Main(
        [
            _page_heading(
                "Customer decision support",
                "Four behavioral segments reveal a concentrated customer base",
                "The model summarizes observed purchasing behavior. It does not predict who will respond to a campaign.",
                "Net RFM · K-means++ · k=4",
            ),
            html.Div(
                [
                    html.Div(f"about {high_customer_share:.1%}", className="hook-number"),
                    html.Div("→", className="hook-arrow"),
                    html.Div(
                        [
                            html.Strong(f"{high_net_share:.2%} of observed Net value"),
                            html.Span("S3 + S4: 457 customers. Concentration is descriptive, not causal value."),
                        ],
                        className="hook-copy",
                    ),
                ],
                className="card hook-card",
            ),
            html.Div(
                [
                    _kpi("Customers", f"{len(repository.customers):,}", "At least one valid positive purchase"),
                    _kpi("Behavioral segments", "4", "Ordered by original Net M median"),
                    _kpi("Cap-affected", f"{int(repository.customers['any_capped_flag'].sum()):,}", "No customer was removed"),
                    _kpi("Reference date", "10 Dec 2011", "Recency measured in calendar days"),
                ],
                className="kpi-grid",
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.H2("Customer share versus observed Net value", className="section-title"),
                            html.P("Read the same four colors across both bars.", className="section-note"),
                            dcc.Graph(figure=overview_share_figure(profiles), config=GRAPH_CONFIG),
                        ],
                        className="card chart-card",
                    ),
                    html.Div(
                        [
                            html.H2("How to use this result", className="section-title"),
                            html.P("Prioritize questions—not guaranteed actions.", className="section-note"),
                            html.Div(
                                [
                                    html.Strong("1. Summarize"),
                                    html.P("Describe differences in recency, frequency and observed Net value."),
                                    html.Strong("2. Query"),
                                    html.P("Inspect real customers and transaction histories inside each segment."),
                                    html.Strong("3. Test"),
                                    html.P("Turn segment-specific ideas into controlled A/B experiments."),
                                ],
                                className="plain-note",
                            ),
                        ],
                        className="card profile-panel",
                    ),
                ],
                className="two-column",
            ),
            html.Div([_segment_card(row) for row in profiles.itertuples()], className="segment-grid"),
            html.Div(
                "Observed Net value is not profit. Strategy cards are hypotheses for future controlled tests, not proven treatment effects.",
                className="disclaimer",
            ),
        ],
        className="page-container",
    )


def selection_card(customer=None) -> html.Div:
    if customer is None:
        return html.Div(
            [html.H3("Select a customer", className="section-title"), html.P("Click any point to connect model-space position back to original RFM.", className="section-note")],
            className="selection-card",
        )
    segment = customer["segment_code"]
    href = "?" + urlencode({"tab": "customer-lookup", "customer": str(customer["customer_id"])})
    return html.Div(
        [
            html.Div(f"{segment} · Customer {customer['customer_id']}", className="segment-code"),
            html.H3(customer["country_display"], className="section-title"),
            html.P(
                f"R {customer['recency']:.0f} days · F {customer['frequency']:.0f} orders · Net £{customer['net_monetary']:,.2f}",
                className="section-note",
            ),
            dcc.Link("Open real transaction history →", href=href, className="nav-link", style={"color": SEGMENT_COLORS[segment], "padding": "4px 0"}),
        ],
        className="selection-card",
    )


def explorer_layout(repository: DashboardRepository) -> html.Main:
    customers = repository.customers
    return html.Main(
        [
            _page_heading(
                "Model-space explorer",
                "Explore the exact three features used by K-means",
                "Hover returns to original days, order counts and pounds. Capping affects distance only; it does not remove customers.",
                "4,338 / 4,338 customers shown",
            ),
            html.Div(
                [
                    html.Div([html.Label("Segments", className="filter-label"), dcc.Dropdown(id="segment-filter", options=[{"label": f"{row.segment_code} · {row.segment_name}", "value": row.segment_code} for row in repository.profiles.itertuples()], value=["S1", "S2", "S3", "S4"], multi=True, clearable=False)]),
                    html.Div([html.Label("Countries", className="filter-label"), dcc.Dropdown(id="country-filter", options=repository.country_options, value=[], multi=True, placeholder="All countries")]),
                    html.Div([html.Label("Cap status", className="filter-label"), dcc.RadioItems(id="cap-filter", options=[{"label": "All", "value": "all"}, {"label": "Capped", "value": "capped"}, {"label": "Uncapped", "value": "uncapped"}], value="all", inline=True)]),
                    html.Div([html.Label("2D slice", className="filter-label"), dcc.RadioItems(id="slice-filter", options=[{"label": "R–F", "value": "rf"}, {"label": "R–M", "value": "rm"}, {"label": "F–M", "value": "fm"}], value="rf", inline=True)]),
                ],
                className="card filter-bar",
            ),
            html.Div(
                [
                    html.Div(
                        dcc.Graph(id="rfm-3d", figure=rfm_3d_figure(customers, repository.centroids), config=GRAPH_CONFIG, style={"height": "510px"}),
                        className="card graph-frame",
                    ),
                    html.Div(
                        [
                            html.Div(id="point-selection", children=selection_card(), className="card"),
                            html.Div(
                                [
                                    html.H2("2D semantic slice", className="section-title"),
                                    html.P("Same model coordinates; no PCA projection.", className="section-note"),
                                    dcc.Graph(id="rfm-slice", figure=rfm_slice_figure(customers, repository.centroids, "rf"), config=GRAPH_CONFIG),
                                ],
                                className="card chart-card",
                            ),
                        ],
                        className="side-stack",
                    ),
                ],
                className="explorer-grid",
            ),
            html.Div("Distance in this view is standardized, capped RFM distance—not similarity in demographics, product preference or future response.", className="disclaimer"),
        ],
        className="page-container",
    )


def _representative_card(repository: DashboardRepository, segment_code: str, customer_id: str) -> html.Button:
    row = repository.customer(customer_id)
    profile = repository.profile(segment_code)
    return html.Button(
        html.Div(
            [
                html.Div(f"{segment_code} · {profile['segment_name']}", className="segment-code"),
                html.Div(f"Customer {customer_id}", className="segment-name", style={"minHeight": "auto"}),
                html.Div(f"R {row['recency']:.0f}d · F {row['frequency']:.0f} · £{row['net_monetary']:,.2f}", className="rep-rfm"),
            ],
            className="card representative-card",
            style={"--segment-color": SEGMENT_COLORS[segment_code]},
        ),
        id=f"rep-{segment_code}",
        n_clicks=0,
        className="representative-button",
        title=f"Open representative {customer_id}",
    )


def _metric_bullet(label: str, value: float, median: float, suffix: str, color: str) -> html.Div:
    maximum = max(abs(value), abs(median), 1.0) * 1.18
    value_width = min(abs(value) / maximum * 100, 100)
    median_position = min(abs(median) / maximum * 100, 100)
    value_text = f"{value:,.0f}{suffix}" if suffix != " £" else f"£{value:,.2f}"
    median_text = f"{median:,.0f}{suffix}" if suffix != " £" else f"£{median:,.2f}"
    return html.Div(
        [
            html.Div([html.Strong(label), html.Span(f"Customer {value_text} · segment median {median_text}")], className="rfm-metric-head"),
            html.Div([html.Div(className="rfm-fill", style={"width": f"{value_width}%", "background": color}), html.Div(className="rfm-median", style={"left": f"{median_position}%"})], className="rfm-track"),
        ],
        className="rfm-metric",
    )


def customer_layout(repository: DashboardRepository, customer_id: str) -> html.Main:
    try:
        customer = repository.customer(customer_id)
    except KeyError:
        customer_id = repository.representative_ids()["S4"]
        customer = repository.customer(customer_id)
    segment = customer["segment_code"]
    profile = repository.profile(segment)
    timeline = repository.timeline(str(customer_id))
    cancellation_count = int(timeline["is_cancellation"].sum())
    positive_invoice_count = int(customer["frequency"])
    representatives = repository.representative_ids()
    color = SEGMENT_COLORS[segment]
    return html.Main(
        [
            _page_heading(
                "Real-customer lookup",
                "A real S4 customer connects the segment to transactions",
                "Search only customers in the fitted dataset. This page does not predict campaign success or assign hypothetical customers.",
                f"Customer {customer_id}",
            ),
            html.Div([_representative_card(repository, code, representatives[code]) for code in ("S1", "S2", "S3", "S4")], className="representative-grid"),
            html.Div(
                [
                    html.Div([html.Label("Search a real CustomerID", className="filter-label"), dcc.Dropdown(id="customer-dropdown", options=repository.customer_options, value=str(customer_id), clearable=False, searchable=True)]),
                    html.Div("Four cards are the nearest real customers to each centroid.", className="section-note"),
                ],
                className="card lookup-controls",
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.Div([html.Div([html.P("Selected customer", className="eyebrow"), html.H2(str(customer_id), className="page-title", style={"fontSize": "32px"}), html.P(customer["country_display"], className="section-note")]), html.Div(f"{segment} · {profile['segment_name']}", className="segment-pill", style={"--segment-color": color})], className="profile-header"),
                            _metric_bullet("Recency", float(customer["recency"]), float(profile["recency_median"]), " days", color),
                            _metric_bullet("Frequency", float(customer["frequency"]), float(profile["frequency_median"]), " orders", color),
                            _metric_bullet("Observed Net value", float(customer["net_monetary"]), float(profile["net_monetary_median"]), " £", color),
                            html.Div(
                                [
                                    html.Strong("Why this segment? "),
                                    f"After F/M capping and standardization, this customer is {customer['centroid_distance']:.3f} units from the {segment} centroid. The comparison uses all three model features together.",
                                ],
                                className="plain-note",
                            ),
                            html.Div([html.Span("Valid purchase invoices"), html.Strong(f"{positive_invoice_count}")], className="segment-stat"),
                            html.Div([html.Span("Cancellation invoices shown"), html.Strong(f"{cancellation_count}")], className="segment-stat"),
                            html.Div([html.Span("All recorded invoices"), html.Strong(f"{len(timeline)}")], className="segment-stat"),
                        ],
                        className="card profile-panel",
                    ),
                    html.Div(
                        [
                            html.H2("Invoice and cancellation timeline", className="section-title"),
                            html.P("Blue/segment color is positive; red is a C-prefixed cancellation. Frequency counts only valid purchase invoices.", className="section-note"),
                            dcc.Graph(figure=timeline_figure(timeline, segment), config=GRAPH_CONFIG),
                        ],
                        className="card timeline-card",
                    ),
                ],
                className="lookup-grid",
            ),
            html.Div("This customer is an observed example near a centroid—not a persona, a prediction, or a guaranteed marketing target.", className="disclaimer"),
        ],
        className="page-container",
    )


def evidence_layout(repository: DashboardRepository) -> html.Main:
    directed = repository.evidence.loc[
        repository.evidence["evidence_type"].eq("directed_sensitivity")
        & repository.evidence["metric_name"].eq("representative_common_ari")
    ].sort_values("candidate")
    cards = [
        html.Div(
            [html.Div(row.candidate, className="pass-title"), html.Div(f"ARI {row.metric_value:.3f}", className="pass-value"), html.Div("Four-level profile retained · PASS", className="pass-note")],
            className="card pass-card",
        )
        for row in directed.itertuples()
    ]
    return html.Main(
        [
            _page_heading(
                "Model evidence",
                "No single score selected the final model",
                "The decision combines elbow, silhouette, initialization stability, cluster size, original-scale profiles and targeted sensitivity checks.",
                "Q&A evidence · not the homepage",
            ),
            html.Div(
                [html.Div([html.H2("Why k=4?", className="section-title"), html.P("The larger blue point is k=4; k=2 is a coarser majority-versus-top split.", className="section-note"), dcc.Graph(figure=k_evidence_figure(repository.evidence), config=GRAPH_CONFIG, style={"height": "390px"})], className="card evidence-card", style={"minHeight": "470px"}),
                html.Div([html.H2("Preprocessing trade-off", className="section-title"), html.P("A high score can isolate only a few extreme customers.", className="section-note"), dcc.Graph(figure=preprocessing_figure(repository.evidence), config=GRAPH_CONFIG, style={"height": "170px"}), html.H2("99.5% cap sensitivity", className="section-title", style={"marginTop": "2px"}), dcc.Graph(figure=cap_evidence_figure(repository.evidence), config=GRAPH_CONFIG, style={"height": "170px"})], className="card evidence-card", style={"minHeight": "470px"}),
            ],
                className="evidence-grid",
            ),
            html.H2("Targeted sensitivity checks", className="section-title", style={"marginTop": "20px"}),
            html.Div(cards, className="pass-grid"),
            html.Div("Silhouette and ARI are internal evaluation and stability evidence. They are not classification accuracy and do not prove that the four groups are ground truth.", className="disclaimer"),
        ],
        className="page-container",
    )


def presentation_layout(repository: DashboardRepository, view: str) -> html.Main:
    allowed = {"3d", "rf", "rm", "fm", "customer-13777"}
    view = view if view in allowed else "3d"
    links = [
        ("3d", "3D"),
        ("rf", "R–F"),
        ("rm", "R–M"),
        ("fm", "F–M"),
        ("customer-13777", "Customer 13777"),
    ]
    heading = html.Div(
        [
            html.Div(
                [
                    html.H1("RFM customer explorer", className="presentation-demo-title"),
                    html.P(
                        "4,338 customers · same scaled/capped coordinates as the model",
                        className="presentation-demo-note",
                    ),
                ]
            ),
            html.Nav(
                [
                    dcc.Link(
                        label,
                        href="?" + urlencode(
                            {"tab": "presentation-demo", "embed": "1", "view": value}
                        ),
                        className="nav-link active" if value == view else "nav-link",
                    )
                    for value, label in links
                ],
                className="presentation-demo-nav",
            ),
        ],
        className="presentation-demo-head",
    )

    if view == "customer-13777":
        customer = repository.customer("13777")
        timeline = repository.timeline("13777")
        compact_timeline = timeline_figure(timeline, "S4")
        compact_timeline.update_layout(
            autosize=True,
            height=None,
            margin={"l": 45, "r": 8, "t": 8, "b": 28},
            font={"size": 8},
        )
        compact_timeline.update_yaxes(title_text="Invoice amount (£)", title_font={"size": 8})
        content = html.Div(
            [
                html.Div(
                    [
                        html.P("Real customer near the S4 centroid", className="eyebrow"),
                        html.H2("13777", className="page-title"),
                        html.Div(
                            [html.Span("Recency"), html.Strong("1 day")],
                            className="segment-stat",
                        ),
                        html.Div(
                            [html.Span("Frequency"), html.Strong("33 valid purchases")],
                            className="segment-stat",
                        ),
                        html.Div(
                            [
                                html.Span("Observed Net value"),
                                html.Strong(f"£{customer['net_monetary']:,.2f}"),
                            ],
                            className="segment-stat",
                        ),
                        html.Div(
                            [html.Span("Recorded invoices"), html.Strong(str(len(timeline)))],
                            className="segment-stat",
                        ),
                        html.Div(
                            [
                                html.Span("C-prefixed cancellations"),
                                html.Strong(str(int(timeline["is_cancellation"].sum()))),
                            ],
                            className="segment-stat",
                        ),
                        html.P(
                            "Observed example—not a persona or response prediction.",
                            className="presentation-demo-note",
                            style={"marginTop": "10px"},
                        ),
                    ],
                    className="presentation-customer-summary",
                ),
                html.Div(
                    dcc.Graph(
                        figure=compact_timeline,
                        config=GRAPH_CONFIG,
                        style={"height": "calc(100vh - 115px)"},
                    ),
                    className="presentation-timeline",
                ),
            ],
            className="presentation-customer",
        )
    elif view == "3d":
        compact_3d = rfm_3d_figure(repository.customers, repository.centroids)
        compact_3d.update_layout(
            autosize=True,
            height=None,
            margin={"l": 0, "r": 0, "t": 10, "b": 0},
            font={"size": 10},
            legend={"font": {"size": 8}, "orientation": "h", "x": 0, "y": 0.98},
            scene={
                "xaxis": {"title": {"text": "R", "font": {"size": 8}}, "tickfont": {"size": 7}},
                "yaxis": {"title": {"text": "F", "font": {"size": 8}}, "tickfont": {"size": 7}},
                "zaxis": {"title": {"text": "Net M", "font": {"size": 8}}, "tickfont": {"size": 7}},
                "camera": {"eye": {"x": 1.9, "y": 1.9, "z": 1.35}},
            },
        )
        content = dcc.Graph(
            figure=compact_3d,
            config=GRAPH_CONFIG,
            className="presentation-demo-graph",
            style={"height": "calc(100vh - 88px)"},
        )
    else:
        content = dcc.Graph(
            figure=rfm_slice_figure(repository.customers, repository.centroids, view),
            config=GRAPH_CONFIG,
            className="presentation-demo-graph",
            style={"height": "calc(100vh - 88px)"},
        )
    return html.Main([heading, content], className="presentation-demo")

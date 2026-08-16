from __future__ import annotations

from pathlib import Path
from urllib.parse import parse_qs, urlencode

from dash import Dash, Input, Output, State, ctx, dcc, html, no_update

from .figures import GRAPH_CONFIG, rfm_3d_figure, rfm_slice_figure
from .layouts import (
    customer_layout,
    evidence_layout,
    explorer_layout,
    overview_layout,
    presentation_layout,
    selection_card,
)
from .repository import DashboardRepository
from .theme import VISUAL_DIR


TABS = (
    ("overview", "Overview"),
    ("rfm-explorer", "RFM Explorer"),
    ("customer-lookup", "Customer Lookup"),
    ("model-evidence", "Model Evidence"),
)


def _query(search: str | None) -> dict[str, str]:
    parsed = parse_qs((search or "").lstrip("?"))
    return {key: values[-1] for key, values in parsed.items() if values}


def create_app(database_path: Path) -> Dash:
    repository = DashboardRepository(database_path)
    app = Dash(
        __name__,
        title="Retail Customer Segmentation",
        assets_folder=str(VISUAL_DIR),
        suppress_callback_exceptions=True,
        update_title=None,
    )

    app.layout = html.Div(
        [
            dcc.Location(id="url", refresh=False),
            html.Header(
                [
                    html.Div([html.H1("Retail RFM", className="brand-title"), html.P("Exploratory customer segmentation", className="brand-subtitle")], className="brand-block"),
                    html.Nav([dcc.Link(label, href=f"?tab={tab}", id=f"nav-{tab}", className="nav-link") for tab, label in TABS], className="nav-links"),
                ],
                className="app-header",
                id="app-header",
            ),
            html.Div(id="page-content"),
        ],
        className="app-shell",
    )

    @app.server.get("/healthz")
    def healthz():
        return {"status": "ok", "customers": len(repository.customers), "schema_version": 1}

    @app.callback(
        Output("page-content", "children"),
        Output("app-header", "style"),
        *[Output(f"nav-{tab}", "className") for tab, _ in TABS],
        Input("url", "search"),
    )
    def render_page(search):
        query = _query(search)
        tab = query.get("tab", "overview")
        is_presentation = tab == "presentation-demo"
        if tab not in {value for value, _ in TABS} and not is_presentation:
            tab = "overview"
        if is_presentation:
            page = presentation_layout(repository, query.get("view", "3d"))
        elif tab == "rfm-explorer":
            page = explorer_layout(repository)
        elif tab == "customer-lookup":
            customer_id = query.get("customer", repository.representative_ids()["S4"])
            page = customer_layout(repository, customer_id)
        elif tab == "model-evidence":
            page = evidence_layout(repository)
        else:
            page = overview_layout(repository)
        classes = ["nav-link active" if value == tab else "nav-link" for value, _ in TABS]
        header_style = {"display": "none"} if is_presentation else None
        return (page, header_style, *classes)

    @app.callback(
        Output("rfm-3d", "figure"),
        Output("rfm-slice", "figure"),
        Input("segment-filter", "value"),
        Input("country-filter", "value"),
        Input("cap-filter", "value"),
        Input("slice-filter", "value"),
    )
    def update_explorer(segments, countries, cap_status, slice_id):
        customers = repository.filtered_customers(segments, countries, cap_status or "all")
        return (
            rfm_3d_figure(customers, repository.centroids),
            rfm_slice_figure(customers, repository.centroids, slice_id or "rf"),
        )

    @app.callback(
        Output("point-selection", "children"),
        Input("rfm-3d", "clickData"),
        Input("rfm-slice", "clickData"),
    )
    def update_selection(click_3d, click_2d):
        click = click_3d if ctx.triggered_id == "rfm-3d" else click_2d
        if not click or not click.get("points"):
            return selection_card()
        customer_id = click["points"][0].get("id")
        if not customer_id:
            return selection_card()
        return selection_card(repository.customer(str(customer_id)))

    @app.callback(
        Output("url", "search", allow_duplicate=True),
        Input("customer-dropdown", "value"),
        Input("rep-S1", "n_clicks"),
        Input("rep-S2", "n_clicks"),
        Input("rep-S3", "n_clicks"),
        Input("rep-S4", "n_clicks"),
        State("url", "search"),
        prevent_initial_call=True,
    )
    def choose_customer(dropdown_value, *_):
        triggered = ctx.triggered_id
        if isinstance(triggered, str) and triggered.startswith("rep-"):
            segment = triggered.removeprefix("rep-")
            customer_id = repository.representative_ids()[segment]
        elif triggered == "customer-dropdown" and dropdown_value:
            customer_id = str(dropdown_value)
        else:
            return no_update
        return "?" + urlencode({"tab": "customer-lookup", "customer": customer_id})

    return app

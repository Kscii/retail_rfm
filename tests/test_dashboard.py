from __future__ import annotations

import json
from pathlib import Path

import pytest

from retail_rfm.dashboard.app import create_app
from retail_rfm.dashboard.figures import (
    cap_evidence_figure,
    k_evidence_figure,
    overview_share_figure,
    rfm_3d_figure,
    rfm_slice_figure,
    timeline_figure,
)
from retail_rfm.dashboard.repository import DashboardRepository
from retail_rfm.dashboard.layouts import presentation_layout


@pytest.fixture(scope="module")
def repository():
    path = Path("artifacts/retail_rfm.sqlite")
    if not path.is_file():
        pytest.skip("Run `uv run retail-rfm build` before dashboard tests")
    return DashboardRepository(path)


def test_dashboard_repository_and_filters(repository):
    assert len(repository.customers) == 4_338
    assert repository.representative_ids() == {
        "S1": "17035",
        "S2": "15801",
        "S3": "12839",
        "S4": "13777",
    }
    capped = repository.filtered_customers(["S1", "S2", "S3", "S4"], [], "capped")
    assert len(capped) == 29
    uk = repository.filtered_customers(None, ["United Kingdom"], "all")
    assert 3_900 < len(uk) < 4_000


def test_dashboard_figures_use_model_coordinates_and_real_timeline(repository):
    customers = repository.customers
    figure_3d = rfm_3d_figure(customers, repository.centroids)
    point_ids = {
        str(customer_id)
        for trace in figure_3d.data
        if getattr(trace, "ids", None) is not None
        for customer_id in trace.ids
    }
    assert len(point_ids) == 4_338
    assert figure_3d.layout.scene.xaxis.title.text == "Scaled Recency"
    assert figure_3d.layout.scene.yaxis.title.text == "Scaled capped Frequency"
    assert figure_3d.layout.scene.zaxis.title.text == "Scaled capped Net value"
    assert figure_3d.data[-1].marker.size == 6
    assert figure_3d.layout.hoverlabel.font.size == 8
    slice_figure = rfm_slice_figure(customers, repository.centroids, "fm")
    assert len(slice_figure.data) == 5
    assert slice_figure.data[-1].marker.size == 8
    assert slice_figure.layout.hoverlabel.font.size == 8
    timeline = repository.timeline("13777")
    assert len(timeline) == 41
    assert int(timeline["is_cancellation"].sum()) == 8
    assert len(timeline_figure(timeline, "S4").data) == 1


def test_summary_and_evidence_figures_build(repository):
    assert len(overview_share_figure(repository.profiles).data) == 4
    assert len(k_evidence_figure(repository.evidence).data) == 4
    assert len(cap_evidence_figure(repository.evidence).data) == 3


def test_dash_server_and_health_endpoint(repository):
    app = create_app(repository.database_path)
    client = app.server.test_client()
    assert client.get("/").status_code == 200
    health = client.get("/healthz")
    assert health.status_code == 200
    assert health.json == {"status": "ok", "customers": 4_338, "schema_version": 1}


def test_hidden_presentation_routes_build_from_real_data(repository):
    for view in ("3d", "rf", "rm", "fm", "customer-13777"):
        layout = presentation_layout(repository, view)
        assert layout.className == "presentation-demo"


def test_visual_tokens_match_shared_css():
    tokens = json.loads(Path("visual/tokens.json").read_text())
    css = Path("visual/theme.css").read_text()
    for key in ("background", "surface", "ink", "S1", "S2", "S3", "S4", "refund", "cap"):
        assert tokens[key] in css

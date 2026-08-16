from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from sklearn.cluster import kmeans_plusplus

from retail_rfm.cli import build_parser
from retail_rfm.presentation_export import export_presentation


def test_export_presentation_cli_contract():
    args = build_parser().parse_args(
        [
            "export-presentation",
            "--csv",
            "resource/Online Retail.csv",
            "--db",
            "artifacts/retail_rfm.sqlite",
            "--output-dir",
            "presentation/public/static-demo",
        ]
    )
    assert args.command == "export-presentation"
    assert args.db == Path("artifacts/retail_rfm.sqlite")


def test_exported_presentation_data_is_auditable(tmp_path):
    database = Path("artifacts/retail_rfm.sqlite")
    if not database.is_file():
        pytest.skip("Run `uv run retail-rfm build` before presentation export tests")
    result = export_presentation(
        Path("resource/Online Retail.csv"), database, tmp_path, Path("docs/assets")
    )
    assert result["customers"] == 4_338
    assert result["centroids"] == 4
    assert result["timeline_invoices"] == 41

    data = json.loads((tmp_path / "data.json").read_text(encoding="utf-8"))
    assert data["schema_version"] == 3
    assert len(data["points"]) == 4_338
    assert sum(point["demo"] for point in data["points"]) == 1
    assert {point["id"] for point in data["points"] if point["demo"]} == {"13777"}
    assert data["findings"]["s3_s4_customers"] == 457
    assert data["demo_customer"]["cancellation_count"] == 8
    assert [row["k"] for row in data["k_evidence"]] == list(range(2, 9))
    animation = data["kmeans_animation"]
    assert animation["seed"] == 431
    assert animation["uses_full_3d"] is True
    assert animation["iterations_to_stable"] == 15
    assert animation["ari_vs_final"] == 1.0
    assert [frame["iteration"] for frame in animation["frames"]] == list(range(1, 16))
    assert all(len(frame["labels"]) == 4_338 for frame in animation["frames"])
    assert [frame["changed_count"] for frame in animation["frames"]] == [
        0,
        205,
        90,
        44,
        16,
        14,
        7,
        5,
        4,
        9,
        7,
        5,
        1,
        1,
        0,
    ]
    assert all(
        set(frame["labels"]) == {"S1", "S2", "S3", "S4"}
        for frame in animation["frames"]
    )
    assert all(
        np.isfinite(
            [center["values"] for center in frame["centers_before"]]
            + [center["values"] for center in frame["centers_after"]]
        ).all()
        for frame in animation["frames"]
    )
    assert animation["frames"][-1]["changed_count"] == 0
    assert len(animation["initialization_steps"]) == 4
    features = np.asarray(
        [[point["x"], point["y"], point["z"]] for point in data["points"]]
    )
    expected_centers, expected_indices = kmeans_plusplus(
        features, n_clusters=4, random_state=431
    )
    assert expected_indices.tolist() == animation["initial_indices"]
    assert np.allclose(expected_centers, animation["initial_centers"])
    for offset, initialization in enumerate(animation["initialization_steps"]):
        assert initialization["center_number"] == offset + 1
        assert initialization["selected_index"] == animation["initial_indices"][offset]
        assert len(initialization["display_intensities"]) == 4_338
        assert np.isfinite(initialization["display_intensities"]).all()
        assert min(initialization["display_intensities"]) >= 0
        assert max(initialization["display_intensities"]) <= 1
        probabilities = initialization["selection_probabilities"]
        if offset == 0:
            assert probabilities is None
            continue
        existing = np.asarray(animation["initial_centers"][:offset])
        expected_squared_distances = (
            (features[:, None, :] - existing[None, :, :]) ** 2
        ).sum(axis=2).min(axis=1)
        expected_probabilities = (
            expected_squared_distances / expected_squared_distances.sum()
        )
        assert np.allclose(probabilities, expected_probabilities, rtol=1e-7, atol=1e-12)
        assert np.isclose(sum(probabilities), 1.0)
    for previous, current in zip(
        animation["frames"][:-1], animation["frames"][1:], strict=True
    ):
        previous_labels = np.asarray(previous["labels"])
        current_labels = np.asarray(current["labels"])
        assert current["changed_count"] == int(
            np.count_nonzero(previous_labels != current_labels)
        )
    assert all(
        frame["changed_count"] == len(frame["changed_indices"])
        for frame in animation["frames"]
    )
    assert (tmp_path / "manifest.json").is_file()
    assert (tmp_path / "plotly.min.js").is_file()
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["schema_version"] == 3
    assert all((tmp_path / f"kmeans-step-{step}.svg").is_file() for step in range(20))
    assert (
        len([name for name in manifest["files"] if name.startswith("kmeans-step-")])
        == 20
    )

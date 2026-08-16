from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import plotly
from sklearn.cluster import kmeans_plusplus
from sklearn.metrics import adjusted_rand_score

from .constants import EXPECTED, PIPELINE_ID
from .modeling import sha256_file
from .storage import assert_schema_version, connect_read_only


STATIC_SCHEMA_VERSION = 3
MAIN_EVIDENCE = Path("rfm-model-exploration/tables/pipeline-k-evidence.csv")
DEMO_CUSTOMER_ID = "13777"
ANIMATION_SEED = 431
ANIMATION_COLORS = {
    "S1": "#4D4D4D",
    "S2": "#6A1B9A",
    "S3": "#008A50",
    "S4": "#F57C00",
}


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    clean = frame.copy()
    clean = clean.where(pd.notna(clean), None)
    return clean.to_dict(orient="records")


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _write_json_atomic(path: Path, value: Any) -> None:
    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", delete=False) as stream:
        staged = Path(stream.name)
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(staged, path)


def _write_text_atomic(path: Path, value: str) -> None:
    payload = value.encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", delete=False) as stream:
        staged = Path(stream.name)
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(staged, path)


def _kmeans_animation(customers: pd.DataFrame) -> dict[str, Any]:
    feature_columns = ["scaled_recency", "scaled_frequency", "scaled_net_monetary"]
    features = customers[feature_columns].to_numpy(dtype=float)
    if not np.isfinite(features).all():
        raise AssertionError("K-means++ animation inputs contain NaN or infinity")
    centers, initial_indices = kmeans_plusplus(
        features,
        n_clusters=4,
        random_state=ANIMATION_SEED,
    )
    initial_centers = centers.copy()
    initialization_steps = []
    for center_offset, selected_index in enumerate(initial_indices):
        if center_offset == 0:
            probabilities = None
            display_intensities = [0.0] * len(features)
            selected_probability = None
        else:
            existing_centers = initial_centers[:center_offset]
            squared_distances = (
                (features[:, None, :] - existing_centers[None, :, :]) ** 2
            ).sum(axis=2).min(axis=1)
            probability_total = float(squared_distances.sum())
            if not np.isfinite(probability_total) or probability_total <= 0:
                raise AssertionError("Invalid K-means++ D-squared probability weights")
            probabilities_array = squared_distances / probability_total
            positive_distances = squared_distances[squared_distances > 0]
            display_cap = float(np.quantile(positive_distances, 0.995))
            display_array = np.clip(squared_distances / display_cap, 0.0, 1.0)
            if not np.isfinite(probabilities_array).all() or not np.isfinite(
                display_array
            ).all():
                raise AssertionError("Invalid K-means++ initialization display values")
            probabilities = probabilities_array.tolist()
            display_intensities = display_array.tolist()
            selected_probability = float(probabilities_array[int(selected_index)])
        initialization_steps.append(
            {
                "center_number": center_offset + 1,
                "selected_index": int(selected_index),
                "selected_center": initial_centers[center_offset].tolist(),
                "centers_selected": initial_centers[: center_offset + 1].tolist(),
                "selection_probabilities": probabilities,
                "display_intensities": display_intensities,
                "display_clip_quantile": 0.995,
                "selected_probability": selected_probability,
            }
        )

    previous_labels: Any = None
    raw_frames: dict[int, dict[str, Any]] = {}

    for iteration in range(1, 301):
        squared_distances = ((features[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2)
        labels = squared_distances.argmin(axis=1)
        members = [features[labels == raw_cluster] for raw_cluster in range(4)]
        if any(len(cluster_members) == 0 for cluster_members in members):
            raise AssertionError("Illustrative K-means++ run produced an empty cluster")
        updated_centers = np.vstack(
            [cluster_members.mean(axis=0) for cluster_members in members]
        )
        changed_indices = (
            []
            if previous_labels is None
            else np.flatnonzero(labels != previous_labels).tolist()
        )
        raw_frames[iteration] = {
            "iteration": iteration,
            "labels": labels.tolist(),
            "centers_before": centers.tolist(),
            "centers_after": updated_centers.tolist(),
            "changed_indices": changed_indices,
            "changed_count": len(changed_indices),
            "max_centroid_shift": float(
                np.sqrt(((updated_centers - centers) ** 2).sum(axis=1)).max()
            ),
        }
        stable = previous_labels is not None and (labels == previous_labels).all()
        centers = updated_centers
        if stable:
            break
        previous_labels = labels.copy()

    if iteration != 15 or list(raw_frames) != list(range(1, 16)):
        raise AssertionError(f"Unexpected illustrative K-means++ trajectory: {iteration} iterations")
    if raw_frames[15]["changed_count"] != 0:
        raise AssertionError("Final illustrative animation frame is not stable")

    semantic_labels = customers["segment_code"].astype(str).to_numpy()
    raw_to_segment: dict[int, str] = {}
    for raw_cluster in range(4):
        members = semantic_labels[labels == raw_cluster]
        counts = pd.Series(members).value_counts()
        if counts.empty:
            raise AssertionError("Illustrative K-means++ run produced an empty final cluster")
        raw_to_segment[raw_cluster] = str(counts.index[0])
    if set(raw_to_segment.values()) != set(ANIMATION_COLORS):
        raise AssertionError(f"Illustrative cluster mapping is not one-to-one: {raw_to_segment}")

    final_semantic = [raw_to_segment[int(label)] for label in labels]
    ari = float(adjusted_rand_score(semantic_labels, final_semantic))
    if ari != 1.0:
        raise AssertionError(f"Illustrative run no longer matches the final assignments: ARI={ari}")

    frames = []
    for frame in raw_frames.values():
        frames.append(
            {
                **frame,
                "labels": [raw_to_segment[int(label)] for label in frame["labels"]],
                "centers_before": [
                    {"segment": raw_to_segment[index], "values": values}
                    for index, values in enumerate(frame["centers_before"])
                ],
                "centers_after": [
                    {"segment": raw_to_segment[index], "values": values}
                    for index, values in enumerate(frame["centers_after"])
                ],
            }
        )

    return {
        "seed": ANIMATION_SEED,
        "k": 4,
        "uses_full_3d": True,
        "display_axes": ["scaled_recency", "scaled_frequency"],
        "iterations_to_stable": iteration,
        "ari_vs_final": ari,
        "initial_indices": initial_indices.tolist(),
        "initial_centers": initial_centers.tolist(),
        "initialization_steps": initialization_steps,
        "raw_to_segment": {str(key): value for key, value in raw_to_segment.items()},
        "frames": frames,
    }


def _animation_svg(
    points: list[dict[str, Any]],
    animation: dict[str, Any],
    step: int,
) -> str:
    width, height = 800, 330
    left, right, top, bottom = 48, 18, 30, 42
    plot_width = width - left - right
    plot_height = height - top - bottom
    xs = [float(point["x"]) for point in points]
    ys = [float(point["y"]) for point in points]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    x_pad = max((x_max - x_min) * 0.035, 0.05)
    y_pad = max((y_max - y_min) * 0.035, 0.05)
    x_min, x_max = x_min - x_pad, x_max + x_pad
    y_min, y_max = y_min - y_pad, y_max + y_pad

    def project(values: list[float]) -> tuple[float, float]:
        x_value, y_value = float(values[0]), float(values[1])
        x = left + (x_value - x_min) / (x_max - x_min) * plot_width
        y = top + plot_height - (y_value - y_min) / (y_max - y_min) * plot_height
        return x, y

    initialization_stages = {
        0: "Start: all 4,338 customer profiles are unlabeled",
        1: "Initialize C1: choose the first customer at random",
        2: "Initialize C2: farther customers receive more selection weight",
        3: "Initialize C3: recompute distance from the nearest chosen center",
        4: "Initialize C4: complete the K-means++ starting centers",
    }
    if step < 0 or step > 19:
        raise ValueError(f"Unknown K-means animation step: {step}")
    if step <= 4:
        stage = initialization_stages[step]
    else:
        iteration_number = step - 4
        stage = (
            "Iteration 15 / 15 — assignments are stable"
            if iteration_number == 15
            else f"Iteration {iteration_number} / 15 — assign in 3D, then recenter"
        )
    labels = [None] * len(points)
    frame = None
    initialization = None
    if 1 <= step <= 4:
        initialization = animation["initialization_steps"][step - 1]
    elif step >= 5:
        frame = animation["frames"][step - 5]
        labels = frame["labels"]

    elements = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L7,3 z" fill="#E64626"/></marker></defs>',
        '<rect width="800" height="330" fill="#fff"/>',
        f'<text x="48" y="18" font-family="Noto Sans, sans-serif" font-size="11.5" font-weight="700" fill="#111">{stage}</text>',
        f'<text x="782" y="18" text-anchor="end" font-family="Noto Sans, sans-serif" font-size="9" font-weight="700" fill="#565656">{step + 1} / 20</text>',
        f'<line x1="{left}" y1="{top + plot_height}" x2="{left + plot_width}" y2="{top + plot_height}" stroke="#999" stroke-width="1"/>',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_height}" stroke="#999" stroke-width="1"/>',
        f'<text x="{left + plot_width / 2:.1f}" y="322" text-anchor="middle" font-family="Noto Sans, sans-serif" font-size="10" fill="#565656">Scaled Recency</text>',
        f'<text x="14" y="{top + plot_height / 2:.1f}" text-anchor="middle" transform="rotate(-90 14 {top + plot_height / 2:.1f})" font-family="Noto Sans, sans-serif" font-size="10" fill="#565656">Scaled capped Frequency</text>',
    ]
    display_intensities = (
        initialization["display_intensities"] if initialization is not None else None
    )
    for point_index, (point, label) in enumerate(zip(points, labels, strict=True)):
        x, y = project([point["x"], point["y"]])
        if display_intensities is not None and step >= 2:
            intensity = float(display_intensities[point_index])
            radius = 0.82 + 0.5 * intensity
            opacity = 0.08 + 0.72 * intensity
            elements.append(
                f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{radius:.2f}" fill="#E64626" fill-opacity="{opacity:.3f}"/>'
            )
        else:
            color = "#AEB5BE" if label is None else ANIMATION_COLORS[str(label)]
            opacity = "0.35" if label is None else "0.48"
            elements.append(
                f'<circle cx="{x:.2f}" cy="{y:.2f}" r="0.95" fill="{color}" fill-opacity="{opacity}"/>'
            )

    if initialization is not None:
        for index, values in enumerate(initialization["centers_selected"], start=1):
            x, y = project(values)
            elements.extend(
                [
                    f'<path d="M{x:.2f},{y-5:.2f} L{x+5:.2f},{y:.2f} L{x:.2f},{y+5:.2f} L{x-5:.2f},{y:.2f} Z" fill="#111" stroke="#fff" stroke-width="1.3"/>',
                    f'<text x="{x+8:.2f}" y="{y-6:.2f}" font-family="Noto Sans, sans-serif" font-size="9" font-weight="700" fill="#111">C{index}</text>',
                ]
            )
        if step == 1:
            elements.append(
                '<text x="782" y="306" text-anchor="end" font-family="Noto Sans, sans-serif" font-size="8.5" font-weight="700" fill="#565656">Initialization — not a cluster · first center is random</text>'
            )
        else:
            elements.append(
                '<text x="782" y="306" text-anchor="end" font-family="Noto Sans, sans-serif" font-size="8.5" font-weight="700" fill="#565656">Initialization weight — not a cluster · orange D² intensity is clipped</text>'
            )
    elif frame is not None:
        for before, after in zip(
            frame["centers_before"], frame["centers_after"], strict=True
        ):
            x1, y1 = project(before["values"])
            x2, y2 = project(after["values"])
            if abs(x2 - x1) > 0.05 or abs(y2 - y1) > 0.05:
                elements.append(
                    f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="#E64626" stroke-width="1.5" marker-end="url(#arrow)"/>'
                )
        if frame["iteration"] >= 2:
            for changed_index in frame["changed_indices"]:
                point = points[int(changed_index)]
                x, y = project([point["x"], point["y"]])
                elements.append(
                    f'<circle cx="{x:.2f}" cy="{y:.2f}" r="1.65" fill="none" stroke="#E64626" stroke-width="0.7" stroke-opacity="0.8"/>'
                )
        for center in frame["centers_before"]:
            x, y = project(center["values"])
            elements.append(
                f'<path d="M{x:.2f},{y-4.5:.2f} L{x+4.5:.2f},{y:.2f} L{x:.2f},{y+4.5:.2f} L{x-4.5:.2f},{y:.2f} Z" fill="#fff" stroke="#111" stroke-width="1.3"/>'
            )
        for center in frame["centers_after"]:
            x, y = project(center["values"])
            segment = str(center["segment"])
            elements.extend(
                [
                    f'<path d="M{x:.2f},{y-5:.2f} L{x+5:.2f},{y:.2f} L{x:.2f},{y+5:.2f} L{x-5:.2f},{y:.2f} Z" fill="#111" stroke="#fff" stroke-width="1.3"/>',
                    f'<text x="{x+8:.2f}" y="{y-6:.2f}" font-family="Noto Sans, sans-serif" font-size="9" font-weight="700" fill="{ANIMATION_COLORS[segment]}">{segment}</text>',
                ]
            )
        if frame["iteration"] == 1:
            iteration_note = "First assignment · hollow = old center · solid = new center"
        elif frame["iteration"] == 15:
            iteration_note = "0 assignments changed · stable · ARI=1 vs final"
        else:
            previous_iteration = frame["iteration"] - 1
            iteration_note = (
                f'{frame["changed_count"]:,} assignments changed vs iteration '
                f"{previous_iteration} · outlined points changed"
            )
        elements.append(
            f'<text x="782" y="306" text-anchor="end" font-family="Noto Sans, sans-serif" font-size="8.5" font-weight="700" fill="#565656">{iteration_note}</text>'
        )

    if step >= 5:
        legend_x = 545
        for index, segment in enumerate(("S1", "S2", "S3", "S4")):
            x = legend_x + index * 58
            elements.append(f'<circle cx="{x}" cy="17" r="4" fill="{ANIMATION_COLORS[segment]}"/><text x="{x+7}" y="20" font-family="Noto Sans, sans-serif" font-size="9" fill="#565656">{segment}</text>')
    elements.append('</svg>')
    return "".join(elements)


def _write_animation_assets(output_dir: Path, payload: dict[str, Any]) -> list[Path]:
    assets = []
    for step in range(20):
        path = output_dir / f"kmeans-step-{step}.svg"
        _write_text_atomic(path, _animation_svg(payload["points"], payload["kmeans_animation"], step))
        assets.append(path)
    return assets


def _source_facts(csv_path: Path) -> dict[str, Any]:
    source = pd.read_csv(
        csv_path,
        dtype={
            "InvoiceNo": "string",
            "StockCode": "string",
            "Description": "string",
            "CustomerID": "string",
            "Country": "string",
        },
        keep_default_na=True,
        low_memory=False,
    )
    source["InvoiceDate"] = pd.to_datetime(source["InvoiceDate"], format="mixed", errors="raise")
    source["Quantity"] = pd.to_numeric(source["Quantity"], errors="raise")
    source["UnitPrice"] = pd.to_numeric(source["UnitPrice"], errors="raise")
    duplicate_extras = int(source.duplicated(keep="first").sum())
    result = {
        "raw_rows": int(len(source)),
        "fields": int(len(source.columns)),
        "unique_invoices": int(source["InvoiceNo"].nunique(dropna=True)),
        "date_start": source["InvoiceDate"].min().strftime("%Y-%m-%d"),
        "date_end": source["InvoiceDate"].max().strftime("%Y-%m-%d"),
        "missing_customer_rows": int(source["CustomerID"].isna().sum()),
        "missing_customer_share": float(source["CustomerID"].isna().mean()),
        "duplicate_extra_rows": duplicate_extras,
        "deduplicated_rows": int(len(source) - duplicate_extras),
    }
    if result["raw_rows"] != EXPECTED["raw_rows"]:
        raise AssertionError(f"Unexpected raw row count: {result['raw_rows']}")
    if result["deduplicated_rows"] != EXPECTED["deduplicated_rows"]:
        raise AssertionError(f"Unexpected deduplicated row count: {result['deduplicated_rows']}")
    return result


def _database_payload(database_path: Path) -> dict[str, Any]:
    assert_schema_version(database_path)
    with connect_read_only(database_path) as connection:
        customers = pd.read_sql_query(
            "SELECT * FROM customer_segments ORDER BY customer_id", connection
        )
        profiles = pd.read_sql_query(
            "SELECT * FROM segment_profiles ORDER BY segment_order", connection
        )
        centroids = pd.read_sql_query(
            "SELECT * FROM cluster_centroids ORDER BY segment_code", connection
        )
        timeline = pd.read_sql_query(
            """
            SELECT invoice_no, invoice_date, invoice_amount, line_count,
                   is_cancellation, has_valid_positive_line
            FROM customer_invoice_timeline
            WHERE customer_id = ?
            ORDER BY invoice_date, invoice_no
            """,
            connection,
            params=(DEMO_CUSTOMER_ID,),
        )
        metadata = dict(
            connection.execute(
                "SELECT metadata_key, metadata_value FROM model_metadata"
            ).fetchall()
        )
        transaction_counts = connection.execute(
            """
            SELECT COUNT(*) AS known_lines,
                   SUM(is_valid_positive_purchase) AS positive_lines
            FROM transaction_lines
            """
        ).fetchone()

    if len(customers) != EXPECTED["customers"]:
        raise AssertionError(f"Unexpected customer count: {len(customers)}")
    if customers["any_capped_flag"].sum() != EXPECTED["cap_affected_customers"]:
        raise AssertionError("Unexpected cap-affected customer count")
    segment_counts = customers["segment_code"].value_counts().sort_index().to_dict()
    if segment_counts != EXPECTED["segment_counts"]:
        raise AssertionError(f"Unexpected segment counts: {segment_counts}")

    high = profiles.loc[profiles["segment_code"].isin(["S3", "S4"])]
    demo = customers.loc[customers["customer_id"].eq(DEMO_CUSTOMER_ID)].iloc[0]
    if len(timeline) != 41 or int(timeline["is_cancellation"].sum()) != 8:
        raise AssertionError("Customer 13777 timeline no longer matches the frozen presentation")

    point_rows = []
    for index, row in enumerate(customers.itertuples(index=False), start=1):
        is_demo = str(row.customer_id) == DEMO_CUSTOMER_ID
        point_rows.append(
            {
                "id": DEMO_CUSTOMER_ID if is_demo else f"P{index:04d}",
                "segment": row.segment_code,
                "x": round(float(row.scaled_recency), 8),
                "y": round(float(row.scaled_frequency), 8),
                "z": round(float(row.scaled_net_monetary), 8),
                "r": int(row.recency),
                "f": int(row.frequency),
                "m": round(float(row.net_monetary), 2),
                "capped": bool(row.any_capped_flag),
                "demo": is_demo,
            }
        )

    profile_columns = [
        "segment_code",
        "segment_order",
        "segment_name",
        "description",
        "strategy_hypothesis",
        "future_kpis",
        "customers",
        "customer_share",
        "net_monetary_total",
        "net_monetary_share",
        "recency_median",
        "frequency_median",
        "net_monetary_median",
    ]
    centroid_columns = [
        "segment_code",
        "scaled_recency",
        "scaled_frequency",
        "scaled_net_monetary",
    ]
    timeline["invoice_date"] = pd.to_datetime(timeline["invoice_date"]).dt.strftime(
        "%Y-%m-%dT%H:%M:%S"
    )
    timeline["invoice_amount"] = timeline["invoice_amount"].round(2)

    return {
        "build": {
            "build_id": metadata["build_id"],
            "input_sha256": metadata["input_sha256"],
            "assignment_sha256": metadata["assignment_sha256"],
            "pipeline_id": PIPELINE_ID,
            "reference_date": metadata["reference_date"],
            "frequency_cap": float(metadata["frequency_cap"]),
            "net_monetary_cap": float(metadata["net_monetary_cap"]),
            "k": int(metadata["k"]),
            "n_init": int(metadata["n_init"]),
            "random_state": int(metadata["random_state"]),
        },
        "funnel": {
            "known_transaction_lines": int(transaction_counts["known_lines"]),
            "valid_positive_lines": int(transaction_counts["positive_lines"]),
            "customers": int(len(customers)),
            "cap_affected_customers": int(customers["any_capped_flag"].sum()),
        },
        "findings": {
            "s3_s4_customers": int(high["customers"].sum()),
            "s3_s4_customer_share": float(high["customer_share"].sum()),
            "s3_s4_net_share": float(high["net_monetary_share"].sum()),
            "clustered_net_total": float(customers["net_monetary"].sum()),
        },
        "long_tail": {
            "frequency_median": float(customers["frequency"].median()),
            "frequency_q995": float(customers["frequency"].quantile(0.995)),
            "frequency_max": int(customers["frequency"].max()),
            "net_median": float(customers["net_monetary"].median()),
            "net_q995": float(customers["net_monetary"].quantile(0.995)),
            "net_max": float(customers["net_monetary"].max()),
        },
        "refund_case": {
            "gross_monetary": float(
                customers.loc[customers["customer_id"].eq("16446"), "gross_monetary"].iloc[0]
            ),
            "net_monetary": float(
                customers.loc[customers["customer_id"].eq("16446"), "net_monetary"].iloc[0]
            ),
        },
        "profiles": _records(profiles[profile_columns]),
        "centroids": _records(centroids[centroid_columns]),
        "points": point_rows,
        "demo_customer": {
            "customer_id": DEMO_CUSTOMER_ID,
            "segment": demo["segment_code"],
            "recency": int(demo["recency"]),
            "frequency": int(demo["frequency"]),
            "net_monetary": float(demo["net_monetary"]),
            "centroid_distance": float(demo["centroid_distance"]),
            "invoice_count": int(len(timeline)),
            "cancellation_count": int(timeline["is_cancellation"].sum()),
            "timeline": _records(timeline),
        },
        "kmeans_animation": _kmeans_animation(customers),
    }


def _k_evidence(evidence_root: Path) -> list[dict[str, Any]]:
    path = evidence_root / MAIN_EVIDENCE
    if not path.is_file():
        raise FileNotFoundError(f"Presentation evidence not found: {path}")
    evidence = pd.read_csv(path)
    selected = evidence.loc[evidence["pipeline_id"].eq(PIPELINE_ID)].copy()
    selected = selected.loc[selected["k"].between(2, 8)].sort_values("k")
    if selected["k"].tolist() != list(range(2, 9)):
        raise AssertionError("Expected complete k=2..8 evidence for the final pipeline")
    columns = [
        "k",
        "median_inertia",
        "median_silhouette_full",
        "median_pairwise_ari",
        "median_min_cluster_size",
        "median_min_cluster_share",
    ]
    return _records(selected[columns])


def _copy_plotly_runtime(output_dir: Path) -> Path:
    source = Path(plotly.__file__).resolve().parent / "package_data" / "plotly.min.js"
    if not source.is_file():
        raise FileNotFoundError(f"Bundled Plotly runtime not found: {source}")
    destination = output_dir / "plotly.min.js"
    if not destination.is_file() or sha256_file(destination) != sha256_file(source):
        shutil.copyfile(source, destination)
    return destination


def export_presentation(
    csv_path: Path,
    database_path: Path,
    output_dir: Path,
    evidence_root: Path,
) -> dict[str, Any]:
    csv_path = Path(csv_path).resolve()
    database_path = Path(database_path).resolve()
    output_dir = Path(output_dir).resolve()
    evidence_root = Path(evidence_root).resolve()
    if not csv_path.is_file():
        raise FileNotFoundError(f"Source CSV not found: {csv_path}")
    if not database_path.is_file():
        raise FileNotFoundError(f"SQLite artifact not found: {database_path}")

    source_sha = sha256_file(csv_path)
    payload = {
        "schema_version": STATIC_SCHEMA_VERSION,
        "generated_at": datetime.now(UTC).isoformat(),
        "source": _source_facts(csv_path),
        **_database_payload(database_path),
        "k_evidence": _k_evidence(evidence_root),
    }
    if payload["build"]["input_sha256"] != source_sha:
        raise AssertionError("CSV hash differs from the SQLite model input hash")

    output_dir.mkdir(parents=True, exist_ok=True)
    data_path = output_dir / "data.json"
    _write_json_atomic(data_path, payload)
    runtime_path = _copy_plotly_runtime(output_dir)
    animation_paths = _write_animation_assets(output_dir, payload)
    data_sha = sha256_file(data_path)
    manifest = {
        "schema_version": STATIC_SCHEMA_VERSION,
        "build_id": payload["build"]["build_id"],
        "input_sha256": source_sha,
        "assignment_sha256": payload["build"]["assignment_sha256"],
        "files": {
            "data.json": {"sha256": data_sha, "bytes": data_path.stat().st_size},
            "plotly.min.js": {
                "sha256": sha256_file(runtime_path),
                "bytes": runtime_path.stat().st_size,
            },
            **{
                path.name: {"sha256": sha256_file(path), "bytes": path.stat().st_size}
                for path in animation_paths
            },
        },
        "data_payload_sha256": _sha256_bytes(
            json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        ),
    }
    manifest_path = output_dir / "manifest.json"
    _write_json_atomic(manifest_path, manifest)
    return {
        "status": "PASS",
        "output_dir": str(output_dir),
        "customers": len(payload["points"]),
        "centroids": len(payload["centroids"]),
        "timeline_invoices": payload["demo_customer"]["invoice_count"],
        "data_sha256": data_sha,
    }

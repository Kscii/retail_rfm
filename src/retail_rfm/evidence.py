from __future__ import annotations

from pathlib import Path

import pandas as pd

from .constants import EVIDENCE_FILES, PIPELINE_ID
from .modeling import sha256_file


def validate_evidence_files(evidence_root: Path) -> dict[str, str]:
    root = Path(evidence_root)
    hashes: dict[str, str] = {}
    missing = [str(root / relative) for relative in EVIDENCE_FILES if not (root / relative).is_file()]
    if missing:
        raise FileNotFoundError(f"Required validated evidence is missing: {missing}")
    for relative in EVIDENCE_FILES:
        path = root / relative
        hashes[relative.as_posix()] = sha256_file(path)

    k_evidence = pd.read_csv(root / EVIDENCE_FILES[0])
    selected = k_evidence.loc[k_evidence["pipeline_id"].eq(PIPELINE_ID)]
    if sorted(selected["k"].astype(int).tolist()) != list(range(2, 9)):
        raise ValueError("Selected k=2…8 evidence is incomplete")
    cap = pd.read_csv(root / "presenter-guide/tables/cap-threshold-summary.csv")
    if set(cap["threshold_id"]) != {"none", "cap990", "cap995", "cap999"}:
        raise ValueError("Cap-threshold evidence is incomplete")
    directed = pd.read_csv(root / "directed-sensitivity/tables/directed-baseline-comparison.csv")
    if set(directed["variant_id"]) != {"duplicates_kept", "product_like_only", "uk_only"}:
        raise ValueError("Directed-sensitivity evidence is incomplete")
    if directed["hard_stop_triggered"].astype(bool).any():
        raise ValueError("Archived sensitivity evidence contains a hard-stop result")
    return hashes


def normalized_evidence(evidence_root: Path) -> pd.DataFrame:
    root = Path(evidence_root)
    rows: list[dict] = []

    k_frame = pd.read_csv(root / "rfm-model-exploration/tables/pipeline-k-evidence.csv")
    k_frame = k_frame.loc[k_frame["pipeline_id"].eq(PIPELINE_ID)].sort_values("k")
    for record in k_frame.to_dict("records"):
        for metric, unit in (
            ("median_inertia", "squared_distance"),
            ("median_silhouette_full", "score"),
            ("median_pairwise_ari", "score"),
            ("median_min_cluster_share", "share"),
        ):
            rows.append(
                {
                    "EvidenceType": "k_selection",
                    "Candidate": "Net cap99.5 Standard",
                    "K": int(record["k"]),
                    "MetricName": metric,
                    "MetricValue": float(record[metric]),
                    "Unit": unit,
                    "Note": "50 fixed seeds; full-population silhouette",
                    "SourcePath": "rfm-model-exploration/tables/pipeline-k-evidence.csv",
                }
            )

    cap_frame = pd.read_csv(root / "presenter-guide/tables/cap-threshold-summary.csv")
    for record in cap_frame.to_dict("records"):
        for metric, unit in (
            ("median_silhouette_full", "score"),
            ("median_pairwise_ari", "score"),
            ("median_min_cluster_share", "share"),
            ("either_affected", "customers"),
        ):
            rows.append(
                {
                    "EvidenceType": "cap_sensitivity",
                    "Candidate": str(record["display_name"]),
                    "K": 4,
                    "MetricName": metric,
                    "MetricValue": float(record[metric]),
                    "Unit": unit,
                    "Note": "F and Net M upper-tail treatment",
                    "SourcePath": "presenter-guide/tables/cap-threshold-summary.csv",
                }
            )

    directed = pd.read_csv(root / "directed-sensitivity/tables/directed-baseline-comparison.csv")
    for record in directed.to_dict("records"):
        for metric, unit in (
            ("representative_common_ari", "score"),
            ("k4_median_pairwise_ari", "score"),
            ("variant_s3s4_net_share", "share"),
            ("top_cluster_customer_share", "share"),
        ):
            rows.append(
                {
                    "EvidenceType": "directed_sensitivity",
                    "Candidate": str(record["display_name"]),
                    "K": 4,
                    "MetricName": metric,
                    "MetricValue": float(record[metric]),
                    "Unit": unit,
                    "Note": "PASS; no predefined hard stop triggered",
                    "SourcePath": "directed-sensitivity/tables/directed-baseline-comparison.csv",
                }
            )

    representative = pd.read_csv(
        root / "rfm-model-exploration/tables/representative-model-metrics.csv"
    )
    route_specs = (
        ("all_4338__net__standard", 4, "Standard / k=4"),
        ("all_4338__net__robust", 2, "Robust / k=2"),
        ("positive_net_4317__net__log1p_standard", 3, "Log / k=3"),
        (PIPELINE_ID, 4, "Cap99.5 / k=4"),
    )
    for pipeline_id, k, label in route_specs:
        selected = representative.loc[
            representative["pipeline_id"].eq(pipeline_id) & representative["k"].eq(k)
        ]
        if len(selected) != 1:
            raise ValueError(f"Missing preprocessing representative: {pipeline_id}, k={k}")
        record = selected.iloc[0]
        for metric, unit in (
            ("silhouette_full", "score"),
            ("min_cluster_share", "share"),
            ("min_cluster_size", "customers"),
        ):
            rows.append(
                {
                    "EvidenceType": "preprocessing",
                    "Candidate": label,
                    "K": k,
                    "MetricName": metric,
                    "MetricValue": float(record[metric]),
                    "Unit": unit,
                    "Note": "Representative n_init=20 model; explanatory comparison",
                    "SourcePath": "rfm-model-exploration/tables/representative-model-metrics.csv",
                }
            )
    return pd.DataFrame(rows)

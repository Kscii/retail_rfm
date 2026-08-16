from __future__ import annotations

import itertools
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.preprocessing import StandardScaler

from .constants import MODEL_SEED
from .modeling import build_rfm, prepare_known_lines, read_source


SEEDS = tuple(range(50))
K_VALUES = tuple(range(2, 9))


def _matrix(rfm: pd.DataFrame, quantile: float | None) -> tuple[np.ndarray, dict[str, float]]:
    values = rfm[["Recency", "Frequency", "NetMonetary"]].astype(float).copy()
    if quantile is None:
        frequency_cap = np.nan
        monetary_cap = np.nan
        affected = 0
    else:
        frequency_cap = float(values["Frequency"].quantile(quantile))
        monetary_cap = float(values["NetMonetary"].quantile(quantile))
        affected = int(
            ((values["Frequency"] > frequency_cap) | (values["NetMonetary"] > monetary_cap)).sum()
        )
        values["Frequency"] = values["Frequency"].clip(upper=frequency_cap)
        values["NetMonetary"] = values["NetMonetary"].clip(upper=monetary_cap)
    matrix = StandardScaler().fit_transform(values)
    if not np.isfinite(matrix).all():
        raise AssertionError("Deep verification produced non-finite model input")
    return matrix, {
        "frequency_cap": frequency_cap,
        "net_monetary_cap": monetary_cap,
        "either_affected": affected,
    }


def _fit(X: np.ndarray, k: int, seed: int, n_init: int) -> tuple[np.ndarray, dict[str, float]]:
    model = KMeans(
        n_clusters=k,
        init="k-means++",
        n_init=n_init,
        random_state=seed,
        algorithm="lloyd",
        max_iter=300,
        tol=1e-4,
    ).fit(X)
    labels = model.labels_.astype(np.int16)
    sizes = np.bincount(labels, minlength=k)
    return labels, {
        "inertia": float(model.inertia_),
        "silhouette": float(silhouette_score(X, labels, metric="euclidean")),
        "min_cluster_share": float(sizes.min() / len(labels)),
    }


def _seed_summary(X: np.ndarray, k: int) -> tuple[dict[str, float], np.ndarray]:
    labels = np.empty((len(SEEDS), len(X)), dtype=np.int16)
    rows = []
    for index, seed in enumerate(SEEDS):
        labels[index], metrics = _fit(X, k, seed, 1)
        rows.append(metrics)
    pairwise_ari = np.asarray(
        [
            adjusted_rand_score(labels[left], labels[right])
            for left, right in itertools.combinations(range(len(SEEDS)), 2)
        ]
    )
    frame = pd.DataFrame(rows)
    return {
        "median_inertia": float(frame["inertia"].median()),
        "median_silhouette_full": float(frame["silhouette"].median()),
        "median_pairwise_ari": float(np.median(pairwise_ari)),
        "median_min_cluster_share": float(frame["min_cluster_share"].median()),
    }, labels


def _representative(X: np.ndarray, k: int = 4) -> np.ndarray:
    labels, _ = _fit(X, k, MODEL_SEED, 20)
    return labels


def _assert_close(label: str, actual: float, expected: float, tolerance: float = 1e-9) -> None:
    if not np.isclose(actual, expected, atol=tolerance, rtol=0):
        raise AssertionError(f"{label}: actual={actual!r}, expected={expected!r}")


def _semantic_profile(rfm: pd.DataFrame, labels: np.ndarray) -> dict[str, float | bool]:
    data = rfm.assign(RawCluster=labels)
    order = (
        data.groupby("RawCluster")["NetMonetary"].median().sort_values(kind="stable").index
    )
    profiles = []
    total = float(data["NetMonetary"].sum())
    for position, raw_cluster in enumerate(order, start=1):
        group = data.loc[data["RawCluster"].eq(raw_cluster)]
        profiles.append(
            {
                "order": position,
                "r": float(group["Recency"].median()),
                "f": float(group["Frequency"].median()),
                "m": float(group["NetMonetary"].median()),
                "customer_share": float(len(group) / len(data)),
                "net_share": float(group["NetMonetary"].sum() / total),
            }
        )
    frame = pd.DataFrame(profiles)
    ordering = bool(
        np.all(np.diff(frame["r"]) <= 0)
        and np.all(np.diff(frame["f"]) >= 0)
        and np.all(np.diff(frame["m"]) >= 0)
    )
    return {
        "ordering": ordering,
        "s3s4_net_share": float(frame.loc[frame["order"].isin([3, 4]), "net_share"].sum()),
        "s4_customer_share": float(frame.loc[frame["order"].eq(4), "customer_share"].iloc[0]),
    }


def deep_verify(csv_path: Path, evidence_root: Path) -> dict:
    source = read_source(Path(csv_path))
    evidence_root = Path(evidence_root)
    baseline_rfm = build_rfm(source.known_lines)
    baseline_X, _ = _matrix(baseline_rfm, 0.995)

    archived_k = pd.read_csv(
        evidence_root / "rfm-model-exploration/tables/pipeline-k-evidence.csv"
    )
    archived_k = archived_k.loc[
        archived_k["pipeline_id"].eq("all_4338__net__cap995_standard")
    ].set_index("k")
    baseline_summaries: dict[int, dict[str, float]] = {}
    for k in K_VALUES:
        summary, _ = _seed_summary(baseline_X, k)
        baseline_summaries[k] = summary
        for metric in (
            "median_inertia",
            "median_silhouette_full",
            "median_pairwise_ari",
            "median_min_cluster_share",
        ):
            _assert_close(f"baseline k={k} {metric}", summary[metric], float(archived_k.loc[k, metric]))

    if not (
        baseline_summaries[4]["median_silhouette_full"]
        > baseline_summaries[3]["median_silhouette_full"]
        > baseline_summaries[5]["median_silhouette_full"]
    ):
        raise AssertionError("Baseline neighboring-k evidence no longer supports k=4")

    archived_cap = pd.read_csv(
        evidence_root / "presenter-guide/tables/cap-threshold-summary.csv"
    ).set_index("threshold_id")
    cap_specs = (("none", None), ("cap990", 0.99), ("cap995", 0.995), ("cap999", 0.999))
    cap_results = {}
    for threshold_id, quantile in cap_specs:
        matrix, transform = _matrix(baseline_rfm, quantile)
        summary, _ = _seed_summary(matrix, 4)
        cap_results[threshold_id] = {**summary, **transform}
        for metric in (
            "median_inertia",
            "median_silhouette_full",
            "median_pairwise_ari",
            "median_min_cluster_share",
        ):
            _assert_close(
                f"cap {threshold_id} {metric}", summary[metric], float(archived_cap.loc[threshold_id, metric])
            )
        if int(transform["either_affected"]) != int(archived_cap.loc[threshold_id, "either_affected"]):
            raise AssertionError(f"cap {threshold_id} affected-customer count differs")

    baseline_rep = _representative(baseline_X)
    baseline_ids = baseline_rfm["CustomerID"].astype(str).to_numpy()
    baseline_assignments = pd.DataFrame({"CustomerID": baseline_ids, "Label": baseline_rep})
    baseline_profile = _semantic_profile(baseline_rfm, baseline_rep)
    archived_directed = pd.read_csv(
        evidence_root / "directed-sensitivity/tables/directed-baseline-comparison.csv"
    ).set_index("variant_id")

    variant_lines = {
        "duplicates_kept": prepare_known_lines(source.raw),
        "product_like_only": source.known_lines.loc[source.known_lines["IsProductLike"]].copy(),
        "uk_only": source.known_lines.loc[source.known_lines["Country"].eq("United Kingdom")].copy(),
    }
    directed_results = {}
    for variant_id, lines in variant_lines.items():
        rfm = build_rfm(lines)
        matrix, _ = _matrix(rfm, 0.995)
        summaries = {}
        for k in K_VALUES:
            summaries[k], _ = _seed_summary(matrix, k)
        labels = _representative(matrix)
        assignments = pd.DataFrame(
            {"CustomerID": rfm["CustomerID"].astype(str).to_numpy(), "LabelVariant": labels}
        )
        common = baseline_assignments.merge(assignments, on="CustomerID", validate="one_to_one")
        common_ari = float(adjusted_rand_score(common["Label"], common["LabelVariant"]))
        profile = _semantic_profile(rfm, labels)
        directed_results[variant_id] = {
            "common_ari": common_ari,
            "k4_median_ari": summaries[4]["median_pairwise_ari"],
            "k4_median_silhouette": summaries[4]["median_silhouette_full"],
            **profile,
        }
        archived = archived_directed.loc[variant_id]
        _assert_close(
            f"{variant_id} common ARI", common_ari, float(archived["representative_common_ari"])
        )
        _assert_close(
            f"{variant_id} k4 ARI",
            summaries[4]["median_pairwise_ari"],
            float(archived["k4_median_pairwise_ari"]),
        )
        _assert_close(
            f"{variant_id} k4 silhouette",
            summaries[4]["median_silhouette_full"],
            float(archived["k4_median_silhouette"]),
        )
        _assert_close(
            f"{variant_id} S3+S4 share",
            float(profile["s3s4_net_share"]),
            float(archived["variant_s3s4_net_share"]),
        )
        if (
            common_ari < 0.8
            or summaries[4]["median_pairwise_ari"] < 0.8
            or not profile["ordering"]
            or abs(float(profile["s3s4_net_share"]) - float(baseline_profile["s3s4_net_share"])) > 0.10
            or float(profile["s4_customer_share"]) < 0.01
        ):
            raise AssertionError(f"Directed sensitivity stop condition triggered: {variant_id}")

    return {
        "status": "PASS",
        "single_init_fits": 1_600,
        "full_population_silhouette": True,
        "baseline_k_values": list(K_VALUES),
        "cap_thresholds": [item[0] for item in cap_specs],
        "directed_variants": directed_results,
    }

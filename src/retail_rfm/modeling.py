from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from .constants import (
    CAP_QUANTILE,
    EXPECTED,
    FEATURE_NAMES,
    MODEL_K,
    MODEL_N_INIT,
    MODEL_SEED,
    PRODUCT_LIKE_PATTERN,
    REFERENCE_DATE,
    SCHEMA_VERSION,
    SEGMENTS,
)

SOURCE_COLUMNS = (
    "InvoiceNo",
    "StockCode",
    "Description",
    "Quantity",
    "InvoiceDate",
    "UnitPrice",
    "CustomerID",
    "Country",
)
STRING_COLUMNS = ("InvoiceNo", "StockCode", "Description", "CustomerID", "Country")


@dataclass
class SourceData:
    raw: pd.DataFrame
    deduplicated: pd.DataFrame
    known_lines: pd.DataFrame
    duplicate_extra_rows: int


@dataclass
class ModelResult:
    rfm: pd.DataFrame
    customer_segments: pd.DataFrame
    customer_countries: pd.DataFrame
    segment_profiles: pd.DataFrame
    cluster_centroids: pd.DataFrame
    scaler: StandardScaler
    model: KMeans
    raw_cluster_to_segment: dict[int, str]
    frequency_cap: float
    net_monetary_cap: float
    assignment_sha256: str


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def read_source(csv_path: Path) -> SourceData:
    csv_path = Path(csv_path)
    raw = pd.read_csv(
        csv_path,
        dtype={column: "string" for column in STRING_COLUMNS},
        keep_default_na=True,
        low_memory=False,
    )
    if tuple(raw.columns) != SOURCE_COLUMNS:
        raise ValueError(f"Unexpected CSV columns: {tuple(raw.columns)!r}")

    raw["SourceRowNumber"] = np.arange(2, len(raw) + 2, dtype=np.int64)
    duplicate_mask = raw.loc[:, SOURCE_COLUMNS].duplicated(keep="first")
    deduplicated = raw.loc[~duplicate_mask].copy()

    for frame in (raw, deduplicated):
        frame["InvoiceNo"] = frame["InvoiceNo"].str.strip()
        frame["StockCode"] = frame["StockCode"].str.strip().str.upper()
        frame["CustomerID"] = frame["CustomerID"].str.strip()
        frame["Country"] = frame["Country"].str.strip()
        frame["Quantity"] = pd.to_numeric(frame["Quantity"], errors="raise").astype("int64")
        frame["UnitPrice"] = pd.to_numeric(frame["UnitPrice"], errors="raise").astype("float64")
        frame["InvoiceDate"] = pd.to_datetime(frame["InvoiceDate"], errors="raise", format="mixed")
        frame["LineAmount"] = frame["Quantity"] * frame["UnitPrice"]

    known_lines = prepare_known_lines(deduplicated)

    return SourceData(
        raw=raw,
        deduplicated=deduplicated,
        known_lines=known_lines,
        duplicate_extra_rows=int(duplicate_mask.sum()),
    )


def prepare_known_lines(frame: pd.DataFrame) -> pd.DataFrame:
    known = frame["CustomerID"].notna() & frame["CustomerID"].ne("")
    known_lines = frame.loc[known].copy()
    if "LineID" in known_lines:
        known_lines = known_lines.drop(columns="LineID")
    known_lines.insert(0, "LineID", np.arange(1, len(known_lines) + 1, dtype=np.int64))
    known_lines["IsCancellation"] = known_lines["InvoiceNo"].str.startswith("C", na=False)
    known_lines["IsNonpositiveQuantity"] = known_lines["Quantity"] <= 0
    known_lines["IsNonpositivePrice"] = known_lines["UnitPrice"] <= 0
    known_lines["IsValidPositivePurchase"] = (
        ~known_lines["IsCancellation"]
        & ~known_lines["IsNonpositiveQuantity"]
        & ~known_lines["IsNonpositivePrice"]
    )
    known_lines["IsProductLike"] = known_lines["StockCode"].str.fullmatch(
        PRODUCT_LIKE_PATTERN, na=False
    )

    return known_lines


def build_rfm(lines: pd.DataFrame, reference_date: str = REFERENCE_DATE) -> pd.DataFrame:
    reference = pd.Timestamp(reference_date)
    positive = lines.loc[lines["IsValidPositivePurchase"]].copy()
    positive["PurchaseDay"] = positive["InvoiceDate"].dt.normalize()
    positive_rfm = positive.groupby("CustomerID", sort=True).agg(
        LastPurchase=("PurchaseDay", "max"),
        Frequency=("InvoiceNo", "nunique"),
        GrossMonetary=("LineAmount", "sum"),
    )
    positive_rfm["Recency"] = (reference - positive_rfm["LastPurchase"]).dt.days.astype("int64")
    net = lines.groupby("CustomerID", sort=True)["LineAmount"].sum().rename("NetMonetary")
    countries = (
        lines.groupby("CustomerID", sort=True)["Country"]
        .agg(lambda values: " | ".join(sorted(set(values.dropna().astype(str)))))
        .rename("CountryDisplay")
    )
    rfm = positive_rfm.join(net, how="left").join(countries, how="left").reset_index()
    rfm = rfm[
        [
            "CustomerID",
            "CountryDisplay",
            "LastPurchase",
            "Recency",
            "Frequency",
            "GrossMonetary",
            "NetMonetary",
        ]
    ].sort_values("CustomerID", kind="stable", ignore_index=True)
    return rfm


def build_customer_countries(lines: pd.DataFrame, customer_ids: pd.Series) -> pd.DataFrame:
    selected = lines.loc[lines["CustomerID"].isin(set(customer_ids.astype(str)))].copy()
    grouped = (
        selected.groupby(["CustomerID", "Country"], as_index=False, dropna=False)
        .agg(
            TransactionLines=("LineID", "size"),
            DistinctInvoices=("InvoiceNo", "nunique"),
            NetMonetary=("LineAmount", "sum"),
        )
        .sort_values(["CustomerID", "Country"], kind="stable", ignore_index=True)
    )
    return grouped


def assignment_fingerprint(customer_ids: pd.Series, segments: pd.Series) -> str:
    payload = "\n".join(
        f"{customer_id},{segment}"
        for customer_id, segment in zip(customer_ids.astype(str), segments.astype(str), strict=True)
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def semantic_cluster_mapping(rfm: pd.DataFrame, labels: np.ndarray) -> dict[int, str]:
    labeled = rfm.assign(RawCluster=np.asarray(labels, dtype=int))
    raw_order = (
        labeled.groupby("RawCluster")["NetMonetary"]
        .median()
        .sort_values(kind="stable")
        .index.tolist()
    )
    return {int(raw): f"S{position + 1}" for position, raw in enumerate(raw_order)}


def fit_model(rfm: pd.DataFrame) -> ModelResult:
    model_input = rfm[["Recency", "Frequency", "NetMonetary"]].astype("float64").copy()
    frequency_cap = float(model_input["Frequency"].quantile(CAP_QUANTILE))
    net_cap = float(model_input["NetMonetary"].quantile(CAP_QUANTILE))
    frequency_capped = model_input["Frequency"] > frequency_cap
    monetary_capped = model_input["NetMonetary"] > net_cap
    model_input["Frequency"] = model_input["Frequency"].clip(upper=frequency_cap)
    model_input["NetMonetary"] = model_input["NetMonetary"].clip(upper=net_cap)

    scaler = StandardScaler()
    scaled = scaler.fit_transform(model_input)
    model = KMeans(
        n_clusters=MODEL_K,
        init="k-means++",
        n_init=MODEL_N_INIT,
        random_state=MODEL_SEED,
        algorithm="lloyd",
        max_iter=300,
        tol=1e-4,
    ).fit(scaled)

    raw_to_segment = semantic_cluster_mapping(rfm, model.labels_)
    segment_codes = pd.Series(model.labels_, index=rfm.index).map(raw_to_segment)
    distances = np.linalg.norm(scaled - model.cluster_centers_[model.labels_], axis=1)

    customers = rfm.copy()
    customers["FrequencyCapped"] = model_input["Frequency"].to_numpy()
    customers["NetMonetaryCapped"] = model_input["NetMonetary"].to_numpy()
    customers["ScaledRecency"] = scaled[:, 0]
    customers["ScaledFrequency"] = scaled[:, 1]
    customers["ScaledNetMonetary"] = scaled[:, 2]
    customers["RawCluster"] = model.labels_.astype("int64")
    customers["SegmentCode"] = segment_codes
    customers["CentroidDistance"] = distances
    customers["FrequencyCappedFlag"] = frequency_capped.to_numpy()
    customers["MonetaryCappedFlag"] = monetary_capped.to_numpy()
    customers["AnyCappedFlag"] = (frequency_capped | monetary_capped).to_numpy()
    customers["IsRepresentative"] = False
    representative_indices = customers.groupby("SegmentCode")["CentroidDistance"].idxmin()
    customers.loc[representative_indices, "IsRepresentative"] = True

    net_total = float(customers["NetMonetary"].sum())
    profile_rows: list[dict[str, Any]] = []
    for segment_code in sorted(SEGMENTS):
        group = customers.loc[customers["SegmentCode"].eq(segment_code)]
        definition = SEGMENTS[segment_code]
        row: dict[str, Any] = {
            "SegmentCode": segment_code,
            "SegmentOrder": int(segment_code[1:]),
            "SegmentName": definition["name"],
            "Description": definition["description"],
            "StrategyHypothesis": definition["hypothesis"],
            "FutureKPIs": definition["future_kpis"],
            "Customers": int(len(group)),
            "CustomerShare": float(len(group) / len(customers)),
            "NetMonetaryTotal": float(group["NetMonetary"].sum()),
            "NetMonetaryShare": float(group["NetMonetary"].sum() / net_total),
        }
        for column in ("Recency", "Frequency", "GrossMonetary", "NetMonetary"):
            row[f"{column}Mean"] = float(group[column].mean())
            row[f"{column}Q25"] = float(group[column].quantile(0.25))
            row[f"{column}Median"] = float(group[column].median())
            row[f"{column}Q75"] = float(group[column].quantile(0.75))
        profile_rows.append(row)
    profiles = pd.DataFrame(profile_rows)

    centroid_rows = []
    for raw_cluster, segment_code in raw_to_segment.items():
        center = model.cluster_centers_[raw_cluster]
        centroid_rows.append(
            {
                "SegmentCode": segment_code,
                "RawCluster": raw_cluster,
                "ScaledRecency": float(center[0]),
                "ScaledFrequency": float(center[1]),
                "ScaledNetMonetary": float(center[2]),
            }
        )
    centroids = pd.DataFrame(centroid_rows).sort_values("SegmentCode", ignore_index=True)
    fingerprint = assignment_fingerprint(customers["CustomerID"], customers["SegmentCode"])
    # Customer-country rows are populated by build_model_result, which has transaction-line access.
    countries = pd.DataFrame()
    return ModelResult(
        rfm=rfm,
        customer_segments=customers,
        customer_countries=countries,
        segment_profiles=profiles,
        cluster_centroids=centroids,
        scaler=scaler,
        model=model,
        raw_cluster_to_segment=raw_to_segment,
        frequency_cap=frequency_cap,
        net_monetary_cap=net_cap,
        assignment_sha256=fingerprint,
    )


def build_model_result(lines: pd.DataFrame) -> ModelResult:
    rfm = build_rfm(lines)
    result = fit_model(rfm)
    result.customer_countries = build_customer_countries(lines, rfm["CustomerID"])
    return result


def model_bundle(result: ModelResult, input_sha256: str, build_id: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "build_id": build_id,
        "input_sha256": input_sha256,
        "reference_date": REFERENCE_DATE,
        "feature_names": FEATURE_NAMES,
        "cap_quantile": CAP_QUANTILE,
        "frequency_cap": result.frequency_cap,
        "net_monetary_cap": result.net_monetary_cap,
        "scaler": result.scaler,
        "kmeans": result.model,
        "raw_cluster_to_segment": result.raw_cluster_to_segment,
        "assignment_sha256": result.assignment_sha256,
        "segment_definitions": SEGMENTS,
    }


def assert_core_result(source: SourceData, result: ModelResult) -> None:
    checks = {
        "raw_rows": len(source.raw),
        "deduplicated_rows": len(source.deduplicated),
        "duplicate_extra_rows": source.duplicate_extra_rows,
        "known_transaction_lines": len(source.known_lines),
        "known_transaction_customers": source.known_lines["CustomerID"].nunique(),
        "customers": len(result.customer_segments),
        "positive_rows": int(source.known_lines["IsValidPositivePurchase"].sum()),
        "positive_invoices": source.known_lines.loc[
            source.known_lines["IsValidPositivePurchase"], "InvoiceNo"
        ].nunique(),
        "cap_affected_customers": int(result.customer_segments["AnyCappedFlag"].sum()),
        "profiles": len(result.segment_profiles),
        "centroids": len(result.cluster_centroids),
    }
    failures = {
        key: {"expected": EXPECTED[key], "actual": actual}
        for key, actual in checks.items()
        if actual != EXPECTED[key]
    }
    net_total = float(result.customer_segments["NetMonetary"].sum())
    if not np.isclose(net_total, EXPECTED["clustered_net_total"], atol=1e-6, rtol=0):
        failures["clustered_net_total"] = {
            "expected": EXPECTED["clustered_net_total"],
            "actual": net_total,
        }
    if result.assignment_sha256 != EXPECTED["assignment_sha256"]:
        failures["assignment_sha256"] = {
            "expected": EXPECTED["assignment_sha256"],
            "actual": result.assignment_sha256,
        }
    segment_counts = result.customer_segments["SegmentCode"].value_counts().sort_index().to_dict()
    if segment_counts != EXPECTED["segment_counts"]:
        failures["segment_counts"] = {
            "expected": EXPECTED["segment_counts"],
            "actual": segment_counts,
        }
    representatives = (
        result.customer_segments.loc[result.customer_segments["IsRepresentative"]]
        .set_index("SegmentCode")["CustomerID"]
        .sort_index()
        .to_dict()
    )
    if representatives != EXPECTED["representative_customers"]:
        failures["representative_customers"] = {
            "expected": EXPECTED["representative_customers"],
            "actual": representatives,
        }
    if failures:
        raise AssertionError(f"Core result does not match frozen evidence: {failures}")

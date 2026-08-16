from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd

from .constants import SCHEMA_VERSION
from .modeling import ModelResult, SourceData


SCHEMA_SQL = """
CREATE TABLE transaction_lines (
    line_id INTEGER PRIMARY KEY,
    source_row_number INTEGER NOT NULL UNIQUE,
    invoice_no TEXT NOT NULL,
    stock_code TEXT NOT NULL,
    description TEXT,
    quantity INTEGER NOT NULL,
    invoice_date TEXT NOT NULL,
    unit_price REAL NOT NULL,
    customer_id TEXT NOT NULL,
    country TEXT NOT NULL,
    line_amount REAL NOT NULL,
    is_cancellation INTEGER NOT NULL CHECK (is_cancellation IN (0, 1)),
    is_valid_positive_purchase INTEGER NOT NULL CHECK (is_valid_positive_purchase IN (0, 1)),
    is_nonpositive_quantity INTEGER NOT NULL CHECK (is_nonpositive_quantity IN (0, 1)),
    is_nonpositive_price INTEGER NOT NULL CHECK (is_nonpositive_price IN (0, 1)),
    is_product_like INTEGER NOT NULL CHECK (is_product_like IN (0, 1))
);

CREATE TABLE customer_segments (
    customer_id TEXT PRIMARY KEY,
    country_display TEXT NOT NULL,
    last_purchase_date TEXT NOT NULL,
    recency INTEGER NOT NULL,
    frequency INTEGER NOT NULL,
    gross_monetary REAL NOT NULL,
    net_monetary REAL NOT NULL,
    frequency_capped REAL NOT NULL,
    net_monetary_capped REAL NOT NULL,
    scaled_recency REAL NOT NULL,
    scaled_frequency REAL NOT NULL,
    scaled_net_monetary REAL NOT NULL,
    raw_cluster INTEGER NOT NULL,
    segment_code TEXT NOT NULL CHECK (segment_code IN ('S1', 'S2', 'S3', 'S4')),
    centroid_distance REAL NOT NULL,
    frequency_capped_flag INTEGER NOT NULL CHECK (frequency_capped_flag IN (0, 1)),
    monetary_capped_flag INTEGER NOT NULL CHECK (monetary_capped_flag IN (0, 1)),
    any_capped_flag INTEGER NOT NULL CHECK (any_capped_flag IN (0, 1)),
    is_representative INTEGER NOT NULL CHECK (is_representative IN (0, 1))
);

CREATE TABLE customer_countries (
    customer_id TEXT NOT NULL,
    country TEXT NOT NULL,
    transaction_lines INTEGER NOT NULL,
    distinct_invoices INTEGER NOT NULL,
    net_monetary REAL NOT NULL,
    PRIMARY KEY (customer_id, country),
    FOREIGN KEY (customer_id) REFERENCES customer_segments(customer_id)
);

CREATE TABLE segment_profiles (
    segment_code TEXT PRIMARY KEY,
    segment_order INTEGER NOT NULL UNIQUE,
    segment_name TEXT NOT NULL,
    description TEXT NOT NULL,
    strategy_hypothesis TEXT NOT NULL,
    future_kpis TEXT NOT NULL,
    customers INTEGER NOT NULL,
    customer_share REAL NOT NULL,
    net_monetary_total REAL NOT NULL,
    net_monetary_share REAL NOT NULL,
    recency_mean REAL NOT NULL,
    recency_q25 REAL NOT NULL,
    recency_median REAL NOT NULL,
    recency_q75 REAL NOT NULL,
    frequency_mean REAL NOT NULL,
    frequency_q25 REAL NOT NULL,
    frequency_median REAL NOT NULL,
    frequency_q75 REAL NOT NULL,
    gross_monetary_mean REAL NOT NULL,
    gross_monetary_q25 REAL NOT NULL,
    gross_monetary_median REAL NOT NULL,
    gross_monetary_q75 REAL NOT NULL,
    net_monetary_mean REAL NOT NULL,
    net_monetary_q25 REAL NOT NULL,
    net_monetary_median REAL NOT NULL,
    net_monetary_q75 REAL NOT NULL
);

CREATE TABLE cluster_centroids (
    segment_code TEXT PRIMARY KEY,
    raw_cluster INTEGER NOT NULL UNIQUE,
    scaled_recency REAL NOT NULL,
    scaled_frequency REAL NOT NULL,
    scaled_net_monetary REAL NOT NULL,
    FOREIGN KEY (segment_code) REFERENCES segment_profiles(segment_code)
);

CREATE TABLE model_metadata (
    metadata_key TEXT PRIMARY KEY,
    metadata_value TEXT NOT NULL,
    value_type TEXT NOT NULL,
    description TEXT NOT NULL
);

CREATE TABLE model_evidence (
    evidence_id INTEGER PRIMARY KEY AUTOINCREMENT,
    evidence_type TEXT NOT NULL,
    candidate TEXT NOT NULL,
    k INTEGER,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    unit TEXT NOT NULL,
    note TEXT NOT NULL,
    source_path TEXT NOT NULL
);

CREATE INDEX idx_transaction_customer ON transaction_lines(customer_id);
CREATE INDEX idx_transaction_invoice ON transaction_lines(invoice_no);
CREATE INDEX idx_transaction_date ON transaction_lines(invoice_date);
CREATE INDEX idx_transaction_customer_date ON transaction_lines(customer_id, invoice_date);
CREATE INDEX idx_customer_segment ON customer_segments(segment_code);
CREATE INDEX idx_customer_cap ON customer_segments(any_capped_flag);
CREATE INDEX idx_country_country ON customer_countries(country);
CREATE INDEX idx_evidence_type ON model_evidence(evidence_type, metric_name);

CREATE VIEW customer_invoice_timeline AS
SELECT
    customer_id,
    invoice_no,
    MIN(invoice_date) AS invoice_date,
    SUM(line_amount) AS invoice_amount,
    COUNT(*) AS line_count,
    MAX(is_cancellation) AS is_cancellation,
    MAX(is_valid_positive_purchase) AS has_valid_positive_line
FROM transaction_lines
GROUP BY customer_id, invoice_no;
"""


def connect_read_only(path: Path) -> sqlite3.Connection:
    resolved = Path(path).resolve()
    connection = sqlite3.connect(f"file:{resolved}?mode=ro", uri=True, timeout=5)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only = ON")
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _write_frame(connection: sqlite3.Connection, table: str, frame: pd.DataFrame) -> None:
    # Keep each multi-row INSERT below conservative SQLite host-parameter limits.
    frame.to_sql(table, connection, if_exists="append", index=False, method="multi", chunksize=500)


def _transaction_frame(source: SourceData) -> pd.DataFrame:
    lines = source.known_lines.copy()
    result = pd.DataFrame(
        {
            "line_id": lines["LineID"].astype("int64"),
            "source_row_number": lines["SourceRowNumber"].astype("int64"),
            "invoice_no": lines["InvoiceNo"].astype(str),
            "stock_code": lines["StockCode"].astype(str),
            "description": lines["Description"].where(lines["Description"].notna(), None),
            "quantity": lines["Quantity"].astype("int64"),
            "invoice_date": lines["InvoiceDate"].dt.strftime("%Y-%m-%dT%H:%M:%S"),
            "unit_price": lines["UnitPrice"].astype(float),
            "customer_id": lines["CustomerID"].astype(str),
            "country": lines["Country"].astype(str),
            "line_amount": lines["LineAmount"].astype(float),
            "is_cancellation": lines["IsCancellation"].astype("int8"),
            "is_valid_positive_purchase": lines["IsValidPositivePurchase"].astype("int8"),
            "is_nonpositive_quantity": lines["IsNonpositiveQuantity"].astype("int8"),
            "is_nonpositive_price": lines["IsNonpositivePrice"].astype("int8"),
            "is_product_like": lines["IsProductLike"].astype("int8"),
        }
    )
    return result


def _customers_frame(result: ModelResult) -> pd.DataFrame:
    customers = result.customer_segments
    return pd.DataFrame(
        {
            "customer_id": customers["CustomerID"].astype(str),
            "country_display": customers["CountryDisplay"].astype(str),
            "last_purchase_date": customers["LastPurchase"].dt.strftime("%Y-%m-%d"),
            "recency": customers["Recency"].astype("int64"),
            "frequency": customers["Frequency"].astype("int64"),
            "gross_monetary": customers["GrossMonetary"].astype(float),
            "net_monetary": customers["NetMonetary"].astype(float),
            "frequency_capped": customers["FrequencyCapped"].astype(float),
            "net_monetary_capped": customers["NetMonetaryCapped"].astype(float),
            "scaled_recency": customers["ScaledRecency"].astype(float),
            "scaled_frequency": customers["ScaledFrequency"].astype(float),
            "scaled_net_monetary": customers["ScaledNetMonetary"].astype(float),
            "raw_cluster": customers["RawCluster"].astype("int64"),
            "segment_code": customers["SegmentCode"].astype(str),
            "centroid_distance": customers["CentroidDistance"].astype(float),
            "frequency_capped_flag": customers["FrequencyCappedFlag"].astype("int8"),
            "monetary_capped_flag": customers["MonetaryCappedFlag"].astype("int8"),
            "any_capped_flag": customers["AnyCappedFlag"].astype("int8"),
            "is_representative": customers["IsRepresentative"].astype("int8"),
        }
    )


def _countries_frame(result: ModelResult) -> pd.DataFrame:
    countries = result.customer_countries
    return pd.DataFrame(
        {
            "customer_id": countries["CustomerID"].astype(str),
            "country": countries["Country"].astype(str),
            "transaction_lines": countries["TransactionLines"].astype("int64"),
            "distinct_invoices": countries["DistinctInvoices"].astype("int64"),
            "net_monetary": countries["NetMonetary"].astype(float),
        }
    )


def _profiles_frame(result: ModelResult) -> pd.DataFrame:
    mapping = {
        "SegmentCode": "segment_code",
        "SegmentOrder": "segment_order",
        "SegmentName": "segment_name",
        "Description": "description",
        "StrategyHypothesis": "strategy_hypothesis",
        "FutureKPIs": "future_kpis",
        "Customers": "customers",
        "CustomerShare": "customer_share",
        "NetMonetaryTotal": "net_monetary_total",
        "NetMonetaryShare": "net_monetary_share",
        "RecencyMean": "recency_mean",
        "RecencyQ25": "recency_q25",
        "RecencyMedian": "recency_median",
        "RecencyQ75": "recency_q75",
        "FrequencyMean": "frequency_mean",
        "FrequencyQ25": "frequency_q25",
        "FrequencyMedian": "frequency_median",
        "FrequencyQ75": "frequency_q75",
        "GrossMonetaryMean": "gross_monetary_mean",
        "GrossMonetaryQ25": "gross_monetary_q25",
        "GrossMonetaryMedian": "gross_monetary_median",
        "GrossMonetaryQ75": "gross_monetary_q75",
        "NetMonetaryMean": "net_monetary_mean",
        "NetMonetaryQ25": "net_monetary_q25",
        "NetMonetaryMedian": "net_monetary_median",
        "NetMonetaryQ75": "net_monetary_q75",
    }
    return result.segment_profiles.rename(columns=mapping)[list(mapping.values())]


def _centroids_frame(result: ModelResult) -> pd.DataFrame:
    return result.cluster_centroids.rename(
        columns={
            "SegmentCode": "segment_code",
            "RawCluster": "raw_cluster",
            "ScaledRecency": "scaled_recency",
            "ScaledFrequency": "scaled_frequency",
            "ScaledNetMonetary": "scaled_net_monetary",
        }
    )


def _evidence_frame(evidence: pd.DataFrame) -> pd.DataFrame:
    return evidence.rename(
        columns={
            "EvidenceType": "evidence_type",
            "Candidate": "candidate",
            "K": "k",
            "MetricName": "metric_name",
            "MetricValue": "metric_value",
            "Unit": "unit",
            "Note": "note",
            "SourcePath": "source_path",
        }
    )


def write_database(
    path: Path,
    source: SourceData,
    result: ModelResult,
    evidence: pd.DataFrame,
    metadata: dict[str, tuple[Any, str, str]],
) -> None:
    path = Path(path)
    if path.exists():
        path.unlink()
    connection = sqlite3.connect(path)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = DELETE")
        connection.execute("PRAGMA synchronous = FULL")
        connection.executescript(SCHEMA_SQL)
        _write_frame(connection, "transaction_lines", _transaction_frame(source))
        _write_frame(connection, "customer_segments", _customers_frame(result))
        _write_frame(connection, "customer_countries", _countries_frame(result))
        _write_frame(connection, "segment_profiles", _profiles_frame(result))
        _write_frame(connection, "cluster_centroids", _centroids_frame(result))
        _write_frame(connection, "model_evidence", _evidence_frame(evidence))
        metadata_rows = pd.DataFrame(
            [
                {
                    "metadata_key": key,
                    "metadata_value": json.dumps(value) if isinstance(value, (dict, list)) else str(value),
                    "value_type": value_type,
                    "description": description,
                }
                for key, (value, value_type, description) in metadata.items()
            ]
        )
        _write_frame(connection, "model_metadata", metadata_rows)
        connection.commit()
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise RuntimeError(f"SQLite integrity check failed: {integrity}")
        foreign_keys = connection.execute("PRAGMA foreign_key_check").fetchall()
        if foreign_keys:
            raise RuntimeError(f"SQLite foreign key check failed: {foreign_keys[:5]}")
        connection.execute("VACUUM")
    finally:
        connection.close()


def database_metadata(path: Path) -> dict[str, str]:
    with connect_read_only(path) as connection:
        rows = connection.execute(
            "SELECT metadata_key, metadata_value FROM model_metadata ORDER BY metadata_key"
        ).fetchall()
    return {row["metadata_key"]: row["metadata_value"] for row in rows}


def assert_schema_version(path: Path) -> None:
    metadata = database_metadata(path)
    if int(metadata.get("schema_version", -1)) != SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported database schema: {metadata.get('schema_version')}; expected {SCHEMA_VERSION}"
        )

from __future__ import annotations

import numpy as np
import pandas as pd

from retail_rfm.constants import EXPECTED
from retail_rfm.modeling import (
    build_model_result,
    build_rfm,
    prepare_known_lines,
    read_source,
    semantic_cluster_mapping,
)


def _lines(records: list[dict]) -> pd.DataFrame:
    frame = pd.DataFrame(records)
    defaults = {
        "StockCode": "10000",
        "Description": "TEST PRODUCT",
        "Country": "United Kingdom",
        "UnitPrice": 10.0,
    }
    for column, value in defaults.items():
        if column not in frame:
            frame[column] = value
    frame["CustomerID"] = frame["CustomerID"].astype("string")
    frame["InvoiceNo"] = frame["InvoiceNo"].astype("string")
    frame["StockCode"] = frame["StockCode"].astype("string")
    frame["Description"] = frame["Description"].astype("string")
    frame["Country"] = frame["Country"].astype("string")
    frame["InvoiceDate"] = pd.to_datetime(frame["InvoiceDate"])
    frame["LineAmount"] = frame["Quantity"] * frame["UnitPrice"]
    frame["SourceRowNumber"] = np.arange(2, len(frame) + 2)
    return prepare_known_lines(frame)


def test_full_refund_keeps_frequency_and_nets_to_zero():
    lines = _lines(
        [
            {"CustomerID": "A", "InvoiceNo": "100", "Quantity": 1, "UnitPrice": 100.0, "InvoiceDate": "2011-01-01"},
            {"CustomerID": "A", "InvoiceNo": "C100", "Quantity": -1, "UnitPrice": 100.0, "InvoiceDate": "2011-01-02"},
        ]
    )
    row = build_rfm(lines).iloc[0]
    assert row["Frequency"] == 1
    assert row["GrossMonetary"] == 100.0
    assert row["NetMonetary"] == 0.0


def test_partial_refund_changes_only_net_monetary():
    lines = _lines(
        [
            {"CustomerID": "A", "InvoiceNo": "100", "Quantity": 10, "UnitPrice": 10.0, "InvoiceDate": "2011-01-01"},
            {"CustomerID": "A", "InvoiceNo": "C100", "Quantity": -2, "UnitPrice": 10.0, "InvoiceDate": "2011-01-02"},
        ]
    )
    row = build_rfm(lines).iloc[0]
    assert row["Frequency"] == 1
    assert row["GrossMonetary"] == 100.0
    assert row["NetMonetary"] == 80.0


def test_c_prefixed_positive_quantity_never_adds_frequency():
    lines = _lines(
        [
            {"CustomerID": "A", "InvoiceNo": "100", "Quantity": 1, "InvoiceDate": "2011-01-01"},
            {"CustomerID": "A", "InvoiceNo": "C101", "Quantity": 1, "InvoiceDate": "2011-02-01"},
        ]
    )
    row = build_rfm(lines).iloc[0]
    assert row["Frequency"] == 1
    assert row["LastPurchase"] == pd.Timestamp("2011-01-01")


def test_semantic_mapping_does_not_depend_on_raw_cluster_numbers():
    rfm = pd.DataFrame({"NetMonetary": [10, 12, 100, 110, 1_000, 1_100, 10_000, 11_000]})
    labels = np.array([8, 8, 2, 2, 7, 7, 1, 1])
    permuted = np.array([3, 3, 9, 9, 0, 0, 5, 5])
    first = semantic_cluster_mapping(rfm, labels)
    second = semantic_cluster_mapping(rfm, permuted)
    first_segments = [first[value] for value in labels]
    second_segments = [second[value] for value in permuted]
    assert first_segments == second_segments == ["S1", "S1", "S2", "S2", "S3", "S3", "S4", "S4"]


def test_real_pipeline_preserves_raw_rfm_and_frozen_assignment():
    source = read_source("resource/Online Retail.csv")
    rfm = build_rfm(source.known_lines)
    raw = rfm[["Recency", "Frequency", "NetMonetary"]].copy(deep=True)
    result = build_model_result(source.known_lines)
    pd.testing.assert_frame_equal(
        raw.reset_index(drop=True),
        result.customer_segments[["Recency", "Frequency", "NetMonetary"]].reset_index(drop=True),
    )
    assert result.assignment_sha256 == EXPECTED["assignment_sha256"]
    assert int(result.customer_segments["AnyCappedFlag"].sum()) == 29

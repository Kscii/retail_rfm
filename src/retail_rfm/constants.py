from __future__ import annotations

from pathlib import Path

REFERENCE_DATE = "2011-12-10"
SCHEMA_VERSION = 1
MODEL_SEED = 431
MODEL_N_INIT = 20
MODEL_K = 4
CAP_QUANTILE = 0.995
FEATURE_NAMES = ("Recency", "FrequencyCapped", "NetMonetaryCapped")
PRODUCT_LIKE_PATTERN = r"^[0-9]{5}[A-Z]{0,2}$"
PIPELINE_ID = "all_4338__net__cap995_standard"

DEFAULT_CSV = Path("resource/Online Retail.csv")
DEFAULT_OUTPUT_DIR = Path("artifacts")
DEFAULT_EVIDENCE_ROOT = Path("docs/assets")

EXPECTED = {
    "raw_rows": 541_909,
    "deduplicated_rows": 536_641,
    "duplicate_extra_rows": 5_268,
    "known_transaction_lines": 401_604,
    "known_transaction_customers": 4_372,
    "customers": 4_338,
    "positive_rows": 392_692,
    "positive_invoices": 18_532,
    "clustered_net_total": 8_288_930.664,
    "cap_affected_customers": 29,
    "profiles": 4,
    "centroids": 4,
    "assignment_sha256": "7c3579fd0f8106258fe58a46b6406743b40e5bbbd08718944c00ab0e01b06b44",
    "segment_counts": {"S1": 1_054, "S2": 2_827, "S3": 406, "S4": 51},
    "representative_customers": {"S1": "17035", "S2": "15801", "S3": "12839", "S4": "13777"},
}

SEGMENTS = {
    "S1": {
        "name": "Long-inactive",
        "description": "Long time since last purchase, with low frequency and observed Net value.",
        "hypothesis": "Test a low-cost reactivation message against a no-contact control.",
        "future_kpis": "Reactivation rate; Net value per contacted customer",
    },
    "S2": {
        "name": "Regular",
        "description": "The customer majority, with mid-range recency, frequency and observed Net value.",
        "hypothesis": "Test reorder reminders or product bundles against the current experience.",
        "future_kpis": "Repeat-purchase rate; average invoice value",
    },
    "S3": {
        "name": "Active high-value",
        "description": "Recent, repeated purchasing with high observed Net value.",
        "hypothesis": "Test loyalty and retention benefits while measuring incremental behavior.",
        "future_kpis": "Retention; purchase frequency; incremental Net value",
    },
    "S4": {
        "name": "Top-frequency high-value",
        "description": "The most recent and frequent behavior, with very high observed Net value.",
        "hypothesis": "Test VIP or high-contact service with an explicit control group.",
        "future_kpis": "Retention; incremental Net value; service cost",
    },
}

EVIDENCE_FILES = (
    Path("rfm-model-exploration/tables/pipeline-k-evidence.csv"),
    Path("rfm-model-exploration/tables/representative-model-metrics.csv"),
    Path("presenter-guide/tables/cap-threshold-summary.csv"),
    Path("presenter-guide/tables/cap-threshold-model-agreements.csv"),
    Path("directed-sensitivity/tables/directed-baseline-comparison.csv"),
    Path("directed-sensitivity/tables/directed-run-summary.csv"),
)

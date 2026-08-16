from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

import joblib
import numpy as np

from .constants import EXPECTED, SCHEMA_VERSION
from .evidence import validate_evidence_files
from .modeling import sha256_file
from .pipeline import ArtifactPaths
from .storage import connect_read_only


def _load_manifest(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"Manifest not found: {path}; run `retail-rfm build` first")
    return json.loads(path.read_text(encoding="utf-8"))


def _assignment_hash(connection: sqlite3.Connection) -> str:
    import hashlib

    rows = connection.execute(
        "SELECT customer_id, segment_code FROM customer_segments ORDER BY customer_id"
    ).fetchall()
    payload = "\n".join(f"{row['customer_id']},{row['segment_code']}" for row in rows).encode()
    return hashlib.sha256(payload).hexdigest()


def verify_artifacts(csv_path: Path, output_dir: Path, evidence_root: Path) -> dict[str, Any]:
    csv_path = Path(csv_path)
    paths = ArtifactPaths.from_output_dir(Path(output_dir))
    manifest = _load_manifest(paths.manifest)
    failures: list[str] = []

    if manifest.get("schema_version") != SCHEMA_VERSION:
        failures.append(
            f"manifest schema_version={manifest.get('schema_version')} expected={SCHEMA_VERSION}"
        )
    if not csv_path.is_file():
        failures.append(f"input CSV missing: {csv_path}")
    elif sha256_file(csv_path) != manifest["input"]["sha256"]:
        failures.append("input CSV SHA-256 differs from manifest")

    evidence_hashes = validate_evidence_files(evidence_root)
    if evidence_hashes != manifest.get("evidence"):
        failures.append("validated evidence hashes differ from manifest")

    for key, path in (("database", paths.database), ("model", paths.model)):
        if not path.is_file():
            failures.append(f"artifact missing: {path}")
            continue
        expected_hash = manifest["artifacts"][key]["sha256"]
        actual_hash = sha256_file(path)
        if actual_hash != expected_hash:
            failures.append(f"{key} SHA-256 differs from manifest")

    if failures:
        raise AssertionError("; ".join(failures))

    bundle = joblib.load(paths.model)
    if bundle["schema_version"] != SCHEMA_VERSION:
        failures.append("joblib schema version mismatch")
    if bundle["build_id"] != manifest["build_id"]:
        failures.append("joblib build ID mismatch")
    if bundle["input_sha256"] != manifest["input"]["sha256"]:
        failures.append("joblib input hash mismatch")
    if bundle["assignment_sha256"] != EXPECTED["assignment_sha256"]:
        failures.append("joblib assignment hash mismatch")

    with connect_read_only(paths.database) as connection:
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            failures.append(f"SQLite integrity_check={integrity}")
        if connection.execute("PRAGMA foreign_key_check").fetchall():
            failures.append("SQLite foreign-key check failed")

        metadata = {
            row["metadata_key"]: row["metadata_value"]
            for row in connection.execute(
                "SELECT metadata_key, metadata_value FROM model_metadata"
            ).fetchall()
        }
        if metadata.get("build_id") != manifest["build_id"]:
            failures.append("SQLite build ID mismatch")
        if metadata.get("input_sha256") != manifest["input"]["sha256"]:
            failures.append("SQLite input hash mismatch")

        counts = {
            "transaction_lines": connection.execute(
                "SELECT COUNT(*) FROM transaction_lines"
            ).fetchone()[0],
            "customers": connection.execute("SELECT COUNT(*) FROM customer_segments").fetchone()[0],
            "profiles": connection.execute("SELECT COUNT(*) FROM segment_profiles").fetchone()[0],
            "centroids": connection.execute("SELECT COUNT(*) FROM cluster_centroids").fetchone()[0],
            "cap_affected": connection.execute(
                "SELECT SUM(any_capped_flag) FROM customer_segments"
            ).fetchone()[0],
        }
        expected_counts = {
            "transaction_lines": EXPECTED["known_transaction_lines"],
            "customers": EXPECTED["customers"],
            "profiles": EXPECTED["profiles"],
            "centroids": EXPECTED["centroids"],
            "cap_affected": EXPECTED["cap_affected_customers"],
        }
        if counts != expected_counts:
            failures.append(f"SQLite counts differ: {counts} expected {expected_counts}")

        segment_counts = dict(
            connection.execute(
                "SELECT segment_code, COUNT(*) FROM customer_segments GROUP BY segment_code ORDER BY segment_code"
            ).fetchall()
        )
        if segment_counts != EXPECTED["segment_counts"]:
            failures.append(f"segment counts differ: {segment_counts}")

        net_total = connection.execute("SELECT SUM(net_monetary) FROM customer_segments").fetchone()[0]
        if not np.isclose(net_total, EXPECTED["clustered_net_total"], atol=1e-6, rtol=0):
            failures.append(f"clustered Net total differs: {net_total}")

        max_net_error = connection.execute(
            """
            WITH line_net AS (
                SELECT customer_id, SUM(line_amount) AS net
                FROM transaction_lines
                GROUP BY customer_id
            )
            SELECT MAX(ABS(cs.net_monetary - ln.net))
            FROM customer_segments cs
            JOIN line_net ln USING (customer_id)
            """
        ).fetchone()[0]
        if max_net_error is None or max_net_error > 1e-6:
            failures.append(f"transaction lines do not reproduce customer Net M: max error={max_net_error}")

        database_assignment_hash = _assignment_hash(connection)
        if database_assignment_hash != EXPECTED["assignment_sha256"]:
            failures.append(f"SQLite assignment hash differs: {database_assignment_hash}")

        representatives = dict(
            connection.execute(
                "SELECT segment_code, customer_id FROM customer_segments WHERE is_representative=1 ORDER BY segment_code"
            ).fetchall()
        )
        if representatives != EXPECTED["representative_customers"]:
            failures.append(f"representative customers differ: {representatives}")

        s4_timeline = connection.execute(
            """
            SELECT COUNT(*) AS invoices, SUM(is_cancellation) AS cancellations
            FROM customer_invoice_timeline
            WHERE customer_id='13777'
            """
        ).fetchone()
        if tuple(s4_timeline) != (41, 8):
            failures.append(f"S4 representative timeline differs: {tuple(s4_timeline)}")

        index_names = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'"
            ).fetchall()
        }
        required_indexes = {
            "idx_transaction_customer",
            "idx_transaction_invoice",
            "idx_transaction_date",
            "idx_transaction_customer_date",
        }
        if not required_indexes.issubset(index_names):
            failures.append(f"required indexes missing: {sorted(required_indexes - index_names)}")

    if failures:
        raise AssertionError("; ".join(failures))

    return {
        "status": "PASS",
        "build_id": manifest["build_id"],
        "assignment_sha256": EXPECTED["assignment_sha256"],
        "counts": manifest["counts"],
        "max_customer_net_error": max_net_error,
        "segment_counts": segment_counts,
        "representatives": representatives,
        "s4_invoice_timeline": {"invoices": 41, "cancellations": 8},
    }

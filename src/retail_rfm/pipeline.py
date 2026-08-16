from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

import joblib

from .constants import (
    CAP_QUANTILE,
    FEATURE_NAMES,
    MODEL_K,
    MODEL_N_INIT,
    MODEL_SEED,
    REFERENCE_DATE,
    SCHEMA_VERSION,
)
from .evidence import normalized_evidence, validate_evidence_files
from .modeling import (
    assert_core_result,
    build_model_result,
    model_bundle,
    read_source,
    sha256_file,
)
from .storage import write_database


@dataclass(frozen=True)
class ArtifactPaths:
    output_dir: Path
    database: Path
    model: Path
    manifest: Path

    @classmethod
    def from_output_dir(cls, output_dir: Path) -> "ArtifactPaths":
        root = Path(output_dir)
        return cls(
            output_dir=root,
            database=root / "retail_rfm.sqlite",
            model=root / "retail_rfm_model.joblib",
            manifest=root / "manifest.json",
        )


def dependency_versions() -> dict[str, str]:
    names = ("pandas", "numpy", "scikit-learn", "scipy", "plotly", "dash", "joblib")
    return {name: importlib.metadata.version(name) for name in names}


def _build_id(input_sha256: str, assignment_sha256: str) -> str:
    payload = f"{SCHEMA_VERSION}|{input_sha256}|{assignment_sha256}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:20]


def _temporary_path(output_dir: Path, suffix: str) -> Path:
    descriptor, raw_path = tempfile.mkstemp(prefix=".retail-rfm-", suffix=suffix, dir=output_dir)
    os.close(descriptor)
    path = Path(raw_path)
    path.unlink()
    return path


def _commit_artifacts(staged_to_final: tuple[tuple[Path, Path], ...]) -> None:
    """Replace a related artifact set and restore the previous set on failure.

    The manifest is committed last, so readers never see a new manifest before
    its referenced files exist. This protects against ordinary Python and I/O
    exceptions during the commit; a machine-level crash is outside this
    process-level guarantee.
    """

    backups: dict[Path, Path | None] = {}
    installed: list[Path] = []
    try:
        for _, destination in staged_to_final:
            if destination.exists():
                backup = _temporary_path(
                    destination.parent, f".{destination.name}.backup"
                )
                os.replace(destination, backup)
                backups[destination] = backup
            else:
                backups[destination] = None

        for staged, destination in staged_to_final:
            os.replace(staged, destination)
            installed.append(destination)
    except BaseException:
        for destination in reversed(installed):
            destination.unlink(missing_ok=True)
        for destination, backup in backups.items():
            if backup is not None and backup.exists():
                os.replace(backup, destination)
        raise
    finally:
        for backup in backups.values():
            if backup is not None:
                backup.unlink(missing_ok=True)


def build_artifacts(csv_path: Path, output_dir: Path, evidence_root: Path) -> dict:
    csv_path = Path(csv_path)
    output_dir = Path(output_dir)
    evidence_root = Path(evidence_root)
    if not csv_path.is_file():
        raise FileNotFoundError(f"Input CSV not found: {csv_path}")
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = ArtifactPaths.from_output_dir(output_dir)

    evidence_hashes = validate_evidence_files(evidence_root)
    evidence = normalized_evidence(evidence_root)
    input_hash = sha256_file(csv_path)
    source = read_source(csv_path)
    result = build_model_result(source.known_lines)
    assert_core_result(source, result)
    build_id = _build_id(input_hash, result.assignment_sha256)

    temporary_database = _temporary_path(output_dir, ".sqlite.tmp")
    temporary_model = _temporary_path(output_dir, ".joblib.tmp")
    temporary_manifest = _temporary_path(output_dir, ".json.tmp")
    temporary_paths = (temporary_database, temporary_model, temporary_manifest)
    try:
        bundle = model_bundle(result, input_hash, build_id)
        joblib.dump(bundle, temporary_model, compress=3)
        versions = dependency_versions()
        metadata = {
            "schema_version": (SCHEMA_VERSION, "integer", "SQLite schema version"),
            "build_id": (build_id, "text", "Deterministic build identifier"),
            "input_sha256": (input_hash, "text", "SHA-256 of the read-only source CSV"),
            "assignment_sha256": (
                result.assignment_sha256,
                "text",
                "SHA-256 of sorted CustomerID and semantic segment assignments",
            ),
            "reference_date": (REFERENCE_DATE, "date", "Recency reference date"),
            "cap_quantile": (CAP_QUANTILE, "real", "Upper-tail quantile for F and Net M"),
            "frequency_cap": (result.frequency_cap, "real", "99.5% Frequency cap"),
            "net_monetary_cap": (result.net_monetary_cap, "real", "99.5% Net Monetary cap"),
            "feature_names": (list(FEATURE_NAMES), "json", "Model input feature order"),
            "k": (MODEL_K, "integer", "Selected cluster count"),
            "init": ("k-means++", "text", "K-means initialization"),
            "n_init": (MODEL_N_INIT, "integer", "Initializations in final model"),
            "random_state": (MODEL_SEED, "integer", "Final model seed"),
            "algorithm": ("lloyd", "text", "K-means iteration algorithm"),
            "raw_cluster_to_segment": (
                result.raw_cluster_to_segment,
                "json",
                "Semantic mapping ordered by raw Net M median",
            ),
            "dependency_versions": (versions, "json", "Locked runtime versions"),
            "evidence_hashes": (evidence_hashes, "json", "Imported validated evidence hashes"),
        }
        write_database(temporary_database, source, result, evidence, metadata)
        manifest = {
            "schema_version": SCHEMA_VERSION,
            "build_id": build_id,
            "input": {"path": str(csv_path), "sha256": input_hash},
            "assignment_sha256": result.assignment_sha256,
            "evidence": evidence_hashes,
            "artifacts": {
                "database": {
                    "path": paths.database.name,
                    "sha256": sha256_file(temporary_database),
                    "bytes": temporary_database.stat().st_size,
                },
                "model": {
                    "path": paths.model.name,
                    "sha256": sha256_file(temporary_model),
                    "bytes": temporary_model.stat().st_size,
                },
            },
            "counts": {
                "raw_rows": len(source.raw),
                "deduplicated_rows": len(source.deduplicated),
                "transaction_lines": len(source.known_lines),
                "customers": len(result.customer_segments),
                "profiles": len(result.segment_profiles),
                "centroids": len(result.cluster_centroids),
                "evidence_rows": len(evidence),
            },
            "versions": versions,
        }
        temporary_manifest.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )

        _commit_artifacts(
            (
                (temporary_model, paths.model),
                (temporary_database, paths.database),
                (temporary_manifest, paths.manifest),
            )
        )
        return manifest
    finally:
        for path in temporary_paths:
            path.unlink(missing_ok=True)

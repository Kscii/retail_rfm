from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from retail_rfm.evidence import validate_evidence_files
from retail_rfm.pipeline import ArtifactPaths, _commit_artifacts, build_artifacts
from retail_rfm.verification import verify_artifacts


def test_evidence_inventory_is_complete():
    hashes = validate_evidence_files(Path("docs/assets"))
    assert len(hashes) == 6
    assert all(len(value) == 64 for value in hashes.values())


def test_missing_evidence_fails_before_writing_artifacts(tmp_path):
    output = tmp_path / "output"
    with pytest.raises(FileNotFoundError):
        build_artifacts(Path("resource/Online Retail.csv"), output, tmp_path / "missing")
    assert not output.exists() or not any(output.iterdir())


def test_generated_artifacts_pass_independent_verification():
    manifest = Path("artifacts/manifest.json")
    if not manifest.is_file():
        pytest.skip("Run `uv run retail-rfm build` before integration verification")
    result = verify_artifacts(
        Path("resource/Online Retail.csv"), Path("artifacts"), Path("docs/assets")
    )
    assert result["status"] == "PASS"
    assert result["max_customer_net_error"] < 1e-6
    stored = json.loads(manifest.read_text())
    assert result["build_id"] == stored["build_id"]


def test_custom_output_path_and_corrupt_manifest_hash(tmp_path):
    source = ArtifactPaths.from_output_dir(Path("artifacts"))
    if not source.manifest.is_file():
        pytest.skip("Run `uv run retail-rfm build` before integration verification")

    custom = ArtifactPaths.from_output_dir(tmp_path / "custom-artifacts")
    custom.output_dir.mkdir()
    custom.database.symlink_to(source.database.resolve())
    custom.model.symlink_to(source.model.resolve())
    custom.manifest.write_text(source.manifest.read_text(encoding="utf-8"), encoding="utf-8")

    result = verify_artifacts(
        Path("resource/Online Retail.csv"), custom.output_dir, Path("docs/assets")
    )
    assert result["status"] == "PASS"

    damaged = json.loads(custom.manifest.read_text(encoding="utf-8"))
    damaged["artifacts"]["model"]["sha256"] = "0" * 64
    custom.manifest.write_text(json.dumps(damaged), encoding="utf-8")
    with pytest.raises(AssertionError, match="model SHA-256 differs from manifest"):
        verify_artifacts(
            Path("resource/Online Retail.csv"), custom.output_dir, Path("docs/assets")
        )


def test_artifact_commit_restores_previous_complete_set_on_failure(tmp_path, monkeypatch):
    destinations = tuple(tmp_path / name for name in ("model", "database", "manifest"))
    staged = tuple(tmp_path / f"new-{name}" for name in ("model", "database", "manifest"))
    for path in destinations:
        path.write_text(f"old-{path.name}", encoding="utf-8")
    for path in staged:
        path.write_text(f"new-{path.name.removeprefix('new-')}", encoding="utf-8")

    real_replace = os.replace
    staged_replacements = 0

    def fail_on_second_install(source, destination):
        nonlocal staged_replacements
        if Path(source) in staged:
            staged_replacements += 1
            if staged_replacements == 2:
                raise OSError("injected artifact commit failure")
        return real_replace(source, destination)

    monkeypatch.setattr("retail_rfm.pipeline.os.replace", fail_on_second_install)
    with pytest.raises(OSError, match="injected artifact commit failure"):
        _commit_artifacts(tuple(zip(staged, destinations, strict=True)))

    assert [path.read_text(encoding="utf-8") for path in destinations] == [
        "old-model",
        "old-database",
        "old-manifest",
    ]

from __future__ import annotations

import json
import re
from pathlib import Path


PRESENTATION = Path("presentation")


def _slides(filename: str = "slides.md") -> list[str]:
    markdown = (PRESENTATION / filename).read_text(encoding="utf-8")
    return re.split(r"\n---\n", markdown)[1:]


def _visible_markdown(filename: str = "slides.md") -> str:
    markdown = (PRESENTATION / filename).read_text(encoding="utf-8")
    return re.sub(r"<!--[\s\S]*?-->", "", markdown)


def _main_script(slide: str) -> str:
    match = re.search(r"【主讲】([\s\S]*?)【本页Q&A，不读】", slide)
    assert match is not None
    return match.group(1)


def test_final_english_deck_has_exactly_ten_pages_and_only_name():
    slides = _slides()
    assert len(slides) == 10
    assert "Online Retail Customer Segmentation" in slides[0]
    assert "Xuejian Fang" in slides[0]
    assert "Professor Osman Yagan" in slides[0]
    assert "Supervised by" not in slides[0]
    assert "Co-author" not in slides[0]
    assert not re.search(r"student\s*id|学号|\bSID\b", slides[0], re.IGNORECASE)
    assert sum("<FindingsDemo" in slide for slide in slides) == 1
    # Chinese rehearsal cues and Q&A may live inside Slidev speaker-note comments,
    # but the audience-facing slide content must remain English-only.
    assert not re.search(r"[\u3400-\u9fff]", _visible_markdown())


def test_chinese_reference_deck_is_preserved():
    slides = _slides("slides.zh.md")
    assert len(slides) == 10
    assert "Xuejian Fang" in slides[0]


def test_click_reveals_are_limited_to_preprocessing_and_methods():
    slides = _slides()
    click_slides = {
        index + 1
        for index, slide in enumerate(slides)
        if any(component in slide for component in ("<PreprocessingFlow", "<KMeansRealData"))
    }
    assert click_slides == {5, 6}
    assert "v-click" not in (PRESENTATION / "slides.md").read_text(encoding="utf-8")


def test_dataset_shows_all_source_fields_and_two_real_invoices():
    source = (PRESENTATION / "components/DatasetSampleEn.vue").read_text(encoding="utf-8")
    for field in (
        "InvoiceNo",
        "StockCode",
        "Description",
        "Quantity",
        "InvoiceDate",
        "UnitPrice",
        "CustomerID",
        "Country",
    ):
        assert field in source
    assert "536365" in source and "536366" in source and "17850" in source
    assert "audit and context" in source
    assert "One customer · two real invoices" in source
    assert '<b>Customer</b><span>1 : N</span><b>Invoice</b>' in source


def test_speaker_notes_are_readable_and_keep_the_requested_notation():
    slides = _slides()
    scripts = [_main_script(slide) for slide in slides]
    words = re.findall(
        r"K-means\+\+|R–F|S[1-4]|[A-Za-z]+(?:[-'][A-Za-z]+)*",
        "\n".join(scripts),
    )
    assert 720 <= len(words) <= 780
    assert sum(len(re.findall(r"^\d+\. ", slide, re.MULTILINE)) for slide in slides) in range(25, 31)
    for script in scripts:
        assert not re.search(r"\d", re.sub(r"S[1-4]", "", script))
        assert not re.search(r"\b(?:Customer|Invoice)\s+\d+", script, re.IGNORECASE)
    joined = "\n".join(scripts)
    assert "K-means++" in joined
    assert "R–F" in joined
    for segment in ("S1", "S2", "S3", "S4"):
        assert segment in joined


def test_real_data_method_and_static_only_findings_contract():
    slides = (PRESENTATION / "slides.md").read_text(encoding="utf-8")
    method = (PRESENTATION / "components/KMeansRealData.vue").read_text(encoding="utf-8")
    findings = (PRESENTATION / "components/FindingsDemo.vue").read_text(encoding="utf-8")
    static_index = (PRESENTATION / "public/static-demo/index.html").read_text(encoding="utf-8")
    static_app = (PRESENTATION / "public/static-demo/app.js").read_text(encoding="utf-8")
    assert "<KMeansRealData" in slides and "<KMeansInit" not in slides
    assert "Farther points receive a higher probability" in method
    assert method.count("v-click") == 19
    assert "not a cluster" in method
    assert "Live Dash" not in findings and "Static fallback" not in findings
    assert "Interactive RFM explorer" not in findings
    assert "static · browser only" not in findings
    assert "<footer>" not in static_index
    assert "Profiles" not in static_index
    assert "size: capped ? 2.8 : 1.8" in static_app
    assert "opacity: capped ? 0.65 : 0.35" in static_app
    assert 'size: 4, symbol: "diamond"' in static_app
    assert "data.schema_version !== 3" in static_app


def test_presentation_assets_resolve_from_the_deployment_base():
    method = (PRESENTATION / "components/KMeansRealData.vue").read_text(encoding="utf-8")
    findings = (PRESENTATION / "components/FindingsDemo.vue").read_text(encoding="utf-8")
    for source in (method, findings):
        assert "import.meta.env.BASE_URL" in source
        assert "document.baseURI" not in source


def test_pages_workflow_uses_repository_base_and_safe_public_boundary():
    workflow = Path(".github/workflows/pages.yml").read_text(encoding="utf-8")
    package = json.loads((PRESENTATION / "package.json").read_text(encoding="utf-8"))
    gitignore = Path(".gitignore").read_text(encoding="utf-8")
    assert "--base /retail_rfm/" in package["scripts"]["build:pages"]
    assert "pnpm build:pages" in workflow
    for entry in ("resource/", "docs/", "presentation/dist/", "*.sqlite", "*.joblib"):
        assert entry in gitignore


def test_final_english_specific_components_have_no_chinese_text():
    final_sources = [
        PRESENTATION / "components/DatasetSampleEn.vue",
        PRESENTATION / "components/EdaTriptychEn.vue",
        PRESENTATION / "public/static-demo/index.html",
        PRESENTATION / "public/static-demo/app.js",
    ]
    for path in final_sources:
        assert not re.search(r"[\u3400-\u9fff]", path.read_text(encoding="utf-8"))


def test_presentation_numbers_match_exported_evidence():
    data = json.loads(
        (PRESENTATION / "public/static-demo/data.json").read_text(encoding="utf-8")
    )
    findings = (PRESENTATION / "components/FindingsDemo.vue").read_text(encoding="utf-8")
    assert len(data["points"]) == 4_338
    assert len(data["centroids"]) == 4
    assert data["findings"]["s3_s4_customers"] == 457
    assert "about 10.5%" in findings
    assert "58.71%" in findings
    assert data["demo_customer"]["customer_id"] == "13777"
    assert data["demo_customer"]["invoice_count"] == 41
    assert data["demo_customer"]["cancellation_count"] == 8


def test_no_remote_frontend_dependencies_or_school_logo():
    source_paths = [PRESENTATION / "slides.md", PRESENTATION / "slides.zh.md"]
    for directory in ("components", "public", "scripts", "styles"):
        source_paths.extend(
            path
            for path in (PRESENTATION / directory).rglob("*")
            if path.is_file() and path.suffix in {".md", ".vue", ".css", ".js", ".mjs", ".html"}
        )
    frontend = "\n".join(
        path.read_text(encoding="utf-8")
        for path in source_paths
    )
    assert "fonts.googleapis.com" not in frontend
    assert "cdn.jsdelivr.net" not in frontend
    assert "University of Sydney logo" not in frontend

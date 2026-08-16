from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
VISUAL_DIR = PROJECT_ROOT / "visual"


def load_tokens() -> dict[str, str]:
    return json.loads((VISUAL_DIR / "tokens.json").read_text(encoding="utf-8"))


TOKENS = load_tokens()
SEGMENT_COLORS = {segment: TOKENS[segment] for segment in ("S1", "S2", "S3", "S4")}
